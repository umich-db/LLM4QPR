# PRICE_N: Hybrid PRICE-LLM SQL Representation

PRICE_N is the third PRICE feature-extractor variant in the LLM4QPR pipeline,
implementing the parsing-rule set from
[`hybrid_price_llm_sql_representation_updated.md`](hybrid_price_llm_sql_representation_updated.md).
It extends the original PRICE encoder with first-class support for the SQL
constructs that PRICE_S and PRICE_M either drop, mis-handle, or silently
approximate, and pushes everything that genuinely cannot be encoded
statistically to an explicit LLM-residual path.

This document is the architectural overview. The full implementation spec is at
[`superpowers/specs/2026-05-02-price-n-parsing-rules-design.md`](superpowers/specs/2026-05-02-price-n-parsing-rules-design.md);
the per-template parse traces are at
[`price_n_query_analysis/INDEX.md`](price_n_query_analysis/INDEX.md).

---

## 1. Motivation

PRICE encodes a SQL query as a fixed-width vector of statistics-grounded
tokens (column histograms, equi-join fanouts, table summaries, filter atoms)
that a Transformer ingests for cardinality / cost prediction. Its strength
is statistical rigor: every token corresponds to a precomputable aggregate
over base relations.

Its weakness is **scope**. The original PRICE assumes:
- conjunctive WHERE clauses,
- equi-joins forming an acyclic graph,
- single-value equality and range filters on numeric columns.

Real-world workloads break each of these assumptions:
- IMDB JOB has ~98% cyclic equi-join graphs.
- TPC-DS has CTEs, set operations, scalar subqueries, outer joins, NULL
  predicates, and `CASE` expressions.
- TPC-H has same-table column comparisons (`l_shipdate < l_commitdate`),
  multi-table self-anti-joins (q21), and date-arithmetic literals.

Earlier extensions PRICE_S (43-dim filter via bounding-box) and PRICE_M
(61-dim filter via 10 multi-ranges) made discrete-column LIKE/IN handling
better but did not address structural gaps: cyclic joins still rejected the
query, outer joins were silently inner-joined, NULL was dropped, etc.

PRICE_N is the systematic fix. It defines a precise boundary between
"statistics core" (what PRICE encodes) and "LLM residual" (what the LLM
tokenizer sees), and extends the PRICE token format just enough to cover the
high-value gaps.

---

## 2. Design philosophy

A query is split into two complementary representations:

### 2.1 Statistics core

A flat conjunctive SELECT over base relations, with predicates drawn from a
**fixed grammar** that PRICE knows how to encode. Each supported atom maps
to a precomputable statistic; the encoder ingests them as tokens.

### 2.2 LLM residual

Anything outside the supported grammar — CTEs with aggregates, UNION
branches, scalar subqueries, EXISTS/IN(subquery) constructs, CASE
expressions, function-call predicates, LIKE patterns, window functions, …
— is encoded by an LLM tokenizer + frozen embedding lookup. A downstream
fusion Transformer combines the PRICE token stream with the residual
embeddings.

**The boundary is the design**: it is not a soft "best effort" cutoff but
a mechanically-checkable rule (see §6). When a construct cannot be
faithfully expressed in the PRICE token stream, we don't fake it with a
zero-fill or a tautology — we punt to the LLM, which has the textual
context the model actually needs.

---

## 3. Five orthogonal CLI flags

PRICE_N's parsing rules and structural changes are independently
controllable, so a user can mix-and-match with PRICE_S / PRICE_M:

| Flag | What it enables | Default |
|---|---|---|
| `--price_n_parsing` | Pre-processor rewrites: NOT push-down (NNF), disjoint-OR → IN-list, date / timestamp literal normalization, atom tagging for new token types | off |
| `--price_n_filter` | 75-dim filter token (10 IN-list slots + tail bucket + null bits). Mutually exclusive with `--price_s`, `--price_m` | off |
| `--price_n_fanout` | 42-dim fanout token (orphan fraction + outer-join preserve flag) | off |
| `--price_n_pairwise` | 5th token type: 70-dim pairwise intra-table filter (same-table column comparisons + cross-table whitelist) | off |
| `--price_n` | Convenience shorthand: enables all four above | off |
| `--no_llm_residual` | Disable the LLM-residual fusion path. PRICE statistics-core embedding (from the OR Transformer in PRICE_N, or the filter_encoder CLS for base/S/M) goes directly to the prediction head; the LLM branch and any fusion-with-LLM components are skipped. Default off (LLM residual is included). | off |

Useful combinations:
- `--price_n` — full PRICE_N.
- `--price_n_parsing` alone — get the parser improvements without changing token shapes (useful for ablation).
- `--price_s --price_n_parsing` — keep PRICE_S filter shape but add NOT push-down, OR→IN, date literals, etc.
- `--price_n_pairwise` alone — add the 5th token type to a base PRICE encoder.

A single mutual-exclusion guard at parse time enforces that at most one of
`{--price_s, --price_m, --price_n_filter}` is set (they all change
filter_dim).

**Pretrained PRICE checkpoint compatibility for discrete columns**: under
lex-order the per-dim semantic of the histogram segment shifts from
"frequency rank" to "lex rank" for discrete columns. For PRICE_N runs,
prefer `--price_random_init` so that filter-embedding weights for discrete
columns are trained from scratch rather than inheriting frequency-ranked
pretrained weights. Numeric columns are unaffected (their histogram ordering
is unchanged).

---

## 4. What PRICE encodes statistically

PRICE_N's encoder consumes five token types per query, processed by a
three-stage pipeline (`scale_encoder` → `filter_encoder` → `OR Transformer`).
Each DNF clause goes through the first two stages independently to produce
a per-clause embedding; the OR Transformer aggregates per-clause embeddings
into the single statistics-core embedding that downstream consumers see.

### 4.1 Join histogram (40 dims, unchanged)

Per join column, the column's per-bin frequency normalized by table size.

### 4.2 Fanout token (42 dims, +2 from base)

Per equi-join direction, the fanout histogram (40 dims, unchanged) plus two
new scalars:
- **`orphan_fraction`** — fraction of rows on this side whose join key has
  zero matches on the other side. Precomputed at stats time from a
  `FULL OUTER JOIN` aggregate.
- **`outer_preserve_flag`** ∈ {0, 1} — set by the SQL pre-processor based
  on the ANSI join side (INNER → 0, LEFT → 1 on L→R, RIGHT → 1 on R→L,
  FULL → 1 on both).

Together these two scalars let the model express
`|L LEFT JOIN R| ≈ |L| · orphan_fraction + Σᵢ |L ∩ binᵢ| · f(L→R)[i]`.

### 4.3 Table token (4 dims, unchanged)

`(log table size, AVI, MinSel, EBO)` over the table's filter atoms.

### 4.4 Filter token (75 dims, +32 from base)

Per filter column:
```
[ histogram (40) ]
[ K = 10 IN-list slots, each (low, high, sel) → 30 dims ]
[ tail bucket (low, high, sel) → 3 dims ]
[ null_fraction, null_pred_flag → 2 dims ]
```

Encodes `col = X`, `col IN (X1, …, Xn)`, `col != X` (rule a extension via
range-pair gap encoding), `col BETWEEN x AND y`, `col IS NULL`,
`col IS NOT NULL`. For >K IN-values, the K most-selective populate slots
explicitly and the rest fold into the tail bucket.

For **discrete (varchar / categorical) columns**, PRICE_N applies lex-order
to the top-39 SpaceSaving keys (OtHeRs stays at bin 39 as the catch-all).
This makes range queries (`col </<=/>/>= 'string'`, `col BETWEEN 'A' AND
'B'`) first-class: they map to a contiguous range of lex-sorted bins,
encoded as a single `(low, high, sel)` slot. Selectivity sums the
frequencies of all top-39 lex-bracket-matching bins; the OtHeRs
lex-below-X contribution is dropped for simplicity (acceptable when OtHeRs
mass is small or when the literal is in top-39).

Frequency-rank ordering in PRICE_S / PRICE_M / base PRICE is unchanged;
only PRICE_N's `Sql2FeatureN.space_saving_summary` overrides the ordering.
Stats files (`summary40.pkl`) are unchanged — the lex re-sort is applied at
load time in PRICE_N only.

For same-column OR chains (`c = v1 OR c < v2 OR c > v3`, including those
produced by NNF expansion of `NOT BETWEEN`), the `or_atoms` field on the
column's filter atom holds a list of `(op, value)` pairs; each pair is
converted to a region via `_atom_to_region` and the union is intersected
with the current region set. See §5a for the DNF treatment.

**Multi-atom AND combination via interval arithmetic.** When a column has
multiple AND-connected atoms (e.g., `c BETWEEN 5 AND 25 AND c != 15`),
`_compute_regions` runs interval arithmetic to produce a sorted list of
disjoint sub-ranges:

1. Start with the universal region `[0, 1]` (normalized).
2. EQ + IN values → intersect with the union of their point regions.
3. Range bounds → intersect with `[range_low, range_high]`.
4. `or_atoms` (same-column OR block) → intersect with the union of their regions.
5. NEQ / NOT IN values → subtract each value's point region.

The final region list is sorted by selectivity descending; the top `K = 10`
populate the explicit slots, the remainder folds into the tail bucket.
NULL atoms are orthogonal (encoded via `null_pred_flag`).

This unifies the encoder around a single principle: slots represent the
*result* of the column's AND filter as a union of disjoint sub-ranges. No
per-kind branching, no silently-dropped atoms.

Example: `c BETWEEN 5 AND 25 AND c != 15` produces 2 slots covering
`[5, 15)` and `(15, 25]`. `c IN (1, 2, 3) AND c >= 2` produces 2 slots
(values 2 and 3 survive). `c = 5 AND c = 10` (contradictory) produces
all-zero slots.

### 4.5 Pairwise intra-table filter token (70 dims, NEW token type)

Per `A.x op A.y` predicate (same-table column comparison) plus one
whitelisted cross-table case (`inv_quantity_on_hand × cs_quantity` from
TPC-DS q72):
```
[ H_xy 8×8 anti-diagonal-ordered (64 dims) ]
[ K = 2 range slots, each (low, high, sel) → 6 dims ]
```

The 64 cells are ordered by anti-diagonal level `d = j − i`, sweeping from
`d = +7` (most extreme `x < y`) through the diagonal (`d = 0`, the 8 cells
where `x ≈ y`) down to `d = −7` (most extreme `x > y`). This ordering makes
each comparison operator's cells **consecutive in bin index**, so the
binary mask is replaced by 1 or 2 range slots.

| Op | Slot 1 range (0-indexed inclusive) | Slot 2 |
|---|---|---|
| `<` | `(0, 27)` | unused |
| `<=` | `(0, 35)` | unused |
| `=` | `(28, 35)` | unused |
| `!=` | `(0, 27)` | `(36, 63)` |
| `>` | `(36, 63)` | unused |
| `>=` | `(28, 63)` | unused |

A bonus from this ordering: date-arithmetic predicates `A.col > B.col + N`
(rule d) translate to `j − i < −N`, which is **a single contiguous range**
in the 64-vector. The encoder learns the offset N → range bound mapping
naturally. Approximate-equality predicates `|A.x − A.y| ≤ k` are similarly
single-range.

For discrete columns (TPC-DS `cd_marital_status`, `ca_city`), the 2D
histogram is computed via the SpaceSaving outer-product trick, with OtHeRs
dropped for high-cardinality columns to avoid diagonal-mass inflation.

### 4.6 OR Transformer (statistics-core composition)

The OR Transformer is the third and final stage of the PRICE encoder,
**applied uniformly to every query** regardless of clause count. Its input
is a variable-length list of per-clause embeddings produced by the existing
`scale_encoder + filter_encoder` pair, one per DNF clause. Its output is
the single statistics-core embedding that downstream consumers (fusion
Transformer + MLP) see. Downstream code never sees the raw `filter_encoder`
output directly.

Architecture: 2-layer multi-head self-attention block with a learned [CLS]
token. The CLS token attends to the per-clause sequence; its position-0
output is the statistics-core embedding.

**Why it always runs.** If the OR Transformer were skipped for single-clause
queries (Identity dispatch by clause count), single-clause queries would
produce one statistical regime (raw `filter_encoder` output) and
multi-clause queries would produce a different one (post-OR-aggregation).
The downstream consumer would see two embedding distributions, training
would be inconsistent, and the OR Transformer's weights would be updated
only by rare multi-clause queries. Always-applied semantics avoid all three
problems. For single-clause input the layer is degenerate — attention over
a length-1 non-CLS sequence reduces to a learned linear projection of the
clause embedding plus the CLS bias — but it is still applied, and its
weights are updated by every query.

**DNF blowup mitigation.** The parser caps DNF expansion at a configurable
threshold (default `max_clauses = 16`). Queries that would produce more
than `max_clauses` get the entire mixed-column `Or` block routed to LLM
residual; the surrounding conjunctive atoms still flow through PRICE as a
single clause. The OR Transformer always sees ≥ 1 clause input.

### 4.7 Empty-token regimes (no-join, no-filter, no-pairwise queries)

PRICE handles queries with empty token categories gracefully — both
`scale_encoder` and `filter_encoder` always run, with whatever tokens they
actually have plus a few placeholders for shape consistency.

| Token type | Possible counts | Placeholder behavior |
|---|---|---|
| Virtual [CLS] (in scale stage) | always 1 | hardcoded by `ScaleEmbedding.virtual_token_embedding` |
| Join histograms | 0 if single-table; else ≥ 1 per join column | for single-table queries, `_create_single_table_features` injects a zero-padded placeholder so `n_jc = 1` |
| Fanout | 0 if single-table; else `2 × n_joins` | same — zero-padded placeholder, `n_fo = 2` |
| Tables | always ≥ 1 | every query has at least one FROM table |
| Filters | 0 if no filter atoms | nothing appended; `n_fc = 0` is fine — the `for i in range(n_filter_col)` loop iterates zero times |
| Pairwise intra | 0 if no col-op-col atoms | nothing appended; `n_pi = 0` is fine |

The architectural invariant: **every query produces a per-clause embedding
via `scale_encoder → filter_encoder`, regardless of how many of each token
type it actually has**. Empty filter / pairwise / join sets are first-class
cases.

For batching across queries with different counts, `pad_and_cache_features`
pads to the batch maximum and emits a padding mask; the transformer's
attention literally ignores padded positions.

The most trivial query (`SELECT count(*) FROM t`) flows through the
pipeline as one DNF clause:

```
scale stage:    [CLS, zero_join_placeholder, zero_fanout_L→R, zero_fanout_R→L]
                → scale_encoder → scale_output (length 4)

filter stage:   [scale_output, table_t]
                → filter_encoder → emb_1

OR Transformer: [CLS_or, emb_1]
                → statistics-core embedding
```

The placeholder zero tokens carry no information (zero embeddings produce
zero contributions via attention), but they keep the encoder's invariant
intact: every stage processes a non-empty token sequence, and the output
shape is fixed.

---

## 5. SQL pre-processor pipeline

When `--price_n_parsing` is on, the AST passes through 9 phases:

1. **Subquery handling** — see §6 below; under PRICE_N, the existing
   inliners are skipped and the subqueries become residuals.
2. **NOT push-down → NNF** (rule i): De Morgan + per-comparator flips +
   `IS NULL` / `IS NOT NULL` swap + `NOT BETWEEN` expansion to
   `Or(LT, GT)` + `NOT IN (literal list)` expansion to `AND` of NEQs.
   After this pass, the only surviving `Not` wrappers are on `Like`
   / `ILike` (which go to residual under §7) and on `In(subquery)`
   (which goes to residual under §6 as `NotInSubquery`).
3. **Disjoint OR → IN** (rule e): collapses `(c=v1 OR c=v2 OR …)` chains
   on the same column into `c IN (v1, …, vk)`.
4. **BETWEEN** — under PRICE_N, **left as-is** (the filter token's slot format
   `(low, high, sel)` already encodes a range natively; `_extract_filter_atoms`
   reads `Between(col, x, y)` directly and either populates `range_low` /
   `range_high` for conjunctive context or appends `("between", x, y)` to
   `or_atoms` for same-column OR blocks). Under PRICE_S / PRICE_M / base
   PRICE the existing expansion to `Paren(And(GTE, LTE))` continues to run.
5. **Date / timestamp literal parsing** (rule c): `DATE 'YYYY-MM-DD'`,
   `TIMESTAMP '…'`, and `DATE '…' ± INTERVAL 'N' DAY` all become integer
   epoch days.
6. **Date arithmetic atom tagging** (rule d): `A.col op B.col + N` self-pair
   patterns get tagged for the pairwise-token path.
7. **ANSI JOIN side preservation** (rule g): instead of dropping `LEFT/RIGHT/FULL`
   when rewriting `JOIN ON` to comma-FROM, the side is stashed for the fanout
   encoder.
8. **Same-table col-op-col tagging** (rule j): `A.x op A.y` patterns
   produce pairwise atoms.
9. **Cross-table non-equi tagging** (rule h): only the whitelisted
   inventory × catalog_sales pair survives; everything else drops.

Phases 6, 7, 8, 9 are gated on the corresponding structural flag — e.g.,
date-arithmetic tagging only runs under `--price_n_pairwise`.

---

## 5a. Canonical form: NNF → per-column DNF

After the pre-processor (§5), the WHERE clause is in **NNF**: every `NOT`
wrapper is gone except where wrapping a `LIKE` (which goes to LLM residual)
or a `NOT IN (subquery)` (which goes to residual under §6). `NOT BETWEEN`
is handled by Phase 2's NNF pass (`Not(Between)` → `Or(LT, GT)`); positive
`BETWEEN` nodes survive as first-class atoms and are read directly by
`_extract_filter_atoms`.

For PRICE's atom-based cardinality estimation, the *useful* canonical form
is **DNF**: a disjunction of conjunctions, where each conjunction is a flat
list of atoms over base relations. In DNF, the model can encode each clause
independently and combine clause selectivities at the top level.

PRICE_N takes a pragmatic approach to DNF rather than full distributive
expansion (which can blow up exponentially — see §6.3 of the [original
design](hybrid_price_llm_sql_representation_updated.md)):

| Pattern | DNF treatment in PRICE_N |
|---|---|
| Pure conjunction `(a AND b AND c)` | Already in DNF (one clause). Per-column atoms combined via interval arithmetic in `_compute_regions`; output is a list of disjoint sub-ranges packed into the column's filter token slots. Naturally handles AND combinations like `BETWEEN x AND y AND col != z` (produces gap-range slots) and `IN (...) AND col >= k` (produces intersection slots). `BETWEEN(col, x, y)` survives as-is and lands in `range_low` / `range_high`. |
| Disjoint-column EQ chain `(c=v1 OR c=v2 OR …)` | Same-column OR; collapsed to a single clause via the rule-e IN-list rewrite. |
| Same-column OR with mixed atom kinds `(c<5 OR c>10)` | Same-column OR; collapsed to a single clause via the `or_atoms` field on the column's filter atom (each leaf becomes one of the K=10 IN-list slots). |
| Same-column BETWEEN OR `(c BETWEEN 1 AND 3 OR c BETWEEN 7 AND 9)` | Each `BETWEEN` leaf becomes a `("between", low, high)` 3-tuple in `or_atoms`; `_atom_to_slot` converts it to a `(low_norm, high_norm, sel)` range slot. |
| Mixed-column OR `(a<5 OR b>10)` | Genuine multi-clause DNF. Distribute to two clauses, each encoded independently by the `scale_encoder + filter_encoder` pair → two per-clause embeddings; the OR Transformer (§4.6) composes them into the final statistics-core embedding. |
| Multi-clause DNF with shared atoms `((a AND b) OR (a AND c))` | After distribution → two clauses `(a AND b)` and `(a AND c)`. Each PRICE-encoded independently, then OR-aggregated. The shared `a` atom appears in both clauses via DNF distribution; the OR Transformer learns the redundancy implicitly. |
| Multi-clause DNF beyond `max_clauses` (default 16) | Residual — the entire `Or` block is encoded by the LLM tokenizer to avoid combinatorial blowup. Surrounding conjunctive atoms still flow through PRICE as one clause. |

The implementation enforces this boundary in `_extract_filter_atoms`:

- Walk every top-level `Or` block.
- If all leaves are predicates on the **same** column, collapse them into
  the column's `or_atoms` list (consumed by the filter-token encoder).
- Otherwise, the `Or` block becomes residual.

This keeps the formal "PRICE encodes one DNF clause" guarantee while
covering the same-column case (which is the only DNF pattern that appears
without exponential blowup in TPC-H/DS).

### Example: NOT BETWEEN

```sql
WHERE c NOT BETWEEN 5 AND 10
```

Pipeline:

1. NNF expansion (Phase 2): `Not(Between)` → `Or(LT(c, 5), GT(c, 10))`.
2. Extractor (`_extract_filter_atoms`): top-level `Or`, both leaves on
   column `c` → collapse to `or_atoms = [("<", 5), (">", 10)]` on `c`.
3. Encoder: two range slots emitted: `(0, c-norm-5, sel_left)` and
   `(c-norm-10, 1, sel_right)`. The `null_pred_flag` is 0.

The result is a single DNF clause encoded as one filter token with two
populated slots. No `Not` wrapper survives, no residual is generated.

### Example: mixed-column OR

```sql
WHERE (c1 < 5 AND c2 > 10) OR (c3 = 'foo' AND c4 BETWEEN 1 AND 100)
```

Pipeline:

1. NNF (no NOT to push).
2. Extractor sees the top-level `Or` with mixed-column leaves.
3. The `Or` block is **not** collapsed — it goes to LLM residual as `MixedColumnOr`.
4. Any pure-conjunctive atoms outside the `Or` block (none in this example) are still extracted normally.
5. The fusion Transformer combines PRICE's residual-rest atoms with the LLM-encoded textual `Or` representation.

When `--price_n_or` is enabled, the parser instead expands mixed-column `Or`
blocks into multiple DNF clauses (up to `--price_n_or_max_clauses`, default
16), encodes each clause independently through `scale_encoder + filter_encoder`,
and aggregates the per-clause embeddings via the OR Transformer (§4.6). The
residual path above applies only when `--price_n_or` is off (the default).

---

## 6. Subquery inlining policy

Under PRICE_N, a subquery (CTE, derived table, or inline) is **inlined** iff
its body is a flat conjunctive SELECT over base relations satisfying **all**
of:

- No GROUP BY
- No HAVING
- No DISTINCT
- No window functions
- No `ORDER BY` + `LIMIT` combination (ORDER BY alone is fine)
- Not itself a UNION / INTERSECT / EXCEPT
- No aggregate function calls (SUM, AVG, MIN, MAX, COUNT) in projections
- Not `WITH RECURSIVE`

Anything else becomes residual.

This means the following always go to LLM residual (no exceptions, no
case-by-case approximations):

- `EXISTS (...)` and `NOT EXISTS (...)`
- `col IN (subquery)` and `col NOT IN (subquery)`
- `col op (SELECT AGG(x) FROM ...)` (scalar subqueries)
- `UNION`, `INTERSECT`, `EXCEPT` set ops
- CTEs whose body has aggregates / GROUP BY / window / etc.
- Subqueries inside SELECT projections or CASE expressions
- LIKE / NOT LIKE / ILIKE patterns (see §7)

Earlier PRICE variants tried to inline EXISTS / IN(subquery) / scalar
subqueries with case-by-case rules — keeping equi-join atoms but dropping
NEQ, treating NOT EXISTS as EXISTS, estimating scalar values from
statistics. Each approximation introduced a different cardinality bias.
PRICE_N abandons these in favor of the uniform residual policy: the LLM
sees the full subquery text and the fusion Transformer learns to combine
it with PRICE's statistical signal.

The full discussion is in
[`SUBQUERY_INLINING.md`](price_n_query_analysis/SUBQUERY_INLINING.md).

---

## 7. LIKE patterns

`col LIKE 'pattern'`, `NOT LIKE`, `ILIKE`, `NOT ILIKE` are **always
residual** under PRICE_N, regardless of column cardinality.

PRICE statistics can only approximate LIKE selectivity by matching the
pattern against a column's top-39 SpaceSaving keys. This works for
low-cardinality categorical columns (e.g., TPC-H `p_type` has ~150 distinct
values) but degrades sharply for high-cardinality text (e.g., IMDB
`movie_companies.note` has millions of distinct strings — the top-39
captures almost none of the matches). The signal is too noisy to model
uniformly.

The LLM tokenizer receives the column reference + pattern and learns
pattern-specific selectivity from training labels — far better positioned
than a SpaceSaving top-39 lookup.

PRICE_S and PRICE_M continue to do SpaceSaving-key-matching; the LIKE →
residual policy is PRICE_N-specific.

---

## 8. NEQ filter encoding (range-pair, rule a extension)

`col != X` is encoded as **two range slots** in the filter token, covering
the gaps on either side of X under the column's natural ordering:

- Numeric columns: `(0, x_norm, sel_left)` + `(x_norm + ε, 1, sel_right)`
  where `x_norm` is X's normalized position on the histogram.
- Discrete columns: same shape, but using SpaceSaving frequency-rank
  ordering. The selectivity sum equals `1 − sel(X) − null_fraction`, which
  is correct under any monotone re-binning — the model's encoder learns
  from the *sum*, not the geometric ordering.

Multiple NEQ values produce N+1 range slots covering the gaps between
sorted exclusions. No polarity bit is needed; the slot coverage itself
represents the "not equal" semantics.

---

## 9. Statistics generation

Five new aggregates extend the existing `histogram40.pkl`, `summary40.pkl`,
`fanout40.pkl`, and `size.pkl`:

| Aggregate | Purpose | Source |
|---|---|---|
| `null_fraction.pkl` | per-column null fraction (rule b) | `SELECT SUM(CASE WHEN col IS NULL THEN 1 ELSE 0 END) / COUNT(*)` per column |
| `__orphan__` nested in `fanout40.pkl` | per-join-direction orphan fraction (rule g) | `FULL OUTER JOIN` aggregate per join column pair |
| `pairwise_intra40.pkl` | same-table 2D joint histograms (rule j) | 8×8 ordered region split per whitelisted column pair; numeric via `width_bucket`, discrete via SpaceSaving outer product |
| `nonequi_pair_xtab.pkl` | cross-table 2D joint (rule h) | bin-then-multiply outer product for the single TPC-DS inventory × catalog_sales whitelist case |
| `nonequi_fanout_op40.pkl` | operator-keyed range-fanout stub (rule d) | empty for current TPC-H/DS workloads |

CLI: `python generate_price_stats_from_pg.py --db tpch --price_n` or `--db
tpcds --price_n`. Each structural flag (`--price_n_filter`, `_fanout`,
`_pairwise`) only enables the aggregates it actually needs, so partial
configurations are supported.

---

## 10. Model-side changes

The PRICE encoder gains:

- **`ScaleEmbedding.fanout_embeddings`**: `Linear(hist_dim+3, n_embd)` (was `+1`) to ingest the wider fanout token.
- **`FilterEmbedding.filter_embeddings`**: `Linear(75, n_embd)` (was `Linear(43, n_embd)` for base, `Linear(61, ...)` for PRICE_M).
- **`FilterEmbedding.pairwise_intra_embeddings`** (new): `Linear(70, n_embd)` for the 5th token type.
- **`OrTransformer`** (new): the third encoder stage, applied uniformly to every query (§4.6). 2-layer multi-head self-attention block with a learned [CLS] token; CLS position-0 output is the statistics-core embedding. Input is a variable-length sequence of per-clause embeddings produced by the existing `scale_encoder + filter_encoder` pair. For single-clause queries the layer is degenerate (length-1 sequence + CLS) but still runs to keep embedding semantics uniform across queries. Instantiated automatically whenever any PRICE_N structural flag (`--price_n_parsing`, `--price_n_filter`, `--price_n_fanout`, `--price_n_pairwise`, or `--price_n`) is enabled. Always starts random-init (no pretrained PRICE counterpart); the partial-copy helper skips its weights. The `--price_n_or` flag controls parser-side DNF expansion to feed multiple clauses per query — orthogonal to the OR Transformer module's presence. **Fully wired through the data pipeline when `--price_n_or` is set**: `_extract_atoms_per_clause` expands the WHERE tree to per-clause atoms_meta dicts, `Sql2FeatureN.create_sql_features` runs in list mode to produce per-clause 6-tuples, `pad_and_cache_features(multi_clause_data=...)` two-level pads and emits a `num_clauses` tensor, and `RegressionModel.forward(num_clauses=...)` reshapes the batch for the OR Transformer. Each clause's atoms — including filter, pairwise (col-op-col, xtab non-equi), and NULL atoms — come from that clause's leaves via `_build_atoms_meta_from_leaves`. Atoms in a top-level AND with the OR block correctly appear in every DNF clause via distribution; atoms inside one OR disjunct correctly appear only in that clause. The FROM clause's join structure (`join_sides`) is shared across all DNF clauses and remains query-level.

Pretrained PRICE checkpoints load with `strict=False` and a partial-copy
helper:
- The first 43 dims of the new 75-dim filter weight match the base PRICE
  layout exactly (`hist[40] + (low, high, sel)` slot 1 = single-equality /
  range case), so the base equi-filter behavior is preserved at init.
- Fanout embedding's first 41 dims match the base layout
  (`hist_sum + raw_hist[40]`); the two new scalars start zero-initialized
  and are trained from labels.
- Pairwise embedding starts fully random.
- OR Transformer starts fully random (no pretrained counterpart in base
  PRICE).

---

## 10a. Full pipeline workflow (PRICE_N + LLM)

End-to-end picture for a single (query plan, query) pair. The
architecture has two LLM-style branches that should not be confused:

- **QueryPlanLLM** — the LoRA-finetuned encoder for the *query plan
  text* (the EXPLAIN output). This is what the existing `--llm_mode lora`
  / `LLMPriceJointModel.self.llm` already does.
- **QueryResidualTokens (QRT)** — a *tokenizer-only* path for the parts
  of the *SQL query* that the statistics core cannot represent
  (LIKE, regex, EXISTS / IN(subquery), scalar subqueries, opaque
  expressions, etc.). It runs through the LLM's tokenizer and embedding
  layer **only** — no transformer blocks — so the output is a sequence
  of raw token embeddings carrying the surface form of the residual
  fragments. It is *not* an LLM forward in the usual sense; the name
  "LLM-residual" used elsewhere refers to this same concept and is
  reserved for legacy compatibility.

```
                     ┌──────────────────────┐    ┌──────────────────────────┐
   inputs:           │  Query Plan  (text)  │    │      Query (SQL text)    │
                     └─────────┬────────────┘    └────────────┬─────────────┘
                               │                              │
                               ▼                              ▼
                  ┌────────────────────────┐   ┌──────────────────────────────┐
                  │  QueryPlanLLM          │   │  Sql2FeatureN parser         │
                  │  (LoRA-finetuned)      │   │  splits the SQL into:        │
                  │  tokenize + encode     │   │   A) statistics-core atoms   │
                  │  → token seq  h_plan   │   │      in DNF form (per AND    │
                  │     [B, T_p, D_llm]    │   │      clause, K clauses)      │
                  └────────────────────────┘   │   B) residual text spans     │
                               │               │      (LIKE / EXISTS / scalar │
                               │               │      subq / opaque)          │
                               │               └─┬────────────────────────┬───┘
                               │                 │ A: K AND-clauses       │ B: residual text
                               │                 ▼                        ▼
                               │     ┌────────────────────────┐   ┌──────────────────────┐
                               │     │ STATISTICS CORE        │   │ QUERY RESIDUAL TOKENS│
                               │     │  (per AND-clause k)    │   │       (QRT)          │
                               │     │   ┌────────────────┐   │   │  tokenizer + embed   │
                               │     │   │ scale_encoder  │   │   │  layer ONLY          │
                               │     │   │ filter_encoder │   │   │  (no transformer     │
                               │     │   │  → CLS_k       │   │   │   blocks)            │
                               │     │   └────────────────┘   │   │  → r_qry             │
                               │     │ → [CLS_1 … CLS_K]      │   │     [B, T_r, D_llm]  │
                               │     └────────────────────────┘   └──────────────────────┘
                               │                 │                        │
                               │                 ▼                        │
                               │     ┌────────────────────────┐           │
                               │     │ OR-TRANSFORMER         │           │
                               │     │  AND-clauses attend    │           │
                               │     │  one another           │           │
                               │     │  Output: CLS-only      │           │
                               │     │  stat_core             │           │
                               │     │   [B, 1, D_stat]       │           │
                               │     └────────────────────────┘           │
                               │                 │                        │
                               │                 └────────┬───────────────┘
                               │                          ▼
                               │       ┌──────────────────────────────────────┐
                               │       │ STAT-CORE  ↔  QRT  CROSS-ATTN        │
                               │       │ (transformer block)                  │
                               │       │  stat_core (CLS, length-1) attends   │
                               │       │  over QRT residual tokens, and vice  │
                               │       │  versa. Joint output:                │
                               │       │   h_query  [B, T_q, D]               │
                               │       └──────────────────────────────────────┘
                               │                          │
                               │                          │
                               ▼                          ▼
                       ┌──────────────────────────────────────────┐
                       │     PLAN  ↔  QUERY  CROSS-ATTN           │
                       │  (transformer block, N layers)           │
                       │   h_plan tokens cross-attend over        │
                       │   h_query, and (optionally) reverse:     │
                       │   h_query attends back to h_plan.        │
                       │   Output: joint embedding                │
                       │     [B, T_joint, D]                      │
                       └──────────────────────────────────────────┘
                                          │
                                          ▼
                                    [CLS] / mean pool
                                          │
                                          ▼
                                         MLP
                                          │
                                          ▼
                                  predicted runtime
```

### Component summary

1. **QueryPlanLLM** (existing). LoRA-finetuned LLM over the EXPLAIN text.
   Produces `h_plan` ∈ ℝ^{B×T_p×D_llm}.

2. **Sql2FeatureN** (existing parser, `experiments/features_tool_n.py`).
   Splits the SQL into (A) statistics-core atoms organized in DNF
   per-clause, and (B) residual text fragments.

3. **Statistics-core encoders** (existing). For each AND-clause *k*,
   the per-clause atoms are scaled (`scale_encoder`) and filtered
   (`filter_encoder`); position-0 of `filter_encoder` output is the
   per-clause CLS token `CLS_k`.

4. **OR-Transformer** (existing). Lets the K per-clause CLS tokens
   attend to one another. Reads only CLS positions of each clause
   (not the full per-clause sequences). Output: a single
   `stat_core` CLS embedding of shape `[B, 1, D_stat]` per query.

5. **QueryResidualTokens (QRT) — NEW**. Residual text fragments are
   passed through QueryPlanLLM's *tokenizer + embedding lookup only*
   (no transformer layers). Output: `r_qry` ∈ ℝ^{B×T_r×D_llm}.
   Concretely, this is `embed_tokens(tokenizer(residual_text))`.

6. **Stat-core ↔ QRT cross-attention — NEW**. A bidirectional
   cross-attention transformer block where `stat_core` (length-1)
   and `r_qry` exchange information. Produces `h_query` — the
   unified query-side representation.

7. **Plan ↔ Query cross-attention** (replaces the current
   biCrossAttn-on-PRICE-summary path). `h_plan` and `h_query`
   exchange via N cross-attention layers. The result is pooled
   (CLS) and fed to the prediction MLP.

### What changes vs. the current implementation

| Component                        | Current (`mode 12 cx=4`)             | Proposed                                                  |
|---|---|---|
| QueryPlanLLM                     | LoRA, full token seq                 | Same                                                      |
| Sql2FeatureN                     | Outputs stat-core only               | Also emits residual text spans for QRT                    |
| Statistics core per-AND-group    | Single AND-clause path (K=1)          | Multi-clause via DNF (data pipeline already wired w/ `--price_n_or`)    |
| OR-Transformer                   | **Constructed but unused** in joint LLM+PRICE: `PRICEEmbedder` skips it; only `RegressionModel.forward` (PRICE-only path) calls it | Wired into the joint path; always run (degenerate at K=1); feeds Stat-core ↔ QRT cross-attn |
| QRT (residual text)              | **Not present** — residual is dropped | NEW: tokenizer + embedding lookup only                    |
| Stat-core ↔ QRT cross-attn       | **Not present**                      | NEW: transformer block fusing stat-core CLS with QRT      |
| Plan ↔ Query cross-attn          | LLM ↔ PRICE-summary (length-1) cross-attn | LLM-plan tokens ↔ unified `h_query` token sequence    |
| Final pooling + MLP              | CLS+L2norm of fused LLM, concat with PRICE | CLS pool of joint output → MLP                       |

### Open design questions

- **D_stat vs. D_llm**: Should `stat_core` and `h_plan` share the
  same hidden dim (so cross-attn is dim-matched without projection),
  or keep `D_stat=512`/`384` and add input projections at every
  cross-attn boundary? Defaulting to `D_stat = D_llm` simplifies
  shapes.
- **CLS-only vs. full sequence at OR-Transformer output**: User
  notes "I think at this point we can just use their CLS tokens,
  not the whole sequence" — adopting that. If we ever need richer
  per-clause information downstream, switch to full-sequence.
- **QRT length budget**: residual fragments per query can vary
  widely. Per-query truncation policy + padding mask convention
  must align with cross-attn masks.
- **N layers for plan↔query cross-attn**: keep the current
  `--n_cross_layers` knob (4 default).

---

## 11. Comparison with PRICE_S and PRICE_M

| Capability | base PRICE | PRICE_S | PRICE_M | PRICE_N |
|---|:---:|:---:|:---:|:---:|
| Equi-joins | ✓ | ✓ | ✓ | ✓ |
| Range filters | ✓ | ✓ | ✓ | ✓ |
| EQ on discrete (SpaceSaving) | ✓ | ✓ | ✓ | ✓ |
| IN-list (literal) | drop | bounding-box | 10 ranges | 10 IN-slots + tail (rule a) |
| LIKE / NOT LIKE | drop | SpaceSaving match | SpaceSaving match | residual |
| BETWEEN | range | range | range | range |
| IS NULL / IS NOT NULL | drop | drop | drop | dedicated bits (rule b) |
| Date / timestamp literals | mostly works | mostly works | mostly works | normalized to epoch (rule c) |
| Date arithmetic cross-row | drop | drop | drop | pairwise token (rule d) |
| Disjoint OR → IN-list rewrite | none | none | none | yes (rule e) |
| Cyclic equi-join graph | rejects query | rejects query | rejects query | accepts (rule f) |
| Outer joins (LEFT/RIGHT/FULL) | inner-joined | inner-joined | inner-joined | preserve flag + orphan (rule g) |
| Cross-table non-equi (whitelisted) | drop | drop | drop | xtab 2D histogram (rule h) |
| NOT push-down → NNF | none | none | none | yes (rule i) |
| Same-table col-op-col | drop | drop | drop | pairwise token (rule j) |
| Subquery inlining | best-effort | best-effort | best-effort | simple-body only |
| EXISTS / IN(subq) / scalar | inlined | inlined | inlined | residual |
| Multi-clause DNF (mixed-column OR) | residual | residual | residual | per-clause encoding + OR Transformer aggregator (`--price_n_or`) |
| Range filter on discrete column (`col < 'string'`) | drop | drop | drop | **lex-order range slot (top-39 contribution; OtHeRs dropped)** |

Filter dim: 43 (base / S) → 61 (M) → 75 (N).
Fanout dim: 40 (base / S / M) → 42 (N).
Pairwise intra dim: 0 (base / S / M) → 70 (N, anti-diagonal range-slot format).
New token type count: 4 (base / S / M) → 5 (N).
Encoder stages: 2 (base / S / M: scale + filter) → 3 (N: scale + filter + OR).

---

## 12. Empirical scope

Per the per-template analysis ([INDEX.md](price_n_query_analysis/INDEX.md)),
across all 121 TPC-H + TPC-DS templates:

- **22 / 22 TPC-H templates** parse cleanly under PRICE_N.
- **99 / 99 TPC-DS templates** parse cleanly.
- IMDB JOB-full and JOB-M: rule f alone (cyclic-join-check removal)
  rescues ~111 / 113 JOB-full and ~108 / 226 JOB-M queries that base / S /
  M reject outright.

Templates exercising specific rules:
- Rule c (date literals): TPC-H q1, q3, q4, q5, q6, q7, q8, q10, q12, q14, q15, q20, q22; many TPC-DS templates.
- Rule f (cyclic joins): all of IMDB JOB.
- Rule g (outer joins): TPC-H q13; TPC-DS q5, q40, q49, q72, q75, q77, q78, q80, q93.
- Rule h (xtab non-equi): TPC-DS q72.
- Rule j (col-op-col): TPC-H q4, q12, q21; TPC-DS q46, q64, q68.

Templates that exercise the residual path heavily:
- TPC-H q21: EXISTS + NOT EXISTS + col-op-col combination.
- TPC-DS q4, q11, q23, q74: 3-branch UNION CTEs.
- TPC-DS q77, q80: multi-CTE all-non-simple → entire query goes to residual.

---

## 13. References

- [Original hybrid design](hybrid_price_llm_sql_representation_updated.md) — full architectural rationale, including OR aggregator Transformer, query-block boundary semantics, and the QueryFormer-style fusion that PRICE_N's residuals feed into (out of scope for this implementation).
- [Implementation spec](superpowers/specs/2026-05-02-price-n-parsing-rules-design.md) — exact token formats, file layouts, and code-level integration points.
- [Implementation plan](superpowers/plans/2026-05-02-price-n-parsing-rules.md) — 25-task TDD breakdown with tests per task.
- [Per-template analysis](price_n_query_analysis/INDEX.md) — what every TPC-H/DS query looks like as PRICE input + LLM residual.
- [Subquery inlining guide](price_n_query_analysis/SUBQUERY_INLINING.md) — when subqueries get inlined and when they don't, with the simple-body rule and the LIKE policy.
- [TPC-H/DS predicate audit](tpch_tpcds_predicate_audit.md) — the empirical survey that motivated the rule set.

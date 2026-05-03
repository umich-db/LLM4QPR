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

## 3. Four orthogonal CLI flags

PRICE_N's parsing rules and structural changes are independently
controllable, so a user can mix-and-match with PRICE_S / PRICE_M:

| Flag | What it enables | Default |
|---|---|---|
| `--price_n_parsing` | Pre-processor rewrites: NOT push-down (NNF), disjoint-OR → IN-list, date / timestamp literal normalization, atom tagging for new token types | off |
| `--price_n_filter` | 75-dim filter token (10 IN-list slots + tail bucket + null bits). Mutually exclusive with `--price_s`, `--price_m` | off |
| `--price_n_fanout` | 42-dim fanout token (orphan fraction + outer-join preserve flag) | off |
| `--price_n_pairwise` | 5th token type: 129-dim pairwise intra-table filter (same-table column comparisons + cross-table whitelist) | off |
| `--price_n` | Convenience shorthand: enables all four above | off |

Useful combinations:
- `--price_n` — full PRICE_N.
- `--price_n_parsing` alone — get the parser improvements without changing token shapes (useful for ablation).
- `--price_s --price_n_parsing` — keep PRICE_S filter shape but add NOT push-down, OR→IN, date literals, etc.
- `--price_n_pairwise` alone — add the 5th token type to a base PRICE encoder.

A single mutual-exclusion guard at parse time enforces that at most one of
`{--price_s, --price_m, --price_n_filter}` is set (they all change
filter_dim).

---

## 4. What PRICE encodes statistically

PRICE_N's encoder consumes five token types per query:

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

### 4.5 Pairwise intra-table filter token (129 dims, NEW token type)

Per `A.x op A.y` predicate (same-table column comparison) plus one
whitelisted cross-table case (`inv_quantity_on_hand × cs_quantity` from
TPC-DS q72):
```
[ H_xy 8×8 ordered (64 dims) ]
[ M_op 8×8 mask  (64 dims) ]
[ s_op (1 dim)            ]
```

The 8×8 grid is region-ordered: 28 cells for `x<y`, 8 diagonal cells for
`x≈y`, 28 cells for `x>y`. Each comparison operator selects a region
combination via the mask. For discrete columns (TPC-DS `cd_marital_status`,
`ca_city`), the 2D histogram is computed via the SpaceSaving outer-product
trick, with OtHeRs dropped for high-cardinality columns to avoid diagonal
mass inflation.

---

## 5. SQL pre-processor pipeline

When `--price_n_parsing` is on, the AST passes through 9 phases:

1. **Subquery handling** — see §6 below; under PRICE_N, the existing
   inliners are skipped and the subqueries become residuals.
2. **NOT push-down → NNF** (rule i): De Morgan + per-comparator flips +
   `IS NULL` / `IS NOT NULL` swap. After this pass, every `Not` wraps a
   leaf predicate.
3. **Disjoint OR → IN** (rule e): collapses `(c=v1 OR c=v2 OR …)` chains
   on the same column into `c IN (v1, …, vk)`.
4. BETWEEN → `>= AND <=` (existing).
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
- **`FilterEmbedding.pairwise_intra_embeddings`** (new): `Linear(129, n_embd)` for the 5th token type.

Pretrained PRICE checkpoints load with `strict=False` and a partial-copy
helper:
- The first 43 dims of the new 75-dim filter weight match the base PRICE
  layout exactly (`hist[40] + (low, high, sel)` slot 1 = single-equality /
  range case), so the base equi-filter behavior is preserved at init.
- Fanout embedding's first 41 dims match the base layout
  (`hist_sum + raw_hist[40]`); the two new scalars start zero-initialized
  and are trained from labels.
- Pairwise embedding starts fully random.

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

Filter dim: 43 (base / S) → 61 (M) → 75 (N).
Fanout dim: 40 (base / S / M) → 42 (N).
New token type count: 4 (base / S / M) → 5 (N).

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

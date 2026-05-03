# Subquery Inlining in PRICE_N

## Inlining policy (revised)

Under PRICE_N, a subquery (CTE, derived table, or inline subquery) is inlined **iff** its body is a flat conjunctive SELECT over base relations, satisfying all of the following:

- No GROUP BY
- No HAVING
- No DISTINCT
- No window functions
- No ORDER BY+LIMIT combination (ORDER BY alone without LIMIT is allowed)
- Not itself a UNION / INTERSECT / EXCEPT
- No aggregate function calls (`SUM`, `AVG`, `MIN`, `MAX`, `COUNT`) in projections
- Not `WITH RECURSIVE`

Anything else becomes **LLM residual** — the LLM residual encoder receives the textual form of the unconverted fragment, and the downstream fusion Transformer learns to combine it with PRICE's statistical signal.

**Note on NEQ filter encoding**: `col != X` predicates that survive to the flat WHERE clause are encoded as range-pair slots in the filter token (rule a extension) rather than being dropped. See the Filter Atoms section below.

---

## Why inline at all?

PRICE expects a query as a **flat conjunction of supported predicates over base relations**. Its tokenizer (`Sql2FeatureN.create_sql_features`) walks the WHERE clause once and emits filter / join / fanout / table / pairwise tokens. Anything that doesn't fit this shape — a CTE, a UNION branch, a correlated subquery, a CASE expression in a projection — has no representation in PRICE's token stream and must be encoded by the LLM-residual path instead.

A subquery is inlinable when its rows can be folded into the outer query's row scope without changing the predicate semantics in a way PRICE can't recover. When the fold is lossless (or close enough), we get the inner tables and their statistics into PRICE's view; when it isn't, the subquery becomes residual.

---

## Which subquery shapes appear in TPC-H/DS

Empirically, looking across all 121 templates ([INDEX](INDEX.md)):

| Shape | Examples | Frequency |
|---|---|---|
| `EXISTS (SELECT … WHERE …)` | TPC-H q4, q21, q22 | 4 templates |
| `NOT EXISTS (SELECT … WHERE …)` | TPC-H q21 | 1 template |
| `col IN (SELECT col FROM …)` | TPC-DS q14, q23, q41, q49, q60 | 8 templates |
| `col NOT IN (SELECT col FROM …)` | TPC-DS q16, q83 | 2 templates |
| `col op (SELECT AGG(x) FROM …)` (scalar) | TPC-H q2, q11, q15, q17, q20, q22; TPC-DS q1, q9, q24, q30, q32, q41, q81, q92 | 14 templates |
| `WITH name AS (SELECT …)` (CTE) | TPC-H q15; TPC-DS q1, q4, q11, q14, q23, q24, q30, q31, q39, q47, q57, q59, q64, q70, q74 + many | ~25 templates |
| `FROM (SELECT …) alias` (derived table) | TPC-DS q11, q23, q24, q30, q31, q34, q39, q40, q47, q57, q59, q64 + many | ~30 templates |
| `UNION` / `UNION ALL` | TPC-DS q4, q5, q11, q14, q23, q33, q49, q54, q56, q60, q66, q71, q74, q75, q76, q77, q80 | 18 templates |
| `INTERSECT` | TPC-DS q8, q14, q38 | 3 templates |

---

## Subqueries that always go to residual under PRICE_N

### EXISTS / NOT EXISTS

`EXISTS (SELECT … WHERE …)` and `NOT EXISTS (SELECT … WHERE …)` are **never inlined** under PRICE_N. The approximation of treating an anti-join (NOT EXISTS) as an inner join is semantically wrong and causes systematic over-estimation. Even the EXISTS case introduces a semantic loss (the semi-join becomes an inner join). Both are reported as `Exists` / `NotExists` residuals.

**Example (TPC-H q21)**:
- Under the old policy: `lineitem l2` and `lineitem l3` would be inlined into the outer query, and the NEQ / NOT EXISTS negations would be silently dropped.
- Under PRICE_N: the EXISTS and NOT EXISTS are left in place. The transformed SQL has only the outer 4 tables (`supplier`, `lineitem l1`, `orders`, `nation`). The LLM residual encoder sees the subquery text.

### IN(subquery) / NOT IN(subquery)

`col IN (SELECT col FROM B WHERE …)` and `col NOT IN (SELECT col FROM B WHERE …)` are **never inlined** under PRICE_N. As with EXISTS, treating a semi-join or anti-semi-join as an equi-join loses the set-membership semantics. These are reported as `InSubquery` / `NotInSubquery` residuals.

Note: `col IN (1, 2, 3)` (value-list IN) is **not** affected — it is handled by the filter-token IN-list slot rule (rule a).

### Scalar subqueries

`col op (SELECT AGG(col) FROM B WHERE …)` — where the subquery must return a scalar — are **never inlined or estimated** under PRICE_N. Estimating the aggregate from histogram statistics introduces approximation errors that compound across the outer query's selectivity estimate. These are reported as `ScalarSubquery` residuals.

Templates affected: TPC-H q2, q11, q15, q17, q20, q22; TPC-DS q1, q9, q24, q30, q32, q41, q81, q92.

---

## CTEs and derived tables: simple-body gate

### Simple CTEs (inlined)

A CTE whose body passes the simple-body check (single flat conjunctive SELECT, no aggregates / DISTINCT / GROUP BY / HAVING / window / ORDER+LIMIT / multi-branch / recursion) is inlined by `flatten_sql_for_price_n`. The inner FROM tables and WHERE conditions become part of the outer query.

**Example (TPC-H q15, simplified)**:
```sql
WITH revenue0 AS (
  SELECT l_suppkey, SUM(l_extendedprice * (1 - l_discount)) AS total_revenue
  FROM lineitem WHERE l_shipdate >= date '1996-01-01' AND l_shipdate < date '1996-04-01'
  GROUP BY l_suppkey
)
SELECT s_suppkey FROM supplier, revenue0
WHERE s_suppkey = l_suppkey ...
```

The body of `revenue0` has both GROUP BY and SUM — it **fails** the simple-body check and is reported as `NonSimpleCTE`. The transformed SQL has fewer tables.

### Non-simple CTEs (residual)

CTEs failing the simple-body check are **not inlined** under PRICE_N. They are reported as `NonSimpleCTE` residuals with the reason for failure.

Common failure reasons:
- `has GROUP BY` (TPC-DS q1 `customer_total_return`, TPC-H q15 `revenue0`)
- `has aggregates in projection` (same examples)
- `multi-branch (UNION/INTERSECT/EXCEPT)` (TPC-DS q4 `year_total`)
- `WITH RECURSIVE` (not present in TPC-H/DS but handled)

**Example (TPC-DS q1)**:
The `customer_total_return` CTE has a `GROUP BY sr_customer_sk, sr_store_sk` and a `SUM(sr_fee)` projection — non-simple. Under PRICE_N it becomes residual. The transformed SQL has only the tables from the outer query that reference the CTE by name.

**Example (TPC-DS q4)**:
The `year_total` CTE has 3 UNION ALL branches — non-simple. Nothing is inlined. The transformed SQL may reduce to a very simple base or fail, with the entire query going to LLM residual.

### Derived tables (FROM-clause subqueries)

`FROM (SELECT … FROM B WHERE …) AS alias` — treated the same as CTEs: inlined only if the body is simple. Non-simple derived tables become `DerivedTable` residuals (same as before; the simple-body gate is new).

---

## NEQ filter encoding (rule a extension)

When a `col != X` predicate survives into the flat transformed WHERE clause (which happens for outer-query NEQ predicates, not those inside residualized subqueries), it is encoded as **N+1 range slots** in the filter token:

- The excluded values are sorted by their position in the column's natural ordering (numeric for continuous columns, SpaceSaving frequency-rank for discrete columns).
- N+1 range slots cover the gaps between the exclusions:
  - Below the first excluded value.
  - Between each consecutive pair of excluded values.
  - Above the last excluded value.
- Each slot has `(lo_norm, hi_norm, selectivity)` just like IN-list slots.
- The total selectivity across all slots approximates `1 - sum(sel(x_i)) - null_fraction`.

This applies to both continuous and SpaceSaving-binned discrete columns. Multiple NEQ values naturally produce multiple gaps. No polarity bit is needed — the slot coverage itself represents the "not equal" semantics.

---

## LIKE predicates (always residual)

Under PRICE_N, `col LIKE 'pattern'`, `col NOT LIKE 'pattern'`, `col ILIKE 'pattern'`, and `col NOT ILIKE 'pattern'` are **always classified as LLM residual**, regardless of column type.

**Rationale**: PRICE statistics can only approximate LIKE selectivity by matching the pattern against the column's top-39 SpaceSaving keys, which works well for low-cardinality discrete columns (e.g., TPC-H `p_type` with ~150 distinct values) but degrades sharply for high-cardinality text columns (e.g., IMDB `movie_companies.note` with millions of distinct strings). The signal is too noisy to model uniformly.

**What flows to the LLM residual**: the column reference + the pattern string. The fusion Transformer learns pattern-specific selectivity from training labels — far better positioned than a SpaceSaving top-39 match.

**Templates affected**: TPC-H q2, q9, q13, q14, q16, q20 (all `LIKE` patterns); TPC-DS q91 (the single `hd_buy_potential LIKE '0-500%'` predicate); all IMDB JOB queries (heavy `LIKE` use on `note` columns).

**PRICE_S / PRICE_M parity**: not affected. PRICE_S/M continue to do SpaceSaving-key-matching and emit IN-list / bounding-box filter tokens for LIKE predicates. The change is PRICE_N-specific.

---

## UNION / INTERSECT / EXCEPT

Set operations combine multiple SELECT branches. PRICE is a single-block model: only the **first** branch flows through to feature extraction. The other branches are tracked in `LLM Residual Constructs` as `Union` / `Intersect` / `Except` entries. This behavior is unchanged by the PRICE_N policy revision.

Templates affected: TPC-DS q4, q5, q11, q14, q23, q33, q49, q54, q56, q60, q66, q71, q74, q75, q76, q77, q80 (UNION) and q8, q14, q38 (INTERSECT).

---

## Summary table: inlining decision under PRICE_N

| Subquery shape | PRICE_N | What survives | Residual kind |
|---|:---:|---|---|
| `EXISTS (SELECT … WHERE …)` | ❌ | n/a | `Exists` |
| `NOT EXISTS (SELECT …)` | ❌ | n/a | `NotExists` |
| `col IN (SELECT col FROM …)` | ❌ | n/a | `InSubquery` |
| `col NOT IN (SELECT col FROM …)` | ❌ | n/a | `NotInSubquery` |
| `col op (SELECT AGG(col) FROM …)` scalar | ❌ | n/a | `ScalarSubquery` |
| `WITH name AS (SELECT …)` simple CTE | ✅ | inner FROM + inner filters | — |
| `WITH name AS (SELECT … GROUP BY …)` | ❌ | n/a | `NonSimpleCTE` |
| `WITH name AS (SELECT … UNION SELECT …)` | ❌ | n/a | `NonSimpleCTE` |
| `WITH RECURSIVE name AS (…)` | ❌ | n/a | `NonSimpleCTE` |
| `FROM (SELECT … FROM B) AS alias` simple | ✅ | inner FROM + inner filters | — |
| `FROM (SELECT col, AGG(…) … GROUP BY col)` | ❌ | n/a | `DerivedTable` |
| `UNION` / `INTERSECT` / `EXCEPT` | ⚠ | first branch only | `Union` / `Intersect` / `Except` |
| Subquery in SELECT projection | ❌ | dropped | residual only |
| Subquery in `CASE WHEN` | ❌ | dropped | residual only |
| Subquery with window function inside | ❌ | dropped | residual only |
| `col != X` (flat outer WHERE) | ✅ | range-pair slots in filter token | — |
| `col LIKE 'pattern'` | ❌ | n/a | `LikePredicate` |
| `col NOT LIKE 'pattern'` | ❌ | n/a | `NotLikePredicate` |
| `col ILIKE 'pattern'` | ❌ | n/a | `ILikePredicate` |
| `col NOT ILIKE 'pattern'` | ❌ | n/a | `NotILikePredicate` |

Legend: ✅ inlined/encoded · ⚠ partial (first branch only) · ❌ not inlined; residual.

For base PRICE / PRICE_S / PRICE_M (no `--price_n` flag), the old behavior is preserved: EXISTS and IN(subquery) are inlined with semantic loss, and scalar subqueries are estimated from statistics. Only PRICE_N (`--price_n` or `--price_n_parsing`) applies the stricter residual policy above.

---

## How to read the per-template analysis

In each `tpch/qN.md` and `tpcds/qN.md`:

- The **"Transformed SQL (input to PRICE)"** block shows the final post-inlining SQL that PRICE actually ingests.
- The **"What goes into PRICE"** section lists tables, joins, and atoms produced by the inlining.
- The **"LLM Residual Constructs"** section lists everything that didn't make it through. Under PRICE_N, entries with kind `Exists`, `NotExists`, `InSubquery`, `NotInSubquery`, `ScalarSubquery`, and `NonSimpleCTE` reflect the new stricter policy.
- The **"Predicate Reordering"** section logs which transformations actually fired (NOT push-down, OR→IN, date-literal normalization).
- The **"DNF (post-NNF)"** section shows the WHERE clause as a flat conjunction of atoms (or as multiple clauses if a disjunction survives all rewrites).

---

*See also: [INDEX.md](INDEX.md) for the per-template summary table, and the PRICE_N design spec for the boundary rules between statistics-grounded core and LLM residual.*

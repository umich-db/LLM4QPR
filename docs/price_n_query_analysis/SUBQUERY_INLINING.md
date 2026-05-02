# Subquery Inlining in PRICE_N

## Why inline at all?

PRICE expects a query as a **flat conjunction of supported predicates over base relations**. Its tokenizer (`Sql2FeatureN.create_sql_features`) walks the WHERE clause once and emits filter / join / fanout / table / pairwise tokens. Anything that doesn't fit this shape — a CTE, a UNION branch, a correlated subquery, a CASE expression in a projection — has no representation in PRICE's token stream and must be encoded by the LLM-residual path instead.

A subquery is "inlinable" when its rows can be folded into the outer query's row scope without changing the predicate's semantics in a way PRICE can't recover. When the fold is lossless (or close enough), we get the inner tables and their statistics into PRICE's view; when it isn't, the subquery becomes residual.

This document explains which subquery shapes get inlined, which get estimated to scalars, which get rewritten to tautologies, and which get pushed entirely to the LLM residual.

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

So most TPC-DS queries trigger at least one form of inlining. The TPC-H templates are simpler (mostly EXISTS or scalar subqueries), and inlining usually succeeds cleanly.

---

## EXISTS / NOT EXISTS

Implementation: `_inline_exists_subqueries` in `experiments/price_data_utils.py:1326`.

### When inlining works

The semantic of `EXISTS (SELECT * FROM B WHERE B.k = A.k AND B.x = 5)` is "for at least one row in B that matches the join condition and the local filter, the outer A row is kept." For PRICE's purposes, this is equivalent to **`A INNER JOIN B ON A.k = B.k WHERE B.x = 5`** at the cardinality estimation level — both produce the same set of A keys. We can absorb B's tables and predicates into the outer query.

What survives the inlining:
- The inner FROM tables → appended to the outer FROM clause.
- The inner WHERE conditions, **filtered to the supported atom kinds**:
  - Equi-joins (`A.k = B.k`) — preserved as outer joins.
  - Range comparisons (`B.col < 100`, `>=`, `<=`, `>`) — preserved as outer filter atoms.

What gets dropped:
- `B.col != X` (NEQ) — silently dropped.
- `B.col LIKE 'pat'` — silently dropped.
- Nested `NOT (...)`, complex expressions, function calls — silently dropped.

If everything in the inner WHERE gets dropped, the EXISTS replacement is just `1 = 1` (tautology) — the inner tables still join in, but no filter constraint propagates.

**Example (TPC-H q21)**:

Raw:
```sql
SELECT s_name FROM supplier, lineitem l1, orders, nation
WHERE s_suppkey = l1.l_suppkey
  AND o_orderkey = l1.l_orderkey
  AND l1.l_receiptdate > l1.l_commitdate
  AND EXISTS (
    SELECT * FROM lineitem l2
    WHERE l2.l_orderkey = l1.l_orderkey
      AND l2.l_suppkey <> l1.l_suppkey
  )
  ...
```

After inlining: `lineitem l2` joins in via `l2.l_orderkey = l1.l_orderkey` (equi-join, preserved); the `l2.l_suppkey != l1.l_suppkey` NEQ is dropped. PRICE sees one extra `lineitem` row scope without the anti-join discrimination — a known approximation.

### When inlining loses fidelity

`NOT EXISTS` is treated identically to `EXISTS` by the inliner — the negation is **silently dropped**. This is wrong in general (NOT EXISTS is an anti-join, not an inner join), but PRICE has no way to express anti-join semantics in its token stream, so this is the least-bad option. The cardinality estimate may overshoot.

Templates where this matters:
- TPC-H q21 has both `EXISTS` (correct as inner-join under our approximation) and `NOT EXISTS` (silently degraded to inner-join). The actual row count from the NOT-EXISTS branch is *much* smaller than what PRICE will compute.

### When inlining can't run at all

A few EXISTS shapes return a tautology unconditionally:
- The inner block isn't a `SELECT` (some sqlglot edge cases on parser-introduced wrappers).
- The inner WHERE is missing entirely (rare).

In those cases, the EXISTS predicate becomes `1=1` and contributes no information at all.

---

## IN (subquery) / NOT IN (subquery)

Implementation: `_inline_in_subqueries` in `experiments/price_data_utils.py:1379`.

`col IN (SELECT inner_col FROM B WHERE …)` is semantically equivalent to a semi-join: keep outer rows whose `col` matches the projection of the inner block. PRICE handles this by:

1. Adding the inner FROM tables to the outer query.
2. Creating an equi-join `outer_col = inner_col` on the projected column.
3. Keeping the inner WHERE conditions (same filter as EXISTS — only EQ / LT / LTE / GT / GTE survive).

### When it works

Standard `IN (SELECT single_col FROM B WHERE …)` shapes inline cleanly. The result is a normal multi-table query that PRICE handles fine.

**Example (TPC-DS q14, simplified)**:
```sql
SELECT … FROM store_sales
WHERE ss_item_sk IN (SELECT ss_item_sk FROM cross_items)
```
becomes:
```sql
SELECT count(*) FROM store_sales, cross_items
WHERE store_sales.ss_item_sk = cross_items.ss_item_sk
```

### When it doesn't

- **`NOT IN (subquery)`** is treated identically to `IN`. Same caveat as `NOT EXISTS` — semantically wrong (anti-semi-join), but the alternative is total residual.
- **Multi-column IN** (`(a, b) IN (SELECT x, y …)`): the inliner only uses the first projection column, so it generates `outer_a = inner_x` but loses the `b = y` constraint. Selectivity over-estimates.
- **`IN (value_list)`** (`col IN (1, 2, 3)`): NOT inlined — this is a literal IN, handled by the filter-token IN-list slot rule (rule a, see [spec §7.5](../superpowers/specs/2026-05-02-price-n-parsing-rules-design.md)).
- **Inner subquery has GROUP BY / DISTINCT / aggregates**: the projected inner column is the result of an aggregate, which can't equate to a base-relation column. The inliner still rewrites it but the equi-join is meaningless.

---

## Scalar subqueries

Implementation: `_estimate_scalar_subqueries` in `experiments/price_data_utils.py:1439`.

A scalar subquery is `outer_col OP (SELECT AGG(col) FROM B WHERE …)` — it must return exactly one row and one column. Common in TPC-H q2, q11, q15, q17, q20, q22 (the "above average …" idiom).

PRICE doesn't keep the subquery; instead it tries to **estimate the scalar value** from base-relation statistics and replace the subquery with a numeric literal.

### Recognized aggregate patterns

The inliner extracts `(multiplier, agg_func, col)` from the inner SELECT for the following shapes:

| Pattern | Example | multiplier |
|---|---|---|
| `AGG(col)` | `SELECT AVG(price) FROM orders` | 1.0 |
| `mult * AGG(col)` | `SELECT 0.2 * SUM(qty) FROM lineitem` | 0.2 |
| `AGG(col) * mult` | `SELECT SUM(qty) * 0.2 FROM lineitem` | 0.2 |

Aggregates: `MIN`, `MAX`, `AVG`, `SUM`, `COUNT`.

The inner table's PRICE statistics (histogram, summary, size) are queried to compute an estimate:
- `MIN(col)` ≈ first bin edge of the histogram.
- `MAX(col)` ≈ last bin edge.
- `AVG(col)` ≈ histogram-weighted mean.
- `SUM(col)` ≈ AVG × table size.
- `COUNT(col)` ≈ table size − null count.

The outer comparison `outer_col > (subq)` becomes `outer_col > <estimated_literal>`. The inner FROM tables and any correlated EQ/range conditions are also added to the outer query (so any join between outer and inner survives).

### When estimation works

- TPC-H q2: `p_size = (SELECT MIN(p_size) FROM part WHERE p_type = 'BRASS')` → `p_size = <min_p_size>`. PRICE uses the histogram min as an estimate. Reasonable cardinality.
- TPC-H q17: `l_quantity < 0.2 * (SELECT AVG(l_quantity) FROM lineitem WHERE l_partkey = p_partkey)` → `l_quantity < 0.2 * <avg_l_quantity>`. The `l_partkey = p_partkey` correlation is preserved as an outer EQ join.

### When estimation fails

Returns tautology (drops the predicate entirely):
- Inner SELECT projects multiple expressions → can't pick one to estimate.
- Inner expression is not an aggregate (e.g., `(SELECT col FROM B LIMIT 1)`) → no statistical estimate.
- Aggregate over an expression (`SUM(a + b)`) — can't be estimated from per-column stats.
- Database stats not loaded for that column.

Templates that lose predicates this way:
- TPC-DS q92: subquery uses `SUM(ws_ext_discount_amt)` over a subset that can't be cheaply summarized.
- TPC-H q15: scalar subquery references a CTE result; CTE-result stats aren't precomputed.

### Correlation handling

When the inner WHERE references an outer alias (correlated subquery), the EQ/range conditions are cloned into the outer WHERE alongside the inner FROM tables. So `WHERE l_partkey = p_partkey` from inside an inner subquery surfaces in the outer query and PRICE sees it as a normal join condition. NEQ / LIKE / non-EQ correlations don't survive.

---

## CTEs (WITH clauses)

Handled by `flatten_sql_for_price` (the sqlglot-based flattener that runs before `_preprocess_predicates`).

A CTE is a named subquery declared once and referenced by name in the main query. PRICE inlines them by:

1. Locating each `name AS (...)` block.
2. Substituting the name with the body wherever it's referenced.
3. The body's tables, WHERE, and projections become part of the outer query.

### When it works

For "simple" CTEs — single SELECT, base-relation FROM, conjunctive WHERE — the inlining produces a flat query that PRICE can ingest directly.

**Example (TPC-DS q1)**:
```sql
WITH customer_total_return AS (
  SELECT sr_customer_sk, sr_store_sk, SUM(sr_fee) AS ctr_total_return
  FROM store_returns, date_dim
  WHERE sr_returned_date_sk = d_date_sk AND d_year = 2000
  GROUP BY sr_customer_sk, sr_store_sk
)
SELECT c_customer_id FROM customer_total_return ctr1, store, customer
WHERE ctr1.ctr_total_return > (SELECT AVG(ctr_total_return) * 1.2 FROM customer_total_return ctr2 …)
  AND s_store_sk = ctr1.ctr_store_sk
  AND s_state = 'TN'
  AND ctr1.ctr_customer_sk = c_customer_sk
```

Inlining produces `FROM store_returns, date_dim, store, customer WHERE sr_returned_date_sk = d_date_sk AND d_year = 2000 AND s_store_sk = … AND s_state = 'TN' AND sr_customer_sk = c_customer_sk`. PRICE sees 4 tables, 3 joins, 2 filter atoms. The inner GROUP BY is silently dropped (PRICE doesn't model aggregation), but the cardinality of the joined base tables is what matters.

### When it doesn't

- **Multi-branch CTE (UNION)**: only the **first** SELECT branch flows through inlining. Other branches become residual constructs. **TPC-DS q4** is a notable case: its `year_total` CTE has 3 UNION ALL branches; PRICE sees only the store_sales branch, the catalog_sales and web_sales branches go to LLM residual.
- **Recursive CTE** (`WITH RECURSIVE …`): not supported. None appear in TPC-H/DS, but they would fail.
- **CTE referenced multiple times with different aliases** (TPC-DS q4: `t_s_firstyear`, `t_s_secyear`, `t_c_firstyear`, etc.): each alias gets its own copy of the inlined body, multiplying the table count. The transformed SQL ends up with 5 redundant joins on the same `customer.c_customer_id = customer.c_customer_id` self-equality and 18 copies of `d_year = 2001/2002`. Faithful but wasteful.
- **CTE whose body is a complex aggregate**: GROUP BY / HAVING in the body get dropped; the projection becomes whatever the inner SELECT names. If the outer query references those projections in non-trivial ways, the cardinality estimate degrades.

---

## Derived tables (FROM-clause subqueries)

`FROM (SELECT … FROM B WHERE …) AS alias` — same idea as a CTE but inline. `flatten_sql_for_price` handles these by replacing the alias with the inner FROM tables and lifting the inner WHERE.

When the inner subquery is a **plain SELECT over base relations**, this works the same as a CTE inline. When it's an aggregate (`FROM (SELECT col, COUNT(*) FROM B GROUP BY col) AS x`), the alias's projections are aggregate results; the outer query's references to `x.col` and `x.cnt` lose their base-relation grounding.

In the analysis docs, these surface as `**DerivedTable**` residuals. They appear in many TPC-DS queries (q34, q39, q47, q57, q59, q64, …).

---

## UNION / INTERSECT / EXCEPT

Set operations combine multiple SELECT branches. PRICE is a single-block model: only the **first** branch flows through to feature extraction. The other branches are tracked in `LLM Residual Constructs` as `Union` / `Intersect` / `Except` entries with their first-line snippet.

This is a known approximation. The first-branch cardinality often differs from the union'd total by 2-5×. The downstream LLM residual encoder gets the textual representation of the dropped branches and the fusion Transformer can in principle correct the estimate.

Templates affected: TPC-DS q4, q5, q11, q14, q23, q33, q49, q54, q56, q60, q66, q71, q74, q75, q76, q77, q80 (UNION) and q8, q14, q38 (INTERSECT).

---

## What deliberately becomes residual

Even when a subquery shape *could* in principle be inlined, the inliner may decline if it would distort PRICE's token semantics too far:

- **Subquery with LIMIT / OFFSET / ORDER BY**: changes which inner rows participate; can't fold into a flat join.
- **Window functions inside a subquery**: per-partition computations; not a base-relation predicate.
- **Recursive CTE**: unbounded depth.
- **Subquery used in SELECT projection** (e.g., `SELECT col, (SELECT MAX(x) FROM B) AS m FROM A`): the scalar projection is a per-row computation; PRICE doesn't model projections.
- **Subquery inside a CASE WHEN**: nested in a per-row decision; PRICE doesn't see WHERE-CASE either.
- **Subquery comparing tuples** (`(a, b) IN (SELECT x, y …)`): only single-column flavors get inlined.

These all surface as residual. The LLM-residual encoder (see [spec §9](../superpowers/specs/2026-05-02-price-n-parsing-rules-design.md)) gets the textual form and the downstream fusion Transformer learns to combine them with PRICE's statistical signal.

---

## Summary table: inlining decision

| Subquery shape | Inlined? | What survives | Failure mode |
|---|:---:|---|---|
| `EXISTS (SELECT … WHERE EQ/range)` | ✅ | inner FROM + inner EQ/range | NEQ/LIKE in inner WHERE dropped |
| `EXISTS (SELECT …)` empty WHERE | ✅ | inner FROM, no filters | becomes `1=1` |
| `NOT EXISTS (...)` | ⚠ | same as EXISTS | negation silently dropped → over-estimate |
| `col IN (SELECT col FROM …)` | ✅ | semi-join via equi-join + inner filters | non-EQ correlations dropped |
| `col NOT IN (...)` | ⚠ | same as IN | negation silently dropped |
| `(a, b) IN (subq)` | ⚠ | only `a = inner_first_col` | second column constraint lost |
| `col op (SELECT AGG(col) FROM …)` scalar | ✅ | estimated literal + inner FROM + correlations | non-aggregate scalar → tautology |
| `col op (SELECT col FROM … LIMIT 1)` | ❌ | tautology | not an aggregate; can't estimate |
| `WITH name AS (SELECT …)` simple CTE | ✅ | inner FROM + inner filters | aggregates / GROUP BY dropped |
| `WITH name AS (SELECT … UNION SELECT …)` | ⚠ | first branch only | other branches → residual |
| `WITH RECURSIVE name AS (…)` | ❌ | n/a | not supported |
| `FROM (SELECT … FROM B) AS alias` | ✅ | inner FROM + inner filters | aggregate projection → residual |
| `FROM (SELECT col, AGG(...) FROM … GROUP BY col)` | ⚠ | base table inlined, aggregates dropped | cardinality of agg result misestimated |
| `UNION` / `INTERSECT` / `EXCEPT` | ⚠ | first branch only | other branches → residual |
| Subquery in SELECT projection | ❌ | dropped | residual only |
| Subquery in `CASE WHEN` | ❌ | dropped | residual only |
| Subquery with window function inside | ❌ | dropped | residual only |

Legend: ✅ inlined cleanly · ⚠ inlined with semantic loss · ❌ not inlined; residual.

---

## How to read the per-template analysis

In each `tpch/qN.md` and `tpcds/qN.md`:

- The **"Transformed SQL (input to PRICE)"** block shows the final post-inlining SQL that PRICE actually ingests.
- The **"What goes into PRICE"** section lists tables, joins, and atoms produced by the inlining.
- The **"LLM Residual Constructs"** section lists everything that didn't make it through. Each entry has a kind (CTE, Union, DerivedTable, GroupBy, Aggregates, OrderBy, Limit, ScalarSubquery, etc.) and a snippet.
- The **"Predicate Reordering"** section logs which transformations actually fired (NOT push-down, OR→IN, date-literal normalization).
- The **"DNF (post-NNF)"** section shows the WHERE clause as a flat conjunction of atoms (or as multiple clauses if a disjunction survives all rewrites).

When a query has many residuals or a transformed SQL with self-equalities like `c_customer_id = c_customer_id`, that's a fingerprint of multi-aliased CTE inlining (TPC-DS q4 is the canonical example).

---

*See also: [INDEX.md](INDEX.md) for the per-template summary table, and [the PRICE_N design spec](../superpowers/specs/2026-05-02-price-n-parsing-rules-design.md) §10 for the boundary rules between statistics-grounded core and LLM residual.*

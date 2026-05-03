# PRICE_N Query Analysis — Index

Per-template analysis of TPC-H (22 queries) and TPC-DS (99 queries).
Shows what PRICE can handle vs. what falls to the LLM residual encoder.

## Statistics

- **TPCH**: 22 templates, 22 fully analyzed, 0 with pipeline errors
- **TPCDS**: 99 templates, 99 fully analyzed, 0 with pipeline errors

## TPC-H Queries

| Query | Tables | Joins | Filter cols | Residuals | Status |
|-------|--------|-------|-------------|-----------|--------|
| [q1](tpch/q1.md) | 1 | 0 | 1 | 3 | OK |
| [q2](tpch/q2.md) | 5 | 4 | 2 | 2 | OK |
| [q3](tpch/q3.md) | 3 | 2 | 3 | 3 | OK |
| [q4](tpch/q4.md) | 1 | 0 | 1 | 4 | OK |
| [q5](tpch/q5.md) | 6 | 6 | 2 | 3 | OK |
| [q6](tpch/q6.md) | 1 | 0 | 3 | 1 | OK |
| [q7](tpch/q7.md) | 5 | 5 | 1 | 4 | OK |
| [q8](tpch/q8.md) | 7 | 7 | 3 | 5 | OK |
| [q9](tpch/q9.md) | 6 | 6 | 0 | 4 | OK |
| [q10](tpch/q10.md) | 4 | 3 | 2 | 3 | OK |
| [q11](tpch/q11.md) | 3 | 2 | 1 | 5 | OK |
| [q12](tpch/q12.md) | 2 | 1 | 2 | 5 | OK |
| [q13](tpch/q13.md) | 2 | 1 | 0 | 4 | OK |
| [q14](tpch/q14.md) | 2 | 1 | 1 | 2 | OK |
| [q15](tpch/q15.md) | 2 | 1 | 0 | 2 | OK |
| [q16](tpch/q16.md) | 2 | 1 | 2 | 4 | OK |
| [q17](tpch/q17.md) | 2 | 1 | 2 | 2 | OK |
| [q18](tpch/q18.md) | 3 | 2 | 0 | 5 | OK |
| [q19](tpch/q19.md) | 2 | 1 | 6 | 1 | OK |
| [q20](tpch/q20.md) | 2 | 1 | 1 | 4 | OK |
| [q21](tpch/q21.md) | 4 | 3 | 2 | 5 | OK |
| [q22](tpch/q22.md) | 2 | 1 | 1 | 6 | OK |

## TPC-DS Queries

| Query | Tables | Joins | Filter cols | Residuals | Status |
|-------|--------|-------|-------------|-----------|--------|
| [q1](tpcds/q1.md) | 1 | 0 | 1 | 5 | OK |
| [q2](tpcds/q2.md) | 1 | 0 | 1 | 8 | OK |
| [q3](tpcds/q3.md) | 3 | 2 | 2 | 4 | OK |
| [q4](tpcds/q4.md) | 1 | 0 | 1 | 5 | OK |
| [q5](tpcds/q5.md) | 1 | 0 | 1 | 12 | OK |
| [q6](tpcds/q6.md) | 5 | 4 | 0 | 5 | OK |
| [q7](tpcds/q7.md) | 5 | 4 | 4 | 4 | OK |
| [q8](tpcds/q8.md) | 3 | 2 | 2 | 8 | OK |
| [q9](tpcds/q9.md) | 1 | 0 | 1 | 6 | OK |
| [q10](tpcds/q10.md) | 3 | 2 | 1 | 7 | OK |
| [q11](tpcds/q11.md) | 1 | 0 | 1 | 5 | OK |
| [q12](tpcds/q12.md) | 3 | 2 | 2 | 5 | OK |
| [q13](tpcds/q13.md) | 6 | 2 | 1 | 1 | OK |
| [q14](tpcds/q14.md) | 1 | 0 | 1 | 14 | OK |
| [q15](tpcds/q15.md) | 4 | 3 | 2 | 4 | OK |
| [q16](tpcds/q16.md) | 4 | 3 | 3 | 5 | OK |
| [q17](tpcds/q17.md) | 6 | 10 | 1 | 4 | OK |
| [q18](tpcds/q18.md) | 6 | 6 | 5 | 4 | OK |
| [q19](tpcds/q19.md) | 6 | 5 | 3 | 4 | OK |
| [q20](tpcds/q20.md) | 3 | 2 | 2 | 5 | OK |
| [q21](tpcds/q21.md) | 4 | 3 | 2 | 4 | OK |
| [q22](tpcds/q22.md) | 3 | 2 | 1 | 4 | OK |
| [q23](tpcds/q23.md) | 1 | 0 | 1 | 14 | OK |
| [q24](tpcds/q24.md) | 1 | 0 | 1 | 6 | OK |
| [q25](tpcds/q25.md) | 6 | 10 | 2 | 4 | OK |
| [q26](tpcds/q26.md) | 5 | 4 | 4 | 4 | OK |
| [q27](tpcds/q27.md) | 5 | 4 | 5 | 4 | OK |
| [q28](tpcds/q28.md) | 1 | 0 | 1 | 7 | OK |
| [q29](tpcds/q29.md) | 6 | 10 | 2 | 4 | OK |
| [q30](tpcds/q30.md) | 1 | 0 | 1 | 5 | OK |
| [q31](tpcds/q31.md) | 1 | 0 | 1 | 4 | OK |
| [q32](tpcds/q32.md) | 3 | 2 | 2 | 3 | OK |
| [q33](tpcds/q33.md) | 1 | 0 | 1 | 12 | OK |
| [q34](tpcds/q34.md) | 4 | 3 | 2 | 3 | OK |
| [q35](tpcds/q35.md) | 3 | 2 | 0 | 7 | OK |
| [q36](tpcds/q36.md) | 4 | 3 | 2 | 6 | OK |
| [q37](tpcds/q37.md) | 4 | 3 | 4 | 3 | OK |
| [q38](tpcds/q38.md) | 5 | 6 | 1 | 3 | OK |
| [q39](tpcds/q39.md) | 4 | 3 | 2 | 4 | OK |
| [q40](tpcds/q40.md) | 5 | 5 | 2 | 6 | OK |
| [q41](tpcds/q41.md) | 1 | 0 | 1 | 2 | OK |
| [q42](tpcds/q42.md) | 3 | 2 | 3 | 4 | OK |
| [q43](tpcds/q43.md) | 3 | 2 | 1 | 11 | OK |
| [q44](tpcds/q44.md) | 1 | 0 | 1 | 11 | OK |
| [q45](tpcds/q45.md) | 5 | 4 | 2 | 5 | OK |
| [q46](tpcds/q46.md) | 5 | 4 | 2 | 4 | OK |
| [q47](tpcds/q47.md) | 1 | 0 | 1 | 6 | OK |
| [q48](tpcds/q48.md) | 5 | 2 | 1 | 1 | OK |
| [q49](tpcds/q49.md) | 7 | 9 | 14 | 12 | OK |
| [q50](tpcds/q50.md) | 4 | 6 | 2 | 9 | OK |
| [q51](tpcds/q51.md) | 1 | 0 | 1 | 8 | OK |
| [q52](tpcds/q52.md) | 3 | 2 | 3 | 4 | OK |
| [q53](tpcds/q53.md) | 4 | 3 | 0 | 5 | OK |
| [q54](tpcds/q54.md) | 1 | 0 | 1 | 9 | OK |
| [q55](tpcds/q55.md) | 3 | 2 | 3 | 4 | OK |
| [q56](tpcds/q56.md) | 1 | 0 | 1 | 12 | OK |
| [q57](tpcds/q57.md) | 1 | 0 | 1 | 6 | OK |
| [q58](tpcds/q58.md) | 1 | 0 | 1 | 9 | OK |
| [q59](tpcds/q59.md) | 1 | 0 | 1 | 6 | OK |
| [q60](tpcds/q60.md) | 1 | 0 | 1 | 12 | OK |
| [q61](tpcds/q61.md) | 7 | 6 | 3 | 4 | OK |
| [q62](tpcds/q62.md) | 5 | 4 | 1 | 9 | OK |
| [q63](tpcds/q63.md) | 4 | 3 | 0 | 5 | OK |
| [q64](tpcds/q64.md) | 1 | 0 | 1 | 5 | OK |
| [q65](tpcds/q65.md) | 2 | 3 | 0 | 6 | OK |
| [q66](tpcds/q66.md) | 6 | 8 | 4 | 6 | OK |
| [q67](tpcds/q67.md) | 4 | 3 | 1 | 6 | OK |
| [q68](tpcds/q68.md) | 5 | 4 | 2 | 4 | OK |
| [q69](tpcds/q69.md) | 3 | 2 | 1 | 7 | OK |
| [q70](tpcds/q70.md) | 3 | 2 | 1 | 8 | OK |
| [q71](tpcds/q71.md) | 2 | 2 | 1 | 5 | OK |
| [q72](tpcds/q72.md) | 9 | 12 | 3 | 6 | OK |
| [q73](tpcds/q73.md) | 4 | 3 | 3 | 3 | OK |
| [q74](tpcds/q74.md) | 1 | 0 | 1 | 5 | OK |
| [q75](tpcds/q75.md) | 1 | 0 | 1 | 6 | OK |
| [q76](tpcds/q76.md) | 5 | 6 | 0 | 6 | OK |
| [q77](tpcds/q77.md) | 1 | 0 | 1 | 12 | OK |
| [q78](tpcds/q78.md) | 1 | 0 | 1 | 6 | OK |
| [q79](tpcds/q79.md) | 4 | 3 | 2 | 4 | OK |
| [q80](tpcds/q80.md) | 1 | 0 | 1 | 9 | OK |
| [q81](tpcds/q81.md) | 1 | 0 | 1 | 5 | OK |
| [q82](tpcds/q82.md) | 4 | 3 | 4 | 3 | OK |
| [q83](tpcds/q83.md) | 1 | 0 | 1 | 12 | OK |
| [q84](tpcds/q84.md) | 6 | 5 | 3 | 2 | OK |
| [q85](tpcds/q85.md) | 7 | 8 | 1 | 4 | OK |
| [q86](tpcds/q86.md) | 3 | 2 | 1 | 6 | OK |
| [q87](tpcds/q87.md) | 5 | 6 | 1 | 2 | OK |
| [q88](tpcds/q88.md) | 4 | 3 | 3 | 8 | OK |
| [q89](tpcds/q89.md) | 4 | 3 | 1 | 5 | OK |
| [q90](tpcds/q90.md) | 4 | 3 | 3 | 4 | OK |
| [q91](tpcds/q91.md) | 7 | 6 | 2 | 3 | OK |
| [q92](tpcds/q92.md) | 3 | 2 | 2 | 4 | OK |
| [q93](tpcds/q93.md) | 3 | 3 | 1 | 5 | OK |
| [q94](tpcds/q94.md) | 4 | 3 | 3 | 5 | OK |
| [q95](tpcds/q95.md) | 4 | 3 | 3 | 6 | OK |
| [q96](tpcds/q96.md) | 4 | 3 | 4 | 3 | OK |
| [q97](tpcds/q97.md) | 1 | 0 | 1 | 8 | OK |
| [q98](tpcds/q98.md) | 3 | 2 | 2 | 4 | OK |
| [q99](tpcds/q99.md) | 5 | 4 | 1 | 9 | OK |

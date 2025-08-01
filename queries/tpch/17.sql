EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice) / 7.0 as avg_yearly from lineitem, part where p_partkey = l_partkey and p_brand = 'Brand#12' and p_container = 'SM BAG' and l_quantity < ( select 0.2 * avg(l_quantity) from lineitem where l_partkey = p_partkey );
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice) / 7.0 as avg_yearly from lineitem, part where p_partkey = l_partkey and p_brand = 'Brand#14' and p_container = 'SM PKG' and l_quantity < ( select 0.2 * avg(l_quantity) from lineitem where l_partkey = p_partkey );
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice) / 7.0 as avg_yearly from lineitem, part where p_partkey = l_partkey and p_brand = 'Brand#11' and p_container = 'LG CASE' and l_quantity < ( select 0.2 * avg(l_quantity) from lineitem where l_partkey = p_partkey );
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice) / 7.0 as avg_yearly from lineitem, part where p_partkey = l_partkey and p_brand = 'Brand#13' and p_container = 'LG BAG' and l_quantity < ( select 0.2 * avg(l_quantity) from lineitem where l_partkey = p_partkey );
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice) / 7.0 as avg_yearly from lineitem, part where p_partkey = l_partkey and p_brand = 'Brand#15' and p_container = 'LG PKG' and l_quantity < ( select 0.2 * avg(l_quantity) from lineitem where l_partkey = p_partkey );
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice) / 7.0 as avg_yearly from lineitem, part where p_partkey = l_partkey and p_brand = 'Brand#12' and p_container = 'MED CASE' and l_quantity < ( select 0.2 * avg(l_quantity) from lineitem where l_partkey = p_partkey );
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice) / 7.0 as avg_yearly from lineitem, part where p_partkey = l_partkey and p_brand = 'Brand#14' and p_container = 'MED BAG' and l_quantity < ( select 0.2 * avg(l_quantity) from lineitem where l_partkey = p_partkey );
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice) / 7.0 as avg_yearly from lineitem, part where p_partkey = l_partkey and p_brand = 'Brand#11' and p_container = 'MED PKG' and l_quantity < ( select 0.2 * avg(l_quantity) from lineitem where l_partkey = p_partkey );
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice) / 7.0 as avg_yearly from lineitem, part where p_partkey = l_partkey and p_brand = 'Brand#13' and p_container = 'JUMBO CASE' and l_quantity < ( select 0.2 * avg(l_quantity) from lineitem where l_partkey = p_partkey );
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice) / 7.0 as avg_yearly from lineitem, part where p_partkey = l_partkey and p_brand = 'Brand#15' and p_container = 'JUMBO BAG' and l_quantity < ( select 0.2 * avg(l_quantity) from lineitem where l_partkey = p_partkey );
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice) / 7.0 as avg_yearly from lineitem, part where p_partkey = l_partkey and p_brand = 'Brand#12' and p_container = 'JUMBO PKG' and l_quantity < ( select 0.2 * avg(l_quantity) from lineitem where l_partkey = p_partkey );
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice) / 7.0 as avg_yearly from lineitem, part where p_partkey = l_partkey and p_brand = 'Brand#14' and p_container = 'WRAP CASE' and l_quantity < ( select 0.2 * avg(l_quantity) from lineitem where l_partkey = p_partkey );
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice) / 7.0 as avg_yearly from lineitem, part where p_partkey = l_partkey and p_brand = 'Brand#15' and p_container = 'WRAP BAG' and l_quantity < ( select 0.2 * avg(l_quantity) from lineitem where l_partkey = p_partkey );
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice) / 7.0 as avg_yearly from lineitem, part where p_partkey = l_partkey and p_brand = 'Brand#12' and p_container = 'WRAP PKG' and l_quantity < ( select 0.2 * avg(l_quantity) from lineitem where l_partkey = p_partkey );
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice) / 7.0 as avg_yearly from lineitem, part where p_partkey = l_partkey and p_brand = 'Brand#14' and p_container = 'SM CASE' and l_quantity < ( select 0.2 * avg(l_quantity) from lineitem where l_partkey = p_partkey );
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice) / 7.0 as avg_yearly from lineitem, part where p_partkey = l_partkey and p_brand = 'Brand#11' and p_container = 'SM BAG' and l_quantity < ( select 0.2 * avg(l_quantity) from lineitem where l_partkey = p_partkey );
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice) / 7.0 as avg_yearly from lineitem, part where p_partkey = l_partkey and p_brand = 'Brand#13' and p_container = 'SM PKG' and l_quantity < ( select 0.2 * avg(l_quantity) from lineitem where l_partkey = p_partkey );
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice) / 7.0 as avg_yearly from lineitem, part where p_partkey = l_partkey and p_brand = 'Brand#15' and p_container = 'LG CASE' and l_quantity < ( select 0.2 * avg(l_quantity) from lineitem where l_partkey = p_partkey );
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice) / 7.0 as avg_yearly from lineitem, part where p_partkey = l_partkey and p_brand = 'Brand#12' and p_container = 'LG BAG' and l_quantity < ( select 0.2 * avg(l_quantity) from lineitem where l_partkey = p_partkey );
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice) / 7.0 as avg_yearly from lineitem, part where p_partkey = l_partkey and p_brand = 'Brand#14' and p_container = 'LG PKG' and l_quantity < ( select 0.2 * avg(l_quantity) from lineitem where l_partkey = p_partkey );
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice) / 7.0 as avg_yearly from lineitem, part where p_partkey = l_partkey and p_brand = 'Brand#11' and p_container = 'MED CASE' and l_quantity < ( select 0.2 * avg(l_quantity) from lineitem where l_partkey = p_partkey );
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice) / 7.0 as avg_yearly from lineitem, part where p_partkey = l_partkey and p_brand = 'Brand#13' and p_container = 'MED BAG' and l_quantity < ( select 0.2 * avg(l_quantity) from lineitem where l_partkey = p_partkey );
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice) / 7.0 as avg_yearly from lineitem, part where p_partkey = l_partkey and p_brand = 'Brand#15' and p_container = 'MED PKG' and l_quantity < ( select 0.2 * avg(l_quantity) from lineitem where l_partkey = p_partkey );
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice) / 7.0 as avg_yearly from lineitem, part where p_partkey = l_partkey and p_brand = 'Brand#12' and p_container = 'JUMBO CASE' and l_quantity < ( select 0.2 * avg(l_quantity) from lineitem where l_partkey = p_partkey );
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice) / 7.0 as avg_yearly from lineitem, part where p_partkey = l_partkey and p_brand = 'Brand#13' and p_container = 'JUMBO BAG' and l_quantity < ( select 0.2 * avg(l_quantity) from lineitem where l_partkey = p_partkey );
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice) / 7.0 as avg_yearly from lineitem, part where p_partkey = l_partkey and p_brand = 'Brand#25' and p_container = 'JUMBO PKG' and l_quantity < ( select 0.2 * avg(l_quantity) from lineitem where l_partkey = p_partkey );
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice) / 7.0 as avg_yearly from lineitem, part where p_partkey = l_partkey and p_brand = 'Brand#22' and p_container = 'WRAP CASE' and l_quantity < ( select 0.2 * avg(l_quantity) from lineitem where l_partkey = p_partkey );
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice) / 7.0 as avg_yearly from lineitem, part where p_partkey = l_partkey and p_brand = 'Brand#24' and p_container = 'WRAP BAG' and l_quantity < ( select 0.2 * avg(l_quantity) from lineitem where l_partkey = p_partkey );
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice) / 7.0 as avg_yearly from lineitem, part where p_partkey = l_partkey and p_brand = 'Brand#21' and p_container = 'WRAP PKG' and l_quantity < ( select 0.2 * avg(l_quantity) from lineitem where l_partkey = p_partkey );
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice) / 7.0 as avg_yearly from lineitem, part where p_partkey = l_partkey and p_brand = 'Brand#23' and p_container = 'SM CASE' and l_quantity < ( select 0.2 * avg(l_quantity) from lineitem where l_partkey = p_partkey );
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice) / 7.0 as avg_yearly from lineitem, part where p_partkey = l_partkey and p_brand = 'Brand#25' and p_container = 'SM BAG' and l_quantity < ( select 0.2 * avg(l_quantity) from lineitem where l_partkey = p_partkey );
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice) / 7.0 as avg_yearly from lineitem, part where p_partkey = l_partkey and p_brand = 'Brand#22' and p_container = 'SM PKG' and l_quantity < ( select 0.2 * avg(l_quantity) from lineitem where l_partkey = p_partkey );
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice) / 7.0 as avg_yearly from lineitem, part where p_partkey = l_partkey and p_brand = 'Brand#24' and p_container = 'LG CASE' and l_quantity < ( select 0.2 * avg(l_quantity) from lineitem where l_partkey = p_partkey );
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice) / 7.0 as avg_yearly from lineitem, part where p_partkey = l_partkey and p_brand = 'Brand#21' and p_container = 'LG BAG' and l_quantity < ( select 0.2 * avg(l_quantity) from lineitem where l_partkey = p_partkey );
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice) / 7.0 as avg_yearly from lineitem, part where p_partkey = l_partkey and p_brand = 'Brand#23' and p_container = 'LG PKG' and l_quantity < ( select 0.2 * avg(l_quantity) from lineitem where l_partkey = p_partkey );
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice) / 7.0 as avg_yearly from lineitem, part where p_partkey = l_partkey and p_brand = 'Brand#25' and p_container = 'MED CASE' and l_quantity < ( select 0.2 * avg(l_quantity) from lineitem where l_partkey = p_partkey );
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice) / 7.0 as avg_yearly from lineitem, part where p_partkey = l_partkey and p_brand = 'Brand#21' and p_container = 'MED BAG' and l_quantity < ( select 0.2 * avg(l_quantity) from lineitem where l_partkey = p_partkey );
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice) / 7.0 as avg_yearly from lineitem, part where p_partkey = l_partkey and p_brand = 'Brand#23' and p_container = 'MED PKG' and l_quantity < ( select 0.2 * avg(l_quantity) from lineitem where l_partkey = p_partkey );
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice) / 7.0 as avg_yearly from lineitem, part where p_partkey = l_partkey and p_brand = 'Brand#25' and p_container = 'JUMBO CASE' and l_quantity < ( select 0.2 * avg(l_quantity) from lineitem where l_partkey = p_partkey );
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice) / 7.0 as avg_yearly from lineitem, part where p_partkey = l_partkey and p_brand = 'Brand#22' and p_container = 'JUMBO BAG' and l_quantity < ( select 0.2 * avg(l_quantity) from lineitem where l_partkey = p_partkey );
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice) / 7.0 as avg_yearly from lineitem, part where p_partkey = l_partkey and p_brand = 'Brand#24' and p_container = 'JUMBO PKG' and l_quantity < ( select 0.2 * avg(l_quantity) from lineitem where l_partkey = p_partkey );
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice) / 7.0 as avg_yearly from lineitem, part where p_partkey = l_partkey and p_brand = 'Brand#21' and p_container = 'WRAP CASE' and l_quantity < ( select 0.2 * avg(l_quantity) from lineitem where l_partkey = p_partkey );
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice) / 7.0 as avg_yearly from lineitem, part where p_partkey = l_partkey and p_brand = 'Brand#23' and p_container = 'WRAP BAG' and l_quantity < ( select 0.2 * avg(l_quantity) from lineitem where l_partkey = p_partkey );
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice) / 7.0 as avg_yearly from lineitem, part where p_partkey = l_partkey and p_brand = 'Brand#25' and p_container = 'WRAP PKG' and l_quantity < ( select 0.2 * avg(l_quantity) from lineitem where l_partkey = p_partkey );
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice) / 7.0 as avg_yearly from lineitem, part where p_partkey = l_partkey and p_brand = 'Brand#22' and p_container = 'SM CASE' and l_quantity < ( select 0.2 * avg(l_quantity) from lineitem where l_partkey = p_partkey );
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice) / 7.0 as avg_yearly from lineitem, part where p_partkey = l_partkey and p_brand = 'Brand#24' and p_container = 'SM BAG' and l_quantity < ( select 0.2 * avg(l_quantity) from lineitem where l_partkey = p_partkey );
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice) / 7.0 as avg_yearly from lineitem, part where p_partkey = l_partkey and p_brand = 'Brand#21' and p_container = 'SM PKG' and l_quantity < ( select 0.2 * avg(l_quantity) from lineitem where l_partkey = p_partkey );
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice) / 7.0 as avg_yearly from lineitem, part where p_partkey = l_partkey and p_brand = 'Brand#23' and p_container = 'LG CASE' and l_quantity < ( select 0.2 * avg(l_quantity) from lineitem where l_partkey = p_partkey );
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice) / 7.0 as avg_yearly from lineitem, part where p_partkey = l_partkey and p_brand = 'Brand#24' and p_container = 'LG JAR' and l_quantity < ( select 0.2 * avg(l_quantity) from lineitem where l_partkey = p_partkey );
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice) / 7.0 as avg_yearly from lineitem, part where p_partkey = l_partkey and p_brand = 'Brand#21' and p_container = 'LG PKG' and l_quantity < ( select 0.2 * avg(l_quantity) from lineitem where l_partkey = p_partkey );
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice) / 7.0 as avg_yearly from lineitem, part where p_partkey = l_partkey and p_brand = 'Brand#23' and p_container = 'MED CASE' and l_quantity < ( select 0.2 * avg(l_quantity) from lineitem where l_partkey = p_partkey );
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice) / 7.0 as avg_yearly from lineitem, part where p_partkey = l_partkey and p_brand = 'Brand#35' and p_container = 'MED JAR' and l_quantity < ( select 0.2 * avg(l_quantity) from lineitem where l_partkey = p_partkey );
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice) / 7.0 as avg_yearly from lineitem, part where p_partkey = l_partkey and p_brand = 'Brand#32' and p_container = 'MED PKG' and l_quantity < ( select 0.2 * avg(l_quantity) from lineitem where l_partkey = p_partkey );
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice) / 7.0 as avg_yearly from lineitem, part where p_partkey = l_partkey and p_brand = 'Brand#34' and p_container = 'JUMBO CASE' and l_quantity < ( select 0.2 * avg(l_quantity) from lineitem where l_partkey = p_partkey );
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice) / 7.0 as avg_yearly from lineitem, part where p_partkey = l_partkey and p_brand = 'Brand#31' and p_container = 'JUMBO JAR' and l_quantity < ( select 0.2 * avg(l_quantity) from lineitem where l_partkey = p_partkey );
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice) / 7.0 as avg_yearly from lineitem, part where p_partkey = l_partkey and p_brand = 'Brand#33' and p_container = 'JUMBO PKG' and l_quantity < ( select 0.2 * avg(l_quantity) from lineitem where l_partkey = p_partkey );
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice) / 7.0 as avg_yearly from lineitem, part where p_partkey = l_partkey and p_brand = 'Brand#35' and p_container = 'WRAP CASE' and l_quantity < ( select 0.2 * avg(l_quantity) from lineitem where l_partkey = p_partkey );
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice) / 7.0 as avg_yearly from lineitem, part where p_partkey = l_partkey and p_brand = 'Brand#32' and p_container = 'WRAP JAR' and l_quantity < ( select 0.2 * avg(l_quantity) from lineitem where l_partkey = p_partkey );
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice) / 7.0 as avg_yearly from lineitem, part where p_partkey = l_partkey and p_brand = 'Brand#34' and p_container = 'WRAP PKG' and l_quantity < ( select 0.2 * avg(l_quantity) from lineitem where l_partkey = p_partkey );
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice) / 7.0 as avg_yearly from lineitem, part where p_partkey = l_partkey and p_brand = 'Brand#31' and p_container = 'SM CASE' and l_quantity < ( select 0.2 * avg(l_quantity) from lineitem where l_partkey = p_partkey );
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice) / 7.0 as avg_yearly from lineitem, part where p_partkey = l_partkey and p_brand = 'Brand#32' and p_container = 'SM JAR' and l_quantity < ( select 0.2 * avg(l_quantity) from lineitem where l_partkey = p_partkey );
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice) / 7.0 as avg_yearly from lineitem, part where p_partkey = l_partkey and p_brand = 'Brand#34' and p_container = 'SM PKG' and l_quantity < ( select 0.2 * avg(l_quantity) from lineitem where l_partkey = p_partkey );
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice) / 7.0 as avg_yearly from lineitem, part where p_partkey = l_partkey and p_brand = 'Brand#31' and p_container = 'LG CASE' and l_quantity < ( select 0.2 * avg(l_quantity) from lineitem where l_partkey = p_partkey );
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice) / 7.0 as avg_yearly from lineitem, part where p_partkey = l_partkey and p_brand = 'Brand#33' and p_container = 'LG JAR' and l_quantity < ( select 0.2 * avg(l_quantity) from lineitem where l_partkey = p_partkey );
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice) / 7.0 as avg_yearly from lineitem, part where p_partkey = l_partkey and p_brand = 'Brand#35' and p_container = 'LG PKG' and l_quantity < ( select 0.2 * avg(l_quantity) from lineitem where l_partkey = p_partkey );
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice) / 7.0 as avg_yearly from lineitem, part where p_partkey = l_partkey and p_brand = 'Brand#32' and p_container = 'MED CASE' and l_quantity < ( select 0.2 * avg(l_quantity) from lineitem where l_partkey = p_partkey );
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice) / 7.0 as avg_yearly from lineitem, part where p_partkey = l_partkey and p_brand = 'Brand#34' and p_container = 'MED JAR' and l_quantity < ( select 0.2 * avg(l_quantity) from lineitem where l_partkey = p_partkey );
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice) / 7.0 as avg_yearly from lineitem, part where p_partkey = l_partkey and p_brand = 'Brand#31' and p_container = 'MED PKG' and l_quantity < ( select 0.2 * avg(l_quantity) from lineitem where l_partkey = p_partkey );
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice) / 7.0 as avg_yearly from lineitem, part where p_partkey = l_partkey and p_brand = 'Brand#33' and p_container = 'JUMBO CASE' and l_quantity < ( select 0.2 * avg(l_quantity) from lineitem where l_partkey = p_partkey );
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice) / 7.0 as avg_yearly from lineitem, part where p_partkey = l_partkey and p_brand = 'Brand#35' and p_container = 'JUMBO JAR' and l_quantity < ( select 0.2 * avg(l_quantity) from lineitem where l_partkey = p_partkey );
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice) / 7.0 as avg_yearly from lineitem, part where p_partkey = l_partkey and p_brand = 'Brand#32' and p_container = 'JUMBO PKG' and l_quantity < ( select 0.2 * avg(l_quantity) from lineitem where l_partkey = p_partkey );
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice) / 7.0 as avg_yearly from lineitem, part where p_partkey = l_partkey and p_brand = 'Brand#34' and p_container = 'WRAP CASE' and l_quantity < ( select 0.2 * avg(l_quantity) from lineitem where l_partkey = p_partkey );
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice) / 7.0 as avg_yearly from lineitem, part where p_partkey = l_partkey and p_brand = 'Brand#35' and p_container = 'WRAP JAR' and l_quantity < ( select 0.2 * avg(l_quantity) from lineitem where l_partkey = p_partkey );
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice) / 7.0 as avg_yearly from lineitem, part where p_partkey = l_partkey and p_brand = 'Brand#32' and p_container = 'WRAP PKG' and l_quantity < ( select 0.2 * avg(l_quantity) from lineitem where l_partkey = p_partkey );
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice) / 7.0 as avg_yearly from lineitem, part where p_partkey = l_partkey and p_brand = 'Brand#34' and p_container = 'SM CASE' and l_quantity < ( select 0.2 * avg(l_quantity) from lineitem where l_partkey = p_partkey );
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice) / 7.0 as avg_yearly from lineitem, part where p_partkey = l_partkey and p_brand = 'Brand#31' and p_container = 'SM JAR' and l_quantity < ( select 0.2 * avg(l_quantity) from lineitem where l_partkey = p_partkey );
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice) / 7.0 as avg_yearly from lineitem, part where p_partkey = l_partkey and p_brand = 'Brand#33' and p_container = 'SM PKG' and l_quantity < ( select 0.2 * avg(l_quantity) from lineitem where l_partkey = p_partkey );
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice) / 7.0 as avg_yearly from lineitem, part where p_partkey = l_partkey and p_brand = 'Brand#45' and p_container = 'LG CASE' and l_quantity < ( select 0.2 * avg(l_quantity) from lineitem where l_partkey = p_partkey );
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice) / 7.0 as avg_yearly from lineitem, part where p_partkey = l_partkey and p_brand = 'Brand#42' and p_container = 'LG JAR' and l_quantity < ( select 0.2 * avg(l_quantity) from lineitem where l_partkey = p_partkey );
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice) / 7.0 as avg_yearly from lineitem, part where p_partkey = l_partkey and p_brand = 'Brand#44' and p_container = 'LG PKG' and l_quantity < ( select 0.2 * avg(l_quantity) from lineitem where l_partkey = p_partkey );
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice) / 7.0 as avg_yearly from lineitem, part where p_partkey = l_partkey and p_brand = 'Brand#41' and p_container = 'MED CASE' and l_quantity < ( select 0.2 * avg(l_quantity) from lineitem where l_partkey = p_partkey );
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice) / 7.0 as avg_yearly from lineitem, part where p_partkey = l_partkey and p_brand = 'Brand#43' and p_container = 'MED JAR' and l_quantity < ( select 0.2 * avg(l_quantity) from lineitem where l_partkey = p_partkey );
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice) / 7.0 as avg_yearly from lineitem, part where p_partkey = l_partkey and p_brand = 'Brand#45' and p_container = 'MED PKG' and l_quantity < ( select 0.2 * avg(l_quantity) from lineitem where l_partkey = p_partkey );
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice) / 7.0 as avg_yearly from lineitem, part where p_partkey = l_partkey and p_brand = 'Brand#42' and p_container = 'JUMBO CASE' and l_quantity < ( select 0.2 * avg(l_quantity) from lineitem where l_partkey = p_partkey );
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice) / 7.0 as avg_yearly from lineitem, part where p_partkey = l_partkey and p_brand = 'Brand#43' and p_container = 'JUMBO JAR' and l_quantity < ( select 0.2 * avg(l_quantity) from lineitem where l_partkey = p_partkey );
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice) / 7.0 as avg_yearly from lineitem, part where p_partkey = l_partkey and p_brand = 'Brand#45' and p_container = 'JUMBO PKG' and l_quantity < ( select 0.2 * avg(l_quantity) from lineitem where l_partkey = p_partkey );
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice) / 7.0 as avg_yearly from lineitem, part where p_partkey = l_partkey and p_brand = 'Brand#42' and p_container = 'WRAP CASE' and l_quantity < ( select 0.2 * avg(l_quantity) from lineitem where l_partkey = p_partkey );
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice) / 7.0 as avg_yearly from lineitem, part where p_partkey = l_partkey and p_brand = 'Brand#44' and p_container = 'WRAP JAR' and l_quantity < ( select 0.2 * avg(l_quantity) from lineitem where l_partkey = p_partkey );
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice) / 7.0 as avg_yearly from lineitem, part where p_partkey = l_partkey and p_brand = 'Brand#41' and p_container = 'WRAP PKG' and l_quantity < ( select 0.2 * avg(l_quantity) from lineitem where l_partkey = p_partkey );
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice) / 7.0 as avg_yearly from lineitem, part where p_partkey = l_partkey and p_brand = 'Brand#43' and p_container = 'SM CASE' and l_quantity < ( select 0.2 * avg(l_quantity) from lineitem where l_partkey = p_partkey );
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice) / 7.0 as avg_yearly from lineitem, part where p_partkey = l_partkey and p_brand = 'Brand#45' and p_container = 'SM JAR' and l_quantity < ( select 0.2 * avg(l_quantity) from lineitem where l_partkey = p_partkey );
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice) / 7.0 as avg_yearly from lineitem, part where p_partkey = l_partkey and p_brand = 'Brand#42' and p_container = 'SM PKG' and l_quantity < ( select 0.2 * avg(l_quantity) from lineitem where l_partkey = p_partkey );
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice) / 7.0 as avg_yearly from lineitem, part where p_partkey = l_partkey and p_brand = 'Brand#44' and p_container = 'LG CASE' and l_quantity < ( select 0.2 * avg(l_quantity) from lineitem where l_partkey = p_partkey );
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice) / 7.0 as avg_yearly from lineitem, part where p_partkey = l_partkey and p_brand = 'Brand#41' and p_container = 'LG JAR' and l_quantity < ( select 0.2 * avg(l_quantity) from lineitem where l_partkey = p_partkey );
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice) / 7.0 as avg_yearly from lineitem, part where p_partkey = l_partkey and p_brand = 'Brand#43' and p_container = 'LG CAN' and l_quantity < ( select 0.2 * avg(l_quantity) from lineitem where l_partkey = p_partkey );
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice) / 7.0 as avg_yearly from lineitem, part where p_partkey = l_partkey and p_brand = 'Brand#45' and p_container = 'MED CASE' and l_quantity < ( select 0.2 * avg(l_quantity) from lineitem where l_partkey = p_partkey );
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice) / 7.0 as avg_yearly from lineitem, part where p_partkey = l_partkey and p_brand = 'Brand#41' and p_container = 'MED JAR' and l_quantity < ( select 0.2 * avg(l_quantity) from lineitem where l_partkey = p_partkey );
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice) / 7.0 as avg_yearly from lineitem, part where p_partkey = l_partkey and p_brand = 'Brand#43' and p_container = 'MED CAN' and l_quantity < ( select 0.2 * avg(l_quantity) from lineitem where l_partkey = p_partkey );
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice) / 7.0 as avg_yearly from lineitem, part where p_partkey = l_partkey and p_brand = 'Brand#45' and p_container = 'JUMBO CASE' and l_quantity < ( select 0.2 * avg(l_quantity) from lineitem where l_partkey = p_partkey );
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice) / 7.0 as avg_yearly from lineitem, part where p_partkey = l_partkey and p_brand = 'Brand#42' and p_container = 'JUMBO JAR' and l_quantity < ( select 0.2 * avg(l_quantity) from lineitem where l_partkey = p_partkey );

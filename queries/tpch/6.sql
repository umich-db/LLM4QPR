EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice * l_discount) as revenue from lineitem where l_shipdate >= date '1993-01-01' and l_shipdate < date '1993-01-01' + interval '1 year' and l_discount between 0.07 - 0.01 and 0.07 + 0.01 and l_quantity < 25;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice * l_discount) as revenue from lineitem where l_shipdate >= date '1993-01-01' and l_shipdate < date '1993-01-01' + interval '1 year' and l_discount between 0.04 - 0.01 and 0.04 + 0.01 and l_quantity < 24;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice * l_discount) as revenue from lineitem where l_shipdate >= date '1993-01-01' and l_shipdate < date '1993-01-01' + interval '1 year' and l_discount between 0.02 - 0.01 and 0.02 + 0.01 and l_quantity < 24;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice * l_discount) as revenue from lineitem where l_shipdate >= date '1993-01-01' and l_shipdate < date '1993-01-01' + interval '1 year' and l_discount between 0.07 - 0.01 and 0.07 + 0.01 and l_quantity < 25;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice * l_discount) as revenue from lineitem where l_shipdate >= date '1994-01-01' and l_shipdate < date '1994-01-01' + interval '1 year' and l_discount between 0.05 - 0.01 and 0.05 + 0.01 and l_quantity < 24;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice * l_discount) as revenue from lineitem where l_shipdate >= date '1994-01-01' and l_shipdate < date '1994-01-01' + interval '1 year' and l_discount between 0.02 - 0.01 and 0.02 + 0.01 and l_quantity < 24;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice * l_discount) as revenue from lineitem where l_shipdate >= date '1994-01-01' and l_shipdate < date '1994-01-01' + interval '1 year' and l_discount between 0.08 - 0.01 and 0.08 + 0.01 and l_quantity < 25;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice * l_discount) as revenue from lineitem where l_shipdate >= date '1994-01-01' and l_shipdate < date '1994-01-01' + interval '1 year' and l_discount between 0.05 - 0.01 and 0.05 + 0.01 and l_quantity < 24;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice * l_discount) as revenue from lineitem where l_shipdate >= date '1995-01-01' and l_shipdate < date '1995-01-01' + interval '1 year' and l_discount between 0.02 - 0.01 and 0.02 + 0.01 and l_quantity < 24;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice * l_discount) as revenue from lineitem where l_shipdate >= date '1995-01-01' and l_shipdate < date '1995-01-01' + interval '1 year' and l_discount between 0.08 - 0.01 and 0.08 + 0.01 and l_quantity < 25;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice * l_discount) as revenue from lineitem where l_shipdate >= date '1995-01-01' and l_shipdate < date '1995-01-01' + interval '1 year' and l_discount between 0.05 - 0.01 and 0.05 + 0.01 and l_quantity < 24;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice * l_discount) as revenue from lineitem where l_shipdate >= date '1995-01-01' and l_shipdate < date '1995-01-01' + interval '1 year' and l_discount between 0.03 - 0.01 and 0.03 + 0.01 and l_quantity < 24;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice * l_discount) as revenue from lineitem where l_shipdate >= date '1996-01-01' and l_shipdate < date '1996-01-01' + interval '1 year' and l_discount between 0.08 - 0.01 and 0.08 + 0.01 and l_quantity < 25;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice * l_discount) as revenue from lineitem where l_shipdate >= date '1996-01-01' and l_shipdate < date '1996-01-01' + interval '1 year' and l_discount between 0.06 - 0.01 and 0.06 + 0.01 and l_quantity < 25;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice * l_discount) as revenue from lineitem where l_shipdate >= date '1996-01-01' and l_shipdate < date '1996-01-01' + interval '1 year' and l_discount between 0.03 - 0.01 and 0.03 + 0.01 and l_quantity < 24;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice * l_discount) as revenue from lineitem where l_shipdate >= date '1996-01-01' and l_shipdate < date '1996-01-01' + interval '1 year' and l_discount between 0.08 - 0.01 and 0.08 + 0.01 and l_quantity < 25;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice * l_discount) as revenue from lineitem where l_shipdate >= date '1996-01-01' and l_shipdate < date '1996-01-01' + interval '1 year' and l_discount between 0.06 - 0.01 and 0.06 + 0.01 and l_quantity < 25;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice * l_discount) as revenue from lineitem where l_shipdate >= date '1997-01-01' and l_shipdate < date '1997-01-01' + interval '1 year' and l_discount between 0.03 - 0.01 and 0.03 + 0.01 and l_quantity < 24;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice * l_discount) as revenue from lineitem where l_shipdate >= date '1997-01-01' and l_shipdate < date '1997-01-01' + interval '1 year' and l_discount between 0.09 - 0.01 and 0.09 + 0.01 and l_quantity < 25;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice * l_discount) as revenue from lineitem where l_shipdate >= date '1997-01-01' and l_shipdate < date '1997-01-01' + interval '1 year' and l_discount between 0.06 - 0.01 and 0.06 + 0.01 and l_quantity < 25;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice * l_discount) as revenue from lineitem where l_shipdate >= date '1997-01-01' and l_shipdate < date '1997-01-01' + interval '1 year' and l_discount between 0.04 - 0.01 and 0.04 + 0.01 and l_quantity < 24;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice * l_discount) as revenue from lineitem where l_shipdate >= date '1993-01-01' and l_shipdate < date '1993-01-01' + interval '1 year' and l_discount between 0.09 - 0.01 and 0.09 + 0.01 and l_quantity < 25;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice * l_discount) as revenue from lineitem where l_shipdate >= date '1993-01-01' and l_shipdate < date '1993-01-01' + interval '1 year' and l_discount between 0.06 - 0.01 and 0.06 + 0.01 and l_quantity < 25;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice * l_discount) as revenue from lineitem where l_shipdate >= date '1993-01-01' and l_shipdate < date '1993-01-01' + interval '1 year' and l_discount between 0.04 - 0.01 and 0.04 + 0.01 and l_quantity < 24;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice * l_discount) as revenue from lineitem where l_shipdate >= date '1993-01-01' and l_shipdate < date '1993-01-01' + interval '1 year' and l_discount between 0.09 - 0.01 and 0.09 + 0.01 and l_quantity < 25;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice * l_discount) as revenue from lineitem where l_shipdate >= date '1994-01-01' and l_shipdate < date '1994-01-01' + interval '1 year' and l_discount between 0.07 - 0.01 and 0.07 + 0.01 and l_quantity < 25;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice * l_discount) as revenue from lineitem where l_shipdate >= date '1994-01-01' and l_shipdate < date '1994-01-01' + interval '1 year' and l_discount between 0.04 - 0.01 and 0.04 + 0.01 and l_quantity < 24;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice * l_discount) as revenue from lineitem where l_shipdate >= date '1994-01-01' and l_shipdate < date '1994-01-01' + interval '1 year' and l_discount between 0.02 - 0.01 and 0.02 + 0.01 and l_quantity < 24;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice * l_discount) as revenue from lineitem where l_shipdate >= date '1994-01-01' and l_shipdate < date '1994-01-01' + interval '1 year' and l_discount between 0.07 - 0.01 and 0.07 + 0.01 and l_quantity < 25;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice * l_discount) as revenue from lineitem where l_shipdate >= date '1995-01-01' and l_shipdate < date '1995-01-01' + interval '1 year' and l_discount between 0.04 - 0.01 and 0.04 + 0.01 and l_quantity < 24;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice * l_discount) as revenue from lineitem where l_shipdate >= date '1995-01-01' and l_shipdate < date '1995-01-01' + interval '1 year' and l_discount between 0.02 - 0.01 and 0.02 + 0.01 and l_quantity < 24;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice * l_discount) as revenue from lineitem where l_shipdate >= date '1995-01-01' and l_shipdate < date '1995-01-01' + interval '1 year' and l_discount between 0.07 - 0.01 and 0.07 + 0.01 and l_quantity < 25;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice * l_discount) as revenue from lineitem where l_shipdate >= date '1995-01-01' and l_shipdate < date '1995-01-01' + interval '1 year' and l_discount between 0.05 - 0.01 and 0.05 + 0.01 and l_quantity < 24;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice * l_discount) as revenue from lineitem where l_shipdate >= date '1995-01-01' and l_shipdate < date '1995-01-01' + interval '1 year' and l_discount between 0.02 - 0.01 and 0.02 + 0.01 and l_quantity < 24;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice * l_discount) as revenue from lineitem where l_shipdate >= date '1996-01-01' and l_shipdate < date '1996-01-01' + interval '1 year' and l_discount between 0.08 - 0.01 and 0.08 + 0.01 and l_quantity < 25;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice * l_discount) as revenue from lineitem where l_shipdate >= date '1996-01-01' and l_shipdate < date '1996-01-01' + interval '1 year' and l_discount between 0.05 - 0.01 and 0.05 + 0.01 and l_quantity < 24;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice * l_discount) as revenue from lineitem where l_shipdate >= date '1996-01-01' and l_shipdate < date '1996-01-01' + interval '1 year' and l_discount between 0.02 - 0.01 and 0.02 + 0.01 and l_quantity < 24;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice * l_discount) as revenue from lineitem where l_shipdate >= date '1996-01-01' and l_shipdate < date '1996-01-01' + interval '1 year' and l_discount between 0.08 - 0.01 and 0.08 + 0.01 and l_quantity < 25;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice * l_discount) as revenue from lineitem where l_shipdate >= date '1997-01-01' and l_shipdate < date '1997-01-01' + interval '1 year' and l_discount between 0.05 - 0.01 and 0.05 + 0.01 and l_quantity < 24;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice * l_discount) as revenue from lineitem where l_shipdate >= date '1997-01-01' and l_shipdate < date '1997-01-01' + interval '1 year' and l_discount between 0.03 - 0.01 and 0.03 + 0.01 and l_quantity < 24;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice * l_discount) as revenue from lineitem where l_shipdate >= date '1997-01-01' and l_shipdate < date '1997-01-01' + interval '1 year' and l_discount between 0.08 - 0.01 and 0.08 + 0.01 and l_quantity < 25;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice * l_discount) as revenue from lineitem where l_shipdate >= date '1997-01-01' and l_shipdate < date '1997-01-01' + interval '1 year' and l_discount between 0.06 - 0.01 and 0.06 + 0.01 and l_quantity < 25;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice * l_discount) as revenue from lineitem where l_shipdate >= date '1993-01-01' and l_shipdate < date '1993-01-01' + interval '1 year' and l_discount between 0.03 - 0.01 and 0.03 + 0.01 and l_quantity < 24;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice * l_discount) as revenue from lineitem where l_shipdate >= date '1993-01-01' and l_shipdate < date '1993-01-01' + interval '1 year' and l_discount between 0.08 - 0.01 and 0.08 + 0.01 and l_quantity < 25;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice * l_discount) as revenue from lineitem where l_shipdate >= date '1993-01-01' and l_shipdate < date '1993-01-01' + interval '1 year' and l_discount between 0.06 - 0.01 and 0.06 + 0.01 and l_quantity < 25;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice * l_discount) as revenue from lineitem where l_shipdate >= date '1993-01-01' and l_shipdate < date '1993-01-01' + interval '1 year' and l_discount between 0.03 - 0.01 and 0.03 + 0.01 and l_quantity < 24;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice * l_discount) as revenue from lineitem where l_shipdate >= date '1994-01-01' and l_shipdate < date '1994-01-01' + interval '1 year' and l_discount between 0.09 - 0.01 and 0.09 + 0.01 and l_quantity < 25;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice * l_discount) as revenue from lineitem where l_shipdate >= date '1994-01-01' and l_shipdate < date '1994-01-01' + interval '1 year' and l_discount between 0.06 - 0.01 and 0.06 + 0.01 and l_quantity < 25;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice * l_discount) as revenue from lineitem where l_shipdate >= date '1994-01-01' and l_shipdate < date '1994-01-01' + interval '1 year' and l_discount between 0.04 - 0.01 and 0.04 + 0.01 and l_quantity < 24;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice * l_discount) as revenue from lineitem where l_shipdate >= date '1994-01-01' and l_shipdate < date '1994-01-01' + interval '1 year' and l_discount between 0.09 - 0.01 and 0.09 + 0.01 and l_quantity < 25;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice * l_discount) as revenue from lineitem where l_shipdate >= date '1994-01-01' and l_shipdate < date '1994-01-01' + interval '1 year' and l_discount between 0.06 - 0.01 and 0.06 + 0.01 and l_quantity < 25;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice * l_discount) as revenue from lineitem where l_shipdate >= date '1995-01-01' and l_shipdate < date '1995-01-01' + interval '1 year' and l_discount between 0.04 - 0.01 and 0.04 + 0.01 and l_quantity < 24;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice * l_discount) as revenue from lineitem where l_shipdate >= date '1995-01-01' and l_shipdate < date '1995-01-01' + interval '1 year' and l_discount between 0.09 - 0.01 and 0.09 + 0.01 and l_quantity < 24;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice * l_discount) as revenue from lineitem where l_shipdate >= date '1995-01-01' and l_shipdate < date '1995-01-01' + interval '1 year' and l_discount between 0.07 - 0.01 and 0.07 + 0.01 and l_quantity < 25;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice * l_discount) as revenue from lineitem where l_shipdate >= date '1995-01-01' and l_shipdate < date '1995-01-01' + interval '1 year' and l_discount between 0.04 - 0.01 and 0.04 + 0.01 and l_quantity < 24;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice * l_discount) as revenue from lineitem where l_shipdate >= date '1996-01-01' and l_shipdate < date '1996-01-01' + interval '1 year' and l_discount between 0.02 - 0.01 and 0.02 + 0.01 and l_quantity < 24;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice * l_discount) as revenue from lineitem where l_shipdate >= date '1996-01-01' and l_shipdate < date '1996-01-01' + interval '1 year' and l_discount between 0.07 - 0.01 and 0.07 + 0.01 and l_quantity < 25;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice * l_discount) as revenue from lineitem where l_shipdate >= date '1996-01-01' and l_shipdate < date '1996-01-01' + interval '1 year' and l_discount between 0.04 - 0.01 and 0.04 + 0.01 and l_quantity < 24;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice * l_discount) as revenue from lineitem where l_shipdate >= date '1996-01-01' and l_shipdate < date '1996-01-01' + interval '1 year' and l_discount between 0.02 - 0.01 and 0.02 + 0.01 and l_quantity < 24;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice * l_discount) as revenue from lineitem where l_shipdate >= date '1997-01-01' and l_shipdate < date '1997-01-01' + interval '1 year' and l_discount between 0.07 - 0.01 and 0.07 + 0.01 and l_quantity < 25;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice * l_discount) as revenue from lineitem where l_shipdate >= date '1997-01-01' and l_shipdate < date '1997-01-01' + interval '1 year' and l_discount between 0.05 - 0.01 and 0.05 + 0.01 and l_quantity < 24;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice * l_discount) as revenue from lineitem where l_shipdate >= date '1997-01-01' and l_shipdate < date '1997-01-01' + interval '1 year' and l_discount between 0.02 - 0.01 and 0.02 + 0.01 and l_quantity < 24;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice * l_discount) as revenue from lineitem where l_shipdate >= date '1997-01-01' and l_shipdate < date '1997-01-01' + interval '1 year' and l_discount between 0.08 - 0.01 and 0.08 + 0.01 and l_quantity < 25;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice * l_discount) as revenue from lineitem where l_shipdate >= date '1993-01-01' and l_shipdate < date '1993-01-01' + interval '1 year' and l_discount between 0.05 - 0.01 and 0.05 + 0.01 and l_quantity < 24;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice * l_discount) as revenue from lineitem where l_shipdate >= date '1993-01-01' and l_shipdate < date '1993-01-01' + interval '1 year' and l_discount between 0.03 - 0.01 and 0.03 + 0.01 and l_quantity < 24;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice * l_discount) as revenue from lineitem where l_shipdate >= date '1993-01-01' and l_shipdate < date '1993-01-01' + interval '1 year' and l_discount between 0.08 - 0.01 and 0.08 + 0.01 and l_quantity < 25;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice * l_discount) as revenue from lineitem where l_shipdate >= date '1993-01-01' and l_shipdate < date '1993-01-01' + interval '1 year' and l_discount between 0.05 - 0.01 and 0.05 + 0.01 and l_quantity < 25;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice * l_discount) as revenue from lineitem where l_shipdate >= date '1993-01-01' and l_shipdate < date '1993-01-01' + interval '1 year' and l_discount between 0.03 - 0.01 and 0.03 + 0.01 and l_quantity < 24;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice * l_discount) as revenue from lineitem where l_shipdate >= date '1994-01-01' and l_shipdate < date '1994-01-01' + interval '1 year' and l_discount between 0.08 - 0.01 and 0.08 + 0.01 and l_quantity < 25;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice * l_discount) as revenue from lineitem where l_shipdate >= date '1994-01-01' and l_shipdate < date '1994-01-01' + interval '1 year' and l_discount between 0.06 - 0.01 and 0.06 + 0.01 and l_quantity < 25;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice * l_discount) as revenue from lineitem where l_shipdate >= date '1994-01-01' and l_shipdate < date '1994-01-01' + interval '1 year' and l_discount between 0.03 - 0.01 and 0.03 + 0.01 and l_quantity < 24;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice * l_discount) as revenue from lineitem where l_shipdate >= date '1994-01-01' and l_shipdate < date '1994-01-01' + interval '1 year' and l_discount between 0.09 - 0.01 and 0.09 + 0.01 and l_quantity < 25;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice * l_discount) as revenue from lineitem where l_shipdate >= date '1995-01-01' and l_shipdate < date '1995-01-01' + interval '1 year' and l_discount between 0.06 - 0.01 and 0.06 + 0.01 and l_quantity < 25;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice * l_discount) as revenue from lineitem where l_shipdate >= date '1995-01-01' and l_shipdate < date '1995-01-01' + interval '1 year' and l_discount between 0.03 - 0.01 and 0.03 + 0.01 and l_quantity < 24;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice * l_discount) as revenue from lineitem where l_shipdate >= date '1995-01-01' and l_shipdate < date '1995-01-01' + interval '1 year' and l_discount between 0.09 - 0.01 and 0.09 + 0.01 and l_quantity < 25;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice * l_discount) as revenue from lineitem where l_shipdate >= date '1995-01-01' and l_shipdate < date '1995-01-01' + interval '1 year' and l_discount between 0.06 - 0.01 and 0.06 + 0.01 and l_quantity < 25;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice * l_discount) as revenue from lineitem where l_shipdate >= date '1996-01-01' and l_shipdate < date '1996-01-01' + interval '1 year' and l_discount between 0.04 - 0.01 and 0.04 + 0.01 and l_quantity < 24;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice * l_discount) as revenue from lineitem where l_shipdate >= date '1996-01-01' and l_shipdate < date '1996-01-01' + interval '1 year' and l_discount between 0.09 - 0.01 and 0.09 + 0.01 and l_quantity < 25;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice * l_discount) as revenue from lineitem where l_shipdate >= date '1996-01-01' and l_shipdate < date '1996-01-01' + interval '1 year' and l_discount between 0.07 - 0.01 and 0.07 + 0.01 and l_quantity < 25;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice * l_discount) as revenue from lineitem where l_shipdate >= date '1996-01-01' and l_shipdate < date '1996-01-01' + interval '1 year' and l_discount between 0.04 - 0.01 and 0.04 + 0.01 and l_quantity < 24;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice * l_discount) as revenue from lineitem where l_shipdate >= date '1997-01-01' and l_shipdate < date '1997-01-01' + interval '1 year' and l_discount between 0.09 - 0.01 and 0.09 + 0.01 and l_quantity < 24;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice * l_discount) as revenue from lineitem where l_shipdate >= date '1997-01-01' and l_shipdate < date '1997-01-01' + interval '1 year' and l_discount between 0.07 - 0.01 and 0.07 + 0.01 and l_quantity < 25;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice * l_discount) as revenue from lineitem where l_shipdate >= date '1997-01-01' and l_shipdate < date '1997-01-01' + interval '1 year' and l_discount between 0.04 - 0.01 and 0.04 + 0.01 and l_quantity < 24;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice * l_discount) as revenue from lineitem where l_shipdate >= date '1997-01-01' and l_shipdate < date '1997-01-01' + interval '1 year' and l_discount between 0.02 - 0.01 and 0.02 + 0.01 and l_quantity < 24;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice * l_discount) as revenue from lineitem where l_shipdate >= date '1997-01-01' and l_shipdate < date '1997-01-01' + interval '1 year' and l_discount between 0.07 - 0.01 and 0.07 + 0.01 and l_quantity < 25;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice * l_discount) as revenue from lineitem where l_shipdate >= date '1993-01-01' and l_shipdate < date '1993-01-01' + interval '1 year' and l_discount between 0.05 - 0.01 and 0.05 + 0.01 and l_quantity < 24;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice * l_discount) as revenue from lineitem where l_shipdate >= date '1993-01-01' and l_shipdate < date '1993-01-01' + interval '1 year' and l_discount between 0.02 - 0.01 and 0.02 + 0.01 and l_quantity < 24;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice * l_discount) as revenue from lineitem where l_shipdate >= date '1993-01-01' and l_shipdate < date '1993-01-01' + interval '1 year' and l_discount between 0.07 - 0.01 and 0.07 + 0.01 and l_quantity < 25;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice * l_discount) as revenue from lineitem where l_shipdate >= date '1993-01-01' and l_shipdate < date '1993-01-01' + interval '1 year' and l_discount between 0.05 - 0.01 and 0.05 + 0.01 and l_quantity < 24;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice * l_discount) as revenue from lineitem where l_shipdate >= date '1994-01-01' and l_shipdate < date '1994-01-01' + interval '1 year' and l_discount between 0.02 - 0.01 and 0.02 + 0.01 and l_quantity < 24;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice * l_discount) as revenue from lineitem where l_shipdate >= date '1994-01-01' and l_shipdate < date '1994-01-01' + interval '1 year' and l_discount between 0.08 - 0.01 and 0.08 + 0.01 and l_quantity < 25;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice * l_discount) as revenue from lineitem where l_shipdate >= date '1994-01-01' and l_shipdate < date '1994-01-01' + interval '1 year' and l_discount between 0.05 - 0.01 and 0.05 + 0.01 and l_quantity < 24;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice * l_discount) as revenue from lineitem where l_shipdate >= date '1994-01-01' and l_shipdate < date '1994-01-01' + interval '1 year' and l_discount between 0.03 - 0.01 and 0.03 + 0.01 and l_quantity < 24;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice * l_discount) as revenue from lineitem where l_shipdate >= date '1995-01-01' and l_shipdate < date '1995-01-01' + interval '1 year' and l_discount between 0.08 - 0.01 and 0.08 + 0.01 and l_quantity < 25;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice * l_discount) as revenue from lineitem where l_shipdate >= date '1995-01-01' and l_shipdate < date '1995-01-01' + interval '1 year' and l_discount between 0.05 - 0.01 and 0.05 + 0.01 and l_quantity < 25;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice * l_discount) as revenue from lineitem where l_shipdate >= date '1995-01-01' and l_shipdate < date '1995-01-01' + interval '1 year' and l_discount between 0.03 - 0.01 and 0.03 + 0.01 and l_quantity < 24;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice * l_discount) as revenue from lineitem where l_shipdate >= date '1995-01-01' and l_shipdate < date '1995-01-01' + interval '1 year' and l_discount between 0.08 - 0.01 and 0.08 + 0.01 and l_quantity < 25;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice * l_discount) as revenue from lineitem where l_shipdate >= date '1996-01-01' and l_shipdate < date '1996-01-01' + interval '1 year' and l_discount between 0.06 - 0.01 and 0.06 + 0.01 and l_quantity < 25;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice * l_discount) as revenue from lineitem where l_shipdate >= date '1996-01-01' and l_shipdate < date '1996-01-01' + interval '1 year' and l_discount between 0.03 - 0.01 and 0.03 + 0.01 and l_quantity < 24;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select sum(l_extendedprice * l_discount) as revenue from lineitem where l_shipdate >= date '1996-01-01' and l_shipdate < date '1996-01-01' + interval '1 year' and l_discount between 0.09 - 0.01 and 0.09 + 0.01 and l_quantity < 25;

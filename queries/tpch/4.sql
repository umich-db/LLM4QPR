EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select o_orderpriority, count(*) as order_count from orders where o_orderdate >= date '1995-07-01' and o_orderdate < date '1995-07-01' + interval '3 months' and exists ( select * from lineitem where l_orderkey = o_orderkey and l_commitdate < l_receiptdate ) group by o_orderpriority order by o_orderpriority;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select o_orderpriority, count(*) as order_count from orders where o_orderdate >= date '1993-04-01' and o_orderdate < date '1993-04-01' + interval '3 months' and exists ( select * from lineitem where l_orderkey = o_orderkey and l_commitdate < l_receiptdate ) group by o_orderpriority order by o_orderpriority;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select o_orderpriority, count(*) as order_count from orders where o_orderdate >= date '1995-11-01' and o_orderdate < date '1995-11-01' + interval '3 months' and exists ( select * from lineitem where l_orderkey = o_orderkey and l_commitdate < l_receiptdate ) group by o_orderpriority order by o_orderpriority;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select o_orderpriority, count(*) as order_count from orders where o_orderdate >= date '1993-08-01' and o_orderdate < date '1993-08-01' + interval '3 months' and exists ( select * from lineitem where l_orderkey = o_orderkey and l_commitdate < l_receiptdate ) group by o_orderpriority order by o_orderpriority;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select o_orderpriority, count(*) as order_count from orders where o_orderdate >= date '1996-03-01' and o_orderdate < date '1996-03-01' + interval '3 months' and exists ( select * from lineitem where l_orderkey = o_orderkey and l_commitdate < l_receiptdate ) group by o_orderpriority order by o_orderpriority;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select o_orderpriority, count(*) as order_count from orders where o_orderdate >= date '1993-12-01' and o_orderdate < date '1993-12-01' + interval '3 months' and exists ( select * from lineitem where l_orderkey = o_orderkey and l_commitdate < l_receiptdate ) group by o_orderpriority order by o_orderpriority;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select o_orderpriority, count(*) as order_count from orders where o_orderdate >= date '1996-07-01' and o_orderdate < date '1996-07-01' + interval '3 months' and exists ( select * from lineitem where l_orderkey = o_orderkey and l_commitdate < l_receiptdate ) group by o_orderpriority order by o_orderpriority;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select o_orderpriority, count(*) as order_count from orders where o_orderdate >= date '1994-04-01' and o_orderdate < date '1994-04-01' + interval '3 months' and exists ( select * from lineitem where l_orderkey = o_orderkey and l_commitdate < l_receiptdate ) group by o_orderpriority order by o_orderpriority;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select o_orderpriority, count(*) as order_count from orders where o_orderdate >= date '1996-11-01' and o_orderdate < date '1996-11-01' + interval '3 months' and exists ( select * from lineitem where l_orderkey = o_orderkey and l_commitdate < l_receiptdate ) group by o_orderpriority order by o_orderpriority;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select o_orderpriority, count(*) as order_count from orders where o_orderdate >= date '1994-08-01' and o_orderdate < date '1994-08-01' + interval '3 months' and exists ( select * from lineitem where l_orderkey = o_orderkey and l_commitdate < l_receiptdate ) group by o_orderpriority order by o_orderpriority;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select o_orderpriority, count(*) as order_count from orders where o_orderdate >= date '1997-02-01' and o_orderdate < date '1997-02-01' + interval '3 months' and exists ( select * from lineitem where l_orderkey = o_orderkey and l_commitdate < l_receiptdate ) group by o_orderpriority order by o_orderpriority;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select o_orderpriority, count(*) as order_count from orders where o_orderdate >= date '1994-11-01' and o_orderdate < date '1994-11-01' + interval '3 months' and exists ( select * from lineitem where l_orderkey = o_orderkey and l_commitdate < l_receiptdate ) group by o_orderpriority order by o_orderpriority;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select o_orderpriority, count(*) as order_count from orders where o_orderdate >= date '1997-06-01' and o_orderdate < date '1997-06-01' + interval '3 months' and exists ( select * from lineitem where l_orderkey = o_orderkey and l_commitdate < l_receiptdate ) group by o_orderpriority order by o_orderpriority;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select o_orderpriority, count(*) as order_count from orders where o_orderdate >= date '1995-03-01' and o_orderdate < date '1995-03-01' + interval '3 months' and exists ( select * from lineitem where l_orderkey = o_orderkey and l_commitdate < l_receiptdate ) group by o_orderpriority order by o_orderpriority;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select o_orderpriority, count(*) as order_count from orders where o_orderdate >= date '1997-10-01' and o_orderdate < date '1997-10-01' + interval '3 months' and exists ( select * from lineitem where l_orderkey = o_orderkey and l_commitdate < l_receiptdate ) group by o_orderpriority order by o_orderpriority;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select o_orderpriority, count(*) as order_count from orders where o_orderdate >= date '1995-07-01' and o_orderdate < date '1995-07-01' + interval '3 months' and exists ( select * from lineitem where l_orderkey = o_orderkey and l_commitdate < l_receiptdate ) group by o_orderpriority order by o_orderpriority;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select o_orderpriority, count(*) as order_count from orders where o_orderdate >= date '1993-04-01' and o_orderdate < date '1993-04-01' + interval '3 months' and exists ( select * from lineitem where l_orderkey = o_orderkey and l_commitdate < l_receiptdate ) group by o_orderpriority order by o_orderpriority;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select o_orderpriority, count(*) as order_count from orders where o_orderdate >= date '1995-11-01' and o_orderdate < date '1995-11-01' + interval '3 months' and exists ( select * from lineitem where l_orderkey = o_orderkey and l_commitdate < l_receiptdate ) group by o_orderpriority order by o_orderpriority;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select o_orderpriority, count(*) as order_count from orders where o_orderdate >= date '1993-08-01' and o_orderdate < date '1993-08-01' + interval '3 months' and exists ( select * from lineitem where l_orderkey = o_orderkey and l_commitdate < l_receiptdate ) group by o_orderpriority order by o_orderpriority;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select o_orderpriority, count(*) as order_count from orders where o_orderdate >= date '1996-03-01' and o_orderdate < date '1996-03-01' + interval '3 months' and exists ( select * from lineitem where l_orderkey = o_orderkey and l_commitdate < l_receiptdate ) group by o_orderpriority order by o_orderpriority;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select o_orderpriority, count(*) as order_count from orders where o_orderdate >= date '1993-11-01' and o_orderdate < date '1993-11-01' + interval '3 months' and exists ( select * from lineitem where l_orderkey = o_orderkey and l_commitdate < l_receiptdate ) group by o_orderpriority order by o_orderpriority;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select o_orderpriority, count(*) as order_count from orders where o_orderdate >= date '1996-06-01' and o_orderdate < date '1996-06-01' + interval '3 months' and exists ( select * from lineitem where l_orderkey = o_orderkey and l_commitdate < l_receiptdate ) group by o_orderpriority order by o_orderpriority;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select o_orderpriority, count(*) as order_count from orders where o_orderdate >= date '1994-03-01' and o_orderdate < date '1994-03-01' + interval '3 months' and exists ( select * from lineitem where l_orderkey = o_orderkey and l_commitdate < l_receiptdate ) group by o_orderpriority order by o_orderpriority;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select o_orderpriority, count(*) as order_count from orders where o_orderdate >= date '1996-10-01' and o_orderdate < date '1996-10-01' + interval '3 months' and exists ( select * from lineitem where l_orderkey = o_orderkey and l_commitdate < l_receiptdate ) group by o_orderpriority order by o_orderpriority;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select o_orderpriority, count(*) as order_count from orders where o_orderdate >= date '1994-07-01' and o_orderdate < date '1994-07-01' + interval '3 months' and exists ( select * from lineitem where l_orderkey = o_orderkey and l_commitdate < l_receiptdate ) group by o_orderpriority order by o_orderpriority;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select o_orderpriority, count(*) as order_count from orders where o_orderdate >= date '1997-02-01' and o_orderdate < date '1997-02-01' + interval '3 months' and exists ( select * from lineitem where l_orderkey = o_orderkey and l_commitdate < l_receiptdate ) group by o_orderpriority order by o_orderpriority;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select o_orderpriority, count(*) as order_count from orders where o_orderdate >= date '1994-11-01' and o_orderdate < date '1994-11-01' + interval '3 months' and exists ( select * from lineitem where l_orderkey = o_orderkey and l_commitdate < l_receiptdate ) group by o_orderpriority order by o_orderpriority;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select o_orderpriority, count(*) as order_count from orders where o_orderdate >= date '1997-06-01' and o_orderdate < date '1997-06-01' + interval '3 months' and exists ( select * from lineitem where l_orderkey = o_orderkey and l_commitdate < l_receiptdate ) group by o_orderpriority order by o_orderpriority;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select o_orderpriority, count(*) as order_count from orders where o_orderdate >= date '1995-03-01' and o_orderdate < date '1995-03-01' + interval '3 months' and exists ( select * from lineitem where l_orderkey = o_orderkey and l_commitdate < l_receiptdate ) group by o_orderpriority order by o_orderpriority;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select o_orderpriority, count(*) as order_count from orders where o_orderdate >= date '1997-10-01' and o_orderdate < date '1997-10-01' + interval '3 months' and exists ( select * from lineitem where l_orderkey = o_orderkey and l_commitdate < l_receiptdate ) group by o_orderpriority order by o_orderpriority;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select o_orderpriority, count(*) as order_count from orders where o_orderdate >= date '1995-06-01' and o_orderdate < date '1995-06-01' + interval '3 months' and exists ( select * from lineitem where l_orderkey = o_orderkey and l_commitdate < l_receiptdate ) group by o_orderpriority order by o_orderpriority;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select o_orderpriority, count(*) as order_count from orders where o_orderdate >= date '1993-03-01' and o_orderdate < date '1993-03-01' + interval '3 months' and exists ( select * from lineitem where l_orderkey = o_orderkey and l_commitdate < l_receiptdate ) group by o_orderpriority order by o_orderpriority;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select o_orderpriority, count(*) as order_count from orders where o_orderdate >= date '1995-10-01' and o_orderdate < date '1995-10-01' + interval '3 months' and exists ( select * from lineitem where l_orderkey = o_orderkey and l_commitdate < l_receiptdate ) group by o_orderpriority order by o_orderpriority;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select o_orderpriority, count(*) as order_count from orders where o_orderdate >= date '1993-07-01' and o_orderdate < date '1993-07-01' + interval '3 months' and exists ( select * from lineitem where l_orderkey = o_orderkey and l_commitdate < l_receiptdate ) group by o_orderpriority order by o_orderpriority;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select o_orderpriority, count(*) as order_count from orders where o_orderdate >= date '1996-02-01' and o_orderdate < date '1996-02-01' + interval '3 months' and exists ( select * from lineitem where l_orderkey = o_orderkey and l_commitdate < l_receiptdate ) group by o_orderpriority order by o_orderpriority;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select o_orderpriority, count(*) as order_count from orders where o_orderdate >= date '1993-11-01' and o_orderdate < date '1993-11-01' + interval '3 months' and exists ( select * from lineitem where l_orderkey = o_orderkey and l_commitdate < l_receiptdate ) group by o_orderpriority order by o_orderpriority;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select o_orderpriority, count(*) as order_count from orders where o_orderdate >= date '1996-06-01' and o_orderdate < date '1996-06-01' + interval '3 months' and exists ( select * from lineitem where l_orderkey = o_orderkey and l_commitdate < l_receiptdate ) group by o_orderpriority order by o_orderpriority;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select o_orderpriority, count(*) as order_count from orders where o_orderdate >= date '1994-03-01' and o_orderdate < date '1994-03-01' + interval '3 months' and exists ( select * from lineitem where l_orderkey = o_orderkey and l_commitdate < l_receiptdate ) group by o_orderpriority order by o_orderpriority;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select o_orderpriority, count(*) as order_count from orders where o_orderdate >= date '1996-10-01' and o_orderdate < date '1996-10-01' + interval '3 months' and exists ( select * from lineitem where l_orderkey = o_orderkey and l_commitdate < l_receiptdate ) group by o_orderpriority order by o_orderpriority;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select o_orderpriority, count(*) as order_count from orders where o_orderdate >= date '1994-07-01' and o_orderdate < date '1994-07-01' + interval '3 months' and exists ( select * from lineitem where l_orderkey = o_orderkey and l_commitdate < l_receiptdate ) group by o_orderpriority order by o_orderpriority;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select o_orderpriority, count(*) as order_count from orders where o_orderdate >= date '1997-01-01' and o_orderdate < date '1997-01-01' + interval '3 months' and exists ( select * from lineitem where l_orderkey = o_orderkey and l_commitdate < l_receiptdate ) group by o_orderpriority order by o_orderpriority;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select o_orderpriority, count(*) as order_count from orders where o_orderdate >= date '1994-10-01' and o_orderdate < date '1994-10-01' + interval '3 months' and exists ( select * from lineitem where l_orderkey = o_orderkey and l_commitdate < l_receiptdate ) group by o_orderpriority order by o_orderpriority;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select o_orderpriority, count(*) as order_count from orders where o_orderdate >= date '1997-05-01' and o_orderdate < date '1997-05-01' + interval '3 months' and exists ( select * from lineitem where l_orderkey = o_orderkey and l_commitdate < l_receiptdate ) group by o_orderpriority order by o_orderpriority;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select o_orderpriority, count(*) as order_count from orders where o_orderdate >= date '1995-02-01' and o_orderdate < date '1995-02-01' + interval '3 months' and exists ( select * from lineitem where l_orderkey = o_orderkey and l_commitdate < l_receiptdate ) group by o_orderpriority order by o_orderpriority;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select o_orderpriority, count(*) as order_count from orders where o_orderdate >= date '1997-09-01' and o_orderdate < date '1997-09-01' + interval '3 months' and exists ( select * from lineitem where l_orderkey = o_orderkey and l_commitdate < l_receiptdate ) group by o_orderpriority order by o_orderpriority;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select o_orderpriority, count(*) as order_count from orders where o_orderdate >= date '1995-06-01' and o_orderdate < date '1995-06-01' + interval '3 months' and exists ( select * from lineitem where l_orderkey = o_orderkey and l_commitdate < l_receiptdate ) group by o_orderpriority order by o_orderpriority;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select o_orderpriority, count(*) as order_count from orders where o_orderdate >= date '1993-03-01' and o_orderdate < date '1993-03-01' + interval '3 months' and exists ( select * from lineitem where l_orderkey = o_orderkey and l_commitdate < l_receiptdate ) group by o_orderpriority order by o_orderpriority;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select o_orderpriority, count(*) as order_count from orders where o_orderdate >= date '1995-10-01' and o_orderdate < date '1995-10-01' + interval '3 months' and exists ( select * from lineitem where l_orderkey = o_orderkey and l_commitdate < l_receiptdate ) group by o_orderpriority order by o_orderpriority;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select o_orderpriority, count(*) as order_count from orders where o_orderdate >= date '1993-07-01' and o_orderdate < date '1993-07-01' + interval '3 months' and exists ( select * from lineitem where l_orderkey = o_orderkey and l_commitdate < l_receiptdate ) group by o_orderpriority order by o_orderpriority;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select o_orderpriority, count(*) as order_count from orders where o_orderdate >= date '1996-02-01' and o_orderdate < date '1996-02-01' + interval '3 months' and exists ( select * from lineitem where l_orderkey = o_orderkey and l_commitdate < l_receiptdate ) group by o_orderpriority order by o_orderpriority;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select o_orderpriority, count(*) as order_count from orders where o_orderdate >= date '1993-10-01' and o_orderdate < date '1993-10-01' + interval '3 months' and exists ( select * from lineitem where l_orderkey = o_orderkey and l_commitdate < l_receiptdate ) group by o_orderpriority order by o_orderpriority;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select o_orderpriority, count(*) as order_count from orders where o_orderdate >= date '1996-05-01' and o_orderdate < date '1996-05-01' + interval '3 months' and exists ( select * from lineitem where l_orderkey = o_orderkey and l_commitdate < l_receiptdate ) group by o_orderpriority order by o_orderpriority;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select o_orderpriority, count(*) as order_count from orders where o_orderdate >= date '1994-02-01' and o_orderdate < date '1994-02-01' + interval '3 months' and exists ( select * from lineitem where l_orderkey = o_orderkey and l_commitdate < l_receiptdate ) group by o_orderpriority order by o_orderpriority;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select o_orderpriority, count(*) as order_count from orders where o_orderdate >= date '1996-09-01' and o_orderdate < date '1996-09-01' + interval '3 months' and exists ( select * from lineitem where l_orderkey = o_orderkey and l_commitdate < l_receiptdate ) group by o_orderpriority order by o_orderpriority;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select o_orderpriority, count(*) as order_count from orders where o_orderdate >= date '1994-06-01' and o_orderdate < date '1994-06-01' + interval '3 months' and exists ( select * from lineitem where l_orderkey = o_orderkey and l_commitdate < l_receiptdate ) group by o_orderpriority order by o_orderpriority;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select o_orderpriority, count(*) as order_count from orders where o_orderdate >= date '1997-01-01' and o_orderdate < date '1997-01-01' + interval '3 months' and exists ( select * from lineitem where l_orderkey = o_orderkey and l_commitdate < l_receiptdate ) group by o_orderpriority order by o_orderpriority;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select o_orderpriority, count(*) as order_count from orders where o_orderdate >= date '1994-10-01' and o_orderdate < date '1994-10-01' + interval '3 months' and exists ( select * from lineitem where l_orderkey = o_orderkey and l_commitdate < l_receiptdate ) group by o_orderpriority order by o_orderpriority;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select o_orderpriority, count(*) as order_count from orders where o_orderdate >= date '1997-05-01' and o_orderdate < date '1997-05-01' + interval '3 months' and exists ( select * from lineitem where l_orderkey = o_orderkey and l_commitdate < l_receiptdate ) group by o_orderpriority order by o_orderpriority;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select o_orderpriority, count(*) as order_count from orders where o_orderdate >= date '1995-02-01' and o_orderdate < date '1995-02-01' + interval '3 months' and exists ( select * from lineitem where l_orderkey = o_orderkey and l_commitdate < l_receiptdate ) group by o_orderpriority order by o_orderpriority;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select o_orderpriority, count(*) as order_count from orders where o_orderdate >= date '1997-09-01' and o_orderdate < date '1997-09-01' + interval '3 months' and exists ( select * from lineitem where l_orderkey = o_orderkey and l_commitdate < l_receiptdate ) group by o_orderpriority order by o_orderpriority;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select o_orderpriority, count(*) as order_count from orders where o_orderdate >= date '1995-05-01' and o_orderdate < date '1995-05-01' + interval '3 months' and exists ( select * from lineitem where l_orderkey = o_orderkey and l_commitdate < l_receiptdate ) group by o_orderpriority order by o_orderpriority;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select o_orderpriority, count(*) as order_count from orders where o_orderdate >= date '1993-02-01' and o_orderdate < date '1993-02-01' + interval '3 months' and exists ( select * from lineitem where l_orderkey = o_orderkey and l_commitdate < l_receiptdate ) group by o_orderpriority order by o_orderpriority;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select o_orderpriority, count(*) as order_count from orders where o_orderdate >= date '1995-09-01' and o_orderdate < date '1995-09-01' + interval '3 months' and exists ( select * from lineitem where l_orderkey = o_orderkey and l_commitdate < l_receiptdate ) group by o_orderpriority order by o_orderpriority;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select o_orderpriority, count(*) as order_count from orders where o_orderdate >= date '1993-06-01' and o_orderdate < date '1993-06-01' + interval '3 months' and exists ( select * from lineitem where l_orderkey = o_orderkey and l_commitdate < l_receiptdate ) group by o_orderpriority order by o_orderpriority;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select o_orderpriority, count(*) as order_count from orders where o_orderdate >= date '1996-01-01' and o_orderdate < date '1996-01-01' + interval '3 months' and exists ( select * from lineitem where l_orderkey = o_orderkey and l_commitdate < l_receiptdate ) group by o_orderpriority order by o_orderpriority;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select o_orderpriority, count(*) as order_count from orders where o_orderdate >= date '1993-10-01' and o_orderdate < date '1993-10-01' + interval '3 months' and exists ( select * from lineitem where l_orderkey = o_orderkey and l_commitdate < l_receiptdate ) group by o_orderpriority order by o_orderpriority;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select o_orderpriority, count(*) as order_count from orders where o_orderdate >= date '1996-05-01' and o_orderdate < date '1996-05-01' + interval '3 months' and exists ( select * from lineitem where l_orderkey = o_orderkey and l_commitdate < l_receiptdate ) group by o_orderpriority order by o_orderpriority;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select o_orderpriority, count(*) as order_count from orders where o_orderdate >= date '1994-02-01' and o_orderdate < date '1994-02-01' + interval '3 months' and exists ( select * from lineitem where l_orderkey = o_orderkey and l_commitdate < l_receiptdate ) group by o_orderpriority order by o_orderpriority;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select o_orderpriority, count(*) as order_count from orders where o_orderdate >= date '1996-09-01' and o_orderdate < date '1996-09-01' + interval '3 months' and exists ( select * from lineitem where l_orderkey = o_orderkey and l_commitdate < l_receiptdate ) group by o_orderpriority order by o_orderpriority;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select o_orderpriority, count(*) as order_count from orders where o_orderdate >= date '1994-06-01' and o_orderdate < date '1994-06-01' + interval '3 months' and exists ( select * from lineitem where l_orderkey = o_orderkey and l_commitdate < l_receiptdate ) group by o_orderpriority order by o_orderpriority;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select o_orderpriority, count(*) as order_count from orders where o_orderdate >= date '1996-12-01' and o_orderdate < date '1996-12-01' + interval '3 months' and exists ( select * from lineitem where l_orderkey = o_orderkey and l_commitdate < l_receiptdate ) group by o_orderpriority order by o_orderpriority;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select o_orderpriority, count(*) as order_count from orders where o_orderdate >= date '1994-09-01' and o_orderdate < date '1994-09-01' + interval '3 months' and exists ( select * from lineitem where l_orderkey = o_orderkey and l_commitdate < l_receiptdate ) group by o_orderpriority order by o_orderpriority;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select o_orderpriority, count(*) as order_count from orders where o_orderdate >= date '1997-04-01' and o_orderdate < date '1997-04-01' + interval '3 months' and exists ( select * from lineitem where l_orderkey = o_orderkey and l_commitdate < l_receiptdate ) group by o_orderpriority order by o_orderpriority;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select o_orderpriority, count(*) as order_count from orders where o_orderdate >= date '1995-01-01' and o_orderdate < date '1995-01-01' + interval '3 months' and exists ( select * from lineitem where l_orderkey = o_orderkey and l_commitdate < l_receiptdate ) group by o_orderpriority order by o_orderpriority;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select o_orderpriority, count(*) as order_count from orders where o_orderdate >= date '1997-08-01' and o_orderdate < date '1997-08-01' + interval '3 months' and exists ( select * from lineitem where l_orderkey = o_orderkey and l_commitdate < l_receiptdate ) group by o_orderpriority order by o_orderpriority;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select o_orderpriority, count(*) as order_count from orders where o_orderdate >= date '1995-05-01' and o_orderdate < date '1995-05-01' + interval '3 months' and exists ( select * from lineitem where l_orderkey = o_orderkey and l_commitdate < l_receiptdate ) group by o_orderpriority order by o_orderpriority;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select o_orderpriority, count(*) as order_count from orders where o_orderdate >= date '1993-02-01' and o_orderdate < date '1993-02-01' + interval '3 months' and exists ( select * from lineitem where l_orderkey = o_orderkey and l_commitdate < l_receiptdate ) group by o_orderpriority order by o_orderpriority;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select o_orderpriority, count(*) as order_count from orders where o_orderdate >= date '1995-09-01' and o_orderdate < date '1995-09-01' + interval '3 months' and exists ( select * from lineitem where l_orderkey = o_orderkey and l_commitdate < l_receiptdate ) group by o_orderpriority order by o_orderpriority;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select o_orderpriority, count(*) as order_count from orders where o_orderdate >= date '1993-06-01' and o_orderdate < date '1993-06-01' + interval '3 months' and exists ( select * from lineitem where l_orderkey = o_orderkey and l_commitdate < l_receiptdate ) group by o_orderpriority order by o_orderpriority;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select o_orderpriority, count(*) as order_count from orders where o_orderdate >= date '1996-01-01' and o_orderdate < date '1996-01-01' + interval '3 months' and exists ( select * from lineitem where l_orderkey = o_orderkey and l_commitdate < l_receiptdate ) group by o_orderpriority order by o_orderpriority;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select o_orderpriority, count(*) as order_count from orders where o_orderdate >= date '1993-09-01' and o_orderdate < date '1993-09-01' + interval '3 months' and exists ( select * from lineitem where l_orderkey = o_orderkey and l_commitdate < l_receiptdate ) group by o_orderpriority order by o_orderpriority;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select o_orderpriority, count(*) as order_count from orders where o_orderdate >= date '1996-04-01' and o_orderdate < date '1996-04-01' + interval '3 months' and exists ( select * from lineitem where l_orderkey = o_orderkey and l_commitdate < l_receiptdate ) group by o_orderpriority order by o_orderpriority;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select o_orderpriority, count(*) as order_count from orders where o_orderdate >= date '1994-01-01' and o_orderdate < date '1994-01-01' + interval '3 months' and exists ( select * from lineitem where l_orderkey = o_orderkey and l_commitdate < l_receiptdate ) group by o_orderpriority order by o_orderpriority;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select o_orderpriority, count(*) as order_count from orders where o_orderdate >= date '1996-08-01' and o_orderdate < date '1996-08-01' + interval '3 months' and exists ( select * from lineitem where l_orderkey = o_orderkey and l_commitdate < l_receiptdate ) group by o_orderpriority order by o_orderpriority;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select o_orderpriority, count(*) as order_count from orders where o_orderdate >= date '1994-05-01' and o_orderdate < date '1994-05-01' + interval '3 months' and exists ( select * from lineitem where l_orderkey = o_orderkey and l_commitdate < l_receiptdate ) group by o_orderpriority order by o_orderpriority;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select o_orderpriority, count(*) as order_count from orders where o_orderdate >= date '1996-12-01' and o_orderdate < date '1996-12-01' + interval '3 months' and exists ( select * from lineitem where l_orderkey = o_orderkey and l_commitdate < l_receiptdate ) group by o_orderpriority order by o_orderpriority;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select o_orderpriority, count(*) as order_count from orders where o_orderdate >= date '1994-09-01' and o_orderdate < date '1994-09-01' + interval '3 months' and exists ( select * from lineitem where l_orderkey = o_orderkey and l_commitdate < l_receiptdate ) group by o_orderpriority order by o_orderpriority;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select o_orderpriority, count(*) as order_count from orders where o_orderdate >= date '1997-04-01' and o_orderdate < date '1997-04-01' + interval '3 months' and exists ( select * from lineitem where l_orderkey = o_orderkey and l_commitdate < l_receiptdate ) group by o_orderpriority order by o_orderpriority;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select o_orderpriority, count(*) as order_count from orders where o_orderdate >= date '1995-01-01' and o_orderdate < date '1995-01-01' + interval '3 months' and exists ( select * from lineitem where l_orderkey = o_orderkey and l_commitdate < l_receiptdate ) group by o_orderpriority order by o_orderpriority;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select o_orderpriority, count(*) as order_count from orders where o_orderdate >= date '1997-08-01' and o_orderdate < date '1997-08-01' + interval '3 months' and exists ( select * from lineitem where l_orderkey = o_orderkey and l_commitdate < l_receiptdate ) group by o_orderpriority order by o_orderpriority;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select o_orderpriority, count(*) as order_count from orders where o_orderdate >= date '1995-04-01' and o_orderdate < date '1995-04-01' + interval '3 months' and exists ( select * from lineitem where l_orderkey = o_orderkey and l_commitdate < l_receiptdate ) group by o_orderpriority order by o_orderpriority;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select o_orderpriority, count(*) as order_count from orders where o_orderdate >= date '1993-01-01' and o_orderdate < date '1993-01-01' + interval '3 months' and exists ( select * from lineitem where l_orderkey = o_orderkey and l_commitdate < l_receiptdate ) group by o_orderpriority order by o_orderpriority;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select o_orderpriority, count(*) as order_count from orders where o_orderdate >= date '1995-08-01' and o_orderdate < date '1995-08-01' + interval '3 months' and exists ( select * from lineitem where l_orderkey = o_orderkey and l_commitdate < l_receiptdate ) group by o_orderpriority order by o_orderpriority;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select o_orderpriority, count(*) as order_count from orders where o_orderdate >= date '1993-05-01' and o_orderdate < date '1993-05-01' + interval '3 months' and exists ( select * from lineitem where l_orderkey = o_orderkey and l_commitdate < l_receiptdate ) group by o_orderpriority order by o_orderpriority;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select o_orderpriority, count(*) as order_count from orders where o_orderdate >= date '1995-12-01' and o_orderdate < date '1995-12-01' + interval '3 months' and exists ( select * from lineitem where l_orderkey = o_orderkey and l_commitdate < l_receiptdate ) group by o_orderpriority order by o_orderpriority;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select o_orderpriority, count(*) as order_count from orders where o_orderdate >= date '1993-09-01' and o_orderdate < date '1993-09-01' + interval '3 months' and exists ( select * from lineitem where l_orderkey = o_orderkey and l_commitdate < l_receiptdate ) group by o_orderpriority order by o_orderpriority;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select o_orderpriority, count(*) as order_count from orders where o_orderdate >= date '1996-04-01' and o_orderdate < date '1996-04-01' + interval '3 months' and exists ( select * from lineitem where l_orderkey = o_orderkey and l_commitdate < l_receiptdate ) group by o_orderpriority order by o_orderpriority;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select o_orderpriority, count(*) as order_count from orders where o_orderdate >= date '1994-01-01' and o_orderdate < date '1994-01-01' + interval '3 months' and exists ( select * from lineitem where l_orderkey = o_orderkey and l_commitdate < l_receiptdate ) group by o_orderpriority order by o_orderpriority;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select o_orderpriority, count(*) as order_count from orders where o_orderdate >= date '1996-08-01' and o_orderdate < date '1996-08-01' + interval '3 months' and exists ( select * from lineitem where l_orderkey = o_orderkey and l_commitdate < l_receiptdate ) group by o_orderpriority order by o_orderpriority;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select o_orderpriority, count(*) as order_count from orders where o_orderdate >= date '1994-05-01' and o_orderdate < date '1994-05-01' + interval '3 months' and exists ( select * from lineitem where l_orderkey = o_orderkey and l_commitdate < l_receiptdate ) group by o_orderpriority order by o_orderpriority;

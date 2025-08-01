EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  sum(cs_ext_discount_amt)  as "excess discount amount" 
from 
   catalog_sales 
   ,item 
   ,date_dim
where
i_manufact_id = 269
and i_item_sk = cs_item_sk 
and d_date between '1998-03-18' and 
        (cast('1998-03-18' as date) + 90)
and d_date_sk = cs_sold_date_sk 
and cs_ext_discount_amt  
     > ( 
         select 
            1.3 * avg(cs_ext_discount_amt) 
         from 
            catalog_sales 
           ,date_dim
         where 
              cs_item_sk = i_item_sk 
          and d_date between '1998-03-18' and
                             (cast('1998-03-18' as date) + 90)
          and d_date_sk = cs_sold_date_sk 
      ) 
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  sum(cs_ext_discount_amt)  as "excess discount amount" 
from 
   catalog_sales 
   ,item 
   ,date_dim
where
i_manufact_id = 305
and i_item_sk = cs_item_sk 
and d_date between '1999-01-14' and 
        (cast('1999-01-14' as date) + 90)
and d_date_sk = cs_sold_date_sk 
and cs_ext_discount_amt  
     > ( 
         select 
            1.3 * avg(cs_ext_discount_amt) 
         from 
            catalog_sales 
           ,date_dim
         where 
              cs_item_sk = i_item_sk 
          and d_date between '1999-01-14' and
                             (cast('1999-01-14' as date) + 90)
          and d_date_sk = cs_sold_date_sk 
      ) 
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  sum(cs_ext_discount_amt)  as "excess discount amount" 
from 
   catalog_sales 
   ,item 
   ,date_dim
where
i_manufact_id = 614
and i_item_sk = cs_item_sk 
and d_date between '2002-02-18' and 
        (cast('2002-02-18' as date) + 90)
and d_date_sk = cs_sold_date_sk 
and cs_ext_discount_amt  
     > ( 
         select 
            1.3 * avg(cs_ext_discount_amt) 
         from 
            catalog_sales 
           ,date_dim
         where 
              cs_item_sk = i_item_sk 
          and d_date between '2002-02-18' and
                             (cast('2002-02-18' as date) + 90)
          and d_date_sk = cs_sold_date_sk 
      ) 
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  sum(cs_ext_discount_amt)  as "excess discount amount" 
from 
   catalog_sales 
   ,item 
   ,date_dim
where
i_manufact_id = 137
and i_item_sk = cs_item_sk 
and d_date between '2000-02-14' and 
        (cast('2000-02-14' as date) + 90)
and d_date_sk = cs_sold_date_sk 
and cs_ext_discount_amt  
     > ( 
         select 
            1.3 * avg(cs_ext_discount_amt) 
         from 
            catalog_sales 
           ,date_dim
         where 
              cs_item_sk = i_item_sk 
          and d_date between '2000-02-14' and
                             (cast('2000-02-14' as date) + 90)
          and d_date_sk = cs_sold_date_sk 
      ) 
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  sum(cs_ext_discount_amt)  as "excess discount amount" 
from 
   catalog_sales 
   ,item 
   ,date_dim
where
i_manufact_id = 782
and i_item_sk = cs_item_sk 
and d_date between '2002-01-24' and 
        (cast('2002-01-24' as date) + 90)
and d_date_sk = cs_sold_date_sk 
and cs_ext_discount_amt  
     > ( 
         select 
            1.3 * avg(cs_ext_discount_amt) 
         from 
            catalog_sales 
           ,date_dim
         where 
              cs_item_sk = i_item_sk 
          and d_date between '2002-01-24' and
                             (cast('2002-01-24' as date) + 90)
          and d_date_sk = cs_sold_date_sk 
      ) 
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  sum(cs_ext_discount_amt)  as "excess discount amount" 
from 
   catalog_sales 
   ,item 
   ,date_dim
where
i_manufact_id = 602
and i_item_sk = cs_item_sk 
and d_date between '2001-02-04' and 
        (cast('2001-02-04' as date) + 90)
and d_date_sk = cs_sold_date_sk 
and cs_ext_discount_amt  
     > ( 
         select 
            1.3 * avg(cs_ext_discount_amt) 
         from 
            catalog_sales 
           ,date_dim
         where 
              cs_item_sk = i_item_sk 
          and d_date between '2001-02-04' and
                             (cast('2001-02-04' as date) + 90)
          and d_date_sk = cs_sold_date_sk 
      ) 
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  sum(cs_ext_discount_amt)  as "excess discount amount" 
from 
   catalog_sales 
   ,item 
   ,date_dim
where
i_manufact_id = 577
and i_item_sk = cs_item_sk 
and d_date between '1998-03-18' and 
        (cast('1998-03-18' as date) + 90)
and d_date_sk = cs_sold_date_sk 
and cs_ext_discount_amt  
     > ( 
         select 
            1.3 * avg(cs_ext_discount_amt) 
         from 
            catalog_sales 
           ,date_dim
         where 
              cs_item_sk = i_item_sk 
          and d_date between '1998-03-18' and
                             (cast('1998-03-18' as date) + 90)
          and d_date_sk = cs_sold_date_sk 
      ) 
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  sum(cs_ext_discount_amt)  as "excess discount amount" 
from 
   catalog_sales 
   ,item 
   ,date_dim
where
i_manufact_id = 423
and i_item_sk = cs_item_sk 
and d_date between '1999-03-22' and 
        (cast('1999-03-22' as date) + 90)
and d_date_sk = cs_sold_date_sk 
and cs_ext_discount_amt  
     > ( 
         select 
            1.3 * avg(cs_ext_discount_amt) 
         from 
            catalog_sales 
           ,date_dim
         where 
              cs_item_sk = i_item_sk 
          and d_date between '1999-03-22' and
                             (cast('1999-03-22' as date) + 90)
          and d_date_sk = cs_sold_date_sk 
      ) 
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  sum(cs_ext_discount_amt)  as "excess discount amount" 
from 
   catalog_sales 
   ,item 
   ,date_dim
where
i_manufact_id = 284
and i_item_sk = cs_item_sk 
and d_date between '2001-01-07' and 
        (cast('2001-01-07' as date) + 90)
and d_date_sk = cs_sold_date_sk 
and cs_ext_discount_amt  
     > ( 
         select 
            1.3 * avg(cs_ext_discount_amt) 
         from 
            catalog_sales 
           ,date_dim
         where 
              cs_item_sk = i_item_sk 
          and d_date between '2001-01-07' and
                             (cast('2001-01-07' as date) + 90)
          and d_date_sk = cs_sold_date_sk 
      ) 
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  sum(cs_ext_discount_amt)  as "excess discount amount" 
from 
   catalog_sales 
   ,item 
   ,date_dim
where
i_manufact_id = 817
and i_item_sk = cs_item_sk 
and d_date between '1999-02-17' and 
        (cast('1999-02-17' as date) + 90)
and d_date_sk = cs_sold_date_sk 
and cs_ext_discount_amt  
     > ( 
         select 
            1.3 * avg(cs_ext_discount_amt) 
         from 
            catalog_sales 
           ,date_dim
         where 
              cs_item_sk = i_item_sk 
          and d_date between '1999-02-17' and
                             (cast('1999-02-17' as date) + 90)
          and d_date_sk = cs_sold_date_sk 
      ) 
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  sum(cs_ext_discount_amt)  as "excess discount amount" 
from 
   catalog_sales 
   ,item 
   ,date_dim
where
i_manufact_id = 765
and i_item_sk = cs_item_sk 
and d_date between '1998-02-22' and 
        (cast('1998-02-22' as date) + 90)
and d_date_sk = cs_sold_date_sk 
and cs_ext_discount_amt  
     > ( 
         select 
            1.3 * avg(cs_ext_discount_amt) 
         from 
            catalog_sales 
           ,date_dim
         where 
              cs_item_sk = i_item_sk 
          and d_date between '1998-02-22' and
                             (cast('1998-02-22' as date) + 90)
          and d_date_sk = cs_sold_date_sk 
      ) 
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  sum(cs_ext_discount_amt)  as "excess discount amount" 
from 
   catalog_sales 
   ,item 
   ,date_dim
where
i_manufact_id = 918
and i_item_sk = cs_item_sk 
and d_date between '2000-01-28' and 
        (cast('2000-01-28' as date) + 90)
and d_date_sk = cs_sold_date_sk 
and cs_ext_discount_amt  
     > ( 
         select 
            1.3 * avg(cs_ext_discount_amt) 
         from 
            catalog_sales 
           ,date_dim
         where 
              cs_item_sk = i_item_sk 
          and d_date between '2000-01-28' and
                             (cast('2000-01-28' as date) + 90)
          and d_date_sk = cs_sold_date_sk 
      ) 
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  sum(cs_ext_discount_amt)  as "excess discount amount" 
from 
   catalog_sales 
   ,item 
   ,date_dim
where
i_manufact_id = 68
and i_item_sk = cs_item_sk 
and d_date between '2001-01-12' and 
        (cast('2001-01-12' as date) + 90)
and d_date_sk = cs_sold_date_sk 
and cs_ext_discount_amt  
     > ( 
         select 
            1.3 * avg(cs_ext_discount_amt) 
         from 
            catalog_sales 
           ,date_dim
         where 
              cs_item_sk = i_item_sk 
          and d_date between '2001-01-12' and
                             (cast('2001-01-12' as date) + 90)
          and d_date_sk = cs_sold_date_sk 
      ) 
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  sum(cs_ext_discount_amt)  as "excess discount amount" 
from 
   catalog_sales 
   ,item 
   ,date_dim
where
i_manufact_id = 223
and i_item_sk = cs_item_sk 
and d_date between '2002-01-18' and 
        (cast('2002-01-18' as date) + 90)
and d_date_sk = cs_sold_date_sk 
and cs_ext_discount_amt  
     > ( 
         select 
            1.3 * avg(cs_ext_discount_amt) 
         from 
            catalog_sales 
           ,date_dim
         where 
              cs_item_sk = i_item_sk 
          and d_date between '2002-01-18' and
                             (cast('2002-01-18' as date) + 90)
          and d_date_sk = cs_sold_date_sk 
      ) 
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  sum(cs_ext_discount_amt)  as "excess discount amount" 
from 
   catalog_sales 
   ,item 
   ,date_dim
where
i_manufact_id = 717
and i_item_sk = cs_item_sk 
and d_date between '2002-01-25' and 
        (cast('2002-01-25' as date) + 90)
and d_date_sk = cs_sold_date_sk 
and cs_ext_discount_amt  
     > ( 
         select 
            1.3 * avg(cs_ext_discount_amt) 
         from 
            catalog_sales 
           ,date_dim
         where 
              cs_item_sk = i_item_sk 
          and d_date between '2002-01-25' and
                             (cast('2002-01-25' as date) + 90)
          and d_date_sk = cs_sold_date_sk 
      ) 
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  sum(cs_ext_discount_amt)  as "excess discount amount" 
from 
   catalog_sales 
   ,item 
   ,date_dim
where
i_manufact_id = 256
and i_item_sk = cs_item_sk 
and d_date between '2000-01-27' and 
        (cast('2000-01-27' as date) + 90)
and d_date_sk = cs_sold_date_sk 
and cs_ext_discount_amt  
     > ( 
         select 
            1.3 * avg(cs_ext_discount_amt) 
         from 
            catalog_sales 
           ,date_dim
         where 
              cs_item_sk = i_item_sk 
          and d_date between '2000-01-27' and
                             (cast('2000-01-27' as date) + 90)
          and d_date_sk = cs_sold_date_sk 
      ) 
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  sum(cs_ext_discount_amt)  as "excess discount amount" 
from 
   catalog_sales 
   ,item 
   ,date_dim
where
i_manufact_id = 200
and i_item_sk = cs_item_sk 
and d_date between '2000-02-06' and 
        (cast('2000-02-06' as date) + 90)
and d_date_sk = cs_sold_date_sk 
and cs_ext_discount_amt  
     > ( 
         select 
            1.3 * avg(cs_ext_discount_amt) 
         from 
            catalog_sales 
           ,date_dim
         where 
              cs_item_sk = i_item_sk 
          and d_date between '2000-02-06' and
                             (cast('2000-02-06' as date) + 90)
          and d_date_sk = cs_sold_date_sk 
      ) 
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  sum(cs_ext_discount_amt)  as "excess discount amount" 
from 
   catalog_sales 
   ,item 
   ,date_dim
where
i_manufact_id = 550
and i_item_sk = cs_item_sk 
and d_date between '2002-03-21' and 
        (cast('2002-03-21' as date) + 90)
and d_date_sk = cs_sold_date_sk 
and cs_ext_discount_amt  
     > ( 
         select 
            1.3 * avg(cs_ext_discount_amt) 
         from 
            catalog_sales 
           ,date_dim
         where 
              cs_item_sk = i_item_sk 
          and d_date between '2002-03-21' and
                             (cast('2002-03-21' as date) + 90)
          and d_date_sk = cs_sold_date_sk 
      ) 
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  sum(cs_ext_discount_amt)  as "excess discount amount" 
from 
   catalog_sales 
   ,item 
   ,date_dim
where
i_manufact_id = 493
and i_item_sk = cs_item_sk 
and d_date between '2000-01-17' and 
        (cast('2000-01-17' as date) + 90)
and d_date_sk = cs_sold_date_sk 
and cs_ext_discount_amt  
     > ( 
         select 
            1.3 * avg(cs_ext_discount_amt) 
         from 
            catalog_sales 
           ,date_dim
         where 
              cs_item_sk = i_item_sk 
          and d_date between '2000-01-17' and
                             (cast('2000-01-17' as date) + 90)
          and d_date_sk = cs_sold_date_sk 
      ) 
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  sum(cs_ext_discount_amt)  as "excess discount amount" 
from 
   catalog_sales 
   ,item 
   ,date_dim
where
i_manufact_id = 550
and i_item_sk = cs_item_sk 
and d_date between '2001-03-14' and 
        (cast('2001-03-14' as date) + 90)
and d_date_sk = cs_sold_date_sk 
and cs_ext_discount_amt  
     > ( 
         select 
            1.3 * avg(cs_ext_discount_amt) 
         from 
            catalog_sales 
           ,date_dim
         where 
              cs_item_sk = i_item_sk 
          and d_date between '2001-03-14' and
                             (cast('2001-03-14' as date) + 90)
          and d_date_sk = cs_sold_date_sk 
      ) 
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  sum(cs_ext_discount_amt)  as "excess discount amount" 
from 
   catalog_sales 
   ,item 
   ,date_dim
where
i_manufact_id = 890
and i_item_sk = cs_item_sk 
and d_date between '1998-03-01' and 
        (cast('1998-03-01' as date) + 90)
and d_date_sk = cs_sold_date_sk 
and cs_ext_discount_amt  
     > ( 
         select 
            1.3 * avg(cs_ext_discount_amt) 
         from 
            catalog_sales 
           ,date_dim
         where 
              cs_item_sk = i_item_sk 
          and d_date between '1998-03-01' and
                             (cast('1998-03-01' as date) + 90)
          and d_date_sk = cs_sold_date_sk 
      ) 
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  sum(cs_ext_discount_amt)  as "excess discount amount" 
from 
   catalog_sales 
   ,item 
   ,date_dim
where
i_manufact_id = 936
and i_item_sk = cs_item_sk 
and d_date between '2000-03-20' and 
        (cast('2000-03-20' as date) + 90)
and d_date_sk = cs_sold_date_sk 
and cs_ext_discount_amt  
     > ( 
         select 
            1.3 * avg(cs_ext_discount_amt) 
         from 
            catalog_sales 
           ,date_dim
         where 
              cs_item_sk = i_item_sk 
          and d_date between '2000-03-20' and
                             (cast('2000-03-20' as date) + 90)
          and d_date_sk = cs_sold_date_sk 
      ) 
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  sum(cs_ext_discount_amt)  as "excess discount amount" 
from 
   catalog_sales 
   ,item 
   ,date_dim
where
i_manufact_id = 400
and i_item_sk = cs_item_sk 
and d_date between '2002-01-09' and 
        (cast('2002-01-09' as date) + 90)
and d_date_sk = cs_sold_date_sk 
and cs_ext_discount_amt  
     > ( 
         select 
            1.3 * avg(cs_ext_discount_amt) 
         from 
            catalog_sales 
           ,date_dim
         where 
              cs_item_sk = i_item_sk 
          and d_date between '2002-01-09' and
                             (cast('2002-01-09' as date) + 90)
          and d_date_sk = cs_sold_date_sk 
      ) 
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  sum(cs_ext_discount_amt)  as "excess discount amount" 
from 
   catalog_sales 
   ,item 
   ,date_dim
where
i_manufact_id = 191
and i_item_sk = cs_item_sk 
and d_date between '1999-03-12' and 
        (cast('1999-03-12' as date) + 90)
and d_date_sk = cs_sold_date_sk 
and cs_ext_discount_amt  
     > ( 
         select 
            1.3 * avg(cs_ext_discount_amt) 
         from 
            catalog_sales 
           ,date_dim
         where 
              cs_item_sk = i_item_sk 
          and d_date between '1999-03-12' and
                             (cast('1999-03-12' as date) + 90)
          and d_date_sk = cs_sold_date_sk 
      ) 
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  sum(cs_ext_discount_amt)  as "excess discount amount" 
from 
   catalog_sales 
   ,item 
   ,date_dim
where
i_manufact_id = 543
and i_item_sk = cs_item_sk 
and d_date between '2002-02-12' and 
        (cast('2002-02-12' as date) + 90)
and d_date_sk = cs_sold_date_sk 
and cs_ext_discount_amt  
     > ( 
         select 
            1.3 * avg(cs_ext_discount_amt) 
         from 
            catalog_sales 
           ,date_dim
         where 
              cs_item_sk = i_item_sk 
          and d_date between '2002-02-12' and
                             (cast('2002-02-12' as date) + 90)
          and d_date_sk = cs_sold_date_sk 
      ) 
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  sum(cs_ext_discount_amt)  as "excess discount amount" 
from 
   catalog_sales 
   ,item 
   ,date_dim
where
i_manufact_id = 948
and i_item_sk = cs_item_sk 
and d_date between '2000-01-28' and 
        (cast('2000-01-28' as date) + 90)
and d_date_sk = cs_sold_date_sk 
and cs_ext_discount_amt  
     > ( 
         select 
            1.3 * avg(cs_ext_discount_amt) 
         from 
            catalog_sales 
           ,date_dim
         where 
              cs_item_sk = i_item_sk 
          and d_date between '2000-01-28' and
                             (cast('2000-01-28' as date) + 90)
          and d_date_sk = cs_sold_date_sk 
      ) 
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  sum(cs_ext_discount_amt)  as "excess discount amount" 
from 
   catalog_sales 
   ,item 
   ,date_dim
where
i_manufact_id = 828
and i_item_sk = cs_item_sk 
and d_date between '2001-02-11' and 
        (cast('2001-02-11' as date) + 90)
and d_date_sk = cs_sold_date_sk 
and cs_ext_discount_amt  
     > ( 
         select 
            1.3 * avg(cs_ext_discount_amt) 
         from 
            catalog_sales 
           ,date_dim
         where 
              cs_item_sk = i_item_sk 
          and d_date between '2001-02-11' and
                             (cast('2001-02-11' as date) + 90)
          and d_date_sk = cs_sold_date_sk 
      ) 
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  sum(cs_ext_discount_amt)  as "excess discount amount" 
from 
   catalog_sales 
   ,item 
   ,date_dim
where
i_manufact_id = 130
and i_item_sk = cs_item_sk 
and d_date between '1999-01-19' and 
        (cast('1999-01-19' as date) + 90)
and d_date_sk = cs_sold_date_sk 
and cs_ext_discount_amt  
     > ( 
         select 
            1.3 * avg(cs_ext_discount_amt) 
         from 
            catalog_sales 
           ,date_dim
         where 
              cs_item_sk = i_item_sk 
          and d_date between '1999-01-19' and
                             (cast('1999-01-19' as date) + 90)
          and d_date_sk = cs_sold_date_sk 
      ) 
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  sum(cs_ext_discount_amt)  as "excess discount amount" 
from 
   catalog_sales 
   ,item 
   ,date_dim
where
i_manufact_id = 700
and i_item_sk = cs_item_sk 
and d_date between '2000-03-29' and 
        (cast('2000-03-29' as date) + 90)
and d_date_sk = cs_sold_date_sk 
and cs_ext_discount_amt  
     > ( 
         select 
            1.3 * avg(cs_ext_discount_amt) 
         from 
            catalog_sales 
           ,date_dim
         where 
              cs_item_sk = i_item_sk 
          and d_date between '2000-03-29' and
                             (cast('2000-03-29' as date) + 90)
          and d_date_sk = cs_sold_date_sk 
      ) 
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  sum(cs_ext_discount_amt)  as "excess discount amount" 
from 
   catalog_sales 
   ,item 
   ,date_dim
where
i_manufact_id = 637
and i_item_sk = cs_item_sk 
and d_date between '2002-02-16' and 
        (cast('2002-02-16' as date) + 90)
and d_date_sk = cs_sold_date_sk 
and cs_ext_discount_amt  
     > ( 
         select 
            1.3 * avg(cs_ext_discount_amt) 
         from 
            catalog_sales 
           ,date_dim
         where 
              cs_item_sk = i_item_sk 
          and d_date between '2002-02-16' and
                             (cast('2002-02-16' as date) + 90)
          and d_date_sk = cs_sold_date_sk 
      ) 
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  sum(cs_ext_discount_amt)  as "excess discount amount" 
from 
   catalog_sales 
   ,item 
   ,date_dim
where
i_manufact_id = 954
and i_item_sk = cs_item_sk 
and d_date between '2002-01-21' and 
        (cast('2002-01-21' as date) + 90)
and d_date_sk = cs_sold_date_sk 
and cs_ext_discount_amt  
     > ( 
         select 
            1.3 * avg(cs_ext_discount_amt) 
         from 
            catalog_sales 
           ,date_dim
         where 
              cs_item_sk = i_item_sk 
          and d_date between '2002-01-21' and
                             (cast('2002-01-21' as date) + 90)
          and d_date_sk = cs_sold_date_sk 
      ) 
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  sum(cs_ext_discount_amt)  as "excess discount amount" 
from 
   catalog_sales 
   ,item 
   ,date_dim
where
i_manufact_id = 434
and i_item_sk = cs_item_sk 
and d_date between '1998-02-25' and 
        (cast('1998-02-25' as date) + 90)
and d_date_sk = cs_sold_date_sk 
and cs_ext_discount_amt  
     > ( 
         select 
            1.3 * avg(cs_ext_discount_amt) 
         from 
            catalog_sales 
           ,date_dim
         where 
              cs_item_sk = i_item_sk 
          and d_date between '1998-02-25' and
                             (cast('1998-02-25' as date) + 90)
          and d_date_sk = cs_sold_date_sk 
      ) 
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  sum(cs_ext_discount_amt)  as "excess discount amount" 
from 
   catalog_sales 
   ,item 
   ,date_dim
where
i_manufact_id = 379
and i_item_sk = cs_item_sk 
and d_date between '2001-03-13' and 
        (cast('2001-03-13' as date) + 90)
and d_date_sk = cs_sold_date_sk 
and cs_ext_discount_amt  
     > ( 
         select 
            1.3 * avg(cs_ext_discount_amt) 
         from 
            catalog_sales 
           ,date_dim
         where 
              cs_item_sk = i_item_sk 
          and d_date between '2001-03-13' and
                             (cast('2001-03-13' as date) + 90)
          and d_date_sk = cs_sold_date_sk 
      ) 
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  sum(cs_ext_discount_amt)  as "excess discount amount" 
from 
   catalog_sales 
   ,item 
   ,date_dim
where
i_manufact_id = 569
and i_item_sk = cs_item_sk 
and d_date between '2000-02-15' and 
        (cast('2000-02-15' as date) + 90)
and d_date_sk = cs_sold_date_sk 
and cs_ext_discount_amt  
     > ( 
         select 
            1.3 * avg(cs_ext_discount_amt) 
         from 
            catalog_sales 
           ,date_dim
         where 
              cs_item_sk = i_item_sk 
          and d_date between '2000-02-15' and
                             (cast('2000-02-15' as date) + 90)
          and d_date_sk = cs_sold_date_sk 
      ) 
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  sum(cs_ext_discount_amt)  as "excess discount amount" 
from 
   catalog_sales 
   ,item 
   ,date_dim
where
i_manufact_id = 255
and i_item_sk = cs_item_sk 
and d_date between '2002-02-08' and 
        (cast('2002-02-08' as date) + 90)
and d_date_sk = cs_sold_date_sk 
and cs_ext_discount_amt  
     > ( 
         select 
            1.3 * avg(cs_ext_discount_amt) 
         from 
            catalog_sales 
           ,date_dim
         where 
              cs_item_sk = i_item_sk 
          and d_date between '2002-02-08' and
                             (cast('2002-02-08' as date) + 90)
          and d_date_sk = cs_sold_date_sk 
      ) 
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  sum(cs_ext_discount_amt)  as "excess discount amount" 
from 
   catalog_sales 
   ,item 
   ,date_dim
where
i_manufact_id = 961
and i_item_sk = cs_item_sk 
and d_date between '1998-03-13' and 
        (cast('1998-03-13' as date) + 90)
and d_date_sk = cs_sold_date_sk 
and cs_ext_discount_amt  
     > ( 
         select 
            1.3 * avg(cs_ext_discount_amt) 
         from 
            catalog_sales 
           ,date_dim
         where 
              cs_item_sk = i_item_sk 
          and d_date between '1998-03-13' and
                             (cast('1998-03-13' as date) + 90)
          and d_date_sk = cs_sold_date_sk 
      ) 
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  sum(cs_ext_discount_amt)  as "excess discount amount" 
from 
   catalog_sales 
   ,item 
   ,date_dim
where
i_manufact_id = 255
and i_item_sk = cs_item_sk 
and d_date between '2002-03-25' and 
        (cast('2002-03-25' as date) + 90)
and d_date_sk = cs_sold_date_sk 
and cs_ext_discount_amt  
     > ( 
         select 
            1.3 * avg(cs_ext_discount_amt) 
         from 
            catalog_sales 
           ,date_dim
         where 
              cs_item_sk = i_item_sk 
          and d_date between '2002-03-25' and
                             (cast('2002-03-25' as date) + 90)
          and d_date_sk = cs_sold_date_sk 
      ) 
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  sum(cs_ext_discount_amt)  as "excess discount amount" 
from 
   catalog_sales 
   ,item 
   ,date_dim
where
i_manufact_id = 175
and i_item_sk = cs_item_sk 
and d_date between '1998-03-11' and 
        (cast('1998-03-11' as date) + 90)
and d_date_sk = cs_sold_date_sk 
and cs_ext_discount_amt  
     > ( 
         select 
            1.3 * avg(cs_ext_discount_amt) 
         from 
            catalog_sales 
           ,date_dim
         where 
              cs_item_sk = i_item_sk 
          and d_date between '1998-03-11' and
                             (cast('1998-03-11' as date) + 90)
          and d_date_sk = cs_sold_date_sk 
      ) 
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  sum(cs_ext_discount_amt)  as "excess discount amount" 
from 
   catalog_sales 
   ,item 
   ,date_dim
where
i_manufact_id = 766
and i_item_sk = cs_item_sk 
and d_date between '2001-01-08' and 
        (cast('2001-01-08' as date) + 90)
and d_date_sk = cs_sold_date_sk 
and cs_ext_discount_amt  
     > ( 
         select 
            1.3 * avg(cs_ext_discount_amt) 
         from 
            catalog_sales 
           ,date_dim
         where 
              cs_item_sk = i_item_sk 
          and d_date between '2001-01-08' and
                             (cast('2001-01-08' as date) + 90)
          and d_date_sk = cs_sold_date_sk 
      ) 
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  sum(cs_ext_discount_amt)  as "excess discount amount" 
from 
   catalog_sales 
   ,item 
   ,date_dim
where
i_manufact_id = 645
and i_item_sk = cs_item_sk 
and d_date between '2001-03-05' and 
        (cast('2001-03-05' as date) + 90)
and d_date_sk = cs_sold_date_sk 
and cs_ext_discount_amt  
     > ( 
         select 
            1.3 * avg(cs_ext_discount_amt) 
         from 
            catalog_sales 
           ,date_dim
         where 
              cs_item_sk = i_item_sk 
          and d_date between '2001-03-05' and
                             (cast('2001-03-05' as date) + 90)
          and d_date_sk = cs_sold_date_sk 
      ) 
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  sum(cs_ext_discount_amt)  as "excess discount amount" 
from 
   catalog_sales 
   ,item 
   ,date_dim
where
i_manufact_id = 955
and i_item_sk = cs_item_sk 
and d_date between '1998-03-30' and 
        (cast('1998-03-30' as date) + 90)
and d_date_sk = cs_sold_date_sk 
and cs_ext_discount_amt  
     > ( 
         select 
            1.3 * avg(cs_ext_discount_amt) 
         from 
            catalog_sales 
           ,date_dim
         where 
              cs_item_sk = i_item_sk 
          and d_date between '1998-03-30' and
                             (cast('1998-03-30' as date) + 90)
          and d_date_sk = cs_sold_date_sk 
      ) 
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  sum(cs_ext_discount_amt)  as "excess discount amount" 
from 
   catalog_sales 
   ,item 
   ,date_dim
where
i_manufact_id = 35
and i_item_sk = cs_item_sk 
and d_date between '2000-03-02' and 
        (cast('2000-03-02' as date) + 90)
and d_date_sk = cs_sold_date_sk 
and cs_ext_discount_amt  
     > ( 
         select 
            1.3 * avg(cs_ext_discount_amt) 
         from 
            catalog_sales 
           ,date_dim
         where 
              cs_item_sk = i_item_sk 
          and d_date between '2000-03-02' and
                             (cast('2000-03-02' as date) + 90)
          and d_date_sk = cs_sold_date_sk 
      ) 
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  sum(cs_ext_discount_amt)  as "excess discount amount" 
from 
   catalog_sales 
   ,item 
   ,date_dim
where
i_manufact_id = 680
and i_item_sk = cs_item_sk 
and d_date between '2001-03-26' and 
        (cast('2001-03-26' as date) + 90)
and d_date_sk = cs_sold_date_sk 
and cs_ext_discount_amt  
     > ( 
         select 
            1.3 * avg(cs_ext_discount_amt) 
         from 
            catalog_sales 
           ,date_dim
         where 
              cs_item_sk = i_item_sk 
          and d_date between '2001-03-26' and
                             (cast('2001-03-26' as date) + 90)
          and d_date_sk = cs_sold_date_sk 
      ) 
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  sum(cs_ext_discount_amt)  as "excess discount amount" 
from 
   catalog_sales 
   ,item 
   ,date_dim
where
i_manufact_id = 298
and i_item_sk = cs_item_sk 
and d_date between '1998-03-16' and 
        (cast('1998-03-16' as date) + 90)
and d_date_sk = cs_sold_date_sk 
and cs_ext_discount_amt  
     > ( 
         select 
            1.3 * avg(cs_ext_discount_amt) 
         from 
            catalog_sales 
           ,date_dim
         where 
              cs_item_sk = i_item_sk 
          and d_date between '1998-03-16' and
                             (cast('1998-03-16' as date) + 90)
          and d_date_sk = cs_sold_date_sk 
      ) 
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  sum(cs_ext_discount_amt)  as "excess discount amount" 
from 
   catalog_sales 
   ,item 
   ,date_dim
where
i_manufact_id = 940
and i_item_sk = cs_item_sk 
and d_date between '2002-03-31' and 
        (cast('2002-03-31' as date) + 90)
and d_date_sk = cs_sold_date_sk 
and cs_ext_discount_amt  
     > ( 
         select 
            1.3 * avg(cs_ext_discount_amt) 
         from 
            catalog_sales 
           ,date_dim
         where 
              cs_item_sk = i_item_sk 
          and d_date between '2002-03-31' and
                             (cast('2002-03-31' as date) + 90)
          and d_date_sk = cs_sold_date_sk 
      ) 
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  sum(cs_ext_discount_amt)  as "excess discount amount" 
from 
   catalog_sales 
   ,item 
   ,date_dim
where
i_manufact_id = 376
and i_item_sk = cs_item_sk 
and d_date between '1998-02-17' and 
        (cast('1998-02-17' as date) + 90)
and d_date_sk = cs_sold_date_sk 
and cs_ext_discount_amt  
     > ( 
         select 
            1.3 * avg(cs_ext_discount_amt) 
         from 
            catalog_sales 
           ,date_dim
         where 
              cs_item_sk = i_item_sk 
          and d_date between '1998-02-17' and
                             (cast('1998-02-17' as date) + 90)
          and d_date_sk = cs_sold_date_sk 
      ) 
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  sum(cs_ext_discount_amt)  as "excess discount amount" 
from 
   catalog_sales 
   ,item 
   ,date_dim
where
i_manufact_id = 583
and i_item_sk = cs_item_sk 
and d_date between '2000-03-23' and 
        (cast('2000-03-23' as date) + 90)
and d_date_sk = cs_sold_date_sk 
and cs_ext_discount_amt  
     > ( 
         select 
            1.3 * avg(cs_ext_discount_amt) 
         from 
            catalog_sales 
           ,date_dim
         where 
              cs_item_sk = i_item_sk 
          and d_date between '2000-03-23' and
                             (cast('2000-03-23' as date) + 90)
          and d_date_sk = cs_sold_date_sk 
      ) 
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  sum(cs_ext_discount_amt)  as "excess discount amount" 
from 
   catalog_sales 
   ,item 
   ,date_dim
where
i_manufact_id = 447
and i_item_sk = cs_item_sk 
and d_date between '2002-01-09' and 
        (cast('2002-01-09' as date) + 90)
and d_date_sk = cs_sold_date_sk 
and cs_ext_discount_amt  
     > ( 
         select 
            1.3 * avg(cs_ext_discount_amt) 
         from 
            catalog_sales 
           ,date_dim
         where 
              cs_item_sk = i_item_sk 
          and d_date between '2002-01-09' and
                             (cast('2002-01-09' as date) + 90)
          and d_date_sk = cs_sold_date_sk 
      ) 
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  sum(cs_ext_discount_amt)  as "excess discount amount" 
from 
   catalog_sales 
   ,item 
   ,date_dim
where
i_manufact_id = 86
and i_item_sk = cs_item_sk 
and d_date between '2002-03-17' and 
        (cast('2002-03-17' as date) + 90)
and d_date_sk = cs_sold_date_sk 
and cs_ext_discount_amt  
     > ( 
         select 
            1.3 * avg(cs_ext_discount_amt) 
         from 
            catalog_sales 
           ,date_dim
         where 
              cs_item_sk = i_item_sk 
          and d_date between '2002-03-17' and
                             (cast('2002-03-17' as date) + 90)
          and d_date_sk = cs_sold_date_sk 
      ) 
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  sum(cs_ext_discount_amt)  as "excess discount amount" 
from 
   catalog_sales 
   ,item 
   ,date_dim
where
i_manufact_id = 427
and i_item_sk = cs_item_sk 
and d_date between '2001-03-05' and 
        (cast('2001-03-05' as date) + 90)
and d_date_sk = cs_sold_date_sk 
and cs_ext_discount_amt  
     > ( 
         select 
            1.3 * avg(cs_ext_discount_amt) 
         from 
            catalog_sales 
           ,date_dim
         where 
              cs_item_sk = i_item_sk 
          and d_date between '2001-03-05' and
                             (cast('2001-03-05' as date) + 90)
          and d_date_sk = cs_sold_date_sk 
      ) 
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  sum(cs_ext_discount_amt)  as "excess discount amount" 
from 
   catalog_sales 
   ,item 
   ,date_dim
where
i_manufact_id = 553
and i_item_sk = cs_item_sk 
and d_date between '2000-02-22' and 
        (cast('2000-02-22' as date) + 90)
and d_date_sk = cs_sold_date_sk 
and cs_ext_discount_amt  
     > ( 
         select 
            1.3 * avg(cs_ext_discount_amt) 
         from 
            catalog_sales 
           ,date_dim
         where 
              cs_item_sk = i_item_sk 
          and d_date between '2000-02-22' and
                             (cast('2000-02-22' as date) + 90)
          and d_date_sk = cs_sold_date_sk 
      ) 
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  sum(cs_ext_discount_amt)  as "excess discount amount" 
from 
   catalog_sales 
   ,item 
   ,date_dim
where
i_manufact_id = 451
and i_item_sk = cs_item_sk 
and d_date between '2002-03-25' and 
        (cast('2002-03-25' as date) + 90)
and d_date_sk = cs_sold_date_sk 
and cs_ext_discount_amt  
     > ( 
         select 
            1.3 * avg(cs_ext_discount_amt) 
         from 
            catalog_sales 
           ,date_dim
         where 
              cs_item_sk = i_item_sk 
          and d_date between '2002-03-25' and
                             (cast('2002-03-25' as date) + 90)
          and d_date_sk = cs_sold_date_sk 
      ) 
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  sum(cs_ext_discount_amt)  as "excess discount amount" 
from 
   catalog_sales 
   ,item 
   ,date_dim
where
i_manufact_id = 256
and i_item_sk = cs_item_sk 
and d_date between '1999-02-14' and 
        (cast('1999-02-14' as date) + 90)
and d_date_sk = cs_sold_date_sk 
and cs_ext_discount_amt  
     > ( 
         select 
            1.3 * avg(cs_ext_discount_amt) 
         from 
            catalog_sales 
           ,date_dim
         where 
              cs_item_sk = i_item_sk 
          and d_date between '1999-02-14' and
                             (cast('1999-02-14' as date) + 90)
          and d_date_sk = cs_sold_date_sk 
      ) 
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  sum(cs_ext_discount_amt)  as "excess discount amount" 
from 
   catalog_sales 
   ,item 
   ,date_dim
where
i_manufact_id = 11
and i_item_sk = cs_item_sk 
and d_date between '2000-03-19' and 
        (cast('2000-03-19' as date) + 90)
and d_date_sk = cs_sold_date_sk 
and cs_ext_discount_amt  
     > ( 
         select 
            1.3 * avg(cs_ext_discount_amt) 
         from 
            catalog_sales 
           ,date_dim
         where 
              cs_item_sk = i_item_sk 
          and d_date between '2000-03-19' and
                             (cast('2000-03-19' as date) + 90)
          and d_date_sk = cs_sold_date_sk 
      ) 
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  sum(cs_ext_discount_amt)  as "excess discount amount" 
from 
   catalog_sales 
   ,item 
   ,date_dim
where
i_manufact_id = 458
and i_item_sk = cs_item_sk 
and d_date between '2001-01-28' and 
        (cast('2001-01-28' as date) + 90)
and d_date_sk = cs_sold_date_sk 
and cs_ext_discount_amt  
     > ( 
         select 
            1.3 * avg(cs_ext_discount_amt) 
         from 
            catalog_sales 
           ,date_dim
         where 
              cs_item_sk = i_item_sk 
          and d_date between '2001-01-28' and
                             (cast('2001-01-28' as date) + 90)
          and d_date_sk = cs_sold_date_sk 
      ) 
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  sum(cs_ext_discount_amt)  as "excess discount amount" 
from 
   catalog_sales 
   ,item 
   ,date_dim
where
i_manufact_id = 555
and i_item_sk = cs_item_sk 
and d_date between '1998-01-03' and 
        (cast('1998-01-03' as date) + 90)
and d_date_sk = cs_sold_date_sk 
and cs_ext_discount_amt  
     > ( 
         select 
            1.3 * avg(cs_ext_discount_amt) 
         from 
            catalog_sales 
           ,date_dim
         where 
              cs_item_sk = i_item_sk 
          and d_date between '1998-01-03' and
                             (cast('1998-01-03' as date) + 90)
          and d_date_sk = cs_sold_date_sk 
      ) 
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  sum(cs_ext_discount_amt)  as "excess discount amount" 
from 
   catalog_sales 
   ,item 
   ,date_dim
where
i_manufact_id = 858
and i_item_sk = cs_item_sk 
and d_date between '2001-01-21' and 
        (cast('2001-01-21' as date) + 90)
and d_date_sk = cs_sold_date_sk 
and cs_ext_discount_amt  
     > ( 
         select 
            1.3 * avg(cs_ext_discount_amt) 
         from 
            catalog_sales 
           ,date_dim
         where 
              cs_item_sk = i_item_sk 
          and d_date between '2001-01-21' and
                             (cast('2001-01-21' as date) + 90)
          and d_date_sk = cs_sold_date_sk 
      ) 
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  sum(cs_ext_discount_amt)  as "excess discount amount" 
from 
   catalog_sales 
   ,item 
   ,date_dim
where
i_manufact_id = 441
and i_item_sk = cs_item_sk 
and d_date between '1998-01-12' and 
        (cast('1998-01-12' as date) + 90)
and d_date_sk = cs_sold_date_sk 
and cs_ext_discount_amt  
     > ( 
         select 
            1.3 * avg(cs_ext_discount_amt) 
         from 
            catalog_sales 
           ,date_dim
         where 
              cs_item_sk = i_item_sk 
          and d_date between '1998-01-12' and
                             (cast('1998-01-12' as date) + 90)
          and d_date_sk = cs_sold_date_sk 
      ) 
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  sum(cs_ext_discount_amt)  as "excess discount amount" 
from 
   catalog_sales 
   ,item 
   ,date_dim
where
i_manufact_id = 852
and i_item_sk = cs_item_sk 
and d_date between '1999-02-18' and 
        (cast('1999-02-18' as date) + 90)
and d_date_sk = cs_sold_date_sk 
and cs_ext_discount_amt  
     > ( 
         select 
            1.3 * avg(cs_ext_discount_amt) 
         from 
            catalog_sales 
           ,date_dim
         where 
              cs_item_sk = i_item_sk 
          and d_date between '1999-02-18' and
                             (cast('1999-02-18' as date) + 90)
          and d_date_sk = cs_sold_date_sk 
      ) 
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  sum(cs_ext_discount_amt)  as "excess discount amount" 
from 
   catalog_sales 
   ,item 
   ,date_dim
where
i_manufact_id = 562
and i_item_sk = cs_item_sk 
and d_date between '2001-03-26' and 
        (cast('2001-03-26' as date) + 90)
and d_date_sk = cs_sold_date_sk 
and cs_ext_discount_amt  
     > ( 
         select 
            1.3 * avg(cs_ext_discount_amt) 
         from 
            catalog_sales 
           ,date_dim
         where 
              cs_item_sk = i_item_sk 
          and d_date between '2001-03-26' and
                             (cast('2001-03-26' as date) + 90)
          and d_date_sk = cs_sold_date_sk 
      ) 
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  sum(cs_ext_discount_amt)  as "excess discount amount" 
from 
   catalog_sales 
   ,item 
   ,date_dim
where
i_manufact_id = 66
and i_item_sk = cs_item_sk 
and d_date between '2000-01-06' and 
        (cast('2000-01-06' as date) + 90)
and d_date_sk = cs_sold_date_sk 
and cs_ext_discount_amt  
     > ( 
         select 
            1.3 * avg(cs_ext_discount_amt) 
         from 
            catalog_sales 
           ,date_dim
         where 
              cs_item_sk = i_item_sk 
          and d_date between '2000-01-06' and
                             (cast('2000-01-06' as date) + 90)
          and d_date_sk = cs_sold_date_sk 
      ) 
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  sum(cs_ext_discount_amt)  as "excess discount amount" 
from 
   catalog_sales 
   ,item 
   ,date_dim
where
i_manufact_id = 862
and i_item_sk = cs_item_sk 
and d_date between '2000-03-15' and 
        (cast('2000-03-15' as date) + 90)
and d_date_sk = cs_sold_date_sk 
and cs_ext_discount_amt  
     > ( 
         select 
            1.3 * avg(cs_ext_discount_amt) 
         from 
            catalog_sales 
           ,date_dim
         where 
              cs_item_sk = i_item_sk 
          and d_date between '2000-03-15' and
                             (cast('2000-03-15' as date) + 90)
          and d_date_sk = cs_sold_date_sk 
      ) 
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  sum(cs_ext_discount_amt)  as "excess discount amount" 
from 
   catalog_sales 
   ,item 
   ,date_dim
where
i_manufact_id = 294
and i_item_sk = cs_item_sk 
and d_date between '2001-03-12' and 
        (cast('2001-03-12' as date) + 90)
and d_date_sk = cs_sold_date_sk 
and cs_ext_discount_amt  
     > ( 
         select 
            1.3 * avg(cs_ext_discount_amt) 
         from 
            catalog_sales 
           ,date_dim
         where 
              cs_item_sk = i_item_sk 
          and d_date between '2001-03-12' and
                             (cast('2001-03-12' as date) + 90)
          and d_date_sk = cs_sold_date_sk 
      ) 
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  sum(cs_ext_discount_amt)  as "excess discount amount" 
from 
   catalog_sales 
   ,item 
   ,date_dim
where
i_manufact_id = 626
and i_item_sk = cs_item_sk 
and d_date between '2002-01-21' and 
        (cast('2002-01-21' as date) + 90)
and d_date_sk = cs_sold_date_sk 
and cs_ext_discount_amt  
     > ( 
         select 
            1.3 * avg(cs_ext_discount_amt) 
         from 
            catalog_sales 
           ,date_dim
         where 
              cs_item_sk = i_item_sk 
          and d_date between '2002-01-21' and
                             (cast('2002-01-21' as date) + 90)
          and d_date_sk = cs_sold_date_sk 
      ) 
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  sum(cs_ext_discount_amt)  as "excess discount amount" 
from 
   catalog_sales 
   ,item 
   ,date_dim
where
i_manufact_id = 527
and i_item_sk = cs_item_sk 
and d_date between '2001-03-05' and 
        (cast('2001-03-05' as date) + 90)
and d_date_sk = cs_sold_date_sk 
and cs_ext_discount_amt  
     > ( 
         select 
            1.3 * avg(cs_ext_discount_amt) 
         from 
            catalog_sales 
           ,date_dim
         where 
              cs_item_sk = i_item_sk 
          and d_date between '2001-03-05' and
                             (cast('2001-03-05' as date) + 90)
          and d_date_sk = cs_sold_date_sk 
      ) 
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  sum(cs_ext_discount_amt)  as "excess discount amount" 
from 
   catalog_sales 
   ,item 
   ,date_dim
where
i_manufact_id = 710
and i_item_sk = cs_item_sk 
and d_date between '1999-03-19' and 
        (cast('1999-03-19' as date) + 90)
and d_date_sk = cs_sold_date_sk 
and cs_ext_discount_amt  
     > ( 
         select 
            1.3 * avg(cs_ext_discount_amt) 
         from 
            catalog_sales 
           ,date_dim
         where 
              cs_item_sk = i_item_sk 
          and d_date between '1999-03-19' and
                             (cast('1999-03-19' as date) + 90)
          and d_date_sk = cs_sold_date_sk 
      ) 
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  sum(cs_ext_discount_amt)  as "excess discount amount" 
from 
   catalog_sales 
   ,item 
   ,date_dim
where
i_manufact_id = 93
and i_item_sk = cs_item_sk 
and d_date between '1998-01-23' and 
        (cast('1998-01-23' as date) + 90)
and d_date_sk = cs_sold_date_sk 
and cs_ext_discount_amt  
     > ( 
         select 
            1.3 * avg(cs_ext_discount_amt) 
         from 
            catalog_sales 
           ,date_dim
         where 
              cs_item_sk = i_item_sk 
          and d_date between '1998-01-23' and
                             (cast('1998-01-23' as date) + 90)
          and d_date_sk = cs_sold_date_sk 
      ) 
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  sum(cs_ext_discount_amt)  as "excess discount amount" 
from 
   catalog_sales 
   ,item 
   ,date_dim
where
i_manufact_id = 994
and i_item_sk = cs_item_sk 
and d_date between '2002-01-20' and 
        (cast('2002-01-20' as date) + 90)
and d_date_sk = cs_sold_date_sk 
and cs_ext_discount_amt  
     > ( 
         select 
            1.3 * avg(cs_ext_discount_amt) 
         from 
            catalog_sales 
           ,date_dim
         where 
              cs_item_sk = i_item_sk 
          and d_date between '2002-01-20' and
                             (cast('2002-01-20' as date) + 90)
          and d_date_sk = cs_sold_date_sk 
      ) 
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  sum(cs_ext_discount_amt)  as "excess discount amount" 
from 
   catalog_sales 
   ,item 
   ,date_dim
where
i_manufact_id = 873
and i_item_sk = cs_item_sk 
and d_date between '2000-03-17' and 
        (cast('2000-03-17' as date) + 90)
and d_date_sk = cs_sold_date_sk 
and cs_ext_discount_amt  
     > ( 
         select 
            1.3 * avg(cs_ext_discount_amt) 
         from 
            catalog_sales 
           ,date_dim
         where 
              cs_item_sk = i_item_sk 
          and d_date between '2000-03-17' and
                             (cast('2000-03-17' as date) + 90)
          and d_date_sk = cs_sold_date_sk 
      ) 
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  sum(cs_ext_discount_amt)  as "excess discount amount" 
from 
   catalog_sales 
   ,item 
   ,date_dim
where
i_manufact_id = 255
and i_item_sk = cs_item_sk 
and d_date between '1998-02-01' and 
        (cast('1998-02-01' as date) + 90)
and d_date_sk = cs_sold_date_sk 
and cs_ext_discount_amt  
     > ( 
         select 
            1.3 * avg(cs_ext_discount_amt) 
         from 
            catalog_sales 
           ,date_dim
         where 
              cs_item_sk = i_item_sk 
          and d_date between '1998-02-01' and
                             (cast('1998-02-01' as date) + 90)
          and d_date_sk = cs_sold_date_sk 
      ) 
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  sum(cs_ext_discount_amt)  as "excess discount amount" 
from 
   catalog_sales 
   ,item 
   ,date_dim
where
i_manufact_id = 873
and i_item_sk = cs_item_sk 
and d_date between '1999-01-11' and 
        (cast('1999-01-11' as date) + 90)
and d_date_sk = cs_sold_date_sk 
and cs_ext_discount_amt  
     > ( 
         select 
            1.3 * avg(cs_ext_discount_amt) 
         from 
            catalog_sales 
           ,date_dim
         where 
              cs_item_sk = i_item_sk 
          and d_date between '1999-01-11' and
                             (cast('1999-01-11' as date) + 90)
          and d_date_sk = cs_sold_date_sk 
      ) 
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  sum(cs_ext_discount_amt)  as "excess discount amount" 
from 
   catalog_sales 
   ,item 
   ,date_dim
where
i_manufact_id = 347
and i_item_sk = cs_item_sk 
and d_date between '2002-01-15' and 
        (cast('2002-01-15' as date) + 90)
and d_date_sk = cs_sold_date_sk 
and cs_ext_discount_amt  
     > ( 
         select 
            1.3 * avg(cs_ext_discount_amt) 
         from 
            catalog_sales 
           ,date_dim
         where 
              cs_item_sk = i_item_sk 
          and d_date between '2002-01-15' and
                             (cast('2002-01-15' as date) + 90)
          and d_date_sk = cs_sold_date_sk 
      ) 
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  sum(cs_ext_discount_amt)  as "excess discount amount" 
from 
   catalog_sales 
   ,item 
   ,date_dim
where
i_manufact_id = 693
and i_item_sk = cs_item_sk 
and d_date between '1998-02-12' and 
        (cast('1998-02-12' as date) + 90)
and d_date_sk = cs_sold_date_sk 
and cs_ext_discount_amt  
     > ( 
         select 
            1.3 * avg(cs_ext_discount_amt) 
         from 
            catalog_sales 
           ,date_dim
         where 
              cs_item_sk = i_item_sk 
          and d_date between '1998-02-12' and
                             (cast('1998-02-12' as date) + 90)
          and d_date_sk = cs_sold_date_sk 
      ) 
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  sum(cs_ext_discount_amt)  as "excess discount amount" 
from 
   catalog_sales 
   ,item 
   ,date_dim
where
i_manufact_id = 262
and i_item_sk = cs_item_sk 
and d_date between '2001-01-26' and 
        (cast('2001-01-26' as date) + 90)
and d_date_sk = cs_sold_date_sk 
and cs_ext_discount_amt  
     > ( 
         select 
            1.3 * avg(cs_ext_discount_amt) 
         from 
            catalog_sales 
           ,date_dim
         where 
              cs_item_sk = i_item_sk 
          and d_date between '2001-01-26' and
                             (cast('2001-01-26' as date) + 90)
          and d_date_sk = cs_sold_date_sk 
      ) 
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  sum(cs_ext_discount_amt)  as "excess discount amount" 
from 
   catalog_sales 
   ,item 
   ,date_dim
where
i_manufact_id = 581
and i_item_sk = cs_item_sk 
and d_date between '2000-03-14' and 
        (cast('2000-03-14' as date) + 90)
and d_date_sk = cs_sold_date_sk 
and cs_ext_discount_amt  
     > ( 
         select 
            1.3 * avg(cs_ext_discount_amt) 
         from 
            catalog_sales 
           ,date_dim
         where 
              cs_item_sk = i_item_sk 
          and d_date between '2000-03-14' and
                             (cast('2000-03-14' as date) + 90)
          and d_date_sk = cs_sold_date_sk 
      ) 
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  sum(cs_ext_discount_amt)  as "excess discount amount" 
from 
   catalog_sales 
   ,item 
   ,date_dim
where
i_manufact_id = 88
and i_item_sk = cs_item_sk 
and d_date between '2000-01-16' and 
        (cast('2000-01-16' as date) + 90)
and d_date_sk = cs_sold_date_sk 
and cs_ext_discount_amt  
     > ( 
         select 
            1.3 * avg(cs_ext_discount_amt) 
         from 
            catalog_sales 
           ,date_dim
         where 
              cs_item_sk = i_item_sk 
          and d_date between '2000-01-16' and
                             (cast('2000-01-16' as date) + 90)
          and d_date_sk = cs_sold_date_sk 
      ) 
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  sum(cs_ext_discount_amt)  as "excess discount amount" 
from 
   catalog_sales 
   ,item 
   ,date_dim
where
i_manufact_id = 464
and i_item_sk = cs_item_sk 
and d_date between '2002-03-30' and 
        (cast('2002-03-30' as date) + 90)
and d_date_sk = cs_sold_date_sk 
and cs_ext_discount_amt  
     > ( 
         select 
            1.3 * avg(cs_ext_discount_amt) 
         from 
            catalog_sales 
           ,date_dim
         where 
              cs_item_sk = i_item_sk 
          and d_date between '2002-03-30' and
                             (cast('2002-03-30' as date) + 90)
          and d_date_sk = cs_sold_date_sk 
      ) 
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  sum(cs_ext_discount_amt)  as "excess discount amount" 
from 
   catalog_sales 
   ,item 
   ,date_dim
where
i_manufact_id = 578
and i_item_sk = cs_item_sk 
and d_date between '1998-03-15' and 
        (cast('1998-03-15' as date) + 90)
and d_date_sk = cs_sold_date_sk 
and cs_ext_discount_amt  
     > ( 
         select 
            1.3 * avg(cs_ext_discount_amt) 
         from 
            catalog_sales 
           ,date_dim
         where 
              cs_item_sk = i_item_sk 
          and d_date between '1998-03-15' and
                             (cast('1998-03-15' as date) + 90)
          and d_date_sk = cs_sold_date_sk 
      ) 
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  sum(cs_ext_discount_amt)  as "excess discount amount" 
from 
   catalog_sales 
   ,item 
   ,date_dim
where
i_manufact_id = 103
and i_item_sk = cs_item_sk 
and d_date between '1998-03-30' and 
        (cast('1998-03-30' as date) + 90)
and d_date_sk = cs_sold_date_sk 
and cs_ext_discount_amt  
     > ( 
         select 
            1.3 * avg(cs_ext_discount_amt) 
         from 
            catalog_sales 
           ,date_dim
         where 
              cs_item_sk = i_item_sk 
          and d_date between '1998-03-30' and
                             (cast('1998-03-30' as date) + 90)
          and d_date_sk = cs_sold_date_sk 
      ) 
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  sum(cs_ext_discount_amt)  as "excess discount amount" 
from 
   catalog_sales 
   ,item 
   ,date_dim
where
i_manufact_id = 907
and i_item_sk = cs_item_sk 
and d_date between '2000-02-20' and 
        (cast('2000-02-20' as date) + 90)
and d_date_sk = cs_sold_date_sk 
and cs_ext_discount_amt  
     > ( 
         select 
            1.3 * avg(cs_ext_discount_amt) 
         from 
            catalog_sales 
           ,date_dim
         where 
              cs_item_sk = i_item_sk 
          and d_date between '2000-02-20' and
                             (cast('2000-02-20' as date) + 90)
          and d_date_sk = cs_sold_date_sk 
      ) 
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  sum(cs_ext_discount_amt)  as "excess discount amount" 
from 
   catalog_sales 
   ,item 
   ,date_dim
where
i_manufact_id = 968
and i_item_sk = cs_item_sk 
and d_date between '2002-01-31' and 
        (cast('2002-01-31' as date) + 90)
and d_date_sk = cs_sold_date_sk 
and cs_ext_discount_amt  
     > ( 
         select 
            1.3 * avg(cs_ext_discount_amt) 
         from 
            catalog_sales 
           ,date_dim
         where 
              cs_item_sk = i_item_sk 
          and d_date between '2002-01-31' and
                             (cast('2002-01-31' as date) + 90)
          and d_date_sk = cs_sold_date_sk 
      ) 
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  sum(cs_ext_discount_amt)  as "excess discount amount" 
from 
   catalog_sales 
   ,item 
   ,date_dim
where
i_manufact_id = 446
and i_item_sk = cs_item_sk 
and d_date between '2001-02-14' and 
        (cast('2001-02-14' as date) + 90)
and d_date_sk = cs_sold_date_sk 
and cs_ext_discount_amt  
     > ( 
         select 
            1.3 * avg(cs_ext_discount_amt) 
         from 
            catalog_sales 
           ,date_dim
         where 
              cs_item_sk = i_item_sk 
          and d_date between '2001-02-14' and
                             (cast('2001-02-14' as date) + 90)
          and d_date_sk = cs_sold_date_sk 
      ) 
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  sum(cs_ext_discount_amt)  as "excess discount amount" 
from 
   catalog_sales 
   ,item 
   ,date_dim
where
i_manufact_id = 879
and i_item_sk = cs_item_sk 
and d_date between '1999-02-09' and 
        (cast('1999-02-09' as date) + 90)
and d_date_sk = cs_sold_date_sk 
and cs_ext_discount_amt  
     > ( 
         select 
            1.3 * avg(cs_ext_discount_amt) 
         from 
            catalog_sales 
           ,date_dim
         where 
              cs_item_sk = i_item_sk 
          and d_date between '1999-02-09' and
                             (cast('1999-02-09' as date) + 90)
          and d_date_sk = cs_sold_date_sk 
      ) 
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  sum(cs_ext_discount_amt)  as "excess discount amount" 
from 
   catalog_sales 
   ,item 
   ,date_dim
where
i_manufact_id = 923
and i_item_sk = cs_item_sk 
and d_date between '1999-03-16' and 
        (cast('1999-03-16' as date) + 90)
and d_date_sk = cs_sold_date_sk 
and cs_ext_discount_amt  
     > ( 
         select 
            1.3 * avg(cs_ext_discount_amt) 
         from 
            catalog_sales 
           ,date_dim
         where 
              cs_item_sk = i_item_sk 
          and d_date between '1999-03-16' and
                             (cast('1999-03-16' as date) + 90)
          and d_date_sk = cs_sold_date_sk 
      ) 
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  sum(cs_ext_discount_amt)  as "excess discount amount" 
from 
   catalog_sales 
   ,item 
   ,date_dim
where
i_manufact_id = 448
and i_item_sk = cs_item_sk 
and d_date between '2000-03-28' and 
        (cast('2000-03-28' as date) + 90)
and d_date_sk = cs_sold_date_sk 
and cs_ext_discount_amt  
     > ( 
         select 
            1.3 * avg(cs_ext_discount_amt) 
         from 
            catalog_sales 
           ,date_dim
         where 
              cs_item_sk = i_item_sk 
          and d_date between '2000-03-28' and
                             (cast('2000-03-28' as date) + 90)
          and d_date_sk = cs_sold_date_sk 
      ) 
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  sum(cs_ext_discount_amt)  as "excess discount amount" 
from 
   catalog_sales 
   ,item 
   ,date_dim
where
i_manufact_id = 101
and i_item_sk = cs_item_sk 
and d_date between '2002-02-15' and 
        (cast('2002-02-15' as date) + 90)
and d_date_sk = cs_sold_date_sk 
and cs_ext_discount_amt  
     > ( 
         select 
            1.3 * avg(cs_ext_discount_amt) 
         from 
            catalog_sales 
           ,date_dim
         where 
              cs_item_sk = i_item_sk 
          and d_date between '2002-02-15' and
                             (cast('2002-02-15' as date) + 90)
          and d_date_sk = cs_sold_date_sk 
      ) 
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  sum(cs_ext_discount_amt)  as "excess discount amount" 
from 
   catalog_sales 
   ,item 
   ,date_dim
where
i_manufact_id = 286
and i_item_sk = cs_item_sk 
and d_date between '2001-03-17' and 
        (cast('2001-03-17' as date) + 90)
and d_date_sk = cs_sold_date_sk 
and cs_ext_discount_amt  
     > ( 
         select 
            1.3 * avg(cs_ext_discount_amt) 
         from 
            catalog_sales 
           ,date_dim
         where 
              cs_item_sk = i_item_sk 
          and d_date between '2001-03-17' and
                             (cast('2001-03-17' as date) + 90)
          and d_date_sk = cs_sold_date_sk 
      ) 
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  sum(cs_ext_discount_amt)  as "excess discount amount" 
from 
   catalog_sales 
   ,item 
   ,date_dim
where
i_manufact_id = 991
and i_item_sk = cs_item_sk 
and d_date between '1998-01-07' and 
        (cast('1998-01-07' as date) + 90)
and d_date_sk = cs_sold_date_sk 
and cs_ext_discount_amt  
     > ( 
         select 
            1.3 * avg(cs_ext_discount_amt) 
         from 
            catalog_sales 
           ,date_dim
         where 
              cs_item_sk = i_item_sk 
          and d_date between '1998-01-07' and
                             (cast('1998-01-07' as date) + 90)
          and d_date_sk = cs_sold_date_sk 
      ) 
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  sum(cs_ext_discount_amt)  as "excess discount amount" 
from 
   catalog_sales 
   ,item 
   ,date_dim
where
i_manufact_id = 122
and i_item_sk = cs_item_sk 
and d_date between '1999-01-20' and 
        (cast('1999-01-20' as date) + 90)
and d_date_sk = cs_sold_date_sk 
and cs_ext_discount_amt  
     > ( 
         select 
            1.3 * avg(cs_ext_discount_amt) 
         from 
            catalog_sales 
           ,date_dim
         where 
              cs_item_sk = i_item_sk 
          and d_date between '1999-01-20' and
                             (cast('1999-01-20' as date) + 90)
          and d_date_sk = cs_sold_date_sk 
      ) 
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  sum(cs_ext_discount_amt)  as "excess discount amount" 
from 
   catalog_sales 
   ,item 
   ,date_dim
where
i_manufact_id = 134
and i_item_sk = cs_item_sk 
and d_date between '2001-01-12' and 
        (cast('2001-01-12' as date) + 90)
and d_date_sk = cs_sold_date_sk 
and cs_ext_discount_amt  
     > ( 
         select 
            1.3 * avg(cs_ext_discount_amt) 
         from 
            catalog_sales 
           ,date_dim
         where 
              cs_item_sk = i_item_sk 
          and d_date between '2001-01-12' and
                             (cast('2001-01-12' as date) + 90)
          and d_date_sk = cs_sold_date_sk 
      ) 
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  sum(cs_ext_discount_amt)  as "excess discount amount" 
from 
   catalog_sales 
   ,item 
   ,date_dim
where
i_manufact_id = 672
and i_item_sk = cs_item_sk 
and d_date between '2002-01-24' and 
        (cast('2002-01-24' as date) + 90)
and d_date_sk = cs_sold_date_sk 
and cs_ext_discount_amt  
     > ( 
         select 
            1.3 * avg(cs_ext_discount_amt) 
         from 
            catalog_sales 
           ,date_dim
         where 
              cs_item_sk = i_item_sk 
          and d_date between '2002-01-24' and
                             (cast('2002-01-24' as date) + 90)
          and d_date_sk = cs_sold_date_sk 
      ) 
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  sum(cs_ext_discount_amt)  as "excess discount amount" 
from 
   catalog_sales 
   ,item 
   ,date_dim
where
i_manufact_id = 410
and i_item_sk = cs_item_sk 
and d_date between '1999-02-18' and 
        (cast('1999-02-18' as date) + 90)
and d_date_sk = cs_sold_date_sk 
and cs_ext_discount_amt  
     > ( 
         select 
            1.3 * avg(cs_ext_discount_amt) 
         from 
            catalog_sales 
           ,date_dim
         where 
              cs_item_sk = i_item_sk 
          and d_date between '1999-02-18' and
                             (cast('1999-02-18' as date) + 90)
          and d_date_sk = cs_sold_date_sk 
      ) 
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  sum(cs_ext_discount_amt)  as "excess discount amount" 
from 
   catalog_sales 
   ,item 
   ,date_dim
where
i_manufact_id = 193
and i_item_sk = cs_item_sk 
and d_date between '2002-03-30' and 
        (cast('2002-03-30' as date) + 90)
and d_date_sk = cs_sold_date_sk 
and cs_ext_discount_amt  
     > ( 
         select 
            1.3 * avg(cs_ext_discount_amt) 
         from 
            catalog_sales 
           ,date_dim
         where 
              cs_item_sk = i_item_sk 
          and d_date between '2002-03-30' and
                             (cast('2002-03-30' as date) + 90)
          and d_date_sk = cs_sold_date_sk 
      ) 
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  sum(cs_ext_discount_amt)  as "excess discount amount" 
from 
   catalog_sales 
   ,item 
   ,date_dim
where
i_manufact_id = 113
and i_item_sk = cs_item_sk 
and d_date between '2001-03-17' and 
        (cast('2001-03-17' as date) + 90)
and d_date_sk = cs_sold_date_sk 
and cs_ext_discount_amt  
     > ( 
         select 
            1.3 * avg(cs_ext_discount_amt) 
         from 
            catalog_sales 
           ,date_dim
         where 
              cs_item_sk = i_item_sk 
          and d_date between '2001-03-17' and
                             (cast('2001-03-17' as date) + 90)
          and d_date_sk = cs_sold_date_sk 
      ) 
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  sum(cs_ext_discount_amt)  as "excess discount amount" 
from 
   catalog_sales 
   ,item 
   ,date_dim
where
i_manufact_id = 80
and i_item_sk = cs_item_sk 
and d_date between '1998-01-05' and 
        (cast('1998-01-05' as date) + 90)
and d_date_sk = cs_sold_date_sk 
and cs_ext_discount_amt  
     > ( 
         select 
            1.3 * avg(cs_ext_discount_amt) 
         from 
            catalog_sales 
           ,date_dim
         where 
              cs_item_sk = i_item_sk 
          and d_date between '1998-01-05' and
                             (cast('1998-01-05' as date) + 90)
          and d_date_sk = cs_sold_date_sk 
      ) 
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  sum(cs_ext_discount_amt)  as "excess discount amount" 
from 
   catalog_sales 
   ,item 
   ,date_dim
where
i_manufact_id = 16
and i_item_sk = cs_item_sk 
and d_date between '1998-03-03' and 
        (cast('1998-03-03' as date) + 90)
and d_date_sk = cs_sold_date_sk 
and cs_ext_discount_amt  
     > ( 
         select 
            1.3 * avg(cs_ext_discount_amt) 
         from 
            catalog_sales 
           ,date_dim
         where 
              cs_item_sk = i_item_sk 
          and d_date between '1998-03-03' and
                             (cast('1998-03-03' as date) + 90)
          and d_date_sk = cs_sold_date_sk 
      ) 
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  sum(cs_ext_discount_amt)  as "excess discount amount" 
from 
   catalog_sales 
   ,item 
   ,date_dim
where
i_manufact_id = 705
and i_item_sk = cs_item_sk 
and d_date between '1999-03-23' and 
        (cast('1999-03-23' as date) + 90)
and d_date_sk = cs_sold_date_sk 
and cs_ext_discount_amt  
     > ( 
         select 
            1.3 * avg(cs_ext_discount_amt) 
         from 
            catalog_sales 
           ,date_dim
         where 
              cs_item_sk = i_item_sk 
          and d_date between '1999-03-23' and
                             (cast('1999-03-23' as date) + 90)
          and d_date_sk = cs_sold_date_sk 
      ) 
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  sum(cs_ext_discount_amt)  as "excess discount amount" 
from 
   catalog_sales 
   ,item 
   ,date_dim
where
i_manufact_id = 844
and i_item_sk = cs_item_sk 
and d_date between '1999-02-18' and 
        (cast('1999-02-18' as date) + 90)
and d_date_sk = cs_sold_date_sk 
and cs_ext_discount_amt  
     > ( 
         select 
            1.3 * avg(cs_ext_discount_amt) 
         from 
            catalog_sales 
           ,date_dim
         where 
              cs_item_sk = i_item_sk 
          and d_date between '1999-02-18' and
                             (cast('1999-02-18' as date) + 90)
          and d_date_sk = cs_sold_date_sk 
      ) 
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  sum(cs_ext_discount_amt)  as "excess discount amount" 
from 
   catalog_sales 
   ,item 
   ,date_dim
where
i_manufact_id = 897
and i_item_sk = cs_item_sk 
and d_date between '1998-03-10' and 
        (cast('1998-03-10' as date) + 90)
and d_date_sk = cs_sold_date_sk 
and cs_ext_discount_amt  
     > ( 
         select 
            1.3 * avg(cs_ext_discount_amt) 
         from 
            catalog_sales 
           ,date_dim
         where 
              cs_item_sk = i_item_sk 
          and d_date between '1998-03-10' and
                             (cast('1998-03-10' as date) + 90)
          and d_date_sk = cs_sold_date_sk 
      ) 
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  sum(cs_ext_discount_amt)  as "excess discount amount" 
from 
   catalog_sales 
   ,item 
   ,date_dim
where
i_manufact_id = 131
and i_item_sk = cs_item_sk 
and d_date between '2002-03-19' and 
        (cast('2002-03-19' as date) + 90)
and d_date_sk = cs_sold_date_sk 
and cs_ext_discount_amt  
     > ( 
         select 
            1.3 * avg(cs_ext_discount_amt) 
         from 
            catalog_sales 
           ,date_dim
         where 
              cs_item_sk = i_item_sk 
          and d_date between '2002-03-19' and
                             (cast('2002-03-19' as date) + 90)
          and d_date_sk = cs_sold_date_sk 
      ) 
limit 100;

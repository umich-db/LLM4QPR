EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  i_item_id
       ,i_item_desc
       ,i_current_price
 from item, inventory, date_dim, store_sales
 where i_current_price between 30 and 30+30
 and inv_item_sk = i_item_sk
 and d_date_sk=inv_date_sk
 and d_date between cast('2002-05-30' as date) and (cast('2002-05-30' as date) +  60 )
 and i_manufact_id in (437,129,727,663)
 and inv_quantity_on_hand between 100 and 500
 and ss_item_sk = i_item_sk
 group by i_item_id,i_item_desc,i_current_price
 order by i_item_id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  i_item_id
       ,i_item_desc
       ,i_current_price
 from item, inventory, date_dim, store_sales
 where i_current_price between 3 and 3+30
 and inv_item_sk = i_item_sk
 and d_date_sk=inv_date_sk
 and d_date between cast('1998-05-20' as date) and (cast('1998-05-20' as date) +  60 )
 and i_manufact_id in (59,526,301,399)
 and inv_quantity_on_hand between 100 and 500
 and ss_item_sk = i_item_sk
 group by i_item_id,i_item_desc,i_current_price
 order by i_item_id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  i_item_id
       ,i_item_desc
       ,i_current_price
 from item, inventory, date_dim, store_sales
 where i_current_price between 34 and 34+30
 and inv_item_sk = i_item_sk
 and d_date_sk=inv_date_sk
 and d_date between cast('1999-01-24' as date) and (cast('1999-01-24' as date) +  60 )
 and i_manufact_id in (33,652,78,269)
 and inv_quantity_on_hand between 100 and 500
 and ss_item_sk = i_item_sk
 group by i_item_id,i_item_desc,i_current_price
 order by i_item_id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  i_item_id
       ,i_item_desc
       ,i_current_price
 from item, inventory, date_dim, store_sales
 where i_current_price between 12 and 12+30
 and inv_item_sk = i_item_sk
 and d_date_sk=inv_date_sk
 and d_date between cast('1998-07-12' as date) and (cast('1998-07-12' as date) +  60 )
 and i_manufact_id in (22,757,210,793)
 and inv_quantity_on_hand between 100 and 500
 and ss_item_sk = i_item_sk
 group by i_item_id,i_item_desc,i_current_price
 order by i_item_id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  i_item_id
       ,i_item_desc
       ,i_current_price
 from item, inventory, date_dim, store_sales
 where i_current_price between 67 and 67+30
 and inv_item_sk = i_item_sk
 and d_date_sk=inv_date_sk
 and d_date between cast('1998-02-27' as date) and (cast('1998-02-27' as date) +  60 )
 and i_manufact_id in (840,885,815,930)
 and inv_quantity_on_hand between 100 and 500
 and ss_item_sk = i_item_sk
 group by i_item_id,i_item_desc,i_current_price
 order by i_item_id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  i_item_id
       ,i_item_desc
       ,i_current_price
 from item, inventory, date_dim, store_sales
 where i_current_price between 23 and 23+30
 and inv_item_sk = i_item_sk
 and d_date_sk=inv_date_sk
 and d_date between cast('2000-03-10' as date) and (cast('2000-03-10' as date) +  60 )
 and i_manufact_id in (410,147,81,759)
 and inv_quantity_on_hand between 100 and 500
 and ss_item_sk = i_item_sk
 group by i_item_id,i_item_desc,i_current_price
 order by i_item_id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  i_item_id
       ,i_item_desc
       ,i_current_price
 from item, inventory, date_dim, store_sales
 where i_current_price between 46 and 46+30
 and inv_item_sk = i_item_sk
 and d_date_sk=inv_date_sk
 and d_date between cast('2002-02-26' as date) and (cast('2002-02-26' as date) +  60 )
 and i_manufact_id in (505,258,76,569)
 and inv_quantity_on_hand between 100 and 500
 and ss_item_sk = i_item_sk
 group by i_item_id,i_item_desc,i_current_price
 order by i_item_id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  i_item_id
       ,i_item_desc
       ,i_current_price
 from item, inventory, date_dim, store_sales
 where i_current_price between 49 and 49+30
 and inv_item_sk = i_item_sk
 and d_date_sk=inv_date_sk
 and d_date between cast('1999-04-02' as date) and (cast('1999-04-02' as date) +  60 )
 and i_manufact_id in (958,374,388,726)
 and inv_quantity_on_hand between 100 and 500
 and ss_item_sk = i_item_sk
 group by i_item_id,i_item_desc,i_current_price
 order by i_item_id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  i_item_id
       ,i_item_desc
       ,i_current_price
 from item, inventory, date_dim, store_sales
 where i_current_price between 33 and 33+30
 and inv_item_sk = i_item_sk
 and d_date_sk=inv_date_sk
 and d_date between cast('2002-02-04' as date) and (cast('2002-02-04' as date) +  60 )
 and i_manufact_id in (241,60,392,873)
 and inv_quantity_on_hand between 100 and 500
 and ss_item_sk = i_item_sk
 group by i_item_id,i_item_desc,i_current_price
 order by i_item_id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  i_item_id
       ,i_item_desc
       ,i_current_price
 from item, inventory, date_dim, store_sales
 where i_current_price between 42 and 42+30
 and inv_item_sk = i_item_sk
 and d_date_sk=inv_date_sk
 and d_date between cast('2000-06-13' as date) and (cast('2000-06-13' as date) +  60 )
 and i_manufact_id in (866,106,599,801)
 and inv_quantity_on_hand between 100 and 500
 and ss_item_sk = i_item_sk
 group by i_item_id,i_item_desc,i_current_price
 order by i_item_id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  i_item_id
       ,i_item_desc
       ,i_current_price
 from item, inventory, date_dim, store_sales
 where i_current_price between 85 and 85+30
 and inv_item_sk = i_item_sk
 and d_date_sk=inv_date_sk
 and d_date between cast('2002-07-04' as date) and (cast('2002-07-04' as date) +  60 )
 and i_manufact_id in (192,973,520,401)
 and inv_quantity_on_hand between 100 and 500
 and ss_item_sk = i_item_sk
 group by i_item_id,i_item_desc,i_current_price
 order by i_item_id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  i_item_id
       ,i_item_desc
       ,i_current_price
 from item, inventory, date_dim, store_sales
 where i_current_price between 82 and 82+30
 and inv_item_sk = i_item_sk
 and d_date_sk=inv_date_sk
 and d_date between cast('2000-06-27' as date) and (cast('2000-06-27' as date) +  60 )
 and i_manufact_id in (845,686,953,463)
 and inv_quantity_on_hand between 100 and 500
 and ss_item_sk = i_item_sk
 group by i_item_id,i_item_desc,i_current_price
 order by i_item_id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  i_item_id
       ,i_item_desc
       ,i_current_price
 from item, inventory, date_dim, store_sales
 where i_current_price between 57 and 57+30
 and inv_item_sk = i_item_sk
 and d_date_sk=inv_date_sk
 and d_date between cast('1998-03-12' as date) and (cast('1998-03-12' as date) +  60 )
 and i_manufact_id in (194,271,102,409)
 and inv_quantity_on_hand between 100 and 500
 and ss_item_sk = i_item_sk
 group by i_item_id,i_item_desc,i_current_price
 order by i_item_id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  i_item_id
       ,i_item_desc
       ,i_current_price
 from item, inventory, date_dim, store_sales
 where i_current_price between 25 and 25+30
 and inv_item_sk = i_item_sk
 and d_date_sk=inv_date_sk
 and d_date between cast('2000-03-10' as date) and (cast('2000-03-10' as date) +  60 )
 and i_manufact_id in (24,396,959,267)
 and inv_quantity_on_hand between 100 and 500
 and ss_item_sk = i_item_sk
 group by i_item_id,i_item_desc,i_current_price
 order by i_item_id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  i_item_id
       ,i_item_desc
       ,i_current_price
 from item, inventory, date_dim, store_sales
 where i_current_price between 53 and 53+30
 and inv_item_sk = i_item_sk
 and d_date_sk=inv_date_sk
 and d_date between cast('2000-01-30' as date) and (cast('2000-01-30' as date) +  60 )
 and i_manufact_id in (395,932,732,447)
 and inv_quantity_on_hand between 100 and 500
 and ss_item_sk = i_item_sk
 group by i_item_id,i_item_desc,i_current_price
 order by i_item_id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  i_item_id
       ,i_item_desc
       ,i_current_price
 from item, inventory, date_dim, store_sales
 where i_current_price between 31 and 31+30
 and inv_item_sk = i_item_sk
 and d_date_sk=inv_date_sk
 and d_date between cast('2002-02-09' as date) and (cast('2002-02-09' as date) +  60 )
 and i_manufact_id in (23,754,830,534)
 and inv_quantity_on_hand between 100 and 500
 and ss_item_sk = i_item_sk
 group by i_item_id,i_item_desc,i_current_price
 order by i_item_id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  i_item_id
       ,i_item_desc
       ,i_current_price
 from item, inventory, date_dim, store_sales
 where i_current_price between 66 and 66+30
 and inv_item_sk = i_item_sk
 and d_date_sk=inv_date_sk
 and d_date between cast('1998-03-13' as date) and (cast('1998-03-13' as date) +  60 )
 and i_manufact_id in (718,208,662,649)
 and inv_quantity_on_hand between 100 and 500
 and ss_item_sk = i_item_sk
 group by i_item_id,i_item_desc,i_current_price
 order by i_item_id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  i_item_id
       ,i_item_desc
       ,i_current_price
 from item, inventory, date_dim, store_sales
 where i_current_price between 26 and 26+30
 and inv_item_sk = i_item_sk
 and d_date_sk=inv_date_sk
 and d_date between cast('2002-03-04' as date) and (cast('2002-03-04' as date) +  60 )
 and i_manufact_id in (716,556,806,512)
 and inv_quantity_on_hand between 100 and 500
 and ss_item_sk = i_item_sk
 group by i_item_id,i_item_desc,i_current_price
 order by i_item_id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  i_item_id
       ,i_item_desc
       ,i_current_price
 from item, inventory, date_dim, store_sales
 where i_current_price between 10 and 10+30
 and inv_item_sk = i_item_sk
 and d_date_sk=inv_date_sk
 and d_date between cast('2001-04-21' as date) and (cast('2001-04-21' as date) +  60 )
 and i_manufact_id in (434,45,972,110)
 and inv_quantity_on_hand between 100 and 500
 and ss_item_sk = i_item_sk
 group by i_item_id,i_item_desc,i_current_price
 order by i_item_id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  i_item_id
       ,i_item_desc
       ,i_current_price
 from item, inventory, date_dim, store_sales
 where i_current_price between 27 and 27+30
 and inv_item_sk = i_item_sk
 and d_date_sk=inv_date_sk
 and d_date between cast('2000-03-20' as date) and (cast('2000-03-20' as date) +  60 )
 and i_manufact_id in (731,877,590,14)
 and inv_quantity_on_hand between 100 and 500
 and ss_item_sk = i_item_sk
 group by i_item_id,i_item_desc,i_current_price
 order by i_item_id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  i_item_id
       ,i_item_desc
       ,i_current_price
 from item, inventory, date_dim, store_sales
 where i_current_price between 84 and 84+30
 and inv_item_sk = i_item_sk
 and d_date_sk=inv_date_sk
 and d_date between cast('2002-06-05' as date) and (cast('2002-06-05' as date) +  60 )
 and i_manufact_id in (157,282,114,656)
 and inv_quantity_on_hand between 100 and 500
 and ss_item_sk = i_item_sk
 group by i_item_id,i_item_desc,i_current_price
 order by i_item_id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  i_item_id
       ,i_item_desc
       ,i_current_price
 from item, inventory, date_dim, store_sales
 where i_current_price between 68 and 68+30
 and inv_item_sk = i_item_sk
 and d_date_sk=inv_date_sk
 and d_date between cast('1998-06-12' as date) and (cast('1998-06-12' as date) +  60 )
 and i_manufact_id in (175,796,290,847)
 and inv_quantity_on_hand between 100 and 500
 and ss_item_sk = i_item_sk
 group by i_item_id,i_item_desc,i_current_price
 order by i_item_id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  i_item_id
       ,i_item_desc
       ,i_current_price
 from item, inventory, date_dim, store_sales
 where i_current_price between 9 and 9+30
 and inv_item_sk = i_item_sk
 and d_date_sk=inv_date_sk
 and d_date between cast('1999-02-25' as date) and (cast('1999-02-25' as date) +  60 )
 and i_manufact_id in (555,348,675,215)
 and inv_quantity_on_hand between 100 and 500
 and ss_item_sk = i_item_sk
 group by i_item_id,i_item_desc,i_current_price
 order by i_item_id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  i_item_id
       ,i_item_desc
       ,i_current_price
 from item, inventory, date_dim, store_sales
 where i_current_price between 13 and 13+30
 and inv_item_sk = i_item_sk
 and d_date_sk=inv_date_sk
 and d_date between cast('2000-03-06' as date) and (cast('2000-03-06' as date) +  60 )
 and i_manufact_id in (540,22,24,929)
 and inv_quantity_on_hand between 100 and 500
 and ss_item_sk = i_item_sk
 group by i_item_id,i_item_desc,i_current_price
 order by i_item_id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  i_item_id
       ,i_item_desc
       ,i_current_price
 from item, inventory, date_dim, store_sales
 where i_current_price between 55 and 55+30
 and inv_item_sk = i_item_sk
 and d_date_sk=inv_date_sk
 and d_date between cast('1998-04-21' as date) and (cast('1998-04-21' as date) +  60 )
 and i_manufact_id in (739,864,762,118)
 and inv_quantity_on_hand between 100 and 500
 and ss_item_sk = i_item_sk
 group by i_item_id,i_item_desc,i_current_price
 order by i_item_id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  i_item_id
       ,i_item_desc
       ,i_current_price
 from item, inventory, date_dim, store_sales
 where i_current_price between 5 and 5+30
 and inv_item_sk = i_item_sk
 and d_date_sk=inv_date_sk
 and d_date between cast('2002-01-21' as date) and (cast('2002-01-21' as date) +  60 )
 and i_manufact_id in (283,951,566,111)
 and inv_quantity_on_hand between 100 and 500
 and ss_item_sk = i_item_sk
 group by i_item_id,i_item_desc,i_current_price
 order by i_item_id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  i_item_id
       ,i_item_desc
       ,i_current_price
 from item, inventory, date_dim, store_sales
 where i_current_price between 67 and 67+30
 and inv_item_sk = i_item_sk
 and d_date_sk=inv_date_sk
 and d_date between cast('2000-03-09' as date) and (cast('2000-03-09' as date) +  60 )
 and i_manufact_id in (839,405,382,485)
 and inv_quantity_on_hand between 100 and 500
 and ss_item_sk = i_item_sk
 group by i_item_id,i_item_desc,i_current_price
 order by i_item_id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  i_item_id
       ,i_item_desc
       ,i_current_price
 from item, inventory, date_dim, store_sales
 where i_current_price between 34 and 34+30
 and inv_item_sk = i_item_sk
 and d_date_sk=inv_date_sk
 and d_date between cast('1999-06-07' as date) and (cast('1999-06-07' as date) +  60 )
 and i_manufact_id in (936,442,287,886)
 and inv_quantity_on_hand between 100 and 500
 and ss_item_sk = i_item_sk
 group by i_item_id,i_item_desc,i_current_price
 order by i_item_id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  i_item_id
       ,i_item_desc
       ,i_current_price
 from item, inventory, date_dim, store_sales
 where i_current_price between 70 and 70+30
 and inv_item_sk = i_item_sk
 and d_date_sk=inv_date_sk
 and d_date between cast('2000-06-27' as date) and (cast('2000-06-27' as date) +  60 )
 and i_manufact_id in (942,27,744,941)
 and inv_quantity_on_hand between 100 and 500
 and ss_item_sk = i_item_sk
 group by i_item_id,i_item_desc,i_current_price
 order by i_item_id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  i_item_id
       ,i_item_desc
       ,i_current_price
 from item, inventory, date_dim, store_sales
 where i_current_price between 35 and 35+30
 and inv_item_sk = i_item_sk
 and d_date_sk=inv_date_sk
 and d_date between cast('2002-05-17' as date) and (cast('2002-05-17' as date) +  60 )
 and i_manufact_id in (835,75,900,510)
 and inv_quantity_on_hand between 100 and 500
 and ss_item_sk = i_item_sk
 group by i_item_id,i_item_desc,i_current_price
 order by i_item_id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  i_item_id
       ,i_item_desc
       ,i_current_price
 from item, inventory, date_dim, store_sales
 where i_current_price between 2 and 2+30
 and inv_item_sk = i_item_sk
 and d_date_sk=inv_date_sk
 and d_date between cast('2001-01-19' as date) and (cast('2001-01-19' as date) +  60 )
 and i_manufact_id in (489,774,200,790)
 and inv_quantity_on_hand between 100 and 500
 and ss_item_sk = i_item_sk
 group by i_item_id,i_item_desc,i_current_price
 order by i_item_id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  i_item_id
       ,i_item_desc
       ,i_current_price
 from item, inventory, date_dim, store_sales
 where i_current_price between 9 and 9+30
 and inv_item_sk = i_item_sk
 and d_date_sk=inv_date_sk
 and d_date between cast('2000-07-15' as date) and (cast('2000-07-15' as date) +  60 )
 and i_manufact_id in (813,331,685,774)
 and inv_quantity_on_hand between 100 and 500
 and ss_item_sk = i_item_sk
 group by i_item_id,i_item_desc,i_current_price
 order by i_item_id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  i_item_id
       ,i_item_desc
       ,i_current_price
 from item, inventory, date_dim, store_sales
 where i_current_price between 45 and 45+30
 and inv_item_sk = i_item_sk
 and d_date_sk=inv_date_sk
 and d_date between cast('2002-07-07' as date) and (cast('2002-07-07' as date) +  60 )
 and i_manufact_id in (618,544,377,790)
 and inv_quantity_on_hand between 100 and 500
 and ss_item_sk = i_item_sk
 group by i_item_id,i_item_desc,i_current_price
 order by i_item_id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  i_item_id
       ,i_item_desc
       ,i_current_price
 from item, inventory, date_dim, store_sales
 where i_current_price between 72 and 72+30
 and inv_item_sk = i_item_sk
 and d_date_sk=inv_date_sk
 and d_date between cast('2000-03-28' as date) and (cast('2000-03-28' as date) +  60 )
 and i_manufact_id in (217,244,362,982)
 and inv_quantity_on_hand between 100 and 500
 and ss_item_sk = i_item_sk
 group by i_item_id,i_item_desc,i_current_price
 order by i_item_id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  i_item_id
       ,i_item_desc
       ,i_current_price
 from item, inventory, date_dim, store_sales
 where i_current_price between 16 and 16+30
 and inv_item_sk = i_item_sk
 and d_date_sk=inv_date_sk
 and d_date between cast('2001-05-14' as date) and (cast('2001-05-14' as date) +  60 )
 and i_manufact_id in (401,963,257,184)
 and inv_quantity_on_hand between 100 and 500
 and ss_item_sk = i_item_sk
 group by i_item_id,i_item_desc,i_current_price
 order by i_item_id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  i_item_id
       ,i_item_desc
       ,i_current_price
 from item, inventory, date_dim, store_sales
 where i_current_price between 29 and 29+30
 and inv_item_sk = i_item_sk
 and d_date_sk=inv_date_sk
 and d_date between cast('2001-01-22' as date) and (cast('2001-01-22' as date) +  60 )
 and i_manufact_id in (699,531,714,110)
 and inv_quantity_on_hand between 100 and 500
 and ss_item_sk = i_item_sk
 group by i_item_id,i_item_desc,i_current_price
 order by i_item_id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  i_item_id
       ,i_item_desc
       ,i_current_price
 from item, inventory, date_dim, store_sales
 where i_current_price between 35 and 35+30
 and inv_item_sk = i_item_sk
 and d_date_sk=inv_date_sk
 and d_date between cast('1998-05-14' as date) and (cast('1998-05-14' as date) +  60 )
 and i_manufact_id in (559,839,179,986)
 and inv_quantity_on_hand between 100 and 500
 and ss_item_sk = i_item_sk
 group by i_item_id,i_item_desc,i_current_price
 order by i_item_id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  i_item_id
       ,i_item_desc
       ,i_current_price
 from item, inventory, date_dim, store_sales
 where i_current_price between 22 and 22+30
 and inv_item_sk = i_item_sk
 and d_date_sk=inv_date_sk
 and d_date between cast('2002-07-18' as date) and (cast('2002-07-18' as date) +  60 )
 and i_manufact_id in (850,549,228,288)
 and inv_quantity_on_hand between 100 and 500
 and ss_item_sk = i_item_sk
 group by i_item_id,i_item_desc,i_current_price
 order by i_item_id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  i_item_id
       ,i_item_desc
       ,i_current_price
 from item, inventory, date_dim, store_sales
 where i_current_price between 8 and 8+30
 and inv_item_sk = i_item_sk
 and d_date_sk=inv_date_sk
 and d_date between cast('1999-03-17' as date) and (cast('1999-03-17' as date) +  60 )
 and i_manufact_id in (625,565,515,854)
 and inv_quantity_on_hand between 100 and 500
 and ss_item_sk = i_item_sk
 group by i_item_id,i_item_desc,i_current_price
 order by i_item_id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  i_item_id
       ,i_item_desc
       ,i_current_price
 from item, inventory, date_dim, store_sales
 where i_current_price between 60 and 60+30
 and inv_item_sk = i_item_sk
 and d_date_sk=inv_date_sk
 and d_date between cast('2000-05-31' as date) and (cast('2000-05-31' as date) +  60 )
 and i_manufact_id in (730,78,521,254)
 and inv_quantity_on_hand between 100 and 500
 and ss_item_sk = i_item_sk
 group by i_item_id,i_item_desc,i_current_price
 order by i_item_id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  i_item_id
       ,i_item_desc
       ,i_current_price
 from item, inventory, date_dim, store_sales
 where i_current_price between 43 and 43+30
 and inv_item_sk = i_item_sk
 and d_date_sk=inv_date_sk
 and d_date between cast('1998-04-21' as date) and (cast('1998-04-21' as date) +  60 )
 and i_manufact_id in (559,57,690,314)
 and inv_quantity_on_hand between 100 and 500
 and ss_item_sk = i_item_sk
 group by i_item_id,i_item_desc,i_current_price
 order by i_item_id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  i_item_id
       ,i_item_desc
       ,i_current_price
 from item, inventory, date_dim, store_sales
 where i_current_price between 2 and 2+30
 and inv_item_sk = i_item_sk
 and d_date_sk=inv_date_sk
 and d_date between cast('2002-05-04' as date) and (cast('2002-05-04' as date) +  60 )
 and i_manufact_id in (63,234,857,618)
 and inv_quantity_on_hand between 100 and 500
 and ss_item_sk = i_item_sk
 group by i_item_id,i_item_desc,i_current_price
 order by i_item_id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  i_item_id
       ,i_item_desc
       ,i_current_price
 from item, inventory, date_dim, store_sales
 where i_current_price between 34 and 34+30
 and inv_item_sk = i_item_sk
 and d_date_sk=inv_date_sk
 and d_date between cast('1998-02-17' as date) and (cast('1998-02-17' as date) +  60 )
 and i_manufact_id in (975,30,764,96)
 and inv_quantity_on_hand between 100 and 500
 and ss_item_sk = i_item_sk
 group by i_item_id,i_item_desc,i_current_price
 order by i_item_id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  i_item_id
       ,i_item_desc
       ,i_current_price
 from item, inventory, date_dim, store_sales
 where i_current_price between 65 and 65+30
 and inv_item_sk = i_item_sk
 and d_date_sk=inv_date_sk
 and d_date between cast('1999-03-08' as date) and (cast('1999-03-08' as date) +  60 )
 and i_manufact_id in (136,971,402,517)
 and inv_quantity_on_hand between 100 and 500
 and ss_item_sk = i_item_sk
 group by i_item_id,i_item_desc,i_current_price
 order by i_item_id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  i_item_id
       ,i_item_desc
       ,i_current_price
 from item, inventory, date_dim, store_sales
 where i_current_price between 52 and 52+30
 and inv_item_sk = i_item_sk
 and d_date_sk=inv_date_sk
 and d_date between cast('1999-03-18' as date) and (cast('1999-03-18' as date) +  60 )
 and i_manufact_id in (263,771,73,193)
 and inv_quantity_on_hand between 100 and 500
 and ss_item_sk = i_item_sk
 group by i_item_id,i_item_desc,i_current_price
 order by i_item_id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  i_item_id
       ,i_item_desc
       ,i_current_price
 from item, inventory, date_dim, store_sales
 where i_current_price between 30 and 30+30
 and inv_item_sk = i_item_sk
 and d_date_sk=inv_date_sk
 and d_date between cast('2002-02-28' as date) and (cast('2002-02-28' as date) +  60 )
 and i_manufact_id in (513,749,502,723)
 and inv_quantity_on_hand between 100 and 500
 and ss_item_sk = i_item_sk
 group by i_item_id,i_item_desc,i_current_price
 order by i_item_id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  i_item_id
       ,i_item_desc
       ,i_current_price
 from item, inventory, date_dim, store_sales
 where i_current_price between 51 and 51+30
 and inv_item_sk = i_item_sk
 and d_date_sk=inv_date_sk
 and d_date between cast('2002-03-01' as date) and (cast('2002-03-01' as date) +  60 )
 and i_manufact_id in (858,1000,117,314)
 and inv_quantity_on_hand between 100 and 500
 and ss_item_sk = i_item_sk
 group by i_item_id,i_item_desc,i_current_price
 order by i_item_id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  i_item_id
       ,i_item_desc
       ,i_current_price
 from item, inventory, date_dim, store_sales
 where i_current_price between 70 and 70+30
 and inv_item_sk = i_item_sk
 and d_date_sk=inv_date_sk
 and d_date between cast('1998-03-08' as date) and (cast('1998-03-08' as date) +  60 )
 and i_manufact_id in (521,144,77,759)
 and inv_quantity_on_hand between 100 and 500
 and ss_item_sk = i_item_sk
 group by i_item_id,i_item_desc,i_current_price
 order by i_item_id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  i_item_id
       ,i_item_desc
       ,i_current_price
 from item, inventory, date_dim, store_sales
 where i_current_price between 79 and 79+30
 and inv_item_sk = i_item_sk
 and d_date_sk=inv_date_sk
 and d_date between cast('2001-05-18' as date) and (cast('2001-05-18' as date) +  60 )
 and i_manufact_id in (812,379,638,872)
 and inv_quantity_on_hand between 100 and 500
 and ss_item_sk = i_item_sk
 group by i_item_id,i_item_desc,i_current_price
 order by i_item_id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  i_item_id
       ,i_item_desc
       ,i_current_price
 from item, inventory, date_dim, store_sales
 where i_current_price between 83 and 83+30
 and inv_item_sk = i_item_sk
 and d_date_sk=inv_date_sk
 and d_date between cast('2002-01-23' as date) and (cast('2002-01-23' as date) +  60 )
 and i_manufact_id in (633,392,378,471)
 and inv_quantity_on_hand between 100 and 500
 and ss_item_sk = i_item_sk
 group by i_item_id,i_item_desc,i_current_price
 order by i_item_id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  i_item_id
       ,i_item_desc
       ,i_current_price
 from item, inventory, date_dim, store_sales
 where i_current_price between 22 and 22+30
 and inv_item_sk = i_item_sk
 and d_date_sk=inv_date_sk
 and d_date between cast('1998-07-19' as date) and (cast('1998-07-19' as date) +  60 )
 and i_manufact_id in (870,433,255,124)
 and inv_quantity_on_hand between 100 and 500
 and ss_item_sk = i_item_sk
 group by i_item_id,i_item_desc,i_current_price
 order by i_item_id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  i_item_id
       ,i_item_desc
       ,i_current_price
 from item, inventory, date_dim, store_sales
 where i_current_price between 23 and 23+30
 and inv_item_sk = i_item_sk
 and d_date_sk=inv_date_sk
 and d_date between cast('2002-02-19' as date) and (cast('2002-02-19' as date) +  60 )
 and i_manufact_id in (491,847,706,608)
 and inv_quantity_on_hand between 100 and 500
 and ss_item_sk = i_item_sk
 group by i_item_id,i_item_desc,i_current_price
 order by i_item_id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  i_item_id
       ,i_item_desc
       ,i_current_price
 from item, inventory, date_dim, store_sales
 where i_current_price between 9 and 9+30
 and inv_item_sk = i_item_sk
 and d_date_sk=inv_date_sk
 and d_date between cast('2002-02-28' as date) and (cast('2002-02-28' as date) +  60 )
 and i_manufact_id in (730,894,907,684)
 and inv_quantity_on_hand between 100 and 500
 and ss_item_sk = i_item_sk
 group by i_item_id,i_item_desc,i_current_price
 order by i_item_id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  i_item_id
       ,i_item_desc
       ,i_current_price
 from item, inventory, date_dim, store_sales
 where i_current_price between 68 and 68+30
 and inv_item_sk = i_item_sk
 and d_date_sk=inv_date_sk
 and d_date between cast('1999-06-06' as date) and (cast('1999-06-06' as date) +  60 )
 and i_manufact_id in (184,377,531,815)
 and inv_quantity_on_hand between 100 and 500
 and ss_item_sk = i_item_sk
 group by i_item_id,i_item_desc,i_current_price
 order by i_item_id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  i_item_id
       ,i_item_desc
       ,i_current_price
 from item, inventory, date_dim, store_sales
 where i_current_price between 33 and 33+30
 and inv_item_sk = i_item_sk
 and d_date_sk=inv_date_sk
 and d_date between cast('2002-07-22' as date) and (cast('2002-07-22' as date) +  60 )
 and i_manufact_id in (318,906,374,961)
 and inv_quantity_on_hand between 100 and 500
 and ss_item_sk = i_item_sk
 group by i_item_id,i_item_desc,i_current_price
 order by i_item_id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  i_item_id
       ,i_item_desc
       ,i_current_price
 from item, inventory, date_dim, store_sales
 where i_current_price between 21 and 21+30
 and inv_item_sk = i_item_sk
 and d_date_sk=inv_date_sk
 and d_date between cast('2002-06-05' as date) and (cast('2002-06-05' as date) +  60 )
 and i_manufact_id in (791,530,183,100)
 and inv_quantity_on_hand between 100 and 500
 and ss_item_sk = i_item_sk
 group by i_item_id,i_item_desc,i_current_price
 order by i_item_id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  i_item_id
       ,i_item_desc
       ,i_current_price
 from item, inventory, date_dim, store_sales
 where i_current_price between 19 and 19+30
 and inv_item_sk = i_item_sk
 and d_date_sk=inv_date_sk
 and d_date between cast('2000-02-15' as date) and (cast('2000-02-15' as date) +  60 )
 and i_manufact_id in (543,631,59,979)
 and inv_quantity_on_hand between 100 and 500
 and ss_item_sk = i_item_sk
 group by i_item_id,i_item_desc,i_current_price
 order by i_item_id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  i_item_id
       ,i_item_desc
       ,i_current_price
 from item, inventory, date_dim, store_sales
 where i_current_price between 44 and 44+30
 and inv_item_sk = i_item_sk
 and d_date_sk=inv_date_sk
 and d_date between cast('2001-01-19' as date) and (cast('2001-01-19' as date) +  60 )
 and i_manufact_id in (343,303,584,321)
 and inv_quantity_on_hand between 100 and 500
 and ss_item_sk = i_item_sk
 group by i_item_id,i_item_desc,i_current_price
 order by i_item_id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  i_item_id
       ,i_item_desc
       ,i_current_price
 from item, inventory, date_dim, store_sales
 where i_current_price between 55 and 55+30
 and inv_item_sk = i_item_sk
 and d_date_sk=inv_date_sk
 and d_date between cast('1999-05-06' as date) and (cast('1999-05-06' as date) +  60 )
 and i_manufact_id in (802,564,513,894)
 and inv_quantity_on_hand between 100 and 500
 and ss_item_sk = i_item_sk
 group by i_item_id,i_item_desc,i_current_price
 order by i_item_id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  i_item_id
       ,i_item_desc
       ,i_current_price
 from item, inventory, date_dim, store_sales
 where i_current_price between 56 and 56+30
 and inv_item_sk = i_item_sk
 and d_date_sk=inv_date_sk
 and d_date between cast('2001-07-07' as date) and (cast('2001-07-07' as date) +  60 )
 and i_manufact_id in (874,946,80,482)
 and inv_quantity_on_hand between 100 and 500
 and ss_item_sk = i_item_sk
 group by i_item_id,i_item_desc,i_current_price
 order by i_item_id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  i_item_id
       ,i_item_desc
       ,i_current_price
 from item, inventory, date_dim, store_sales
 where i_current_price between 37 and 37+30
 and inv_item_sk = i_item_sk
 and d_date_sk=inv_date_sk
 and d_date between cast('2001-06-01' as date) and (cast('2001-06-01' as date) +  60 )
 and i_manufact_id in (322,374,318,680)
 and inv_quantity_on_hand between 100 and 500
 and ss_item_sk = i_item_sk
 group by i_item_id,i_item_desc,i_current_price
 order by i_item_id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  i_item_id
       ,i_item_desc
       ,i_current_price
 from item, inventory, date_dim, store_sales
 where i_current_price between 39 and 39+30
 and inv_item_sk = i_item_sk
 and d_date_sk=inv_date_sk
 and d_date between cast('1998-04-06' as date) and (cast('1998-04-06' as date) +  60 )
 and i_manufact_id in (105,137,991,713)
 and inv_quantity_on_hand between 100 and 500
 and ss_item_sk = i_item_sk
 group by i_item_id,i_item_desc,i_current_price
 order by i_item_id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  i_item_id
       ,i_item_desc
       ,i_current_price
 from item, inventory, date_dim, store_sales
 where i_current_price between 73 and 73+30
 and inv_item_sk = i_item_sk
 and d_date_sk=inv_date_sk
 and d_date between cast('1998-01-31' as date) and (cast('1998-01-31' as date) +  60 )
 and i_manufact_id in (280,958,150,333)
 and inv_quantity_on_hand between 100 and 500
 and ss_item_sk = i_item_sk
 group by i_item_id,i_item_desc,i_current_price
 order by i_item_id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  i_item_id
       ,i_item_desc
       ,i_current_price
 from item, inventory, date_dim, store_sales
 where i_current_price between 39 and 39+30
 and inv_item_sk = i_item_sk
 and d_date_sk=inv_date_sk
 and d_date between cast('2000-02-29' as date) and (cast('2000-02-29' as date) +  60 )
 and i_manufact_id in (558,492,665,283)
 and inv_quantity_on_hand between 100 and 500
 and ss_item_sk = i_item_sk
 group by i_item_id,i_item_desc,i_current_price
 order by i_item_id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  i_item_id
       ,i_item_desc
       ,i_current_price
 from item, inventory, date_dim, store_sales
 where i_current_price between 77 and 77+30
 and inv_item_sk = i_item_sk
 and d_date_sk=inv_date_sk
 and d_date between cast('2001-01-03' as date) and (cast('2001-01-03' as date) +  60 )
 and i_manufact_id in (125,759,286,287)
 and inv_quantity_on_hand between 100 and 500
 and ss_item_sk = i_item_sk
 group by i_item_id,i_item_desc,i_current_price
 order by i_item_id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  i_item_id
       ,i_item_desc
       ,i_current_price
 from item, inventory, date_dim, store_sales
 where i_current_price between 38 and 38+30
 and inv_item_sk = i_item_sk
 and d_date_sk=inv_date_sk
 and d_date between cast('2001-04-28' as date) and (cast('2001-04-28' as date) +  60 )
 and i_manufact_id in (262,33,374,651)
 and inv_quantity_on_hand between 100 and 500
 and ss_item_sk = i_item_sk
 group by i_item_id,i_item_desc,i_current_price
 order by i_item_id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  i_item_id
       ,i_item_desc
       ,i_current_price
 from item, inventory, date_dim, store_sales
 where i_current_price between 26 and 26+30
 and inv_item_sk = i_item_sk
 and d_date_sk=inv_date_sk
 and d_date between cast('2002-02-02' as date) and (cast('2002-02-02' as date) +  60 )
 and i_manufact_id in (349,784,865,473)
 and inv_quantity_on_hand between 100 and 500
 and ss_item_sk = i_item_sk
 group by i_item_id,i_item_desc,i_current_price
 order by i_item_id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  i_item_id
       ,i_item_desc
       ,i_current_price
 from item, inventory, date_dim, store_sales
 where i_current_price between 27 and 27+30
 and inv_item_sk = i_item_sk
 and d_date_sk=inv_date_sk
 and d_date between cast('1999-02-16' as date) and (cast('1999-02-16' as date) +  60 )
 and i_manufact_id in (539,115,614,79)
 and inv_quantity_on_hand between 100 and 500
 and ss_item_sk = i_item_sk
 group by i_item_id,i_item_desc,i_current_price
 order by i_item_id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  i_item_id
       ,i_item_desc
       ,i_current_price
 from item, inventory, date_dim, store_sales
 where i_current_price between 65 and 65+30
 and inv_item_sk = i_item_sk
 and d_date_sk=inv_date_sk
 and d_date between cast('2001-06-06' as date) and (cast('2001-06-06' as date) +  60 )
 and i_manufact_id in (884,594,722,319)
 and inv_quantity_on_hand between 100 and 500
 and ss_item_sk = i_item_sk
 group by i_item_id,i_item_desc,i_current_price
 order by i_item_id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  i_item_id
       ,i_item_desc
       ,i_current_price
 from item, inventory, date_dim, store_sales
 where i_current_price between 53 and 53+30
 and inv_item_sk = i_item_sk
 and d_date_sk=inv_date_sk
 and d_date between cast('2000-03-23' as date) and (cast('2000-03-23' as date) +  60 )
 and i_manufact_id in (834,75,767,188)
 and inv_quantity_on_hand between 100 and 500
 and ss_item_sk = i_item_sk
 group by i_item_id,i_item_desc,i_current_price
 order by i_item_id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  i_item_id
       ,i_item_desc
       ,i_current_price
 from item, inventory, date_dim, store_sales
 where i_current_price between 45 and 45+30
 and inv_item_sk = i_item_sk
 and d_date_sk=inv_date_sk
 and d_date between cast('2001-06-01' as date) and (cast('2001-06-01' as date) +  60 )
 and i_manufact_id in (421,290,880,462)
 and inv_quantity_on_hand between 100 and 500
 and ss_item_sk = i_item_sk
 group by i_item_id,i_item_desc,i_current_price
 order by i_item_id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  i_item_id
       ,i_item_desc
       ,i_current_price
 from item, inventory, date_dim, store_sales
 where i_current_price between 74 and 74+30
 and inv_item_sk = i_item_sk
 and d_date_sk=inv_date_sk
 and d_date between cast('2002-04-07' as date) and (cast('2002-04-07' as date) +  60 )
 and i_manufact_id in (517,456,591,321)
 and inv_quantity_on_hand between 100 and 500
 and ss_item_sk = i_item_sk
 group by i_item_id,i_item_desc,i_current_price
 order by i_item_id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  i_item_id
       ,i_item_desc
       ,i_current_price
 from item, inventory, date_dim, store_sales
 where i_current_price between 85 and 85+30
 and inv_item_sk = i_item_sk
 and d_date_sk=inv_date_sk
 and d_date between cast('1999-05-06' as date) and (cast('1999-05-06' as date) +  60 )
 and i_manufact_id in (866,18,348,499)
 and inv_quantity_on_hand between 100 and 500
 and ss_item_sk = i_item_sk
 group by i_item_id,i_item_desc,i_current_price
 order by i_item_id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  i_item_id
       ,i_item_desc
       ,i_current_price
 from item, inventory, date_dim, store_sales
 where i_current_price between 4 and 4+30
 and inv_item_sk = i_item_sk
 and d_date_sk=inv_date_sk
 and d_date between cast('2001-03-01' as date) and (cast('2001-03-01' as date) +  60 )
 and i_manufact_id in (502,728,213,593)
 and inv_quantity_on_hand between 100 and 500
 and ss_item_sk = i_item_sk
 group by i_item_id,i_item_desc,i_current_price
 order by i_item_id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  i_item_id
       ,i_item_desc
       ,i_current_price
 from item, inventory, date_dim, store_sales
 where i_current_price between 75 and 75+30
 and inv_item_sk = i_item_sk
 and d_date_sk=inv_date_sk
 and d_date between cast('2001-05-05' as date) and (cast('2001-05-05' as date) +  60 )
 and i_manufact_id in (213,665,610,184)
 and inv_quantity_on_hand between 100 and 500
 and ss_item_sk = i_item_sk
 group by i_item_id,i_item_desc,i_current_price
 order by i_item_id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  i_item_id
       ,i_item_desc
       ,i_current_price
 from item, inventory, date_dim, store_sales
 where i_current_price between 46 and 46+30
 and inv_item_sk = i_item_sk
 and d_date_sk=inv_date_sk
 and d_date between cast('1999-05-19' as date) and (cast('1999-05-19' as date) +  60 )
 and i_manufact_id in (505,616,920,935)
 and inv_quantity_on_hand between 100 and 500
 and ss_item_sk = i_item_sk
 group by i_item_id,i_item_desc,i_current_price
 order by i_item_id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  i_item_id
       ,i_item_desc
       ,i_current_price
 from item, inventory, date_dim, store_sales
 where i_current_price between 46 and 46+30
 and inv_item_sk = i_item_sk
 and d_date_sk=inv_date_sk
 and d_date between cast('1999-03-25' as date) and (cast('1999-03-25' as date) +  60 )
 and i_manufact_id in (892,384,347,36)
 and inv_quantity_on_hand between 100 and 500
 and ss_item_sk = i_item_sk
 group by i_item_id,i_item_desc,i_current_price
 order by i_item_id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  i_item_id
       ,i_item_desc
       ,i_current_price
 from item, inventory, date_dim, store_sales
 where i_current_price between 9 and 9+30
 and inv_item_sk = i_item_sk
 and d_date_sk=inv_date_sk
 and d_date between cast('2001-05-23' as date) and (cast('2001-05-23' as date) +  60 )
 and i_manufact_id in (714,305,756,537)
 and inv_quantity_on_hand between 100 and 500
 and ss_item_sk = i_item_sk
 group by i_item_id,i_item_desc,i_current_price
 order by i_item_id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  i_item_id
       ,i_item_desc
       ,i_current_price
 from item, inventory, date_dim, store_sales
 where i_current_price between 13 and 13+30
 and inv_item_sk = i_item_sk
 and d_date_sk=inv_date_sk
 and d_date between cast('1999-04-09' as date) and (cast('1999-04-09' as date) +  60 )
 and i_manufact_id in (764,268,833,16)
 and inv_quantity_on_hand between 100 and 500
 and ss_item_sk = i_item_sk
 group by i_item_id,i_item_desc,i_current_price
 order by i_item_id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  i_item_id
       ,i_item_desc
       ,i_current_price
 from item, inventory, date_dim, store_sales
 where i_current_price between 69 and 69+30
 and inv_item_sk = i_item_sk
 and d_date_sk=inv_date_sk
 and d_date between cast('1999-04-27' as date) and (cast('1999-04-27' as date) +  60 )
 and i_manufact_id in (949,28,204,736)
 and inv_quantity_on_hand between 100 and 500
 and ss_item_sk = i_item_sk
 group by i_item_id,i_item_desc,i_current_price
 order by i_item_id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  i_item_id
       ,i_item_desc
       ,i_current_price
 from item, inventory, date_dim, store_sales
 where i_current_price between 86 and 86+30
 and inv_item_sk = i_item_sk
 and d_date_sk=inv_date_sk
 and d_date between cast('1998-02-01' as date) and (cast('1998-02-01' as date) +  60 )
 and i_manufact_id in (110,102,758,850)
 and inv_quantity_on_hand between 100 and 500
 and ss_item_sk = i_item_sk
 group by i_item_id,i_item_desc,i_current_price
 order by i_item_id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  i_item_id
       ,i_item_desc
       ,i_current_price
 from item, inventory, date_dim, store_sales
 where i_current_price between 89 and 89+30
 and inv_item_sk = i_item_sk
 and d_date_sk=inv_date_sk
 and d_date between cast('1998-02-11' as date) and (cast('1998-02-11' as date) +  60 )
 and i_manufact_id in (262,464,3,768)
 and inv_quantity_on_hand between 100 and 500
 and ss_item_sk = i_item_sk
 group by i_item_id,i_item_desc,i_current_price
 order by i_item_id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  i_item_id
       ,i_item_desc
       ,i_current_price
 from item, inventory, date_dim, store_sales
 where i_current_price between 3 and 3+30
 and inv_item_sk = i_item_sk
 and d_date_sk=inv_date_sk
 and d_date between cast('2001-04-27' as date) and (cast('2001-04-27' as date) +  60 )
 and i_manufact_id in (723,251,782,299)
 and inv_quantity_on_hand between 100 and 500
 and ss_item_sk = i_item_sk
 group by i_item_id,i_item_desc,i_current_price
 order by i_item_id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  i_item_id
       ,i_item_desc
       ,i_current_price
 from item, inventory, date_dim, store_sales
 where i_current_price between 60 and 60+30
 and inv_item_sk = i_item_sk
 and d_date_sk=inv_date_sk
 and d_date between cast('2002-03-19' as date) and (cast('2002-03-19' as date) +  60 )
 and i_manufact_id in (999,352,617,212)
 and inv_quantity_on_hand between 100 and 500
 and ss_item_sk = i_item_sk
 group by i_item_id,i_item_desc,i_current_price
 order by i_item_id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  i_item_id
       ,i_item_desc
       ,i_current_price
 from item, inventory, date_dim, store_sales
 where i_current_price between 48 and 48+30
 and inv_item_sk = i_item_sk
 and d_date_sk=inv_date_sk
 and d_date between cast('1999-03-18' as date) and (cast('1999-03-18' as date) +  60 )
 and i_manufact_id in (159,251,762,248)
 and inv_quantity_on_hand between 100 and 500
 and ss_item_sk = i_item_sk
 group by i_item_id,i_item_desc,i_current_price
 order by i_item_id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  i_item_id
       ,i_item_desc
       ,i_current_price
 from item, inventory, date_dim, store_sales
 where i_current_price between 88 and 88+30
 and inv_item_sk = i_item_sk
 and d_date_sk=inv_date_sk
 and d_date between cast('2002-02-04' as date) and (cast('2002-02-04' as date) +  60 )
 and i_manufact_id in (955,765,714,561)
 and inv_quantity_on_hand between 100 and 500
 and ss_item_sk = i_item_sk
 group by i_item_id,i_item_desc,i_current_price
 order by i_item_id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  i_item_id
       ,i_item_desc
       ,i_current_price
 from item, inventory, date_dim, store_sales
 where i_current_price between 56 and 56+30
 and inv_item_sk = i_item_sk
 and d_date_sk=inv_date_sk
 and d_date between cast('1998-04-21' as date) and (cast('1998-04-21' as date) +  60 )
 and i_manufact_id in (803,265,968,87)
 and inv_quantity_on_hand between 100 and 500
 and ss_item_sk = i_item_sk
 group by i_item_id,i_item_desc,i_current_price
 order by i_item_id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  i_item_id
       ,i_item_desc
       ,i_current_price
 from item, inventory, date_dim, store_sales
 where i_current_price between 50 and 50+30
 and inv_item_sk = i_item_sk
 and d_date_sk=inv_date_sk
 and d_date between cast('2001-05-10' as date) and (cast('2001-05-10' as date) +  60 )
 and i_manufact_id in (102,52,204,592)
 and inv_quantity_on_hand between 100 and 500
 and ss_item_sk = i_item_sk
 group by i_item_id,i_item_desc,i_current_price
 order by i_item_id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  i_item_id
       ,i_item_desc
       ,i_current_price
 from item, inventory, date_dim, store_sales
 where i_current_price between 8 and 8+30
 and inv_item_sk = i_item_sk
 and d_date_sk=inv_date_sk
 and d_date between cast('1999-04-09' as date) and (cast('1999-04-09' as date) +  60 )
 and i_manufact_id in (607,390,21,116)
 and inv_quantity_on_hand between 100 and 500
 and ss_item_sk = i_item_sk
 group by i_item_id,i_item_desc,i_current_price
 order by i_item_id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  i_item_id
       ,i_item_desc
       ,i_current_price
 from item, inventory, date_dim, store_sales
 where i_current_price between 13 and 13+30
 and inv_item_sk = i_item_sk
 and d_date_sk=inv_date_sk
 and d_date between cast('2000-04-30' as date) and (cast('2000-04-30' as date) +  60 )
 and i_manufact_id in (375,141,290,198)
 and inv_quantity_on_hand between 100 and 500
 and ss_item_sk = i_item_sk
 group by i_item_id,i_item_desc,i_current_price
 order by i_item_id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  i_item_id
       ,i_item_desc
       ,i_current_price
 from item, inventory, date_dim, store_sales
 where i_current_price between 2 and 2+30
 and inv_item_sk = i_item_sk
 and d_date_sk=inv_date_sk
 and d_date between cast('1999-04-12' as date) and (cast('1999-04-12' as date) +  60 )
 and i_manufact_id in (143,144,205,382)
 and inv_quantity_on_hand between 100 and 500
 and ss_item_sk = i_item_sk
 group by i_item_id,i_item_desc,i_current_price
 order by i_item_id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  i_item_id
       ,i_item_desc
       ,i_current_price
 from item, inventory, date_dim, store_sales
 where i_current_price between 38 and 38+30
 and inv_item_sk = i_item_sk
 and d_date_sk=inv_date_sk
 and d_date between cast('1999-04-08' as date) and (cast('1999-04-08' as date) +  60 )
 and i_manufact_id in (96,838,622,931)
 and inv_quantity_on_hand between 100 and 500
 and ss_item_sk = i_item_sk
 group by i_item_id,i_item_desc,i_current_price
 order by i_item_id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  i_item_id
       ,i_item_desc
       ,i_current_price
 from item, inventory, date_dim, store_sales
 where i_current_price between 10 and 10+30
 and inv_item_sk = i_item_sk
 and d_date_sk=inv_date_sk
 and d_date between cast('2001-06-29' as date) and (cast('2001-06-29' as date) +  60 )
 and i_manufact_id in (408,22,999,986)
 and inv_quantity_on_hand between 100 and 500
 and ss_item_sk = i_item_sk
 group by i_item_id,i_item_desc,i_current_price
 order by i_item_id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  i_item_id
       ,i_item_desc
       ,i_current_price
 from item, inventory, date_dim, store_sales
 where i_current_price between 27 and 27+30
 and inv_item_sk = i_item_sk
 and d_date_sk=inv_date_sk
 and d_date between cast('2002-06-04' as date) and (cast('2002-06-04' as date) +  60 )
 and i_manufact_id in (996,775,48,389)
 and inv_quantity_on_hand between 100 and 500
 and ss_item_sk = i_item_sk
 group by i_item_id,i_item_desc,i_current_price
 order by i_item_id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  i_item_id
       ,i_item_desc
       ,i_current_price
 from item, inventory, date_dim, store_sales
 where i_current_price between 37 and 37+30
 and inv_item_sk = i_item_sk
 and d_date_sk=inv_date_sk
 and d_date between cast('2001-01-25' as date) and (cast('2001-01-25' as date) +  60 )
 and i_manufact_id in (14,140,724,795)
 and inv_quantity_on_hand between 100 and 500
 and ss_item_sk = i_item_sk
 group by i_item_id,i_item_desc,i_current_price
 order by i_item_id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  i_item_id
       ,i_item_desc
       ,i_current_price
 from item, inventory, date_dim, store_sales
 where i_current_price between 42 and 42+30
 and inv_item_sk = i_item_sk
 and d_date_sk=inv_date_sk
 and d_date between cast('2001-03-21' as date) and (cast('2001-03-21' as date) +  60 )
 and i_manufact_id in (116,877,360,602)
 and inv_quantity_on_hand between 100 and 500
 and ss_item_sk = i_item_sk
 group by i_item_id,i_item_desc,i_current_price
 order by i_item_id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  i_item_id
       ,i_item_desc
       ,i_current_price
 from item, inventory, date_dim, store_sales
 where i_current_price between 8 and 8+30
 and inv_item_sk = i_item_sk
 and d_date_sk=inv_date_sk
 and d_date between cast('1998-04-22' as date) and (cast('1998-04-22' as date) +  60 )
 and i_manufact_id in (641,601,653,598)
 and inv_quantity_on_hand between 100 and 500
 and ss_item_sk = i_item_sk
 group by i_item_id,i_item_desc,i_current_price
 order by i_item_id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  i_item_id
       ,i_item_desc
       ,i_current_price
 from item, inventory, date_dim, store_sales
 where i_current_price between 44 and 44+30
 and inv_item_sk = i_item_sk
 and d_date_sk=inv_date_sk
 and d_date between cast('2001-04-01' as date) and (cast('2001-04-01' as date) +  60 )
 and i_manufact_id in (410,513,310,684)
 and inv_quantity_on_hand between 100 and 500
 and ss_item_sk = i_item_sk
 group by i_item_id,i_item_desc,i_current_price
 order by i_item_id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  i_item_id
       ,i_item_desc
       ,i_current_price
 from item, inventory, date_dim, store_sales
 where i_current_price between 87 and 87+30
 and inv_item_sk = i_item_sk
 and d_date_sk=inv_date_sk
 and d_date between cast('2000-01-09' as date) and (cast('2000-01-09' as date) +  60 )
 and i_manufact_id in (897,766,54,88)
 and inv_quantity_on_hand between 100 and 500
 and ss_item_sk = i_item_sk
 group by i_item_id,i_item_desc,i_current_price
 order by i_item_id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  i_item_id
       ,i_item_desc
       ,i_current_price
 from item, inventory, date_dim, store_sales
 where i_current_price between 29 and 29+30
 and inv_item_sk = i_item_sk
 and d_date_sk=inv_date_sk
 and d_date between cast('1998-03-03' as date) and (cast('1998-03-03' as date) +  60 )
 and i_manufact_id in (248,409,826,918)
 and inv_quantity_on_hand between 100 and 500
 and ss_item_sk = i_item_sk
 group by i_item_id,i_item_desc,i_current_price
 order by i_item_id
 limit 100;

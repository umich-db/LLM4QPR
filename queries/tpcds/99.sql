EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk <= 30 ) then 1 else 0 end)  as "30 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 30) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 60) then 1 else 0 end )  as "31-60 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 60) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 90) then 1 else 0 end)  as "61-90 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 90) and
                 (cs_ship_date_sk - cs_sold_date_sk <= 120) then 1 else 0 end)  as "91-120 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk  > 120) then 1 else 0 end)  as ">120 days" 
from
   catalog_sales
  ,warehouse
  ,ship_mode
  ,call_center
  ,date_dim
where
    d_month_seq between 1212 and 1212 + 11
and cs_ship_date_sk   = d_date_sk
and cs_warehouse_sk   = w_warehouse_sk
and cs_ship_mode_sk   = sm_ship_mode_sk
and cs_call_center_sk = cc_call_center_sk
group by
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
order by substr(w_warehouse_name,1,20)
        ,sm_type
        ,cc_name
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk <= 30 ) then 1 else 0 end)  as "30 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 30) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 60) then 1 else 0 end )  as "31-60 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 60) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 90) then 1 else 0 end)  as "61-90 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 90) and
                 (cs_ship_date_sk - cs_sold_date_sk <= 120) then 1 else 0 end)  as "91-120 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk  > 120) then 1 else 0 end)  as ">120 days" 
from
   catalog_sales
  ,warehouse
  ,ship_mode
  ,call_center
  ,date_dim
where
    d_month_seq between 1190 and 1190 + 11
and cs_ship_date_sk   = d_date_sk
and cs_warehouse_sk   = w_warehouse_sk
and cs_ship_mode_sk   = sm_ship_mode_sk
and cs_call_center_sk = cc_call_center_sk
group by
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
order by substr(w_warehouse_name,1,20)
        ,sm_type
        ,cc_name
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk <= 30 ) then 1 else 0 end)  as "30 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 30) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 60) then 1 else 0 end )  as "31-60 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 60) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 90) then 1 else 0 end)  as "61-90 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 90) and
                 (cs_ship_date_sk - cs_sold_date_sk <= 120) then 1 else 0 end)  as "91-120 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk  > 120) then 1 else 0 end)  as ">120 days" 
from
   catalog_sales
  ,warehouse
  ,ship_mode
  ,call_center
  ,date_dim
where
    d_month_seq between 1178 and 1178 + 11
and cs_ship_date_sk   = d_date_sk
and cs_warehouse_sk   = w_warehouse_sk
and cs_ship_mode_sk   = sm_ship_mode_sk
and cs_call_center_sk = cc_call_center_sk
group by
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
order by substr(w_warehouse_name,1,20)
        ,sm_type
        ,cc_name
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk <= 30 ) then 1 else 0 end)  as "30 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 30) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 60) then 1 else 0 end )  as "31-60 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 60) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 90) then 1 else 0 end)  as "61-90 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 90) and
                 (cs_ship_date_sk - cs_sold_date_sk <= 120) then 1 else 0 end)  as "91-120 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk  > 120) then 1 else 0 end)  as ">120 days" 
from
   catalog_sales
  ,warehouse
  ,ship_mode
  ,call_center
  ,date_dim
where
    d_month_seq between 1222 and 1222 + 11
and cs_ship_date_sk   = d_date_sk
and cs_warehouse_sk   = w_warehouse_sk
and cs_ship_mode_sk   = sm_ship_mode_sk
and cs_call_center_sk = cc_call_center_sk
group by
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
order by substr(w_warehouse_name,1,20)
        ,sm_type
        ,cc_name
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk <= 30 ) then 1 else 0 end)  as "30 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 30) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 60) then 1 else 0 end )  as "31-60 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 60) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 90) then 1 else 0 end)  as "61-90 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 90) and
                 (cs_ship_date_sk - cs_sold_date_sk <= 120) then 1 else 0 end)  as "91-120 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk  > 120) then 1 else 0 end)  as ">120 days" 
from
   catalog_sales
  ,warehouse
  ,ship_mode
  ,call_center
  ,date_dim
where
    d_month_seq between 1192 and 1192 + 11
and cs_ship_date_sk   = d_date_sk
and cs_warehouse_sk   = w_warehouse_sk
and cs_ship_mode_sk   = sm_ship_mode_sk
and cs_call_center_sk = cc_call_center_sk
group by
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
order by substr(w_warehouse_name,1,20)
        ,sm_type
        ,cc_name
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk <= 30 ) then 1 else 0 end)  as "30 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 30) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 60) then 1 else 0 end )  as "31-60 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 60) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 90) then 1 else 0 end)  as "61-90 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 90) and
                 (cs_ship_date_sk - cs_sold_date_sk <= 120) then 1 else 0 end)  as "91-120 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk  > 120) then 1 else 0 end)  as ">120 days" 
from
   catalog_sales
  ,warehouse
  ,ship_mode
  ,call_center
  ,date_dim
where
    d_month_seq between 1215 and 1215 + 11
and cs_ship_date_sk   = d_date_sk
and cs_warehouse_sk   = w_warehouse_sk
and cs_ship_mode_sk   = sm_ship_mode_sk
and cs_call_center_sk = cc_call_center_sk
group by
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
order by substr(w_warehouse_name,1,20)
        ,sm_type
        ,cc_name
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk <= 30 ) then 1 else 0 end)  as "30 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 30) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 60) then 1 else 0 end )  as "31-60 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 60) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 90) then 1 else 0 end)  as "61-90 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 90) and
                 (cs_ship_date_sk - cs_sold_date_sk <= 120) then 1 else 0 end)  as "91-120 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk  > 120) then 1 else 0 end)  as ">120 days" 
from
   catalog_sales
  ,warehouse
  ,ship_mode
  ,call_center
  ,date_dim
where
    d_month_seq between 1220 and 1220 + 11
and cs_ship_date_sk   = d_date_sk
and cs_warehouse_sk   = w_warehouse_sk
and cs_ship_mode_sk   = sm_ship_mode_sk
and cs_call_center_sk = cc_call_center_sk
group by
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
order by substr(w_warehouse_name,1,20)
        ,sm_type
        ,cc_name
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk <= 30 ) then 1 else 0 end)  as "30 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 30) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 60) then 1 else 0 end )  as "31-60 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 60) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 90) then 1 else 0 end)  as "61-90 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 90) and
                 (cs_ship_date_sk - cs_sold_date_sk <= 120) then 1 else 0 end)  as "91-120 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk  > 120) then 1 else 0 end)  as ">120 days" 
from
   catalog_sales
  ,warehouse
  ,ship_mode
  ,call_center
  ,date_dim
where
    d_month_seq between 1220 and 1220 + 11
and cs_ship_date_sk   = d_date_sk
and cs_warehouse_sk   = w_warehouse_sk
and cs_ship_mode_sk   = sm_ship_mode_sk
and cs_call_center_sk = cc_call_center_sk
group by
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
order by substr(w_warehouse_name,1,20)
        ,sm_type
        ,cc_name
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk <= 30 ) then 1 else 0 end)  as "30 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 30) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 60) then 1 else 0 end )  as "31-60 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 60) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 90) then 1 else 0 end)  as "61-90 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 90) and
                 (cs_ship_date_sk - cs_sold_date_sk <= 120) then 1 else 0 end)  as "91-120 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk  > 120) then 1 else 0 end)  as ">120 days" 
from
   catalog_sales
  ,warehouse
  ,ship_mode
  ,call_center
  ,date_dim
where
    d_month_seq between 1199 and 1199 + 11
and cs_ship_date_sk   = d_date_sk
and cs_warehouse_sk   = w_warehouse_sk
and cs_ship_mode_sk   = sm_ship_mode_sk
and cs_call_center_sk = cc_call_center_sk
group by
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
order by substr(w_warehouse_name,1,20)
        ,sm_type
        ,cc_name
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk <= 30 ) then 1 else 0 end)  as "30 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 30) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 60) then 1 else 0 end )  as "31-60 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 60) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 90) then 1 else 0 end)  as "61-90 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 90) and
                 (cs_ship_date_sk - cs_sold_date_sk <= 120) then 1 else 0 end)  as "91-120 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk  > 120) then 1 else 0 end)  as ">120 days" 
from
   catalog_sales
  ,warehouse
  ,ship_mode
  ,call_center
  ,date_dim
where
    d_month_seq between 1185 and 1185 + 11
and cs_ship_date_sk   = d_date_sk
and cs_warehouse_sk   = w_warehouse_sk
and cs_ship_mode_sk   = sm_ship_mode_sk
and cs_call_center_sk = cc_call_center_sk
group by
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
order by substr(w_warehouse_name,1,20)
        ,sm_type
        ,cc_name
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk <= 30 ) then 1 else 0 end)  as "30 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 30) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 60) then 1 else 0 end )  as "31-60 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 60) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 90) then 1 else 0 end)  as "61-90 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 90) and
                 (cs_ship_date_sk - cs_sold_date_sk <= 120) then 1 else 0 end)  as "91-120 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk  > 120) then 1 else 0 end)  as ">120 days" 
from
   catalog_sales
  ,warehouse
  ,ship_mode
  ,call_center
  ,date_dim
where
    d_month_seq between 1221 and 1221 + 11
and cs_ship_date_sk   = d_date_sk
and cs_warehouse_sk   = w_warehouse_sk
and cs_ship_mode_sk   = sm_ship_mode_sk
and cs_call_center_sk = cc_call_center_sk
group by
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
order by substr(w_warehouse_name,1,20)
        ,sm_type
        ,cc_name
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk <= 30 ) then 1 else 0 end)  as "30 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 30) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 60) then 1 else 0 end )  as "31-60 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 60) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 90) then 1 else 0 end)  as "61-90 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 90) and
                 (cs_ship_date_sk - cs_sold_date_sk <= 120) then 1 else 0 end)  as "91-120 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk  > 120) then 1 else 0 end)  as ">120 days" 
from
   catalog_sales
  ,warehouse
  ,ship_mode
  ,call_center
  ,date_dim
where
    d_month_seq between 1192 and 1192 + 11
and cs_ship_date_sk   = d_date_sk
and cs_warehouse_sk   = w_warehouse_sk
and cs_ship_mode_sk   = sm_ship_mode_sk
and cs_call_center_sk = cc_call_center_sk
group by
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
order by substr(w_warehouse_name,1,20)
        ,sm_type
        ,cc_name
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk <= 30 ) then 1 else 0 end)  as "30 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 30) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 60) then 1 else 0 end )  as "31-60 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 60) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 90) then 1 else 0 end)  as "61-90 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 90) and
                 (cs_ship_date_sk - cs_sold_date_sk <= 120) then 1 else 0 end)  as "91-120 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk  > 120) then 1 else 0 end)  as ">120 days" 
from
   catalog_sales
  ,warehouse
  ,ship_mode
  ,call_center
  ,date_dim
where
    d_month_seq between 1181 and 1181 + 11
and cs_ship_date_sk   = d_date_sk
and cs_warehouse_sk   = w_warehouse_sk
and cs_ship_mode_sk   = sm_ship_mode_sk
and cs_call_center_sk = cc_call_center_sk
group by
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
order by substr(w_warehouse_name,1,20)
        ,sm_type
        ,cc_name
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk <= 30 ) then 1 else 0 end)  as "30 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 30) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 60) then 1 else 0 end )  as "31-60 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 60) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 90) then 1 else 0 end)  as "61-90 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 90) and
                 (cs_ship_date_sk - cs_sold_date_sk <= 120) then 1 else 0 end)  as "91-120 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk  > 120) then 1 else 0 end)  as ">120 days" 
from
   catalog_sales
  ,warehouse
  ,ship_mode
  ,call_center
  ,date_dim
where
    d_month_seq between 1205 and 1205 + 11
and cs_ship_date_sk   = d_date_sk
and cs_warehouse_sk   = w_warehouse_sk
and cs_ship_mode_sk   = sm_ship_mode_sk
and cs_call_center_sk = cc_call_center_sk
group by
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
order by substr(w_warehouse_name,1,20)
        ,sm_type
        ,cc_name
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk <= 30 ) then 1 else 0 end)  as "30 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 30) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 60) then 1 else 0 end )  as "31-60 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 60) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 90) then 1 else 0 end)  as "61-90 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 90) and
                 (cs_ship_date_sk - cs_sold_date_sk <= 120) then 1 else 0 end)  as "91-120 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk  > 120) then 1 else 0 end)  as ">120 days" 
from
   catalog_sales
  ,warehouse
  ,ship_mode
  ,call_center
  ,date_dim
where
    d_month_seq between 1185 and 1185 + 11
and cs_ship_date_sk   = d_date_sk
and cs_warehouse_sk   = w_warehouse_sk
and cs_ship_mode_sk   = sm_ship_mode_sk
and cs_call_center_sk = cc_call_center_sk
group by
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
order by substr(w_warehouse_name,1,20)
        ,sm_type
        ,cc_name
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk <= 30 ) then 1 else 0 end)  as "30 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 30) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 60) then 1 else 0 end )  as "31-60 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 60) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 90) then 1 else 0 end)  as "61-90 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 90) and
                 (cs_ship_date_sk - cs_sold_date_sk <= 120) then 1 else 0 end)  as "91-120 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk  > 120) then 1 else 0 end)  as ">120 days" 
from
   catalog_sales
  ,warehouse
  ,ship_mode
  ,call_center
  ,date_dim
where
    d_month_seq between 1206 and 1206 + 11
and cs_ship_date_sk   = d_date_sk
and cs_warehouse_sk   = w_warehouse_sk
and cs_ship_mode_sk   = sm_ship_mode_sk
and cs_call_center_sk = cc_call_center_sk
group by
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
order by substr(w_warehouse_name,1,20)
        ,sm_type
        ,cc_name
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk <= 30 ) then 1 else 0 end)  as "30 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 30) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 60) then 1 else 0 end )  as "31-60 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 60) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 90) then 1 else 0 end)  as "61-90 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 90) and
                 (cs_ship_date_sk - cs_sold_date_sk <= 120) then 1 else 0 end)  as "91-120 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk  > 120) then 1 else 0 end)  as ">120 days" 
from
   catalog_sales
  ,warehouse
  ,ship_mode
  ,call_center
  ,date_dim
where
    d_month_seq between 1210 and 1210 + 11
and cs_ship_date_sk   = d_date_sk
and cs_warehouse_sk   = w_warehouse_sk
and cs_ship_mode_sk   = sm_ship_mode_sk
and cs_call_center_sk = cc_call_center_sk
group by
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
order by substr(w_warehouse_name,1,20)
        ,sm_type
        ,cc_name
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk <= 30 ) then 1 else 0 end)  as "30 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 30) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 60) then 1 else 0 end )  as "31-60 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 60) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 90) then 1 else 0 end)  as "61-90 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 90) and
                 (cs_ship_date_sk - cs_sold_date_sk <= 120) then 1 else 0 end)  as "91-120 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk  > 120) then 1 else 0 end)  as ">120 days" 
from
   catalog_sales
  ,warehouse
  ,ship_mode
  ,call_center
  ,date_dim
where
    d_month_seq between 1178 and 1178 + 11
and cs_ship_date_sk   = d_date_sk
and cs_warehouse_sk   = w_warehouse_sk
and cs_ship_mode_sk   = sm_ship_mode_sk
and cs_call_center_sk = cc_call_center_sk
group by
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
order by substr(w_warehouse_name,1,20)
        ,sm_type
        ,cc_name
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk <= 30 ) then 1 else 0 end)  as "30 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 30) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 60) then 1 else 0 end )  as "31-60 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 60) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 90) then 1 else 0 end)  as "61-90 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 90) and
                 (cs_ship_date_sk - cs_sold_date_sk <= 120) then 1 else 0 end)  as "91-120 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk  > 120) then 1 else 0 end)  as ">120 days" 
from
   catalog_sales
  ,warehouse
  ,ship_mode
  ,call_center
  ,date_dim
where
    d_month_seq between 1178 and 1178 + 11
and cs_ship_date_sk   = d_date_sk
and cs_warehouse_sk   = w_warehouse_sk
and cs_ship_mode_sk   = sm_ship_mode_sk
and cs_call_center_sk = cc_call_center_sk
group by
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
order by substr(w_warehouse_name,1,20)
        ,sm_type
        ,cc_name
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk <= 30 ) then 1 else 0 end)  as "30 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 30) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 60) then 1 else 0 end )  as "31-60 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 60) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 90) then 1 else 0 end)  as "61-90 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 90) and
                 (cs_ship_date_sk - cs_sold_date_sk <= 120) then 1 else 0 end)  as "91-120 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk  > 120) then 1 else 0 end)  as ">120 days" 
from
   catalog_sales
  ,warehouse
  ,ship_mode
  ,call_center
  ,date_dim
where
    d_month_seq between 1191 and 1191 + 11
and cs_ship_date_sk   = d_date_sk
and cs_warehouse_sk   = w_warehouse_sk
and cs_ship_mode_sk   = sm_ship_mode_sk
and cs_call_center_sk = cc_call_center_sk
group by
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
order by substr(w_warehouse_name,1,20)
        ,sm_type
        ,cc_name
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk <= 30 ) then 1 else 0 end)  as "30 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 30) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 60) then 1 else 0 end )  as "31-60 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 60) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 90) then 1 else 0 end)  as "61-90 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 90) and
                 (cs_ship_date_sk - cs_sold_date_sk <= 120) then 1 else 0 end)  as "91-120 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk  > 120) then 1 else 0 end)  as ">120 days" 
from
   catalog_sales
  ,warehouse
  ,ship_mode
  ,call_center
  ,date_dim
where
    d_month_seq between 1215 and 1215 + 11
and cs_ship_date_sk   = d_date_sk
and cs_warehouse_sk   = w_warehouse_sk
and cs_ship_mode_sk   = sm_ship_mode_sk
and cs_call_center_sk = cc_call_center_sk
group by
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
order by substr(w_warehouse_name,1,20)
        ,sm_type
        ,cc_name
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk <= 30 ) then 1 else 0 end)  as "30 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 30) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 60) then 1 else 0 end )  as "31-60 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 60) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 90) then 1 else 0 end)  as "61-90 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 90) and
                 (cs_ship_date_sk - cs_sold_date_sk <= 120) then 1 else 0 end)  as "91-120 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk  > 120) then 1 else 0 end)  as ">120 days" 
from
   catalog_sales
  ,warehouse
  ,ship_mode
  ,call_center
  ,date_dim
where
    d_month_seq between 1214 and 1214 + 11
and cs_ship_date_sk   = d_date_sk
and cs_warehouse_sk   = w_warehouse_sk
and cs_ship_mode_sk   = sm_ship_mode_sk
and cs_call_center_sk = cc_call_center_sk
group by
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
order by substr(w_warehouse_name,1,20)
        ,sm_type
        ,cc_name
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk <= 30 ) then 1 else 0 end)  as "30 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 30) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 60) then 1 else 0 end )  as "31-60 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 60) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 90) then 1 else 0 end)  as "61-90 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 90) and
                 (cs_ship_date_sk - cs_sold_date_sk <= 120) then 1 else 0 end)  as "91-120 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk  > 120) then 1 else 0 end)  as ">120 days" 
from
   catalog_sales
  ,warehouse
  ,ship_mode
  ,call_center
  ,date_dim
where
    d_month_seq between 1190 and 1190 + 11
and cs_ship_date_sk   = d_date_sk
and cs_warehouse_sk   = w_warehouse_sk
and cs_ship_mode_sk   = sm_ship_mode_sk
and cs_call_center_sk = cc_call_center_sk
group by
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
order by substr(w_warehouse_name,1,20)
        ,sm_type
        ,cc_name
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk <= 30 ) then 1 else 0 end)  as "30 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 30) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 60) then 1 else 0 end )  as "31-60 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 60) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 90) then 1 else 0 end)  as "61-90 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 90) and
                 (cs_ship_date_sk - cs_sold_date_sk <= 120) then 1 else 0 end)  as "91-120 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk  > 120) then 1 else 0 end)  as ">120 days" 
from
   catalog_sales
  ,warehouse
  ,ship_mode
  ,call_center
  ,date_dim
where
    d_month_seq between 1176 and 1176 + 11
and cs_ship_date_sk   = d_date_sk
and cs_warehouse_sk   = w_warehouse_sk
and cs_ship_mode_sk   = sm_ship_mode_sk
and cs_call_center_sk = cc_call_center_sk
group by
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
order by substr(w_warehouse_name,1,20)
        ,sm_type
        ,cc_name
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk <= 30 ) then 1 else 0 end)  as "30 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 30) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 60) then 1 else 0 end )  as "31-60 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 60) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 90) then 1 else 0 end)  as "61-90 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 90) and
                 (cs_ship_date_sk - cs_sold_date_sk <= 120) then 1 else 0 end)  as "91-120 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk  > 120) then 1 else 0 end)  as ">120 days" 
from
   catalog_sales
  ,warehouse
  ,ship_mode
  ,call_center
  ,date_dim
where
    d_month_seq between 1198 and 1198 + 11
and cs_ship_date_sk   = d_date_sk
and cs_warehouse_sk   = w_warehouse_sk
and cs_ship_mode_sk   = sm_ship_mode_sk
and cs_call_center_sk = cc_call_center_sk
group by
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
order by substr(w_warehouse_name,1,20)
        ,sm_type
        ,cc_name
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk <= 30 ) then 1 else 0 end)  as "30 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 30) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 60) then 1 else 0 end )  as "31-60 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 60) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 90) then 1 else 0 end)  as "61-90 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 90) and
                 (cs_ship_date_sk - cs_sold_date_sk <= 120) then 1 else 0 end)  as "91-120 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk  > 120) then 1 else 0 end)  as ">120 days" 
from
   catalog_sales
  ,warehouse
  ,ship_mode
  ,call_center
  ,date_dim
where
    d_month_seq between 1205 and 1205 + 11
and cs_ship_date_sk   = d_date_sk
and cs_warehouse_sk   = w_warehouse_sk
and cs_ship_mode_sk   = sm_ship_mode_sk
and cs_call_center_sk = cc_call_center_sk
group by
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
order by substr(w_warehouse_name,1,20)
        ,sm_type
        ,cc_name
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk <= 30 ) then 1 else 0 end)  as "30 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 30) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 60) then 1 else 0 end )  as "31-60 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 60) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 90) then 1 else 0 end)  as "61-90 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 90) and
                 (cs_ship_date_sk - cs_sold_date_sk <= 120) then 1 else 0 end)  as "91-120 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk  > 120) then 1 else 0 end)  as ">120 days" 
from
   catalog_sales
  ,warehouse
  ,ship_mode
  ,call_center
  ,date_dim
where
    d_month_seq between 1193 and 1193 + 11
and cs_ship_date_sk   = d_date_sk
and cs_warehouse_sk   = w_warehouse_sk
and cs_ship_mode_sk   = sm_ship_mode_sk
and cs_call_center_sk = cc_call_center_sk
group by
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
order by substr(w_warehouse_name,1,20)
        ,sm_type
        ,cc_name
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk <= 30 ) then 1 else 0 end)  as "30 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 30) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 60) then 1 else 0 end )  as "31-60 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 60) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 90) then 1 else 0 end)  as "61-90 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 90) and
                 (cs_ship_date_sk - cs_sold_date_sk <= 120) then 1 else 0 end)  as "91-120 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk  > 120) then 1 else 0 end)  as ">120 days" 
from
   catalog_sales
  ,warehouse
  ,ship_mode
  ,call_center
  ,date_dim
where
    d_month_seq between 1211 and 1211 + 11
and cs_ship_date_sk   = d_date_sk
and cs_warehouse_sk   = w_warehouse_sk
and cs_ship_mode_sk   = sm_ship_mode_sk
and cs_call_center_sk = cc_call_center_sk
group by
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
order by substr(w_warehouse_name,1,20)
        ,sm_type
        ,cc_name
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk <= 30 ) then 1 else 0 end)  as "30 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 30) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 60) then 1 else 0 end )  as "31-60 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 60) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 90) then 1 else 0 end)  as "61-90 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 90) and
                 (cs_ship_date_sk - cs_sold_date_sk <= 120) then 1 else 0 end)  as "91-120 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk  > 120) then 1 else 0 end)  as ">120 days" 
from
   catalog_sales
  ,warehouse
  ,ship_mode
  ,call_center
  ,date_dim
where
    d_month_seq between 1194 and 1194 + 11
and cs_ship_date_sk   = d_date_sk
and cs_warehouse_sk   = w_warehouse_sk
and cs_ship_mode_sk   = sm_ship_mode_sk
and cs_call_center_sk = cc_call_center_sk
group by
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
order by substr(w_warehouse_name,1,20)
        ,sm_type
        ,cc_name
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk <= 30 ) then 1 else 0 end)  as "30 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 30) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 60) then 1 else 0 end )  as "31-60 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 60) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 90) then 1 else 0 end)  as "61-90 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 90) and
                 (cs_ship_date_sk - cs_sold_date_sk <= 120) then 1 else 0 end)  as "91-120 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk  > 120) then 1 else 0 end)  as ">120 days" 
from
   catalog_sales
  ,warehouse
  ,ship_mode
  ,call_center
  ,date_dim
where
    d_month_seq between 1215 and 1215 + 11
and cs_ship_date_sk   = d_date_sk
and cs_warehouse_sk   = w_warehouse_sk
and cs_ship_mode_sk   = sm_ship_mode_sk
and cs_call_center_sk = cc_call_center_sk
group by
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
order by substr(w_warehouse_name,1,20)
        ,sm_type
        ,cc_name
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk <= 30 ) then 1 else 0 end)  as "30 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 30) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 60) then 1 else 0 end )  as "31-60 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 60) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 90) then 1 else 0 end)  as "61-90 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 90) and
                 (cs_ship_date_sk - cs_sold_date_sk <= 120) then 1 else 0 end)  as "91-120 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk  > 120) then 1 else 0 end)  as ">120 days" 
from
   catalog_sales
  ,warehouse
  ,ship_mode
  ,call_center
  ,date_dim
where
    d_month_seq between 1220 and 1220 + 11
and cs_ship_date_sk   = d_date_sk
and cs_warehouse_sk   = w_warehouse_sk
and cs_ship_mode_sk   = sm_ship_mode_sk
and cs_call_center_sk = cc_call_center_sk
group by
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
order by substr(w_warehouse_name,1,20)
        ,sm_type
        ,cc_name
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk <= 30 ) then 1 else 0 end)  as "30 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 30) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 60) then 1 else 0 end )  as "31-60 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 60) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 90) then 1 else 0 end)  as "61-90 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 90) and
                 (cs_ship_date_sk - cs_sold_date_sk <= 120) then 1 else 0 end)  as "91-120 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk  > 120) then 1 else 0 end)  as ">120 days" 
from
   catalog_sales
  ,warehouse
  ,ship_mode
  ,call_center
  ,date_dim
where
    d_month_seq between 1210 and 1210 + 11
and cs_ship_date_sk   = d_date_sk
and cs_warehouse_sk   = w_warehouse_sk
and cs_ship_mode_sk   = sm_ship_mode_sk
and cs_call_center_sk = cc_call_center_sk
group by
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
order by substr(w_warehouse_name,1,20)
        ,sm_type
        ,cc_name
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk <= 30 ) then 1 else 0 end)  as "30 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 30) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 60) then 1 else 0 end )  as "31-60 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 60) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 90) then 1 else 0 end)  as "61-90 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 90) and
                 (cs_ship_date_sk - cs_sold_date_sk <= 120) then 1 else 0 end)  as "91-120 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk  > 120) then 1 else 0 end)  as ">120 days" 
from
   catalog_sales
  ,warehouse
  ,ship_mode
  ,call_center
  ,date_dim
where
    d_month_seq between 1217 and 1217 + 11
and cs_ship_date_sk   = d_date_sk
and cs_warehouse_sk   = w_warehouse_sk
and cs_ship_mode_sk   = sm_ship_mode_sk
and cs_call_center_sk = cc_call_center_sk
group by
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
order by substr(w_warehouse_name,1,20)
        ,sm_type
        ,cc_name
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk <= 30 ) then 1 else 0 end)  as "30 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 30) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 60) then 1 else 0 end )  as "31-60 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 60) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 90) then 1 else 0 end)  as "61-90 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 90) and
                 (cs_ship_date_sk - cs_sold_date_sk <= 120) then 1 else 0 end)  as "91-120 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk  > 120) then 1 else 0 end)  as ">120 days" 
from
   catalog_sales
  ,warehouse
  ,ship_mode
  ,call_center
  ,date_dim
where
    d_month_seq between 1178 and 1178 + 11
and cs_ship_date_sk   = d_date_sk
and cs_warehouse_sk   = w_warehouse_sk
and cs_ship_mode_sk   = sm_ship_mode_sk
and cs_call_center_sk = cc_call_center_sk
group by
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
order by substr(w_warehouse_name,1,20)
        ,sm_type
        ,cc_name
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk <= 30 ) then 1 else 0 end)  as "30 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 30) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 60) then 1 else 0 end )  as "31-60 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 60) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 90) then 1 else 0 end)  as "61-90 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 90) and
                 (cs_ship_date_sk - cs_sold_date_sk <= 120) then 1 else 0 end)  as "91-120 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk  > 120) then 1 else 0 end)  as ">120 days" 
from
   catalog_sales
  ,warehouse
  ,ship_mode
  ,call_center
  ,date_dim
where
    d_month_seq between 1203 and 1203 + 11
and cs_ship_date_sk   = d_date_sk
and cs_warehouse_sk   = w_warehouse_sk
and cs_ship_mode_sk   = sm_ship_mode_sk
and cs_call_center_sk = cc_call_center_sk
group by
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
order by substr(w_warehouse_name,1,20)
        ,sm_type
        ,cc_name
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk <= 30 ) then 1 else 0 end)  as "30 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 30) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 60) then 1 else 0 end )  as "31-60 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 60) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 90) then 1 else 0 end)  as "61-90 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 90) and
                 (cs_ship_date_sk - cs_sold_date_sk <= 120) then 1 else 0 end)  as "91-120 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk  > 120) then 1 else 0 end)  as ">120 days" 
from
   catalog_sales
  ,warehouse
  ,ship_mode
  ,call_center
  ,date_dim
where
    d_month_seq between 1199 and 1199 + 11
and cs_ship_date_sk   = d_date_sk
and cs_warehouse_sk   = w_warehouse_sk
and cs_ship_mode_sk   = sm_ship_mode_sk
and cs_call_center_sk = cc_call_center_sk
group by
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
order by substr(w_warehouse_name,1,20)
        ,sm_type
        ,cc_name
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk <= 30 ) then 1 else 0 end)  as "30 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 30) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 60) then 1 else 0 end )  as "31-60 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 60) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 90) then 1 else 0 end)  as "61-90 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 90) and
                 (cs_ship_date_sk - cs_sold_date_sk <= 120) then 1 else 0 end)  as "91-120 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk  > 120) then 1 else 0 end)  as ">120 days" 
from
   catalog_sales
  ,warehouse
  ,ship_mode
  ,call_center
  ,date_dim
where
    d_month_seq between 1202 and 1202 + 11
and cs_ship_date_sk   = d_date_sk
and cs_warehouse_sk   = w_warehouse_sk
and cs_ship_mode_sk   = sm_ship_mode_sk
and cs_call_center_sk = cc_call_center_sk
group by
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
order by substr(w_warehouse_name,1,20)
        ,sm_type
        ,cc_name
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk <= 30 ) then 1 else 0 end)  as "30 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 30) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 60) then 1 else 0 end )  as "31-60 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 60) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 90) then 1 else 0 end)  as "61-90 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 90) and
                 (cs_ship_date_sk - cs_sold_date_sk <= 120) then 1 else 0 end)  as "91-120 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk  > 120) then 1 else 0 end)  as ">120 days" 
from
   catalog_sales
  ,warehouse
  ,ship_mode
  ,call_center
  ,date_dim
where
    d_month_seq between 1181 and 1181 + 11
and cs_ship_date_sk   = d_date_sk
and cs_warehouse_sk   = w_warehouse_sk
and cs_ship_mode_sk   = sm_ship_mode_sk
and cs_call_center_sk = cc_call_center_sk
group by
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
order by substr(w_warehouse_name,1,20)
        ,sm_type
        ,cc_name
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk <= 30 ) then 1 else 0 end)  as "30 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 30) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 60) then 1 else 0 end )  as "31-60 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 60) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 90) then 1 else 0 end)  as "61-90 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 90) and
                 (cs_ship_date_sk - cs_sold_date_sk <= 120) then 1 else 0 end)  as "91-120 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk  > 120) then 1 else 0 end)  as ">120 days" 
from
   catalog_sales
  ,warehouse
  ,ship_mode
  ,call_center
  ,date_dim
where
    d_month_seq between 1212 and 1212 + 11
and cs_ship_date_sk   = d_date_sk
and cs_warehouse_sk   = w_warehouse_sk
and cs_ship_mode_sk   = sm_ship_mode_sk
and cs_call_center_sk = cc_call_center_sk
group by
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
order by substr(w_warehouse_name,1,20)
        ,sm_type
        ,cc_name
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk <= 30 ) then 1 else 0 end)  as "30 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 30) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 60) then 1 else 0 end )  as "31-60 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 60) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 90) then 1 else 0 end)  as "61-90 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 90) and
                 (cs_ship_date_sk - cs_sold_date_sk <= 120) then 1 else 0 end)  as "91-120 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk  > 120) then 1 else 0 end)  as ">120 days" 
from
   catalog_sales
  ,warehouse
  ,ship_mode
  ,call_center
  ,date_dim
where
    d_month_seq between 1178 and 1178 + 11
and cs_ship_date_sk   = d_date_sk
and cs_warehouse_sk   = w_warehouse_sk
and cs_ship_mode_sk   = sm_ship_mode_sk
and cs_call_center_sk = cc_call_center_sk
group by
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
order by substr(w_warehouse_name,1,20)
        ,sm_type
        ,cc_name
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk <= 30 ) then 1 else 0 end)  as "30 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 30) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 60) then 1 else 0 end )  as "31-60 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 60) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 90) then 1 else 0 end)  as "61-90 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 90) and
                 (cs_ship_date_sk - cs_sold_date_sk <= 120) then 1 else 0 end)  as "91-120 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk  > 120) then 1 else 0 end)  as ">120 days" 
from
   catalog_sales
  ,warehouse
  ,ship_mode
  ,call_center
  ,date_dim
where
    d_month_seq between 1199 and 1199 + 11
and cs_ship_date_sk   = d_date_sk
and cs_warehouse_sk   = w_warehouse_sk
and cs_ship_mode_sk   = sm_ship_mode_sk
and cs_call_center_sk = cc_call_center_sk
group by
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
order by substr(w_warehouse_name,1,20)
        ,sm_type
        ,cc_name
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk <= 30 ) then 1 else 0 end)  as "30 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 30) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 60) then 1 else 0 end )  as "31-60 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 60) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 90) then 1 else 0 end)  as "61-90 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 90) and
                 (cs_ship_date_sk - cs_sold_date_sk <= 120) then 1 else 0 end)  as "91-120 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk  > 120) then 1 else 0 end)  as ">120 days" 
from
   catalog_sales
  ,warehouse
  ,ship_mode
  ,call_center
  ,date_dim
where
    d_month_seq between 1212 and 1212 + 11
and cs_ship_date_sk   = d_date_sk
and cs_warehouse_sk   = w_warehouse_sk
and cs_ship_mode_sk   = sm_ship_mode_sk
and cs_call_center_sk = cc_call_center_sk
group by
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
order by substr(w_warehouse_name,1,20)
        ,sm_type
        ,cc_name
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk <= 30 ) then 1 else 0 end)  as "30 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 30) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 60) then 1 else 0 end )  as "31-60 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 60) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 90) then 1 else 0 end)  as "61-90 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 90) and
                 (cs_ship_date_sk - cs_sold_date_sk <= 120) then 1 else 0 end)  as "91-120 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk  > 120) then 1 else 0 end)  as ">120 days" 
from
   catalog_sales
  ,warehouse
  ,ship_mode
  ,call_center
  ,date_dim
where
    d_month_seq between 1184 and 1184 + 11
and cs_ship_date_sk   = d_date_sk
and cs_warehouse_sk   = w_warehouse_sk
and cs_ship_mode_sk   = sm_ship_mode_sk
and cs_call_center_sk = cc_call_center_sk
group by
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
order by substr(w_warehouse_name,1,20)
        ,sm_type
        ,cc_name
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk <= 30 ) then 1 else 0 end)  as "30 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 30) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 60) then 1 else 0 end )  as "31-60 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 60) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 90) then 1 else 0 end)  as "61-90 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 90) and
                 (cs_ship_date_sk - cs_sold_date_sk <= 120) then 1 else 0 end)  as "91-120 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk  > 120) then 1 else 0 end)  as ">120 days" 
from
   catalog_sales
  ,warehouse
  ,ship_mode
  ,call_center
  ,date_dim
where
    d_month_seq between 1218 and 1218 + 11
and cs_ship_date_sk   = d_date_sk
and cs_warehouse_sk   = w_warehouse_sk
and cs_ship_mode_sk   = sm_ship_mode_sk
and cs_call_center_sk = cc_call_center_sk
group by
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
order by substr(w_warehouse_name,1,20)
        ,sm_type
        ,cc_name
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk <= 30 ) then 1 else 0 end)  as "30 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 30) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 60) then 1 else 0 end )  as "31-60 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 60) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 90) then 1 else 0 end)  as "61-90 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 90) and
                 (cs_ship_date_sk - cs_sold_date_sk <= 120) then 1 else 0 end)  as "91-120 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk  > 120) then 1 else 0 end)  as ">120 days" 
from
   catalog_sales
  ,warehouse
  ,ship_mode
  ,call_center
  ,date_dim
where
    d_month_seq between 1198 and 1198 + 11
and cs_ship_date_sk   = d_date_sk
and cs_warehouse_sk   = w_warehouse_sk
and cs_ship_mode_sk   = sm_ship_mode_sk
and cs_call_center_sk = cc_call_center_sk
group by
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
order by substr(w_warehouse_name,1,20)
        ,sm_type
        ,cc_name
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk <= 30 ) then 1 else 0 end)  as "30 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 30) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 60) then 1 else 0 end )  as "31-60 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 60) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 90) then 1 else 0 end)  as "61-90 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 90) and
                 (cs_ship_date_sk - cs_sold_date_sk <= 120) then 1 else 0 end)  as "91-120 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk  > 120) then 1 else 0 end)  as ">120 days" 
from
   catalog_sales
  ,warehouse
  ,ship_mode
  ,call_center
  ,date_dim
where
    d_month_seq between 1183 and 1183 + 11
and cs_ship_date_sk   = d_date_sk
and cs_warehouse_sk   = w_warehouse_sk
and cs_ship_mode_sk   = sm_ship_mode_sk
and cs_call_center_sk = cc_call_center_sk
group by
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
order by substr(w_warehouse_name,1,20)
        ,sm_type
        ,cc_name
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk <= 30 ) then 1 else 0 end)  as "30 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 30) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 60) then 1 else 0 end )  as "31-60 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 60) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 90) then 1 else 0 end)  as "61-90 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 90) and
                 (cs_ship_date_sk - cs_sold_date_sk <= 120) then 1 else 0 end)  as "91-120 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk  > 120) then 1 else 0 end)  as ">120 days" 
from
   catalog_sales
  ,warehouse
  ,ship_mode
  ,call_center
  ,date_dim
where
    d_month_seq between 1178 and 1178 + 11
and cs_ship_date_sk   = d_date_sk
and cs_warehouse_sk   = w_warehouse_sk
and cs_ship_mode_sk   = sm_ship_mode_sk
and cs_call_center_sk = cc_call_center_sk
group by
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
order by substr(w_warehouse_name,1,20)
        ,sm_type
        ,cc_name
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk <= 30 ) then 1 else 0 end)  as "30 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 30) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 60) then 1 else 0 end )  as "31-60 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 60) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 90) then 1 else 0 end)  as "61-90 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 90) and
                 (cs_ship_date_sk - cs_sold_date_sk <= 120) then 1 else 0 end)  as "91-120 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk  > 120) then 1 else 0 end)  as ">120 days" 
from
   catalog_sales
  ,warehouse
  ,ship_mode
  ,call_center
  ,date_dim
where
    d_month_seq between 1193 and 1193 + 11
and cs_ship_date_sk   = d_date_sk
and cs_warehouse_sk   = w_warehouse_sk
and cs_ship_mode_sk   = sm_ship_mode_sk
and cs_call_center_sk = cc_call_center_sk
group by
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
order by substr(w_warehouse_name,1,20)
        ,sm_type
        ,cc_name
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk <= 30 ) then 1 else 0 end)  as "30 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 30) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 60) then 1 else 0 end )  as "31-60 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 60) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 90) then 1 else 0 end)  as "61-90 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 90) and
                 (cs_ship_date_sk - cs_sold_date_sk <= 120) then 1 else 0 end)  as "91-120 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk  > 120) then 1 else 0 end)  as ">120 days" 
from
   catalog_sales
  ,warehouse
  ,ship_mode
  ,call_center
  ,date_dim
where
    d_month_seq between 1199 and 1199 + 11
and cs_ship_date_sk   = d_date_sk
and cs_warehouse_sk   = w_warehouse_sk
and cs_ship_mode_sk   = sm_ship_mode_sk
and cs_call_center_sk = cc_call_center_sk
group by
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
order by substr(w_warehouse_name,1,20)
        ,sm_type
        ,cc_name
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk <= 30 ) then 1 else 0 end)  as "30 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 30) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 60) then 1 else 0 end )  as "31-60 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 60) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 90) then 1 else 0 end)  as "61-90 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 90) and
                 (cs_ship_date_sk - cs_sold_date_sk <= 120) then 1 else 0 end)  as "91-120 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk  > 120) then 1 else 0 end)  as ">120 days" 
from
   catalog_sales
  ,warehouse
  ,ship_mode
  ,call_center
  ,date_dim
where
    d_month_seq between 1217 and 1217 + 11
and cs_ship_date_sk   = d_date_sk
and cs_warehouse_sk   = w_warehouse_sk
and cs_ship_mode_sk   = sm_ship_mode_sk
and cs_call_center_sk = cc_call_center_sk
group by
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
order by substr(w_warehouse_name,1,20)
        ,sm_type
        ,cc_name
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk <= 30 ) then 1 else 0 end)  as "30 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 30) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 60) then 1 else 0 end )  as "31-60 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 60) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 90) then 1 else 0 end)  as "61-90 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 90) and
                 (cs_ship_date_sk - cs_sold_date_sk <= 120) then 1 else 0 end)  as "91-120 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk  > 120) then 1 else 0 end)  as ">120 days" 
from
   catalog_sales
  ,warehouse
  ,ship_mode
  ,call_center
  ,date_dim
where
    d_month_seq between 1201 and 1201 + 11
and cs_ship_date_sk   = d_date_sk
and cs_warehouse_sk   = w_warehouse_sk
and cs_ship_mode_sk   = sm_ship_mode_sk
and cs_call_center_sk = cc_call_center_sk
group by
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
order by substr(w_warehouse_name,1,20)
        ,sm_type
        ,cc_name
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk <= 30 ) then 1 else 0 end)  as "30 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 30) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 60) then 1 else 0 end )  as "31-60 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 60) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 90) then 1 else 0 end)  as "61-90 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 90) and
                 (cs_ship_date_sk - cs_sold_date_sk <= 120) then 1 else 0 end)  as "91-120 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk  > 120) then 1 else 0 end)  as ">120 days" 
from
   catalog_sales
  ,warehouse
  ,ship_mode
  ,call_center
  ,date_dim
where
    d_month_seq between 1209 and 1209 + 11
and cs_ship_date_sk   = d_date_sk
and cs_warehouse_sk   = w_warehouse_sk
and cs_ship_mode_sk   = sm_ship_mode_sk
and cs_call_center_sk = cc_call_center_sk
group by
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
order by substr(w_warehouse_name,1,20)
        ,sm_type
        ,cc_name
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk <= 30 ) then 1 else 0 end)  as "30 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 30) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 60) then 1 else 0 end )  as "31-60 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 60) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 90) then 1 else 0 end)  as "61-90 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 90) and
                 (cs_ship_date_sk - cs_sold_date_sk <= 120) then 1 else 0 end)  as "91-120 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk  > 120) then 1 else 0 end)  as ">120 days" 
from
   catalog_sales
  ,warehouse
  ,ship_mode
  ,call_center
  ,date_dim
where
    d_month_seq between 1203 and 1203 + 11
and cs_ship_date_sk   = d_date_sk
and cs_warehouse_sk   = w_warehouse_sk
and cs_ship_mode_sk   = sm_ship_mode_sk
and cs_call_center_sk = cc_call_center_sk
group by
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
order by substr(w_warehouse_name,1,20)
        ,sm_type
        ,cc_name
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk <= 30 ) then 1 else 0 end)  as "30 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 30) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 60) then 1 else 0 end )  as "31-60 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 60) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 90) then 1 else 0 end)  as "61-90 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 90) and
                 (cs_ship_date_sk - cs_sold_date_sk <= 120) then 1 else 0 end)  as "91-120 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk  > 120) then 1 else 0 end)  as ">120 days" 
from
   catalog_sales
  ,warehouse
  ,ship_mode
  ,call_center
  ,date_dim
where
    d_month_seq between 1176 and 1176 + 11
and cs_ship_date_sk   = d_date_sk
and cs_warehouse_sk   = w_warehouse_sk
and cs_ship_mode_sk   = sm_ship_mode_sk
and cs_call_center_sk = cc_call_center_sk
group by
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
order by substr(w_warehouse_name,1,20)
        ,sm_type
        ,cc_name
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk <= 30 ) then 1 else 0 end)  as "30 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 30) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 60) then 1 else 0 end )  as "31-60 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 60) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 90) then 1 else 0 end)  as "61-90 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 90) and
                 (cs_ship_date_sk - cs_sold_date_sk <= 120) then 1 else 0 end)  as "91-120 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk  > 120) then 1 else 0 end)  as ">120 days" 
from
   catalog_sales
  ,warehouse
  ,ship_mode
  ,call_center
  ,date_dim
where
    d_month_seq between 1217 and 1217 + 11
and cs_ship_date_sk   = d_date_sk
and cs_warehouse_sk   = w_warehouse_sk
and cs_ship_mode_sk   = sm_ship_mode_sk
and cs_call_center_sk = cc_call_center_sk
group by
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
order by substr(w_warehouse_name,1,20)
        ,sm_type
        ,cc_name
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk <= 30 ) then 1 else 0 end)  as "30 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 30) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 60) then 1 else 0 end )  as "31-60 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 60) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 90) then 1 else 0 end)  as "61-90 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 90) and
                 (cs_ship_date_sk - cs_sold_date_sk <= 120) then 1 else 0 end)  as "91-120 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk  > 120) then 1 else 0 end)  as ">120 days" 
from
   catalog_sales
  ,warehouse
  ,ship_mode
  ,call_center
  ,date_dim
where
    d_month_seq between 1199 and 1199 + 11
and cs_ship_date_sk   = d_date_sk
and cs_warehouse_sk   = w_warehouse_sk
and cs_ship_mode_sk   = sm_ship_mode_sk
and cs_call_center_sk = cc_call_center_sk
group by
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
order by substr(w_warehouse_name,1,20)
        ,sm_type
        ,cc_name
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk <= 30 ) then 1 else 0 end)  as "30 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 30) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 60) then 1 else 0 end )  as "31-60 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 60) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 90) then 1 else 0 end)  as "61-90 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 90) and
                 (cs_ship_date_sk - cs_sold_date_sk <= 120) then 1 else 0 end)  as "91-120 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk  > 120) then 1 else 0 end)  as ">120 days" 
from
   catalog_sales
  ,warehouse
  ,ship_mode
  ,call_center
  ,date_dim
where
    d_month_seq between 1196 and 1196 + 11
and cs_ship_date_sk   = d_date_sk
and cs_warehouse_sk   = w_warehouse_sk
and cs_ship_mode_sk   = sm_ship_mode_sk
and cs_call_center_sk = cc_call_center_sk
group by
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
order by substr(w_warehouse_name,1,20)
        ,sm_type
        ,cc_name
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk <= 30 ) then 1 else 0 end)  as "30 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 30) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 60) then 1 else 0 end )  as "31-60 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 60) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 90) then 1 else 0 end)  as "61-90 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 90) and
                 (cs_ship_date_sk - cs_sold_date_sk <= 120) then 1 else 0 end)  as "91-120 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk  > 120) then 1 else 0 end)  as ">120 days" 
from
   catalog_sales
  ,warehouse
  ,ship_mode
  ,call_center
  ,date_dim
where
    d_month_seq between 1223 and 1223 + 11
and cs_ship_date_sk   = d_date_sk
and cs_warehouse_sk   = w_warehouse_sk
and cs_ship_mode_sk   = sm_ship_mode_sk
and cs_call_center_sk = cc_call_center_sk
group by
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
order by substr(w_warehouse_name,1,20)
        ,sm_type
        ,cc_name
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk <= 30 ) then 1 else 0 end)  as "30 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 30) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 60) then 1 else 0 end )  as "31-60 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 60) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 90) then 1 else 0 end)  as "61-90 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 90) and
                 (cs_ship_date_sk - cs_sold_date_sk <= 120) then 1 else 0 end)  as "91-120 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk  > 120) then 1 else 0 end)  as ">120 days" 
from
   catalog_sales
  ,warehouse
  ,ship_mode
  ,call_center
  ,date_dim
where
    d_month_seq between 1202 and 1202 + 11
and cs_ship_date_sk   = d_date_sk
and cs_warehouse_sk   = w_warehouse_sk
and cs_ship_mode_sk   = sm_ship_mode_sk
and cs_call_center_sk = cc_call_center_sk
group by
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
order by substr(w_warehouse_name,1,20)
        ,sm_type
        ,cc_name
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk <= 30 ) then 1 else 0 end)  as "30 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 30) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 60) then 1 else 0 end )  as "31-60 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 60) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 90) then 1 else 0 end)  as "61-90 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 90) and
                 (cs_ship_date_sk - cs_sold_date_sk <= 120) then 1 else 0 end)  as "91-120 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk  > 120) then 1 else 0 end)  as ">120 days" 
from
   catalog_sales
  ,warehouse
  ,ship_mode
  ,call_center
  ,date_dim
where
    d_month_seq between 1209 and 1209 + 11
and cs_ship_date_sk   = d_date_sk
and cs_warehouse_sk   = w_warehouse_sk
and cs_ship_mode_sk   = sm_ship_mode_sk
and cs_call_center_sk = cc_call_center_sk
group by
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
order by substr(w_warehouse_name,1,20)
        ,sm_type
        ,cc_name
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk <= 30 ) then 1 else 0 end)  as "30 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 30) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 60) then 1 else 0 end )  as "31-60 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 60) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 90) then 1 else 0 end)  as "61-90 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 90) and
                 (cs_ship_date_sk - cs_sold_date_sk <= 120) then 1 else 0 end)  as "91-120 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk  > 120) then 1 else 0 end)  as ">120 days" 
from
   catalog_sales
  ,warehouse
  ,ship_mode
  ,call_center
  ,date_dim
where
    d_month_seq between 1207 and 1207 + 11
and cs_ship_date_sk   = d_date_sk
and cs_warehouse_sk   = w_warehouse_sk
and cs_ship_mode_sk   = sm_ship_mode_sk
and cs_call_center_sk = cc_call_center_sk
group by
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
order by substr(w_warehouse_name,1,20)
        ,sm_type
        ,cc_name
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk <= 30 ) then 1 else 0 end)  as "30 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 30) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 60) then 1 else 0 end )  as "31-60 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 60) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 90) then 1 else 0 end)  as "61-90 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 90) and
                 (cs_ship_date_sk - cs_sold_date_sk <= 120) then 1 else 0 end)  as "91-120 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk  > 120) then 1 else 0 end)  as ">120 days" 
from
   catalog_sales
  ,warehouse
  ,ship_mode
  ,call_center
  ,date_dim
where
    d_month_seq between 1195 and 1195 + 11
and cs_ship_date_sk   = d_date_sk
and cs_warehouse_sk   = w_warehouse_sk
and cs_ship_mode_sk   = sm_ship_mode_sk
and cs_call_center_sk = cc_call_center_sk
group by
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
order by substr(w_warehouse_name,1,20)
        ,sm_type
        ,cc_name
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk <= 30 ) then 1 else 0 end)  as "30 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 30) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 60) then 1 else 0 end )  as "31-60 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 60) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 90) then 1 else 0 end)  as "61-90 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 90) and
                 (cs_ship_date_sk - cs_sold_date_sk <= 120) then 1 else 0 end)  as "91-120 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk  > 120) then 1 else 0 end)  as ">120 days" 
from
   catalog_sales
  ,warehouse
  ,ship_mode
  ,call_center
  ,date_dim
where
    d_month_seq between 1190 and 1190 + 11
and cs_ship_date_sk   = d_date_sk
and cs_warehouse_sk   = w_warehouse_sk
and cs_ship_mode_sk   = sm_ship_mode_sk
and cs_call_center_sk = cc_call_center_sk
group by
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
order by substr(w_warehouse_name,1,20)
        ,sm_type
        ,cc_name
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk <= 30 ) then 1 else 0 end)  as "30 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 30) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 60) then 1 else 0 end )  as "31-60 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 60) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 90) then 1 else 0 end)  as "61-90 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 90) and
                 (cs_ship_date_sk - cs_sold_date_sk <= 120) then 1 else 0 end)  as "91-120 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk  > 120) then 1 else 0 end)  as ">120 days" 
from
   catalog_sales
  ,warehouse
  ,ship_mode
  ,call_center
  ,date_dim
where
    d_month_seq between 1223 and 1223 + 11
and cs_ship_date_sk   = d_date_sk
and cs_warehouse_sk   = w_warehouse_sk
and cs_ship_mode_sk   = sm_ship_mode_sk
and cs_call_center_sk = cc_call_center_sk
group by
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
order by substr(w_warehouse_name,1,20)
        ,sm_type
        ,cc_name
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk <= 30 ) then 1 else 0 end)  as "30 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 30) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 60) then 1 else 0 end )  as "31-60 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 60) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 90) then 1 else 0 end)  as "61-90 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 90) and
                 (cs_ship_date_sk - cs_sold_date_sk <= 120) then 1 else 0 end)  as "91-120 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk  > 120) then 1 else 0 end)  as ">120 days" 
from
   catalog_sales
  ,warehouse
  ,ship_mode
  ,call_center
  ,date_dim
where
    d_month_seq between 1223 and 1223 + 11
and cs_ship_date_sk   = d_date_sk
and cs_warehouse_sk   = w_warehouse_sk
and cs_ship_mode_sk   = sm_ship_mode_sk
and cs_call_center_sk = cc_call_center_sk
group by
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
order by substr(w_warehouse_name,1,20)
        ,sm_type
        ,cc_name
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk <= 30 ) then 1 else 0 end)  as "30 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 30) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 60) then 1 else 0 end )  as "31-60 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 60) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 90) then 1 else 0 end)  as "61-90 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 90) and
                 (cs_ship_date_sk - cs_sold_date_sk <= 120) then 1 else 0 end)  as "91-120 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk  > 120) then 1 else 0 end)  as ">120 days" 
from
   catalog_sales
  ,warehouse
  ,ship_mode
  ,call_center
  ,date_dim
where
    d_month_seq between 1183 and 1183 + 11
and cs_ship_date_sk   = d_date_sk
and cs_warehouse_sk   = w_warehouse_sk
and cs_ship_mode_sk   = sm_ship_mode_sk
and cs_call_center_sk = cc_call_center_sk
group by
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
order by substr(w_warehouse_name,1,20)
        ,sm_type
        ,cc_name
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk <= 30 ) then 1 else 0 end)  as "30 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 30) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 60) then 1 else 0 end )  as "31-60 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 60) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 90) then 1 else 0 end)  as "61-90 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 90) and
                 (cs_ship_date_sk - cs_sold_date_sk <= 120) then 1 else 0 end)  as "91-120 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk  > 120) then 1 else 0 end)  as ">120 days" 
from
   catalog_sales
  ,warehouse
  ,ship_mode
  ,call_center
  ,date_dim
where
    d_month_seq between 1216 and 1216 + 11
and cs_ship_date_sk   = d_date_sk
and cs_warehouse_sk   = w_warehouse_sk
and cs_ship_mode_sk   = sm_ship_mode_sk
and cs_call_center_sk = cc_call_center_sk
group by
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
order by substr(w_warehouse_name,1,20)
        ,sm_type
        ,cc_name
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk <= 30 ) then 1 else 0 end)  as "30 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 30) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 60) then 1 else 0 end )  as "31-60 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 60) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 90) then 1 else 0 end)  as "61-90 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 90) and
                 (cs_ship_date_sk - cs_sold_date_sk <= 120) then 1 else 0 end)  as "91-120 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk  > 120) then 1 else 0 end)  as ">120 days" 
from
   catalog_sales
  ,warehouse
  ,ship_mode
  ,call_center
  ,date_dim
where
    d_month_seq between 1207 and 1207 + 11
and cs_ship_date_sk   = d_date_sk
and cs_warehouse_sk   = w_warehouse_sk
and cs_ship_mode_sk   = sm_ship_mode_sk
and cs_call_center_sk = cc_call_center_sk
group by
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
order by substr(w_warehouse_name,1,20)
        ,sm_type
        ,cc_name
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk <= 30 ) then 1 else 0 end)  as "30 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 30) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 60) then 1 else 0 end )  as "31-60 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 60) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 90) then 1 else 0 end)  as "61-90 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 90) and
                 (cs_ship_date_sk - cs_sold_date_sk <= 120) then 1 else 0 end)  as "91-120 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk  > 120) then 1 else 0 end)  as ">120 days" 
from
   catalog_sales
  ,warehouse
  ,ship_mode
  ,call_center
  ,date_dim
where
    d_month_seq between 1179 and 1179 + 11
and cs_ship_date_sk   = d_date_sk
and cs_warehouse_sk   = w_warehouse_sk
and cs_ship_mode_sk   = sm_ship_mode_sk
and cs_call_center_sk = cc_call_center_sk
group by
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
order by substr(w_warehouse_name,1,20)
        ,sm_type
        ,cc_name
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk <= 30 ) then 1 else 0 end)  as "30 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 30) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 60) then 1 else 0 end )  as "31-60 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 60) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 90) then 1 else 0 end)  as "61-90 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 90) and
                 (cs_ship_date_sk - cs_sold_date_sk <= 120) then 1 else 0 end)  as "91-120 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk  > 120) then 1 else 0 end)  as ">120 days" 
from
   catalog_sales
  ,warehouse
  ,ship_mode
  ,call_center
  ,date_dim
where
    d_month_seq between 1194 and 1194 + 11
and cs_ship_date_sk   = d_date_sk
and cs_warehouse_sk   = w_warehouse_sk
and cs_ship_mode_sk   = sm_ship_mode_sk
and cs_call_center_sk = cc_call_center_sk
group by
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
order by substr(w_warehouse_name,1,20)
        ,sm_type
        ,cc_name
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk <= 30 ) then 1 else 0 end)  as "30 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 30) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 60) then 1 else 0 end )  as "31-60 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 60) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 90) then 1 else 0 end)  as "61-90 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 90) and
                 (cs_ship_date_sk - cs_sold_date_sk <= 120) then 1 else 0 end)  as "91-120 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk  > 120) then 1 else 0 end)  as ">120 days" 
from
   catalog_sales
  ,warehouse
  ,ship_mode
  ,call_center
  ,date_dim
where
    d_month_seq between 1213 and 1213 + 11
and cs_ship_date_sk   = d_date_sk
and cs_warehouse_sk   = w_warehouse_sk
and cs_ship_mode_sk   = sm_ship_mode_sk
and cs_call_center_sk = cc_call_center_sk
group by
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
order by substr(w_warehouse_name,1,20)
        ,sm_type
        ,cc_name
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk <= 30 ) then 1 else 0 end)  as "30 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 30) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 60) then 1 else 0 end )  as "31-60 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 60) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 90) then 1 else 0 end)  as "61-90 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 90) and
                 (cs_ship_date_sk - cs_sold_date_sk <= 120) then 1 else 0 end)  as "91-120 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk  > 120) then 1 else 0 end)  as ">120 days" 
from
   catalog_sales
  ,warehouse
  ,ship_mode
  ,call_center
  ,date_dim
where
    d_month_seq between 1221 and 1221 + 11
and cs_ship_date_sk   = d_date_sk
and cs_warehouse_sk   = w_warehouse_sk
and cs_ship_mode_sk   = sm_ship_mode_sk
and cs_call_center_sk = cc_call_center_sk
group by
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
order by substr(w_warehouse_name,1,20)
        ,sm_type
        ,cc_name
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk <= 30 ) then 1 else 0 end)  as "30 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 30) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 60) then 1 else 0 end )  as "31-60 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 60) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 90) then 1 else 0 end)  as "61-90 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 90) and
                 (cs_ship_date_sk - cs_sold_date_sk <= 120) then 1 else 0 end)  as "91-120 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk  > 120) then 1 else 0 end)  as ">120 days" 
from
   catalog_sales
  ,warehouse
  ,ship_mode
  ,call_center
  ,date_dim
where
    d_month_seq between 1194 and 1194 + 11
and cs_ship_date_sk   = d_date_sk
and cs_warehouse_sk   = w_warehouse_sk
and cs_ship_mode_sk   = sm_ship_mode_sk
and cs_call_center_sk = cc_call_center_sk
group by
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
order by substr(w_warehouse_name,1,20)
        ,sm_type
        ,cc_name
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk <= 30 ) then 1 else 0 end)  as "30 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 30) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 60) then 1 else 0 end )  as "31-60 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 60) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 90) then 1 else 0 end)  as "61-90 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 90) and
                 (cs_ship_date_sk - cs_sold_date_sk <= 120) then 1 else 0 end)  as "91-120 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk  > 120) then 1 else 0 end)  as ">120 days" 
from
   catalog_sales
  ,warehouse
  ,ship_mode
  ,call_center
  ,date_dim
where
    d_month_seq between 1224 and 1224 + 11
and cs_ship_date_sk   = d_date_sk
and cs_warehouse_sk   = w_warehouse_sk
and cs_ship_mode_sk   = sm_ship_mode_sk
and cs_call_center_sk = cc_call_center_sk
group by
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
order by substr(w_warehouse_name,1,20)
        ,sm_type
        ,cc_name
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk <= 30 ) then 1 else 0 end)  as "30 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 30) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 60) then 1 else 0 end )  as "31-60 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 60) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 90) then 1 else 0 end)  as "61-90 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 90) and
                 (cs_ship_date_sk - cs_sold_date_sk <= 120) then 1 else 0 end)  as "91-120 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk  > 120) then 1 else 0 end)  as ">120 days" 
from
   catalog_sales
  ,warehouse
  ,ship_mode
  ,call_center
  ,date_dim
where
    d_month_seq between 1200 and 1200 + 11
and cs_ship_date_sk   = d_date_sk
and cs_warehouse_sk   = w_warehouse_sk
and cs_ship_mode_sk   = sm_ship_mode_sk
and cs_call_center_sk = cc_call_center_sk
group by
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
order by substr(w_warehouse_name,1,20)
        ,sm_type
        ,cc_name
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk <= 30 ) then 1 else 0 end)  as "30 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 30) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 60) then 1 else 0 end )  as "31-60 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 60) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 90) then 1 else 0 end)  as "61-90 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 90) and
                 (cs_ship_date_sk - cs_sold_date_sk <= 120) then 1 else 0 end)  as "91-120 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk  > 120) then 1 else 0 end)  as ">120 days" 
from
   catalog_sales
  ,warehouse
  ,ship_mode
  ,call_center
  ,date_dim
where
    d_month_seq between 1210 and 1210 + 11
and cs_ship_date_sk   = d_date_sk
and cs_warehouse_sk   = w_warehouse_sk
and cs_ship_mode_sk   = sm_ship_mode_sk
and cs_call_center_sk = cc_call_center_sk
group by
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
order by substr(w_warehouse_name,1,20)
        ,sm_type
        ,cc_name
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk <= 30 ) then 1 else 0 end)  as "30 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 30) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 60) then 1 else 0 end )  as "31-60 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 60) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 90) then 1 else 0 end)  as "61-90 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 90) and
                 (cs_ship_date_sk - cs_sold_date_sk <= 120) then 1 else 0 end)  as "91-120 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk  > 120) then 1 else 0 end)  as ">120 days" 
from
   catalog_sales
  ,warehouse
  ,ship_mode
  ,call_center
  ,date_dim
where
    d_month_seq between 1205 and 1205 + 11
and cs_ship_date_sk   = d_date_sk
and cs_warehouse_sk   = w_warehouse_sk
and cs_ship_mode_sk   = sm_ship_mode_sk
and cs_call_center_sk = cc_call_center_sk
group by
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
order by substr(w_warehouse_name,1,20)
        ,sm_type
        ,cc_name
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk <= 30 ) then 1 else 0 end)  as "30 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 30) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 60) then 1 else 0 end )  as "31-60 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 60) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 90) then 1 else 0 end)  as "61-90 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 90) and
                 (cs_ship_date_sk - cs_sold_date_sk <= 120) then 1 else 0 end)  as "91-120 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk  > 120) then 1 else 0 end)  as ">120 days" 
from
   catalog_sales
  ,warehouse
  ,ship_mode
  ,call_center
  ,date_dim
where
    d_month_seq between 1213 and 1213 + 11
and cs_ship_date_sk   = d_date_sk
and cs_warehouse_sk   = w_warehouse_sk
and cs_ship_mode_sk   = sm_ship_mode_sk
and cs_call_center_sk = cc_call_center_sk
group by
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
order by substr(w_warehouse_name,1,20)
        ,sm_type
        ,cc_name
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk <= 30 ) then 1 else 0 end)  as "30 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 30) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 60) then 1 else 0 end )  as "31-60 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 60) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 90) then 1 else 0 end)  as "61-90 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 90) and
                 (cs_ship_date_sk - cs_sold_date_sk <= 120) then 1 else 0 end)  as "91-120 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk  > 120) then 1 else 0 end)  as ">120 days" 
from
   catalog_sales
  ,warehouse
  ,ship_mode
  ,call_center
  ,date_dim
where
    d_month_seq between 1187 and 1187 + 11
and cs_ship_date_sk   = d_date_sk
and cs_warehouse_sk   = w_warehouse_sk
and cs_ship_mode_sk   = sm_ship_mode_sk
and cs_call_center_sk = cc_call_center_sk
group by
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
order by substr(w_warehouse_name,1,20)
        ,sm_type
        ,cc_name
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk <= 30 ) then 1 else 0 end)  as "30 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 30) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 60) then 1 else 0 end )  as "31-60 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 60) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 90) then 1 else 0 end)  as "61-90 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 90) and
                 (cs_ship_date_sk - cs_sold_date_sk <= 120) then 1 else 0 end)  as "91-120 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk  > 120) then 1 else 0 end)  as ">120 days" 
from
   catalog_sales
  ,warehouse
  ,ship_mode
  ,call_center
  ,date_dim
where
    d_month_seq between 1220 and 1220 + 11
and cs_ship_date_sk   = d_date_sk
and cs_warehouse_sk   = w_warehouse_sk
and cs_ship_mode_sk   = sm_ship_mode_sk
and cs_call_center_sk = cc_call_center_sk
group by
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
order by substr(w_warehouse_name,1,20)
        ,sm_type
        ,cc_name
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk <= 30 ) then 1 else 0 end)  as "30 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 30) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 60) then 1 else 0 end )  as "31-60 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 60) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 90) then 1 else 0 end)  as "61-90 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 90) and
                 (cs_ship_date_sk - cs_sold_date_sk <= 120) then 1 else 0 end)  as "91-120 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk  > 120) then 1 else 0 end)  as ">120 days" 
from
   catalog_sales
  ,warehouse
  ,ship_mode
  ,call_center
  ,date_dim
where
    d_month_seq between 1210 and 1210 + 11
and cs_ship_date_sk   = d_date_sk
and cs_warehouse_sk   = w_warehouse_sk
and cs_ship_mode_sk   = sm_ship_mode_sk
and cs_call_center_sk = cc_call_center_sk
group by
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
order by substr(w_warehouse_name,1,20)
        ,sm_type
        ,cc_name
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk <= 30 ) then 1 else 0 end)  as "30 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 30) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 60) then 1 else 0 end )  as "31-60 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 60) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 90) then 1 else 0 end)  as "61-90 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 90) and
                 (cs_ship_date_sk - cs_sold_date_sk <= 120) then 1 else 0 end)  as "91-120 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk  > 120) then 1 else 0 end)  as ">120 days" 
from
   catalog_sales
  ,warehouse
  ,ship_mode
  ,call_center
  ,date_dim
where
    d_month_seq between 1184 and 1184 + 11
and cs_ship_date_sk   = d_date_sk
and cs_warehouse_sk   = w_warehouse_sk
and cs_ship_mode_sk   = sm_ship_mode_sk
and cs_call_center_sk = cc_call_center_sk
group by
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
order by substr(w_warehouse_name,1,20)
        ,sm_type
        ,cc_name
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk <= 30 ) then 1 else 0 end)  as "30 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 30) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 60) then 1 else 0 end )  as "31-60 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 60) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 90) then 1 else 0 end)  as "61-90 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 90) and
                 (cs_ship_date_sk - cs_sold_date_sk <= 120) then 1 else 0 end)  as "91-120 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk  > 120) then 1 else 0 end)  as ">120 days" 
from
   catalog_sales
  ,warehouse
  ,ship_mode
  ,call_center
  ,date_dim
where
    d_month_seq between 1208 and 1208 + 11
and cs_ship_date_sk   = d_date_sk
and cs_warehouse_sk   = w_warehouse_sk
and cs_ship_mode_sk   = sm_ship_mode_sk
and cs_call_center_sk = cc_call_center_sk
group by
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
order by substr(w_warehouse_name,1,20)
        ,sm_type
        ,cc_name
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk <= 30 ) then 1 else 0 end)  as "30 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 30) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 60) then 1 else 0 end )  as "31-60 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 60) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 90) then 1 else 0 end)  as "61-90 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 90) and
                 (cs_ship_date_sk - cs_sold_date_sk <= 120) then 1 else 0 end)  as "91-120 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk  > 120) then 1 else 0 end)  as ">120 days" 
from
   catalog_sales
  ,warehouse
  ,ship_mode
  ,call_center
  ,date_dim
where
    d_month_seq between 1180 and 1180 + 11
and cs_ship_date_sk   = d_date_sk
and cs_warehouse_sk   = w_warehouse_sk
and cs_ship_mode_sk   = sm_ship_mode_sk
and cs_call_center_sk = cc_call_center_sk
group by
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
order by substr(w_warehouse_name,1,20)
        ,sm_type
        ,cc_name
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk <= 30 ) then 1 else 0 end)  as "30 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 30) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 60) then 1 else 0 end )  as "31-60 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 60) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 90) then 1 else 0 end)  as "61-90 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 90) and
                 (cs_ship_date_sk - cs_sold_date_sk <= 120) then 1 else 0 end)  as "91-120 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk  > 120) then 1 else 0 end)  as ">120 days" 
from
   catalog_sales
  ,warehouse
  ,ship_mode
  ,call_center
  ,date_dim
where
    d_month_seq between 1183 and 1183 + 11
and cs_ship_date_sk   = d_date_sk
and cs_warehouse_sk   = w_warehouse_sk
and cs_ship_mode_sk   = sm_ship_mode_sk
and cs_call_center_sk = cc_call_center_sk
group by
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
order by substr(w_warehouse_name,1,20)
        ,sm_type
        ,cc_name
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk <= 30 ) then 1 else 0 end)  as "30 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 30) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 60) then 1 else 0 end )  as "31-60 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 60) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 90) then 1 else 0 end)  as "61-90 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 90) and
                 (cs_ship_date_sk - cs_sold_date_sk <= 120) then 1 else 0 end)  as "91-120 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk  > 120) then 1 else 0 end)  as ">120 days" 
from
   catalog_sales
  ,warehouse
  ,ship_mode
  ,call_center
  ,date_dim
where
    d_month_seq between 1186 and 1186 + 11
and cs_ship_date_sk   = d_date_sk
and cs_warehouse_sk   = w_warehouse_sk
and cs_ship_mode_sk   = sm_ship_mode_sk
and cs_call_center_sk = cc_call_center_sk
group by
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
order by substr(w_warehouse_name,1,20)
        ,sm_type
        ,cc_name
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk <= 30 ) then 1 else 0 end)  as "30 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 30) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 60) then 1 else 0 end )  as "31-60 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 60) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 90) then 1 else 0 end)  as "61-90 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 90) and
                 (cs_ship_date_sk - cs_sold_date_sk <= 120) then 1 else 0 end)  as "91-120 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk  > 120) then 1 else 0 end)  as ">120 days" 
from
   catalog_sales
  ,warehouse
  ,ship_mode
  ,call_center
  ,date_dim
where
    d_month_seq between 1220 and 1220 + 11
and cs_ship_date_sk   = d_date_sk
and cs_warehouse_sk   = w_warehouse_sk
and cs_ship_mode_sk   = sm_ship_mode_sk
and cs_call_center_sk = cc_call_center_sk
group by
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
order by substr(w_warehouse_name,1,20)
        ,sm_type
        ,cc_name
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk <= 30 ) then 1 else 0 end)  as "30 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 30) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 60) then 1 else 0 end )  as "31-60 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 60) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 90) then 1 else 0 end)  as "61-90 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 90) and
                 (cs_ship_date_sk - cs_sold_date_sk <= 120) then 1 else 0 end)  as "91-120 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk  > 120) then 1 else 0 end)  as ">120 days" 
from
   catalog_sales
  ,warehouse
  ,ship_mode
  ,call_center
  ,date_dim
where
    d_month_seq between 1201 and 1201 + 11
and cs_ship_date_sk   = d_date_sk
and cs_warehouse_sk   = w_warehouse_sk
and cs_ship_mode_sk   = sm_ship_mode_sk
and cs_call_center_sk = cc_call_center_sk
group by
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
order by substr(w_warehouse_name,1,20)
        ,sm_type
        ,cc_name
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk <= 30 ) then 1 else 0 end)  as "30 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 30) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 60) then 1 else 0 end )  as "31-60 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 60) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 90) then 1 else 0 end)  as "61-90 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 90) and
                 (cs_ship_date_sk - cs_sold_date_sk <= 120) then 1 else 0 end)  as "91-120 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk  > 120) then 1 else 0 end)  as ">120 days" 
from
   catalog_sales
  ,warehouse
  ,ship_mode
  ,call_center
  ,date_dim
where
    d_month_seq between 1197 and 1197 + 11
and cs_ship_date_sk   = d_date_sk
and cs_warehouse_sk   = w_warehouse_sk
and cs_ship_mode_sk   = sm_ship_mode_sk
and cs_call_center_sk = cc_call_center_sk
group by
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
order by substr(w_warehouse_name,1,20)
        ,sm_type
        ,cc_name
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk <= 30 ) then 1 else 0 end)  as "30 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 30) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 60) then 1 else 0 end )  as "31-60 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 60) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 90) then 1 else 0 end)  as "61-90 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 90) and
                 (cs_ship_date_sk - cs_sold_date_sk <= 120) then 1 else 0 end)  as "91-120 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk  > 120) then 1 else 0 end)  as ">120 days" 
from
   catalog_sales
  ,warehouse
  ,ship_mode
  ,call_center
  ,date_dim
where
    d_month_seq between 1198 and 1198 + 11
and cs_ship_date_sk   = d_date_sk
and cs_warehouse_sk   = w_warehouse_sk
and cs_ship_mode_sk   = sm_ship_mode_sk
and cs_call_center_sk = cc_call_center_sk
group by
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
order by substr(w_warehouse_name,1,20)
        ,sm_type
        ,cc_name
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk <= 30 ) then 1 else 0 end)  as "30 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 30) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 60) then 1 else 0 end )  as "31-60 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 60) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 90) then 1 else 0 end)  as "61-90 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 90) and
                 (cs_ship_date_sk - cs_sold_date_sk <= 120) then 1 else 0 end)  as "91-120 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk  > 120) then 1 else 0 end)  as ">120 days" 
from
   catalog_sales
  ,warehouse
  ,ship_mode
  ,call_center
  ,date_dim
where
    d_month_seq between 1191 and 1191 + 11
and cs_ship_date_sk   = d_date_sk
and cs_warehouse_sk   = w_warehouse_sk
and cs_ship_mode_sk   = sm_ship_mode_sk
and cs_call_center_sk = cc_call_center_sk
group by
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
order by substr(w_warehouse_name,1,20)
        ,sm_type
        ,cc_name
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk <= 30 ) then 1 else 0 end)  as "30 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 30) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 60) then 1 else 0 end )  as "31-60 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 60) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 90) then 1 else 0 end)  as "61-90 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 90) and
                 (cs_ship_date_sk - cs_sold_date_sk <= 120) then 1 else 0 end)  as "91-120 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk  > 120) then 1 else 0 end)  as ">120 days" 
from
   catalog_sales
  ,warehouse
  ,ship_mode
  ,call_center
  ,date_dim
where
    d_month_seq between 1204 and 1204 + 11
and cs_ship_date_sk   = d_date_sk
and cs_warehouse_sk   = w_warehouse_sk
and cs_ship_mode_sk   = sm_ship_mode_sk
and cs_call_center_sk = cc_call_center_sk
group by
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
order by substr(w_warehouse_name,1,20)
        ,sm_type
        ,cc_name
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk <= 30 ) then 1 else 0 end)  as "30 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 30) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 60) then 1 else 0 end )  as "31-60 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 60) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 90) then 1 else 0 end)  as "61-90 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 90) and
                 (cs_ship_date_sk - cs_sold_date_sk <= 120) then 1 else 0 end)  as "91-120 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk  > 120) then 1 else 0 end)  as ">120 days" 
from
   catalog_sales
  ,warehouse
  ,ship_mode
  ,call_center
  ,date_dim
where
    d_month_seq between 1213 and 1213 + 11
and cs_ship_date_sk   = d_date_sk
and cs_warehouse_sk   = w_warehouse_sk
and cs_ship_mode_sk   = sm_ship_mode_sk
and cs_call_center_sk = cc_call_center_sk
group by
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
order by substr(w_warehouse_name,1,20)
        ,sm_type
        ,cc_name
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk <= 30 ) then 1 else 0 end)  as "30 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 30) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 60) then 1 else 0 end )  as "31-60 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 60) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 90) then 1 else 0 end)  as "61-90 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 90) and
                 (cs_ship_date_sk - cs_sold_date_sk <= 120) then 1 else 0 end)  as "91-120 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk  > 120) then 1 else 0 end)  as ">120 days" 
from
   catalog_sales
  ,warehouse
  ,ship_mode
  ,call_center
  ,date_dim
where
    d_month_seq between 1176 and 1176 + 11
and cs_ship_date_sk   = d_date_sk
and cs_warehouse_sk   = w_warehouse_sk
and cs_ship_mode_sk   = sm_ship_mode_sk
and cs_call_center_sk = cc_call_center_sk
group by
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
order by substr(w_warehouse_name,1,20)
        ,sm_type
        ,cc_name
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk <= 30 ) then 1 else 0 end)  as "30 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 30) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 60) then 1 else 0 end )  as "31-60 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 60) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 90) then 1 else 0 end)  as "61-90 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 90) and
                 (cs_ship_date_sk - cs_sold_date_sk <= 120) then 1 else 0 end)  as "91-120 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk  > 120) then 1 else 0 end)  as ">120 days" 
from
   catalog_sales
  ,warehouse
  ,ship_mode
  ,call_center
  ,date_dim
where
    d_month_seq between 1219 and 1219 + 11
and cs_ship_date_sk   = d_date_sk
and cs_warehouse_sk   = w_warehouse_sk
and cs_ship_mode_sk   = sm_ship_mode_sk
and cs_call_center_sk = cc_call_center_sk
group by
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
order by substr(w_warehouse_name,1,20)
        ,sm_type
        ,cc_name
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk <= 30 ) then 1 else 0 end)  as "30 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 30) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 60) then 1 else 0 end )  as "31-60 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 60) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 90) then 1 else 0 end)  as "61-90 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 90) and
                 (cs_ship_date_sk - cs_sold_date_sk <= 120) then 1 else 0 end)  as "91-120 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk  > 120) then 1 else 0 end)  as ">120 days" 
from
   catalog_sales
  ,warehouse
  ,ship_mode
  ,call_center
  ,date_dim
where
    d_month_seq between 1184 and 1184 + 11
and cs_ship_date_sk   = d_date_sk
and cs_warehouse_sk   = w_warehouse_sk
and cs_ship_mode_sk   = sm_ship_mode_sk
and cs_call_center_sk = cc_call_center_sk
group by
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
order by substr(w_warehouse_name,1,20)
        ,sm_type
        ,cc_name
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk <= 30 ) then 1 else 0 end)  as "30 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 30) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 60) then 1 else 0 end )  as "31-60 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 60) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 90) then 1 else 0 end)  as "61-90 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 90) and
                 (cs_ship_date_sk - cs_sold_date_sk <= 120) then 1 else 0 end)  as "91-120 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk  > 120) then 1 else 0 end)  as ">120 days" 
from
   catalog_sales
  ,warehouse
  ,ship_mode
  ,call_center
  ,date_dim
where
    d_month_seq between 1194 and 1194 + 11
and cs_ship_date_sk   = d_date_sk
and cs_warehouse_sk   = w_warehouse_sk
and cs_ship_mode_sk   = sm_ship_mode_sk
and cs_call_center_sk = cc_call_center_sk
group by
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
order by substr(w_warehouse_name,1,20)
        ,sm_type
        ,cc_name
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk <= 30 ) then 1 else 0 end)  as "30 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 30) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 60) then 1 else 0 end )  as "31-60 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 60) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 90) then 1 else 0 end)  as "61-90 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 90) and
                 (cs_ship_date_sk - cs_sold_date_sk <= 120) then 1 else 0 end)  as "91-120 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk  > 120) then 1 else 0 end)  as ">120 days" 
from
   catalog_sales
  ,warehouse
  ,ship_mode
  ,call_center
  ,date_dim
where
    d_month_seq between 1206 and 1206 + 11
and cs_ship_date_sk   = d_date_sk
and cs_warehouse_sk   = w_warehouse_sk
and cs_ship_mode_sk   = sm_ship_mode_sk
and cs_call_center_sk = cc_call_center_sk
group by
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
order by substr(w_warehouse_name,1,20)
        ,sm_type
        ,cc_name
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk <= 30 ) then 1 else 0 end)  as "30 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 30) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 60) then 1 else 0 end )  as "31-60 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 60) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 90) then 1 else 0 end)  as "61-90 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 90) and
                 (cs_ship_date_sk - cs_sold_date_sk <= 120) then 1 else 0 end)  as "91-120 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk  > 120) then 1 else 0 end)  as ">120 days" 
from
   catalog_sales
  ,warehouse
  ,ship_mode
  ,call_center
  ,date_dim
where
    d_month_seq between 1200 and 1200 + 11
and cs_ship_date_sk   = d_date_sk
and cs_warehouse_sk   = w_warehouse_sk
and cs_ship_mode_sk   = sm_ship_mode_sk
and cs_call_center_sk = cc_call_center_sk
group by
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
order by substr(w_warehouse_name,1,20)
        ,sm_type
        ,cc_name
limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
select  
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk <= 30 ) then 1 else 0 end)  as "30 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 30) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 60) then 1 else 0 end )  as "31-60 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 60) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 90) then 1 else 0 end)  as "61-90 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 90) and
                 (cs_ship_date_sk - cs_sold_date_sk <= 120) then 1 else 0 end)  as "91-120 days" 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk  > 120) then 1 else 0 end)  as ">120 days" 
from
   catalog_sales
  ,warehouse
  ,ship_mode
  ,call_center
  ,date_dim
where
    d_month_seq between 1224 and 1224 + 11
and cs_ship_date_sk   = d_date_sk
and cs_warehouse_sk   = w_warehouse_sk
and cs_ship_mode_sk   = sm_ship_mode_sk
and cs_call_center_sk = cc_call_center_sk
group by
   substr(w_warehouse_name,1,20)
  ,sm_type
  ,cc_name
order by substr(w_warehouse_name,1,20)
        ,sm_type
        ,cc_name
limit 100;

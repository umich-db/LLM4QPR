EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ss as
 (select s_store_sk,
         sum(ss_ext_sales_price) as sales,
         sum(ss_net_profit) as profit
 from store_sales,
      date_dim,
      store
 where ss_sold_date_sk = d_date_sk
       and d_date between cast('1998-08-04' as date) 
                  and (cast('1998-08-04' as date) +  30 ) 
       and ss_store_sk = s_store_sk
 group by s_store_sk)
 ,
 sr as
 (select s_store_sk,
         sum(sr_return_amt) as returns,
         sum(sr_net_loss) as profit_loss
 from store_returns,
      date_dim,
      store
 where sr_returned_date_sk = d_date_sk
       and d_date between cast('1998-08-04' as date)
                  and (cast('1998-08-04' as date) +  30 )
       and sr_store_sk = s_store_sk
 group by s_store_sk), 
 cs as
 (select cs_call_center_sk,
        sum(cs_ext_sales_price) as sales,
        sum(cs_net_profit) as profit
 from catalog_sales,
      date_dim
 where cs_sold_date_sk = d_date_sk
       and d_date between cast('1998-08-04' as date)
                  and (cast('1998-08-04' as date) +  30 )
 group by cs_call_center_sk 
 ), 
 cr as
 (select cr_call_center_sk,
         sum(cr_return_amount) as returns,
         sum(cr_net_loss) as profit_loss
 from catalog_returns,
      date_dim
 where cr_returned_date_sk = d_date_sk
       and d_date between cast('1998-08-04' as date)
                  and (cast('1998-08-04' as date) +  30 )
 group by cr_call_center_sk
 ), 
 ws as
 ( select wp_web_page_sk,
        sum(ws_ext_sales_price) as sales,
        sum(ws_net_profit) as profit
 from web_sales,
      date_dim,
      web_page
 where ws_sold_date_sk = d_date_sk
       and d_date between cast('1998-08-04' as date)
                  and (cast('1998-08-04' as date) +  30 )
       and ws_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk), 
 wr as
 (select wp_web_page_sk,
        sum(wr_return_amt) as returns,
        sum(wr_net_loss) as profit_loss
 from web_returns,
      date_dim,
      web_page
 where wr_returned_date_sk = d_date_sk
       and d_date between cast('1998-08-04' as date)
                  and (cast('1998-08-04' as date) +  30 )
       and wr_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk)
  select  channel
        , id
        , sum(sales) as sales
        , sum(returns) as returns
        , sum(profit) as profit
 from 
 (select 'store channel' as channel
        , ss.s_store_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ss left join sr
        on  ss.s_store_sk = sr.s_store_sk
 union all
 select 'catalog channel' as channel
        , cs_call_center_sk as id
        , sales
        , returns
        , (profit - profit_loss) as profit
 from  cs
       , cr
 union all
 select 'web channel' as channel
        , ws.wp_web_page_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ws left join wr
        on  ws.wp_web_page_sk = wr.wp_web_page_sk
 ) x
 group by rollup (channel, id)
 order by channel
         ,id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ss as
 (select s_store_sk,
         sum(ss_ext_sales_price) as sales,
         sum(ss_net_profit) as profit
 from store_sales,
      date_dim,
      store
 where ss_sold_date_sk = d_date_sk
       and d_date between cast('2001-08-12' as date) 
                  and (cast('2001-08-12' as date) +  30 ) 
       and ss_store_sk = s_store_sk
 group by s_store_sk)
 ,
 sr as
 (select s_store_sk,
         sum(sr_return_amt) as returns,
         sum(sr_net_loss) as profit_loss
 from store_returns,
      date_dim,
      store
 where sr_returned_date_sk = d_date_sk
       and d_date between cast('2001-08-12' as date)
                  and (cast('2001-08-12' as date) +  30 )
       and sr_store_sk = s_store_sk
 group by s_store_sk), 
 cs as
 (select cs_call_center_sk,
        sum(cs_ext_sales_price) as sales,
        sum(cs_net_profit) as profit
 from catalog_sales,
      date_dim
 where cs_sold_date_sk = d_date_sk
       and d_date between cast('2001-08-12' as date)
                  and (cast('2001-08-12' as date) +  30 )
 group by cs_call_center_sk 
 ), 
 cr as
 (select cr_call_center_sk,
         sum(cr_return_amount) as returns,
         sum(cr_net_loss) as profit_loss
 from catalog_returns,
      date_dim
 where cr_returned_date_sk = d_date_sk
       and d_date between cast('2001-08-12' as date)
                  and (cast('2001-08-12' as date) +  30 )
 group by cr_call_center_sk
 ), 
 ws as
 ( select wp_web_page_sk,
        sum(ws_ext_sales_price) as sales,
        sum(ws_net_profit) as profit
 from web_sales,
      date_dim,
      web_page
 where ws_sold_date_sk = d_date_sk
       and d_date between cast('2001-08-12' as date)
                  and (cast('2001-08-12' as date) +  30 )
       and ws_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk), 
 wr as
 (select wp_web_page_sk,
        sum(wr_return_amt) as returns,
        sum(wr_net_loss) as profit_loss
 from web_returns,
      date_dim,
      web_page
 where wr_returned_date_sk = d_date_sk
       and d_date between cast('2001-08-12' as date)
                  and (cast('2001-08-12' as date) +  30 )
       and wr_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk)
  select  channel
        , id
        , sum(sales) as sales
        , sum(returns) as returns
        , sum(profit) as profit
 from 
 (select 'store channel' as channel
        , ss.s_store_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ss left join sr
        on  ss.s_store_sk = sr.s_store_sk
 union all
 select 'catalog channel' as channel
        , cs_call_center_sk as id
        , sales
        , returns
        , (profit - profit_loss) as profit
 from  cs
       , cr
 union all
 select 'web channel' as channel
        , ws.wp_web_page_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ws left join wr
        on  ws.wp_web_page_sk = wr.wp_web_page_sk
 ) x
 group by rollup (channel, id)
 order by channel
         ,id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ss as
 (select s_store_sk,
         sum(ss_ext_sales_price) as sales,
         sum(ss_net_profit) as profit
 from store_sales,
      date_dim,
      store
 where ss_sold_date_sk = d_date_sk
       and d_date between cast('1998-08-12' as date) 
                  and (cast('1998-08-12' as date) +  30 ) 
       and ss_store_sk = s_store_sk
 group by s_store_sk)
 ,
 sr as
 (select s_store_sk,
         sum(sr_return_amt) as returns,
         sum(sr_net_loss) as profit_loss
 from store_returns,
      date_dim,
      store
 where sr_returned_date_sk = d_date_sk
       and d_date between cast('1998-08-12' as date)
                  and (cast('1998-08-12' as date) +  30 )
       and sr_store_sk = s_store_sk
 group by s_store_sk), 
 cs as
 (select cs_call_center_sk,
        sum(cs_ext_sales_price) as sales,
        sum(cs_net_profit) as profit
 from catalog_sales,
      date_dim
 where cs_sold_date_sk = d_date_sk
       and d_date between cast('1998-08-12' as date)
                  and (cast('1998-08-12' as date) +  30 )
 group by cs_call_center_sk 
 ), 
 cr as
 (select cr_call_center_sk,
         sum(cr_return_amount) as returns,
         sum(cr_net_loss) as profit_loss
 from catalog_returns,
      date_dim
 where cr_returned_date_sk = d_date_sk
       and d_date between cast('1998-08-12' as date)
                  and (cast('1998-08-12' as date) +  30 )
 group by cr_call_center_sk
 ), 
 ws as
 ( select wp_web_page_sk,
        sum(ws_ext_sales_price) as sales,
        sum(ws_net_profit) as profit
 from web_sales,
      date_dim,
      web_page
 where ws_sold_date_sk = d_date_sk
       and d_date between cast('1998-08-12' as date)
                  and (cast('1998-08-12' as date) +  30 )
       and ws_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk), 
 wr as
 (select wp_web_page_sk,
        sum(wr_return_amt) as returns,
        sum(wr_net_loss) as profit_loss
 from web_returns,
      date_dim,
      web_page
 where wr_returned_date_sk = d_date_sk
       and d_date between cast('1998-08-12' as date)
                  and (cast('1998-08-12' as date) +  30 )
       and wr_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk)
  select  channel
        , id
        , sum(sales) as sales
        , sum(returns) as returns
        , sum(profit) as profit
 from 
 (select 'store channel' as channel
        , ss.s_store_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ss left join sr
        on  ss.s_store_sk = sr.s_store_sk
 union all
 select 'catalog channel' as channel
        , cs_call_center_sk as id
        , sales
        , returns
        , (profit - profit_loss) as profit
 from  cs
       , cr
 union all
 select 'web channel' as channel
        , ws.wp_web_page_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ws left join wr
        on  ws.wp_web_page_sk = wr.wp_web_page_sk
 ) x
 group by rollup (channel, id)
 order by channel
         ,id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ss as
 (select s_store_sk,
         sum(ss_ext_sales_price) as sales,
         sum(ss_net_profit) as profit
 from store_sales,
      date_dim,
      store
 where ss_sold_date_sk = d_date_sk
       and d_date between cast('2002-08-17' as date) 
                  and (cast('2002-08-17' as date) +  30 ) 
       and ss_store_sk = s_store_sk
 group by s_store_sk)
 ,
 sr as
 (select s_store_sk,
         sum(sr_return_amt) as returns,
         sum(sr_net_loss) as profit_loss
 from store_returns,
      date_dim,
      store
 where sr_returned_date_sk = d_date_sk
       and d_date between cast('2002-08-17' as date)
                  and (cast('2002-08-17' as date) +  30 )
       and sr_store_sk = s_store_sk
 group by s_store_sk), 
 cs as
 (select cs_call_center_sk,
        sum(cs_ext_sales_price) as sales,
        sum(cs_net_profit) as profit
 from catalog_sales,
      date_dim
 where cs_sold_date_sk = d_date_sk
       and d_date between cast('2002-08-17' as date)
                  and (cast('2002-08-17' as date) +  30 )
 group by cs_call_center_sk 
 ), 
 cr as
 (select cr_call_center_sk,
         sum(cr_return_amount) as returns,
         sum(cr_net_loss) as profit_loss
 from catalog_returns,
      date_dim
 where cr_returned_date_sk = d_date_sk
       and d_date between cast('2002-08-17' as date)
                  and (cast('2002-08-17' as date) +  30 )
 group by cr_call_center_sk
 ), 
 ws as
 ( select wp_web_page_sk,
        sum(ws_ext_sales_price) as sales,
        sum(ws_net_profit) as profit
 from web_sales,
      date_dim,
      web_page
 where ws_sold_date_sk = d_date_sk
       and d_date between cast('2002-08-17' as date)
                  and (cast('2002-08-17' as date) +  30 )
       and ws_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk), 
 wr as
 (select wp_web_page_sk,
        sum(wr_return_amt) as returns,
        sum(wr_net_loss) as profit_loss
 from web_returns,
      date_dim,
      web_page
 where wr_returned_date_sk = d_date_sk
       and d_date between cast('2002-08-17' as date)
                  and (cast('2002-08-17' as date) +  30 )
       and wr_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk)
  select  channel
        , id
        , sum(sales) as sales
        , sum(returns) as returns
        , sum(profit) as profit
 from 
 (select 'store channel' as channel
        , ss.s_store_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ss left join sr
        on  ss.s_store_sk = sr.s_store_sk
 union all
 select 'catalog channel' as channel
        , cs_call_center_sk as id
        , sales
        , returns
        , (profit - profit_loss) as profit
 from  cs
       , cr
 union all
 select 'web channel' as channel
        , ws.wp_web_page_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ws left join wr
        on  ws.wp_web_page_sk = wr.wp_web_page_sk
 ) x
 group by rollup (channel, id)
 order by channel
         ,id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ss as
 (select s_store_sk,
         sum(ss_ext_sales_price) as sales,
         sum(ss_net_profit) as profit
 from store_sales,
      date_dim,
      store
 where ss_sold_date_sk = d_date_sk
       and d_date between cast('2001-08-15' as date) 
                  and (cast('2001-08-15' as date) +  30 ) 
       and ss_store_sk = s_store_sk
 group by s_store_sk)
 ,
 sr as
 (select s_store_sk,
         sum(sr_return_amt) as returns,
         sum(sr_net_loss) as profit_loss
 from store_returns,
      date_dim,
      store
 where sr_returned_date_sk = d_date_sk
       and d_date between cast('2001-08-15' as date)
                  and (cast('2001-08-15' as date) +  30 )
       and sr_store_sk = s_store_sk
 group by s_store_sk), 
 cs as
 (select cs_call_center_sk,
        sum(cs_ext_sales_price) as sales,
        sum(cs_net_profit) as profit
 from catalog_sales,
      date_dim
 where cs_sold_date_sk = d_date_sk
       and d_date between cast('2001-08-15' as date)
                  and (cast('2001-08-15' as date) +  30 )
 group by cs_call_center_sk 
 ), 
 cr as
 (select cr_call_center_sk,
         sum(cr_return_amount) as returns,
         sum(cr_net_loss) as profit_loss
 from catalog_returns,
      date_dim
 where cr_returned_date_sk = d_date_sk
       and d_date between cast('2001-08-15' as date)
                  and (cast('2001-08-15' as date) +  30 )
 group by cr_call_center_sk
 ), 
 ws as
 ( select wp_web_page_sk,
        sum(ws_ext_sales_price) as sales,
        sum(ws_net_profit) as profit
 from web_sales,
      date_dim,
      web_page
 where ws_sold_date_sk = d_date_sk
       and d_date between cast('2001-08-15' as date)
                  and (cast('2001-08-15' as date) +  30 )
       and ws_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk), 
 wr as
 (select wp_web_page_sk,
        sum(wr_return_amt) as returns,
        sum(wr_net_loss) as profit_loss
 from web_returns,
      date_dim,
      web_page
 where wr_returned_date_sk = d_date_sk
       and d_date between cast('2001-08-15' as date)
                  and (cast('2001-08-15' as date) +  30 )
       and wr_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk)
  select  channel
        , id
        , sum(sales) as sales
        , sum(returns) as returns
        , sum(profit) as profit
 from 
 (select 'store channel' as channel
        , ss.s_store_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ss left join sr
        on  ss.s_store_sk = sr.s_store_sk
 union all
 select 'catalog channel' as channel
        , cs_call_center_sk as id
        , sales
        , returns
        , (profit - profit_loss) as profit
 from  cs
       , cr
 union all
 select 'web channel' as channel
        , ws.wp_web_page_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ws left join wr
        on  ws.wp_web_page_sk = wr.wp_web_page_sk
 ) x
 group by rollup (channel, id)
 order by channel
         ,id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ss as
 (select s_store_sk,
         sum(ss_ext_sales_price) as sales,
         sum(ss_net_profit) as profit
 from store_sales,
      date_dim,
      store
 where ss_sold_date_sk = d_date_sk
       and d_date between cast('2001-08-25' as date) 
                  and (cast('2001-08-25' as date) +  30 ) 
       and ss_store_sk = s_store_sk
 group by s_store_sk)
 ,
 sr as
 (select s_store_sk,
         sum(sr_return_amt) as returns,
         sum(sr_net_loss) as profit_loss
 from store_returns,
      date_dim,
      store
 where sr_returned_date_sk = d_date_sk
       and d_date between cast('2001-08-25' as date)
                  and (cast('2001-08-25' as date) +  30 )
       and sr_store_sk = s_store_sk
 group by s_store_sk), 
 cs as
 (select cs_call_center_sk,
        sum(cs_ext_sales_price) as sales,
        sum(cs_net_profit) as profit
 from catalog_sales,
      date_dim
 where cs_sold_date_sk = d_date_sk
       and d_date between cast('2001-08-25' as date)
                  and (cast('2001-08-25' as date) +  30 )
 group by cs_call_center_sk 
 ), 
 cr as
 (select cr_call_center_sk,
         sum(cr_return_amount) as returns,
         sum(cr_net_loss) as profit_loss
 from catalog_returns,
      date_dim
 where cr_returned_date_sk = d_date_sk
       and d_date between cast('2001-08-25' as date)
                  and (cast('2001-08-25' as date) +  30 )
 group by cr_call_center_sk
 ), 
 ws as
 ( select wp_web_page_sk,
        sum(ws_ext_sales_price) as sales,
        sum(ws_net_profit) as profit
 from web_sales,
      date_dim,
      web_page
 where ws_sold_date_sk = d_date_sk
       and d_date between cast('2001-08-25' as date)
                  and (cast('2001-08-25' as date) +  30 )
       and ws_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk), 
 wr as
 (select wp_web_page_sk,
        sum(wr_return_amt) as returns,
        sum(wr_net_loss) as profit_loss
 from web_returns,
      date_dim,
      web_page
 where wr_returned_date_sk = d_date_sk
       and d_date between cast('2001-08-25' as date)
                  and (cast('2001-08-25' as date) +  30 )
       and wr_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk)
  select  channel
        , id
        , sum(sales) as sales
        , sum(returns) as returns
        , sum(profit) as profit
 from 
 (select 'store channel' as channel
        , ss.s_store_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ss left join sr
        on  ss.s_store_sk = sr.s_store_sk
 union all
 select 'catalog channel' as channel
        , cs_call_center_sk as id
        , sales
        , returns
        , (profit - profit_loss) as profit
 from  cs
       , cr
 union all
 select 'web channel' as channel
        , ws.wp_web_page_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ws left join wr
        on  ws.wp_web_page_sk = wr.wp_web_page_sk
 ) x
 group by rollup (channel, id)
 order by channel
         ,id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ss as
 (select s_store_sk,
         sum(ss_ext_sales_price) as sales,
         sum(ss_net_profit) as profit
 from store_sales,
      date_dim,
      store
 where ss_sold_date_sk = d_date_sk
       and d_date between cast('2002-08-04' as date) 
                  and (cast('2002-08-04' as date) +  30 ) 
       and ss_store_sk = s_store_sk
 group by s_store_sk)
 ,
 sr as
 (select s_store_sk,
         sum(sr_return_amt) as returns,
         sum(sr_net_loss) as profit_loss
 from store_returns,
      date_dim,
      store
 where sr_returned_date_sk = d_date_sk
       and d_date between cast('2002-08-04' as date)
                  and (cast('2002-08-04' as date) +  30 )
       and sr_store_sk = s_store_sk
 group by s_store_sk), 
 cs as
 (select cs_call_center_sk,
        sum(cs_ext_sales_price) as sales,
        sum(cs_net_profit) as profit
 from catalog_sales,
      date_dim
 where cs_sold_date_sk = d_date_sk
       and d_date between cast('2002-08-04' as date)
                  and (cast('2002-08-04' as date) +  30 )
 group by cs_call_center_sk 
 ), 
 cr as
 (select cr_call_center_sk,
         sum(cr_return_amount) as returns,
         sum(cr_net_loss) as profit_loss
 from catalog_returns,
      date_dim
 where cr_returned_date_sk = d_date_sk
       and d_date between cast('2002-08-04' as date)
                  and (cast('2002-08-04' as date) +  30 )
 group by cr_call_center_sk
 ), 
 ws as
 ( select wp_web_page_sk,
        sum(ws_ext_sales_price) as sales,
        sum(ws_net_profit) as profit
 from web_sales,
      date_dim,
      web_page
 where ws_sold_date_sk = d_date_sk
       and d_date between cast('2002-08-04' as date)
                  and (cast('2002-08-04' as date) +  30 )
       and ws_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk), 
 wr as
 (select wp_web_page_sk,
        sum(wr_return_amt) as returns,
        sum(wr_net_loss) as profit_loss
 from web_returns,
      date_dim,
      web_page
 where wr_returned_date_sk = d_date_sk
       and d_date between cast('2002-08-04' as date)
                  and (cast('2002-08-04' as date) +  30 )
       and wr_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk)
  select  channel
        , id
        , sum(sales) as sales
        , sum(returns) as returns
        , sum(profit) as profit
 from 
 (select 'store channel' as channel
        , ss.s_store_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ss left join sr
        on  ss.s_store_sk = sr.s_store_sk
 union all
 select 'catalog channel' as channel
        , cs_call_center_sk as id
        , sales
        , returns
        , (profit - profit_loss) as profit
 from  cs
       , cr
 union all
 select 'web channel' as channel
        , ws.wp_web_page_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ws left join wr
        on  ws.wp_web_page_sk = wr.wp_web_page_sk
 ) x
 group by rollup (channel, id)
 order by channel
         ,id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ss as
 (select s_store_sk,
         sum(ss_ext_sales_price) as sales,
         sum(ss_net_profit) as profit
 from store_sales,
      date_dim,
      store
 where ss_sold_date_sk = d_date_sk
       and d_date between cast('1999-08-25' as date) 
                  and (cast('1999-08-25' as date) +  30 ) 
       and ss_store_sk = s_store_sk
 group by s_store_sk)
 ,
 sr as
 (select s_store_sk,
         sum(sr_return_amt) as returns,
         sum(sr_net_loss) as profit_loss
 from store_returns,
      date_dim,
      store
 where sr_returned_date_sk = d_date_sk
       and d_date between cast('1999-08-25' as date)
                  and (cast('1999-08-25' as date) +  30 )
       and sr_store_sk = s_store_sk
 group by s_store_sk), 
 cs as
 (select cs_call_center_sk,
        sum(cs_ext_sales_price) as sales,
        sum(cs_net_profit) as profit
 from catalog_sales,
      date_dim
 where cs_sold_date_sk = d_date_sk
       and d_date between cast('1999-08-25' as date)
                  and (cast('1999-08-25' as date) +  30 )
 group by cs_call_center_sk 
 ), 
 cr as
 (select cr_call_center_sk,
         sum(cr_return_amount) as returns,
         sum(cr_net_loss) as profit_loss
 from catalog_returns,
      date_dim
 where cr_returned_date_sk = d_date_sk
       and d_date between cast('1999-08-25' as date)
                  and (cast('1999-08-25' as date) +  30 )
 group by cr_call_center_sk
 ), 
 ws as
 ( select wp_web_page_sk,
        sum(ws_ext_sales_price) as sales,
        sum(ws_net_profit) as profit
 from web_sales,
      date_dim,
      web_page
 where ws_sold_date_sk = d_date_sk
       and d_date between cast('1999-08-25' as date)
                  and (cast('1999-08-25' as date) +  30 )
       and ws_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk), 
 wr as
 (select wp_web_page_sk,
        sum(wr_return_amt) as returns,
        sum(wr_net_loss) as profit_loss
 from web_returns,
      date_dim,
      web_page
 where wr_returned_date_sk = d_date_sk
       and d_date between cast('1999-08-25' as date)
                  and (cast('1999-08-25' as date) +  30 )
       and wr_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk)
  select  channel
        , id
        , sum(sales) as sales
        , sum(returns) as returns
        , sum(profit) as profit
 from 
 (select 'store channel' as channel
        , ss.s_store_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ss left join sr
        on  ss.s_store_sk = sr.s_store_sk
 union all
 select 'catalog channel' as channel
        , cs_call_center_sk as id
        , sales
        , returns
        , (profit - profit_loss) as profit
 from  cs
       , cr
 union all
 select 'web channel' as channel
        , ws.wp_web_page_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ws left join wr
        on  ws.wp_web_page_sk = wr.wp_web_page_sk
 ) x
 group by rollup (channel, id)
 order by channel
         ,id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ss as
 (select s_store_sk,
         sum(ss_ext_sales_price) as sales,
         sum(ss_net_profit) as profit
 from store_sales,
      date_dim,
      store
 where ss_sold_date_sk = d_date_sk
       and d_date between cast('2000-08-10' as date) 
                  and (cast('2000-08-10' as date) +  30 ) 
       and ss_store_sk = s_store_sk
 group by s_store_sk)
 ,
 sr as
 (select s_store_sk,
         sum(sr_return_amt) as returns,
         sum(sr_net_loss) as profit_loss
 from store_returns,
      date_dim,
      store
 where sr_returned_date_sk = d_date_sk
       and d_date between cast('2000-08-10' as date)
                  and (cast('2000-08-10' as date) +  30 )
       and sr_store_sk = s_store_sk
 group by s_store_sk), 
 cs as
 (select cs_call_center_sk,
        sum(cs_ext_sales_price) as sales,
        sum(cs_net_profit) as profit
 from catalog_sales,
      date_dim
 where cs_sold_date_sk = d_date_sk
       and d_date between cast('2000-08-10' as date)
                  and (cast('2000-08-10' as date) +  30 )
 group by cs_call_center_sk 
 ), 
 cr as
 (select cr_call_center_sk,
         sum(cr_return_amount) as returns,
         sum(cr_net_loss) as profit_loss
 from catalog_returns,
      date_dim
 where cr_returned_date_sk = d_date_sk
       and d_date between cast('2000-08-10' as date)
                  and (cast('2000-08-10' as date) +  30 )
 group by cr_call_center_sk
 ), 
 ws as
 ( select wp_web_page_sk,
        sum(ws_ext_sales_price) as sales,
        sum(ws_net_profit) as profit
 from web_sales,
      date_dim,
      web_page
 where ws_sold_date_sk = d_date_sk
       and d_date between cast('2000-08-10' as date)
                  and (cast('2000-08-10' as date) +  30 )
       and ws_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk), 
 wr as
 (select wp_web_page_sk,
        sum(wr_return_amt) as returns,
        sum(wr_net_loss) as profit_loss
 from web_returns,
      date_dim,
      web_page
 where wr_returned_date_sk = d_date_sk
       and d_date between cast('2000-08-10' as date)
                  and (cast('2000-08-10' as date) +  30 )
       and wr_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk)
  select  channel
        , id
        , sum(sales) as sales
        , sum(returns) as returns
        , sum(profit) as profit
 from 
 (select 'store channel' as channel
        , ss.s_store_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ss left join sr
        on  ss.s_store_sk = sr.s_store_sk
 union all
 select 'catalog channel' as channel
        , cs_call_center_sk as id
        , sales
        , returns
        , (profit - profit_loss) as profit
 from  cs
       , cr
 union all
 select 'web channel' as channel
        , ws.wp_web_page_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ws left join wr
        on  ws.wp_web_page_sk = wr.wp_web_page_sk
 ) x
 group by rollup (channel, id)
 order by channel
         ,id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ss as
 (select s_store_sk,
         sum(ss_ext_sales_price) as sales,
         sum(ss_net_profit) as profit
 from store_sales,
      date_dim,
      store
 where ss_sold_date_sk = d_date_sk
       and d_date between cast('1998-08-28' as date) 
                  and (cast('1998-08-28' as date) +  30 ) 
       and ss_store_sk = s_store_sk
 group by s_store_sk)
 ,
 sr as
 (select s_store_sk,
         sum(sr_return_amt) as returns,
         sum(sr_net_loss) as profit_loss
 from store_returns,
      date_dim,
      store
 where sr_returned_date_sk = d_date_sk
       and d_date between cast('1998-08-28' as date)
                  and (cast('1998-08-28' as date) +  30 )
       and sr_store_sk = s_store_sk
 group by s_store_sk), 
 cs as
 (select cs_call_center_sk,
        sum(cs_ext_sales_price) as sales,
        sum(cs_net_profit) as profit
 from catalog_sales,
      date_dim
 where cs_sold_date_sk = d_date_sk
       and d_date between cast('1998-08-28' as date)
                  and (cast('1998-08-28' as date) +  30 )
 group by cs_call_center_sk 
 ), 
 cr as
 (select cr_call_center_sk,
         sum(cr_return_amount) as returns,
         sum(cr_net_loss) as profit_loss
 from catalog_returns,
      date_dim
 where cr_returned_date_sk = d_date_sk
       and d_date between cast('1998-08-28' as date)
                  and (cast('1998-08-28' as date) +  30 )
 group by cr_call_center_sk
 ), 
 ws as
 ( select wp_web_page_sk,
        sum(ws_ext_sales_price) as sales,
        sum(ws_net_profit) as profit
 from web_sales,
      date_dim,
      web_page
 where ws_sold_date_sk = d_date_sk
       and d_date between cast('1998-08-28' as date)
                  and (cast('1998-08-28' as date) +  30 )
       and ws_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk), 
 wr as
 (select wp_web_page_sk,
        sum(wr_return_amt) as returns,
        sum(wr_net_loss) as profit_loss
 from web_returns,
      date_dim,
      web_page
 where wr_returned_date_sk = d_date_sk
       and d_date between cast('1998-08-28' as date)
                  and (cast('1998-08-28' as date) +  30 )
       and wr_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk)
  select  channel
        , id
        , sum(sales) as sales
        , sum(returns) as returns
        , sum(profit) as profit
 from 
 (select 'store channel' as channel
        , ss.s_store_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ss left join sr
        on  ss.s_store_sk = sr.s_store_sk
 union all
 select 'catalog channel' as channel
        , cs_call_center_sk as id
        , sales
        , returns
        , (profit - profit_loss) as profit
 from  cs
       , cr
 union all
 select 'web channel' as channel
        , ws.wp_web_page_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ws left join wr
        on  ws.wp_web_page_sk = wr.wp_web_page_sk
 ) x
 group by rollup (channel, id)
 order by channel
         ,id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ss as
 (select s_store_sk,
         sum(ss_ext_sales_price) as sales,
         sum(ss_net_profit) as profit
 from store_sales,
      date_dim,
      store
 where ss_sold_date_sk = d_date_sk
       and d_date between cast('1999-08-12' as date) 
                  and (cast('1999-08-12' as date) +  30 ) 
       and ss_store_sk = s_store_sk
 group by s_store_sk)
 ,
 sr as
 (select s_store_sk,
         sum(sr_return_amt) as returns,
         sum(sr_net_loss) as profit_loss
 from store_returns,
      date_dim,
      store
 where sr_returned_date_sk = d_date_sk
       and d_date between cast('1999-08-12' as date)
                  and (cast('1999-08-12' as date) +  30 )
       and sr_store_sk = s_store_sk
 group by s_store_sk), 
 cs as
 (select cs_call_center_sk,
        sum(cs_ext_sales_price) as sales,
        sum(cs_net_profit) as profit
 from catalog_sales,
      date_dim
 where cs_sold_date_sk = d_date_sk
       and d_date between cast('1999-08-12' as date)
                  and (cast('1999-08-12' as date) +  30 )
 group by cs_call_center_sk 
 ), 
 cr as
 (select cr_call_center_sk,
         sum(cr_return_amount) as returns,
         sum(cr_net_loss) as profit_loss
 from catalog_returns,
      date_dim
 where cr_returned_date_sk = d_date_sk
       and d_date between cast('1999-08-12' as date)
                  and (cast('1999-08-12' as date) +  30 )
 group by cr_call_center_sk
 ), 
 ws as
 ( select wp_web_page_sk,
        sum(ws_ext_sales_price) as sales,
        sum(ws_net_profit) as profit
 from web_sales,
      date_dim,
      web_page
 where ws_sold_date_sk = d_date_sk
       and d_date between cast('1999-08-12' as date)
                  and (cast('1999-08-12' as date) +  30 )
       and ws_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk), 
 wr as
 (select wp_web_page_sk,
        sum(wr_return_amt) as returns,
        sum(wr_net_loss) as profit_loss
 from web_returns,
      date_dim,
      web_page
 where wr_returned_date_sk = d_date_sk
       and d_date between cast('1999-08-12' as date)
                  and (cast('1999-08-12' as date) +  30 )
       and wr_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk)
  select  channel
        , id
        , sum(sales) as sales
        , sum(returns) as returns
        , sum(profit) as profit
 from 
 (select 'store channel' as channel
        , ss.s_store_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ss left join sr
        on  ss.s_store_sk = sr.s_store_sk
 union all
 select 'catalog channel' as channel
        , cs_call_center_sk as id
        , sales
        , returns
        , (profit - profit_loss) as profit
 from  cs
       , cr
 union all
 select 'web channel' as channel
        , ws.wp_web_page_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ws left join wr
        on  ws.wp_web_page_sk = wr.wp_web_page_sk
 ) x
 group by rollup (channel, id)
 order by channel
         ,id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ss as
 (select s_store_sk,
         sum(ss_ext_sales_price) as sales,
         sum(ss_net_profit) as profit
 from store_sales,
      date_dim,
      store
 where ss_sold_date_sk = d_date_sk
       and d_date between cast('2002-08-05' as date) 
                  and (cast('2002-08-05' as date) +  30 ) 
       and ss_store_sk = s_store_sk
 group by s_store_sk)
 ,
 sr as
 (select s_store_sk,
         sum(sr_return_amt) as returns,
         sum(sr_net_loss) as profit_loss
 from store_returns,
      date_dim,
      store
 where sr_returned_date_sk = d_date_sk
       and d_date between cast('2002-08-05' as date)
                  and (cast('2002-08-05' as date) +  30 )
       and sr_store_sk = s_store_sk
 group by s_store_sk), 
 cs as
 (select cs_call_center_sk,
        sum(cs_ext_sales_price) as sales,
        sum(cs_net_profit) as profit
 from catalog_sales,
      date_dim
 where cs_sold_date_sk = d_date_sk
       and d_date between cast('2002-08-05' as date)
                  and (cast('2002-08-05' as date) +  30 )
 group by cs_call_center_sk 
 ), 
 cr as
 (select cr_call_center_sk,
         sum(cr_return_amount) as returns,
         sum(cr_net_loss) as profit_loss
 from catalog_returns,
      date_dim
 where cr_returned_date_sk = d_date_sk
       and d_date between cast('2002-08-05' as date)
                  and (cast('2002-08-05' as date) +  30 )
 group by cr_call_center_sk
 ), 
 ws as
 ( select wp_web_page_sk,
        sum(ws_ext_sales_price) as sales,
        sum(ws_net_profit) as profit
 from web_sales,
      date_dim,
      web_page
 where ws_sold_date_sk = d_date_sk
       and d_date between cast('2002-08-05' as date)
                  and (cast('2002-08-05' as date) +  30 )
       and ws_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk), 
 wr as
 (select wp_web_page_sk,
        sum(wr_return_amt) as returns,
        sum(wr_net_loss) as profit_loss
 from web_returns,
      date_dim,
      web_page
 where wr_returned_date_sk = d_date_sk
       and d_date between cast('2002-08-05' as date)
                  and (cast('2002-08-05' as date) +  30 )
       and wr_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk)
  select  channel
        , id
        , sum(sales) as sales
        , sum(returns) as returns
        , sum(profit) as profit
 from 
 (select 'store channel' as channel
        , ss.s_store_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ss left join sr
        on  ss.s_store_sk = sr.s_store_sk
 union all
 select 'catalog channel' as channel
        , cs_call_center_sk as id
        , sales
        , returns
        , (profit - profit_loss) as profit
 from  cs
       , cr
 union all
 select 'web channel' as channel
        , ws.wp_web_page_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ws left join wr
        on  ws.wp_web_page_sk = wr.wp_web_page_sk
 ) x
 group by rollup (channel, id)
 order by channel
         ,id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ss as
 (select s_store_sk,
         sum(ss_ext_sales_price) as sales,
         sum(ss_net_profit) as profit
 from store_sales,
      date_dim,
      store
 where ss_sold_date_sk = d_date_sk
       and d_date between cast('2001-08-03' as date) 
                  and (cast('2001-08-03' as date) +  30 ) 
       and ss_store_sk = s_store_sk
 group by s_store_sk)
 ,
 sr as
 (select s_store_sk,
         sum(sr_return_amt) as returns,
         sum(sr_net_loss) as profit_loss
 from store_returns,
      date_dim,
      store
 where sr_returned_date_sk = d_date_sk
       and d_date between cast('2001-08-03' as date)
                  and (cast('2001-08-03' as date) +  30 )
       and sr_store_sk = s_store_sk
 group by s_store_sk), 
 cs as
 (select cs_call_center_sk,
        sum(cs_ext_sales_price) as sales,
        sum(cs_net_profit) as profit
 from catalog_sales,
      date_dim
 where cs_sold_date_sk = d_date_sk
       and d_date between cast('2001-08-03' as date)
                  and (cast('2001-08-03' as date) +  30 )
 group by cs_call_center_sk 
 ), 
 cr as
 (select cr_call_center_sk,
         sum(cr_return_amount) as returns,
         sum(cr_net_loss) as profit_loss
 from catalog_returns,
      date_dim
 where cr_returned_date_sk = d_date_sk
       and d_date between cast('2001-08-03' as date)
                  and (cast('2001-08-03' as date) +  30 )
 group by cr_call_center_sk
 ), 
 ws as
 ( select wp_web_page_sk,
        sum(ws_ext_sales_price) as sales,
        sum(ws_net_profit) as profit
 from web_sales,
      date_dim,
      web_page
 where ws_sold_date_sk = d_date_sk
       and d_date between cast('2001-08-03' as date)
                  and (cast('2001-08-03' as date) +  30 )
       and ws_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk), 
 wr as
 (select wp_web_page_sk,
        sum(wr_return_amt) as returns,
        sum(wr_net_loss) as profit_loss
 from web_returns,
      date_dim,
      web_page
 where wr_returned_date_sk = d_date_sk
       and d_date between cast('2001-08-03' as date)
                  and (cast('2001-08-03' as date) +  30 )
       and wr_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk)
  select  channel
        , id
        , sum(sales) as sales
        , sum(returns) as returns
        , sum(profit) as profit
 from 
 (select 'store channel' as channel
        , ss.s_store_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ss left join sr
        on  ss.s_store_sk = sr.s_store_sk
 union all
 select 'catalog channel' as channel
        , cs_call_center_sk as id
        , sales
        , returns
        , (profit - profit_loss) as profit
 from  cs
       , cr
 union all
 select 'web channel' as channel
        , ws.wp_web_page_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ws left join wr
        on  ws.wp_web_page_sk = wr.wp_web_page_sk
 ) x
 group by rollup (channel, id)
 order by channel
         ,id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ss as
 (select s_store_sk,
         sum(ss_ext_sales_price) as sales,
         sum(ss_net_profit) as profit
 from store_sales,
      date_dim,
      store
 where ss_sold_date_sk = d_date_sk
       and d_date between cast('2001-08-12' as date) 
                  and (cast('2001-08-12' as date) +  30 ) 
       and ss_store_sk = s_store_sk
 group by s_store_sk)
 ,
 sr as
 (select s_store_sk,
         sum(sr_return_amt) as returns,
         sum(sr_net_loss) as profit_loss
 from store_returns,
      date_dim,
      store
 where sr_returned_date_sk = d_date_sk
       and d_date between cast('2001-08-12' as date)
                  and (cast('2001-08-12' as date) +  30 )
       and sr_store_sk = s_store_sk
 group by s_store_sk), 
 cs as
 (select cs_call_center_sk,
        sum(cs_ext_sales_price) as sales,
        sum(cs_net_profit) as profit
 from catalog_sales,
      date_dim
 where cs_sold_date_sk = d_date_sk
       and d_date between cast('2001-08-12' as date)
                  and (cast('2001-08-12' as date) +  30 )
 group by cs_call_center_sk 
 ), 
 cr as
 (select cr_call_center_sk,
         sum(cr_return_amount) as returns,
         sum(cr_net_loss) as profit_loss
 from catalog_returns,
      date_dim
 where cr_returned_date_sk = d_date_sk
       and d_date between cast('2001-08-12' as date)
                  and (cast('2001-08-12' as date) +  30 )
 group by cr_call_center_sk
 ), 
 ws as
 ( select wp_web_page_sk,
        sum(ws_ext_sales_price) as sales,
        sum(ws_net_profit) as profit
 from web_sales,
      date_dim,
      web_page
 where ws_sold_date_sk = d_date_sk
       and d_date between cast('2001-08-12' as date)
                  and (cast('2001-08-12' as date) +  30 )
       and ws_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk), 
 wr as
 (select wp_web_page_sk,
        sum(wr_return_amt) as returns,
        sum(wr_net_loss) as profit_loss
 from web_returns,
      date_dim,
      web_page
 where wr_returned_date_sk = d_date_sk
       and d_date between cast('2001-08-12' as date)
                  and (cast('2001-08-12' as date) +  30 )
       and wr_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk)
  select  channel
        , id
        , sum(sales) as sales
        , sum(returns) as returns
        , sum(profit) as profit
 from 
 (select 'store channel' as channel
        , ss.s_store_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ss left join sr
        on  ss.s_store_sk = sr.s_store_sk
 union all
 select 'catalog channel' as channel
        , cs_call_center_sk as id
        , sales
        , returns
        , (profit - profit_loss) as profit
 from  cs
       , cr
 union all
 select 'web channel' as channel
        , ws.wp_web_page_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ws left join wr
        on  ws.wp_web_page_sk = wr.wp_web_page_sk
 ) x
 group by rollup (channel, id)
 order by channel
         ,id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ss as
 (select s_store_sk,
         sum(ss_ext_sales_price) as sales,
         sum(ss_net_profit) as profit
 from store_sales,
      date_dim,
      store
 where ss_sold_date_sk = d_date_sk
       and d_date between cast('1999-08-13' as date) 
                  and (cast('1999-08-13' as date) +  30 ) 
       and ss_store_sk = s_store_sk
 group by s_store_sk)
 ,
 sr as
 (select s_store_sk,
         sum(sr_return_amt) as returns,
         sum(sr_net_loss) as profit_loss
 from store_returns,
      date_dim,
      store
 where sr_returned_date_sk = d_date_sk
       and d_date between cast('1999-08-13' as date)
                  and (cast('1999-08-13' as date) +  30 )
       and sr_store_sk = s_store_sk
 group by s_store_sk), 
 cs as
 (select cs_call_center_sk,
        sum(cs_ext_sales_price) as sales,
        sum(cs_net_profit) as profit
 from catalog_sales,
      date_dim
 where cs_sold_date_sk = d_date_sk
       and d_date between cast('1999-08-13' as date)
                  and (cast('1999-08-13' as date) +  30 )
 group by cs_call_center_sk 
 ), 
 cr as
 (select cr_call_center_sk,
         sum(cr_return_amount) as returns,
         sum(cr_net_loss) as profit_loss
 from catalog_returns,
      date_dim
 where cr_returned_date_sk = d_date_sk
       and d_date between cast('1999-08-13' as date)
                  and (cast('1999-08-13' as date) +  30 )
 group by cr_call_center_sk
 ), 
 ws as
 ( select wp_web_page_sk,
        sum(ws_ext_sales_price) as sales,
        sum(ws_net_profit) as profit
 from web_sales,
      date_dim,
      web_page
 where ws_sold_date_sk = d_date_sk
       and d_date between cast('1999-08-13' as date)
                  and (cast('1999-08-13' as date) +  30 )
       and ws_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk), 
 wr as
 (select wp_web_page_sk,
        sum(wr_return_amt) as returns,
        sum(wr_net_loss) as profit_loss
 from web_returns,
      date_dim,
      web_page
 where wr_returned_date_sk = d_date_sk
       and d_date between cast('1999-08-13' as date)
                  and (cast('1999-08-13' as date) +  30 )
       and wr_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk)
  select  channel
        , id
        , sum(sales) as sales
        , sum(returns) as returns
        , sum(profit) as profit
 from 
 (select 'store channel' as channel
        , ss.s_store_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ss left join sr
        on  ss.s_store_sk = sr.s_store_sk
 union all
 select 'catalog channel' as channel
        , cs_call_center_sk as id
        , sales
        , returns
        , (profit - profit_loss) as profit
 from  cs
       , cr
 union all
 select 'web channel' as channel
        , ws.wp_web_page_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ws left join wr
        on  ws.wp_web_page_sk = wr.wp_web_page_sk
 ) x
 group by rollup (channel, id)
 order by channel
         ,id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ss as
 (select s_store_sk,
         sum(ss_ext_sales_price) as sales,
         sum(ss_net_profit) as profit
 from store_sales,
      date_dim,
      store
 where ss_sold_date_sk = d_date_sk
       and d_date between cast('1998-08-29' as date) 
                  and (cast('1998-08-29' as date) +  30 ) 
       and ss_store_sk = s_store_sk
 group by s_store_sk)
 ,
 sr as
 (select s_store_sk,
         sum(sr_return_amt) as returns,
         sum(sr_net_loss) as profit_loss
 from store_returns,
      date_dim,
      store
 where sr_returned_date_sk = d_date_sk
       and d_date between cast('1998-08-29' as date)
                  and (cast('1998-08-29' as date) +  30 )
       and sr_store_sk = s_store_sk
 group by s_store_sk), 
 cs as
 (select cs_call_center_sk,
        sum(cs_ext_sales_price) as sales,
        sum(cs_net_profit) as profit
 from catalog_sales,
      date_dim
 where cs_sold_date_sk = d_date_sk
       and d_date between cast('1998-08-29' as date)
                  and (cast('1998-08-29' as date) +  30 )
 group by cs_call_center_sk 
 ), 
 cr as
 (select cr_call_center_sk,
         sum(cr_return_amount) as returns,
         sum(cr_net_loss) as profit_loss
 from catalog_returns,
      date_dim
 where cr_returned_date_sk = d_date_sk
       and d_date between cast('1998-08-29' as date)
                  and (cast('1998-08-29' as date) +  30 )
 group by cr_call_center_sk
 ), 
 ws as
 ( select wp_web_page_sk,
        sum(ws_ext_sales_price) as sales,
        sum(ws_net_profit) as profit
 from web_sales,
      date_dim,
      web_page
 where ws_sold_date_sk = d_date_sk
       and d_date between cast('1998-08-29' as date)
                  and (cast('1998-08-29' as date) +  30 )
       and ws_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk), 
 wr as
 (select wp_web_page_sk,
        sum(wr_return_amt) as returns,
        sum(wr_net_loss) as profit_loss
 from web_returns,
      date_dim,
      web_page
 where wr_returned_date_sk = d_date_sk
       and d_date between cast('1998-08-29' as date)
                  and (cast('1998-08-29' as date) +  30 )
       and wr_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk)
  select  channel
        , id
        , sum(sales) as sales
        , sum(returns) as returns
        , sum(profit) as profit
 from 
 (select 'store channel' as channel
        , ss.s_store_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ss left join sr
        on  ss.s_store_sk = sr.s_store_sk
 union all
 select 'catalog channel' as channel
        , cs_call_center_sk as id
        , sales
        , returns
        , (profit - profit_loss) as profit
 from  cs
       , cr
 union all
 select 'web channel' as channel
        , ws.wp_web_page_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ws left join wr
        on  ws.wp_web_page_sk = wr.wp_web_page_sk
 ) x
 group by rollup (channel, id)
 order by channel
         ,id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ss as
 (select s_store_sk,
         sum(ss_ext_sales_price) as sales,
         sum(ss_net_profit) as profit
 from store_sales,
      date_dim,
      store
 where ss_sold_date_sk = d_date_sk
       and d_date between cast('2002-08-12' as date) 
                  and (cast('2002-08-12' as date) +  30 ) 
       and ss_store_sk = s_store_sk
 group by s_store_sk)
 ,
 sr as
 (select s_store_sk,
         sum(sr_return_amt) as returns,
         sum(sr_net_loss) as profit_loss
 from store_returns,
      date_dim,
      store
 where sr_returned_date_sk = d_date_sk
       and d_date between cast('2002-08-12' as date)
                  and (cast('2002-08-12' as date) +  30 )
       and sr_store_sk = s_store_sk
 group by s_store_sk), 
 cs as
 (select cs_call_center_sk,
        sum(cs_ext_sales_price) as sales,
        sum(cs_net_profit) as profit
 from catalog_sales,
      date_dim
 where cs_sold_date_sk = d_date_sk
       and d_date between cast('2002-08-12' as date)
                  and (cast('2002-08-12' as date) +  30 )
 group by cs_call_center_sk 
 ), 
 cr as
 (select cr_call_center_sk,
         sum(cr_return_amount) as returns,
         sum(cr_net_loss) as profit_loss
 from catalog_returns,
      date_dim
 where cr_returned_date_sk = d_date_sk
       and d_date between cast('2002-08-12' as date)
                  and (cast('2002-08-12' as date) +  30 )
 group by cr_call_center_sk
 ), 
 ws as
 ( select wp_web_page_sk,
        sum(ws_ext_sales_price) as sales,
        sum(ws_net_profit) as profit
 from web_sales,
      date_dim,
      web_page
 where ws_sold_date_sk = d_date_sk
       and d_date between cast('2002-08-12' as date)
                  and (cast('2002-08-12' as date) +  30 )
       and ws_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk), 
 wr as
 (select wp_web_page_sk,
        sum(wr_return_amt) as returns,
        sum(wr_net_loss) as profit_loss
 from web_returns,
      date_dim,
      web_page
 where wr_returned_date_sk = d_date_sk
       and d_date between cast('2002-08-12' as date)
                  and (cast('2002-08-12' as date) +  30 )
       and wr_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk)
  select  channel
        , id
        , sum(sales) as sales
        , sum(returns) as returns
        , sum(profit) as profit
 from 
 (select 'store channel' as channel
        , ss.s_store_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ss left join sr
        on  ss.s_store_sk = sr.s_store_sk
 union all
 select 'catalog channel' as channel
        , cs_call_center_sk as id
        , sales
        , returns
        , (profit - profit_loss) as profit
 from  cs
       , cr
 union all
 select 'web channel' as channel
        , ws.wp_web_page_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ws left join wr
        on  ws.wp_web_page_sk = wr.wp_web_page_sk
 ) x
 group by rollup (channel, id)
 order by channel
         ,id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ss as
 (select s_store_sk,
         sum(ss_ext_sales_price) as sales,
         sum(ss_net_profit) as profit
 from store_sales,
      date_dim,
      store
 where ss_sold_date_sk = d_date_sk
       and d_date between cast('1998-08-11' as date) 
                  and (cast('1998-08-11' as date) +  30 ) 
       and ss_store_sk = s_store_sk
 group by s_store_sk)
 ,
 sr as
 (select s_store_sk,
         sum(sr_return_amt) as returns,
         sum(sr_net_loss) as profit_loss
 from store_returns,
      date_dim,
      store
 where sr_returned_date_sk = d_date_sk
       and d_date between cast('1998-08-11' as date)
                  and (cast('1998-08-11' as date) +  30 )
       and sr_store_sk = s_store_sk
 group by s_store_sk), 
 cs as
 (select cs_call_center_sk,
        sum(cs_ext_sales_price) as sales,
        sum(cs_net_profit) as profit
 from catalog_sales,
      date_dim
 where cs_sold_date_sk = d_date_sk
       and d_date between cast('1998-08-11' as date)
                  and (cast('1998-08-11' as date) +  30 )
 group by cs_call_center_sk 
 ), 
 cr as
 (select cr_call_center_sk,
         sum(cr_return_amount) as returns,
         sum(cr_net_loss) as profit_loss
 from catalog_returns,
      date_dim
 where cr_returned_date_sk = d_date_sk
       and d_date between cast('1998-08-11' as date)
                  and (cast('1998-08-11' as date) +  30 )
 group by cr_call_center_sk
 ), 
 ws as
 ( select wp_web_page_sk,
        sum(ws_ext_sales_price) as sales,
        sum(ws_net_profit) as profit
 from web_sales,
      date_dim,
      web_page
 where ws_sold_date_sk = d_date_sk
       and d_date between cast('1998-08-11' as date)
                  and (cast('1998-08-11' as date) +  30 )
       and ws_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk), 
 wr as
 (select wp_web_page_sk,
        sum(wr_return_amt) as returns,
        sum(wr_net_loss) as profit_loss
 from web_returns,
      date_dim,
      web_page
 where wr_returned_date_sk = d_date_sk
       and d_date between cast('1998-08-11' as date)
                  and (cast('1998-08-11' as date) +  30 )
       and wr_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk)
  select  channel
        , id
        , sum(sales) as sales
        , sum(returns) as returns
        , sum(profit) as profit
 from 
 (select 'store channel' as channel
        , ss.s_store_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ss left join sr
        on  ss.s_store_sk = sr.s_store_sk
 union all
 select 'catalog channel' as channel
        , cs_call_center_sk as id
        , sales
        , returns
        , (profit - profit_loss) as profit
 from  cs
       , cr
 union all
 select 'web channel' as channel
        , ws.wp_web_page_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ws left join wr
        on  ws.wp_web_page_sk = wr.wp_web_page_sk
 ) x
 group by rollup (channel, id)
 order by channel
         ,id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ss as
 (select s_store_sk,
         sum(ss_ext_sales_price) as sales,
         sum(ss_net_profit) as profit
 from store_sales,
      date_dim,
      store
 where ss_sold_date_sk = d_date_sk
       and d_date between cast('2001-08-04' as date) 
                  and (cast('2001-08-04' as date) +  30 ) 
       and ss_store_sk = s_store_sk
 group by s_store_sk)
 ,
 sr as
 (select s_store_sk,
         sum(sr_return_amt) as returns,
         sum(sr_net_loss) as profit_loss
 from store_returns,
      date_dim,
      store
 where sr_returned_date_sk = d_date_sk
       and d_date between cast('2001-08-04' as date)
                  and (cast('2001-08-04' as date) +  30 )
       and sr_store_sk = s_store_sk
 group by s_store_sk), 
 cs as
 (select cs_call_center_sk,
        sum(cs_ext_sales_price) as sales,
        sum(cs_net_profit) as profit
 from catalog_sales,
      date_dim
 where cs_sold_date_sk = d_date_sk
       and d_date between cast('2001-08-04' as date)
                  and (cast('2001-08-04' as date) +  30 )
 group by cs_call_center_sk 
 ), 
 cr as
 (select cr_call_center_sk,
         sum(cr_return_amount) as returns,
         sum(cr_net_loss) as profit_loss
 from catalog_returns,
      date_dim
 where cr_returned_date_sk = d_date_sk
       and d_date between cast('2001-08-04' as date)
                  and (cast('2001-08-04' as date) +  30 )
 group by cr_call_center_sk
 ), 
 ws as
 ( select wp_web_page_sk,
        sum(ws_ext_sales_price) as sales,
        sum(ws_net_profit) as profit
 from web_sales,
      date_dim,
      web_page
 where ws_sold_date_sk = d_date_sk
       and d_date between cast('2001-08-04' as date)
                  and (cast('2001-08-04' as date) +  30 )
       and ws_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk), 
 wr as
 (select wp_web_page_sk,
        sum(wr_return_amt) as returns,
        sum(wr_net_loss) as profit_loss
 from web_returns,
      date_dim,
      web_page
 where wr_returned_date_sk = d_date_sk
       and d_date between cast('2001-08-04' as date)
                  and (cast('2001-08-04' as date) +  30 )
       and wr_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk)
  select  channel
        , id
        , sum(sales) as sales
        , sum(returns) as returns
        , sum(profit) as profit
 from 
 (select 'store channel' as channel
        , ss.s_store_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ss left join sr
        on  ss.s_store_sk = sr.s_store_sk
 union all
 select 'catalog channel' as channel
        , cs_call_center_sk as id
        , sales
        , returns
        , (profit - profit_loss) as profit
 from  cs
       , cr
 union all
 select 'web channel' as channel
        , ws.wp_web_page_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ws left join wr
        on  ws.wp_web_page_sk = wr.wp_web_page_sk
 ) x
 group by rollup (channel, id)
 order by channel
         ,id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ss as
 (select s_store_sk,
         sum(ss_ext_sales_price) as sales,
         sum(ss_net_profit) as profit
 from store_sales,
      date_dim,
      store
 where ss_sold_date_sk = d_date_sk
       and d_date between cast('2000-08-27' as date) 
                  and (cast('2000-08-27' as date) +  30 ) 
       and ss_store_sk = s_store_sk
 group by s_store_sk)
 ,
 sr as
 (select s_store_sk,
         sum(sr_return_amt) as returns,
         sum(sr_net_loss) as profit_loss
 from store_returns,
      date_dim,
      store
 where sr_returned_date_sk = d_date_sk
       and d_date between cast('2000-08-27' as date)
                  and (cast('2000-08-27' as date) +  30 )
       and sr_store_sk = s_store_sk
 group by s_store_sk), 
 cs as
 (select cs_call_center_sk,
        sum(cs_ext_sales_price) as sales,
        sum(cs_net_profit) as profit
 from catalog_sales,
      date_dim
 where cs_sold_date_sk = d_date_sk
       and d_date between cast('2000-08-27' as date)
                  and (cast('2000-08-27' as date) +  30 )
 group by cs_call_center_sk 
 ), 
 cr as
 (select cr_call_center_sk,
         sum(cr_return_amount) as returns,
         sum(cr_net_loss) as profit_loss
 from catalog_returns,
      date_dim
 where cr_returned_date_sk = d_date_sk
       and d_date between cast('2000-08-27' as date)
                  and (cast('2000-08-27' as date) +  30 )
 group by cr_call_center_sk
 ), 
 ws as
 ( select wp_web_page_sk,
        sum(ws_ext_sales_price) as sales,
        sum(ws_net_profit) as profit
 from web_sales,
      date_dim,
      web_page
 where ws_sold_date_sk = d_date_sk
       and d_date between cast('2000-08-27' as date)
                  and (cast('2000-08-27' as date) +  30 )
       and ws_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk), 
 wr as
 (select wp_web_page_sk,
        sum(wr_return_amt) as returns,
        sum(wr_net_loss) as profit_loss
 from web_returns,
      date_dim,
      web_page
 where wr_returned_date_sk = d_date_sk
       and d_date between cast('2000-08-27' as date)
                  and (cast('2000-08-27' as date) +  30 )
       and wr_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk)
  select  channel
        , id
        , sum(sales) as sales
        , sum(returns) as returns
        , sum(profit) as profit
 from 
 (select 'store channel' as channel
        , ss.s_store_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ss left join sr
        on  ss.s_store_sk = sr.s_store_sk
 union all
 select 'catalog channel' as channel
        , cs_call_center_sk as id
        , sales
        , returns
        , (profit - profit_loss) as profit
 from  cs
       , cr
 union all
 select 'web channel' as channel
        , ws.wp_web_page_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ws left join wr
        on  ws.wp_web_page_sk = wr.wp_web_page_sk
 ) x
 group by rollup (channel, id)
 order by channel
         ,id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ss as
 (select s_store_sk,
         sum(ss_ext_sales_price) as sales,
         sum(ss_net_profit) as profit
 from store_sales,
      date_dim,
      store
 where ss_sold_date_sk = d_date_sk
       and d_date between cast('1999-08-02' as date) 
                  and (cast('1999-08-02' as date) +  30 ) 
       and ss_store_sk = s_store_sk
 group by s_store_sk)
 ,
 sr as
 (select s_store_sk,
         sum(sr_return_amt) as returns,
         sum(sr_net_loss) as profit_loss
 from store_returns,
      date_dim,
      store
 where sr_returned_date_sk = d_date_sk
       and d_date between cast('1999-08-02' as date)
                  and (cast('1999-08-02' as date) +  30 )
       and sr_store_sk = s_store_sk
 group by s_store_sk), 
 cs as
 (select cs_call_center_sk,
        sum(cs_ext_sales_price) as sales,
        sum(cs_net_profit) as profit
 from catalog_sales,
      date_dim
 where cs_sold_date_sk = d_date_sk
       and d_date between cast('1999-08-02' as date)
                  and (cast('1999-08-02' as date) +  30 )
 group by cs_call_center_sk 
 ), 
 cr as
 (select cr_call_center_sk,
         sum(cr_return_amount) as returns,
         sum(cr_net_loss) as profit_loss
 from catalog_returns,
      date_dim
 where cr_returned_date_sk = d_date_sk
       and d_date between cast('1999-08-02' as date)
                  and (cast('1999-08-02' as date) +  30 )
 group by cr_call_center_sk
 ), 
 ws as
 ( select wp_web_page_sk,
        sum(ws_ext_sales_price) as sales,
        sum(ws_net_profit) as profit
 from web_sales,
      date_dim,
      web_page
 where ws_sold_date_sk = d_date_sk
       and d_date between cast('1999-08-02' as date)
                  and (cast('1999-08-02' as date) +  30 )
       and ws_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk), 
 wr as
 (select wp_web_page_sk,
        sum(wr_return_amt) as returns,
        sum(wr_net_loss) as profit_loss
 from web_returns,
      date_dim,
      web_page
 where wr_returned_date_sk = d_date_sk
       and d_date between cast('1999-08-02' as date)
                  and (cast('1999-08-02' as date) +  30 )
       and wr_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk)
  select  channel
        , id
        , sum(sales) as sales
        , sum(returns) as returns
        , sum(profit) as profit
 from 
 (select 'store channel' as channel
        , ss.s_store_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ss left join sr
        on  ss.s_store_sk = sr.s_store_sk
 union all
 select 'catalog channel' as channel
        , cs_call_center_sk as id
        , sales
        , returns
        , (profit - profit_loss) as profit
 from  cs
       , cr
 union all
 select 'web channel' as channel
        , ws.wp_web_page_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ws left join wr
        on  ws.wp_web_page_sk = wr.wp_web_page_sk
 ) x
 group by rollup (channel, id)
 order by channel
         ,id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ss as
 (select s_store_sk,
         sum(ss_ext_sales_price) as sales,
         sum(ss_net_profit) as profit
 from store_sales,
      date_dim,
      store
 where ss_sold_date_sk = d_date_sk
       and d_date between cast('2002-08-05' as date) 
                  and (cast('2002-08-05' as date) +  30 ) 
       and ss_store_sk = s_store_sk
 group by s_store_sk)
 ,
 sr as
 (select s_store_sk,
         sum(sr_return_amt) as returns,
         sum(sr_net_loss) as profit_loss
 from store_returns,
      date_dim,
      store
 where sr_returned_date_sk = d_date_sk
       and d_date between cast('2002-08-05' as date)
                  and (cast('2002-08-05' as date) +  30 )
       and sr_store_sk = s_store_sk
 group by s_store_sk), 
 cs as
 (select cs_call_center_sk,
        sum(cs_ext_sales_price) as sales,
        sum(cs_net_profit) as profit
 from catalog_sales,
      date_dim
 where cs_sold_date_sk = d_date_sk
       and d_date between cast('2002-08-05' as date)
                  and (cast('2002-08-05' as date) +  30 )
 group by cs_call_center_sk 
 ), 
 cr as
 (select cr_call_center_sk,
         sum(cr_return_amount) as returns,
         sum(cr_net_loss) as profit_loss
 from catalog_returns,
      date_dim
 where cr_returned_date_sk = d_date_sk
       and d_date between cast('2002-08-05' as date)
                  and (cast('2002-08-05' as date) +  30 )
 group by cr_call_center_sk
 ), 
 ws as
 ( select wp_web_page_sk,
        sum(ws_ext_sales_price) as sales,
        sum(ws_net_profit) as profit
 from web_sales,
      date_dim,
      web_page
 where ws_sold_date_sk = d_date_sk
       and d_date between cast('2002-08-05' as date)
                  and (cast('2002-08-05' as date) +  30 )
       and ws_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk), 
 wr as
 (select wp_web_page_sk,
        sum(wr_return_amt) as returns,
        sum(wr_net_loss) as profit_loss
 from web_returns,
      date_dim,
      web_page
 where wr_returned_date_sk = d_date_sk
       and d_date between cast('2002-08-05' as date)
                  and (cast('2002-08-05' as date) +  30 )
       and wr_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk)
  select  channel
        , id
        , sum(sales) as sales
        , sum(returns) as returns
        , sum(profit) as profit
 from 
 (select 'store channel' as channel
        , ss.s_store_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ss left join sr
        on  ss.s_store_sk = sr.s_store_sk
 union all
 select 'catalog channel' as channel
        , cs_call_center_sk as id
        , sales
        , returns
        , (profit - profit_loss) as profit
 from  cs
       , cr
 union all
 select 'web channel' as channel
        , ws.wp_web_page_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ws left join wr
        on  ws.wp_web_page_sk = wr.wp_web_page_sk
 ) x
 group by rollup (channel, id)
 order by channel
         ,id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ss as
 (select s_store_sk,
         sum(ss_ext_sales_price) as sales,
         sum(ss_net_profit) as profit
 from store_sales,
      date_dim,
      store
 where ss_sold_date_sk = d_date_sk
       and d_date between cast('1999-08-18' as date) 
                  and (cast('1999-08-18' as date) +  30 ) 
       and ss_store_sk = s_store_sk
 group by s_store_sk)
 ,
 sr as
 (select s_store_sk,
         sum(sr_return_amt) as returns,
         sum(sr_net_loss) as profit_loss
 from store_returns,
      date_dim,
      store
 where sr_returned_date_sk = d_date_sk
       and d_date between cast('1999-08-18' as date)
                  and (cast('1999-08-18' as date) +  30 )
       and sr_store_sk = s_store_sk
 group by s_store_sk), 
 cs as
 (select cs_call_center_sk,
        sum(cs_ext_sales_price) as sales,
        sum(cs_net_profit) as profit
 from catalog_sales,
      date_dim
 where cs_sold_date_sk = d_date_sk
       and d_date between cast('1999-08-18' as date)
                  and (cast('1999-08-18' as date) +  30 )
 group by cs_call_center_sk 
 ), 
 cr as
 (select cr_call_center_sk,
         sum(cr_return_amount) as returns,
         sum(cr_net_loss) as profit_loss
 from catalog_returns,
      date_dim
 where cr_returned_date_sk = d_date_sk
       and d_date between cast('1999-08-18' as date)
                  and (cast('1999-08-18' as date) +  30 )
 group by cr_call_center_sk
 ), 
 ws as
 ( select wp_web_page_sk,
        sum(ws_ext_sales_price) as sales,
        sum(ws_net_profit) as profit
 from web_sales,
      date_dim,
      web_page
 where ws_sold_date_sk = d_date_sk
       and d_date between cast('1999-08-18' as date)
                  and (cast('1999-08-18' as date) +  30 )
       and ws_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk), 
 wr as
 (select wp_web_page_sk,
        sum(wr_return_amt) as returns,
        sum(wr_net_loss) as profit_loss
 from web_returns,
      date_dim,
      web_page
 where wr_returned_date_sk = d_date_sk
       and d_date between cast('1999-08-18' as date)
                  and (cast('1999-08-18' as date) +  30 )
       and wr_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk)
  select  channel
        , id
        , sum(sales) as sales
        , sum(returns) as returns
        , sum(profit) as profit
 from 
 (select 'store channel' as channel
        , ss.s_store_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ss left join sr
        on  ss.s_store_sk = sr.s_store_sk
 union all
 select 'catalog channel' as channel
        , cs_call_center_sk as id
        , sales
        , returns
        , (profit - profit_loss) as profit
 from  cs
       , cr
 union all
 select 'web channel' as channel
        , ws.wp_web_page_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ws left join wr
        on  ws.wp_web_page_sk = wr.wp_web_page_sk
 ) x
 group by rollup (channel, id)
 order by channel
         ,id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ss as
 (select s_store_sk,
         sum(ss_ext_sales_price) as sales,
         sum(ss_net_profit) as profit
 from store_sales,
      date_dim,
      store
 where ss_sold_date_sk = d_date_sk
       and d_date between cast('2000-08-16' as date) 
                  and (cast('2000-08-16' as date) +  30 ) 
       and ss_store_sk = s_store_sk
 group by s_store_sk)
 ,
 sr as
 (select s_store_sk,
         sum(sr_return_amt) as returns,
         sum(sr_net_loss) as profit_loss
 from store_returns,
      date_dim,
      store
 where sr_returned_date_sk = d_date_sk
       and d_date between cast('2000-08-16' as date)
                  and (cast('2000-08-16' as date) +  30 )
       and sr_store_sk = s_store_sk
 group by s_store_sk), 
 cs as
 (select cs_call_center_sk,
        sum(cs_ext_sales_price) as sales,
        sum(cs_net_profit) as profit
 from catalog_sales,
      date_dim
 where cs_sold_date_sk = d_date_sk
       and d_date between cast('2000-08-16' as date)
                  and (cast('2000-08-16' as date) +  30 )
 group by cs_call_center_sk 
 ), 
 cr as
 (select cr_call_center_sk,
         sum(cr_return_amount) as returns,
         sum(cr_net_loss) as profit_loss
 from catalog_returns,
      date_dim
 where cr_returned_date_sk = d_date_sk
       and d_date between cast('2000-08-16' as date)
                  and (cast('2000-08-16' as date) +  30 )
 group by cr_call_center_sk
 ), 
 ws as
 ( select wp_web_page_sk,
        sum(ws_ext_sales_price) as sales,
        sum(ws_net_profit) as profit
 from web_sales,
      date_dim,
      web_page
 where ws_sold_date_sk = d_date_sk
       and d_date between cast('2000-08-16' as date)
                  and (cast('2000-08-16' as date) +  30 )
       and ws_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk), 
 wr as
 (select wp_web_page_sk,
        sum(wr_return_amt) as returns,
        sum(wr_net_loss) as profit_loss
 from web_returns,
      date_dim,
      web_page
 where wr_returned_date_sk = d_date_sk
       and d_date between cast('2000-08-16' as date)
                  and (cast('2000-08-16' as date) +  30 )
       and wr_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk)
  select  channel
        , id
        , sum(sales) as sales
        , sum(returns) as returns
        , sum(profit) as profit
 from 
 (select 'store channel' as channel
        , ss.s_store_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ss left join sr
        on  ss.s_store_sk = sr.s_store_sk
 union all
 select 'catalog channel' as channel
        , cs_call_center_sk as id
        , sales
        , returns
        , (profit - profit_loss) as profit
 from  cs
       , cr
 union all
 select 'web channel' as channel
        , ws.wp_web_page_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ws left join wr
        on  ws.wp_web_page_sk = wr.wp_web_page_sk
 ) x
 group by rollup (channel, id)
 order by channel
         ,id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ss as
 (select s_store_sk,
         sum(ss_ext_sales_price) as sales,
         sum(ss_net_profit) as profit
 from store_sales,
      date_dim,
      store
 where ss_sold_date_sk = d_date_sk
       and d_date between cast('2000-08-23' as date) 
                  and (cast('2000-08-23' as date) +  30 ) 
       and ss_store_sk = s_store_sk
 group by s_store_sk)
 ,
 sr as
 (select s_store_sk,
         sum(sr_return_amt) as returns,
         sum(sr_net_loss) as profit_loss
 from store_returns,
      date_dim,
      store
 where sr_returned_date_sk = d_date_sk
       and d_date between cast('2000-08-23' as date)
                  and (cast('2000-08-23' as date) +  30 )
       and sr_store_sk = s_store_sk
 group by s_store_sk), 
 cs as
 (select cs_call_center_sk,
        sum(cs_ext_sales_price) as sales,
        sum(cs_net_profit) as profit
 from catalog_sales,
      date_dim
 where cs_sold_date_sk = d_date_sk
       and d_date between cast('2000-08-23' as date)
                  and (cast('2000-08-23' as date) +  30 )
 group by cs_call_center_sk 
 ), 
 cr as
 (select cr_call_center_sk,
         sum(cr_return_amount) as returns,
         sum(cr_net_loss) as profit_loss
 from catalog_returns,
      date_dim
 where cr_returned_date_sk = d_date_sk
       and d_date between cast('2000-08-23' as date)
                  and (cast('2000-08-23' as date) +  30 )
 group by cr_call_center_sk
 ), 
 ws as
 ( select wp_web_page_sk,
        sum(ws_ext_sales_price) as sales,
        sum(ws_net_profit) as profit
 from web_sales,
      date_dim,
      web_page
 where ws_sold_date_sk = d_date_sk
       and d_date between cast('2000-08-23' as date)
                  and (cast('2000-08-23' as date) +  30 )
       and ws_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk), 
 wr as
 (select wp_web_page_sk,
        sum(wr_return_amt) as returns,
        sum(wr_net_loss) as profit_loss
 from web_returns,
      date_dim,
      web_page
 where wr_returned_date_sk = d_date_sk
       and d_date between cast('2000-08-23' as date)
                  and (cast('2000-08-23' as date) +  30 )
       and wr_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk)
  select  channel
        , id
        , sum(sales) as sales
        , sum(returns) as returns
        , sum(profit) as profit
 from 
 (select 'store channel' as channel
        , ss.s_store_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ss left join sr
        on  ss.s_store_sk = sr.s_store_sk
 union all
 select 'catalog channel' as channel
        , cs_call_center_sk as id
        , sales
        , returns
        , (profit - profit_loss) as profit
 from  cs
       , cr
 union all
 select 'web channel' as channel
        , ws.wp_web_page_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ws left join wr
        on  ws.wp_web_page_sk = wr.wp_web_page_sk
 ) x
 group by rollup (channel, id)
 order by channel
         ,id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ss as
 (select s_store_sk,
         sum(ss_ext_sales_price) as sales,
         sum(ss_net_profit) as profit
 from store_sales,
      date_dim,
      store
 where ss_sold_date_sk = d_date_sk
       and d_date between cast('2002-08-20' as date) 
                  and (cast('2002-08-20' as date) +  30 ) 
       and ss_store_sk = s_store_sk
 group by s_store_sk)
 ,
 sr as
 (select s_store_sk,
         sum(sr_return_amt) as returns,
         sum(sr_net_loss) as profit_loss
 from store_returns,
      date_dim,
      store
 where sr_returned_date_sk = d_date_sk
       and d_date between cast('2002-08-20' as date)
                  and (cast('2002-08-20' as date) +  30 )
       and sr_store_sk = s_store_sk
 group by s_store_sk), 
 cs as
 (select cs_call_center_sk,
        sum(cs_ext_sales_price) as sales,
        sum(cs_net_profit) as profit
 from catalog_sales,
      date_dim
 where cs_sold_date_sk = d_date_sk
       and d_date between cast('2002-08-20' as date)
                  and (cast('2002-08-20' as date) +  30 )
 group by cs_call_center_sk 
 ), 
 cr as
 (select cr_call_center_sk,
         sum(cr_return_amount) as returns,
         sum(cr_net_loss) as profit_loss
 from catalog_returns,
      date_dim
 where cr_returned_date_sk = d_date_sk
       and d_date between cast('2002-08-20' as date)
                  and (cast('2002-08-20' as date) +  30 )
 group by cr_call_center_sk
 ), 
 ws as
 ( select wp_web_page_sk,
        sum(ws_ext_sales_price) as sales,
        sum(ws_net_profit) as profit
 from web_sales,
      date_dim,
      web_page
 where ws_sold_date_sk = d_date_sk
       and d_date between cast('2002-08-20' as date)
                  and (cast('2002-08-20' as date) +  30 )
       and ws_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk), 
 wr as
 (select wp_web_page_sk,
        sum(wr_return_amt) as returns,
        sum(wr_net_loss) as profit_loss
 from web_returns,
      date_dim,
      web_page
 where wr_returned_date_sk = d_date_sk
       and d_date between cast('2002-08-20' as date)
                  and (cast('2002-08-20' as date) +  30 )
       and wr_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk)
  select  channel
        , id
        , sum(sales) as sales
        , sum(returns) as returns
        , sum(profit) as profit
 from 
 (select 'store channel' as channel
        , ss.s_store_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ss left join sr
        on  ss.s_store_sk = sr.s_store_sk
 union all
 select 'catalog channel' as channel
        , cs_call_center_sk as id
        , sales
        , returns
        , (profit - profit_loss) as profit
 from  cs
       , cr
 union all
 select 'web channel' as channel
        , ws.wp_web_page_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ws left join wr
        on  ws.wp_web_page_sk = wr.wp_web_page_sk
 ) x
 group by rollup (channel, id)
 order by channel
         ,id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ss as
 (select s_store_sk,
         sum(ss_ext_sales_price) as sales,
         sum(ss_net_profit) as profit
 from store_sales,
      date_dim,
      store
 where ss_sold_date_sk = d_date_sk
       and d_date between cast('2002-08-12' as date) 
                  and (cast('2002-08-12' as date) +  30 ) 
       and ss_store_sk = s_store_sk
 group by s_store_sk)
 ,
 sr as
 (select s_store_sk,
         sum(sr_return_amt) as returns,
         sum(sr_net_loss) as profit_loss
 from store_returns,
      date_dim,
      store
 where sr_returned_date_sk = d_date_sk
       and d_date between cast('2002-08-12' as date)
                  and (cast('2002-08-12' as date) +  30 )
       and sr_store_sk = s_store_sk
 group by s_store_sk), 
 cs as
 (select cs_call_center_sk,
        sum(cs_ext_sales_price) as sales,
        sum(cs_net_profit) as profit
 from catalog_sales,
      date_dim
 where cs_sold_date_sk = d_date_sk
       and d_date between cast('2002-08-12' as date)
                  and (cast('2002-08-12' as date) +  30 )
 group by cs_call_center_sk 
 ), 
 cr as
 (select cr_call_center_sk,
         sum(cr_return_amount) as returns,
         sum(cr_net_loss) as profit_loss
 from catalog_returns,
      date_dim
 where cr_returned_date_sk = d_date_sk
       and d_date between cast('2002-08-12' as date)
                  and (cast('2002-08-12' as date) +  30 )
 group by cr_call_center_sk
 ), 
 ws as
 ( select wp_web_page_sk,
        sum(ws_ext_sales_price) as sales,
        sum(ws_net_profit) as profit
 from web_sales,
      date_dim,
      web_page
 where ws_sold_date_sk = d_date_sk
       and d_date between cast('2002-08-12' as date)
                  and (cast('2002-08-12' as date) +  30 )
       and ws_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk), 
 wr as
 (select wp_web_page_sk,
        sum(wr_return_amt) as returns,
        sum(wr_net_loss) as profit_loss
 from web_returns,
      date_dim,
      web_page
 where wr_returned_date_sk = d_date_sk
       and d_date between cast('2002-08-12' as date)
                  and (cast('2002-08-12' as date) +  30 )
       and wr_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk)
  select  channel
        , id
        , sum(sales) as sales
        , sum(returns) as returns
        , sum(profit) as profit
 from 
 (select 'store channel' as channel
        , ss.s_store_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ss left join sr
        on  ss.s_store_sk = sr.s_store_sk
 union all
 select 'catalog channel' as channel
        , cs_call_center_sk as id
        , sales
        , returns
        , (profit - profit_loss) as profit
 from  cs
       , cr
 union all
 select 'web channel' as channel
        , ws.wp_web_page_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ws left join wr
        on  ws.wp_web_page_sk = wr.wp_web_page_sk
 ) x
 group by rollup (channel, id)
 order by channel
         ,id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ss as
 (select s_store_sk,
         sum(ss_ext_sales_price) as sales,
         sum(ss_net_profit) as profit
 from store_sales,
      date_dim,
      store
 where ss_sold_date_sk = d_date_sk
       and d_date between cast('2000-08-17' as date) 
                  and (cast('2000-08-17' as date) +  30 ) 
       and ss_store_sk = s_store_sk
 group by s_store_sk)
 ,
 sr as
 (select s_store_sk,
         sum(sr_return_amt) as returns,
         sum(sr_net_loss) as profit_loss
 from store_returns,
      date_dim,
      store
 where sr_returned_date_sk = d_date_sk
       and d_date between cast('2000-08-17' as date)
                  and (cast('2000-08-17' as date) +  30 )
       and sr_store_sk = s_store_sk
 group by s_store_sk), 
 cs as
 (select cs_call_center_sk,
        sum(cs_ext_sales_price) as sales,
        sum(cs_net_profit) as profit
 from catalog_sales,
      date_dim
 where cs_sold_date_sk = d_date_sk
       and d_date between cast('2000-08-17' as date)
                  and (cast('2000-08-17' as date) +  30 )
 group by cs_call_center_sk 
 ), 
 cr as
 (select cr_call_center_sk,
         sum(cr_return_amount) as returns,
         sum(cr_net_loss) as profit_loss
 from catalog_returns,
      date_dim
 where cr_returned_date_sk = d_date_sk
       and d_date between cast('2000-08-17' as date)
                  and (cast('2000-08-17' as date) +  30 )
 group by cr_call_center_sk
 ), 
 ws as
 ( select wp_web_page_sk,
        sum(ws_ext_sales_price) as sales,
        sum(ws_net_profit) as profit
 from web_sales,
      date_dim,
      web_page
 where ws_sold_date_sk = d_date_sk
       and d_date between cast('2000-08-17' as date)
                  and (cast('2000-08-17' as date) +  30 )
       and ws_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk), 
 wr as
 (select wp_web_page_sk,
        sum(wr_return_amt) as returns,
        sum(wr_net_loss) as profit_loss
 from web_returns,
      date_dim,
      web_page
 where wr_returned_date_sk = d_date_sk
       and d_date between cast('2000-08-17' as date)
                  and (cast('2000-08-17' as date) +  30 )
       and wr_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk)
  select  channel
        , id
        , sum(sales) as sales
        , sum(returns) as returns
        , sum(profit) as profit
 from 
 (select 'store channel' as channel
        , ss.s_store_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ss left join sr
        on  ss.s_store_sk = sr.s_store_sk
 union all
 select 'catalog channel' as channel
        , cs_call_center_sk as id
        , sales
        , returns
        , (profit - profit_loss) as profit
 from  cs
       , cr
 union all
 select 'web channel' as channel
        , ws.wp_web_page_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ws left join wr
        on  ws.wp_web_page_sk = wr.wp_web_page_sk
 ) x
 group by rollup (channel, id)
 order by channel
         ,id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ss as
 (select s_store_sk,
         sum(ss_ext_sales_price) as sales,
         sum(ss_net_profit) as profit
 from store_sales,
      date_dim,
      store
 where ss_sold_date_sk = d_date_sk
       and d_date between cast('2000-08-27' as date) 
                  and (cast('2000-08-27' as date) +  30 ) 
       and ss_store_sk = s_store_sk
 group by s_store_sk)
 ,
 sr as
 (select s_store_sk,
         sum(sr_return_amt) as returns,
         sum(sr_net_loss) as profit_loss
 from store_returns,
      date_dim,
      store
 where sr_returned_date_sk = d_date_sk
       and d_date between cast('2000-08-27' as date)
                  and (cast('2000-08-27' as date) +  30 )
       and sr_store_sk = s_store_sk
 group by s_store_sk), 
 cs as
 (select cs_call_center_sk,
        sum(cs_ext_sales_price) as sales,
        sum(cs_net_profit) as profit
 from catalog_sales,
      date_dim
 where cs_sold_date_sk = d_date_sk
       and d_date between cast('2000-08-27' as date)
                  and (cast('2000-08-27' as date) +  30 )
 group by cs_call_center_sk 
 ), 
 cr as
 (select cr_call_center_sk,
         sum(cr_return_amount) as returns,
         sum(cr_net_loss) as profit_loss
 from catalog_returns,
      date_dim
 where cr_returned_date_sk = d_date_sk
       and d_date between cast('2000-08-27' as date)
                  and (cast('2000-08-27' as date) +  30 )
 group by cr_call_center_sk
 ), 
 ws as
 ( select wp_web_page_sk,
        sum(ws_ext_sales_price) as sales,
        sum(ws_net_profit) as profit
 from web_sales,
      date_dim,
      web_page
 where ws_sold_date_sk = d_date_sk
       and d_date between cast('2000-08-27' as date)
                  and (cast('2000-08-27' as date) +  30 )
       and ws_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk), 
 wr as
 (select wp_web_page_sk,
        sum(wr_return_amt) as returns,
        sum(wr_net_loss) as profit_loss
 from web_returns,
      date_dim,
      web_page
 where wr_returned_date_sk = d_date_sk
       and d_date between cast('2000-08-27' as date)
                  and (cast('2000-08-27' as date) +  30 )
       and wr_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk)
  select  channel
        , id
        , sum(sales) as sales
        , sum(returns) as returns
        , sum(profit) as profit
 from 
 (select 'store channel' as channel
        , ss.s_store_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ss left join sr
        on  ss.s_store_sk = sr.s_store_sk
 union all
 select 'catalog channel' as channel
        , cs_call_center_sk as id
        , sales
        , returns
        , (profit - profit_loss) as profit
 from  cs
       , cr
 union all
 select 'web channel' as channel
        , ws.wp_web_page_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ws left join wr
        on  ws.wp_web_page_sk = wr.wp_web_page_sk
 ) x
 group by rollup (channel, id)
 order by channel
         ,id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ss as
 (select s_store_sk,
         sum(ss_ext_sales_price) as sales,
         sum(ss_net_profit) as profit
 from store_sales,
      date_dim,
      store
 where ss_sold_date_sk = d_date_sk
       and d_date between cast('1998-08-21' as date) 
                  and (cast('1998-08-21' as date) +  30 ) 
       and ss_store_sk = s_store_sk
 group by s_store_sk)
 ,
 sr as
 (select s_store_sk,
         sum(sr_return_amt) as returns,
         sum(sr_net_loss) as profit_loss
 from store_returns,
      date_dim,
      store
 where sr_returned_date_sk = d_date_sk
       and d_date between cast('1998-08-21' as date)
                  and (cast('1998-08-21' as date) +  30 )
       and sr_store_sk = s_store_sk
 group by s_store_sk), 
 cs as
 (select cs_call_center_sk,
        sum(cs_ext_sales_price) as sales,
        sum(cs_net_profit) as profit
 from catalog_sales,
      date_dim
 where cs_sold_date_sk = d_date_sk
       and d_date between cast('1998-08-21' as date)
                  and (cast('1998-08-21' as date) +  30 )
 group by cs_call_center_sk 
 ), 
 cr as
 (select cr_call_center_sk,
         sum(cr_return_amount) as returns,
         sum(cr_net_loss) as profit_loss
 from catalog_returns,
      date_dim
 where cr_returned_date_sk = d_date_sk
       and d_date between cast('1998-08-21' as date)
                  and (cast('1998-08-21' as date) +  30 )
 group by cr_call_center_sk
 ), 
 ws as
 ( select wp_web_page_sk,
        sum(ws_ext_sales_price) as sales,
        sum(ws_net_profit) as profit
 from web_sales,
      date_dim,
      web_page
 where ws_sold_date_sk = d_date_sk
       and d_date between cast('1998-08-21' as date)
                  and (cast('1998-08-21' as date) +  30 )
       and ws_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk), 
 wr as
 (select wp_web_page_sk,
        sum(wr_return_amt) as returns,
        sum(wr_net_loss) as profit_loss
 from web_returns,
      date_dim,
      web_page
 where wr_returned_date_sk = d_date_sk
       and d_date between cast('1998-08-21' as date)
                  and (cast('1998-08-21' as date) +  30 )
       and wr_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk)
  select  channel
        , id
        , sum(sales) as sales
        , sum(returns) as returns
        , sum(profit) as profit
 from 
 (select 'store channel' as channel
        , ss.s_store_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ss left join sr
        on  ss.s_store_sk = sr.s_store_sk
 union all
 select 'catalog channel' as channel
        , cs_call_center_sk as id
        , sales
        , returns
        , (profit - profit_loss) as profit
 from  cs
       , cr
 union all
 select 'web channel' as channel
        , ws.wp_web_page_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ws left join wr
        on  ws.wp_web_page_sk = wr.wp_web_page_sk
 ) x
 group by rollup (channel, id)
 order by channel
         ,id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ss as
 (select s_store_sk,
         sum(ss_ext_sales_price) as sales,
         sum(ss_net_profit) as profit
 from store_sales,
      date_dim,
      store
 where ss_sold_date_sk = d_date_sk
       and d_date between cast('1998-08-08' as date) 
                  and (cast('1998-08-08' as date) +  30 ) 
       and ss_store_sk = s_store_sk
 group by s_store_sk)
 ,
 sr as
 (select s_store_sk,
         sum(sr_return_amt) as returns,
         sum(sr_net_loss) as profit_loss
 from store_returns,
      date_dim,
      store
 where sr_returned_date_sk = d_date_sk
       and d_date between cast('1998-08-08' as date)
                  and (cast('1998-08-08' as date) +  30 )
       and sr_store_sk = s_store_sk
 group by s_store_sk), 
 cs as
 (select cs_call_center_sk,
        sum(cs_ext_sales_price) as sales,
        sum(cs_net_profit) as profit
 from catalog_sales,
      date_dim
 where cs_sold_date_sk = d_date_sk
       and d_date between cast('1998-08-08' as date)
                  and (cast('1998-08-08' as date) +  30 )
 group by cs_call_center_sk 
 ), 
 cr as
 (select cr_call_center_sk,
         sum(cr_return_amount) as returns,
         sum(cr_net_loss) as profit_loss
 from catalog_returns,
      date_dim
 where cr_returned_date_sk = d_date_sk
       and d_date between cast('1998-08-08' as date)
                  and (cast('1998-08-08' as date) +  30 )
 group by cr_call_center_sk
 ), 
 ws as
 ( select wp_web_page_sk,
        sum(ws_ext_sales_price) as sales,
        sum(ws_net_profit) as profit
 from web_sales,
      date_dim,
      web_page
 where ws_sold_date_sk = d_date_sk
       and d_date between cast('1998-08-08' as date)
                  and (cast('1998-08-08' as date) +  30 )
       and ws_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk), 
 wr as
 (select wp_web_page_sk,
        sum(wr_return_amt) as returns,
        sum(wr_net_loss) as profit_loss
 from web_returns,
      date_dim,
      web_page
 where wr_returned_date_sk = d_date_sk
       and d_date between cast('1998-08-08' as date)
                  and (cast('1998-08-08' as date) +  30 )
       and wr_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk)
  select  channel
        , id
        , sum(sales) as sales
        , sum(returns) as returns
        , sum(profit) as profit
 from 
 (select 'store channel' as channel
        , ss.s_store_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ss left join sr
        on  ss.s_store_sk = sr.s_store_sk
 union all
 select 'catalog channel' as channel
        , cs_call_center_sk as id
        , sales
        , returns
        , (profit - profit_loss) as profit
 from  cs
       , cr
 union all
 select 'web channel' as channel
        , ws.wp_web_page_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ws left join wr
        on  ws.wp_web_page_sk = wr.wp_web_page_sk
 ) x
 group by rollup (channel, id)
 order by channel
         ,id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ss as
 (select s_store_sk,
         sum(ss_ext_sales_price) as sales,
         sum(ss_net_profit) as profit
 from store_sales,
      date_dim,
      store
 where ss_sold_date_sk = d_date_sk
       and d_date between cast('2002-08-19' as date) 
                  and (cast('2002-08-19' as date) +  30 ) 
       and ss_store_sk = s_store_sk
 group by s_store_sk)
 ,
 sr as
 (select s_store_sk,
         sum(sr_return_amt) as returns,
         sum(sr_net_loss) as profit_loss
 from store_returns,
      date_dim,
      store
 where sr_returned_date_sk = d_date_sk
       and d_date between cast('2002-08-19' as date)
                  and (cast('2002-08-19' as date) +  30 )
       and sr_store_sk = s_store_sk
 group by s_store_sk), 
 cs as
 (select cs_call_center_sk,
        sum(cs_ext_sales_price) as sales,
        sum(cs_net_profit) as profit
 from catalog_sales,
      date_dim
 where cs_sold_date_sk = d_date_sk
       and d_date between cast('2002-08-19' as date)
                  and (cast('2002-08-19' as date) +  30 )
 group by cs_call_center_sk 
 ), 
 cr as
 (select cr_call_center_sk,
         sum(cr_return_amount) as returns,
         sum(cr_net_loss) as profit_loss
 from catalog_returns,
      date_dim
 where cr_returned_date_sk = d_date_sk
       and d_date between cast('2002-08-19' as date)
                  and (cast('2002-08-19' as date) +  30 )
 group by cr_call_center_sk
 ), 
 ws as
 ( select wp_web_page_sk,
        sum(ws_ext_sales_price) as sales,
        sum(ws_net_profit) as profit
 from web_sales,
      date_dim,
      web_page
 where ws_sold_date_sk = d_date_sk
       and d_date between cast('2002-08-19' as date)
                  and (cast('2002-08-19' as date) +  30 )
       and ws_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk), 
 wr as
 (select wp_web_page_sk,
        sum(wr_return_amt) as returns,
        sum(wr_net_loss) as profit_loss
 from web_returns,
      date_dim,
      web_page
 where wr_returned_date_sk = d_date_sk
       and d_date between cast('2002-08-19' as date)
                  and (cast('2002-08-19' as date) +  30 )
       and wr_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk)
  select  channel
        , id
        , sum(sales) as sales
        , sum(returns) as returns
        , sum(profit) as profit
 from 
 (select 'store channel' as channel
        , ss.s_store_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ss left join sr
        on  ss.s_store_sk = sr.s_store_sk
 union all
 select 'catalog channel' as channel
        , cs_call_center_sk as id
        , sales
        , returns
        , (profit - profit_loss) as profit
 from  cs
       , cr
 union all
 select 'web channel' as channel
        , ws.wp_web_page_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ws left join wr
        on  ws.wp_web_page_sk = wr.wp_web_page_sk
 ) x
 group by rollup (channel, id)
 order by channel
         ,id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ss as
 (select s_store_sk,
         sum(ss_ext_sales_price) as sales,
         sum(ss_net_profit) as profit
 from store_sales,
      date_dim,
      store
 where ss_sold_date_sk = d_date_sk
       and d_date between cast('1999-08-04' as date) 
                  and (cast('1999-08-04' as date) +  30 ) 
       and ss_store_sk = s_store_sk
 group by s_store_sk)
 ,
 sr as
 (select s_store_sk,
         sum(sr_return_amt) as returns,
         sum(sr_net_loss) as profit_loss
 from store_returns,
      date_dim,
      store
 where sr_returned_date_sk = d_date_sk
       and d_date between cast('1999-08-04' as date)
                  and (cast('1999-08-04' as date) +  30 )
       and sr_store_sk = s_store_sk
 group by s_store_sk), 
 cs as
 (select cs_call_center_sk,
        sum(cs_ext_sales_price) as sales,
        sum(cs_net_profit) as profit
 from catalog_sales,
      date_dim
 where cs_sold_date_sk = d_date_sk
       and d_date between cast('1999-08-04' as date)
                  and (cast('1999-08-04' as date) +  30 )
 group by cs_call_center_sk 
 ), 
 cr as
 (select cr_call_center_sk,
         sum(cr_return_amount) as returns,
         sum(cr_net_loss) as profit_loss
 from catalog_returns,
      date_dim
 where cr_returned_date_sk = d_date_sk
       and d_date between cast('1999-08-04' as date)
                  and (cast('1999-08-04' as date) +  30 )
 group by cr_call_center_sk
 ), 
 ws as
 ( select wp_web_page_sk,
        sum(ws_ext_sales_price) as sales,
        sum(ws_net_profit) as profit
 from web_sales,
      date_dim,
      web_page
 where ws_sold_date_sk = d_date_sk
       and d_date between cast('1999-08-04' as date)
                  and (cast('1999-08-04' as date) +  30 )
       and ws_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk), 
 wr as
 (select wp_web_page_sk,
        sum(wr_return_amt) as returns,
        sum(wr_net_loss) as profit_loss
 from web_returns,
      date_dim,
      web_page
 where wr_returned_date_sk = d_date_sk
       and d_date between cast('1999-08-04' as date)
                  and (cast('1999-08-04' as date) +  30 )
       and wr_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk)
  select  channel
        , id
        , sum(sales) as sales
        , sum(returns) as returns
        , sum(profit) as profit
 from 
 (select 'store channel' as channel
        , ss.s_store_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ss left join sr
        on  ss.s_store_sk = sr.s_store_sk
 union all
 select 'catalog channel' as channel
        , cs_call_center_sk as id
        , sales
        , returns
        , (profit - profit_loss) as profit
 from  cs
       , cr
 union all
 select 'web channel' as channel
        , ws.wp_web_page_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ws left join wr
        on  ws.wp_web_page_sk = wr.wp_web_page_sk
 ) x
 group by rollup (channel, id)
 order by channel
         ,id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ss as
 (select s_store_sk,
         sum(ss_ext_sales_price) as sales,
         sum(ss_net_profit) as profit
 from store_sales,
      date_dim,
      store
 where ss_sold_date_sk = d_date_sk
       and d_date between cast('2002-08-29' as date) 
                  and (cast('2002-08-29' as date) +  30 ) 
       and ss_store_sk = s_store_sk
 group by s_store_sk)
 ,
 sr as
 (select s_store_sk,
         sum(sr_return_amt) as returns,
         sum(sr_net_loss) as profit_loss
 from store_returns,
      date_dim,
      store
 where sr_returned_date_sk = d_date_sk
       and d_date between cast('2002-08-29' as date)
                  and (cast('2002-08-29' as date) +  30 )
       and sr_store_sk = s_store_sk
 group by s_store_sk), 
 cs as
 (select cs_call_center_sk,
        sum(cs_ext_sales_price) as sales,
        sum(cs_net_profit) as profit
 from catalog_sales,
      date_dim
 where cs_sold_date_sk = d_date_sk
       and d_date between cast('2002-08-29' as date)
                  and (cast('2002-08-29' as date) +  30 )
 group by cs_call_center_sk 
 ), 
 cr as
 (select cr_call_center_sk,
         sum(cr_return_amount) as returns,
         sum(cr_net_loss) as profit_loss
 from catalog_returns,
      date_dim
 where cr_returned_date_sk = d_date_sk
       and d_date between cast('2002-08-29' as date)
                  and (cast('2002-08-29' as date) +  30 )
 group by cr_call_center_sk
 ), 
 ws as
 ( select wp_web_page_sk,
        sum(ws_ext_sales_price) as sales,
        sum(ws_net_profit) as profit
 from web_sales,
      date_dim,
      web_page
 where ws_sold_date_sk = d_date_sk
       and d_date between cast('2002-08-29' as date)
                  and (cast('2002-08-29' as date) +  30 )
       and ws_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk), 
 wr as
 (select wp_web_page_sk,
        sum(wr_return_amt) as returns,
        sum(wr_net_loss) as profit_loss
 from web_returns,
      date_dim,
      web_page
 where wr_returned_date_sk = d_date_sk
       and d_date between cast('2002-08-29' as date)
                  and (cast('2002-08-29' as date) +  30 )
       and wr_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk)
  select  channel
        , id
        , sum(sales) as sales
        , sum(returns) as returns
        , sum(profit) as profit
 from 
 (select 'store channel' as channel
        , ss.s_store_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ss left join sr
        on  ss.s_store_sk = sr.s_store_sk
 union all
 select 'catalog channel' as channel
        , cs_call_center_sk as id
        , sales
        , returns
        , (profit - profit_loss) as profit
 from  cs
       , cr
 union all
 select 'web channel' as channel
        , ws.wp_web_page_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ws left join wr
        on  ws.wp_web_page_sk = wr.wp_web_page_sk
 ) x
 group by rollup (channel, id)
 order by channel
         ,id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ss as
 (select s_store_sk,
         sum(ss_ext_sales_price) as sales,
         sum(ss_net_profit) as profit
 from store_sales,
      date_dim,
      store
 where ss_sold_date_sk = d_date_sk
       and d_date between cast('2002-08-08' as date) 
                  and (cast('2002-08-08' as date) +  30 ) 
       and ss_store_sk = s_store_sk
 group by s_store_sk)
 ,
 sr as
 (select s_store_sk,
         sum(sr_return_amt) as returns,
         sum(sr_net_loss) as profit_loss
 from store_returns,
      date_dim,
      store
 where sr_returned_date_sk = d_date_sk
       and d_date between cast('2002-08-08' as date)
                  and (cast('2002-08-08' as date) +  30 )
       and sr_store_sk = s_store_sk
 group by s_store_sk), 
 cs as
 (select cs_call_center_sk,
        sum(cs_ext_sales_price) as sales,
        sum(cs_net_profit) as profit
 from catalog_sales,
      date_dim
 where cs_sold_date_sk = d_date_sk
       and d_date between cast('2002-08-08' as date)
                  and (cast('2002-08-08' as date) +  30 )
 group by cs_call_center_sk 
 ), 
 cr as
 (select cr_call_center_sk,
         sum(cr_return_amount) as returns,
         sum(cr_net_loss) as profit_loss
 from catalog_returns,
      date_dim
 where cr_returned_date_sk = d_date_sk
       and d_date between cast('2002-08-08' as date)
                  and (cast('2002-08-08' as date) +  30 )
 group by cr_call_center_sk
 ), 
 ws as
 ( select wp_web_page_sk,
        sum(ws_ext_sales_price) as sales,
        sum(ws_net_profit) as profit
 from web_sales,
      date_dim,
      web_page
 where ws_sold_date_sk = d_date_sk
       and d_date between cast('2002-08-08' as date)
                  and (cast('2002-08-08' as date) +  30 )
       and ws_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk), 
 wr as
 (select wp_web_page_sk,
        sum(wr_return_amt) as returns,
        sum(wr_net_loss) as profit_loss
 from web_returns,
      date_dim,
      web_page
 where wr_returned_date_sk = d_date_sk
       and d_date between cast('2002-08-08' as date)
                  and (cast('2002-08-08' as date) +  30 )
       and wr_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk)
  select  channel
        , id
        , sum(sales) as sales
        , sum(returns) as returns
        , sum(profit) as profit
 from 
 (select 'store channel' as channel
        , ss.s_store_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ss left join sr
        on  ss.s_store_sk = sr.s_store_sk
 union all
 select 'catalog channel' as channel
        , cs_call_center_sk as id
        , sales
        , returns
        , (profit - profit_loss) as profit
 from  cs
       , cr
 union all
 select 'web channel' as channel
        , ws.wp_web_page_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ws left join wr
        on  ws.wp_web_page_sk = wr.wp_web_page_sk
 ) x
 group by rollup (channel, id)
 order by channel
         ,id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ss as
 (select s_store_sk,
         sum(ss_ext_sales_price) as sales,
         sum(ss_net_profit) as profit
 from store_sales,
      date_dim,
      store
 where ss_sold_date_sk = d_date_sk
       and d_date between cast('1998-08-12' as date) 
                  and (cast('1998-08-12' as date) +  30 ) 
       and ss_store_sk = s_store_sk
 group by s_store_sk)
 ,
 sr as
 (select s_store_sk,
         sum(sr_return_amt) as returns,
         sum(sr_net_loss) as profit_loss
 from store_returns,
      date_dim,
      store
 where sr_returned_date_sk = d_date_sk
       and d_date between cast('1998-08-12' as date)
                  and (cast('1998-08-12' as date) +  30 )
       and sr_store_sk = s_store_sk
 group by s_store_sk), 
 cs as
 (select cs_call_center_sk,
        sum(cs_ext_sales_price) as sales,
        sum(cs_net_profit) as profit
 from catalog_sales,
      date_dim
 where cs_sold_date_sk = d_date_sk
       and d_date between cast('1998-08-12' as date)
                  and (cast('1998-08-12' as date) +  30 )
 group by cs_call_center_sk 
 ), 
 cr as
 (select cr_call_center_sk,
         sum(cr_return_amount) as returns,
         sum(cr_net_loss) as profit_loss
 from catalog_returns,
      date_dim
 where cr_returned_date_sk = d_date_sk
       and d_date between cast('1998-08-12' as date)
                  and (cast('1998-08-12' as date) +  30 )
 group by cr_call_center_sk
 ), 
 ws as
 ( select wp_web_page_sk,
        sum(ws_ext_sales_price) as sales,
        sum(ws_net_profit) as profit
 from web_sales,
      date_dim,
      web_page
 where ws_sold_date_sk = d_date_sk
       and d_date between cast('1998-08-12' as date)
                  and (cast('1998-08-12' as date) +  30 )
       and ws_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk), 
 wr as
 (select wp_web_page_sk,
        sum(wr_return_amt) as returns,
        sum(wr_net_loss) as profit_loss
 from web_returns,
      date_dim,
      web_page
 where wr_returned_date_sk = d_date_sk
       and d_date between cast('1998-08-12' as date)
                  and (cast('1998-08-12' as date) +  30 )
       and wr_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk)
  select  channel
        , id
        , sum(sales) as sales
        , sum(returns) as returns
        , sum(profit) as profit
 from 
 (select 'store channel' as channel
        , ss.s_store_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ss left join sr
        on  ss.s_store_sk = sr.s_store_sk
 union all
 select 'catalog channel' as channel
        , cs_call_center_sk as id
        , sales
        , returns
        , (profit - profit_loss) as profit
 from  cs
       , cr
 union all
 select 'web channel' as channel
        , ws.wp_web_page_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ws left join wr
        on  ws.wp_web_page_sk = wr.wp_web_page_sk
 ) x
 group by rollup (channel, id)
 order by channel
         ,id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ss as
 (select s_store_sk,
         sum(ss_ext_sales_price) as sales,
         sum(ss_net_profit) as profit
 from store_sales,
      date_dim,
      store
 where ss_sold_date_sk = d_date_sk
       and d_date between cast('2002-08-23' as date) 
                  and (cast('2002-08-23' as date) +  30 ) 
       and ss_store_sk = s_store_sk
 group by s_store_sk)
 ,
 sr as
 (select s_store_sk,
         sum(sr_return_amt) as returns,
         sum(sr_net_loss) as profit_loss
 from store_returns,
      date_dim,
      store
 where sr_returned_date_sk = d_date_sk
       and d_date between cast('2002-08-23' as date)
                  and (cast('2002-08-23' as date) +  30 )
       and sr_store_sk = s_store_sk
 group by s_store_sk), 
 cs as
 (select cs_call_center_sk,
        sum(cs_ext_sales_price) as sales,
        sum(cs_net_profit) as profit
 from catalog_sales,
      date_dim
 where cs_sold_date_sk = d_date_sk
       and d_date between cast('2002-08-23' as date)
                  and (cast('2002-08-23' as date) +  30 )
 group by cs_call_center_sk 
 ), 
 cr as
 (select cr_call_center_sk,
         sum(cr_return_amount) as returns,
         sum(cr_net_loss) as profit_loss
 from catalog_returns,
      date_dim
 where cr_returned_date_sk = d_date_sk
       and d_date between cast('2002-08-23' as date)
                  and (cast('2002-08-23' as date) +  30 )
 group by cr_call_center_sk
 ), 
 ws as
 ( select wp_web_page_sk,
        sum(ws_ext_sales_price) as sales,
        sum(ws_net_profit) as profit
 from web_sales,
      date_dim,
      web_page
 where ws_sold_date_sk = d_date_sk
       and d_date between cast('2002-08-23' as date)
                  and (cast('2002-08-23' as date) +  30 )
       and ws_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk), 
 wr as
 (select wp_web_page_sk,
        sum(wr_return_amt) as returns,
        sum(wr_net_loss) as profit_loss
 from web_returns,
      date_dim,
      web_page
 where wr_returned_date_sk = d_date_sk
       and d_date between cast('2002-08-23' as date)
                  and (cast('2002-08-23' as date) +  30 )
       and wr_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk)
  select  channel
        , id
        , sum(sales) as sales
        , sum(returns) as returns
        , sum(profit) as profit
 from 
 (select 'store channel' as channel
        , ss.s_store_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ss left join sr
        on  ss.s_store_sk = sr.s_store_sk
 union all
 select 'catalog channel' as channel
        , cs_call_center_sk as id
        , sales
        , returns
        , (profit - profit_loss) as profit
 from  cs
       , cr
 union all
 select 'web channel' as channel
        , ws.wp_web_page_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ws left join wr
        on  ws.wp_web_page_sk = wr.wp_web_page_sk
 ) x
 group by rollup (channel, id)
 order by channel
         ,id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ss as
 (select s_store_sk,
         sum(ss_ext_sales_price) as sales,
         sum(ss_net_profit) as profit
 from store_sales,
      date_dim,
      store
 where ss_sold_date_sk = d_date_sk
       and d_date between cast('2000-08-17' as date) 
                  and (cast('2000-08-17' as date) +  30 ) 
       and ss_store_sk = s_store_sk
 group by s_store_sk)
 ,
 sr as
 (select s_store_sk,
         sum(sr_return_amt) as returns,
         sum(sr_net_loss) as profit_loss
 from store_returns,
      date_dim,
      store
 where sr_returned_date_sk = d_date_sk
       and d_date between cast('2000-08-17' as date)
                  and (cast('2000-08-17' as date) +  30 )
       and sr_store_sk = s_store_sk
 group by s_store_sk), 
 cs as
 (select cs_call_center_sk,
        sum(cs_ext_sales_price) as sales,
        sum(cs_net_profit) as profit
 from catalog_sales,
      date_dim
 where cs_sold_date_sk = d_date_sk
       and d_date between cast('2000-08-17' as date)
                  and (cast('2000-08-17' as date) +  30 )
 group by cs_call_center_sk 
 ), 
 cr as
 (select cr_call_center_sk,
         sum(cr_return_amount) as returns,
         sum(cr_net_loss) as profit_loss
 from catalog_returns,
      date_dim
 where cr_returned_date_sk = d_date_sk
       and d_date between cast('2000-08-17' as date)
                  and (cast('2000-08-17' as date) +  30 )
 group by cr_call_center_sk
 ), 
 ws as
 ( select wp_web_page_sk,
        sum(ws_ext_sales_price) as sales,
        sum(ws_net_profit) as profit
 from web_sales,
      date_dim,
      web_page
 where ws_sold_date_sk = d_date_sk
       and d_date between cast('2000-08-17' as date)
                  and (cast('2000-08-17' as date) +  30 )
       and ws_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk), 
 wr as
 (select wp_web_page_sk,
        sum(wr_return_amt) as returns,
        sum(wr_net_loss) as profit_loss
 from web_returns,
      date_dim,
      web_page
 where wr_returned_date_sk = d_date_sk
       and d_date between cast('2000-08-17' as date)
                  and (cast('2000-08-17' as date) +  30 )
       and wr_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk)
  select  channel
        , id
        , sum(sales) as sales
        , sum(returns) as returns
        , sum(profit) as profit
 from 
 (select 'store channel' as channel
        , ss.s_store_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ss left join sr
        on  ss.s_store_sk = sr.s_store_sk
 union all
 select 'catalog channel' as channel
        , cs_call_center_sk as id
        , sales
        , returns
        , (profit - profit_loss) as profit
 from  cs
       , cr
 union all
 select 'web channel' as channel
        , ws.wp_web_page_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ws left join wr
        on  ws.wp_web_page_sk = wr.wp_web_page_sk
 ) x
 group by rollup (channel, id)
 order by channel
         ,id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ss as
 (select s_store_sk,
         sum(ss_ext_sales_price) as sales,
         sum(ss_net_profit) as profit
 from store_sales,
      date_dim,
      store
 where ss_sold_date_sk = d_date_sk
       and d_date between cast('1998-08-22' as date) 
                  and (cast('1998-08-22' as date) +  30 ) 
       and ss_store_sk = s_store_sk
 group by s_store_sk)
 ,
 sr as
 (select s_store_sk,
         sum(sr_return_amt) as returns,
         sum(sr_net_loss) as profit_loss
 from store_returns,
      date_dim,
      store
 where sr_returned_date_sk = d_date_sk
       and d_date between cast('1998-08-22' as date)
                  and (cast('1998-08-22' as date) +  30 )
       and sr_store_sk = s_store_sk
 group by s_store_sk), 
 cs as
 (select cs_call_center_sk,
        sum(cs_ext_sales_price) as sales,
        sum(cs_net_profit) as profit
 from catalog_sales,
      date_dim
 where cs_sold_date_sk = d_date_sk
       and d_date between cast('1998-08-22' as date)
                  and (cast('1998-08-22' as date) +  30 )
 group by cs_call_center_sk 
 ), 
 cr as
 (select cr_call_center_sk,
         sum(cr_return_amount) as returns,
         sum(cr_net_loss) as profit_loss
 from catalog_returns,
      date_dim
 where cr_returned_date_sk = d_date_sk
       and d_date between cast('1998-08-22' as date)
                  and (cast('1998-08-22' as date) +  30 )
 group by cr_call_center_sk
 ), 
 ws as
 ( select wp_web_page_sk,
        sum(ws_ext_sales_price) as sales,
        sum(ws_net_profit) as profit
 from web_sales,
      date_dim,
      web_page
 where ws_sold_date_sk = d_date_sk
       and d_date between cast('1998-08-22' as date)
                  and (cast('1998-08-22' as date) +  30 )
       and ws_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk), 
 wr as
 (select wp_web_page_sk,
        sum(wr_return_amt) as returns,
        sum(wr_net_loss) as profit_loss
 from web_returns,
      date_dim,
      web_page
 where wr_returned_date_sk = d_date_sk
       and d_date between cast('1998-08-22' as date)
                  and (cast('1998-08-22' as date) +  30 )
       and wr_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk)
  select  channel
        , id
        , sum(sales) as sales
        , sum(returns) as returns
        , sum(profit) as profit
 from 
 (select 'store channel' as channel
        , ss.s_store_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ss left join sr
        on  ss.s_store_sk = sr.s_store_sk
 union all
 select 'catalog channel' as channel
        , cs_call_center_sk as id
        , sales
        , returns
        , (profit - profit_loss) as profit
 from  cs
       , cr
 union all
 select 'web channel' as channel
        , ws.wp_web_page_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ws left join wr
        on  ws.wp_web_page_sk = wr.wp_web_page_sk
 ) x
 group by rollup (channel, id)
 order by channel
         ,id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ss as
 (select s_store_sk,
         sum(ss_ext_sales_price) as sales,
         sum(ss_net_profit) as profit
 from store_sales,
      date_dim,
      store
 where ss_sold_date_sk = d_date_sk
       and d_date between cast('2001-08-06' as date) 
                  and (cast('2001-08-06' as date) +  30 ) 
       and ss_store_sk = s_store_sk
 group by s_store_sk)
 ,
 sr as
 (select s_store_sk,
         sum(sr_return_amt) as returns,
         sum(sr_net_loss) as profit_loss
 from store_returns,
      date_dim,
      store
 where sr_returned_date_sk = d_date_sk
       and d_date between cast('2001-08-06' as date)
                  and (cast('2001-08-06' as date) +  30 )
       and sr_store_sk = s_store_sk
 group by s_store_sk), 
 cs as
 (select cs_call_center_sk,
        sum(cs_ext_sales_price) as sales,
        sum(cs_net_profit) as profit
 from catalog_sales,
      date_dim
 where cs_sold_date_sk = d_date_sk
       and d_date between cast('2001-08-06' as date)
                  and (cast('2001-08-06' as date) +  30 )
 group by cs_call_center_sk 
 ), 
 cr as
 (select cr_call_center_sk,
         sum(cr_return_amount) as returns,
         sum(cr_net_loss) as profit_loss
 from catalog_returns,
      date_dim
 where cr_returned_date_sk = d_date_sk
       and d_date between cast('2001-08-06' as date)
                  and (cast('2001-08-06' as date) +  30 )
 group by cr_call_center_sk
 ), 
 ws as
 ( select wp_web_page_sk,
        sum(ws_ext_sales_price) as sales,
        sum(ws_net_profit) as profit
 from web_sales,
      date_dim,
      web_page
 where ws_sold_date_sk = d_date_sk
       and d_date between cast('2001-08-06' as date)
                  and (cast('2001-08-06' as date) +  30 )
       and ws_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk), 
 wr as
 (select wp_web_page_sk,
        sum(wr_return_amt) as returns,
        sum(wr_net_loss) as profit_loss
 from web_returns,
      date_dim,
      web_page
 where wr_returned_date_sk = d_date_sk
       and d_date between cast('2001-08-06' as date)
                  and (cast('2001-08-06' as date) +  30 )
       and wr_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk)
  select  channel
        , id
        , sum(sales) as sales
        , sum(returns) as returns
        , sum(profit) as profit
 from 
 (select 'store channel' as channel
        , ss.s_store_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ss left join sr
        on  ss.s_store_sk = sr.s_store_sk
 union all
 select 'catalog channel' as channel
        , cs_call_center_sk as id
        , sales
        , returns
        , (profit - profit_loss) as profit
 from  cs
       , cr
 union all
 select 'web channel' as channel
        , ws.wp_web_page_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ws left join wr
        on  ws.wp_web_page_sk = wr.wp_web_page_sk
 ) x
 group by rollup (channel, id)
 order by channel
         ,id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ss as
 (select s_store_sk,
         sum(ss_ext_sales_price) as sales,
         sum(ss_net_profit) as profit
 from store_sales,
      date_dim,
      store
 where ss_sold_date_sk = d_date_sk
       and d_date between cast('2000-08-08' as date) 
                  and (cast('2000-08-08' as date) +  30 ) 
       and ss_store_sk = s_store_sk
 group by s_store_sk)
 ,
 sr as
 (select s_store_sk,
         sum(sr_return_amt) as returns,
         sum(sr_net_loss) as profit_loss
 from store_returns,
      date_dim,
      store
 where sr_returned_date_sk = d_date_sk
       and d_date between cast('2000-08-08' as date)
                  and (cast('2000-08-08' as date) +  30 )
       and sr_store_sk = s_store_sk
 group by s_store_sk), 
 cs as
 (select cs_call_center_sk,
        sum(cs_ext_sales_price) as sales,
        sum(cs_net_profit) as profit
 from catalog_sales,
      date_dim
 where cs_sold_date_sk = d_date_sk
       and d_date between cast('2000-08-08' as date)
                  and (cast('2000-08-08' as date) +  30 )
 group by cs_call_center_sk 
 ), 
 cr as
 (select cr_call_center_sk,
         sum(cr_return_amount) as returns,
         sum(cr_net_loss) as profit_loss
 from catalog_returns,
      date_dim
 where cr_returned_date_sk = d_date_sk
       and d_date between cast('2000-08-08' as date)
                  and (cast('2000-08-08' as date) +  30 )
 group by cr_call_center_sk
 ), 
 ws as
 ( select wp_web_page_sk,
        sum(ws_ext_sales_price) as sales,
        sum(ws_net_profit) as profit
 from web_sales,
      date_dim,
      web_page
 where ws_sold_date_sk = d_date_sk
       and d_date between cast('2000-08-08' as date)
                  and (cast('2000-08-08' as date) +  30 )
       and ws_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk), 
 wr as
 (select wp_web_page_sk,
        sum(wr_return_amt) as returns,
        sum(wr_net_loss) as profit_loss
 from web_returns,
      date_dim,
      web_page
 where wr_returned_date_sk = d_date_sk
       and d_date between cast('2000-08-08' as date)
                  and (cast('2000-08-08' as date) +  30 )
       and wr_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk)
  select  channel
        , id
        , sum(sales) as sales
        , sum(returns) as returns
        , sum(profit) as profit
 from 
 (select 'store channel' as channel
        , ss.s_store_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ss left join sr
        on  ss.s_store_sk = sr.s_store_sk
 union all
 select 'catalog channel' as channel
        , cs_call_center_sk as id
        , sales
        , returns
        , (profit - profit_loss) as profit
 from  cs
       , cr
 union all
 select 'web channel' as channel
        , ws.wp_web_page_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ws left join wr
        on  ws.wp_web_page_sk = wr.wp_web_page_sk
 ) x
 group by rollup (channel, id)
 order by channel
         ,id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ss as
 (select s_store_sk,
         sum(ss_ext_sales_price) as sales,
         sum(ss_net_profit) as profit
 from store_sales,
      date_dim,
      store
 where ss_sold_date_sk = d_date_sk
       and d_date between cast('2000-08-27' as date) 
                  and (cast('2000-08-27' as date) +  30 ) 
       and ss_store_sk = s_store_sk
 group by s_store_sk)
 ,
 sr as
 (select s_store_sk,
         sum(sr_return_amt) as returns,
         sum(sr_net_loss) as profit_loss
 from store_returns,
      date_dim,
      store
 where sr_returned_date_sk = d_date_sk
       and d_date between cast('2000-08-27' as date)
                  and (cast('2000-08-27' as date) +  30 )
       and sr_store_sk = s_store_sk
 group by s_store_sk), 
 cs as
 (select cs_call_center_sk,
        sum(cs_ext_sales_price) as sales,
        sum(cs_net_profit) as profit
 from catalog_sales,
      date_dim
 where cs_sold_date_sk = d_date_sk
       and d_date between cast('2000-08-27' as date)
                  and (cast('2000-08-27' as date) +  30 )
 group by cs_call_center_sk 
 ), 
 cr as
 (select cr_call_center_sk,
         sum(cr_return_amount) as returns,
         sum(cr_net_loss) as profit_loss
 from catalog_returns,
      date_dim
 where cr_returned_date_sk = d_date_sk
       and d_date between cast('2000-08-27' as date)
                  and (cast('2000-08-27' as date) +  30 )
 group by cr_call_center_sk
 ), 
 ws as
 ( select wp_web_page_sk,
        sum(ws_ext_sales_price) as sales,
        sum(ws_net_profit) as profit
 from web_sales,
      date_dim,
      web_page
 where ws_sold_date_sk = d_date_sk
       and d_date between cast('2000-08-27' as date)
                  and (cast('2000-08-27' as date) +  30 )
       and ws_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk), 
 wr as
 (select wp_web_page_sk,
        sum(wr_return_amt) as returns,
        sum(wr_net_loss) as profit_loss
 from web_returns,
      date_dim,
      web_page
 where wr_returned_date_sk = d_date_sk
       and d_date between cast('2000-08-27' as date)
                  and (cast('2000-08-27' as date) +  30 )
       and wr_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk)
  select  channel
        , id
        , sum(sales) as sales
        , sum(returns) as returns
        , sum(profit) as profit
 from 
 (select 'store channel' as channel
        , ss.s_store_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ss left join sr
        on  ss.s_store_sk = sr.s_store_sk
 union all
 select 'catalog channel' as channel
        , cs_call_center_sk as id
        , sales
        , returns
        , (profit - profit_loss) as profit
 from  cs
       , cr
 union all
 select 'web channel' as channel
        , ws.wp_web_page_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ws left join wr
        on  ws.wp_web_page_sk = wr.wp_web_page_sk
 ) x
 group by rollup (channel, id)
 order by channel
         ,id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ss as
 (select s_store_sk,
         sum(ss_ext_sales_price) as sales,
         sum(ss_net_profit) as profit
 from store_sales,
      date_dim,
      store
 where ss_sold_date_sk = d_date_sk
       and d_date between cast('2000-08-17' as date) 
                  and (cast('2000-08-17' as date) +  30 ) 
       and ss_store_sk = s_store_sk
 group by s_store_sk)
 ,
 sr as
 (select s_store_sk,
         sum(sr_return_amt) as returns,
         sum(sr_net_loss) as profit_loss
 from store_returns,
      date_dim,
      store
 where sr_returned_date_sk = d_date_sk
       and d_date between cast('2000-08-17' as date)
                  and (cast('2000-08-17' as date) +  30 )
       and sr_store_sk = s_store_sk
 group by s_store_sk), 
 cs as
 (select cs_call_center_sk,
        sum(cs_ext_sales_price) as sales,
        sum(cs_net_profit) as profit
 from catalog_sales,
      date_dim
 where cs_sold_date_sk = d_date_sk
       and d_date between cast('2000-08-17' as date)
                  and (cast('2000-08-17' as date) +  30 )
 group by cs_call_center_sk 
 ), 
 cr as
 (select cr_call_center_sk,
         sum(cr_return_amount) as returns,
         sum(cr_net_loss) as profit_loss
 from catalog_returns,
      date_dim
 where cr_returned_date_sk = d_date_sk
       and d_date between cast('2000-08-17' as date)
                  and (cast('2000-08-17' as date) +  30 )
 group by cr_call_center_sk
 ), 
 ws as
 ( select wp_web_page_sk,
        sum(ws_ext_sales_price) as sales,
        sum(ws_net_profit) as profit
 from web_sales,
      date_dim,
      web_page
 where ws_sold_date_sk = d_date_sk
       and d_date between cast('2000-08-17' as date)
                  and (cast('2000-08-17' as date) +  30 )
       and ws_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk), 
 wr as
 (select wp_web_page_sk,
        sum(wr_return_amt) as returns,
        sum(wr_net_loss) as profit_loss
 from web_returns,
      date_dim,
      web_page
 where wr_returned_date_sk = d_date_sk
       and d_date between cast('2000-08-17' as date)
                  and (cast('2000-08-17' as date) +  30 )
       and wr_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk)
  select  channel
        , id
        , sum(sales) as sales
        , sum(returns) as returns
        , sum(profit) as profit
 from 
 (select 'store channel' as channel
        , ss.s_store_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ss left join sr
        on  ss.s_store_sk = sr.s_store_sk
 union all
 select 'catalog channel' as channel
        , cs_call_center_sk as id
        , sales
        , returns
        , (profit - profit_loss) as profit
 from  cs
       , cr
 union all
 select 'web channel' as channel
        , ws.wp_web_page_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ws left join wr
        on  ws.wp_web_page_sk = wr.wp_web_page_sk
 ) x
 group by rollup (channel, id)
 order by channel
         ,id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ss as
 (select s_store_sk,
         sum(ss_ext_sales_price) as sales,
         sum(ss_net_profit) as profit
 from store_sales,
      date_dim,
      store
 where ss_sold_date_sk = d_date_sk
       and d_date between cast('2002-08-03' as date) 
                  and (cast('2002-08-03' as date) +  30 ) 
       and ss_store_sk = s_store_sk
 group by s_store_sk)
 ,
 sr as
 (select s_store_sk,
         sum(sr_return_amt) as returns,
         sum(sr_net_loss) as profit_loss
 from store_returns,
      date_dim,
      store
 where sr_returned_date_sk = d_date_sk
       and d_date between cast('2002-08-03' as date)
                  and (cast('2002-08-03' as date) +  30 )
       and sr_store_sk = s_store_sk
 group by s_store_sk), 
 cs as
 (select cs_call_center_sk,
        sum(cs_ext_sales_price) as sales,
        sum(cs_net_profit) as profit
 from catalog_sales,
      date_dim
 where cs_sold_date_sk = d_date_sk
       and d_date between cast('2002-08-03' as date)
                  and (cast('2002-08-03' as date) +  30 )
 group by cs_call_center_sk 
 ), 
 cr as
 (select cr_call_center_sk,
         sum(cr_return_amount) as returns,
         sum(cr_net_loss) as profit_loss
 from catalog_returns,
      date_dim
 where cr_returned_date_sk = d_date_sk
       and d_date between cast('2002-08-03' as date)
                  and (cast('2002-08-03' as date) +  30 )
 group by cr_call_center_sk
 ), 
 ws as
 ( select wp_web_page_sk,
        sum(ws_ext_sales_price) as sales,
        sum(ws_net_profit) as profit
 from web_sales,
      date_dim,
      web_page
 where ws_sold_date_sk = d_date_sk
       and d_date between cast('2002-08-03' as date)
                  and (cast('2002-08-03' as date) +  30 )
       and ws_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk), 
 wr as
 (select wp_web_page_sk,
        sum(wr_return_amt) as returns,
        sum(wr_net_loss) as profit_loss
 from web_returns,
      date_dim,
      web_page
 where wr_returned_date_sk = d_date_sk
       and d_date between cast('2002-08-03' as date)
                  and (cast('2002-08-03' as date) +  30 )
       and wr_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk)
  select  channel
        , id
        , sum(sales) as sales
        , sum(returns) as returns
        , sum(profit) as profit
 from 
 (select 'store channel' as channel
        , ss.s_store_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ss left join sr
        on  ss.s_store_sk = sr.s_store_sk
 union all
 select 'catalog channel' as channel
        , cs_call_center_sk as id
        , sales
        , returns
        , (profit - profit_loss) as profit
 from  cs
       , cr
 union all
 select 'web channel' as channel
        , ws.wp_web_page_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ws left join wr
        on  ws.wp_web_page_sk = wr.wp_web_page_sk
 ) x
 group by rollup (channel, id)
 order by channel
         ,id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ss as
 (select s_store_sk,
         sum(ss_ext_sales_price) as sales,
         sum(ss_net_profit) as profit
 from store_sales,
      date_dim,
      store
 where ss_sold_date_sk = d_date_sk
       and d_date between cast('1999-08-08' as date) 
                  and (cast('1999-08-08' as date) +  30 ) 
       and ss_store_sk = s_store_sk
 group by s_store_sk)
 ,
 sr as
 (select s_store_sk,
         sum(sr_return_amt) as returns,
         sum(sr_net_loss) as profit_loss
 from store_returns,
      date_dim,
      store
 where sr_returned_date_sk = d_date_sk
       and d_date between cast('1999-08-08' as date)
                  and (cast('1999-08-08' as date) +  30 )
       and sr_store_sk = s_store_sk
 group by s_store_sk), 
 cs as
 (select cs_call_center_sk,
        sum(cs_ext_sales_price) as sales,
        sum(cs_net_profit) as profit
 from catalog_sales,
      date_dim
 where cs_sold_date_sk = d_date_sk
       and d_date between cast('1999-08-08' as date)
                  and (cast('1999-08-08' as date) +  30 )
 group by cs_call_center_sk 
 ), 
 cr as
 (select cr_call_center_sk,
         sum(cr_return_amount) as returns,
         sum(cr_net_loss) as profit_loss
 from catalog_returns,
      date_dim
 where cr_returned_date_sk = d_date_sk
       and d_date between cast('1999-08-08' as date)
                  and (cast('1999-08-08' as date) +  30 )
 group by cr_call_center_sk
 ), 
 ws as
 ( select wp_web_page_sk,
        sum(ws_ext_sales_price) as sales,
        sum(ws_net_profit) as profit
 from web_sales,
      date_dim,
      web_page
 where ws_sold_date_sk = d_date_sk
       and d_date between cast('1999-08-08' as date)
                  and (cast('1999-08-08' as date) +  30 )
       and ws_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk), 
 wr as
 (select wp_web_page_sk,
        sum(wr_return_amt) as returns,
        sum(wr_net_loss) as profit_loss
 from web_returns,
      date_dim,
      web_page
 where wr_returned_date_sk = d_date_sk
       and d_date between cast('1999-08-08' as date)
                  and (cast('1999-08-08' as date) +  30 )
       and wr_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk)
  select  channel
        , id
        , sum(sales) as sales
        , sum(returns) as returns
        , sum(profit) as profit
 from 
 (select 'store channel' as channel
        , ss.s_store_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ss left join sr
        on  ss.s_store_sk = sr.s_store_sk
 union all
 select 'catalog channel' as channel
        , cs_call_center_sk as id
        , sales
        , returns
        , (profit - profit_loss) as profit
 from  cs
       , cr
 union all
 select 'web channel' as channel
        , ws.wp_web_page_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ws left join wr
        on  ws.wp_web_page_sk = wr.wp_web_page_sk
 ) x
 group by rollup (channel, id)
 order by channel
         ,id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ss as
 (select s_store_sk,
         sum(ss_ext_sales_price) as sales,
         sum(ss_net_profit) as profit
 from store_sales,
      date_dim,
      store
 where ss_sold_date_sk = d_date_sk
       and d_date between cast('2002-08-29' as date) 
                  and (cast('2002-08-29' as date) +  30 ) 
       and ss_store_sk = s_store_sk
 group by s_store_sk)
 ,
 sr as
 (select s_store_sk,
         sum(sr_return_amt) as returns,
         sum(sr_net_loss) as profit_loss
 from store_returns,
      date_dim,
      store
 where sr_returned_date_sk = d_date_sk
       and d_date between cast('2002-08-29' as date)
                  and (cast('2002-08-29' as date) +  30 )
       and sr_store_sk = s_store_sk
 group by s_store_sk), 
 cs as
 (select cs_call_center_sk,
        sum(cs_ext_sales_price) as sales,
        sum(cs_net_profit) as profit
 from catalog_sales,
      date_dim
 where cs_sold_date_sk = d_date_sk
       and d_date between cast('2002-08-29' as date)
                  and (cast('2002-08-29' as date) +  30 )
 group by cs_call_center_sk 
 ), 
 cr as
 (select cr_call_center_sk,
         sum(cr_return_amount) as returns,
         sum(cr_net_loss) as profit_loss
 from catalog_returns,
      date_dim
 where cr_returned_date_sk = d_date_sk
       and d_date between cast('2002-08-29' as date)
                  and (cast('2002-08-29' as date) +  30 )
 group by cr_call_center_sk
 ), 
 ws as
 ( select wp_web_page_sk,
        sum(ws_ext_sales_price) as sales,
        sum(ws_net_profit) as profit
 from web_sales,
      date_dim,
      web_page
 where ws_sold_date_sk = d_date_sk
       and d_date between cast('2002-08-29' as date)
                  and (cast('2002-08-29' as date) +  30 )
       and ws_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk), 
 wr as
 (select wp_web_page_sk,
        sum(wr_return_amt) as returns,
        sum(wr_net_loss) as profit_loss
 from web_returns,
      date_dim,
      web_page
 where wr_returned_date_sk = d_date_sk
       and d_date between cast('2002-08-29' as date)
                  and (cast('2002-08-29' as date) +  30 )
       and wr_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk)
  select  channel
        , id
        , sum(sales) as sales
        , sum(returns) as returns
        , sum(profit) as profit
 from 
 (select 'store channel' as channel
        , ss.s_store_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ss left join sr
        on  ss.s_store_sk = sr.s_store_sk
 union all
 select 'catalog channel' as channel
        , cs_call_center_sk as id
        , sales
        , returns
        , (profit - profit_loss) as profit
 from  cs
       , cr
 union all
 select 'web channel' as channel
        , ws.wp_web_page_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ws left join wr
        on  ws.wp_web_page_sk = wr.wp_web_page_sk
 ) x
 group by rollup (channel, id)
 order by channel
         ,id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ss as
 (select s_store_sk,
         sum(ss_ext_sales_price) as sales,
         sum(ss_net_profit) as profit
 from store_sales,
      date_dim,
      store
 where ss_sold_date_sk = d_date_sk
       and d_date between cast('2001-08-12' as date) 
                  and (cast('2001-08-12' as date) +  30 ) 
       and ss_store_sk = s_store_sk
 group by s_store_sk)
 ,
 sr as
 (select s_store_sk,
         sum(sr_return_amt) as returns,
         sum(sr_net_loss) as profit_loss
 from store_returns,
      date_dim,
      store
 where sr_returned_date_sk = d_date_sk
       and d_date between cast('2001-08-12' as date)
                  and (cast('2001-08-12' as date) +  30 )
       and sr_store_sk = s_store_sk
 group by s_store_sk), 
 cs as
 (select cs_call_center_sk,
        sum(cs_ext_sales_price) as sales,
        sum(cs_net_profit) as profit
 from catalog_sales,
      date_dim
 where cs_sold_date_sk = d_date_sk
       and d_date between cast('2001-08-12' as date)
                  and (cast('2001-08-12' as date) +  30 )
 group by cs_call_center_sk 
 ), 
 cr as
 (select cr_call_center_sk,
         sum(cr_return_amount) as returns,
         sum(cr_net_loss) as profit_loss
 from catalog_returns,
      date_dim
 where cr_returned_date_sk = d_date_sk
       and d_date between cast('2001-08-12' as date)
                  and (cast('2001-08-12' as date) +  30 )
 group by cr_call_center_sk
 ), 
 ws as
 ( select wp_web_page_sk,
        sum(ws_ext_sales_price) as sales,
        sum(ws_net_profit) as profit
 from web_sales,
      date_dim,
      web_page
 where ws_sold_date_sk = d_date_sk
       and d_date between cast('2001-08-12' as date)
                  and (cast('2001-08-12' as date) +  30 )
       and ws_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk), 
 wr as
 (select wp_web_page_sk,
        sum(wr_return_amt) as returns,
        sum(wr_net_loss) as profit_loss
 from web_returns,
      date_dim,
      web_page
 where wr_returned_date_sk = d_date_sk
       and d_date between cast('2001-08-12' as date)
                  and (cast('2001-08-12' as date) +  30 )
       and wr_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk)
  select  channel
        , id
        , sum(sales) as sales
        , sum(returns) as returns
        , sum(profit) as profit
 from 
 (select 'store channel' as channel
        , ss.s_store_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ss left join sr
        on  ss.s_store_sk = sr.s_store_sk
 union all
 select 'catalog channel' as channel
        , cs_call_center_sk as id
        , sales
        , returns
        , (profit - profit_loss) as profit
 from  cs
       , cr
 union all
 select 'web channel' as channel
        , ws.wp_web_page_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ws left join wr
        on  ws.wp_web_page_sk = wr.wp_web_page_sk
 ) x
 group by rollup (channel, id)
 order by channel
         ,id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ss as
 (select s_store_sk,
         sum(ss_ext_sales_price) as sales,
         sum(ss_net_profit) as profit
 from store_sales,
      date_dim,
      store
 where ss_sold_date_sk = d_date_sk
       and d_date between cast('2000-08-16' as date) 
                  and (cast('2000-08-16' as date) +  30 ) 
       and ss_store_sk = s_store_sk
 group by s_store_sk)
 ,
 sr as
 (select s_store_sk,
         sum(sr_return_amt) as returns,
         sum(sr_net_loss) as profit_loss
 from store_returns,
      date_dim,
      store
 where sr_returned_date_sk = d_date_sk
       and d_date between cast('2000-08-16' as date)
                  and (cast('2000-08-16' as date) +  30 )
       and sr_store_sk = s_store_sk
 group by s_store_sk), 
 cs as
 (select cs_call_center_sk,
        sum(cs_ext_sales_price) as sales,
        sum(cs_net_profit) as profit
 from catalog_sales,
      date_dim
 where cs_sold_date_sk = d_date_sk
       and d_date between cast('2000-08-16' as date)
                  and (cast('2000-08-16' as date) +  30 )
 group by cs_call_center_sk 
 ), 
 cr as
 (select cr_call_center_sk,
         sum(cr_return_amount) as returns,
         sum(cr_net_loss) as profit_loss
 from catalog_returns,
      date_dim
 where cr_returned_date_sk = d_date_sk
       and d_date between cast('2000-08-16' as date)
                  and (cast('2000-08-16' as date) +  30 )
 group by cr_call_center_sk
 ), 
 ws as
 ( select wp_web_page_sk,
        sum(ws_ext_sales_price) as sales,
        sum(ws_net_profit) as profit
 from web_sales,
      date_dim,
      web_page
 where ws_sold_date_sk = d_date_sk
       and d_date between cast('2000-08-16' as date)
                  and (cast('2000-08-16' as date) +  30 )
       and ws_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk), 
 wr as
 (select wp_web_page_sk,
        sum(wr_return_amt) as returns,
        sum(wr_net_loss) as profit_loss
 from web_returns,
      date_dim,
      web_page
 where wr_returned_date_sk = d_date_sk
       and d_date between cast('2000-08-16' as date)
                  and (cast('2000-08-16' as date) +  30 )
       and wr_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk)
  select  channel
        , id
        , sum(sales) as sales
        , sum(returns) as returns
        , sum(profit) as profit
 from 
 (select 'store channel' as channel
        , ss.s_store_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ss left join sr
        on  ss.s_store_sk = sr.s_store_sk
 union all
 select 'catalog channel' as channel
        , cs_call_center_sk as id
        , sales
        , returns
        , (profit - profit_loss) as profit
 from  cs
       , cr
 union all
 select 'web channel' as channel
        , ws.wp_web_page_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ws left join wr
        on  ws.wp_web_page_sk = wr.wp_web_page_sk
 ) x
 group by rollup (channel, id)
 order by channel
         ,id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ss as
 (select s_store_sk,
         sum(ss_ext_sales_price) as sales,
         sum(ss_net_profit) as profit
 from store_sales,
      date_dim,
      store
 where ss_sold_date_sk = d_date_sk
       and d_date between cast('2001-08-19' as date) 
                  and (cast('2001-08-19' as date) +  30 ) 
       and ss_store_sk = s_store_sk
 group by s_store_sk)
 ,
 sr as
 (select s_store_sk,
         sum(sr_return_amt) as returns,
         sum(sr_net_loss) as profit_loss
 from store_returns,
      date_dim,
      store
 where sr_returned_date_sk = d_date_sk
       and d_date between cast('2001-08-19' as date)
                  and (cast('2001-08-19' as date) +  30 )
       and sr_store_sk = s_store_sk
 group by s_store_sk), 
 cs as
 (select cs_call_center_sk,
        sum(cs_ext_sales_price) as sales,
        sum(cs_net_profit) as profit
 from catalog_sales,
      date_dim
 where cs_sold_date_sk = d_date_sk
       and d_date between cast('2001-08-19' as date)
                  and (cast('2001-08-19' as date) +  30 )
 group by cs_call_center_sk 
 ), 
 cr as
 (select cr_call_center_sk,
         sum(cr_return_amount) as returns,
         sum(cr_net_loss) as profit_loss
 from catalog_returns,
      date_dim
 where cr_returned_date_sk = d_date_sk
       and d_date between cast('2001-08-19' as date)
                  and (cast('2001-08-19' as date) +  30 )
 group by cr_call_center_sk
 ), 
 ws as
 ( select wp_web_page_sk,
        sum(ws_ext_sales_price) as sales,
        sum(ws_net_profit) as profit
 from web_sales,
      date_dim,
      web_page
 where ws_sold_date_sk = d_date_sk
       and d_date between cast('2001-08-19' as date)
                  and (cast('2001-08-19' as date) +  30 )
       and ws_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk), 
 wr as
 (select wp_web_page_sk,
        sum(wr_return_amt) as returns,
        sum(wr_net_loss) as profit_loss
 from web_returns,
      date_dim,
      web_page
 where wr_returned_date_sk = d_date_sk
       and d_date between cast('2001-08-19' as date)
                  and (cast('2001-08-19' as date) +  30 )
       and wr_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk)
  select  channel
        , id
        , sum(sales) as sales
        , sum(returns) as returns
        , sum(profit) as profit
 from 
 (select 'store channel' as channel
        , ss.s_store_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ss left join sr
        on  ss.s_store_sk = sr.s_store_sk
 union all
 select 'catalog channel' as channel
        , cs_call_center_sk as id
        , sales
        , returns
        , (profit - profit_loss) as profit
 from  cs
       , cr
 union all
 select 'web channel' as channel
        , ws.wp_web_page_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ws left join wr
        on  ws.wp_web_page_sk = wr.wp_web_page_sk
 ) x
 group by rollup (channel, id)
 order by channel
         ,id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ss as
 (select s_store_sk,
         sum(ss_ext_sales_price) as sales,
         sum(ss_net_profit) as profit
 from store_sales,
      date_dim,
      store
 where ss_sold_date_sk = d_date_sk
       and d_date between cast('2001-08-23' as date) 
                  and (cast('2001-08-23' as date) +  30 ) 
       and ss_store_sk = s_store_sk
 group by s_store_sk)
 ,
 sr as
 (select s_store_sk,
         sum(sr_return_amt) as returns,
         sum(sr_net_loss) as profit_loss
 from store_returns,
      date_dim,
      store
 where sr_returned_date_sk = d_date_sk
       and d_date between cast('2001-08-23' as date)
                  and (cast('2001-08-23' as date) +  30 )
       and sr_store_sk = s_store_sk
 group by s_store_sk), 
 cs as
 (select cs_call_center_sk,
        sum(cs_ext_sales_price) as sales,
        sum(cs_net_profit) as profit
 from catalog_sales,
      date_dim
 where cs_sold_date_sk = d_date_sk
       and d_date between cast('2001-08-23' as date)
                  and (cast('2001-08-23' as date) +  30 )
 group by cs_call_center_sk 
 ), 
 cr as
 (select cr_call_center_sk,
         sum(cr_return_amount) as returns,
         sum(cr_net_loss) as profit_loss
 from catalog_returns,
      date_dim
 where cr_returned_date_sk = d_date_sk
       and d_date between cast('2001-08-23' as date)
                  and (cast('2001-08-23' as date) +  30 )
 group by cr_call_center_sk
 ), 
 ws as
 ( select wp_web_page_sk,
        sum(ws_ext_sales_price) as sales,
        sum(ws_net_profit) as profit
 from web_sales,
      date_dim,
      web_page
 where ws_sold_date_sk = d_date_sk
       and d_date between cast('2001-08-23' as date)
                  and (cast('2001-08-23' as date) +  30 )
       and ws_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk), 
 wr as
 (select wp_web_page_sk,
        sum(wr_return_amt) as returns,
        sum(wr_net_loss) as profit_loss
 from web_returns,
      date_dim,
      web_page
 where wr_returned_date_sk = d_date_sk
       and d_date between cast('2001-08-23' as date)
                  and (cast('2001-08-23' as date) +  30 )
       and wr_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk)
  select  channel
        , id
        , sum(sales) as sales
        , sum(returns) as returns
        , sum(profit) as profit
 from 
 (select 'store channel' as channel
        , ss.s_store_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ss left join sr
        on  ss.s_store_sk = sr.s_store_sk
 union all
 select 'catalog channel' as channel
        , cs_call_center_sk as id
        , sales
        , returns
        , (profit - profit_loss) as profit
 from  cs
       , cr
 union all
 select 'web channel' as channel
        , ws.wp_web_page_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ws left join wr
        on  ws.wp_web_page_sk = wr.wp_web_page_sk
 ) x
 group by rollup (channel, id)
 order by channel
         ,id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ss as
 (select s_store_sk,
         sum(ss_ext_sales_price) as sales,
         sum(ss_net_profit) as profit
 from store_sales,
      date_dim,
      store
 where ss_sold_date_sk = d_date_sk
       and d_date between cast('1998-08-21' as date) 
                  and (cast('1998-08-21' as date) +  30 ) 
       and ss_store_sk = s_store_sk
 group by s_store_sk)
 ,
 sr as
 (select s_store_sk,
         sum(sr_return_amt) as returns,
         sum(sr_net_loss) as profit_loss
 from store_returns,
      date_dim,
      store
 where sr_returned_date_sk = d_date_sk
       and d_date between cast('1998-08-21' as date)
                  and (cast('1998-08-21' as date) +  30 )
       and sr_store_sk = s_store_sk
 group by s_store_sk), 
 cs as
 (select cs_call_center_sk,
        sum(cs_ext_sales_price) as sales,
        sum(cs_net_profit) as profit
 from catalog_sales,
      date_dim
 where cs_sold_date_sk = d_date_sk
       and d_date between cast('1998-08-21' as date)
                  and (cast('1998-08-21' as date) +  30 )
 group by cs_call_center_sk 
 ), 
 cr as
 (select cr_call_center_sk,
         sum(cr_return_amount) as returns,
         sum(cr_net_loss) as profit_loss
 from catalog_returns,
      date_dim
 where cr_returned_date_sk = d_date_sk
       and d_date between cast('1998-08-21' as date)
                  and (cast('1998-08-21' as date) +  30 )
 group by cr_call_center_sk
 ), 
 ws as
 ( select wp_web_page_sk,
        sum(ws_ext_sales_price) as sales,
        sum(ws_net_profit) as profit
 from web_sales,
      date_dim,
      web_page
 where ws_sold_date_sk = d_date_sk
       and d_date between cast('1998-08-21' as date)
                  and (cast('1998-08-21' as date) +  30 )
       and ws_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk), 
 wr as
 (select wp_web_page_sk,
        sum(wr_return_amt) as returns,
        sum(wr_net_loss) as profit_loss
 from web_returns,
      date_dim,
      web_page
 where wr_returned_date_sk = d_date_sk
       and d_date between cast('1998-08-21' as date)
                  and (cast('1998-08-21' as date) +  30 )
       and wr_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk)
  select  channel
        , id
        , sum(sales) as sales
        , sum(returns) as returns
        , sum(profit) as profit
 from 
 (select 'store channel' as channel
        , ss.s_store_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ss left join sr
        on  ss.s_store_sk = sr.s_store_sk
 union all
 select 'catalog channel' as channel
        , cs_call_center_sk as id
        , sales
        , returns
        , (profit - profit_loss) as profit
 from  cs
       , cr
 union all
 select 'web channel' as channel
        , ws.wp_web_page_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ws left join wr
        on  ws.wp_web_page_sk = wr.wp_web_page_sk
 ) x
 group by rollup (channel, id)
 order by channel
         ,id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ss as
 (select s_store_sk,
         sum(ss_ext_sales_price) as sales,
         sum(ss_net_profit) as profit
 from store_sales,
      date_dim,
      store
 where ss_sold_date_sk = d_date_sk
       and d_date between cast('2002-08-11' as date) 
                  and (cast('2002-08-11' as date) +  30 ) 
       and ss_store_sk = s_store_sk
 group by s_store_sk)
 ,
 sr as
 (select s_store_sk,
         sum(sr_return_amt) as returns,
         sum(sr_net_loss) as profit_loss
 from store_returns,
      date_dim,
      store
 where sr_returned_date_sk = d_date_sk
       and d_date between cast('2002-08-11' as date)
                  and (cast('2002-08-11' as date) +  30 )
       and sr_store_sk = s_store_sk
 group by s_store_sk), 
 cs as
 (select cs_call_center_sk,
        sum(cs_ext_sales_price) as sales,
        sum(cs_net_profit) as profit
 from catalog_sales,
      date_dim
 where cs_sold_date_sk = d_date_sk
       and d_date between cast('2002-08-11' as date)
                  and (cast('2002-08-11' as date) +  30 )
 group by cs_call_center_sk 
 ), 
 cr as
 (select cr_call_center_sk,
         sum(cr_return_amount) as returns,
         sum(cr_net_loss) as profit_loss
 from catalog_returns,
      date_dim
 where cr_returned_date_sk = d_date_sk
       and d_date between cast('2002-08-11' as date)
                  and (cast('2002-08-11' as date) +  30 )
 group by cr_call_center_sk
 ), 
 ws as
 ( select wp_web_page_sk,
        sum(ws_ext_sales_price) as sales,
        sum(ws_net_profit) as profit
 from web_sales,
      date_dim,
      web_page
 where ws_sold_date_sk = d_date_sk
       and d_date between cast('2002-08-11' as date)
                  and (cast('2002-08-11' as date) +  30 )
       and ws_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk), 
 wr as
 (select wp_web_page_sk,
        sum(wr_return_amt) as returns,
        sum(wr_net_loss) as profit_loss
 from web_returns,
      date_dim,
      web_page
 where wr_returned_date_sk = d_date_sk
       and d_date between cast('2002-08-11' as date)
                  and (cast('2002-08-11' as date) +  30 )
       and wr_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk)
  select  channel
        , id
        , sum(sales) as sales
        , sum(returns) as returns
        , sum(profit) as profit
 from 
 (select 'store channel' as channel
        , ss.s_store_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ss left join sr
        on  ss.s_store_sk = sr.s_store_sk
 union all
 select 'catalog channel' as channel
        , cs_call_center_sk as id
        , sales
        , returns
        , (profit - profit_loss) as profit
 from  cs
       , cr
 union all
 select 'web channel' as channel
        , ws.wp_web_page_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ws left join wr
        on  ws.wp_web_page_sk = wr.wp_web_page_sk
 ) x
 group by rollup (channel, id)
 order by channel
         ,id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ss as
 (select s_store_sk,
         sum(ss_ext_sales_price) as sales,
         sum(ss_net_profit) as profit
 from store_sales,
      date_dim,
      store
 where ss_sold_date_sk = d_date_sk
       and d_date between cast('2002-08-12' as date) 
                  and (cast('2002-08-12' as date) +  30 ) 
       and ss_store_sk = s_store_sk
 group by s_store_sk)
 ,
 sr as
 (select s_store_sk,
         sum(sr_return_amt) as returns,
         sum(sr_net_loss) as profit_loss
 from store_returns,
      date_dim,
      store
 where sr_returned_date_sk = d_date_sk
       and d_date between cast('2002-08-12' as date)
                  and (cast('2002-08-12' as date) +  30 )
       and sr_store_sk = s_store_sk
 group by s_store_sk), 
 cs as
 (select cs_call_center_sk,
        sum(cs_ext_sales_price) as sales,
        sum(cs_net_profit) as profit
 from catalog_sales,
      date_dim
 where cs_sold_date_sk = d_date_sk
       and d_date between cast('2002-08-12' as date)
                  and (cast('2002-08-12' as date) +  30 )
 group by cs_call_center_sk 
 ), 
 cr as
 (select cr_call_center_sk,
         sum(cr_return_amount) as returns,
         sum(cr_net_loss) as profit_loss
 from catalog_returns,
      date_dim
 where cr_returned_date_sk = d_date_sk
       and d_date between cast('2002-08-12' as date)
                  and (cast('2002-08-12' as date) +  30 )
 group by cr_call_center_sk
 ), 
 ws as
 ( select wp_web_page_sk,
        sum(ws_ext_sales_price) as sales,
        sum(ws_net_profit) as profit
 from web_sales,
      date_dim,
      web_page
 where ws_sold_date_sk = d_date_sk
       and d_date between cast('2002-08-12' as date)
                  and (cast('2002-08-12' as date) +  30 )
       and ws_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk), 
 wr as
 (select wp_web_page_sk,
        sum(wr_return_amt) as returns,
        sum(wr_net_loss) as profit_loss
 from web_returns,
      date_dim,
      web_page
 where wr_returned_date_sk = d_date_sk
       and d_date between cast('2002-08-12' as date)
                  and (cast('2002-08-12' as date) +  30 )
       and wr_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk)
  select  channel
        , id
        , sum(sales) as sales
        , sum(returns) as returns
        , sum(profit) as profit
 from 
 (select 'store channel' as channel
        , ss.s_store_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ss left join sr
        on  ss.s_store_sk = sr.s_store_sk
 union all
 select 'catalog channel' as channel
        , cs_call_center_sk as id
        , sales
        , returns
        , (profit - profit_loss) as profit
 from  cs
       , cr
 union all
 select 'web channel' as channel
        , ws.wp_web_page_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ws left join wr
        on  ws.wp_web_page_sk = wr.wp_web_page_sk
 ) x
 group by rollup (channel, id)
 order by channel
         ,id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ss as
 (select s_store_sk,
         sum(ss_ext_sales_price) as sales,
         sum(ss_net_profit) as profit
 from store_sales,
      date_dim,
      store
 where ss_sold_date_sk = d_date_sk
       and d_date between cast('2002-08-10' as date) 
                  and (cast('2002-08-10' as date) +  30 ) 
       and ss_store_sk = s_store_sk
 group by s_store_sk)
 ,
 sr as
 (select s_store_sk,
         sum(sr_return_amt) as returns,
         sum(sr_net_loss) as profit_loss
 from store_returns,
      date_dim,
      store
 where sr_returned_date_sk = d_date_sk
       and d_date between cast('2002-08-10' as date)
                  and (cast('2002-08-10' as date) +  30 )
       and sr_store_sk = s_store_sk
 group by s_store_sk), 
 cs as
 (select cs_call_center_sk,
        sum(cs_ext_sales_price) as sales,
        sum(cs_net_profit) as profit
 from catalog_sales,
      date_dim
 where cs_sold_date_sk = d_date_sk
       and d_date between cast('2002-08-10' as date)
                  and (cast('2002-08-10' as date) +  30 )
 group by cs_call_center_sk 
 ), 
 cr as
 (select cr_call_center_sk,
         sum(cr_return_amount) as returns,
         sum(cr_net_loss) as profit_loss
 from catalog_returns,
      date_dim
 where cr_returned_date_sk = d_date_sk
       and d_date between cast('2002-08-10' as date)
                  and (cast('2002-08-10' as date) +  30 )
 group by cr_call_center_sk
 ), 
 ws as
 ( select wp_web_page_sk,
        sum(ws_ext_sales_price) as sales,
        sum(ws_net_profit) as profit
 from web_sales,
      date_dim,
      web_page
 where ws_sold_date_sk = d_date_sk
       and d_date between cast('2002-08-10' as date)
                  and (cast('2002-08-10' as date) +  30 )
       and ws_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk), 
 wr as
 (select wp_web_page_sk,
        sum(wr_return_amt) as returns,
        sum(wr_net_loss) as profit_loss
 from web_returns,
      date_dim,
      web_page
 where wr_returned_date_sk = d_date_sk
       and d_date between cast('2002-08-10' as date)
                  and (cast('2002-08-10' as date) +  30 )
       and wr_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk)
  select  channel
        , id
        , sum(sales) as sales
        , sum(returns) as returns
        , sum(profit) as profit
 from 
 (select 'store channel' as channel
        , ss.s_store_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ss left join sr
        on  ss.s_store_sk = sr.s_store_sk
 union all
 select 'catalog channel' as channel
        , cs_call_center_sk as id
        , sales
        , returns
        , (profit - profit_loss) as profit
 from  cs
       , cr
 union all
 select 'web channel' as channel
        , ws.wp_web_page_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ws left join wr
        on  ws.wp_web_page_sk = wr.wp_web_page_sk
 ) x
 group by rollup (channel, id)
 order by channel
         ,id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ss as
 (select s_store_sk,
         sum(ss_ext_sales_price) as sales,
         sum(ss_net_profit) as profit
 from store_sales,
      date_dim,
      store
 where ss_sold_date_sk = d_date_sk
       and d_date between cast('2002-08-03' as date) 
                  and (cast('2002-08-03' as date) +  30 ) 
       and ss_store_sk = s_store_sk
 group by s_store_sk)
 ,
 sr as
 (select s_store_sk,
         sum(sr_return_amt) as returns,
         sum(sr_net_loss) as profit_loss
 from store_returns,
      date_dim,
      store
 where sr_returned_date_sk = d_date_sk
       and d_date between cast('2002-08-03' as date)
                  and (cast('2002-08-03' as date) +  30 )
       and sr_store_sk = s_store_sk
 group by s_store_sk), 
 cs as
 (select cs_call_center_sk,
        sum(cs_ext_sales_price) as sales,
        sum(cs_net_profit) as profit
 from catalog_sales,
      date_dim
 where cs_sold_date_sk = d_date_sk
       and d_date between cast('2002-08-03' as date)
                  and (cast('2002-08-03' as date) +  30 )
 group by cs_call_center_sk 
 ), 
 cr as
 (select cr_call_center_sk,
         sum(cr_return_amount) as returns,
         sum(cr_net_loss) as profit_loss
 from catalog_returns,
      date_dim
 where cr_returned_date_sk = d_date_sk
       and d_date between cast('2002-08-03' as date)
                  and (cast('2002-08-03' as date) +  30 )
 group by cr_call_center_sk
 ), 
 ws as
 ( select wp_web_page_sk,
        sum(ws_ext_sales_price) as sales,
        sum(ws_net_profit) as profit
 from web_sales,
      date_dim,
      web_page
 where ws_sold_date_sk = d_date_sk
       and d_date between cast('2002-08-03' as date)
                  and (cast('2002-08-03' as date) +  30 )
       and ws_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk), 
 wr as
 (select wp_web_page_sk,
        sum(wr_return_amt) as returns,
        sum(wr_net_loss) as profit_loss
 from web_returns,
      date_dim,
      web_page
 where wr_returned_date_sk = d_date_sk
       and d_date between cast('2002-08-03' as date)
                  and (cast('2002-08-03' as date) +  30 )
       and wr_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk)
  select  channel
        , id
        , sum(sales) as sales
        , sum(returns) as returns
        , sum(profit) as profit
 from 
 (select 'store channel' as channel
        , ss.s_store_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ss left join sr
        on  ss.s_store_sk = sr.s_store_sk
 union all
 select 'catalog channel' as channel
        , cs_call_center_sk as id
        , sales
        , returns
        , (profit - profit_loss) as profit
 from  cs
       , cr
 union all
 select 'web channel' as channel
        , ws.wp_web_page_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ws left join wr
        on  ws.wp_web_page_sk = wr.wp_web_page_sk
 ) x
 group by rollup (channel, id)
 order by channel
         ,id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ss as
 (select s_store_sk,
         sum(ss_ext_sales_price) as sales,
         sum(ss_net_profit) as profit
 from store_sales,
      date_dim,
      store
 where ss_sold_date_sk = d_date_sk
       and d_date between cast('2002-08-23' as date) 
                  and (cast('2002-08-23' as date) +  30 ) 
       and ss_store_sk = s_store_sk
 group by s_store_sk)
 ,
 sr as
 (select s_store_sk,
         sum(sr_return_amt) as returns,
         sum(sr_net_loss) as profit_loss
 from store_returns,
      date_dim,
      store
 where sr_returned_date_sk = d_date_sk
       and d_date between cast('2002-08-23' as date)
                  and (cast('2002-08-23' as date) +  30 )
       and sr_store_sk = s_store_sk
 group by s_store_sk), 
 cs as
 (select cs_call_center_sk,
        sum(cs_ext_sales_price) as sales,
        sum(cs_net_profit) as profit
 from catalog_sales,
      date_dim
 where cs_sold_date_sk = d_date_sk
       and d_date between cast('2002-08-23' as date)
                  and (cast('2002-08-23' as date) +  30 )
 group by cs_call_center_sk 
 ), 
 cr as
 (select cr_call_center_sk,
         sum(cr_return_amount) as returns,
         sum(cr_net_loss) as profit_loss
 from catalog_returns,
      date_dim
 where cr_returned_date_sk = d_date_sk
       and d_date between cast('2002-08-23' as date)
                  and (cast('2002-08-23' as date) +  30 )
 group by cr_call_center_sk
 ), 
 ws as
 ( select wp_web_page_sk,
        sum(ws_ext_sales_price) as sales,
        sum(ws_net_profit) as profit
 from web_sales,
      date_dim,
      web_page
 where ws_sold_date_sk = d_date_sk
       and d_date between cast('2002-08-23' as date)
                  and (cast('2002-08-23' as date) +  30 )
       and ws_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk), 
 wr as
 (select wp_web_page_sk,
        sum(wr_return_amt) as returns,
        sum(wr_net_loss) as profit_loss
 from web_returns,
      date_dim,
      web_page
 where wr_returned_date_sk = d_date_sk
       and d_date between cast('2002-08-23' as date)
                  and (cast('2002-08-23' as date) +  30 )
       and wr_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk)
  select  channel
        , id
        , sum(sales) as sales
        , sum(returns) as returns
        , sum(profit) as profit
 from 
 (select 'store channel' as channel
        , ss.s_store_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ss left join sr
        on  ss.s_store_sk = sr.s_store_sk
 union all
 select 'catalog channel' as channel
        , cs_call_center_sk as id
        , sales
        , returns
        , (profit - profit_loss) as profit
 from  cs
       , cr
 union all
 select 'web channel' as channel
        , ws.wp_web_page_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ws left join wr
        on  ws.wp_web_page_sk = wr.wp_web_page_sk
 ) x
 group by rollup (channel, id)
 order by channel
         ,id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ss as
 (select s_store_sk,
         sum(ss_ext_sales_price) as sales,
         sum(ss_net_profit) as profit
 from store_sales,
      date_dim,
      store
 where ss_sold_date_sk = d_date_sk
       and d_date between cast('2002-08-13' as date) 
                  and (cast('2002-08-13' as date) +  30 ) 
       and ss_store_sk = s_store_sk
 group by s_store_sk)
 ,
 sr as
 (select s_store_sk,
         sum(sr_return_amt) as returns,
         sum(sr_net_loss) as profit_loss
 from store_returns,
      date_dim,
      store
 where sr_returned_date_sk = d_date_sk
       and d_date between cast('2002-08-13' as date)
                  and (cast('2002-08-13' as date) +  30 )
       and sr_store_sk = s_store_sk
 group by s_store_sk), 
 cs as
 (select cs_call_center_sk,
        sum(cs_ext_sales_price) as sales,
        sum(cs_net_profit) as profit
 from catalog_sales,
      date_dim
 where cs_sold_date_sk = d_date_sk
       and d_date between cast('2002-08-13' as date)
                  and (cast('2002-08-13' as date) +  30 )
 group by cs_call_center_sk 
 ), 
 cr as
 (select cr_call_center_sk,
         sum(cr_return_amount) as returns,
         sum(cr_net_loss) as profit_loss
 from catalog_returns,
      date_dim
 where cr_returned_date_sk = d_date_sk
       and d_date between cast('2002-08-13' as date)
                  and (cast('2002-08-13' as date) +  30 )
 group by cr_call_center_sk
 ), 
 ws as
 ( select wp_web_page_sk,
        sum(ws_ext_sales_price) as sales,
        sum(ws_net_profit) as profit
 from web_sales,
      date_dim,
      web_page
 where ws_sold_date_sk = d_date_sk
       and d_date between cast('2002-08-13' as date)
                  and (cast('2002-08-13' as date) +  30 )
       and ws_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk), 
 wr as
 (select wp_web_page_sk,
        sum(wr_return_amt) as returns,
        sum(wr_net_loss) as profit_loss
 from web_returns,
      date_dim,
      web_page
 where wr_returned_date_sk = d_date_sk
       and d_date between cast('2002-08-13' as date)
                  and (cast('2002-08-13' as date) +  30 )
       and wr_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk)
  select  channel
        , id
        , sum(sales) as sales
        , sum(returns) as returns
        , sum(profit) as profit
 from 
 (select 'store channel' as channel
        , ss.s_store_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ss left join sr
        on  ss.s_store_sk = sr.s_store_sk
 union all
 select 'catalog channel' as channel
        , cs_call_center_sk as id
        , sales
        , returns
        , (profit - profit_loss) as profit
 from  cs
       , cr
 union all
 select 'web channel' as channel
        , ws.wp_web_page_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ws left join wr
        on  ws.wp_web_page_sk = wr.wp_web_page_sk
 ) x
 group by rollup (channel, id)
 order by channel
         ,id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ss as
 (select s_store_sk,
         sum(ss_ext_sales_price) as sales,
         sum(ss_net_profit) as profit
 from store_sales,
      date_dim,
      store
 where ss_sold_date_sk = d_date_sk
       and d_date between cast('2001-08-20' as date) 
                  and (cast('2001-08-20' as date) +  30 ) 
       and ss_store_sk = s_store_sk
 group by s_store_sk)
 ,
 sr as
 (select s_store_sk,
         sum(sr_return_amt) as returns,
         sum(sr_net_loss) as profit_loss
 from store_returns,
      date_dim,
      store
 where sr_returned_date_sk = d_date_sk
       and d_date between cast('2001-08-20' as date)
                  and (cast('2001-08-20' as date) +  30 )
       and sr_store_sk = s_store_sk
 group by s_store_sk), 
 cs as
 (select cs_call_center_sk,
        sum(cs_ext_sales_price) as sales,
        sum(cs_net_profit) as profit
 from catalog_sales,
      date_dim
 where cs_sold_date_sk = d_date_sk
       and d_date between cast('2001-08-20' as date)
                  and (cast('2001-08-20' as date) +  30 )
 group by cs_call_center_sk 
 ), 
 cr as
 (select cr_call_center_sk,
         sum(cr_return_amount) as returns,
         sum(cr_net_loss) as profit_loss
 from catalog_returns,
      date_dim
 where cr_returned_date_sk = d_date_sk
       and d_date between cast('2001-08-20' as date)
                  and (cast('2001-08-20' as date) +  30 )
 group by cr_call_center_sk
 ), 
 ws as
 ( select wp_web_page_sk,
        sum(ws_ext_sales_price) as sales,
        sum(ws_net_profit) as profit
 from web_sales,
      date_dim,
      web_page
 where ws_sold_date_sk = d_date_sk
       and d_date between cast('2001-08-20' as date)
                  and (cast('2001-08-20' as date) +  30 )
       and ws_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk), 
 wr as
 (select wp_web_page_sk,
        sum(wr_return_amt) as returns,
        sum(wr_net_loss) as profit_loss
 from web_returns,
      date_dim,
      web_page
 where wr_returned_date_sk = d_date_sk
       and d_date between cast('2001-08-20' as date)
                  and (cast('2001-08-20' as date) +  30 )
       and wr_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk)
  select  channel
        , id
        , sum(sales) as sales
        , sum(returns) as returns
        , sum(profit) as profit
 from 
 (select 'store channel' as channel
        , ss.s_store_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ss left join sr
        on  ss.s_store_sk = sr.s_store_sk
 union all
 select 'catalog channel' as channel
        , cs_call_center_sk as id
        , sales
        , returns
        , (profit - profit_loss) as profit
 from  cs
       , cr
 union all
 select 'web channel' as channel
        , ws.wp_web_page_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ws left join wr
        on  ws.wp_web_page_sk = wr.wp_web_page_sk
 ) x
 group by rollup (channel, id)
 order by channel
         ,id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ss as
 (select s_store_sk,
         sum(ss_ext_sales_price) as sales,
         sum(ss_net_profit) as profit
 from store_sales,
      date_dim,
      store
 where ss_sold_date_sk = d_date_sk
       and d_date between cast('1998-08-06' as date) 
                  and (cast('1998-08-06' as date) +  30 ) 
       and ss_store_sk = s_store_sk
 group by s_store_sk)
 ,
 sr as
 (select s_store_sk,
         sum(sr_return_amt) as returns,
         sum(sr_net_loss) as profit_loss
 from store_returns,
      date_dim,
      store
 where sr_returned_date_sk = d_date_sk
       and d_date between cast('1998-08-06' as date)
                  and (cast('1998-08-06' as date) +  30 )
       and sr_store_sk = s_store_sk
 group by s_store_sk), 
 cs as
 (select cs_call_center_sk,
        sum(cs_ext_sales_price) as sales,
        sum(cs_net_profit) as profit
 from catalog_sales,
      date_dim
 where cs_sold_date_sk = d_date_sk
       and d_date between cast('1998-08-06' as date)
                  and (cast('1998-08-06' as date) +  30 )
 group by cs_call_center_sk 
 ), 
 cr as
 (select cr_call_center_sk,
         sum(cr_return_amount) as returns,
         sum(cr_net_loss) as profit_loss
 from catalog_returns,
      date_dim
 where cr_returned_date_sk = d_date_sk
       and d_date between cast('1998-08-06' as date)
                  and (cast('1998-08-06' as date) +  30 )
 group by cr_call_center_sk
 ), 
 ws as
 ( select wp_web_page_sk,
        sum(ws_ext_sales_price) as sales,
        sum(ws_net_profit) as profit
 from web_sales,
      date_dim,
      web_page
 where ws_sold_date_sk = d_date_sk
       and d_date between cast('1998-08-06' as date)
                  and (cast('1998-08-06' as date) +  30 )
       and ws_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk), 
 wr as
 (select wp_web_page_sk,
        sum(wr_return_amt) as returns,
        sum(wr_net_loss) as profit_loss
 from web_returns,
      date_dim,
      web_page
 where wr_returned_date_sk = d_date_sk
       and d_date between cast('1998-08-06' as date)
                  and (cast('1998-08-06' as date) +  30 )
       and wr_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk)
  select  channel
        , id
        , sum(sales) as sales
        , sum(returns) as returns
        , sum(profit) as profit
 from 
 (select 'store channel' as channel
        , ss.s_store_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ss left join sr
        on  ss.s_store_sk = sr.s_store_sk
 union all
 select 'catalog channel' as channel
        , cs_call_center_sk as id
        , sales
        , returns
        , (profit - profit_loss) as profit
 from  cs
       , cr
 union all
 select 'web channel' as channel
        , ws.wp_web_page_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ws left join wr
        on  ws.wp_web_page_sk = wr.wp_web_page_sk
 ) x
 group by rollup (channel, id)
 order by channel
         ,id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ss as
 (select s_store_sk,
         sum(ss_ext_sales_price) as sales,
         sum(ss_net_profit) as profit
 from store_sales,
      date_dim,
      store
 where ss_sold_date_sk = d_date_sk
       and d_date between cast('1998-08-15' as date) 
                  and (cast('1998-08-15' as date) +  30 ) 
       and ss_store_sk = s_store_sk
 group by s_store_sk)
 ,
 sr as
 (select s_store_sk,
         sum(sr_return_amt) as returns,
         sum(sr_net_loss) as profit_loss
 from store_returns,
      date_dim,
      store
 where sr_returned_date_sk = d_date_sk
       and d_date between cast('1998-08-15' as date)
                  and (cast('1998-08-15' as date) +  30 )
       and sr_store_sk = s_store_sk
 group by s_store_sk), 
 cs as
 (select cs_call_center_sk,
        sum(cs_ext_sales_price) as sales,
        sum(cs_net_profit) as profit
 from catalog_sales,
      date_dim
 where cs_sold_date_sk = d_date_sk
       and d_date between cast('1998-08-15' as date)
                  and (cast('1998-08-15' as date) +  30 )
 group by cs_call_center_sk 
 ), 
 cr as
 (select cr_call_center_sk,
         sum(cr_return_amount) as returns,
         sum(cr_net_loss) as profit_loss
 from catalog_returns,
      date_dim
 where cr_returned_date_sk = d_date_sk
       and d_date between cast('1998-08-15' as date)
                  and (cast('1998-08-15' as date) +  30 )
 group by cr_call_center_sk
 ), 
 ws as
 ( select wp_web_page_sk,
        sum(ws_ext_sales_price) as sales,
        sum(ws_net_profit) as profit
 from web_sales,
      date_dim,
      web_page
 where ws_sold_date_sk = d_date_sk
       and d_date between cast('1998-08-15' as date)
                  and (cast('1998-08-15' as date) +  30 )
       and ws_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk), 
 wr as
 (select wp_web_page_sk,
        sum(wr_return_amt) as returns,
        sum(wr_net_loss) as profit_loss
 from web_returns,
      date_dim,
      web_page
 where wr_returned_date_sk = d_date_sk
       and d_date between cast('1998-08-15' as date)
                  and (cast('1998-08-15' as date) +  30 )
       and wr_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk)
  select  channel
        , id
        , sum(sales) as sales
        , sum(returns) as returns
        , sum(profit) as profit
 from 
 (select 'store channel' as channel
        , ss.s_store_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ss left join sr
        on  ss.s_store_sk = sr.s_store_sk
 union all
 select 'catalog channel' as channel
        , cs_call_center_sk as id
        , sales
        , returns
        , (profit - profit_loss) as profit
 from  cs
       , cr
 union all
 select 'web channel' as channel
        , ws.wp_web_page_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ws left join wr
        on  ws.wp_web_page_sk = wr.wp_web_page_sk
 ) x
 group by rollup (channel, id)
 order by channel
         ,id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ss as
 (select s_store_sk,
         sum(ss_ext_sales_price) as sales,
         sum(ss_net_profit) as profit
 from store_sales,
      date_dim,
      store
 where ss_sold_date_sk = d_date_sk
       and d_date between cast('1998-08-12' as date) 
                  and (cast('1998-08-12' as date) +  30 ) 
       and ss_store_sk = s_store_sk
 group by s_store_sk)
 ,
 sr as
 (select s_store_sk,
         sum(sr_return_amt) as returns,
         sum(sr_net_loss) as profit_loss
 from store_returns,
      date_dim,
      store
 where sr_returned_date_sk = d_date_sk
       and d_date between cast('1998-08-12' as date)
                  and (cast('1998-08-12' as date) +  30 )
       and sr_store_sk = s_store_sk
 group by s_store_sk), 
 cs as
 (select cs_call_center_sk,
        sum(cs_ext_sales_price) as sales,
        sum(cs_net_profit) as profit
 from catalog_sales,
      date_dim
 where cs_sold_date_sk = d_date_sk
       and d_date between cast('1998-08-12' as date)
                  and (cast('1998-08-12' as date) +  30 )
 group by cs_call_center_sk 
 ), 
 cr as
 (select cr_call_center_sk,
         sum(cr_return_amount) as returns,
         sum(cr_net_loss) as profit_loss
 from catalog_returns,
      date_dim
 where cr_returned_date_sk = d_date_sk
       and d_date between cast('1998-08-12' as date)
                  and (cast('1998-08-12' as date) +  30 )
 group by cr_call_center_sk
 ), 
 ws as
 ( select wp_web_page_sk,
        sum(ws_ext_sales_price) as sales,
        sum(ws_net_profit) as profit
 from web_sales,
      date_dim,
      web_page
 where ws_sold_date_sk = d_date_sk
       and d_date between cast('1998-08-12' as date)
                  and (cast('1998-08-12' as date) +  30 )
       and ws_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk), 
 wr as
 (select wp_web_page_sk,
        sum(wr_return_amt) as returns,
        sum(wr_net_loss) as profit_loss
 from web_returns,
      date_dim,
      web_page
 where wr_returned_date_sk = d_date_sk
       and d_date between cast('1998-08-12' as date)
                  and (cast('1998-08-12' as date) +  30 )
       and wr_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk)
  select  channel
        , id
        , sum(sales) as sales
        , sum(returns) as returns
        , sum(profit) as profit
 from 
 (select 'store channel' as channel
        , ss.s_store_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ss left join sr
        on  ss.s_store_sk = sr.s_store_sk
 union all
 select 'catalog channel' as channel
        , cs_call_center_sk as id
        , sales
        , returns
        , (profit - profit_loss) as profit
 from  cs
       , cr
 union all
 select 'web channel' as channel
        , ws.wp_web_page_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ws left join wr
        on  ws.wp_web_page_sk = wr.wp_web_page_sk
 ) x
 group by rollup (channel, id)
 order by channel
         ,id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ss as
 (select s_store_sk,
         sum(ss_ext_sales_price) as sales,
         sum(ss_net_profit) as profit
 from store_sales,
      date_dim,
      store
 where ss_sold_date_sk = d_date_sk
       and d_date between cast('2002-08-06' as date) 
                  and (cast('2002-08-06' as date) +  30 ) 
       and ss_store_sk = s_store_sk
 group by s_store_sk)
 ,
 sr as
 (select s_store_sk,
         sum(sr_return_amt) as returns,
         sum(sr_net_loss) as profit_loss
 from store_returns,
      date_dim,
      store
 where sr_returned_date_sk = d_date_sk
       and d_date between cast('2002-08-06' as date)
                  and (cast('2002-08-06' as date) +  30 )
       and sr_store_sk = s_store_sk
 group by s_store_sk), 
 cs as
 (select cs_call_center_sk,
        sum(cs_ext_sales_price) as sales,
        sum(cs_net_profit) as profit
 from catalog_sales,
      date_dim
 where cs_sold_date_sk = d_date_sk
       and d_date between cast('2002-08-06' as date)
                  and (cast('2002-08-06' as date) +  30 )
 group by cs_call_center_sk 
 ), 
 cr as
 (select cr_call_center_sk,
         sum(cr_return_amount) as returns,
         sum(cr_net_loss) as profit_loss
 from catalog_returns,
      date_dim
 where cr_returned_date_sk = d_date_sk
       and d_date between cast('2002-08-06' as date)
                  and (cast('2002-08-06' as date) +  30 )
 group by cr_call_center_sk
 ), 
 ws as
 ( select wp_web_page_sk,
        sum(ws_ext_sales_price) as sales,
        sum(ws_net_profit) as profit
 from web_sales,
      date_dim,
      web_page
 where ws_sold_date_sk = d_date_sk
       and d_date between cast('2002-08-06' as date)
                  and (cast('2002-08-06' as date) +  30 )
       and ws_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk), 
 wr as
 (select wp_web_page_sk,
        sum(wr_return_amt) as returns,
        sum(wr_net_loss) as profit_loss
 from web_returns,
      date_dim,
      web_page
 where wr_returned_date_sk = d_date_sk
       and d_date between cast('2002-08-06' as date)
                  and (cast('2002-08-06' as date) +  30 )
       and wr_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk)
  select  channel
        , id
        , sum(sales) as sales
        , sum(returns) as returns
        , sum(profit) as profit
 from 
 (select 'store channel' as channel
        , ss.s_store_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ss left join sr
        on  ss.s_store_sk = sr.s_store_sk
 union all
 select 'catalog channel' as channel
        , cs_call_center_sk as id
        , sales
        , returns
        , (profit - profit_loss) as profit
 from  cs
       , cr
 union all
 select 'web channel' as channel
        , ws.wp_web_page_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ws left join wr
        on  ws.wp_web_page_sk = wr.wp_web_page_sk
 ) x
 group by rollup (channel, id)
 order by channel
         ,id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ss as
 (select s_store_sk,
         sum(ss_ext_sales_price) as sales,
         sum(ss_net_profit) as profit
 from store_sales,
      date_dim,
      store
 where ss_sold_date_sk = d_date_sk
       and d_date between cast('1999-08-21' as date) 
                  and (cast('1999-08-21' as date) +  30 ) 
       and ss_store_sk = s_store_sk
 group by s_store_sk)
 ,
 sr as
 (select s_store_sk,
         sum(sr_return_amt) as returns,
         sum(sr_net_loss) as profit_loss
 from store_returns,
      date_dim,
      store
 where sr_returned_date_sk = d_date_sk
       and d_date between cast('1999-08-21' as date)
                  and (cast('1999-08-21' as date) +  30 )
       and sr_store_sk = s_store_sk
 group by s_store_sk), 
 cs as
 (select cs_call_center_sk,
        sum(cs_ext_sales_price) as sales,
        sum(cs_net_profit) as profit
 from catalog_sales,
      date_dim
 where cs_sold_date_sk = d_date_sk
       and d_date between cast('1999-08-21' as date)
                  and (cast('1999-08-21' as date) +  30 )
 group by cs_call_center_sk 
 ), 
 cr as
 (select cr_call_center_sk,
         sum(cr_return_amount) as returns,
         sum(cr_net_loss) as profit_loss
 from catalog_returns,
      date_dim
 where cr_returned_date_sk = d_date_sk
       and d_date between cast('1999-08-21' as date)
                  and (cast('1999-08-21' as date) +  30 )
 group by cr_call_center_sk
 ), 
 ws as
 ( select wp_web_page_sk,
        sum(ws_ext_sales_price) as sales,
        sum(ws_net_profit) as profit
 from web_sales,
      date_dim,
      web_page
 where ws_sold_date_sk = d_date_sk
       and d_date between cast('1999-08-21' as date)
                  and (cast('1999-08-21' as date) +  30 )
       and ws_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk), 
 wr as
 (select wp_web_page_sk,
        sum(wr_return_amt) as returns,
        sum(wr_net_loss) as profit_loss
 from web_returns,
      date_dim,
      web_page
 where wr_returned_date_sk = d_date_sk
       and d_date between cast('1999-08-21' as date)
                  and (cast('1999-08-21' as date) +  30 )
       and wr_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk)
  select  channel
        , id
        , sum(sales) as sales
        , sum(returns) as returns
        , sum(profit) as profit
 from 
 (select 'store channel' as channel
        , ss.s_store_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ss left join sr
        on  ss.s_store_sk = sr.s_store_sk
 union all
 select 'catalog channel' as channel
        , cs_call_center_sk as id
        , sales
        , returns
        , (profit - profit_loss) as profit
 from  cs
       , cr
 union all
 select 'web channel' as channel
        , ws.wp_web_page_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ws left join wr
        on  ws.wp_web_page_sk = wr.wp_web_page_sk
 ) x
 group by rollup (channel, id)
 order by channel
         ,id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ss as
 (select s_store_sk,
         sum(ss_ext_sales_price) as sales,
         sum(ss_net_profit) as profit
 from store_sales,
      date_dim,
      store
 where ss_sold_date_sk = d_date_sk
       and d_date between cast('2001-08-04' as date) 
                  and (cast('2001-08-04' as date) +  30 ) 
       and ss_store_sk = s_store_sk
 group by s_store_sk)
 ,
 sr as
 (select s_store_sk,
         sum(sr_return_amt) as returns,
         sum(sr_net_loss) as profit_loss
 from store_returns,
      date_dim,
      store
 where sr_returned_date_sk = d_date_sk
       and d_date between cast('2001-08-04' as date)
                  and (cast('2001-08-04' as date) +  30 )
       and sr_store_sk = s_store_sk
 group by s_store_sk), 
 cs as
 (select cs_call_center_sk,
        sum(cs_ext_sales_price) as sales,
        sum(cs_net_profit) as profit
 from catalog_sales,
      date_dim
 where cs_sold_date_sk = d_date_sk
       and d_date between cast('2001-08-04' as date)
                  and (cast('2001-08-04' as date) +  30 )
 group by cs_call_center_sk 
 ), 
 cr as
 (select cr_call_center_sk,
         sum(cr_return_amount) as returns,
         sum(cr_net_loss) as profit_loss
 from catalog_returns,
      date_dim
 where cr_returned_date_sk = d_date_sk
       and d_date between cast('2001-08-04' as date)
                  and (cast('2001-08-04' as date) +  30 )
 group by cr_call_center_sk
 ), 
 ws as
 ( select wp_web_page_sk,
        sum(ws_ext_sales_price) as sales,
        sum(ws_net_profit) as profit
 from web_sales,
      date_dim,
      web_page
 where ws_sold_date_sk = d_date_sk
       and d_date between cast('2001-08-04' as date)
                  and (cast('2001-08-04' as date) +  30 )
       and ws_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk), 
 wr as
 (select wp_web_page_sk,
        sum(wr_return_amt) as returns,
        sum(wr_net_loss) as profit_loss
 from web_returns,
      date_dim,
      web_page
 where wr_returned_date_sk = d_date_sk
       and d_date between cast('2001-08-04' as date)
                  and (cast('2001-08-04' as date) +  30 )
       and wr_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk)
  select  channel
        , id
        , sum(sales) as sales
        , sum(returns) as returns
        , sum(profit) as profit
 from 
 (select 'store channel' as channel
        , ss.s_store_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ss left join sr
        on  ss.s_store_sk = sr.s_store_sk
 union all
 select 'catalog channel' as channel
        , cs_call_center_sk as id
        , sales
        , returns
        , (profit - profit_loss) as profit
 from  cs
       , cr
 union all
 select 'web channel' as channel
        , ws.wp_web_page_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ws left join wr
        on  ws.wp_web_page_sk = wr.wp_web_page_sk
 ) x
 group by rollup (channel, id)
 order by channel
         ,id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ss as
 (select s_store_sk,
         sum(ss_ext_sales_price) as sales,
         sum(ss_net_profit) as profit
 from store_sales,
      date_dim,
      store
 where ss_sold_date_sk = d_date_sk
       and d_date between cast('2002-08-27' as date) 
                  and (cast('2002-08-27' as date) +  30 ) 
       and ss_store_sk = s_store_sk
 group by s_store_sk)
 ,
 sr as
 (select s_store_sk,
         sum(sr_return_amt) as returns,
         sum(sr_net_loss) as profit_loss
 from store_returns,
      date_dim,
      store
 where sr_returned_date_sk = d_date_sk
       and d_date between cast('2002-08-27' as date)
                  and (cast('2002-08-27' as date) +  30 )
       and sr_store_sk = s_store_sk
 group by s_store_sk), 
 cs as
 (select cs_call_center_sk,
        sum(cs_ext_sales_price) as sales,
        sum(cs_net_profit) as profit
 from catalog_sales,
      date_dim
 where cs_sold_date_sk = d_date_sk
       and d_date between cast('2002-08-27' as date)
                  and (cast('2002-08-27' as date) +  30 )
 group by cs_call_center_sk 
 ), 
 cr as
 (select cr_call_center_sk,
         sum(cr_return_amount) as returns,
         sum(cr_net_loss) as profit_loss
 from catalog_returns,
      date_dim
 where cr_returned_date_sk = d_date_sk
       and d_date between cast('2002-08-27' as date)
                  and (cast('2002-08-27' as date) +  30 )
 group by cr_call_center_sk
 ), 
 ws as
 ( select wp_web_page_sk,
        sum(ws_ext_sales_price) as sales,
        sum(ws_net_profit) as profit
 from web_sales,
      date_dim,
      web_page
 where ws_sold_date_sk = d_date_sk
       and d_date between cast('2002-08-27' as date)
                  and (cast('2002-08-27' as date) +  30 )
       and ws_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk), 
 wr as
 (select wp_web_page_sk,
        sum(wr_return_amt) as returns,
        sum(wr_net_loss) as profit_loss
 from web_returns,
      date_dim,
      web_page
 where wr_returned_date_sk = d_date_sk
       and d_date between cast('2002-08-27' as date)
                  and (cast('2002-08-27' as date) +  30 )
       and wr_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk)
  select  channel
        , id
        , sum(sales) as sales
        , sum(returns) as returns
        , sum(profit) as profit
 from 
 (select 'store channel' as channel
        , ss.s_store_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ss left join sr
        on  ss.s_store_sk = sr.s_store_sk
 union all
 select 'catalog channel' as channel
        , cs_call_center_sk as id
        , sales
        , returns
        , (profit - profit_loss) as profit
 from  cs
       , cr
 union all
 select 'web channel' as channel
        , ws.wp_web_page_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ws left join wr
        on  ws.wp_web_page_sk = wr.wp_web_page_sk
 ) x
 group by rollup (channel, id)
 order by channel
         ,id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ss as
 (select s_store_sk,
         sum(ss_ext_sales_price) as sales,
         sum(ss_net_profit) as profit
 from store_sales,
      date_dim,
      store
 where ss_sold_date_sk = d_date_sk
       and d_date between cast('1998-08-08' as date) 
                  and (cast('1998-08-08' as date) +  30 ) 
       and ss_store_sk = s_store_sk
 group by s_store_sk)
 ,
 sr as
 (select s_store_sk,
         sum(sr_return_amt) as returns,
         sum(sr_net_loss) as profit_loss
 from store_returns,
      date_dim,
      store
 where sr_returned_date_sk = d_date_sk
       and d_date between cast('1998-08-08' as date)
                  and (cast('1998-08-08' as date) +  30 )
       and sr_store_sk = s_store_sk
 group by s_store_sk), 
 cs as
 (select cs_call_center_sk,
        sum(cs_ext_sales_price) as sales,
        sum(cs_net_profit) as profit
 from catalog_sales,
      date_dim
 where cs_sold_date_sk = d_date_sk
       and d_date between cast('1998-08-08' as date)
                  and (cast('1998-08-08' as date) +  30 )
 group by cs_call_center_sk 
 ), 
 cr as
 (select cr_call_center_sk,
         sum(cr_return_amount) as returns,
         sum(cr_net_loss) as profit_loss
 from catalog_returns,
      date_dim
 where cr_returned_date_sk = d_date_sk
       and d_date between cast('1998-08-08' as date)
                  and (cast('1998-08-08' as date) +  30 )
 group by cr_call_center_sk
 ), 
 ws as
 ( select wp_web_page_sk,
        sum(ws_ext_sales_price) as sales,
        sum(ws_net_profit) as profit
 from web_sales,
      date_dim,
      web_page
 where ws_sold_date_sk = d_date_sk
       and d_date between cast('1998-08-08' as date)
                  and (cast('1998-08-08' as date) +  30 )
       and ws_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk), 
 wr as
 (select wp_web_page_sk,
        sum(wr_return_amt) as returns,
        sum(wr_net_loss) as profit_loss
 from web_returns,
      date_dim,
      web_page
 where wr_returned_date_sk = d_date_sk
       and d_date between cast('1998-08-08' as date)
                  and (cast('1998-08-08' as date) +  30 )
       and wr_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk)
  select  channel
        , id
        , sum(sales) as sales
        , sum(returns) as returns
        , sum(profit) as profit
 from 
 (select 'store channel' as channel
        , ss.s_store_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ss left join sr
        on  ss.s_store_sk = sr.s_store_sk
 union all
 select 'catalog channel' as channel
        , cs_call_center_sk as id
        , sales
        , returns
        , (profit - profit_loss) as profit
 from  cs
       , cr
 union all
 select 'web channel' as channel
        , ws.wp_web_page_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ws left join wr
        on  ws.wp_web_page_sk = wr.wp_web_page_sk
 ) x
 group by rollup (channel, id)
 order by channel
         ,id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ss as
 (select s_store_sk,
         sum(ss_ext_sales_price) as sales,
         sum(ss_net_profit) as profit
 from store_sales,
      date_dim,
      store
 where ss_sold_date_sk = d_date_sk
       and d_date between cast('2002-08-25' as date) 
                  and (cast('2002-08-25' as date) +  30 ) 
       and ss_store_sk = s_store_sk
 group by s_store_sk)
 ,
 sr as
 (select s_store_sk,
         sum(sr_return_amt) as returns,
         sum(sr_net_loss) as profit_loss
 from store_returns,
      date_dim,
      store
 where sr_returned_date_sk = d_date_sk
       and d_date between cast('2002-08-25' as date)
                  and (cast('2002-08-25' as date) +  30 )
       and sr_store_sk = s_store_sk
 group by s_store_sk), 
 cs as
 (select cs_call_center_sk,
        sum(cs_ext_sales_price) as sales,
        sum(cs_net_profit) as profit
 from catalog_sales,
      date_dim
 where cs_sold_date_sk = d_date_sk
       and d_date between cast('2002-08-25' as date)
                  and (cast('2002-08-25' as date) +  30 )
 group by cs_call_center_sk 
 ), 
 cr as
 (select cr_call_center_sk,
         sum(cr_return_amount) as returns,
         sum(cr_net_loss) as profit_loss
 from catalog_returns,
      date_dim
 where cr_returned_date_sk = d_date_sk
       and d_date between cast('2002-08-25' as date)
                  and (cast('2002-08-25' as date) +  30 )
 group by cr_call_center_sk
 ), 
 ws as
 ( select wp_web_page_sk,
        sum(ws_ext_sales_price) as sales,
        sum(ws_net_profit) as profit
 from web_sales,
      date_dim,
      web_page
 where ws_sold_date_sk = d_date_sk
       and d_date between cast('2002-08-25' as date)
                  and (cast('2002-08-25' as date) +  30 )
       and ws_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk), 
 wr as
 (select wp_web_page_sk,
        sum(wr_return_amt) as returns,
        sum(wr_net_loss) as profit_loss
 from web_returns,
      date_dim,
      web_page
 where wr_returned_date_sk = d_date_sk
       and d_date between cast('2002-08-25' as date)
                  and (cast('2002-08-25' as date) +  30 )
       and wr_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk)
  select  channel
        , id
        , sum(sales) as sales
        , sum(returns) as returns
        , sum(profit) as profit
 from 
 (select 'store channel' as channel
        , ss.s_store_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ss left join sr
        on  ss.s_store_sk = sr.s_store_sk
 union all
 select 'catalog channel' as channel
        , cs_call_center_sk as id
        , sales
        , returns
        , (profit - profit_loss) as profit
 from  cs
       , cr
 union all
 select 'web channel' as channel
        , ws.wp_web_page_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ws left join wr
        on  ws.wp_web_page_sk = wr.wp_web_page_sk
 ) x
 group by rollup (channel, id)
 order by channel
         ,id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ss as
 (select s_store_sk,
         sum(ss_ext_sales_price) as sales,
         sum(ss_net_profit) as profit
 from store_sales,
      date_dim,
      store
 where ss_sold_date_sk = d_date_sk
       and d_date between cast('2002-08-12' as date) 
                  and (cast('2002-08-12' as date) +  30 ) 
       and ss_store_sk = s_store_sk
 group by s_store_sk)
 ,
 sr as
 (select s_store_sk,
         sum(sr_return_amt) as returns,
         sum(sr_net_loss) as profit_loss
 from store_returns,
      date_dim,
      store
 where sr_returned_date_sk = d_date_sk
       and d_date between cast('2002-08-12' as date)
                  and (cast('2002-08-12' as date) +  30 )
       and sr_store_sk = s_store_sk
 group by s_store_sk), 
 cs as
 (select cs_call_center_sk,
        sum(cs_ext_sales_price) as sales,
        sum(cs_net_profit) as profit
 from catalog_sales,
      date_dim
 where cs_sold_date_sk = d_date_sk
       and d_date between cast('2002-08-12' as date)
                  and (cast('2002-08-12' as date) +  30 )
 group by cs_call_center_sk 
 ), 
 cr as
 (select cr_call_center_sk,
         sum(cr_return_amount) as returns,
         sum(cr_net_loss) as profit_loss
 from catalog_returns,
      date_dim
 where cr_returned_date_sk = d_date_sk
       and d_date between cast('2002-08-12' as date)
                  and (cast('2002-08-12' as date) +  30 )
 group by cr_call_center_sk
 ), 
 ws as
 ( select wp_web_page_sk,
        sum(ws_ext_sales_price) as sales,
        sum(ws_net_profit) as profit
 from web_sales,
      date_dim,
      web_page
 where ws_sold_date_sk = d_date_sk
       and d_date between cast('2002-08-12' as date)
                  and (cast('2002-08-12' as date) +  30 )
       and ws_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk), 
 wr as
 (select wp_web_page_sk,
        sum(wr_return_amt) as returns,
        sum(wr_net_loss) as profit_loss
 from web_returns,
      date_dim,
      web_page
 where wr_returned_date_sk = d_date_sk
       and d_date between cast('2002-08-12' as date)
                  and (cast('2002-08-12' as date) +  30 )
       and wr_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk)
  select  channel
        , id
        , sum(sales) as sales
        , sum(returns) as returns
        , sum(profit) as profit
 from 
 (select 'store channel' as channel
        , ss.s_store_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ss left join sr
        on  ss.s_store_sk = sr.s_store_sk
 union all
 select 'catalog channel' as channel
        , cs_call_center_sk as id
        , sales
        , returns
        , (profit - profit_loss) as profit
 from  cs
       , cr
 union all
 select 'web channel' as channel
        , ws.wp_web_page_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ws left join wr
        on  ws.wp_web_page_sk = wr.wp_web_page_sk
 ) x
 group by rollup (channel, id)
 order by channel
         ,id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ss as
 (select s_store_sk,
         sum(ss_ext_sales_price) as sales,
         sum(ss_net_profit) as profit
 from store_sales,
      date_dim,
      store
 where ss_sold_date_sk = d_date_sk
       and d_date between cast('1999-08-05' as date) 
                  and (cast('1999-08-05' as date) +  30 ) 
       and ss_store_sk = s_store_sk
 group by s_store_sk)
 ,
 sr as
 (select s_store_sk,
         sum(sr_return_amt) as returns,
         sum(sr_net_loss) as profit_loss
 from store_returns,
      date_dim,
      store
 where sr_returned_date_sk = d_date_sk
       and d_date between cast('1999-08-05' as date)
                  and (cast('1999-08-05' as date) +  30 )
       and sr_store_sk = s_store_sk
 group by s_store_sk), 
 cs as
 (select cs_call_center_sk,
        sum(cs_ext_sales_price) as sales,
        sum(cs_net_profit) as profit
 from catalog_sales,
      date_dim
 where cs_sold_date_sk = d_date_sk
       and d_date between cast('1999-08-05' as date)
                  and (cast('1999-08-05' as date) +  30 )
 group by cs_call_center_sk 
 ), 
 cr as
 (select cr_call_center_sk,
         sum(cr_return_amount) as returns,
         sum(cr_net_loss) as profit_loss
 from catalog_returns,
      date_dim
 where cr_returned_date_sk = d_date_sk
       and d_date between cast('1999-08-05' as date)
                  and (cast('1999-08-05' as date) +  30 )
 group by cr_call_center_sk
 ), 
 ws as
 ( select wp_web_page_sk,
        sum(ws_ext_sales_price) as sales,
        sum(ws_net_profit) as profit
 from web_sales,
      date_dim,
      web_page
 where ws_sold_date_sk = d_date_sk
       and d_date between cast('1999-08-05' as date)
                  and (cast('1999-08-05' as date) +  30 )
       and ws_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk), 
 wr as
 (select wp_web_page_sk,
        sum(wr_return_amt) as returns,
        sum(wr_net_loss) as profit_loss
 from web_returns,
      date_dim,
      web_page
 where wr_returned_date_sk = d_date_sk
       and d_date between cast('1999-08-05' as date)
                  and (cast('1999-08-05' as date) +  30 )
       and wr_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk)
  select  channel
        , id
        , sum(sales) as sales
        , sum(returns) as returns
        , sum(profit) as profit
 from 
 (select 'store channel' as channel
        , ss.s_store_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ss left join sr
        on  ss.s_store_sk = sr.s_store_sk
 union all
 select 'catalog channel' as channel
        , cs_call_center_sk as id
        , sales
        , returns
        , (profit - profit_loss) as profit
 from  cs
       , cr
 union all
 select 'web channel' as channel
        , ws.wp_web_page_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ws left join wr
        on  ws.wp_web_page_sk = wr.wp_web_page_sk
 ) x
 group by rollup (channel, id)
 order by channel
         ,id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ss as
 (select s_store_sk,
         sum(ss_ext_sales_price) as sales,
         sum(ss_net_profit) as profit
 from store_sales,
      date_dim,
      store
 where ss_sold_date_sk = d_date_sk
       and d_date between cast('2000-08-07' as date) 
                  and (cast('2000-08-07' as date) +  30 ) 
       and ss_store_sk = s_store_sk
 group by s_store_sk)
 ,
 sr as
 (select s_store_sk,
         sum(sr_return_amt) as returns,
         sum(sr_net_loss) as profit_loss
 from store_returns,
      date_dim,
      store
 where sr_returned_date_sk = d_date_sk
       and d_date between cast('2000-08-07' as date)
                  and (cast('2000-08-07' as date) +  30 )
       and sr_store_sk = s_store_sk
 group by s_store_sk), 
 cs as
 (select cs_call_center_sk,
        sum(cs_ext_sales_price) as sales,
        sum(cs_net_profit) as profit
 from catalog_sales,
      date_dim
 where cs_sold_date_sk = d_date_sk
       and d_date between cast('2000-08-07' as date)
                  and (cast('2000-08-07' as date) +  30 )
 group by cs_call_center_sk 
 ), 
 cr as
 (select cr_call_center_sk,
         sum(cr_return_amount) as returns,
         sum(cr_net_loss) as profit_loss
 from catalog_returns,
      date_dim
 where cr_returned_date_sk = d_date_sk
       and d_date between cast('2000-08-07' as date)
                  and (cast('2000-08-07' as date) +  30 )
 group by cr_call_center_sk
 ), 
 ws as
 ( select wp_web_page_sk,
        sum(ws_ext_sales_price) as sales,
        sum(ws_net_profit) as profit
 from web_sales,
      date_dim,
      web_page
 where ws_sold_date_sk = d_date_sk
       and d_date between cast('2000-08-07' as date)
                  and (cast('2000-08-07' as date) +  30 )
       and ws_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk), 
 wr as
 (select wp_web_page_sk,
        sum(wr_return_amt) as returns,
        sum(wr_net_loss) as profit_loss
 from web_returns,
      date_dim,
      web_page
 where wr_returned_date_sk = d_date_sk
       and d_date between cast('2000-08-07' as date)
                  and (cast('2000-08-07' as date) +  30 )
       and wr_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk)
  select  channel
        , id
        , sum(sales) as sales
        , sum(returns) as returns
        , sum(profit) as profit
 from 
 (select 'store channel' as channel
        , ss.s_store_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ss left join sr
        on  ss.s_store_sk = sr.s_store_sk
 union all
 select 'catalog channel' as channel
        , cs_call_center_sk as id
        , sales
        , returns
        , (profit - profit_loss) as profit
 from  cs
       , cr
 union all
 select 'web channel' as channel
        , ws.wp_web_page_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ws left join wr
        on  ws.wp_web_page_sk = wr.wp_web_page_sk
 ) x
 group by rollup (channel, id)
 order by channel
         ,id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ss as
 (select s_store_sk,
         sum(ss_ext_sales_price) as sales,
         sum(ss_net_profit) as profit
 from store_sales,
      date_dim,
      store
 where ss_sold_date_sk = d_date_sk
       and d_date between cast('2000-08-09' as date) 
                  and (cast('2000-08-09' as date) +  30 ) 
       and ss_store_sk = s_store_sk
 group by s_store_sk)
 ,
 sr as
 (select s_store_sk,
         sum(sr_return_amt) as returns,
         sum(sr_net_loss) as profit_loss
 from store_returns,
      date_dim,
      store
 where sr_returned_date_sk = d_date_sk
       and d_date between cast('2000-08-09' as date)
                  and (cast('2000-08-09' as date) +  30 )
       and sr_store_sk = s_store_sk
 group by s_store_sk), 
 cs as
 (select cs_call_center_sk,
        sum(cs_ext_sales_price) as sales,
        sum(cs_net_profit) as profit
 from catalog_sales,
      date_dim
 where cs_sold_date_sk = d_date_sk
       and d_date between cast('2000-08-09' as date)
                  and (cast('2000-08-09' as date) +  30 )
 group by cs_call_center_sk 
 ), 
 cr as
 (select cr_call_center_sk,
         sum(cr_return_amount) as returns,
         sum(cr_net_loss) as profit_loss
 from catalog_returns,
      date_dim
 where cr_returned_date_sk = d_date_sk
       and d_date between cast('2000-08-09' as date)
                  and (cast('2000-08-09' as date) +  30 )
 group by cr_call_center_sk
 ), 
 ws as
 ( select wp_web_page_sk,
        sum(ws_ext_sales_price) as sales,
        sum(ws_net_profit) as profit
 from web_sales,
      date_dim,
      web_page
 where ws_sold_date_sk = d_date_sk
       and d_date between cast('2000-08-09' as date)
                  and (cast('2000-08-09' as date) +  30 )
       and ws_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk), 
 wr as
 (select wp_web_page_sk,
        sum(wr_return_amt) as returns,
        sum(wr_net_loss) as profit_loss
 from web_returns,
      date_dim,
      web_page
 where wr_returned_date_sk = d_date_sk
       and d_date between cast('2000-08-09' as date)
                  and (cast('2000-08-09' as date) +  30 )
       and wr_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk)
  select  channel
        , id
        , sum(sales) as sales
        , sum(returns) as returns
        , sum(profit) as profit
 from 
 (select 'store channel' as channel
        , ss.s_store_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ss left join sr
        on  ss.s_store_sk = sr.s_store_sk
 union all
 select 'catalog channel' as channel
        , cs_call_center_sk as id
        , sales
        , returns
        , (profit - profit_loss) as profit
 from  cs
       , cr
 union all
 select 'web channel' as channel
        , ws.wp_web_page_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ws left join wr
        on  ws.wp_web_page_sk = wr.wp_web_page_sk
 ) x
 group by rollup (channel, id)
 order by channel
         ,id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ss as
 (select s_store_sk,
         sum(ss_ext_sales_price) as sales,
         sum(ss_net_profit) as profit
 from store_sales,
      date_dim,
      store
 where ss_sold_date_sk = d_date_sk
       and d_date between cast('2000-08-29' as date) 
                  and (cast('2000-08-29' as date) +  30 ) 
       and ss_store_sk = s_store_sk
 group by s_store_sk)
 ,
 sr as
 (select s_store_sk,
         sum(sr_return_amt) as returns,
         sum(sr_net_loss) as profit_loss
 from store_returns,
      date_dim,
      store
 where sr_returned_date_sk = d_date_sk
       and d_date between cast('2000-08-29' as date)
                  and (cast('2000-08-29' as date) +  30 )
       and sr_store_sk = s_store_sk
 group by s_store_sk), 
 cs as
 (select cs_call_center_sk,
        sum(cs_ext_sales_price) as sales,
        sum(cs_net_profit) as profit
 from catalog_sales,
      date_dim
 where cs_sold_date_sk = d_date_sk
       and d_date between cast('2000-08-29' as date)
                  and (cast('2000-08-29' as date) +  30 )
 group by cs_call_center_sk 
 ), 
 cr as
 (select cr_call_center_sk,
         sum(cr_return_amount) as returns,
         sum(cr_net_loss) as profit_loss
 from catalog_returns,
      date_dim
 where cr_returned_date_sk = d_date_sk
       and d_date between cast('2000-08-29' as date)
                  and (cast('2000-08-29' as date) +  30 )
 group by cr_call_center_sk
 ), 
 ws as
 ( select wp_web_page_sk,
        sum(ws_ext_sales_price) as sales,
        sum(ws_net_profit) as profit
 from web_sales,
      date_dim,
      web_page
 where ws_sold_date_sk = d_date_sk
       and d_date between cast('2000-08-29' as date)
                  and (cast('2000-08-29' as date) +  30 )
       and ws_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk), 
 wr as
 (select wp_web_page_sk,
        sum(wr_return_amt) as returns,
        sum(wr_net_loss) as profit_loss
 from web_returns,
      date_dim,
      web_page
 where wr_returned_date_sk = d_date_sk
       and d_date between cast('2000-08-29' as date)
                  and (cast('2000-08-29' as date) +  30 )
       and wr_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk)
  select  channel
        , id
        , sum(sales) as sales
        , sum(returns) as returns
        , sum(profit) as profit
 from 
 (select 'store channel' as channel
        , ss.s_store_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ss left join sr
        on  ss.s_store_sk = sr.s_store_sk
 union all
 select 'catalog channel' as channel
        , cs_call_center_sk as id
        , sales
        , returns
        , (profit - profit_loss) as profit
 from  cs
       , cr
 union all
 select 'web channel' as channel
        , ws.wp_web_page_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ws left join wr
        on  ws.wp_web_page_sk = wr.wp_web_page_sk
 ) x
 group by rollup (channel, id)
 order by channel
         ,id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ss as
 (select s_store_sk,
         sum(ss_ext_sales_price) as sales,
         sum(ss_net_profit) as profit
 from store_sales,
      date_dim,
      store
 where ss_sold_date_sk = d_date_sk
       and d_date between cast('2002-08-23' as date) 
                  and (cast('2002-08-23' as date) +  30 ) 
       and ss_store_sk = s_store_sk
 group by s_store_sk)
 ,
 sr as
 (select s_store_sk,
         sum(sr_return_amt) as returns,
         sum(sr_net_loss) as profit_loss
 from store_returns,
      date_dim,
      store
 where sr_returned_date_sk = d_date_sk
       and d_date between cast('2002-08-23' as date)
                  and (cast('2002-08-23' as date) +  30 )
       and sr_store_sk = s_store_sk
 group by s_store_sk), 
 cs as
 (select cs_call_center_sk,
        sum(cs_ext_sales_price) as sales,
        sum(cs_net_profit) as profit
 from catalog_sales,
      date_dim
 where cs_sold_date_sk = d_date_sk
       and d_date between cast('2002-08-23' as date)
                  and (cast('2002-08-23' as date) +  30 )
 group by cs_call_center_sk 
 ), 
 cr as
 (select cr_call_center_sk,
         sum(cr_return_amount) as returns,
         sum(cr_net_loss) as profit_loss
 from catalog_returns,
      date_dim
 where cr_returned_date_sk = d_date_sk
       and d_date between cast('2002-08-23' as date)
                  and (cast('2002-08-23' as date) +  30 )
 group by cr_call_center_sk
 ), 
 ws as
 ( select wp_web_page_sk,
        sum(ws_ext_sales_price) as sales,
        sum(ws_net_profit) as profit
 from web_sales,
      date_dim,
      web_page
 where ws_sold_date_sk = d_date_sk
       and d_date between cast('2002-08-23' as date)
                  and (cast('2002-08-23' as date) +  30 )
       and ws_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk), 
 wr as
 (select wp_web_page_sk,
        sum(wr_return_amt) as returns,
        sum(wr_net_loss) as profit_loss
 from web_returns,
      date_dim,
      web_page
 where wr_returned_date_sk = d_date_sk
       and d_date between cast('2002-08-23' as date)
                  and (cast('2002-08-23' as date) +  30 )
       and wr_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk)
  select  channel
        , id
        , sum(sales) as sales
        , sum(returns) as returns
        , sum(profit) as profit
 from 
 (select 'store channel' as channel
        , ss.s_store_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ss left join sr
        on  ss.s_store_sk = sr.s_store_sk
 union all
 select 'catalog channel' as channel
        , cs_call_center_sk as id
        , sales
        , returns
        , (profit - profit_loss) as profit
 from  cs
       , cr
 union all
 select 'web channel' as channel
        , ws.wp_web_page_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ws left join wr
        on  ws.wp_web_page_sk = wr.wp_web_page_sk
 ) x
 group by rollup (channel, id)
 order by channel
         ,id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ss as
 (select s_store_sk,
         sum(ss_ext_sales_price) as sales,
         sum(ss_net_profit) as profit
 from store_sales,
      date_dim,
      store
 where ss_sold_date_sk = d_date_sk
       and d_date between cast('1998-08-16' as date) 
                  and (cast('1998-08-16' as date) +  30 ) 
       and ss_store_sk = s_store_sk
 group by s_store_sk)
 ,
 sr as
 (select s_store_sk,
         sum(sr_return_amt) as returns,
         sum(sr_net_loss) as profit_loss
 from store_returns,
      date_dim,
      store
 where sr_returned_date_sk = d_date_sk
       and d_date between cast('1998-08-16' as date)
                  and (cast('1998-08-16' as date) +  30 )
       and sr_store_sk = s_store_sk
 group by s_store_sk), 
 cs as
 (select cs_call_center_sk,
        sum(cs_ext_sales_price) as sales,
        sum(cs_net_profit) as profit
 from catalog_sales,
      date_dim
 where cs_sold_date_sk = d_date_sk
       and d_date between cast('1998-08-16' as date)
                  and (cast('1998-08-16' as date) +  30 )
 group by cs_call_center_sk 
 ), 
 cr as
 (select cr_call_center_sk,
         sum(cr_return_amount) as returns,
         sum(cr_net_loss) as profit_loss
 from catalog_returns,
      date_dim
 where cr_returned_date_sk = d_date_sk
       and d_date between cast('1998-08-16' as date)
                  and (cast('1998-08-16' as date) +  30 )
 group by cr_call_center_sk
 ), 
 ws as
 ( select wp_web_page_sk,
        sum(ws_ext_sales_price) as sales,
        sum(ws_net_profit) as profit
 from web_sales,
      date_dim,
      web_page
 where ws_sold_date_sk = d_date_sk
       and d_date between cast('1998-08-16' as date)
                  and (cast('1998-08-16' as date) +  30 )
       and ws_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk), 
 wr as
 (select wp_web_page_sk,
        sum(wr_return_amt) as returns,
        sum(wr_net_loss) as profit_loss
 from web_returns,
      date_dim,
      web_page
 where wr_returned_date_sk = d_date_sk
       and d_date between cast('1998-08-16' as date)
                  and (cast('1998-08-16' as date) +  30 )
       and wr_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk)
  select  channel
        , id
        , sum(sales) as sales
        , sum(returns) as returns
        , sum(profit) as profit
 from 
 (select 'store channel' as channel
        , ss.s_store_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ss left join sr
        on  ss.s_store_sk = sr.s_store_sk
 union all
 select 'catalog channel' as channel
        , cs_call_center_sk as id
        , sales
        , returns
        , (profit - profit_loss) as profit
 from  cs
       , cr
 union all
 select 'web channel' as channel
        , ws.wp_web_page_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ws left join wr
        on  ws.wp_web_page_sk = wr.wp_web_page_sk
 ) x
 group by rollup (channel, id)
 order by channel
         ,id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ss as
 (select s_store_sk,
         sum(ss_ext_sales_price) as sales,
         sum(ss_net_profit) as profit
 from store_sales,
      date_dim,
      store
 where ss_sold_date_sk = d_date_sk
       and d_date between cast('2001-08-08' as date) 
                  and (cast('2001-08-08' as date) +  30 ) 
       and ss_store_sk = s_store_sk
 group by s_store_sk)
 ,
 sr as
 (select s_store_sk,
         sum(sr_return_amt) as returns,
         sum(sr_net_loss) as profit_loss
 from store_returns,
      date_dim,
      store
 where sr_returned_date_sk = d_date_sk
       and d_date between cast('2001-08-08' as date)
                  and (cast('2001-08-08' as date) +  30 )
       and sr_store_sk = s_store_sk
 group by s_store_sk), 
 cs as
 (select cs_call_center_sk,
        sum(cs_ext_sales_price) as sales,
        sum(cs_net_profit) as profit
 from catalog_sales,
      date_dim
 where cs_sold_date_sk = d_date_sk
       and d_date between cast('2001-08-08' as date)
                  and (cast('2001-08-08' as date) +  30 )
 group by cs_call_center_sk 
 ), 
 cr as
 (select cr_call_center_sk,
         sum(cr_return_amount) as returns,
         sum(cr_net_loss) as profit_loss
 from catalog_returns,
      date_dim
 where cr_returned_date_sk = d_date_sk
       and d_date between cast('2001-08-08' as date)
                  and (cast('2001-08-08' as date) +  30 )
 group by cr_call_center_sk
 ), 
 ws as
 ( select wp_web_page_sk,
        sum(ws_ext_sales_price) as sales,
        sum(ws_net_profit) as profit
 from web_sales,
      date_dim,
      web_page
 where ws_sold_date_sk = d_date_sk
       and d_date between cast('2001-08-08' as date)
                  and (cast('2001-08-08' as date) +  30 )
       and ws_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk), 
 wr as
 (select wp_web_page_sk,
        sum(wr_return_amt) as returns,
        sum(wr_net_loss) as profit_loss
 from web_returns,
      date_dim,
      web_page
 where wr_returned_date_sk = d_date_sk
       and d_date between cast('2001-08-08' as date)
                  and (cast('2001-08-08' as date) +  30 )
       and wr_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk)
  select  channel
        , id
        , sum(sales) as sales
        , sum(returns) as returns
        , sum(profit) as profit
 from 
 (select 'store channel' as channel
        , ss.s_store_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ss left join sr
        on  ss.s_store_sk = sr.s_store_sk
 union all
 select 'catalog channel' as channel
        , cs_call_center_sk as id
        , sales
        , returns
        , (profit - profit_loss) as profit
 from  cs
       , cr
 union all
 select 'web channel' as channel
        , ws.wp_web_page_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ws left join wr
        on  ws.wp_web_page_sk = wr.wp_web_page_sk
 ) x
 group by rollup (channel, id)
 order by channel
         ,id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ss as
 (select s_store_sk,
         sum(ss_ext_sales_price) as sales,
         sum(ss_net_profit) as profit
 from store_sales,
      date_dim,
      store
 where ss_sold_date_sk = d_date_sk
       and d_date between cast('2000-08-25' as date) 
                  and (cast('2000-08-25' as date) +  30 ) 
       and ss_store_sk = s_store_sk
 group by s_store_sk)
 ,
 sr as
 (select s_store_sk,
         sum(sr_return_amt) as returns,
         sum(sr_net_loss) as profit_loss
 from store_returns,
      date_dim,
      store
 where sr_returned_date_sk = d_date_sk
       and d_date between cast('2000-08-25' as date)
                  and (cast('2000-08-25' as date) +  30 )
       and sr_store_sk = s_store_sk
 group by s_store_sk), 
 cs as
 (select cs_call_center_sk,
        sum(cs_ext_sales_price) as sales,
        sum(cs_net_profit) as profit
 from catalog_sales,
      date_dim
 where cs_sold_date_sk = d_date_sk
       and d_date between cast('2000-08-25' as date)
                  and (cast('2000-08-25' as date) +  30 )
 group by cs_call_center_sk 
 ), 
 cr as
 (select cr_call_center_sk,
         sum(cr_return_amount) as returns,
         sum(cr_net_loss) as profit_loss
 from catalog_returns,
      date_dim
 where cr_returned_date_sk = d_date_sk
       and d_date between cast('2000-08-25' as date)
                  and (cast('2000-08-25' as date) +  30 )
 group by cr_call_center_sk
 ), 
 ws as
 ( select wp_web_page_sk,
        sum(ws_ext_sales_price) as sales,
        sum(ws_net_profit) as profit
 from web_sales,
      date_dim,
      web_page
 where ws_sold_date_sk = d_date_sk
       and d_date between cast('2000-08-25' as date)
                  and (cast('2000-08-25' as date) +  30 )
       and ws_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk), 
 wr as
 (select wp_web_page_sk,
        sum(wr_return_amt) as returns,
        sum(wr_net_loss) as profit_loss
 from web_returns,
      date_dim,
      web_page
 where wr_returned_date_sk = d_date_sk
       and d_date between cast('2000-08-25' as date)
                  and (cast('2000-08-25' as date) +  30 )
       and wr_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk)
  select  channel
        , id
        , sum(sales) as sales
        , sum(returns) as returns
        , sum(profit) as profit
 from 
 (select 'store channel' as channel
        , ss.s_store_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ss left join sr
        on  ss.s_store_sk = sr.s_store_sk
 union all
 select 'catalog channel' as channel
        , cs_call_center_sk as id
        , sales
        , returns
        , (profit - profit_loss) as profit
 from  cs
       , cr
 union all
 select 'web channel' as channel
        , ws.wp_web_page_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ws left join wr
        on  ws.wp_web_page_sk = wr.wp_web_page_sk
 ) x
 group by rollup (channel, id)
 order by channel
         ,id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ss as
 (select s_store_sk,
         sum(ss_ext_sales_price) as sales,
         sum(ss_net_profit) as profit
 from store_sales,
      date_dim,
      store
 where ss_sold_date_sk = d_date_sk
       and d_date between cast('2000-08-06' as date) 
                  and (cast('2000-08-06' as date) +  30 ) 
       and ss_store_sk = s_store_sk
 group by s_store_sk)
 ,
 sr as
 (select s_store_sk,
         sum(sr_return_amt) as returns,
         sum(sr_net_loss) as profit_loss
 from store_returns,
      date_dim,
      store
 where sr_returned_date_sk = d_date_sk
       and d_date between cast('2000-08-06' as date)
                  and (cast('2000-08-06' as date) +  30 )
       and sr_store_sk = s_store_sk
 group by s_store_sk), 
 cs as
 (select cs_call_center_sk,
        sum(cs_ext_sales_price) as sales,
        sum(cs_net_profit) as profit
 from catalog_sales,
      date_dim
 where cs_sold_date_sk = d_date_sk
       and d_date between cast('2000-08-06' as date)
                  and (cast('2000-08-06' as date) +  30 )
 group by cs_call_center_sk 
 ), 
 cr as
 (select cr_call_center_sk,
         sum(cr_return_amount) as returns,
         sum(cr_net_loss) as profit_loss
 from catalog_returns,
      date_dim
 where cr_returned_date_sk = d_date_sk
       and d_date between cast('2000-08-06' as date)
                  and (cast('2000-08-06' as date) +  30 )
 group by cr_call_center_sk
 ), 
 ws as
 ( select wp_web_page_sk,
        sum(ws_ext_sales_price) as sales,
        sum(ws_net_profit) as profit
 from web_sales,
      date_dim,
      web_page
 where ws_sold_date_sk = d_date_sk
       and d_date between cast('2000-08-06' as date)
                  and (cast('2000-08-06' as date) +  30 )
       and ws_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk), 
 wr as
 (select wp_web_page_sk,
        sum(wr_return_amt) as returns,
        sum(wr_net_loss) as profit_loss
 from web_returns,
      date_dim,
      web_page
 where wr_returned_date_sk = d_date_sk
       and d_date between cast('2000-08-06' as date)
                  and (cast('2000-08-06' as date) +  30 )
       and wr_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk)
  select  channel
        , id
        , sum(sales) as sales
        , sum(returns) as returns
        , sum(profit) as profit
 from 
 (select 'store channel' as channel
        , ss.s_store_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ss left join sr
        on  ss.s_store_sk = sr.s_store_sk
 union all
 select 'catalog channel' as channel
        , cs_call_center_sk as id
        , sales
        , returns
        , (profit - profit_loss) as profit
 from  cs
       , cr
 union all
 select 'web channel' as channel
        , ws.wp_web_page_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ws left join wr
        on  ws.wp_web_page_sk = wr.wp_web_page_sk
 ) x
 group by rollup (channel, id)
 order by channel
         ,id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ss as
 (select s_store_sk,
         sum(ss_ext_sales_price) as sales,
         sum(ss_net_profit) as profit
 from store_sales,
      date_dim,
      store
 where ss_sold_date_sk = d_date_sk
       and d_date between cast('2001-08-05' as date) 
                  and (cast('2001-08-05' as date) +  30 ) 
       and ss_store_sk = s_store_sk
 group by s_store_sk)
 ,
 sr as
 (select s_store_sk,
         sum(sr_return_amt) as returns,
         sum(sr_net_loss) as profit_loss
 from store_returns,
      date_dim,
      store
 where sr_returned_date_sk = d_date_sk
       and d_date between cast('2001-08-05' as date)
                  and (cast('2001-08-05' as date) +  30 )
       and sr_store_sk = s_store_sk
 group by s_store_sk), 
 cs as
 (select cs_call_center_sk,
        sum(cs_ext_sales_price) as sales,
        sum(cs_net_profit) as profit
 from catalog_sales,
      date_dim
 where cs_sold_date_sk = d_date_sk
       and d_date between cast('2001-08-05' as date)
                  and (cast('2001-08-05' as date) +  30 )
 group by cs_call_center_sk 
 ), 
 cr as
 (select cr_call_center_sk,
         sum(cr_return_amount) as returns,
         sum(cr_net_loss) as profit_loss
 from catalog_returns,
      date_dim
 where cr_returned_date_sk = d_date_sk
       and d_date between cast('2001-08-05' as date)
                  and (cast('2001-08-05' as date) +  30 )
 group by cr_call_center_sk
 ), 
 ws as
 ( select wp_web_page_sk,
        sum(ws_ext_sales_price) as sales,
        sum(ws_net_profit) as profit
 from web_sales,
      date_dim,
      web_page
 where ws_sold_date_sk = d_date_sk
       and d_date between cast('2001-08-05' as date)
                  and (cast('2001-08-05' as date) +  30 )
       and ws_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk), 
 wr as
 (select wp_web_page_sk,
        sum(wr_return_amt) as returns,
        sum(wr_net_loss) as profit_loss
 from web_returns,
      date_dim,
      web_page
 where wr_returned_date_sk = d_date_sk
       and d_date between cast('2001-08-05' as date)
                  and (cast('2001-08-05' as date) +  30 )
       and wr_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk)
  select  channel
        , id
        , sum(sales) as sales
        , sum(returns) as returns
        , sum(profit) as profit
 from 
 (select 'store channel' as channel
        , ss.s_store_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ss left join sr
        on  ss.s_store_sk = sr.s_store_sk
 union all
 select 'catalog channel' as channel
        , cs_call_center_sk as id
        , sales
        , returns
        , (profit - profit_loss) as profit
 from  cs
       , cr
 union all
 select 'web channel' as channel
        , ws.wp_web_page_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ws left join wr
        on  ws.wp_web_page_sk = wr.wp_web_page_sk
 ) x
 group by rollup (channel, id)
 order by channel
         ,id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ss as
 (select s_store_sk,
         sum(ss_ext_sales_price) as sales,
         sum(ss_net_profit) as profit
 from store_sales,
      date_dim,
      store
 where ss_sold_date_sk = d_date_sk
       and d_date between cast('1999-08-13' as date) 
                  and (cast('1999-08-13' as date) +  30 ) 
       and ss_store_sk = s_store_sk
 group by s_store_sk)
 ,
 sr as
 (select s_store_sk,
         sum(sr_return_amt) as returns,
         sum(sr_net_loss) as profit_loss
 from store_returns,
      date_dim,
      store
 where sr_returned_date_sk = d_date_sk
       and d_date between cast('1999-08-13' as date)
                  and (cast('1999-08-13' as date) +  30 )
       and sr_store_sk = s_store_sk
 group by s_store_sk), 
 cs as
 (select cs_call_center_sk,
        sum(cs_ext_sales_price) as sales,
        sum(cs_net_profit) as profit
 from catalog_sales,
      date_dim
 where cs_sold_date_sk = d_date_sk
       and d_date between cast('1999-08-13' as date)
                  and (cast('1999-08-13' as date) +  30 )
 group by cs_call_center_sk 
 ), 
 cr as
 (select cr_call_center_sk,
         sum(cr_return_amount) as returns,
         sum(cr_net_loss) as profit_loss
 from catalog_returns,
      date_dim
 where cr_returned_date_sk = d_date_sk
       and d_date between cast('1999-08-13' as date)
                  and (cast('1999-08-13' as date) +  30 )
 group by cr_call_center_sk
 ), 
 ws as
 ( select wp_web_page_sk,
        sum(ws_ext_sales_price) as sales,
        sum(ws_net_profit) as profit
 from web_sales,
      date_dim,
      web_page
 where ws_sold_date_sk = d_date_sk
       and d_date between cast('1999-08-13' as date)
                  and (cast('1999-08-13' as date) +  30 )
       and ws_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk), 
 wr as
 (select wp_web_page_sk,
        sum(wr_return_amt) as returns,
        sum(wr_net_loss) as profit_loss
 from web_returns,
      date_dim,
      web_page
 where wr_returned_date_sk = d_date_sk
       and d_date between cast('1999-08-13' as date)
                  and (cast('1999-08-13' as date) +  30 )
       and wr_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk)
  select  channel
        , id
        , sum(sales) as sales
        , sum(returns) as returns
        , sum(profit) as profit
 from 
 (select 'store channel' as channel
        , ss.s_store_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ss left join sr
        on  ss.s_store_sk = sr.s_store_sk
 union all
 select 'catalog channel' as channel
        , cs_call_center_sk as id
        , sales
        , returns
        , (profit - profit_loss) as profit
 from  cs
       , cr
 union all
 select 'web channel' as channel
        , ws.wp_web_page_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ws left join wr
        on  ws.wp_web_page_sk = wr.wp_web_page_sk
 ) x
 group by rollup (channel, id)
 order by channel
         ,id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ss as
 (select s_store_sk,
         sum(ss_ext_sales_price) as sales,
         sum(ss_net_profit) as profit
 from store_sales,
      date_dim,
      store
 where ss_sold_date_sk = d_date_sk
       and d_date between cast('1998-08-27' as date) 
                  and (cast('1998-08-27' as date) +  30 ) 
       and ss_store_sk = s_store_sk
 group by s_store_sk)
 ,
 sr as
 (select s_store_sk,
         sum(sr_return_amt) as returns,
         sum(sr_net_loss) as profit_loss
 from store_returns,
      date_dim,
      store
 where sr_returned_date_sk = d_date_sk
       and d_date between cast('1998-08-27' as date)
                  and (cast('1998-08-27' as date) +  30 )
       and sr_store_sk = s_store_sk
 group by s_store_sk), 
 cs as
 (select cs_call_center_sk,
        sum(cs_ext_sales_price) as sales,
        sum(cs_net_profit) as profit
 from catalog_sales,
      date_dim
 where cs_sold_date_sk = d_date_sk
       and d_date between cast('1998-08-27' as date)
                  and (cast('1998-08-27' as date) +  30 )
 group by cs_call_center_sk 
 ), 
 cr as
 (select cr_call_center_sk,
         sum(cr_return_amount) as returns,
         sum(cr_net_loss) as profit_loss
 from catalog_returns,
      date_dim
 where cr_returned_date_sk = d_date_sk
       and d_date between cast('1998-08-27' as date)
                  and (cast('1998-08-27' as date) +  30 )
 group by cr_call_center_sk
 ), 
 ws as
 ( select wp_web_page_sk,
        sum(ws_ext_sales_price) as sales,
        sum(ws_net_profit) as profit
 from web_sales,
      date_dim,
      web_page
 where ws_sold_date_sk = d_date_sk
       and d_date between cast('1998-08-27' as date)
                  and (cast('1998-08-27' as date) +  30 )
       and ws_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk), 
 wr as
 (select wp_web_page_sk,
        sum(wr_return_amt) as returns,
        sum(wr_net_loss) as profit_loss
 from web_returns,
      date_dim,
      web_page
 where wr_returned_date_sk = d_date_sk
       and d_date between cast('1998-08-27' as date)
                  and (cast('1998-08-27' as date) +  30 )
       and wr_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk)
  select  channel
        , id
        , sum(sales) as sales
        , sum(returns) as returns
        , sum(profit) as profit
 from 
 (select 'store channel' as channel
        , ss.s_store_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ss left join sr
        on  ss.s_store_sk = sr.s_store_sk
 union all
 select 'catalog channel' as channel
        , cs_call_center_sk as id
        , sales
        , returns
        , (profit - profit_loss) as profit
 from  cs
       , cr
 union all
 select 'web channel' as channel
        , ws.wp_web_page_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ws left join wr
        on  ws.wp_web_page_sk = wr.wp_web_page_sk
 ) x
 group by rollup (channel, id)
 order by channel
         ,id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ss as
 (select s_store_sk,
         sum(ss_ext_sales_price) as sales,
         sum(ss_net_profit) as profit
 from store_sales,
      date_dim,
      store
 where ss_sold_date_sk = d_date_sk
       and d_date between cast('2001-08-29' as date) 
                  and (cast('2001-08-29' as date) +  30 ) 
       and ss_store_sk = s_store_sk
 group by s_store_sk)
 ,
 sr as
 (select s_store_sk,
         sum(sr_return_amt) as returns,
         sum(sr_net_loss) as profit_loss
 from store_returns,
      date_dim,
      store
 where sr_returned_date_sk = d_date_sk
       and d_date between cast('2001-08-29' as date)
                  and (cast('2001-08-29' as date) +  30 )
       and sr_store_sk = s_store_sk
 group by s_store_sk), 
 cs as
 (select cs_call_center_sk,
        sum(cs_ext_sales_price) as sales,
        sum(cs_net_profit) as profit
 from catalog_sales,
      date_dim
 where cs_sold_date_sk = d_date_sk
       and d_date between cast('2001-08-29' as date)
                  and (cast('2001-08-29' as date) +  30 )
 group by cs_call_center_sk 
 ), 
 cr as
 (select cr_call_center_sk,
         sum(cr_return_amount) as returns,
         sum(cr_net_loss) as profit_loss
 from catalog_returns,
      date_dim
 where cr_returned_date_sk = d_date_sk
       and d_date between cast('2001-08-29' as date)
                  and (cast('2001-08-29' as date) +  30 )
 group by cr_call_center_sk
 ), 
 ws as
 ( select wp_web_page_sk,
        sum(ws_ext_sales_price) as sales,
        sum(ws_net_profit) as profit
 from web_sales,
      date_dim,
      web_page
 where ws_sold_date_sk = d_date_sk
       and d_date between cast('2001-08-29' as date)
                  and (cast('2001-08-29' as date) +  30 )
       and ws_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk), 
 wr as
 (select wp_web_page_sk,
        sum(wr_return_amt) as returns,
        sum(wr_net_loss) as profit_loss
 from web_returns,
      date_dim,
      web_page
 where wr_returned_date_sk = d_date_sk
       and d_date between cast('2001-08-29' as date)
                  and (cast('2001-08-29' as date) +  30 )
       and wr_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk)
  select  channel
        , id
        , sum(sales) as sales
        , sum(returns) as returns
        , sum(profit) as profit
 from 
 (select 'store channel' as channel
        , ss.s_store_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ss left join sr
        on  ss.s_store_sk = sr.s_store_sk
 union all
 select 'catalog channel' as channel
        , cs_call_center_sk as id
        , sales
        , returns
        , (profit - profit_loss) as profit
 from  cs
       , cr
 union all
 select 'web channel' as channel
        , ws.wp_web_page_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ws left join wr
        on  ws.wp_web_page_sk = wr.wp_web_page_sk
 ) x
 group by rollup (channel, id)
 order by channel
         ,id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ss as
 (select s_store_sk,
         sum(ss_ext_sales_price) as sales,
         sum(ss_net_profit) as profit
 from store_sales,
      date_dim,
      store
 where ss_sold_date_sk = d_date_sk
       and d_date between cast('2001-08-28' as date) 
                  and (cast('2001-08-28' as date) +  30 ) 
       and ss_store_sk = s_store_sk
 group by s_store_sk)
 ,
 sr as
 (select s_store_sk,
         sum(sr_return_amt) as returns,
         sum(sr_net_loss) as profit_loss
 from store_returns,
      date_dim,
      store
 where sr_returned_date_sk = d_date_sk
       and d_date between cast('2001-08-28' as date)
                  and (cast('2001-08-28' as date) +  30 )
       and sr_store_sk = s_store_sk
 group by s_store_sk), 
 cs as
 (select cs_call_center_sk,
        sum(cs_ext_sales_price) as sales,
        sum(cs_net_profit) as profit
 from catalog_sales,
      date_dim
 where cs_sold_date_sk = d_date_sk
       and d_date between cast('2001-08-28' as date)
                  and (cast('2001-08-28' as date) +  30 )
 group by cs_call_center_sk 
 ), 
 cr as
 (select cr_call_center_sk,
         sum(cr_return_amount) as returns,
         sum(cr_net_loss) as profit_loss
 from catalog_returns,
      date_dim
 where cr_returned_date_sk = d_date_sk
       and d_date between cast('2001-08-28' as date)
                  and (cast('2001-08-28' as date) +  30 )
 group by cr_call_center_sk
 ), 
 ws as
 ( select wp_web_page_sk,
        sum(ws_ext_sales_price) as sales,
        sum(ws_net_profit) as profit
 from web_sales,
      date_dim,
      web_page
 where ws_sold_date_sk = d_date_sk
       and d_date between cast('2001-08-28' as date)
                  and (cast('2001-08-28' as date) +  30 )
       and ws_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk), 
 wr as
 (select wp_web_page_sk,
        sum(wr_return_amt) as returns,
        sum(wr_net_loss) as profit_loss
 from web_returns,
      date_dim,
      web_page
 where wr_returned_date_sk = d_date_sk
       and d_date between cast('2001-08-28' as date)
                  and (cast('2001-08-28' as date) +  30 )
       and wr_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk)
  select  channel
        , id
        , sum(sales) as sales
        , sum(returns) as returns
        , sum(profit) as profit
 from 
 (select 'store channel' as channel
        , ss.s_store_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ss left join sr
        on  ss.s_store_sk = sr.s_store_sk
 union all
 select 'catalog channel' as channel
        , cs_call_center_sk as id
        , sales
        , returns
        , (profit - profit_loss) as profit
 from  cs
       , cr
 union all
 select 'web channel' as channel
        , ws.wp_web_page_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ws left join wr
        on  ws.wp_web_page_sk = wr.wp_web_page_sk
 ) x
 group by rollup (channel, id)
 order by channel
         ,id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ss as
 (select s_store_sk,
         sum(ss_ext_sales_price) as sales,
         sum(ss_net_profit) as profit
 from store_sales,
      date_dim,
      store
 where ss_sold_date_sk = d_date_sk
       and d_date between cast('2000-08-23' as date) 
                  and (cast('2000-08-23' as date) +  30 ) 
       and ss_store_sk = s_store_sk
 group by s_store_sk)
 ,
 sr as
 (select s_store_sk,
         sum(sr_return_amt) as returns,
         sum(sr_net_loss) as profit_loss
 from store_returns,
      date_dim,
      store
 where sr_returned_date_sk = d_date_sk
       and d_date between cast('2000-08-23' as date)
                  and (cast('2000-08-23' as date) +  30 )
       and sr_store_sk = s_store_sk
 group by s_store_sk), 
 cs as
 (select cs_call_center_sk,
        sum(cs_ext_sales_price) as sales,
        sum(cs_net_profit) as profit
 from catalog_sales,
      date_dim
 where cs_sold_date_sk = d_date_sk
       and d_date between cast('2000-08-23' as date)
                  and (cast('2000-08-23' as date) +  30 )
 group by cs_call_center_sk 
 ), 
 cr as
 (select cr_call_center_sk,
         sum(cr_return_amount) as returns,
         sum(cr_net_loss) as profit_loss
 from catalog_returns,
      date_dim
 where cr_returned_date_sk = d_date_sk
       and d_date between cast('2000-08-23' as date)
                  and (cast('2000-08-23' as date) +  30 )
 group by cr_call_center_sk
 ), 
 ws as
 ( select wp_web_page_sk,
        sum(ws_ext_sales_price) as sales,
        sum(ws_net_profit) as profit
 from web_sales,
      date_dim,
      web_page
 where ws_sold_date_sk = d_date_sk
       and d_date between cast('2000-08-23' as date)
                  and (cast('2000-08-23' as date) +  30 )
       and ws_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk), 
 wr as
 (select wp_web_page_sk,
        sum(wr_return_amt) as returns,
        sum(wr_net_loss) as profit_loss
 from web_returns,
      date_dim,
      web_page
 where wr_returned_date_sk = d_date_sk
       and d_date between cast('2000-08-23' as date)
                  and (cast('2000-08-23' as date) +  30 )
       and wr_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk)
  select  channel
        , id
        , sum(sales) as sales
        , sum(returns) as returns
        , sum(profit) as profit
 from 
 (select 'store channel' as channel
        , ss.s_store_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ss left join sr
        on  ss.s_store_sk = sr.s_store_sk
 union all
 select 'catalog channel' as channel
        , cs_call_center_sk as id
        , sales
        , returns
        , (profit - profit_loss) as profit
 from  cs
       , cr
 union all
 select 'web channel' as channel
        , ws.wp_web_page_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ws left join wr
        on  ws.wp_web_page_sk = wr.wp_web_page_sk
 ) x
 group by rollup (channel, id)
 order by channel
         ,id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ss as
 (select s_store_sk,
         sum(ss_ext_sales_price) as sales,
         sum(ss_net_profit) as profit
 from store_sales,
      date_dim,
      store
 where ss_sold_date_sk = d_date_sk
       and d_date between cast('1998-08-24' as date) 
                  and (cast('1998-08-24' as date) +  30 ) 
       and ss_store_sk = s_store_sk
 group by s_store_sk)
 ,
 sr as
 (select s_store_sk,
         sum(sr_return_amt) as returns,
         sum(sr_net_loss) as profit_loss
 from store_returns,
      date_dim,
      store
 where sr_returned_date_sk = d_date_sk
       and d_date between cast('1998-08-24' as date)
                  and (cast('1998-08-24' as date) +  30 )
       and sr_store_sk = s_store_sk
 group by s_store_sk), 
 cs as
 (select cs_call_center_sk,
        sum(cs_ext_sales_price) as sales,
        sum(cs_net_profit) as profit
 from catalog_sales,
      date_dim
 where cs_sold_date_sk = d_date_sk
       and d_date between cast('1998-08-24' as date)
                  and (cast('1998-08-24' as date) +  30 )
 group by cs_call_center_sk 
 ), 
 cr as
 (select cr_call_center_sk,
         sum(cr_return_amount) as returns,
         sum(cr_net_loss) as profit_loss
 from catalog_returns,
      date_dim
 where cr_returned_date_sk = d_date_sk
       and d_date between cast('1998-08-24' as date)
                  and (cast('1998-08-24' as date) +  30 )
 group by cr_call_center_sk
 ), 
 ws as
 ( select wp_web_page_sk,
        sum(ws_ext_sales_price) as sales,
        sum(ws_net_profit) as profit
 from web_sales,
      date_dim,
      web_page
 where ws_sold_date_sk = d_date_sk
       and d_date between cast('1998-08-24' as date)
                  and (cast('1998-08-24' as date) +  30 )
       and ws_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk), 
 wr as
 (select wp_web_page_sk,
        sum(wr_return_amt) as returns,
        sum(wr_net_loss) as profit_loss
 from web_returns,
      date_dim,
      web_page
 where wr_returned_date_sk = d_date_sk
       and d_date between cast('1998-08-24' as date)
                  and (cast('1998-08-24' as date) +  30 )
       and wr_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk)
  select  channel
        , id
        , sum(sales) as sales
        , sum(returns) as returns
        , sum(profit) as profit
 from 
 (select 'store channel' as channel
        , ss.s_store_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ss left join sr
        on  ss.s_store_sk = sr.s_store_sk
 union all
 select 'catalog channel' as channel
        , cs_call_center_sk as id
        , sales
        , returns
        , (profit - profit_loss) as profit
 from  cs
       , cr
 union all
 select 'web channel' as channel
        , ws.wp_web_page_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ws left join wr
        on  ws.wp_web_page_sk = wr.wp_web_page_sk
 ) x
 group by rollup (channel, id)
 order by channel
         ,id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ss as
 (select s_store_sk,
         sum(ss_ext_sales_price) as sales,
         sum(ss_net_profit) as profit
 from store_sales,
      date_dim,
      store
 where ss_sold_date_sk = d_date_sk
       and d_date between cast('2001-08-25' as date) 
                  and (cast('2001-08-25' as date) +  30 ) 
       and ss_store_sk = s_store_sk
 group by s_store_sk)
 ,
 sr as
 (select s_store_sk,
         sum(sr_return_amt) as returns,
         sum(sr_net_loss) as profit_loss
 from store_returns,
      date_dim,
      store
 where sr_returned_date_sk = d_date_sk
       and d_date between cast('2001-08-25' as date)
                  and (cast('2001-08-25' as date) +  30 )
       and sr_store_sk = s_store_sk
 group by s_store_sk), 
 cs as
 (select cs_call_center_sk,
        sum(cs_ext_sales_price) as sales,
        sum(cs_net_profit) as profit
 from catalog_sales,
      date_dim
 where cs_sold_date_sk = d_date_sk
       and d_date between cast('2001-08-25' as date)
                  and (cast('2001-08-25' as date) +  30 )
 group by cs_call_center_sk 
 ), 
 cr as
 (select cr_call_center_sk,
         sum(cr_return_amount) as returns,
         sum(cr_net_loss) as profit_loss
 from catalog_returns,
      date_dim
 where cr_returned_date_sk = d_date_sk
       and d_date between cast('2001-08-25' as date)
                  and (cast('2001-08-25' as date) +  30 )
 group by cr_call_center_sk
 ), 
 ws as
 ( select wp_web_page_sk,
        sum(ws_ext_sales_price) as sales,
        sum(ws_net_profit) as profit
 from web_sales,
      date_dim,
      web_page
 where ws_sold_date_sk = d_date_sk
       and d_date between cast('2001-08-25' as date)
                  and (cast('2001-08-25' as date) +  30 )
       and ws_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk), 
 wr as
 (select wp_web_page_sk,
        sum(wr_return_amt) as returns,
        sum(wr_net_loss) as profit_loss
 from web_returns,
      date_dim,
      web_page
 where wr_returned_date_sk = d_date_sk
       and d_date between cast('2001-08-25' as date)
                  and (cast('2001-08-25' as date) +  30 )
       and wr_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk)
  select  channel
        , id
        , sum(sales) as sales
        , sum(returns) as returns
        , sum(profit) as profit
 from 
 (select 'store channel' as channel
        , ss.s_store_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ss left join sr
        on  ss.s_store_sk = sr.s_store_sk
 union all
 select 'catalog channel' as channel
        , cs_call_center_sk as id
        , sales
        , returns
        , (profit - profit_loss) as profit
 from  cs
       , cr
 union all
 select 'web channel' as channel
        , ws.wp_web_page_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ws left join wr
        on  ws.wp_web_page_sk = wr.wp_web_page_sk
 ) x
 group by rollup (channel, id)
 order by channel
         ,id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ss as
 (select s_store_sk,
         sum(ss_ext_sales_price) as sales,
         sum(ss_net_profit) as profit
 from store_sales,
      date_dim,
      store
 where ss_sold_date_sk = d_date_sk
       and d_date between cast('2000-08-24' as date) 
                  and (cast('2000-08-24' as date) +  30 ) 
       and ss_store_sk = s_store_sk
 group by s_store_sk)
 ,
 sr as
 (select s_store_sk,
         sum(sr_return_amt) as returns,
         sum(sr_net_loss) as profit_loss
 from store_returns,
      date_dim,
      store
 where sr_returned_date_sk = d_date_sk
       and d_date between cast('2000-08-24' as date)
                  and (cast('2000-08-24' as date) +  30 )
       and sr_store_sk = s_store_sk
 group by s_store_sk), 
 cs as
 (select cs_call_center_sk,
        sum(cs_ext_sales_price) as sales,
        sum(cs_net_profit) as profit
 from catalog_sales,
      date_dim
 where cs_sold_date_sk = d_date_sk
       and d_date between cast('2000-08-24' as date)
                  and (cast('2000-08-24' as date) +  30 )
 group by cs_call_center_sk 
 ), 
 cr as
 (select cr_call_center_sk,
         sum(cr_return_amount) as returns,
         sum(cr_net_loss) as profit_loss
 from catalog_returns,
      date_dim
 where cr_returned_date_sk = d_date_sk
       and d_date between cast('2000-08-24' as date)
                  and (cast('2000-08-24' as date) +  30 )
 group by cr_call_center_sk
 ), 
 ws as
 ( select wp_web_page_sk,
        sum(ws_ext_sales_price) as sales,
        sum(ws_net_profit) as profit
 from web_sales,
      date_dim,
      web_page
 where ws_sold_date_sk = d_date_sk
       and d_date between cast('2000-08-24' as date)
                  and (cast('2000-08-24' as date) +  30 )
       and ws_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk), 
 wr as
 (select wp_web_page_sk,
        sum(wr_return_amt) as returns,
        sum(wr_net_loss) as profit_loss
 from web_returns,
      date_dim,
      web_page
 where wr_returned_date_sk = d_date_sk
       and d_date between cast('2000-08-24' as date)
                  and (cast('2000-08-24' as date) +  30 )
       and wr_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk)
  select  channel
        , id
        , sum(sales) as sales
        , sum(returns) as returns
        , sum(profit) as profit
 from 
 (select 'store channel' as channel
        , ss.s_store_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ss left join sr
        on  ss.s_store_sk = sr.s_store_sk
 union all
 select 'catalog channel' as channel
        , cs_call_center_sk as id
        , sales
        , returns
        , (profit - profit_loss) as profit
 from  cs
       , cr
 union all
 select 'web channel' as channel
        , ws.wp_web_page_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ws left join wr
        on  ws.wp_web_page_sk = wr.wp_web_page_sk
 ) x
 group by rollup (channel, id)
 order by channel
         ,id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ss as
 (select s_store_sk,
         sum(ss_ext_sales_price) as sales,
         sum(ss_net_profit) as profit
 from store_sales,
      date_dim,
      store
 where ss_sold_date_sk = d_date_sk
       and d_date between cast('1998-08-21' as date) 
                  and (cast('1998-08-21' as date) +  30 ) 
       and ss_store_sk = s_store_sk
 group by s_store_sk)
 ,
 sr as
 (select s_store_sk,
         sum(sr_return_amt) as returns,
         sum(sr_net_loss) as profit_loss
 from store_returns,
      date_dim,
      store
 where sr_returned_date_sk = d_date_sk
       and d_date between cast('1998-08-21' as date)
                  and (cast('1998-08-21' as date) +  30 )
       and sr_store_sk = s_store_sk
 group by s_store_sk), 
 cs as
 (select cs_call_center_sk,
        sum(cs_ext_sales_price) as sales,
        sum(cs_net_profit) as profit
 from catalog_sales,
      date_dim
 where cs_sold_date_sk = d_date_sk
       and d_date between cast('1998-08-21' as date)
                  and (cast('1998-08-21' as date) +  30 )
 group by cs_call_center_sk 
 ), 
 cr as
 (select cr_call_center_sk,
         sum(cr_return_amount) as returns,
         sum(cr_net_loss) as profit_loss
 from catalog_returns,
      date_dim
 where cr_returned_date_sk = d_date_sk
       and d_date between cast('1998-08-21' as date)
                  and (cast('1998-08-21' as date) +  30 )
 group by cr_call_center_sk
 ), 
 ws as
 ( select wp_web_page_sk,
        sum(ws_ext_sales_price) as sales,
        sum(ws_net_profit) as profit
 from web_sales,
      date_dim,
      web_page
 where ws_sold_date_sk = d_date_sk
       and d_date between cast('1998-08-21' as date)
                  and (cast('1998-08-21' as date) +  30 )
       and ws_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk), 
 wr as
 (select wp_web_page_sk,
        sum(wr_return_amt) as returns,
        sum(wr_net_loss) as profit_loss
 from web_returns,
      date_dim,
      web_page
 where wr_returned_date_sk = d_date_sk
       and d_date between cast('1998-08-21' as date)
                  and (cast('1998-08-21' as date) +  30 )
       and wr_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk)
  select  channel
        , id
        , sum(sales) as sales
        , sum(returns) as returns
        , sum(profit) as profit
 from 
 (select 'store channel' as channel
        , ss.s_store_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ss left join sr
        on  ss.s_store_sk = sr.s_store_sk
 union all
 select 'catalog channel' as channel
        , cs_call_center_sk as id
        , sales
        , returns
        , (profit - profit_loss) as profit
 from  cs
       , cr
 union all
 select 'web channel' as channel
        , ws.wp_web_page_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ws left join wr
        on  ws.wp_web_page_sk = wr.wp_web_page_sk
 ) x
 group by rollup (channel, id)
 order by channel
         ,id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ss as
 (select s_store_sk,
         sum(ss_ext_sales_price) as sales,
         sum(ss_net_profit) as profit
 from store_sales,
      date_dim,
      store
 where ss_sold_date_sk = d_date_sk
       and d_date between cast('1999-08-21' as date) 
                  and (cast('1999-08-21' as date) +  30 ) 
       and ss_store_sk = s_store_sk
 group by s_store_sk)
 ,
 sr as
 (select s_store_sk,
         sum(sr_return_amt) as returns,
         sum(sr_net_loss) as profit_loss
 from store_returns,
      date_dim,
      store
 where sr_returned_date_sk = d_date_sk
       and d_date between cast('1999-08-21' as date)
                  and (cast('1999-08-21' as date) +  30 )
       and sr_store_sk = s_store_sk
 group by s_store_sk), 
 cs as
 (select cs_call_center_sk,
        sum(cs_ext_sales_price) as sales,
        sum(cs_net_profit) as profit
 from catalog_sales,
      date_dim
 where cs_sold_date_sk = d_date_sk
       and d_date between cast('1999-08-21' as date)
                  and (cast('1999-08-21' as date) +  30 )
 group by cs_call_center_sk 
 ), 
 cr as
 (select cr_call_center_sk,
         sum(cr_return_amount) as returns,
         sum(cr_net_loss) as profit_loss
 from catalog_returns,
      date_dim
 where cr_returned_date_sk = d_date_sk
       and d_date between cast('1999-08-21' as date)
                  and (cast('1999-08-21' as date) +  30 )
 group by cr_call_center_sk
 ), 
 ws as
 ( select wp_web_page_sk,
        sum(ws_ext_sales_price) as sales,
        sum(ws_net_profit) as profit
 from web_sales,
      date_dim,
      web_page
 where ws_sold_date_sk = d_date_sk
       and d_date between cast('1999-08-21' as date)
                  and (cast('1999-08-21' as date) +  30 )
       and ws_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk), 
 wr as
 (select wp_web_page_sk,
        sum(wr_return_amt) as returns,
        sum(wr_net_loss) as profit_loss
 from web_returns,
      date_dim,
      web_page
 where wr_returned_date_sk = d_date_sk
       and d_date between cast('1999-08-21' as date)
                  and (cast('1999-08-21' as date) +  30 )
       and wr_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk)
  select  channel
        , id
        , sum(sales) as sales
        , sum(returns) as returns
        , sum(profit) as profit
 from 
 (select 'store channel' as channel
        , ss.s_store_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ss left join sr
        on  ss.s_store_sk = sr.s_store_sk
 union all
 select 'catalog channel' as channel
        , cs_call_center_sk as id
        , sales
        , returns
        , (profit - profit_loss) as profit
 from  cs
       , cr
 union all
 select 'web channel' as channel
        , ws.wp_web_page_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ws left join wr
        on  ws.wp_web_page_sk = wr.wp_web_page_sk
 ) x
 group by rollup (channel, id)
 order by channel
         ,id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ss as
 (select s_store_sk,
         sum(ss_ext_sales_price) as sales,
         sum(ss_net_profit) as profit
 from store_sales,
      date_dim,
      store
 where ss_sold_date_sk = d_date_sk
       and d_date between cast('1999-08-04' as date) 
                  and (cast('1999-08-04' as date) +  30 ) 
       and ss_store_sk = s_store_sk
 group by s_store_sk)
 ,
 sr as
 (select s_store_sk,
         sum(sr_return_amt) as returns,
         sum(sr_net_loss) as profit_loss
 from store_returns,
      date_dim,
      store
 where sr_returned_date_sk = d_date_sk
       and d_date between cast('1999-08-04' as date)
                  and (cast('1999-08-04' as date) +  30 )
       and sr_store_sk = s_store_sk
 group by s_store_sk), 
 cs as
 (select cs_call_center_sk,
        sum(cs_ext_sales_price) as sales,
        sum(cs_net_profit) as profit
 from catalog_sales,
      date_dim
 where cs_sold_date_sk = d_date_sk
       and d_date between cast('1999-08-04' as date)
                  and (cast('1999-08-04' as date) +  30 )
 group by cs_call_center_sk 
 ), 
 cr as
 (select cr_call_center_sk,
         sum(cr_return_amount) as returns,
         sum(cr_net_loss) as profit_loss
 from catalog_returns,
      date_dim
 where cr_returned_date_sk = d_date_sk
       and d_date between cast('1999-08-04' as date)
                  and (cast('1999-08-04' as date) +  30 )
 group by cr_call_center_sk
 ), 
 ws as
 ( select wp_web_page_sk,
        sum(ws_ext_sales_price) as sales,
        sum(ws_net_profit) as profit
 from web_sales,
      date_dim,
      web_page
 where ws_sold_date_sk = d_date_sk
       and d_date between cast('1999-08-04' as date)
                  and (cast('1999-08-04' as date) +  30 )
       and ws_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk), 
 wr as
 (select wp_web_page_sk,
        sum(wr_return_amt) as returns,
        sum(wr_net_loss) as profit_loss
 from web_returns,
      date_dim,
      web_page
 where wr_returned_date_sk = d_date_sk
       and d_date between cast('1999-08-04' as date)
                  and (cast('1999-08-04' as date) +  30 )
       and wr_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk)
  select  channel
        , id
        , sum(sales) as sales
        , sum(returns) as returns
        , sum(profit) as profit
 from 
 (select 'store channel' as channel
        , ss.s_store_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ss left join sr
        on  ss.s_store_sk = sr.s_store_sk
 union all
 select 'catalog channel' as channel
        , cs_call_center_sk as id
        , sales
        , returns
        , (profit - profit_loss) as profit
 from  cs
       , cr
 union all
 select 'web channel' as channel
        , ws.wp_web_page_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ws left join wr
        on  ws.wp_web_page_sk = wr.wp_web_page_sk
 ) x
 group by rollup (channel, id)
 order by channel
         ,id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ss as
 (select s_store_sk,
         sum(ss_ext_sales_price) as sales,
         sum(ss_net_profit) as profit
 from store_sales,
      date_dim,
      store
 where ss_sold_date_sk = d_date_sk
       and d_date between cast('1998-08-08' as date) 
                  and (cast('1998-08-08' as date) +  30 ) 
       and ss_store_sk = s_store_sk
 group by s_store_sk)
 ,
 sr as
 (select s_store_sk,
         sum(sr_return_amt) as returns,
         sum(sr_net_loss) as profit_loss
 from store_returns,
      date_dim,
      store
 where sr_returned_date_sk = d_date_sk
       and d_date between cast('1998-08-08' as date)
                  and (cast('1998-08-08' as date) +  30 )
       and sr_store_sk = s_store_sk
 group by s_store_sk), 
 cs as
 (select cs_call_center_sk,
        sum(cs_ext_sales_price) as sales,
        sum(cs_net_profit) as profit
 from catalog_sales,
      date_dim
 where cs_sold_date_sk = d_date_sk
       and d_date between cast('1998-08-08' as date)
                  and (cast('1998-08-08' as date) +  30 )
 group by cs_call_center_sk 
 ), 
 cr as
 (select cr_call_center_sk,
         sum(cr_return_amount) as returns,
         sum(cr_net_loss) as profit_loss
 from catalog_returns,
      date_dim
 where cr_returned_date_sk = d_date_sk
       and d_date between cast('1998-08-08' as date)
                  and (cast('1998-08-08' as date) +  30 )
 group by cr_call_center_sk
 ), 
 ws as
 ( select wp_web_page_sk,
        sum(ws_ext_sales_price) as sales,
        sum(ws_net_profit) as profit
 from web_sales,
      date_dim,
      web_page
 where ws_sold_date_sk = d_date_sk
       and d_date between cast('1998-08-08' as date)
                  and (cast('1998-08-08' as date) +  30 )
       and ws_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk), 
 wr as
 (select wp_web_page_sk,
        sum(wr_return_amt) as returns,
        sum(wr_net_loss) as profit_loss
 from web_returns,
      date_dim,
      web_page
 where wr_returned_date_sk = d_date_sk
       and d_date between cast('1998-08-08' as date)
                  and (cast('1998-08-08' as date) +  30 )
       and wr_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk)
  select  channel
        , id
        , sum(sales) as sales
        , sum(returns) as returns
        , sum(profit) as profit
 from 
 (select 'store channel' as channel
        , ss.s_store_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ss left join sr
        on  ss.s_store_sk = sr.s_store_sk
 union all
 select 'catalog channel' as channel
        , cs_call_center_sk as id
        , sales
        , returns
        , (profit - profit_loss) as profit
 from  cs
       , cr
 union all
 select 'web channel' as channel
        , ws.wp_web_page_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ws left join wr
        on  ws.wp_web_page_sk = wr.wp_web_page_sk
 ) x
 group by rollup (channel, id)
 order by channel
         ,id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ss as
 (select s_store_sk,
         sum(ss_ext_sales_price) as sales,
         sum(ss_net_profit) as profit
 from store_sales,
      date_dim,
      store
 where ss_sold_date_sk = d_date_sk
       and d_date between cast('2000-08-16' as date) 
                  and (cast('2000-08-16' as date) +  30 ) 
       and ss_store_sk = s_store_sk
 group by s_store_sk)
 ,
 sr as
 (select s_store_sk,
         sum(sr_return_amt) as returns,
         sum(sr_net_loss) as profit_loss
 from store_returns,
      date_dim,
      store
 where sr_returned_date_sk = d_date_sk
       and d_date between cast('2000-08-16' as date)
                  and (cast('2000-08-16' as date) +  30 )
       and sr_store_sk = s_store_sk
 group by s_store_sk), 
 cs as
 (select cs_call_center_sk,
        sum(cs_ext_sales_price) as sales,
        sum(cs_net_profit) as profit
 from catalog_sales,
      date_dim
 where cs_sold_date_sk = d_date_sk
       and d_date between cast('2000-08-16' as date)
                  and (cast('2000-08-16' as date) +  30 )
 group by cs_call_center_sk 
 ), 
 cr as
 (select cr_call_center_sk,
         sum(cr_return_amount) as returns,
         sum(cr_net_loss) as profit_loss
 from catalog_returns,
      date_dim
 where cr_returned_date_sk = d_date_sk
       and d_date between cast('2000-08-16' as date)
                  and (cast('2000-08-16' as date) +  30 )
 group by cr_call_center_sk
 ), 
 ws as
 ( select wp_web_page_sk,
        sum(ws_ext_sales_price) as sales,
        sum(ws_net_profit) as profit
 from web_sales,
      date_dim,
      web_page
 where ws_sold_date_sk = d_date_sk
       and d_date between cast('2000-08-16' as date)
                  and (cast('2000-08-16' as date) +  30 )
       and ws_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk), 
 wr as
 (select wp_web_page_sk,
        sum(wr_return_amt) as returns,
        sum(wr_net_loss) as profit_loss
 from web_returns,
      date_dim,
      web_page
 where wr_returned_date_sk = d_date_sk
       and d_date between cast('2000-08-16' as date)
                  and (cast('2000-08-16' as date) +  30 )
       and wr_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk)
  select  channel
        , id
        , sum(sales) as sales
        , sum(returns) as returns
        , sum(profit) as profit
 from 
 (select 'store channel' as channel
        , ss.s_store_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ss left join sr
        on  ss.s_store_sk = sr.s_store_sk
 union all
 select 'catalog channel' as channel
        , cs_call_center_sk as id
        , sales
        , returns
        , (profit - profit_loss) as profit
 from  cs
       , cr
 union all
 select 'web channel' as channel
        , ws.wp_web_page_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ws left join wr
        on  ws.wp_web_page_sk = wr.wp_web_page_sk
 ) x
 group by rollup (channel, id)
 order by channel
         ,id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ss as
 (select s_store_sk,
         sum(ss_ext_sales_price) as sales,
         sum(ss_net_profit) as profit
 from store_sales,
      date_dim,
      store
 where ss_sold_date_sk = d_date_sk
       and d_date between cast('1998-08-03' as date) 
                  and (cast('1998-08-03' as date) +  30 ) 
       and ss_store_sk = s_store_sk
 group by s_store_sk)
 ,
 sr as
 (select s_store_sk,
         sum(sr_return_amt) as returns,
         sum(sr_net_loss) as profit_loss
 from store_returns,
      date_dim,
      store
 where sr_returned_date_sk = d_date_sk
       and d_date between cast('1998-08-03' as date)
                  and (cast('1998-08-03' as date) +  30 )
       and sr_store_sk = s_store_sk
 group by s_store_sk), 
 cs as
 (select cs_call_center_sk,
        sum(cs_ext_sales_price) as sales,
        sum(cs_net_profit) as profit
 from catalog_sales,
      date_dim
 where cs_sold_date_sk = d_date_sk
       and d_date between cast('1998-08-03' as date)
                  and (cast('1998-08-03' as date) +  30 )
 group by cs_call_center_sk 
 ), 
 cr as
 (select cr_call_center_sk,
         sum(cr_return_amount) as returns,
         sum(cr_net_loss) as profit_loss
 from catalog_returns,
      date_dim
 where cr_returned_date_sk = d_date_sk
       and d_date between cast('1998-08-03' as date)
                  and (cast('1998-08-03' as date) +  30 )
 group by cr_call_center_sk
 ), 
 ws as
 ( select wp_web_page_sk,
        sum(ws_ext_sales_price) as sales,
        sum(ws_net_profit) as profit
 from web_sales,
      date_dim,
      web_page
 where ws_sold_date_sk = d_date_sk
       and d_date between cast('1998-08-03' as date)
                  and (cast('1998-08-03' as date) +  30 )
       and ws_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk), 
 wr as
 (select wp_web_page_sk,
        sum(wr_return_amt) as returns,
        sum(wr_net_loss) as profit_loss
 from web_returns,
      date_dim,
      web_page
 where wr_returned_date_sk = d_date_sk
       and d_date between cast('1998-08-03' as date)
                  and (cast('1998-08-03' as date) +  30 )
       and wr_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk)
  select  channel
        , id
        , sum(sales) as sales
        , sum(returns) as returns
        , sum(profit) as profit
 from 
 (select 'store channel' as channel
        , ss.s_store_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ss left join sr
        on  ss.s_store_sk = sr.s_store_sk
 union all
 select 'catalog channel' as channel
        , cs_call_center_sk as id
        , sales
        , returns
        , (profit - profit_loss) as profit
 from  cs
       , cr
 union all
 select 'web channel' as channel
        , ws.wp_web_page_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ws left join wr
        on  ws.wp_web_page_sk = wr.wp_web_page_sk
 ) x
 group by rollup (channel, id)
 order by channel
         ,id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ss as
 (select s_store_sk,
         sum(ss_ext_sales_price) as sales,
         sum(ss_net_profit) as profit
 from store_sales,
      date_dim,
      store
 where ss_sold_date_sk = d_date_sk
       and d_date between cast('1998-08-22' as date) 
                  and (cast('1998-08-22' as date) +  30 ) 
       and ss_store_sk = s_store_sk
 group by s_store_sk)
 ,
 sr as
 (select s_store_sk,
         sum(sr_return_amt) as returns,
         sum(sr_net_loss) as profit_loss
 from store_returns,
      date_dim,
      store
 where sr_returned_date_sk = d_date_sk
       and d_date between cast('1998-08-22' as date)
                  and (cast('1998-08-22' as date) +  30 )
       and sr_store_sk = s_store_sk
 group by s_store_sk), 
 cs as
 (select cs_call_center_sk,
        sum(cs_ext_sales_price) as sales,
        sum(cs_net_profit) as profit
 from catalog_sales,
      date_dim
 where cs_sold_date_sk = d_date_sk
       and d_date between cast('1998-08-22' as date)
                  and (cast('1998-08-22' as date) +  30 )
 group by cs_call_center_sk 
 ), 
 cr as
 (select cr_call_center_sk,
         sum(cr_return_amount) as returns,
         sum(cr_net_loss) as profit_loss
 from catalog_returns,
      date_dim
 where cr_returned_date_sk = d_date_sk
       and d_date between cast('1998-08-22' as date)
                  and (cast('1998-08-22' as date) +  30 )
 group by cr_call_center_sk
 ), 
 ws as
 ( select wp_web_page_sk,
        sum(ws_ext_sales_price) as sales,
        sum(ws_net_profit) as profit
 from web_sales,
      date_dim,
      web_page
 where ws_sold_date_sk = d_date_sk
       and d_date between cast('1998-08-22' as date)
                  and (cast('1998-08-22' as date) +  30 )
       and ws_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk), 
 wr as
 (select wp_web_page_sk,
        sum(wr_return_amt) as returns,
        sum(wr_net_loss) as profit_loss
 from web_returns,
      date_dim,
      web_page
 where wr_returned_date_sk = d_date_sk
       and d_date between cast('1998-08-22' as date)
                  and (cast('1998-08-22' as date) +  30 )
       and wr_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk)
  select  channel
        , id
        , sum(sales) as sales
        , sum(returns) as returns
        , sum(profit) as profit
 from 
 (select 'store channel' as channel
        , ss.s_store_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ss left join sr
        on  ss.s_store_sk = sr.s_store_sk
 union all
 select 'catalog channel' as channel
        , cs_call_center_sk as id
        , sales
        , returns
        , (profit - profit_loss) as profit
 from  cs
       , cr
 union all
 select 'web channel' as channel
        , ws.wp_web_page_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ws left join wr
        on  ws.wp_web_page_sk = wr.wp_web_page_sk
 ) x
 group by rollup (channel, id)
 order by channel
         ,id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ss as
 (select s_store_sk,
         sum(ss_ext_sales_price) as sales,
         sum(ss_net_profit) as profit
 from store_sales,
      date_dim,
      store
 where ss_sold_date_sk = d_date_sk
       and d_date between cast('2001-08-02' as date) 
                  and (cast('2001-08-02' as date) +  30 ) 
       and ss_store_sk = s_store_sk
 group by s_store_sk)
 ,
 sr as
 (select s_store_sk,
         sum(sr_return_amt) as returns,
         sum(sr_net_loss) as profit_loss
 from store_returns,
      date_dim,
      store
 where sr_returned_date_sk = d_date_sk
       and d_date between cast('2001-08-02' as date)
                  and (cast('2001-08-02' as date) +  30 )
       and sr_store_sk = s_store_sk
 group by s_store_sk), 
 cs as
 (select cs_call_center_sk,
        sum(cs_ext_sales_price) as sales,
        sum(cs_net_profit) as profit
 from catalog_sales,
      date_dim
 where cs_sold_date_sk = d_date_sk
       and d_date between cast('2001-08-02' as date)
                  and (cast('2001-08-02' as date) +  30 )
 group by cs_call_center_sk 
 ), 
 cr as
 (select cr_call_center_sk,
         sum(cr_return_amount) as returns,
         sum(cr_net_loss) as profit_loss
 from catalog_returns,
      date_dim
 where cr_returned_date_sk = d_date_sk
       and d_date between cast('2001-08-02' as date)
                  and (cast('2001-08-02' as date) +  30 )
 group by cr_call_center_sk
 ), 
 ws as
 ( select wp_web_page_sk,
        sum(ws_ext_sales_price) as sales,
        sum(ws_net_profit) as profit
 from web_sales,
      date_dim,
      web_page
 where ws_sold_date_sk = d_date_sk
       and d_date between cast('2001-08-02' as date)
                  and (cast('2001-08-02' as date) +  30 )
       and ws_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk), 
 wr as
 (select wp_web_page_sk,
        sum(wr_return_amt) as returns,
        sum(wr_net_loss) as profit_loss
 from web_returns,
      date_dim,
      web_page
 where wr_returned_date_sk = d_date_sk
       and d_date between cast('2001-08-02' as date)
                  and (cast('2001-08-02' as date) +  30 )
       and wr_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk)
  select  channel
        , id
        , sum(sales) as sales
        , sum(returns) as returns
        , sum(profit) as profit
 from 
 (select 'store channel' as channel
        , ss.s_store_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ss left join sr
        on  ss.s_store_sk = sr.s_store_sk
 union all
 select 'catalog channel' as channel
        , cs_call_center_sk as id
        , sales
        , returns
        , (profit - profit_loss) as profit
 from  cs
       , cr
 union all
 select 'web channel' as channel
        , ws.wp_web_page_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ws left join wr
        on  ws.wp_web_page_sk = wr.wp_web_page_sk
 ) x
 group by rollup (channel, id)
 order by channel
         ,id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ss as
 (select s_store_sk,
         sum(ss_ext_sales_price) as sales,
         sum(ss_net_profit) as profit
 from store_sales,
      date_dim,
      store
 where ss_sold_date_sk = d_date_sk
       and d_date between cast('2001-08-10' as date) 
                  and (cast('2001-08-10' as date) +  30 ) 
       and ss_store_sk = s_store_sk
 group by s_store_sk)
 ,
 sr as
 (select s_store_sk,
         sum(sr_return_amt) as returns,
         sum(sr_net_loss) as profit_loss
 from store_returns,
      date_dim,
      store
 where sr_returned_date_sk = d_date_sk
       and d_date between cast('2001-08-10' as date)
                  and (cast('2001-08-10' as date) +  30 )
       and sr_store_sk = s_store_sk
 group by s_store_sk), 
 cs as
 (select cs_call_center_sk,
        sum(cs_ext_sales_price) as sales,
        sum(cs_net_profit) as profit
 from catalog_sales,
      date_dim
 where cs_sold_date_sk = d_date_sk
       and d_date between cast('2001-08-10' as date)
                  and (cast('2001-08-10' as date) +  30 )
 group by cs_call_center_sk 
 ), 
 cr as
 (select cr_call_center_sk,
         sum(cr_return_amount) as returns,
         sum(cr_net_loss) as profit_loss
 from catalog_returns,
      date_dim
 where cr_returned_date_sk = d_date_sk
       and d_date between cast('2001-08-10' as date)
                  and (cast('2001-08-10' as date) +  30 )
 group by cr_call_center_sk
 ), 
 ws as
 ( select wp_web_page_sk,
        sum(ws_ext_sales_price) as sales,
        sum(ws_net_profit) as profit
 from web_sales,
      date_dim,
      web_page
 where ws_sold_date_sk = d_date_sk
       and d_date between cast('2001-08-10' as date)
                  and (cast('2001-08-10' as date) +  30 )
       and ws_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk), 
 wr as
 (select wp_web_page_sk,
        sum(wr_return_amt) as returns,
        sum(wr_net_loss) as profit_loss
 from web_returns,
      date_dim,
      web_page
 where wr_returned_date_sk = d_date_sk
       and d_date between cast('2001-08-10' as date)
                  and (cast('2001-08-10' as date) +  30 )
       and wr_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk)
  select  channel
        , id
        , sum(sales) as sales
        , sum(returns) as returns
        , sum(profit) as profit
 from 
 (select 'store channel' as channel
        , ss.s_store_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ss left join sr
        on  ss.s_store_sk = sr.s_store_sk
 union all
 select 'catalog channel' as channel
        , cs_call_center_sk as id
        , sales
        , returns
        , (profit - profit_loss) as profit
 from  cs
       , cr
 union all
 select 'web channel' as channel
        , ws.wp_web_page_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ws left join wr
        on  ws.wp_web_page_sk = wr.wp_web_page_sk
 ) x
 group by rollup (channel, id)
 order by channel
         ,id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ss as
 (select s_store_sk,
         sum(ss_ext_sales_price) as sales,
         sum(ss_net_profit) as profit
 from store_sales,
      date_dim,
      store
 where ss_sold_date_sk = d_date_sk
       and d_date between cast('2000-08-11' as date) 
                  and (cast('2000-08-11' as date) +  30 ) 
       and ss_store_sk = s_store_sk
 group by s_store_sk)
 ,
 sr as
 (select s_store_sk,
         sum(sr_return_amt) as returns,
         sum(sr_net_loss) as profit_loss
 from store_returns,
      date_dim,
      store
 where sr_returned_date_sk = d_date_sk
       and d_date between cast('2000-08-11' as date)
                  and (cast('2000-08-11' as date) +  30 )
       and sr_store_sk = s_store_sk
 group by s_store_sk), 
 cs as
 (select cs_call_center_sk,
        sum(cs_ext_sales_price) as sales,
        sum(cs_net_profit) as profit
 from catalog_sales,
      date_dim
 where cs_sold_date_sk = d_date_sk
       and d_date between cast('2000-08-11' as date)
                  and (cast('2000-08-11' as date) +  30 )
 group by cs_call_center_sk 
 ), 
 cr as
 (select cr_call_center_sk,
         sum(cr_return_amount) as returns,
         sum(cr_net_loss) as profit_loss
 from catalog_returns,
      date_dim
 where cr_returned_date_sk = d_date_sk
       and d_date between cast('2000-08-11' as date)
                  and (cast('2000-08-11' as date) +  30 )
 group by cr_call_center_sk
 ), 
 ws as
 ( select wp_web_page_sk,
        sum(ws_ext_sales_price) as sales,
        sum(ws_net_profit) as profit
 from web_sales,
      date_dim,
      web_page
 where ws_sold_date_sk = d_date_sk
       and d_date between cast('2000-08-11' as date)
                  and (cast('2000-08-11' as date) +  30 )
       and ws_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk), 
 wr as
 (select wp_web_page_sk,
        sum(wr_return_amt) as returns,
        sum(wr_net_loss) as profit_loss
 from web_returns,
      date_dim,
      web_page
 where wr_returned_date_sk = d_date_sk
       and d_date between cast('2000-08-11' as date)
                  and (cast('2000-08-11' as date) +  30 )
       and wr_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk)
  select  channel
        , id
        , sum(sales) as sales
        , sum(returns) as returns
        , sum(profit) as profit
 from 
 (select 'store channel' as channel
        , ss.s_store_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ss left join sr
        on  ss.s_store_sk = sr.s_store_sk
 union all
 select 'catalog channel' as channel
        , cs_call_center_sk as id
        , sales
        , returns
        , (profit - profit_loss) as profit
 from  cs
       , cr
 union all
 select 'web channel' as channel
        , ws.wp_web_page_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ws left join wr
        on  ws.wp_web_page_sk = wr.wp_web_page_sk
 ) x
 group by rollup (channel, id)
 order by channel
         ,id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ss as
 (select s_store_sk,
         sum(ss_ext_sales_price) as sales,
         sum(ss_net_profit) as profit
 from store_sales,
      date_dim,
      store
 where ss_sold_date_sk = d_date_sk
       and d_date between cast('2001-08-15' as date) 
                  and (cast('2001-08-15' as date) +  30 ) 
       and ss_store_sk = s_store_sk
 group by s_store_sk)
 ,
 sr as
 (select s_store_sk,
         sum(sr_return_amt) as returns,
         sum(sr_net_loss) as profit_loss
 from store_returns,
      date_dim,
      store
 where sr_returned_date_sk = d_date_sk
       and d_date between cast('2001-08-15' as date)
                  and (cast('2001-08-15' as date) +  30 )
       and sr_store_sk = s_store_sk
 group by s_store_sk), 
 cs as
 (select cs_call_center_sk,
        sum(cs_ext_sales_price) as sales,
        sum(cs_net_profit) as profit
 from catalog_sales,
      date_dim
 where cs_sold_date_sk = d_date_sk
       and d_date between cast('2001-08-15' as date)
                  and (cast('2001-08-15' as date) +  30 )
 group by cs_call_center_sk 
 ), 
 cr as
 (select cr_call_center_sk,
         sum(cr_return_amount) as returns,
         sum(cr_net_loss) as profit_loss
 from catalog_returns,
      date_dim
 where cr_returned_date_sk = d_date_sk
       and d_date between cast('2001-08-15' as date)
                  and (cast('2001-08-15' as date) +  30 )
 group by cr_call_center_sk
 ), 
 ws as
 ( select wp_web_page_sk,
        sum(ws_ext_sales_price) as sales,
        sum(ws_net_profit) as profit
 from web_sales,
      date_dim,
      web_page
 where ws_sold_date_sk = d_date_sk
       and d_date between cast('2001-08-15' as date)
                  and (cast('2001-08-15' as date) +  30 )
       and ws_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk), 
 wr as
 (select wp_web_page_sk,
        sum(wr_return_amt) as returns,
        sum(wr_net_loss) as profit_loss
 from web_returns,
      date_dim,
      web_page
 where wr_returned_date_sk = d_date_sk
       and d_date between cast('2001-08-15' as date)
                  and (cast('2001-08-15' as date) +  30 )
       and wr_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk)
  select  channel
        , id
        , sum(sales) as sales
        , sum(returns) as returns
        , sum(profit) as profit
 from 
 (select 'store channel' as channel
        , ss.s_store_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ss left join sr
        on  ss.s_store_sk = sr.s_store_sk
 union all
 select 'catalog channel' as channel
        , cs_call_center_sk as id
        , sales
        , returns
        , (profit - profit_loss) as profit
 from  cs
       , cr
 union all
 select 'web channel' as channel
        , ws.wp_web_page_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ws left join wr
        on  ws.wp_web_page_sk = wr.wp_web_page_sk
 ) x
 group by rollup (channel, id)
 order by channel
         ,id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ss as
 (select s_store_sk,
         sum(ss_ext_sales_price) as sales,
         sum(ss_net_profit) as profit
 from store_sales,
      date_dim,
      store
 where ss_sold_date_sk = d_date_sk
       and d_date between cast('1999-08-12' as date) 
                  and (cast('1999-08-12' as date) +  30 ) 
       and ss_store_sk = s_store_sk
 group by s_store_sk)
 ,
 sr as
 (select s_store_sk,
         sum(sr_return_amt) as returns,
         sum(sr_net_loss) as profit_loss
 from store_returns,
      date_dim,
      store
 where sr_returned_date_sk = d_date_sk
       and d_date between cast('1999-08-12' as date)
                  and (cast('1999-08-12' as date) +  30 )
       and sr_store_sk = s_store_sk
 group by s_store_sk), 
 cs as
 (select cs_call_center_sk,
        sum(cs_ext_sales_price) as sales,
        sum(cs_net_profit) as profit
 from catalog_sales,
      date_dim
 where cs_sold_date_sk = d_date_sk
       and d_date between cast('1999-08-12' as date)
                  and (cast('1999-08-12' as date) +  30 )
 group by cs_call_center_sk 
 ), 
 cr as
 (select cr_call_center_sk,
         sum(cr_return_amount) as returns,
         sum(cr_net_loss) as profit_loss
 from catalog_returns,
      date_dim
 where cr_returned_date_sk = d_date_sk
       and d_date between cast('1999-08-12' as date)
                  and (cast('1999-08-12' as date) +  30 )
 group by cr_call_center_sk
 ), 
 ws as
 ( select wp_web_page_sk,
        sum(ws_ext_sales_price) as sales,
        sum(ws_net_profit) as profit
 from web_sales,
      date_dim,
      web_page
 where ws_sold_date_sk = d_date_sk
       and d_date between cast('1999-08-12' as date)
                  and (cast('1999-08-12' as date) +  30 )
       and ws_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk), 
 wr as
 (select wp_web_page_sk,
        sum(wr_return_amt) as returns,
        sum(wr_net_loss) as profit_loss
 from web_returns,
      date_dim,
      web_page
 where wr_returned_date_sk = d_date_sk
       and d_date between cast('1999-08-12' as date)
                  and (cast('1999-08-12' as date) +  30 )
       and wr_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk)
  select  channel
        , id
        , sum(sales) as sales
        , sum(returns) as returns
        , sum(profit) as profit
 from 
 (select 'store channel' as channel
        , ss.s_store_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ss left join sr
        on  ss.s_store_sk = sr.s_store_sk
 union all
 select 'catalog channel' as channel
        , cs_call_center_sk as id
        , sales
        , returns
        , (profit - profit_loss) as profit
 from  cs
       , cr
 union all
 select 'web channel' as channel
        , ws.wp_web_page_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ws left join wr
        on  ws.wp_web_page_sk = wr.wp_web_page_sk
 ) x
 group by rollup (channel, id)
 order by channel
         ,id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ss as
 (select s_store_sk,
         sum(ss_ext_sales_price) as sales,
         sum(ss_net_profit) as profit
 from store_sales,
      date_dim,
      store
 where ss_sold_date_sk = d_date_sk
       and d_date between cast('2000-08-29' as date) 
                  and (cast('2000-08-29' as date) +  30 ) 
       and ss_store_sk = s_store_sk
 group by s_store_sk)
 ,
 sr as
 (select s_store_sk,
         sum(sr_return_amt) as returns,
         sum(sr_net_loss) as profit_loss
 from store_returns,
      date_dim,
      store
 where sr_returned_date_sk = d_date_sk
       and d_date between cast('2000-08-29' as date)
                  and (cast('2000-08-29' as date) +  30 )
       and sr_store_sk = s_store_sk
 group by s_store_sk), 
 cs as
 (select cs_call_center_sk,
        sum(cs_ext_sales_price) as sales,
        sum(cs_net_profit) as profit
 from catalog_sales,
      date_dim
 where cs_sold_date_sk = d_date_sk
       and d_date between cast('2000-08-29' as date)
                  and (cast('2000-08-29' as date) +  30 )
 group by cs_call_center_sk 
 ), 
 cr as
 (select cr_call_center_sk,
         sum(cr_return_amount) as returns,
         sum(cr_net_loss) as profit_loss
 from catalog_returns,
      date_dim
 where cr_returned_date_sk = d_date_sk
       and d_date between cast('2000-08-29' as date)
                  and (cast('2000-08-29' as date) +  30 )
 group by cr_call_center_sk
 ), 
 ws as
 ( select wp_web_page_sk,
        sum(ws_ext_sales_price) as sales,
        sum(ws_net_profit) as profit
 from web_sales,
      date_dim,
      web_page
 where ws_sold_date_sk = d_date_sk
       and d_date between cast('2000-08-29' as date)
                  and (cast('2000-08-29' as date) +  30 )
       and ws_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk), 
 wr as
 (select wp_web_page_sk,
        sum(wr_return_amt) as returns,
        sum(wr_net_loss) as profit_loss
 from web_returns,
      date_dim,
      web_page
 where wr_returned_date_sk = d_date_sk
       and d_date between cast('2000-08-29' as date)
                  and (cast('2000-08-29' as date) +  30 )
       and wr_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk)
  select  channel
        , id
        , sum(sales) as sales
        , sum(returns) as returns
        , sum(profit) as profit
 from 
 (select 'store channel' as channel
        , ss.s_store_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ss left join sr
        on  ss.s_store_sk = sr.s_store_sk
 union all
 select 'catalog channel' as channel
        , cs_call_center_sk as id
        , sales
        , returns
        , (profit - profit_loss) as profit
 from  cs
       , cr
 union all
 select 'web channel' as channel
        , ws.wp_web_page_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ws left join wr
        on  ws.wp_web_page_sk = wr.wp_web_page_sk
 ) x
 group by rollup (channel, id)
 order by channel
         ,id
 limit 100;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ss as
 (select s_store_sk,
         sum(ss_ext_sales_price) as sales,
         sum(ss_net_profit) as profit
 from store_sales,
      date_dim,
      store
 where ss_sold_date_sk = d_date_sk
       and d_date between cast('1998-08-15' as date) 
                  and (cast('1998-08-15' as date) +  30 ) 
       and ss_store_sk = s_store_sk
 group by s_store_sk)
 ,
 sr as
 (select s_store_sk,
         sum(sr_return_amt) as returns,
         sum(sr_net_loss) as profit_loss
 from store_returns,
      date_dim,
      store
 where sr_returned_date_sk = d_date_sk
       and d_date between cast('1998-08-15' as date)
                  and (cast('1998-08-15' as date) +  30 )
       and sr_store_sk = s_store_sk
 group by s_store_sk), 
 cs as
 (select cs_call_center_sk,
        sum(cs_ext_sales_price) as sales,
        sum(cs_net_profit) as profit
 from catalog_sales,
      date_dim
 where cs_sold_date_sk = d_date_sk
       and d_date between cast('1998-08-15' as date)
                  and (cast('1998-08-15' as date) +  30 )
 group by cs_call_center_sk 
 ), 
 cr as
 (select cr_call_center_sk,
         sum(cr_return_amount) as returns,
         sum(cr_net_loss) as profit_loss
 from catalog_returns,
      date_dim
 where cr_returned_date_sk = d_date_sk
       and d_date between cast('1998-08-15' as date)
                  and (cast('1998-08-15' as date) +  30 )
 group by cr_call_center_sk
 ), 
 ws as
 ( select wp_web_page_sk,
        sum(ws_ext_sales_price) as sales,
        sum(ws_net_profit) as profit
 from web_sales,
      date_dim,
      web_page
 where ws_sold_date_sk = d_date_sk
       and d_date between cast('1998-08-15' as date)
                  and (cast('1998-08-15' as date) +  30 )
       and ws_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk), 
 wr as
 (select wp_web_page_sk,
        sum(wr_return_amt) as returns,
        sum(wr_net_loss) as profit_loss
 from web_returns,
      date_dim,
      web_page
 where wr_returned_date_sk = d_date_sk
       and d_date between cast('1998-08-15' as date)
                  and (cast('1998-08-15' as date) +  30 )
       and wr_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk)
  select  channel
        , id
        , sum(sales) as sales
        , sum(returns) as returns
        , sum(profit) as profit
 from 
 (select 'store channel' as channel
        , ss.s_store_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ss left join sr
        on  ss.s_store_sk = sr.s_store_sk
 union all
 select 'catalog channel' as channel
        , cs_call_center_sk as id
        , sales
        , returns
        , (profit - profit_loss) as profit
 from  cs
       , cr
 union all
 select 'web channel' as channel
        , ws.wp_web_page_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ws left join wr
        on  ws.wp_web_page_sk = wr.wp_web_page_sk
 ) x
 group by rollup (channel, id)
 order by channel
         ,id
 limit 100;

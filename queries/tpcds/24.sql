EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_sales_price) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
and s_market_id=7
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'orchid'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                                 from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_sales_price) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
  and s_market_id = 7
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'chiffon'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                           from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_sales_price) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
and s_market_id=8
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'lace'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                                 from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_sales_price) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
  and s_market_id = 8
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'floral'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                           from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_net_paid_inc_tax) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
and s_market_id=5
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'yellow'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                                 from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_net_paid_inc_tax) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
  and s_market_id = 5
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'chocolate'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                           from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_net_paid_inc_tax) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
and s_market_id=10
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'purple'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                                 from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_net_paid_inc_tax) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
  and s_market_id = 10
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'dim'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                           from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_sales_price) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
and s_market_id=9
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'steel'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                                 from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_sales_price) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
  and s_market_id = 9
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'ivory'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                           from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_net_profit) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
and s_market_id=7
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'blush'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                                 from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_net_profit) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
  and s_market_id = 7
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'bisque'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                           from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_net_paid) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
and s_market_id=9
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'firebrick'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                                 from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_net_paid) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
  and s_market_id = 9
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'bisque'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                           from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_sales_price) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
and s_market_id=6
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'aquamarine'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                                 from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_sales_price) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
  and s_market_id = 6
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'chiffon'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                           from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_ext_sales_price) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
and s_market_id=9
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'dodger'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                                 from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_ext_sales_price) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
  and s_market_id = 9
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'plum'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                           from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_sales_price) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
and s_market_id=7
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'plum'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                                 from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_sales_price) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
  and s_market_id = 7
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'forest'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                           from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_net_profit) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
and s_market_id=5
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'red'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                                 from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_net_profit) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
  and s_market_id = 5
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'gainsboro'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                           from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_net_paid) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
and s_market_id=8
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'antique'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                                 from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_net_paid) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
  and s_market_id = 8
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'khaki'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                           from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_net_paid) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
and s_market_id=9
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'almond'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                                 from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_net_paid) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
  and s_market_id = 9
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'smoke'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                           from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_ext_sales_price) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
and s_market_id=10
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'smoke'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                                 from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_ext_sales_price) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
  and s_market_id = 10
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'white'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                           from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_net_paid) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
and s_market_id=9
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'cream'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                                 from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_net_paid) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
  and s_market_id = 9
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'grey'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                           from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_sales_price) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
and s_market_id=10
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'mint'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                                 from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_sales_price) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
  and s_market_id = 10
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'cornflower'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                           from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_net_profit) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
and s_market_id=5
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'cornsilk'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                                 from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_net_profit) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
  and s_market_id = 5
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'goldenrod'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                           from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_net_profit) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
and s_market_id=10
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'magenta'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                                 from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_net_profit) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
  and s_market_id = 10
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'green'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                           from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_net_paid_inc_tax) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
and s_market_id=6
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'cornflower'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                                 from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_net_paid_inc_tax) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
  and s_market_id = 6
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'aquamarine'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                           from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_net_paid_inc_tax) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
and s_market_id=6
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'floral'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                                 from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_net_paid_inc_tax) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
  and s_market_id = 6
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'white'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                           from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_net_profit) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
and s_market_id=6
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'honeydew'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                                 from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_net_profit) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
  and s_market_id = 6
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'grey'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                           from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_net_paid_inc_tax) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
and s_market_id=7
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'blush'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                                 from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_net_paid_inc_tax) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
  and s_market_id = 7
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'peach'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                           from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_net_paid_inc_tax) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
and s_market_id=9
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'cornflower'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                                 from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_net_paid_inc_tax) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
  and s_market_id = 9
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'plum'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                           from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_net_paid) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
and s_market_id=6
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'dodger'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                                 from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_net_paid) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
  and s_market_id = 6
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'cyan'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                           from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_net_profit) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
and s_market_id=10
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'royal'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                                 from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_net_profit) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
  and s_market_id = 10
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'honeydew'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                           from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_ext_sales_price) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
and s_market_id=5
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'hot'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                                 from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_ext_sales_price) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
  and s_market_id = 5
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'blue'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                           from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_net_paid_inc_tax) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
and s_market_id=9
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'chocolate'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                                 from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_net_paid_inc_tax) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
  and s_market_id = 9
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'ghost'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                           from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_net_paid) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
and s_market_id=7
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'lawn'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                                 from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_net_paid) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
  and s_market_id = 7
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'cornflower'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                           from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_ext_sales_price) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
and s_market_id=5
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'ivory'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                                 from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_ext_sales_price) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
  and s_market_id = 5
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'forest'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                           from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_ext_sales_price) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
and s_market_id=10
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'olive'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                                 from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_ext_sales_price) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
  and s_market_id = 10
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'moccasin'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                           from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_ext_sales_price) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
and s_market_id=7
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'chiffon'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                                 from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_ext_sales_price) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
  and s_market_id = 7
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'goldenrod'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                           from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_net_paid_inc_tax) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
and s_market_id=5
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'olive'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                                 from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_net_paid_inc_tax) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
  and s_market_id = 5
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'honeydew'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                           from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_net_profit) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
and s_market_id=5
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'saddle'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                                 from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_net_profit) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
  and s_market_id = 5
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'burlywood'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                           from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_net_profit) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
and s_market_id=8
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'floral'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                                 from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_net_profit) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
  and s_market_id = 8
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'frosted'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                           from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_net_paid) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
and s_market_id=9
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'bisque'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                                 from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_net_paid) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
  and s_market_id = 9
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'blush'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                           from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_ext_sales_price) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
and s_market_id=9
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'dodger'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                                 from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_ext_sales_price) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
  and s_market_id = 9
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'snow'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                           from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_net_profit) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
and s_market_id=7
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'ghost'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                                 from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_net_profit) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
  and s_market_id = 7
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'spring'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                           from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_sales_price) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
and s_market_id=9
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'magenta'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                                 from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_sales_price) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
  and s_market_id = 9
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'cyan'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                           from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_net_paid_inc_tax) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
and s_market_id=8
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'deep'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                                 from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_net_paid_inc_tax) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
  and s_market_id = 8
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'blanched'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                           from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_ext_sales_price) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
and s_market_id=9
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'grey'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                                 from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_ext_sales_price) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
  and s_market_id = 9
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'moccasin'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                           from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_ext_sales_price) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
and s_market_id=10
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'papaya'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                                 from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_ext_sales_price) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
  and s_market_id = 10
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'magenta'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                           from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_net_paid_inc_tax) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
and s_market_id=6
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'thistle'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                                 from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_net_paid_inc_tax) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
  and s_market_id = 6
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'saddle'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                           from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_sales_price) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
and s_market_id=10
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'puff'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                                 from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_sales_price) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
  and s_market_id = 10
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'chartreuse'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                           from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_sales_price) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
and s_market_id=7
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'navy'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                                 from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_sales_price) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
  and s_market_id = 7
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'smoke'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                           from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_ext_sales_price) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
and s_market_id=6
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'mint'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                                 from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_ext_sales_price) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
  and s_market_id = 6
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'black'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                           from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_net_paid) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
and s_market_id=6
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'violet'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                                 from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_net_paid) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
  and s_market_id = 6
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'metallic'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                           from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_sales_price) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
and s_market_id=7
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'drab'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                                 from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_sales_price) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
  and s_market_id = 7
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'white'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                           from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_net_profit) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
and s_market_id=5
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'misty'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                                 from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_net_profit) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
  and s_market_id = 5
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'beige'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                           from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_ext_sales_price) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
and s_market_id=7
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'dodger'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                                 from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_ext_sales_price) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
  and s_market_id = 7
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'mint'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                           from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_net_profit) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
and s_market_id=9
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'powder'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                                 from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_net_profit) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
  and s_market_id = 9
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'steel'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                           from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_net_paid_inc_tax) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
and s_market_id=6
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'light'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                                 from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_net_paid_inc_tax) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
  and s_market_id = 6
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'navajo'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                           from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_sales_price) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
and s_market_id=10
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'ivory'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                                 from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_sales_price) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
  and s_market_id = 10
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'blue'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                           from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_sales_price) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
and s_market_id=5
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'cream'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                                 from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_sales_price) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
  and s_market_id = 5
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'smoke'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                           from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_sales_price) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
and s_market_id=6
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'spring'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                                 from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_sales_price) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
  and s_market_id = 6
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'hot'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                           from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_ext_sales_price) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
and s_market_id=5
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'forest'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                                 from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_ext_sales_price) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
  and s_market_id = 5
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'chartreuse'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                           from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_sales_price) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
and s_market_id=6
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'bisque'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                                 from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_sales_price) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
  and s_market_id = 6
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'smoke'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                           from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_net_profit) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
and s_market_id=10
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'navy'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                                 from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_net_profit) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
  and s_market_id = 10
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'peru'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                           from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_net_profit) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
and s_market_id=10
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'floral'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                                 from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_net_profit) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
  and s_market_id = 10
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'ivory'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                           from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_sales_price) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
and s_market_id=8
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'beige'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                                 from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_sales_price) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
  and s_market_id = 8
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'sandy'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                           from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_net_profit) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
and s_market_id=5
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'lime'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                                 from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_net_profit) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
  and s_market_id = 5
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'tomato'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                           from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_net_paid) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
and s_market_id=6
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'black'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                                 from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_net_paid) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
  and s_market_id = 6
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'medium'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                           from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_net_paid) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
and s_market_id=10
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'chocolate'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                                 from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_net_paid) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
  and s_market_id = 10
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'dim'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                           from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_net_profit) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
and s_market_id=7
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'snow'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                                 from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_net_profit) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
  and s_market_id = 7
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'hot'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                           from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_sales_price) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
and s_market_id=7
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'magenta'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                                 from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_sales_price) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
  and s_market_id = 7
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'sky'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                           from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_sales_price) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
and s_market_id=5
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'forest'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                                 from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_sales_price) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
  and s_market_id = 5
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'chartreuse'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                           from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_net_paid) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
and s_market_id=7
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'magenta'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                                 from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_net_paid) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
  and s_market_id = 7
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'drab'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                           from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_net_paid) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
and s_market_id=7
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'metallic'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                                 from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_net_paid) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
  and s_market_id = 7
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'burlywood'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                           from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_sales_price) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
and s_market_id=10
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'cyan'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                                 from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_sales_price) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
  and s_market_id = 10
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'dark'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                           from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_net_paid) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
and s_market_id=7
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'snow'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                                 from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_net_paid) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
  and s_market_id = 7
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'mint'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                           from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_sales_price) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
and s_market_id=7
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'cornsilk'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                                 from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_sales_price) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
  and s_market_id = 7
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'cornflower'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                           from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_ext_sales_price) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
and s_market_id=9
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'lemon'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                                 from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_ext_sales_price) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
  and s_market_id = 9
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'dark'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                           from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_ext_sales_price) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
and s_market_id=7
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'thistle'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                                 from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_ext_sales_price) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
  and s_market_id = 7
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'black'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                           from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_net_paid) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
and s_market_id=8
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'cornflower'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                                 from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_net_paid) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
  and s_market_id = 8
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'peach'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                           from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_net_profit) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
and s_market_id=10
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'green'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                                 from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_net_profit) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
  and s_market_id = 10
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'lemon'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                           from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_net_paid_inc_tax) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
and s_market_id=6
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'sky'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                                 from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_net_paid_inc_tax) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
  and s_market_id = 6
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'cornflower'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                           from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_sales_price) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
and s_market_id=9
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'medium'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                                 from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_sales_price) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
  and s_market_id = 9
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'indian'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                           from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_ext_sales_price) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
and s_market_id=5
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'maroon'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                                 from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_ext_sales_price) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
  and s_market_id = 5
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'light'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                           from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_ext_sales_price) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
and s_market_id=6
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'thistle'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                                 from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_ext_sales_price) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
  and s_market_id = 6
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'brown'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                           from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_net_paid_inc_tax) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
and s_market_id=5
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'khaki'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                                 from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_net_paid_inc_tax) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
  and s_market_id = 5
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'chocolate'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                           from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_net_paid_inc_tax) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
and s_market_id=10
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'blanched'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                                 from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_net_paid_inc_tax) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
  and s_market_id = 10
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'white'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                           from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_sales_price) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
and s_market_id=8
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'tan'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                                 from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_sales_price) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
  and s_market_id = 8
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'midnight'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                           from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_ext_sales_price) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
and s_market_id=10
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'thistle'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                                 from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_ext_sales_price) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
  and s_market_id = 10
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'ghost'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                           from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_sales_price) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
and s_market_id=8
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'navy'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                                 from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_sales_price) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
  and s_market_id = 8
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'beige'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                           from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_ext_sales_price) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
and s_market_id=10
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'purple'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                                 from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_ext_sales_price) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
  and s_market_id = 10
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'dodger'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                           from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_ext_sales_price) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
and s_market_id=7
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'red'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                                 from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_ext_sales_price) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
  and s_market_id = 7
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'burnished'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                           from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_sales_price) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
and s_market_id=10
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'frosted'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                                 from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_sales_price) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
  and s_market_id = 10
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'burlywood'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                           from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_ext_sales_price) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
and s_market_id=5
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'rose'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                                 from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_ext_sales_price) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
  and s_market_id = 5
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'goldenrod'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                           from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_net_profit) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
and s_market_id=10
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'khaki'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                                 from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_net_profit) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
  and s_market_id = 10
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'metallic'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                           from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_net_paid_inc_tax) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
and s_market_id=10
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'chartreuse'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                                 from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_net_paid_inc_tax) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
  and s_market_id = 10
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'blush'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                           from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_net_paid) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
and s_market_id=5
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'red'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                                 from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_net_paid) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
  and s_market_id = 5
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'floral'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                           from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_ext_sales_price) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
and s_market_id=6
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'slate'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                                 from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_ext_sales_price) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
  and s_market_id = 6
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'peru'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                           from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_net_profit) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
and s_market_id=8
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'powder'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                                 from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_net_profit) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
  and s_market_id = 8
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'drab'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                           from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_net_profit) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
and s_market_id=6
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'chartreuse'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                                 from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_net_profit) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
  and s_market_id = 6
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'blue'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                           from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_net_profit) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
and s_market_id=7
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'sandy'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                                 from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_net_profit) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
  and s_market_id = 7
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'almond'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                           from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_net_paid) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
and s_market_id=7
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'lime'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                                 from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_net_paid) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
  and s_market_id = 7
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'rose'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                           from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_net_paid) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
and s_market_id=6
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'hot'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                                 from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_net_paid) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
  and s_market_id = 6
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'antique'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                           from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_ext_sales_price) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
and s_market_id=10
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'orchid'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                                 from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_ext_sales_price) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
  and s_market_id = 10
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'forest'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                           from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_sales_price) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
and s_market_id=6
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'cream'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                                 from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_sales_price) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
  and s_market_id = 6
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'mint'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                           from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_net_paid_inc_tax) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
and s_market_id=10
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'dim'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                                 from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_net_paid_inc_tax) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
  and s_market_id = 10
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'drab'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                           from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;


EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_sales_price) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
and s_market_id=5
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'drab'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                                 from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_sales_price) netpaid
from store_sales
    ,store_returns
    ,store
    ,item
    ,customer
    ,customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
  and s_market_id = 5
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'snow'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                           from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;

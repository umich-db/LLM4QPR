EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_companies mc WHERE t.id=mc.movie_id AND mc.company_type_id=2;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_info_idx mi_idx,movie_companies mc WHERE t.id=mi_idx.movie_id AND t.id=mc.movie_id AND mi_idx.info_type_id=112 AND mc.company_type_id=2;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_info_idx mi_idx,title t WHERE t.id=mi_idx.movie_id AND mi_idx.info_type_id=112;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_info_idx mi_idx,movie_companies mc,title t WHERE t.id=mi_idx.movie_id AND t.id=mc.movie_id AND mi_idx.info_type_id=112 AND mc.company_type_id=2;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_companies mc WHERE t.id=mc.movie_id AND t.production_year>2005 AND t.production_year<2010 AND mc.company_type_id=2;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_info_idx mi_idx,movie_companies mc WHERE t.id=mi_idx.movie_id AND t.id=mc.movie_id AND mi_idx.info_type_id=113 AND mc.company_type_id=2;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_info_idx mi_idx,title t WHERE t.id=mi_idx.movie_id AND mi_idx.info_type_id=113 AND t.production_year>2005 AND t.production_year<2010;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_info_idx mi_idx,movie_companies mc,title t WHERE t.id=mi_idx.movie_id AND t.id=mc.movie_id AND mi_idx.info_type_id=113 AND mc.company_type_id=2 AND t.production_year>2005 AND t.production_year<2010;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_companies mc WHERE t.id=mc.movie_id AND t.production_year>2010 AND mc.company_type_id=2;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_info_idx mi_idx,movie_companies mc WHERE t.id=mi_idx.movie_id AND t.id=mc.movie_id AND mi_idx.info_type_id=112 AND mc.company_type_id=2;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_info_idx mi_idx,title t WHERE t.id=mi_idx.movie_id AND mi_idx.info_type_id=112 AND t.production_year>2010;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_info_idx mi_idx,movie_companies mc,title t WHERE t.id=mi_idx.movie_id AND t.id=mc.movie_id AND mi_idx.info_type_id=112 AND mc.company_type_id=2 AND t.production_year>2010;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_companies mc WHERE t.id=mc.movie_id AND t.production_year>2000 AND mc.company_type_id=2;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_info_idx mi_idx,movie_companies mc WHERE t.id=mi_idx.movie_id AND t.id=mc.movie_id AND mi_idx.info_type_id=113 AND mc.company_type_id=2;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_info_idx mi_idx,title t WHERE t.id=mi_idx.movie_id AND mi_idx.info_type_id=113 AND t.production_year>2000;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_info_idx mi_idx,movie_companies mc,title t WHERE t.id=mi_idx.movie_id AND t.id=mc.movie_id AND mi_idx.info_type_id=113 AND mc.company_type_id=2 AND t.production_year>2000;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_companies mc WHERE t.id=mc.movie_id;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_keyword mk,movie_companies mc WHERE t.id=mk.movie_id AND t.id=mc.movie_id AND mk.keyword_id=117;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t WHERE t.id=mk.movie_id AND mk.keyword_id=117;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,movie_companies mc,title t WHERE t.id=mk.movie_id AND t.id=mc.movie_id AND mk.keyword_id=117;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_info mi,title t WHERE t.id=mi.movie_id AND t.production_year>2005;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t WHERE t.id=mk.movie_id AND t.production_year>2005;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_keyword mk,movie_info mi WHERE t.id=mk.movie_id AND t.id=mi.movie_id;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t,movie_info mi WHERE t.id=mk.movie_id AND t.id=mi.movie_id AND t.production_year>2005;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_info mi,title t WHERE t.id=mi.movie_id AND t.production_year>2010;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t WHERE t.id=mk.movie_id AND t.production_year>2010;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_keyword mk,movie_info mi WHERE t.id=mk.movie_id AND t.id=mi.movie_id;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t,movie_info mi WHERE t.id=mk.movie_id AND t.id=mi.movie_id AND t.production_year>2010;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_info mi,title t WHERE t.id=mi.movie_id AND t.production_year>1990;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t WHERE t.id=mk.movie_id AND t.production_year>1990;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_keyword mk,movie_info mi WHERE t.id=mk.movie_id AND t.id=mi.movie_id;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t,movie_info mi WHERE t.id=mk.movie_id AND t.id=mi.movie_id AND t.production_year>1990;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_info_idx mi_idx,title t WHERE t.id=mi_idx.movie_id AND mi_idx.info_type_id=101 AND t.production_year>2005;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t WHERE t.id=mk.movie_id AND t.production_year>2005;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_keyword mk,movie_info_idx mi_idx WHERE t.id=mk.movie_id AND t.id=mi_idx.movie_id AND mi_idx.info_type_id=101;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t,movie_info_idx mi_idx WHERE t.id=mk.movie_id AND t.id=mi_idx.movie_id AND t.production_year>2005 AND mi_idx.info_type_id=101;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_info_idx mi_idx,title t WHERE t.id=mi_idx.movie_id AND mi_idx.info_type_id=101 AND t.production_year>2010;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t WHERE t.id=mk.movie_id AND t.production_year>2010;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_keyword mk,movie_info_idx mi_idx WHERE t.id=mk.movie_id AND t.id=mi_idx.movie_id AND mi_idx.info_type_id=101;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t,movie_info_idx mi_idx WHERE t.id=mk.movie_id AND t.id=mi_idx.movie_id AND t.production_year>2010 AND mi_idx.info_type_id=101;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_info_idx mi_idx,title t WHERE t.id=mi_idx.movie_id AND mi_idx.info_type_id=101 AND t.production_year>1990;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t WHERE t.id=mk.movie_id AND t.production_year>1990;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_keyword mk,movie_info_idx mi_idx WHERE t.id=mk.movie_id AND t.id=mi_idx.movie_id AND mi_idx.info_type_id=101;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t,movie_info_idx mi_idx WHERE t.id=mk.movie_id AND t.id=mi_idx.movie_id AND t.production_year>1990 AND mi_idx.info_type_id=101;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_info mi,title t WHERE t.id=mi.movie_id AND t.production_year>2005;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_companies mc,title t WHERE t.id=mc.movie_id AND mc.company_type_id=2 AND t.production_year>2005;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_companies mc,movie_info mi WHERE t.id=mc.movie_id AND t.id=mi.movie_id AND mc.company_type_id=2;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_companies mc,title t,movie_info mi WHERE t.id=mc.movie_id AND t.id=mi.movie_id AND mc.company_type_id=2 AND t.production_year>2005;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_info mi,title t WHERE t.id=mi.movie_id AND t.production_year>2010;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_companies mc,title t WHERE t.id=mc.movie_id AND mc.company_type_id=2 AND t.production_year>2010;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_companies mc,movie_info mi WHERE t.id=mc.movie_id AND t.id=mi.movie_id AND mc.company_type_id=2;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_companies mc,title t,movie_info mi WHERE t.id=mc.movie_id AND t.id=mi.movie_id AND mc.company_type_id=2 AND t.production_year>2010;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_info mi,title t WHERE t.id=mi.movie_id AND t.production_year>1990;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_companies mc,title t WHERE t.id=mc.movie_id AND mc.company_type_id=2 AND t.production_year>1990;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_companies mc,movie_info mi WHERE t.id=mc.movie_id AND t.id=mi.movie_id AND mc.company_type_id=2;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_companies mc,title t,movie_info mi WHERE t.id=mc.movie_id AND t.id=mi.movie_id AND mc.company_type_id=2 AND t.production_year>1990;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_keyword mk WHERE t.id=mk.movie_id AND t.production_year>2010 AND mk.keyword_id=8200;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,cast_info ci,movie_keyword mk WHERE t.id=ci.movie_id AND t.id=mk.movie_id AND mk.keyword_id=8200;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM cast_info ci,title t WHERE t.id=ci.movie_id AND t.production_year>2010;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM cast_info ci,movie_keyword mk,title t WHERE t.id=ci.movie_id AND t.id=mk.movie_id AND mk.keyword_id=8200 AND t.production_year>2010;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_keyword mk WHERE t.id=mk.movie_id AND t.production_year>2014;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,cast_info ci,movie_keyword mk WHERE t.id=ci.movie_id AND t.id=mk.movie_id;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM cast_info ci,title t WHERE t.id=ci.movie_id AND t.production_year>2014;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM cast_info ci,movie_keyword mk,title t WHERE t.id=ci.movie_id AND t.id=mk.movie_id AND t.production_year>2014;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_keyword mk WHERE t.id=mk.movie_id AND t.production_year>2014 AND mk.keyword_id=8200;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,cast_info ci,movie_keyword mk WHERE t.id=ci.movie_id AND t.id=mk.movie_id AND mk.keyword_id=8200;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM cast_info ci,title t WHERE t.id=ci.movie_id AND t.production_year>2014;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM cast_info ci,movie_keyword mk,title t WHERE t.id=ci.movie_id AND t.id=mk.movie_id AND mk.keyword_id=8200 AND t.production_year>2014;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_keyword mk WHERE t.id=mk.movie_id AND t.production_year>2000 AND mk.keyword_id=8200;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,cast_info ci,movie_keyword mk WHERE t.id=ci.movie_id AND t.id=mk.movie_id AND mk.keyword_id=8200;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM cast_info ci,title t WHERE t.id=ci.movie_id AND t.production_year>2000;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM cast_info ci,movie_keyword mk,title t WHERE t.id=ci.movie_id AND t.id=mk.movie_id AND mk.keyword_id=8200 AND t.production_year>2000;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_keyword mk WHERE t.id=mk.movie_id AND t.production_year>2000;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,cast_info ci,movie_keyword mk WHERE t.id=ci.movie_id AND t.id=mk.movie_id;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM cast_info ci,title t WHERE t.id=ci.movie_id AND t.production_year>2000;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM cast_info ci,movie_keyword mk,title t WHERE t.id=ci.movie_id AND t.id=mk.movie_id AND t.production_year>2000;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,cast_info ci WHERE t.id=ci.movie_id AND t.production_year>1980 AND t.production_year<1995;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,cast_info ci WHERE t.id=ci.movie_id AND t.production_year>1980 AND t.production_year<1984;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,cast_info ci WHERE t.id=ci.movie_id AND t.production_year>1980 AND t.production_year<2010;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,cast_info ci WHERE t.id=ci.movie_id AND ci.role_id=2;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_companies mc,cast_info ci WHERE t.id=mc.movie_id AND t.id=ci.movie_id AND ci.role_id=2;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_companies mc,title t WHERE t.id=mc.movie_id;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_companies mc,cast_info ci,title t WHERE t.id=mc.movie_id AND t.id=ci.movie_id AND ci.role_id=2;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,cast_info ci WHERE t.id=ci.movie_id AND ci.role_id=4;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_companies mc,cast_info ci WHERE t.id=mc.movie_id AND t.id=ci.movie_id AND ci.role_id=4;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_companies mc,title t WHERE t.id=mc.movie_id;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_companies mc,cast_info ci,title t WHERE t.id=mc.movie_id AND t.id=ci.movie_id AND ci.role_id=4;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,cast_info ci WHERE t.id=ci.movie_id AND ci.role_id=7;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_companies mc,cast_info ci WHERE t.id=mc.movie_id AND t.id=ci.movie_id AND ci.role_id=7;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_companies mc,title t WHERE t.id=mc.movie_id;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_companies mc,cast_info ci,title t WHERE t.id=mc.movie_id AND t.id=ci.movie_id AND ci.role_id=7;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,cast_info ci WHERE t.id=ci.movie_id AND t.production_year>2005 AND t.production_year<2015 AND ci.role_id=2;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_companies mc,cast_info ci WHERE t.id=mc.movie_id AND t.id=ci.movie_id AND ci.role_id=2;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_companies mc,title t WHERE t.id=mc.movie_id AND t.production_year>2005 AND t.production_year<2015;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_companies mc,cast_info ci,title t WHERE t.id=mc.movie_id AND t.id=ci.movie_id AND ci.role_id=2 AND t.production_year>2005 AND t.production_year<2015;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,cast_info ci WHERE t.id=ci.movie_id AND t.production_year>2007 AND t.production_year<2010 AND ci.role_id=2;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_companies mc,cast_info ci WHERE t.id=mc.movie_id AND t.id=ci.movie_id AND ci.role_id=2;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_companies mc,title t WHERE t.id=mc.movie_id AND t.production_year>2007 AND t.production_year<2010;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_companies mc,cast_info ci,title t WHERE t.id=mc.movie_id AND t.id=ci.movie_id AND ci.role_id=2 AND t.production_year>2007 AND t.production_year<2010;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM cast_info ci,title t WHERE t.id=ci.movie_id AND ci.role_id=1 AND t.production_year>2005;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_companies mc,title t WHERE t.id=mc.movie_id AND t.production_year>2005;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_companies mc,cast_info ci WHERE t.id=mc.movie_id AND t.id=ci.movie_id AND ci.role_id=1;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_companies mc,title t,cast_info ci WHERE t.id=mc.movie_id AND t.id=ci.movie_id AND t.production_year>2005 AND ci.role_id=1;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM cast_info ci,title t WHERE t.id=ci.movie_id AND ci.role_id=1 AND t.production_year>2010;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_companies mc,title t WHERE t.id=mc.movie_id AND t.production_year>2010;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_companies mc,cast_info ci WHERE t.id=mc.movie_id AND t.id=ci.movie_id AND ci.role_id=1;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_companies mc,title t,cast_info ci WHERE t.id=mc.movie_id AND t.id=ci.movie_id AND t.production_year>2010 AND ci.role_id=1;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM cast_info ci,title t WHERE t.id=ci.movie_id AND t.production_year>1990;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_companies mc,title t WHERE t.id=mc.movie_id AND t.production_year>1990;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_companies mc,cast_info ci WHERE t.id=mc.movie_id AND t.id=ci.movie_id;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_companies mc,title t,cast_info ci WHERE t.id=mc.movie_id AND t.id=ci.movie_id AND t.production_year>1990;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t WHERE t.id=mk.movie_id AND mk.keyword_id=398 AND t.production_year>1950 AND t.production_year<2000;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_companies mc,title t WHERE t.id=mc.movie_id AND mc.company_type_id=2 AND t.production_year>1950 AND t.production_year<2000;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_companies mc,movie_keyword mk WHERE t.id=mc.movie_id AND t.id=mk.movie_id AND mc.company_type_id=2 AND mk.keyword_id=398;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_companies mc,title t,movie_keyword mk WHERE t.id=mc.movie_id AND t.id=mk.movie_id AND mc.company_type_id=2 AND t.production_year>1950 AND t.production_year<2000 AND mk.keyword_id=398;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t WHERE t.id=mk.movie_id AND mk.keyword_id=398;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_companies mc,title t WHERE t.id=mc.movie_id AND mc.company_type_id=2;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_companies mc,movie_keyword mk WHERE t.id=mc.movie_id AND t.id=mk.movie_id AND mc.company_type_id=2 AND mk.keyword_id=398;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_companies mc,title t,movie_keyword mk WHERE t.id=mc.movie_id AND t.id=mk.movie_id AND mc.company_type_id=2 AND mk.keyword_id=398;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t WHERE t.id=mk.movie_id AND t.production_year>1950;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_companies mc,title t WHERE t.id=mc.movie_id AND t.production_year>1950;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_companies mc,movie_keyword mk WHERE t.id=mc.movie_id AND t.id=mk.movie_id;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_companies mc,title t,movie_keyword mk WHERE t.id=mc.movie_id AND t.id=mk.movie_id AND t.production_year>1950;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_info mi,title t WHERE t.id=mi.movie_id AND mi.info_type_id=3 AND t.production_year>2005 AND t.production_year<2008;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_info_idx mi_idx,title t WHERE t.id=mi_idx.movie_id AND mi_idx.info_type_id=101 AND t.production_year>2005 AND t.production_year<2008;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_companies mc,title t WHERE t.id=mc.movie_id AND mc.company_type_id=2 AND t.production_year>2005 AND t.production_year<2008;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_info_idx mi_idx,movie_info mi WHERE t.id=mi_idx.movie_id AND t.id=mi.movie_id AND mi_idx.info_type_id=101 AND mi.info_type_id=3;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_companies mc,movie_info mi WHERE t.id=mc.movie_id AND t.id=mi.movie_id AND mc.company_type_id=2 AND mi.info_type_id=3;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_companies mc,movie_info_idx mi_idx WHERE t.id=mc.movie_id AND t.id=mi_idx.movie_id AND mc.company_type_id=2 AND mi_idx.info_type_id=101;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_info_idx mi_idx,title t,movie_info mi WHERE t.id=mi_idx.movie_id AND t.id=mi.movie_id AND mi_idx.info_type_id=101 AND t.production_year>2005 AND t.production_year<2008 AND mi.info_type_id=3;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_companies mc,title t,movie_info mi WHERE t.id=mc.movie_id AND t.id=mi.movie_id AND mc.company_type_id=2 AND t.production_year>2005 AND t.production_year<2008 AND mi.info_type_id=3;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_companies mc,title t,movie_info_idx mi_idx WHERE t.id=mc.movie_id AND t.id=mi_idx.movie_id AND mc.company_type_id=2 AND t.production_year>2005 AND t.production_year<2008 AND mi_idx.info_type_id=101;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_companies mc,movie_info mi,movie_info_idx mi_idx WHERE t.id=mc.movie_id AND t.id=mi.movie_id AND t.id=mi_idx.movie_id AND mc.company_type_id=2 AND mi.info_type_id=3 AND mi_idx.info_type_id=101;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_companies mc,title t,movie_info mi,movie_info_idx mi_idx WHERE t.id=mc.movie_id AND t.id=mi.movie_id AND t.id=mi_idx.movie_id AND mc.company_type_id=2 AND t.production_year>2005 AND t.production_year<2008 AND mi.info_type_id=3 AND mi_idx.info_type_id=101;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_info mi,title t WHERE t.id=mi.movie_id AND mi.info_type_id=105;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_info_idx mi_idx,title t WHERE t.id=mi_idx.movie_id AND mi_idx.info_type_id=113;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_companies mc,title t WHERE t.id=mc.movie_id;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_info_idx mi_idx,movie_info mi WHERE t.id=mi_idx.movie_id AND t.id=mi.movie_id AND mi_idx.info_type_id=113 AND mi.info_type_id=105;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_companies mc,movie_info mi WHERE t.id=mc.movie_id AND t.id=mi.movie_id AND mi.info_type_id=105;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_companies mc,movie_info_idx mi_idx WHERE t.id=mc.movie_id AND t.id=mi_idx.movie_id AND mi_idx.info_type_id=113;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_info_idx mi_idx,title t,movie_info mi WHERE t.id=mi_idx.movie_id AND t.id=mi.movie_id AND mi_idx.info_type_id=113 AND mi.info_type_id=105;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_companies mc,title t,movie_info mi WHERE t.id=mc.movie_id AND t.id=mi.movie_id AND mi.info_type_id=105;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_companies mc,title t,movie_info_idx mi_idx WHERE t.id=mc.movie_id AND t.id=mi_idx.movie_id AND mi_idx.info_type_id=113;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_companies mc,movie_info mi,movie_info_idx mi_idx WHERE t.id=mc.movie_id AND t.id=mi.movie_id AND t.id=mi_idx.movie_id AND mi.info_type_id=105 AND mi_idx.info_type_id=113;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_companies mc,title t,movie_info mi,movie_info_idx mi_idx WHERE t.id=mc.movie_id AND t.id=mi.movie_id AND t.id=mi_idx.movie_id AND mi.info_type_id=105 AND mi_idx.info_type_id=113;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_info mi,title t WHERE t.id=mi.movie_id AND mi.info_type_id=3 AND t.production_year>2000 AND t.production_year<2010;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_info_idx mi_idx,title t WHERE t.id=mi_idx.movie_id AND mi_idx.info_type_id=101 AND t.production_year>2000 AND t.production_year<2010;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_companies mc,title t WHERE t.id=mc.movie_id AND mc.company_type_id=2 AND t.production_year>2000 AND t.production_year<2010;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_info_idx mi_idx,movie_info mi WHERE t.id=mi_idx.movie_id AND t.id=mi.movie_id AND mi_idx.info_type_id=101 AND mi.info_type_id=3;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_companies mc,movie_info mi WHERE t.id=mc.movie_id AND t.id=mi.movie_id AND mc.company_type_id=2 AND mi.info_type_id=3;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_companies mc,movie_info_idx mi_idx WHERE t.id=mc.movie_id AND t.id=mi_idx.movie_id AND mc.company_type_id=2 AND mi_idx.info_type_id=101;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_info_idx mi_idx,title t,movie_info mi WHERE t.id=mi_idx.movie_id AND t.id=mi.movie_id AND mi_idx.info_type_id=101 AND t.production_year>2000 AND t.production_year<2010 AND mi.info_type_id=3;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_companies mc,title t,movie_info mi WHERE t.id=mc.movie_id AND t.id=mi.movie_id AND mc.company_type_id=2 AND t.production_year>2000 AND t.production_year<2010 AND mi.info_type_id=3;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_companies mc,title t,movie_info_idx mi_idx WHERE t.id=mc.movie_id AND t.id=mi_idx.movie_id AND mc.company_type_id=2 AND t.production_year>2000 AND t.production_year<2010 AND mi_idx.info_type_id=101;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_companies mc,movie_info mi,movie_info_idx mi_idx WHERE t.id=mc.movie_id AND t.id=mi.movie_id AND t.id=mi_idx.movie_id AND mc.company_type_id=2 AND mi.info_type_id=3 AND mi_idx.info_type_id=101;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_companies mc,title t,movie_info mi,movie_info_idx mi_idx WHERE t.id=mc.movie_id AND t.id=mi.movie_id AND t.id=mi_idx.movie_id AND mc.company_type_id=2 AND t.production_year>2000 AND t.production_year<2010 AND mi.info_type_id=3 AND mi_idx.info_type_id=101;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_info mi,title t WHERE t.id=mi.movie_id AND mi.info_type_id=16 AND t.kind_id=1;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_companies mc,title t WHERE t.id=mc.movie_id AND mc.company_type_id=2 AND t.kind_id=1;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_info_idx mi_idx,title t WHERE t.id=mi_idx.movie_id AND mi_idx.info_type_id=101 AND t.kind_id=1;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_companies mc,movie_info mi WHERE t.id=mc.movie_id AND t.id=mi.movie_id AND mc.company_type_id=2 AND mi.info_type_id=16;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_info_idx mi_idx,movie_info mi WHERE t.id=mi_idx.movie_id AND t.id=mi.movie_id AND mi_idx.info_type_id=101 AND mi.info_type_id=16;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_info_idx mi_idx,movie_companies mc WHERE t.id=mi_idx.movie_id AND t.id=mc.movie_id AND mi_idx.info_type_id=101 AND mc.company_type_id=2;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_companies mc,title t,movie_info mi WHERE t.id=mc.movie_id AND t.id=mi.movie_id AND mc.company_type_id=2 AND t.kind_id=1 AND mi.info_type_id=16;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_info_idx mi_idx,title t,movie_info mi WHERE t.id=mi_idx.movie_id AND t.id=mi.movie_id AND mi_idx.info_type_id=101 AND t.kind_id=1 AND mi.info_type_id=16;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_info_idx mi_idx,title t,movie_companies mc WHERE t.id=mi_idx.movie_id AND t.id=mc.movie_id AND mi_idx.info_type_id=101 AND t.kind_id=1 AND mc.company_type_id=2;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_info_idx mi_idx,movie_info mi,movie_companies mc WHERE t.id=mi_idx.movie_id AND t.id=mi.movie_id AND t.id=mc.movie_id AND mi_idx.info_type_id=101 AND mi.info_type_id=16 AND mc.company_type_id=2;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_info_idx mi_idx,title t,movie_info mi,movie_companies mc WHERE t.id=mi_idx.movie_id AND t.id=mi.movie_id AND t.id=mc.movie_id AND mi_idx.info_type_id=101 AND t.kind_id=1 AND mi.info_type_id=16 AND mc.company_type_id=2;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_info mi,title t WHERE t.id=mi.movie_id AND mi.info_type_id=8 AND t.production_year>2010 AND t.kind_id=1;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_info_idx mi_idx,title t WHERE t.id=mi_idx.movie_id AND mi_idx.info_type_id=101 AND t.production_year>2010 AND t.kind_id=1;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t WHERE t.id=mk.movie_id AND t.production_year>2010 AND t.kind_id=1;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_info_idx mi_idx,movie_info mi WHERE t.id=mi_idx.movie_id AND t.id=mi.movie_id AND mi_idx.info_type_id=101 AND mi.info_type_id=8;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_keyword mk,movie_info mi WHERE t.id=mk.movie_id AND t.id=mi.movie_id AND mi.info_type_id=8;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_keyword mk,movie_info_idx mi_idx WHERE t.id=mk.movie_id AND t.id=mi_idx.movie_id AND mi_idx.info_type_id=101;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_info_idx mi_idx,title t,movie_info mi WHERE t.id=mi_idx.movie_id AND t.id=mi.movie_id AND mi_idx.info_type_id=101 AND t.production_year>2010 AND t.kind_id=1 AND mi.info_type_id=8;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t,movie_info mi WHERE t.id=mk.movie_id AND t.id=mi.movie_id AND t.production_year>2010 AND t.kind_id=1 AND mi.info_type_id=8;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t,movie_info_idx mi_idx WHERE t.id=mk.movie_id AND t.id=mi_idx.movie_id AND t.production_year>2010 AND t.kind_id=1 AND mi_idx.info_type_id=101;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_keyword mk,movie_info mi,movie_info_idx mi_idx WHERE t.id=mk.movie_id AND t.id=mi.movie_id AND t.id=mi_idx.movie_id AND mi.info_type_id=8 AND mi_idx.info_type_id=101;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t,movie_info mi,movie_info_idx mi_idx WHERE t.id=mk.movie_id AND t.id=mi.movie_id AND t.id=mi_idx.movie_id AND t.production_year>2010 AND t.kind_id=1 AND mi.info_type_id=8 AND mi_idx.info_type_id=101;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_info mi,title t WHERE t.id=mi.movie_id AND mi.info_type_id=8 AND t.kind_id=1;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_info_idx mi_idx,title t WHERE t.id=mi_idx.movie_id AND mi_idx.info_type_id=101 AND t.kind_id=1;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t WHERE t.id=mk.movie_id AND t.kind_id=1;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_info_idx mi_idx,movie_info mi WHERE t.id=mi_idx.movie_id AND t.id=mi.movie_id AND mi_idx.info_type_id=101 AND mi.info_type_id=8;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_keyword mk,movie_info mi WHERE t.id=mk.movie_id AND t.id=mi.movie_id AND mi.info_type_id=8;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_keyword mk,movie_info_idx mi_idx WHERE t.id=mk.movie_id AND t.id=mi_idx.movie_id AND mi_idx.info_type_id=101;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_info_idx mi_idx,title t,movie_info mi WHERE t.id=mi_idx.movie_id AND t.id=mi.movie_id AND mi_idx.info_type_id=101 AND t.kind_id=1 AND mi.info_type_id=8;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t,movie_info mi WHERE t.id=mk.movie_id AND t.id=mi.movie_id AND t.kind_id=1 AND mi.info_type_id=8;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t,movie_info_idx mi_idx WHERE t.id=mk.movie_id AND t.id=mi_idx.movie_id AND t.kind_id=1 AND mi_idx.info_type_id=101;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_keyword mk,movie_info mi,movie_info_idx mi_idx WHERE t.id=mk.movie_id AND t.id=mi.movie_id AND t.id=mi_idx.movie_id AND mi.info_type_id=8 AND mi_idx.info_type_id=101;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t,movie_info mi,movie_info_idx mi_idx WHERE t.id=mk.movie_id AND t.id=mi.movie_id AND t.id=mi_idx.movie_id AND t.kind_id=1 AND mi.info_type_id=8 AND mi_idx.info_type_id=101;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_info mi,title t WHERE t.id=mi.movie_id AND mi.info_type_id=8 AND t.production_year>2005;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_info_idx mi_idx,title t WHERE t.id=mi_idx.movie_id AND mi_idx.info_type_id=101 AND t.production_year>2005;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t WHERE t.id=mk.movie_id AND t.production_year>2005;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_info_idx mi_idx,movie_info mi WHERE t.id=mi_idx.movie_id AND t.id=mi.movie_id AND mi_idx.info_type_id=101 AND mi.info_type_id=8;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_keyword mk,movie_info mi WHERE t.id=mk.movie_id AND t.id=mi.movie_id AND mi.info_type_id=8;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_keyword mk,movie_info_idx mi_idx WHERE t.id=mk.movie_id AND t.id=mi_idx.movie_id AND mi_idx.info_type_id=101;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_info_idx mi_idx,title t,movie_info mi WHERE t.id=mi_idx.movie_id AND t.id=mi.movie_id AND mi_idx.info_type_id=101 AND t.production_year>2005 AND mi.info_type_id=8;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t,movie_info mi WHERE t.id=mk.movie_id AND t.id=mi.movie_id AND t.production_year>2005 AND mi.info_type_id=8;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t,movie_info_idx mi_idx WHERE t.id=mk.movie_id AND t.id=mi_idx.movie_id AND t.production_year>2005 AND mi_idx.info_type_id=101;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_keyword mk,movie_info mi,movie_info_idx mi_idx WHERE t.id=mk.movie_id AND t.id=mi.movie_id AND t.id=mi_idx.movie_id AND mi.info_type_id=8 AND mi_idx.info_type_id=101;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t,movie_info mi,movie_info_idx mi_idx WHERE t.id=mk.movie_id AND t.id=mi.movie_id AND t.id=mi_idx.movie_id AND t.production_year>2005 AND mi.info_type_id=8 AND mi_idx.info_type_id=101;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_info mi,title t WHERE t.id=mi.movie_id AND mi.info_type_id=16 AND t.production_year>2000;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_companies mc,title t WHERE t.id=mc.movie_id AND t.production_year>2000;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t WHERE t.id=mk.movie_id AND t.production_year>2000;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_companies mc,movie_info mi WHERE t.id=mc.movie_id AND t.id=mi.movie_id AND mi.info_type_id=16;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_keyword mk,movie_info mi WHERE t.id=mk.movie_id AND t.id=mi.movie_id AND mi.info_type_id=16;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_keyword mk,movie_companies mc WHERE t.id=mk.movie_id AND t.id=mc.movie_id;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_companies mc,title t,movie_info mi WHERE t.id=mc.movie_id AND t.id=mi.movie_id AND t.production_year>2000 AND mi.info_type_id=16;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t,movie_info mi WHERE t.id=mk.movie_id AND t.id=mi.movie_id AND t.production_year>2000 AND mi.info_type_id=16;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t,movie_companies mc WHERE t.id=mk.movie_id AND t.id=mc.movie_id AND t.production_year>2000;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_keyword mk,movie_info mi,movie_companies mc WHERE t.id=mk.movie_id AND t.id=mi.movie_id AND t.id=mc.movie_id AND mi.info_type_id=16;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t,movie_info mi,movie_companies mc WHERE t.id=mk.movie_id AND t.id=mi.movie_id AND t.id=mc.movie_id AND t.production_year>2000 AND mi.info_type_id=16;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_info mi,title t WHERE t.id=mi.movie_id AND mi.info_type_id=16 AND t.production_year>2005 AND t.production_year<2010;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_companies mc,title t WHERE t.id=mc.movie_id AND t.production_year>2005 AND t.production_year<2010;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t WHERE t.id=mk.movie_id AND t.production_year>2005 AND t.production_year<2010;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_companies mc,movie_info mi WHERE t.id=mc.movie_id AND t.id=mi.movie_id AND mi.info_type_id=16;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_keyword mk,movie_info mi WHERE t.id=mk.movie_id AND t.id=mi.movie_id AND mi.info_type_id=16;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_keyword mk,movie_companies mc WHERE t.id=mk.movie_id AND t.id=mc.movie_id;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_companies mc,title t,movie_info mi WHERE t.id=mc.movie_id AND t.id=mi.movie_id AND t.production_year>2005 AND t.production_year<2010 AND mi.info_type_id=16;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t,movie_info mi WHERE t.id=mk.movie_id AND t.id=mi.movie_id AND t.production_year>2005 AND t.production_year<2010 AND mi.info_type_id=16;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t,movie_companies mc WHERE t.id=mk.movie_id AND t.id=mc.movie_id AND t.production_year>2005 AND t.production_year<2010;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_keyword mk,movie_info mi,movie_companies mc WHERE t.id=mk.movie_id AND t.id=mi.movie_id AND t.id=mc.movie_id AND mi.info_type_id=16;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t,movie_info mi,movie_companies mc WHERE t.id=mk.movie_id AND t.id=mi.movie_id AND t.id=mc.movie_id AND t.production_year>2005 AND t.production_year<2010 AND mi.info_type_id=16;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_info mi,title t WHERE t.id=mi.movie_id AND mi.info_type_id=16 AND t.production_year>1990;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_companies mc,title t WHERE t.id=mc.movie_id AND t.production_year>1990;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t WHERE t.id=mk.movie_id AND t.production_year>1990;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_companies mc,movie_info mi WHERE t.id=mc.movie_id AND t.id=mi.movie_id AND mi.info_type_id=16;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_keyword mk,movie_info mi WHERE t.id=mk.movie_id AND t.id=mi.movie_id AND mi.info_type_id=16;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_keyword mk,movie_companies mc WHERE t.id=mk.movie_id AND t.id=mc.movie_id;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_companies mc,title t,movie_info mi WHERE t.id=mc.movie_id AND t.id=mi.movie_id AND t.production_year>1990 AND mi.info_type_id=16;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t,movie_info mi WHERE t.id=mk.movie_id AND t.id=mi.movie_id AND t.production_year>1990 AND mi.info_type_id=16;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t,movie_companies mc WHERE t.id=mk.movie_id AND t.id=mc.movie_id AND t.production_year>1990;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_keyword mk,movie_info mi,movie_companies mc WHERE t.id=mk.movie_id AND t.id=mi.movie_id AND t.id=mc.movie_id AND mi.info_type_id=16;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t,movie_info mi,movie_companies mc WHERE t.id=mk.movie_id AND t.id=mi.movie_id AND t.id=mc.movie_id AND t.production_year>1990 AND mi.info_type_id=16;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,cast_info ci WHERE t.id=ci.movie_id;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_keyword mk,cast_info ci WHERE t.id=mk.movie_id AND t.id=ci.movie_id AND mk.keyword_id=117;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_companies mc,cast_info ci WHERE t.id=mc.movie_id AND t.id=ci.movie_id;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t WHERE t.id=mk.movie_id AND mk.keyword_id=117;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_companies mc,title t WHERE t.id=mc.movie_id;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_companies mc,movie_keyword mk WHERE t.id=mc.movie_id AND t.id=mk.movie_id AND mk.keyword_id=117;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,cast_info ci,title t WHERE t.id=mk.movie_id AND t.id=ci.movie_id AND mk.keyword_id=117;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_companies mc,cast_info ci,title t WHERE t.id=mc.movie_id AND t.id=ci.movie_id;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_companies mc,cast_info ci,movie_keyword mk WHERE t.id=mc.movie_id AND t.id=ci.movie_id AND t.id=mk.movie_id AND mk.keyword_id=117;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_companies mc,title t,movie_keyword mk WHERE t.id=mc.movie_id AND t.id=mk.movie_id AND mk.keyword_id=117;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_companies mc,cast_info ci,title t,movie_keyword mk WHERE t.id=mc.movie_id AND t.id=ci.movie_id AND t.id=mk.movie_id AND mk.keyword_id=117;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_info mi,title t WHERE t.id=mi.movie_id AND mi.info_type_id=105;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_info_idx mi_idx,title t WHERE t.id=mi_idx.movie_id AND mi_idx.info_type_id=100;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM cast_info ci,title t WHERE t.id=ci.movie_id;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_info_idx mi_idx,movie_info mi WHERE t.id=mi_idx.movie_id AND t.id=mi.movie_id AND mi_idx.info_type_id=100 AND mi.info_type_id=105;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,cast_info ci,movie_info mi WHERE t.id=ci.movie_id AND t.id=mi.movie_id AND mi.info_type_id=105;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,cast_info ci,movie_info_idx mi_idx WHERE t.id=ci.movie_id AND t.id=mi_idx.movie_id AND mi_idx.info_type_id=100;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_info_idx mi_idx,title t,movie_info mi WHERE t.id=mi_idx.movie_id AND t.id=mi.movie_id AND mi_idx.info_type_id=100 AND mi.info_type_id=105;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM cast_info ci,title t,movie_info mi WHERE t.id=ci.movie_id AND t.id=mi.movie_id AND mi.info_type_id=105;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM cast_info ci,title t,movie_info_idx mi_idx WHERE t.id=ci.movie_id AND t.id=mi_idx.movie_id AND mi_idx.info_type_id=100;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,cast_info ci,movie_info mi,movie_info_idx mi_idx WHERE t.id=ci.movie_id AND t.id=mi.movie_id AND t.id=mi_idx.movie_id AND mi.info_type_id=105 AND mi_idx.info_type_id=100;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM cast_info ci,title t,movie_info mi,movie_info_idx mi_idx WHERE t.id=ci.movie_id AND t.id=mi.movie_id AND t.id=mi_idx.movie_id AND mi.info_type_id=105 AND mi_idx.info_type_id=100;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_info mi,title t WHERE t.id=mi.movie_id AND mi.info_type_id=3 AND t.production_year>2008 AND t.production_year<2014;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_info_idx mi_idx,title t WHERE t.id=mi_idx.movie_id AND mi_idx.info_type_id=101 AND t.production_year>2008 AND t.production_year<2014;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM cast_info ci,title t WHERE t.id=ci.movie_id AND t.production_year>2008 AND t.production_year<2014;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_info_idx mi_idx,movie_info mi WHERE t.id=mi_idx.movie_id AND t.id=mi.movie_id AND mi_idx.info_type_id=101 AND mi.info_type_id=3;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,cast_info ci,movie_info mi WHERE t.id=ci.movie_id AND t.id=mi.movie_id AND mi.info_type_id=3;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,cast_info ci,movie_info_idx mi_idx WHERE t.id=ci.movie_id AND t.id=mi_idx.movie_id AND mi_idx.info_type_id=101;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_info_idx mi_idx,title t,movie_info mi WHERE t.id=mi_idx.movie_id AND t.id=mi.movie_id AND mi_idx.info_type_id=101 AND t.production_year>2008 AND t.production_year<2014 AND mi.info_type_id=3;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM cast_info ci,title t,movie_info mi WHERE t.id=ci.movie_id AND t.id=mi.movie_id AND t.production_year>2008 AND t.production_year<2014 AND mi.info_type_id=3;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM cast_info ci,title t,movie_info_idx mi_idx WHERE t.id=ci.movie_id AND t.id=mi_idx.movie_id AND t.production_year>2008 AND t.production_year<2014 AND mi_idx.info_type_id=101;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,cast_info ci,movie_info mi,movie_info_idx mi_idx WHERE t.id=ci.movie_id AND t.id=mi.movie_id AND t.id=mi_idx.movie_id AND mi.info_type_id=3 AND mi_idx.info_type_id=101;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM cast_info ci,title t,movie_info mi,movie_info_idx mi_idx WHERE t.id=ci.movie_id AND t.id=mi.movie_id AND t.id=mi_idx.movie_id AND t.production_year>2008 AND t.production_year<2014 AND mi.info_type_id=3 AND mi_idx.info_type_id=101;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_info mi,title t WHERE t.id=mi.movie_id AND mi.info_type_id=3;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_info_idx mi_idx,title t WHERE t.id=mi_idx.movie_id AND mi_idx.info_type_id=100;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM cast_info ci,title t WHERE t.id=ci.movie_id;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_info_idx mi_idx,movie_info mi WHERE t.id=mi_idx.movie_id AND t.id=mi.movie_id AND mi_idx.info_type_id=100 AND mi.info_type_id=3;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,cast_info ci,movie_info mi WHERE t.id=ci.movie_id AND t.id=mi.movie_id AND mi.info_type_id=3;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,cast_info ci,movie_info_idx mi_idx WHERE t.id=ci.movie_id AND t.id=mi_idx.movie_id AND mi_idx.info_type_id=100;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_info_idx mi_idx,title t,movie_info mi WHERE t.id=mi_idx.movie_id AND t.id=mi.movie_id AND mi_idx.info_type_id=100 AND mi.info_type_id=3;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM cast_info ci,title t,movie_info mi WHERE t.id=ci.movie_id AND t.id=mi.movie_id AND mi.info_type_id=3;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM cast_info ci,title t,movie_info_idx mi_idx WHERE t.id=ci.movie_id AND t.id=mi_idx.movie_id AND mi_idx.info_type_id=100;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,cast_info ci,movie_info mi,movie_info_idx mi_idx WHERE t.id=ci.movie_id AND t.id=mi.movie_id AND t.id=mi_idx.movie_id AND mi.info_type_id=3 AND mi_idx.info_type_id=100;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM cast_info ci,title t,movie_info mi,movie_info_idx mi_idx WHERE t.id=ci.movie_id AND t.id=mi.movie_id AND t.id=mi_idx.movie_id AND mi.info_type_id=3 AND mi_idx.info_type_id=100;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_info mi,title t WHERE t.id=mi.movie_id AND mi.info_type_id=16 AND t.production_year>2005 AND t.production_year<2009;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_companies mc,title t WHERE t.id=mc.movie_id AND t.production_year>2005 AND t.production_year<2009;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM cast_info ci,title t WHERE t.id=ci.movie_id AND ci.role_id=2 AND t.production_year>2005 AND t.production_year<2009;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_companies mc,movie_info mi WHERE t.id=mc.movie_id AND t.id=mi.movie_id AND mi.info_type_id=16;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,cast_info ci,movie_info mi WHERE t.id=ci.movie_id AND t.id=mi.movie_id AND ci.role_id=2 AND mi.info_type_id=16;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,cast_info ci,movie_companies mc WHERE t.id=ci.movie_id AND t.id=mc.movie_id AND ci.role_id=2;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_companies mc,title t,movie_info mi WHERE t.id=mc.movie_id AND t.id=mi.movie_id AND t.production_year>2005 AND t.production_year<2009 AND mi.info_type_id=16;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM cast_info ci,title t,movie_info mi WHERE t.id=ci.movie_id AND t.id=mi.movie_id AND ci.role_id=2 AND t.production_year>2005 AND t.production_year<2009 AND mi.info_type_id=16;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM cast_info ci,title t,movie_companies mc WHERE t.id=ci.movie_id AND t.id=mc.movie_id AND ci.role_id=2 AND t.production_year>2005 AND t.production_year<2009;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,cast_info ci,movie_info mi,movie_companies mc WHERE t.id=ci.movie_id AND t.id=mi.movie_id AND t.id=mc.movie_id AND ci.role_id=2 AND mi.info_type_id=16;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM cast_info ci,title t,movie_info mi,movie_companies mc WHERE t.id=ci.movie_id AND t.id=mi.movie_id AND t.id=mc.movie_id AND ci.role_id=2 AND t.production_year>2005 AND t.production_year<2009 AND mi.info_type_id=16;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_info mi,title t WHERE t.id=mi.movie_id AND mi.info_type_id=16;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_companies mc,title t WHERE t.id=mc.movie_id;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM cast_info ci,title t WHERE t.id=ci.movie_id AND ci.role_id=2;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_companies mc,movie_info mi WHERE t.id=mc.movie_id AND t.id=mi.movie_id AND mi.info_type_id=16;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,cast_info ci,movie_info mi WHERE t.id=ci.movie_id AND t.id=mi.movie_id AND ci.role_id=2 AND mi.info_type_id=16;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,cast_info ci,movie_companies mc WHERE t.id=ci.movie_id AND t.id=mc.movie_id AND ci.role_id=2;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_companies mc,title t,movie_info mi WHERE t.id=mc.movie_id AND t.id=mi.movie_id AND mi.info_type_id=16;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM cast_info ci,title t,movie_info mi WHERE t.id=ci.movie_id AND t.id=mi.movie_id AND ci.role_id=2 AND mi.info_type_id=16;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM cast_info ci,title t,movie_companies mc WHERE t.id=ci.movie_id AND t.id=mc.movie_id AND ci.role_id=2;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,cast_info ci,movie_info mi,movie_companies mc WHERE t.id=ci.movie_id AND t.id=mi.movie_id AND t.id=mc.movie_id AND ci.role_id=2 AND mi.info_type_id=16;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM cast_info ci,title t,movie_info mi,movie_companies mc WHERE t.id=ci.movie_id AND t.id=mi.movie_id AND t.id=mc.movie_id AND ci.role_id=2 AND mi.info_type_id=16;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_info mi,title t WHERE t.id=mi.movie_id AND mi.info_type_id=16 AND t.production_year>2000;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_companies mc,title t WHERE t.id=mc.movie_id AND t.production_year>2000;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM cast_info ci,title t WHERE t.id=ci.movie_id AND ci.role_id=2 AND t.production_year>2000;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_companies mc,movie_info mi WHERE t.id=mc.movie_id AND t.id=mi.movie_id AND mi.info_type_id=16;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,cast_info ci,movie_info mi WHERE t.id=ci.movie_id AND t.id=mi.movie_id AND ci.role_id=2 AND mi.info_type_id=16;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,cast_info ci,movie_companies mc WHERE t.id=ci.movie_id AND t.id=mc.movie_id AND ci.role_id=2;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_companies mc,title t,movie_info mi WHERE t.id=mc.movie_id AND t.id=mi.movie_id AND t.production_year>2000 AND mi.info_type_id=16;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM cast_info ci,title t,movie_info mi WHERE t.id=ci.movie_id AND t.id=mi.movie_id AND ci.role_id=2 AND t.production_year>2000 AND mi.info_type_id=16;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM cast_info ci,title t,movie_companies mc WHERE t.id=ci.movie_id AND t.id=mc.movie_id AND ci.role_id=2 AND t.production_year>2000;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,cast_info ci,movie_info mi,movie_companies mc WHERE t.id=ci.movie_id AND t.id=mi.movie_id AND t.id=mc.movie_id AND ci.role_id=2 AND mi.info_type_id=16;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM cast_info ci,title t,movie_info mi,movie_companies mc WHERE t.id=ci.movie_id AND t.id=mi.movie_id AND t.id=mc.movie_id AND ci.role_id=2 AND t.production_year>2000 AND mi.info_type_id=16;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM cast_info ci,title t WHERE t.id=ci.movie_id AND t.production_year>1950 AND t.kind_id=1;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t WHERE t.id=mk.movie_id AND t.production_year>1950 AND t.kind_id=1;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_keyword mk,cast_info ci WHERE t.id=mk.movie_id AND t.id=ci.movie_id;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t,cast_info ci WHERE t.id=mk.movie_id AND t.id=ci.movie_id AND t.production_year>1950 AND t.kind_id=1;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM cast_info ci,title t WHERE t.id=ci.movie_id AND t.production_year>2000 AND t.kind_id=1;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t WHERE t.id=mk.movie_id AND t.production_year>2000 AND t.kind_id=1;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_keyword mk,cast_info ci WHERE t.id=mk.movie_id AND t.id=ci.movie_id;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t,cast_info ci WHERE t.id=mk.movie_id AND t.id=ci.movie_id AND t.production_year>2000 AND t.kind_id=1;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t WHERE t.id=mk.movie_id AND mk.keyword_id=398 AND t.production_year>1950 AND t.production_year<2000;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_companies mc,title t WHERE t.id=mc.movie_id AND mc.company_type_id=2 AND t.production_year>1950 AND t.production_year<2000;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_info mi,title t WHERE t.id=mi.movie_id AND t.production_year>1950 AND t.production_year<2000;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_companies mc,movie_keyword mk WHERE t.id=mc.movie_id AND t.id=mk.movie_id AND mc.company_type_id=2 AND mk.keyword_id=398;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_info mi,movie_keyword mk WHERE t.id=mi.movie_id AND t.id=mk.movie_id AND mk.keyword_id=398;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_info mi,movie_companies mc WHERE t.id=mi.movie_id AND t.id=mc.movie_id AND mc.company_type_id=2;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_companies mc,title t,movie_keyword mk WHERE t.id=mc.movie_id AND t.id=mk.movie_id AND mc.company_type_id=2 AND t.production_year>1950 AND t.production_year<2000 AND mk.keyword_id=398;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_info mi,title t,movie_keyword mk WHERE t.id=mi.movie_id AND t.id=mk.movie_id AND t.production_year>1950 AND t.production_year<2000 AND mk.keyword_id=398;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_info mi,title t,movie_companies mc WHERE t.id=mi.movie_id AND t.id=mc.movie_id AND t.production_year>1950 AND t.production_year<2000 AND mc.company_type_id=2;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_info mi,movie_keyword mk,movie_companies mc WHERE t.id=mi.movie_id AND t.id=mk.movie_id AND t.id=mc.movie_id AND mk.keyword_id=398 AND mc.company_type_id=2;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_info mi,title t,movie_keyword mk,movie_companies mc WHERE t.id=mi.movie_id AND t.id=mk.movie_id AND t.id=mc.movie_id AND t.production_year>1950 AND t.production_year<2000 AND mk.keyword_id=398 AND mc.company_type_id=2;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t WHERE t.id=mk.movie_id AND mk.keyword_id=398 AND t.production_year>2000 AND t.production_year<2010;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_companies mc,title t WHERE t.id=mc.movie_id AND mc.company_type_id=2 AND t.production_year>2000 AND t.production_year<2010;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_info mi,title t WHERE t.id=mi.movie_id AND t.production_year>2000 AND t.production_year<2010;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_companies mc,movie_keyword mk WHERE t.id=mc.movie_id AND t.id=mk.movie_id AND mc.company_type_id=2 AND mk.keyword_id=398;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_info mi,movie_keyword mk WHERE t.id=mi.movie_id AND t.id=mk.movie_id AND mk.keyword_id=398;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_info mi,movie_companies mc WHERE t.id=mi.movie_id AND t.id=mc.movie_id AND mc.company_type_id=2;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_companies mc,title t,movie_keyword mk WHERE t.id=mc.movie_id AND t.id=mk.movie_id AND mc.company_type_id=2 AND t.production_year>2000 AND t.production_year<2010 AND mk.keyword_id=398;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_info mi,title t,movie_keyword mk WHERE t.id=mi.movie_id AND t.id=mk.movie_id AND t.production_year>2000 AND t.production_year<2010 AND mk.keyword_id=398;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_info mi,title t,movie_companies mc WHERE t.id=mi.movie_id AND t.id=mc.movie_id AND t.production_year>2000 AND t.production_year<2010 AND mc.company_type_id=2;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_info mi,movie_keyword mk,movie_companies mc WHERE t.id=mi.movie_id AND t.id=mk.movie_id AND t.id=mc.movie_id AND mk.keyword_id=398 AND mc.company_type_id=2;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_info mi,title t,movie_keyword mk,movie_companies mc WHERE t.id=mi.movie_id AND t.id=mk.movie_id AND t.id=mc.movie_id AND t.production_year>2000 AND t.production_year<2010 AND mk.keyword_id=398 AND mc.company_type_id=2;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t WHERE t.id=mk.movie_id AND mk.keyword_id=398 AND t.production_year>1950 AND t.production_year<2010;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_companies mc,title t WHERE t.id=mc.movie_id AND mc.company_type_id=2 AND t.production_year>1950 AND t.production_year<2010;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_info mi,title t WHERE t.id=mi.movie_id AND t.production_year>1950 AND t.production_year<2010;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_companies mc,movie_keyword mk WHERE t.id=mc.movie_id AND t.id=mk.movie_id AND mc.company_type_id=2 AND mk.keyword_id=398;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_info mi,movie_keyword mk WHERE t.id=mi.movie_id AND t.id=mk.movie_id AND mk.keyword_id=398;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_info mi,movie_companies mc WHERE t.id=mi.movie_id AND t.id=mc.movie_id AND mc.company_type_id=2;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_companies mc,title t,movie_keyword mk WHERE t.id=mc.movie_id AND t.id=mk.movie_id AND mc.company_type_id=2 AND t.production_year>1950 AND t.production_year<2010 AND mk.keyword_id=398;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_info mi,title t,movie_keyword mk WHERE t.id=mi.movie_id AND t.id=mk.movie_id AND t.production_year>1950 AND t.production_year<2010 AND mk.keyword_id=398;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_info mi,title t,movie_companies mc WHERE t.id=mi.movie_id AND t.id=mc.movie_id AND t.production_year>1950 AND t.production_year<2010 AND mc.company_type_id=2;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_info mi,movie_keyword mk,movie_companies mc WHERE t.id=mi.movie_id AND t.id=mk.movie_id AND t.id=mc.movie_id AND mk.keyword_id=398 AND mc.company_type_id=2;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_info mi,title t,movie_keyword mk,movie_companies mc WHERE t.id=mi.movie_id AND t.id=mk.movie_id AND t.id=mc.movie_id AND t.production_year>1950 AND t.production_year<2010 AND mk.keyword_id=398 AND mc.company_type_id=2;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_info mi,title t WHERE t.id=mi.movie_id AND mi.info_type_id=8 AND t.production_year>2008;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_info_idx mi_idx,title t WHERE t.id=mi_idx.movie_id AND mi_idx.info_type_id=101 AND t.production_year>2008;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t WHERE t.id=mk.movie_id AND t.production_year>2008;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_companies mc,title t WHERE t.id=mc.movie_id AND t.production_year>2008;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_info_idx mi_idx,movie_info mi WHERE t.id=mi_idx.movie_id AND t.id=mi.movie_id AND mi_idx.info_type_id=101 AND mi.info_type_id=8;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_keyword mk,movie_info mi WHERE t.id=mk.movie_id AND t.id=mi.movie_id AND mi.info_type_id=8;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_companies mc,movie_info mi WHERE t.id=mc.movie_id AND t.id=mi.movie_id AND mi.info_type_id=8;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_keyword mk,movie_info_idx mi_idx WHERE t.id=mk.movie_id AND t.id=mi_idx.movie_id AND mi_idx.info_type_id=101;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_companies mc,movie_info_idx mi_idx WHERE t.id=mc.movie_id AND t.id=mi_idx.movie_id AND mi_idx.info_type_id=101;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_companies mc,movie_keyword mk WHERE t.id=mc.movie_id AND t.id=mk.movie_id;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_info_idx mi_idx,title t,movie_info mi WHERE t.id=mi_idx.movie_id AND t.id=mi.movie_id AND mi_idx.info_type_id=101 AND t.production_year>2008 AND mi.info_type_id=8;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t,movie_info mi WHERE t.id=mk.movie_id AND t.id=mi.movie_id AND t.production_year>2008 AND mi.info_type_id=8;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_companies mc,title t,movie_info mi WHERE t.id=mc.movie_id AND t.id=mi.movie_id AND t.production_year>2008 AND mi.info_type_id=8;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t,movie_info_idx mi_idx WHERE t.id=mk.movie_id AND t.id=mi_idx.movie_id AND t.production_year>2008 AND mi_idx.info_type_id=101;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_companies mc,title t,movie_info_idx mi_idx WHERE t.id=mc.movie_id AND t.id=mi_idx.movie_id AND t.production_year>2008 AND mi_idx.info_type_id=101;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_companies mc,title t,movie_keyword mk WHERE t.id=mc.movie_id AND t.id=mk.movie_id AND t.production_year>2008;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_keyword mk,movie_info mi,movie_info_idx mi_idx WHERE t.id=mk.movie_id AND t.id=mi.movie_id AND t.id=mi_idx.movie_id AND mi.info_type_id=8 AND mi_idx.info_type_id=101;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_companies mc,movie_info mi,movie_info_idx mi_idx WHERE t.id=mc.movie_id AND t.id=mi.movie_id AND t.id=mi_idx.movie_id AND mi.info_type_id=8 AND mi_idx.info_type_id=101;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_companies mc,movie_info mi,movie_keyword mk WHERE t.id=mc.movie_id AND t.id=mi.movie_id AND t.id=mk.movie_id AND mi.info_type_id=8;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_companies mc,movie_info_idx mi_idx,movie_keyword mk WHERE t.id=mc.movie_id AND t.id=mi_idx.movie_id AND t.id=mk.movie_id AND mi_idx.info_type_id=101;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t,movie_info mi,movie_info_idx mi_idx WHERE t.id=mk.movie_id AND t.id=mi.movie_id AND t.id=mi_idx.movie_id AND t.production_year>2008 AND mi.info_type_id=8 AND mi_idx.info_type_id=101;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_companies mc,title t,movie_info mi,movie_info_idx mi_idx WHERE t.id=mc.movie_id AND t.id=mi.movie_id AND t.id=mi_idx.movie_id AND t.production_year>2008 AND mi.info_type_id=8 AND mi_idx.info_type_id=101;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_companies mc,title t,movie_info mi,movie_keyword mk WHERE t.id=mc.movie_id AND t.id=mi.movie_id AND t.id=mk.movie_id AND t.production_year>2008 AND mi.info_type_id=8;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_companies mc,title t,movie_info_idx mi_idx,movie_keyword mk WHERE t.id=mc.movie_id AND t.id=mi_idx.movie_id AND t.id=mk.movie_id AND t.production_year>2008 AND mi_idx.info_type_id=101;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_companies mc,movie_info mi,movie_info_idx mi_idx,movie_keyword mk WHERE t.id=mc.movie_id AND t.id=mi.movie_id AND t.id=mi_idx.movie_id AND t.id=mk.movie_id AND mi.info_type_id=8 AND mi_idx.info_type_id=101;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_companies mc,title t,movie_info mi,movie_info_idx mi_idx,movie_keyword mk WHERE t.id=mc.movie_id AND t.id=mi.movie_id AND t.id=mi_idx.movie_id AND t.id=mk.movie_id AND t.production_year>2008 AND mi.info_type_id=8 AND mi_idx.info_type_id=101;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_info mi,title t WHERE t.id=mi.movie_id AND mi.info_type_id=8 AND t.production_year>2009;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_info_idx mi_idx,title t WHERE t.id=mi_idx.movie_id AND mi_idx.info_type_id=101 AND t.production_year>2009;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t WHERE t.id=mk.movie_id AND t.production_year>2009;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_companies mc,title t WHERE t.id=mc.movie_id AND t.production_year>2009;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_info_idx mi_idx,movie_info mi WHERE t.id=mi_idx.movie_id AND t.id=mi.movie_id AND mi_idx.info_type_id=101 AND mi.info_type_id=8;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_keyword mk,movie_info mi WHERE t.id=mk.movie_id AND t.id=mi.movie_id AND mi.info_type_id=8;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_companies mc,movie_info mi WHERE t.id=mc.movie_id AND t.id=mi.movie_id AND mi.info_type_id=8;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_keyword mk,movie_info_idx mi_idx WHERE t.id=mk.movie_id AND t.id=mi_idx.movie_id AND mi_idx.info_type_id=101;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_companies mc,movie_info_idx mi_idx WHERE t.id=mc.movie_id AND t.id=mi_idx.movie_id AND mi_idx.info_type_id=101;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_companies mc,movie_keyword mk WHERE t.id=mc.movie_id AND t.id=mk.movie_id;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_info_idx mi_idx,title t,movie_info mi WHERE t.id=mi_idx.movie_id AND t.id=mi.movie_id AND mi_idx.info_type_id=101 AND t.production_year>2009 AND mi.info_type_id=8;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t,movie_info mi WHERE t.id=mk.movie_id AND t.id=mi.movie_id AND t.production_year>2009 AND mi.info_type_id=8;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_companies mc,title t,movie_info mi WHERE t.id=mc.movie_id AND t.id=mi.movie_id AND t.production_year>2009 AND mi.info_type_id=8;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t,movie_info_idx mi_idx WHERE t.id=mk.movie_id AND t.id=mi_idx.movie_id AND t.production_year>2009 AND mi_idx.info_type_id=101;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_companies mc,title t,movie_info_idx mi_idx WHERE t.id=mc.movie_id AND t.id=mi_idx.movie_id AND t.production_year>2009 AND mi_idx.info_type_id=101;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_companies mc,title t,movie_keyword mk WHERE t.id=mc.movie_id AND t.id=mk.movie_id AND t.production_year>2009;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_keyword mk,movie_info mi,movie_info_idx mi_idx WHERE t.id=mk.movie_id AND t.id=mi.movie_id AND t.id=mi_idx.movie_id AND mi.info_type_id=8 AND mi_idx.info_type_id=101;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_companies mc,movie_info mi,movie_info_idx mi_idx WHERE t.id=mc.movie_id AND t.id=mi.movie_id AND t.id=mi_idx.movie_id AND mi.info_type_id=8 AND mi_idx.info_type_id=101;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_companies mc,movie_info mi,movie_keyword mk WHERE t.id=mc.movie_id AND t.id=mi.movie_id AND t.id=mk.movie_id AND mi.info_type_id=8;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_companies mc,movie_info_idx mi_idx,movie_keyword mk WHERE t.id=mc.movie_id AND t.id=mi_idx.movie_id AND t.id=mk.movie_id AND mi_idx.info_type_id=101;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t,movie_info mi,movie_info_idx mi_idx WHERE t.id=mk.movie_id AND t.id=mi.movie_id AND t.id=mi_idx.movie_id AND t.production_year>2009 AND mi.info_type_id=8 AND mi_idx.info_type_id=101;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_companies mc,title t,movie_info mi,movie_info_idx mi_idx WHERE t.id=mc.movie_id AND t.id=mi.movie_id AND t.id=mi_idx.movie_id AND t.production_year>2009 AND mi.info_type_id=8 AND mi_idx.info_type_id=101;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_companies mc,title t,movie_info mi,movie_keyword mk WHERE t.id=mc.movie_id AND t.id=mi.movie_id AND t.id=mk.movie_id AND t.production_year>2009 AND mi.info_type_id=8;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_companies mc,title t,movie_info_idx mi_idx,movie_keyword mk WHERE t.id=mc.movie_id AND t.id=mi_idx.movie_id AND t.id=mk.movie_id AND t.production_year>2009 AND mi_idx.info_type_id=101;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_companies mc,movie_info mi,movie_info_idx mi_idx,movie_keyword mk WHERE t.id=mc.movie_id AND t.id=mi.movie_id AND t.id=mi_idx.movie_id AND t.id=mk.movie_id AND mi.info_type_id=8 AND mi_idx.info_type_id=101;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_companies mc,title t,movie_info mi,movie_info_idx mi_idx,movie_keyword mk WHERE t.id=mc.movie_id AND t.id=mi.movie_id AND t.id=mi_idx.movie_id AND t.id=mk.movie_id AND t.production_year>2009 AND mi.info_type_id=8 AND mi_idx.info_type_id=101;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_info mi,title t WHERE t.id=mi.movie_id AND mi.info_type_id=16 AND t.production_year>2010;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_companies mc,title t WHERE t.id=mc.movie_id AND t.production_year>2010;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM cast_info ci,title t WHERE t.id=ci.movie_id AND ci.role_id=2 AND t.production_year>2010;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t WHERE t.id=mk.movie_id AND t.production_year>2010;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_companies mc,movie_info mi WHERE t.id=mc.movie_id AND t.id=mi.movie_id AND mi.info_type_id=16;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,cast_info ci,movie_info mi WHERE t.id=ci.movie_id AND t.id=mi.movie_id AND ci.role_id=2 AND mi.info_type_id=16;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_keyword mk,movie_info mi WHERE t.id=mk.movie_id AND t.id=mi.movie_id AND mi.info_type_id=16;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,cast_info ci,movie_companies mc WHERE t.id=ci.movie_id AND t.id=mc.movie_id AND ci.role_id=2;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_keyword mk,movie_companies mc WHERE t.id=mk.movie_id AND t.id=mc.movie_id;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_keyword mk,cast_info ci WHERE t.id=mk.movie_id AND t.id=ci.movie_id AND ci.role_id=2;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_companies mc,title t,movie_info mi WHERE t.id=mc.movie_id AND t.id=mi.movie_id AND t.production_year>2010 AND mi.info_type_id=16;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM cast_info ci,title t,movie_info mi WHERE t.id=ci.movie_id AND t.id=mi.movie_id AND ci.role_id=2 AND t.production_year>2010 AND mi.info_type_id=16;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t,movie_info mi WHERE t.id=mk.movie_id AND t.id=mi.movie_id AND t.production_year>2010 AND mi.info_type_id=16;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM cast_info ci,title t,movie_companies mc WHERE t.id=ci.movie_id AND t.id=mc.movie_id AND ci.role_id=2 AND t.production_year>2010;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t,movie_companies mc WHERE t.id=mk.movie_id AND t.id=mc.movie_id AND t.production_year>2010;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t,cast_info ci WHERE t.id=mk.movie_id AND t.id=ci.movie_id AND t.production_year>2010 AND ci.role_id=2;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,cast_info ci,movie_info mi,movie_companies mc WHERE t.id=ci.movie_id AND t.id=mi.movie_id AND t.id=mc.movie_id AND ci.role_id=2 AND mi.info_type_id=16;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_keyword mk,movie_info mi,movie_companies mc WHERE t.id=mk.movie_id AND t.id=mi.movie_id AND t.id=mc.movie_id AND mi.info_type_id=16;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_keyword mk,movie_info mi,cast_info ci WHERE t.id=mk.movie_id AND t.id=mi.movie_id AND t.id=ci.movie_id AND mi.info_type_id=16 AND ci.role_id=2;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_keyword mk,movie_companies mc,cast_info ci WHERE t.id=mk.movie_id AND t.id=mc.movie_id AND t.id=ci.movie_id AND ci.role_id=2;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM cast_info ci,title t,movie_info mi,movie_companies mc WHERE t.id=ci.movie_id AND t.id=mi.movie_id AND t.id=mc.movie_id AND ci.role_id=2 AND t.production_year>2010 AND mi.info_type_id=16;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t,movie_info mi,movie_companies mc WHERE t.id=mk.movie_id AND t.id=mi.movie_id AND t.id=mc.movie_id AND t.production_year>2010 AND mi.info_type_id=16;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t,movie_info mi,cast_info ci WHERE t.id=mk.movie_id AND t.id=mi.movie_id AND t.id=ci.movie_id AND t.production_year>2010 AND mi.info_type_id=16 AND ci.role_id=2;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t,movie_companies mc,cast_info ci WHERE t.id=mk.movie_id AND t.id=mc.movie_id AND t.id=ci.movie_id AND t.production_year>2010 AND ci.role_id=2;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_keyword mk,movie_info mi,movie_companies mc,cast_info ci WHERE t.id=mk.movie_id AND t.id=mi.movie_id AND t.id=mc.movie_id AND t.id=ci.movie_id AND mi.info_type_id=16 AND ci.role_id=2;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t,movie_info mi,movie_companies mc,cast_info ci WHERE t.id=mk.movie_id AND t.id=mi.movie_id AND t.id=mc.movie_id AND t.id=ci.movie_id AND t.production_year>2010 AND mi.info_type_id=16 AND ci.role_id=2;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_info mi,title t WHERE t.id=mi.movie_id AND mi.info_type_id=16 AND t.production_year>2010;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_companies mc,title t WHERE t.id=mc.movie_id AND mc.company_id=22956 AND t.production_year>2010;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM cast_info ci,title t WHERE t.id=ci.movie_id AND ci.role_id=2 AND t.production_year>2010;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t WHERE t.id=mk.movie_id AND t.production_year>2010;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_companies mc,movie_info mi WHERE t.id=mc.movie_id AND t.id=mi.movie_id AND mc.company_id=22956 AND mi.info_type_id=16;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,cast_info ci,movie_info mi WHERE t.id=ci.movie_id AND t.id=mi.movie_id AND ci.role_id=2 AND mi.info_type_id=16;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_keyword mk,movie_info mi WHERE t.id=mk.movie_id AND t.id=mi.movie_id AND mi.info_type_id=16;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,cast_info ci,movie_companies mc WHERE t.id=ci.movie_id AND t.id=mc.movie_id AND ci.role_id=2 AND mc.company_id=22956;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_keyword mk,movie_companies mc WHERE t.id=mk.movie_id AND t.id=mc.movie_id AND mc.company_id=22956;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_keyword mk,cast_info ci WHERE t.id=mk.movie_id AND t.id=ci.movie_id AND ci.role_id=2;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_companies mc,title t,movie_info mi WHERE t.id=mc.movie_id AND t.id=mi.movie_id AND mc.company_id=22956 AND t.production_year>2010 AND mi.info_type_id=16;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM cast_info ci,title t,movie_info mi WHERE t.id=ci.movie_id AND t.id=mi.movie_id AND ci.role_id=2 AND t.production_year>2010 AND mi.info_type_id=16;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t,movie_info mi WHERE t.id=mk.movie_id AND t.id=mi.movie_id AND t.production_year>2010 AND mi.info_type_id=16;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM cast_info ci,title t,movie_companies mc WHERE t.id=ci.movie_id AND t.id=mc.movie_id AND ci.role_id=2 AND t.production_year>2010 AND mc.company_id=22956;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t,movie_companies mc WHERE t.id=mk.movie_id AND t.id=mc.movie_id AND t.production_year>2010 AND mc.company_id=22956;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t,cast_info ci WHERE t.id=mk.movie_id AND t.id=ci.movie_id AND t.production_year>2010 AND ci.role_id=2;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,cast_info ci,movie_info mi,movie_companies mc WHERE t.id=ci.movie_id AND t.id=mi.movie_id AND t.id=mc.movie_id AND ci.role_id=2 AND mi.info_type_id=16 AND mc.company_id=22956;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_keyword mk,movie_info mi,movie_companies mc WHERE t.id=mk.movie_id AND t.id=mi.movie_id AND t.id=mc.movie_id AND mi.info_type_id=16 AND mc.company_id=22956;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_keyword mk,movie_info mi,cast_info ci WHERE t.id=mk.movie_id AND t.id=mi.movie_id AND t.id=ci.movie_id AND mi.info_type_id=16 AND ci.role_id=2;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_keyword mk,movie_companies mc,cast_info ci WHERE t.id=mk.movie_id AND t.id=mc.movie_id AND t.id=ci.movie_id AND mc.company_id=22956 AND ci.role_id=2;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM cast_info ci,title t,movie_info mi,movie_companies mc WHERE t.id=ci.movie_id AND t.id=mi.movie_id AND t.id=mc.movie_id AND ci.role_id=2 AND t.production_year>2010 AND mi.info_type_id=16 AND mc.company_id=22956;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t,movie_info mi,movie_companies mc WHERE t.id=mk.movie_id AND t.id=mi.movie_id AND t.id=mc.movie_id AND t.production_year>2010 AND mi.info_type_id=16 AND mc.company_id=22956;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t,movie_info mi,cast_info ci WHERE t.id=mk.movie_id AND t.id=mi.movie_id AND t.id=ci.movie_id AND t.production_year>2010 AND mi.info_type_id=16 AND ci.role_id=2;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t,movie_companies mc,cast_info ci WHERE t.id=mk.movie_id AND t.id=mc.movie_id AND t.id=ci.movie_id AND t.production_year>2010 AND mc.company_id=22956 AND ci.role_id=2;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_keyword mk,movie_info mi,movie_companies mc,cast_info ci WHERE t.id=mk.movie_id AND t.id=mi.movie_id AND t.id=mc.movie_id AND t.id=ci.movie_id AND mi.info_type_id=16 AND mc.company_id=22956 AND ci.role_id=2;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t,movie_info mi,movie_companies mc,cast_info ci WHERE t.id=mk.movie_id AND t.id=mi.movie_id AND t.id=mc.movie_id AND t.id=ci.movie_id AND t.production_year>2010 AND mi.info_type_id=16 AND mc.company_id=22956 AND ci.role_id=2;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_info mi,title t WHERE t.id=mi.movie_id AND mi.info_type_id=16 AND t.production_year>2000;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_companies mc,title t WHERE t.id=mc.movie_id AND t.production_year>2000;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM cast_info ci,title t WHERE t.id=ci.movie_id AND ci.role_id=2 AND t.production_year>2000;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t WHERE t.id=mk.movie_id AND t.production_year>2000;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_companies mc,movie_info mi WHERE t.id=mc.movie_id AND t.id=mi.movie_id AND mi.info_type_id=16;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,cast_info ci,movie_info mi WHERE t.id=ci.movie_id AND t.id=mi.movie_id AND ci.role_id=2 AND mi.info_type_id=16;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_keyword mk,movie_info mi WHERE t.id=mk.movie_id AND t.id=mi.movie_id AND mi.info_type_id=16;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,cast_info ci,movie_companies mc WHERE t.id=ci.movie_id AND t.id=mc.movie_id AND ci.role_id=2;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_keyword mk,movie_companies mc WHERE t.id=mk.movie_id AND t.id=mc.movie_id;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_keyword mk,cast_info ci WHERE t.id=mk.movie_id AND t.id=ci.movie_id AND ci.role_id=2;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_companies mc,title t,movie_info mi WHERE t.id=mc.movie_id AND t.id=mi.movie_id AND t.production_year>2000 AND mi.info_type_id=16;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM cast_info ci,title t,movie_info mi WHERE t.id=ci.movie_id AND t.id=mi.movie_id AND ci.role_id=2 AND t.production_year>2000 AND mi.info_type_id=16;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t,movie_info mi WHERE t.id=mk.movie_id AND t.id=mi.movie_id AND t.production_year>2000 AND mi.info_type_id=16;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM cast_info ci,title t,movie_companies mc WHERE t.id=ci.movie_id AND t.id=mc.movie_id AND ci.role_id=2 AND t.production_year>2000;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t,movie_companies mc WHERE t.id=mk.movie_id AND t.id=mc.movie_id AND t.production_year>2000;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t,cast_info ci WHERE t.id=mk.movie_id AND t.id=ci.movie_id AND t.production_year>2000 AND ci.role_id=2;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,cast_info ci,movie_info mi,movie_companies mc WHERE t.id=ci.movie_id AND t.id=mi.movie_id AND t.id=mc.movie_id AND ci.role_id=2 AND mi.info_type_id=16;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_keyword mk,movie_info mi,movie_companies mc WHERE t.id=mk.movie_id AND t.id=mi.movie_id AND t.id=mc.movie_id AND mi.info_type_id=16;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_keyword mk,movie_info mi,cast_info ci WHERE t.id=mk.movie_id AND t.id=mi.movie_id AND t.id=ci.movie_id AND mi.info_type_id=16 AND ci.role_id=2;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_keyword mk,movie_companies mc,cast_info ci WHERE t.id=mk.movie_id AND t.id=mc.movie_id AND t.id=ci.movie_id AND ci.role_id=2;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM cast_info ci,title t,movie_info mi,movie_companies mc WHERE t.id=ci.movie_id AND t.id=mi.movie_id AND t.id=mc.movie_id AND ci.role_id=2 AND t.production_year>2000 AND mi.info_type_id=16;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t,movie_info mi,movie_companies mc WHERE t.id=mk.movie_id AND t.id=mi.movie_id AND t.id=mc.movie_id AND t.production_year>2000 AND mi.info_type_id=16;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t,movie_info mi,cast_info ci WHERE t.id=mk.movie_id AND t.id=mi.movie_id AND t.id=ci.movie_id AND t.production_year>2000 AND mi.info_type_id=16 AND ci.role_id=2;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t,movie_companies mc,cast_info ci WHERE t.id=mk.movie_id AND t.id=mc.movie_id AND t.id=ci.movie_id AND t.production_year>2000 AND ci.role_id=2;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_keyword mk,movie_info mi,movie_companies mc,cast_info ci WHERE t.id=mk.movie_id AND t.id=mi.movie_id AND t.id=mc.movie_id AND t.id=ci.movie_id AND mi.info_type_id=16 AND ci.role_id=2;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t,movie_info mi,movie_companies mc,cast_info ci WHERE t.id=mk.movie_id AND t.id=mi.movie_id AND t.id=mc.movie_id AND t.id=ci.movie_id AND t.production_year>2000 AND mi.info_type_id=16 AND ci.role_id=2;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_info mi,title t WHERE t.id=mi.movie_id AND mi.info_type_id=3;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_info_idx mi_idx,title t WHERE t.id=mi_idx.movie_id AND mi_idx.info_type_id=100;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM cast_info ci,title t WHERE t.id=ci.movie_id;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t WHERE t.id=mk.movie_id;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_info_idx mi_idx,movie_info mi WHERE t.id=mi_idx.movie_id AND t.id=mi.movie_id AND mi_idx.info_type_id=100 AND mi.info_type_id=3;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,cast_info ci,movie_info mi WHERE t.id=ci.movie_id AND t.id=mi.movie_id AND mi.info_type_id=3;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_keyword mk,movie_info mi WHERE t.id=mk.movie_id AND t.id=mi.movie_id AND mi.info_type_id=3;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,cast_info ci,movie_info_idx mi_idx WHERE t.id=ci.movie_id AND t.id=mi_idx.movie_id AND mi_idx.info_type_id=100;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_keyword mk,movie_info_idx mi_idx WHERE t.id=mk.movie_id AND t.id=mi_idx.movie_id AND mi_idx.info_type_id=100;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_keyword mk,cast_info ci WHERE t.id=mk.movie_id AND t.id=ci.movie_id;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_info_idx mi_idx,title t,movie_info mi WHERE t.id=mi_idx.movie_id AND t.id=mi.movie_id AND mi_idx.info_type_id=100 AND mi.info_type_id=3;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM cast_info ci,title t,movie_info mi WHERE t.id=ci.movie_id AND t.id=mi.movie_id AND mi.info_type_id=3;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t,movie_info mi WHERE t.id=mk.movie_id AND t.id=mi.movie_id AND mi.info_type_id=3;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM cast_info ci,title t,movie_info_idx mi_idx WHERE t.id=ci.movie_id AND t.id=mi_idx.movie_id AND mi_idx.info_type_id=100;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t,movie_info_idx mi_idx WHERE t.id=mk.movie_id AND t.id=mi_idx.movie_id AND mi_idx.info_type_id=100;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t,cast_info ci WHERE t.id=mk.movie_id AND t.id=ci.movie_id;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,cast_info ci,movie_info mi,movie_info_idx mi_idx WHERE t.id=ci.movie_id AND t.id=mi.movie_id AND t.id=mi_idx.movie_id AND mi.info_type_id=3 AND mi_idx.info_type_id=100;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_keyword mk,movie_info mi,movie_info_idx mi_idx WHERE t.id=mk.movie_id AND t.id=mi.movie_id AND t.id=mi_idx.movie_id AND mi.info_type_id=3 AND mi_idx.info_type_id=100;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_keyword mk,movie_info mi,cast_info ci WHERE t.id=mk.movie_id AND t.id=mi.movie_id AND t.id=ci.movie_id AND mi.info_type_id=3;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_keyword mk,movie_info_idx mi_idx,cast_info ci WHERE t.id=mk.movie_id AND t.id=mi_idx.movie_id AND t.id=ci.movie_id AND mi_idx.info_type_id=100;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM cast_info ci,title t,movie_info mi,movie_info_idx mi_idx WHERE t.id=ci.movie_id AND t.id=mi.movie_id AND t.id=mi_idx.movie_id AND mi.info_type_id=3 AND mi_idx.info_type_id=100;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t,movie_info mi,movie_info_idx mi_idx WHERE t.id=mk.movie_id AND t.id=mi.movie_id AND t.id=mi_idx.movie_id AND mi.info_type_id=3 AND mi_idx.info_type_id=100;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t,movie_info mi,cast_info ci WHERE t.id=mk.movie_id AND t.id=mi.movie_id AND t.id=ci.movie_id AND mi.info_type_id=3;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t,movie_info_idx mi_idx,cast_info ci WHERE t.id=mk.movie_id AND t.id=mi_idx.movie_id AND t.id=ci.movie_id AND mi_idx.info_type_id=100;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_keyword mk,movie_info mi,movie_info_idx mi_idx,cast_info ci WHERE t.id=mk.movie_id AND t.id=mi.movie_id AND t.id=mi_idx.movie_id AND t.id=ci.movie_id AND mi.info_type_id=3 AND mi_idx.info_type_id=100;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t,movie_info mi,movie_info_idx mi_idx,cast_info ci WHERE t.id=mk.movie_id AND t.id=mi.movie_id AND t.id=mi_idx.movie_id AND t.id=ci.movie_id AND mi.info_type_id=3 AND mi_idx.info_type_id=100;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_info mi,title t WHERE t.id=mi.movie_id AND mi.info_type_id=3 AND t.production_year>2010;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_info_idx mi_idx,title t WHERE t.id=mi_idx.movie_id AND mi_idx.info_type_id=100 AND t.production_year>2010;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM cast_info ci,title t WHERE t.id=ci.movie_id AND t.production_year>2010;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t WHERE t.id=mk.movie_id AND t.production_year>2010;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_info_idx mi_idx,movie_info mi WHERE t.id=mi_idx.movie_id AND t.id=mi.movie_id AND mi_idx.info_type_id=100 AND mi.info_type_id=3;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,cast_info ci,movie_info mi WHERE t.id=ci.movie_id AND t.id=mi.movie_id AND mi.info_type_id=3;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_keyword mk,movie_info mi WHERE t.id=mk.movie_id AND t.id=mi.movie_id AND mi.info_type_id=3;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,cast_info ci,movie_info_idx mi_idx WHERE t.id=ci.movie_id AND t.id=mi_idx.movie_id AND mi_idx.info_type_id=100;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_keyword mk,movie_info_idx mi_idx WHERE t.id=mk.movie_id AND t.id=mi_idx.movie_id AND mi_idx.info_type_id=100;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_keyword mk,cast_info ci WHERE t.id=mk.movie_id AND t.id=ci.movie_id;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_info_idx mi_idx,title t,movie_info mi WHERE t.id=mi_idx.movie_id AND t.id=mi.movie_id AND mi_idx.info_type_id=100 AND t.production_year>2010 AND mi.info_type_id=3;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM cast_info ci,title t,movie_info mi WHERE t.id=ci.movie_id AND t.id=mi.movie_id AND t.production_year>2010 AND mi.info_type_id=3;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t,movie_info mi WHERE t.id=mk.movie_id AND t.id=mi.movie_id AND t.production_year>2010 AND mi.info_type_id=3;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM cast_info ci,title t,movie_info_idx mi_idx WHERE t.id=ci.movie_id AND t.id=mi_idx.movie_id AND t.production_year>2010 AND mi_idx.info_type_id=100;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t,movie_info_idx mi_idx WHERE t.id=mk.movie_id AND t.id=mi_idx.movie_id AND t.production_year>2010 AND mi_idx.info_type_id=100;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t,cast_info ci WHERE t.id=mk.movie_id AND t.id=ci.movie_id AND t.production_year>2010;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,cast_info ci,movie_info mi,movie_info_idx mi_idx WHERE t.id=ci.movie_id AND t.id=mi.movie_id AND t.id=mi_idx.movie_id AND mi.info_type_id=3 AND mi_idx.info_type_id=100;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_keyword mk,movie_info mi,movie_info_idx mi_idx WHERE t.id=mk.movie_id AND t.id=mi.movie_id AND t.id=mi_idx.movie_id AND mi.info_type_id=3 AND mi_idx.info_type_id=100;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_keyword mk,movie_info mi,cast_info ci WHERE t.id=mk.movie_id AND t.id=mi.movie_id AND t.id=ci.movie_id AND mi.info_type_id=3;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_keyword mk,movie_info_idx mi_idx,cast_info ci WHERE t.id=mk.movie_id AND t.id=mi_idx.movie_id AND t.id=ci.movie_id AND mi_idx.info_type_id=100;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM cast_info ci,title t,movie_info mi,movie_info_idx mi_idx WHERE t.id=ci.movie_id AND t.id=mi.movie_id AND t.id=mi_idx.movie_id AND t.production_year>2010 AND mi.info_type_id=3 AND mi_idx.info_type_id=100;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t,movie_info mi,movie_info_idx mi_idx WHERE t.id=mk.movie_id AND t.id=mi.movie_id AND t.id=mi_idx.movie_id AND t.production_year>2010 AND mi.info_type_id=3 AND mi_idx.info_type_id=100;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t,movie_info mi,cast_info ci WHERE t.id=mk.movie_id AND t.id=mi.movie_id AND t.id=ci.movie_id AND t.production_year>2010 AND mi.info_type_id=3;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t,movie_info_idx mi_idx,cast_info ci WHERE t.id=mk.movie_id AND t.id=mi_idx.movie_id AND t.id=ci.movie_id AND t.production_year>2010 AND mi_idx.info_type_id=100;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_keyword mk,movie_info mi,movie_info_idx mi_idx,cast_info ci WHERE t.id=mk.movie_id AND t.id=mi.movie_id AND t.id=mi_idx.movie_id AND t.id=ci.movie_id AND mi.info_type_id=3 AND mi_idx.info_type_id=100;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t,movie_info mi,movie_info_idx mi_idx,cast_info ci WHERE t.id=mk.movie_id AND t.id=mi.movie_id AND t.id=mi_idx.movie_id AND t.id=ci.movie_id AND t.production_year>2010 AND mi.info_type_id=3 AND mi_idx.info_type_id=100;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM cast_info ci,title t WHERE t.id=ci.movie_id AND t.production_year>2000 AND t.kind_id=1;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t WHERE t.id=mk.movie_id AND t.production_year>2000 AND t.kind_id=1;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_info_idx mi_idx,title t WHERE t.id=mi_idx.movie_id AND mi_idx.info_type_id=101 AND t.production_year>2000 AND t.kind_id=1;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_keyword mk,cast_info ci WHERE t.id=mk.movie_id AND t.id=ci.movie_id;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_info_idx mi_idx,cast_info ci WHERE t.id=mi_idx.movie_id AND t.id=ci.movie_id AND mi_idx.info_type_id=101;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_info_idx mi_idx,movie_keyword mk WHERE t.id=mi_idx.movie_id AND t.id=mk.movie_id AND mi_idx.info_type_id=101;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t,cast_info ci WHERE t.id=mk.movie_id AND t.id=ci.movie_id AND t.production_year>2000 AND t.kind_id=1;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_info_idx mi_idx,title t,cast_info ci WHERE t.id=mi_idx.movie_id AND t.id=ci.movie_id AND mi_idx.info_type_id=101 AND t.production_year>2000 AND t.kind_id=1;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_info_idx mi_idx,title t,movie_keyword mk WHERE t.id=mi_idx.movie_id AND t.id=mk.movie_id AND mi_idx.info_type_id=101 AND t.production_year>2000 AND t.kind_id=1;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_info_idx mi_idx,cast_info ci,movie_keyword mk WHERE t.id=mi_idx.movie_id AND t.id=ci.movie_id AND t.id=mk.movie_id AND mi_idx.info_type_id=101;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_info_idx mi_idx,title t,cast_info ci,movie_keyword mk WHERE t.id=mi_idx.movie_id AND t.id=ci.movie_id AND t.id=mk.movie_id AND mi_idx.info_type_id=101 AND t.production_year>2000 AND t.kind_id=1;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM cast_info ci,title t WHERE t.id=ci.movie_id AND t.production_year>2005 AND t.kind_id=1;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t WHERE t.id=mk.movie_id AND t.production_year>2005 AND t.kind_id=1;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_info_idx mi_idx,title t WHERE t.id=mi_idx.movie_id AND mi_idx.info_type_id=101 AND t.production_year>2005 AND t.kind_id=1;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_keyword mk,cast_info ci WHERE t.id=mk.movie_id AND t.id=ci.movie_id;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_info_idx mi_idx,cast_info ci WHERE t.id=mi_idx.movie_id AND t.id=ci.movie_id AND mi_idx.info_type_id=101;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_info_idx mi_idx,movie_keyword mk WHERE t.id=mi_idx.movie_id AND t.id=mk.movie_id AND mi_idx.info_type_id=101;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t,cast_info ci WHERE t.id=mk.movie_id AND t.id=ci.movie_id AND t.production_year>2005 AND t.kind_id=1;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_info_idx mi_idx,title t,cast_info ci WHERE t.id=mi_idx.movie_id AND t.id=ci.movie_id AND mi_idx.info_type_id=101 AND t.production_year>2005 AND t.kind_id=1;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_info_idx mi_idx,title t,movie_keyword mk WHERE t.id=mi_idx.movie_id AND t.id=mk.movie_id AND mi_idx.info_type_id=101 AND t.production_year>2005 AND t.kind_id=1;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_info_idx mi_idx,cast_info ci,movie_keyword mk WHERE t.id=mi_idx.movie_id AND t.id=ci.movie_id AND t.id=mk.movie_id AND mi_idx.info_type_id=101;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_info_idx mi_idx,title t,cast_info ci,movie_keyword mk WHERE t.id=mi_idx.movie_id AND t.id=ci.movie_id AND t.id=mk.movie_id AND mi_idx.info_type_id=101 AND t.production_year>2005 AND t.kind_id=1;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t WHERE t.id=mk.movie_id AND mk.keyword_id=398 AND t.production_year=1998;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_companies mc,title t WHERE t.id=mc.movie_id AND mc.company_type_id=2 AND t.production_year=1998;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_info mi,title t WHERE t.id=mi.movie_id AND t.production_year=1998;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_companies mc,movie_keyword mk WHERE t.id=mc.movie_id AND t.id=mk.movie_id AND mc.company_type_id=2 AND mk.keyword_id=398;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_info mi,movie_keyword mk WHERE t.id=mi.movie_id AND t.id=mk.movie_id AND mk.keyword_id=398;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_info mi,movie_companies mc WHERE t.id=mi.movie_id AND t.id=mc.movie_id AND mc.company_type_id=2;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_companies mc,title t,movie_keyword mk WHERE t.id=mc.movie_id AND t.id=mk.movie_id AND mc.company_type_id=2 AND t.production_year=1998 AND mk.keyword_id=398;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_info mi,title t,movie_keyword mk WHERE t.id=mi.movie_id AND t.id=mk.movie_id AND t.production_year=1998 AND mk.keyword_id=398;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_info mi,title t,movie_companies mc WHERE t.id=mi.movie_id AND t.id=mc.movie_id AND t.production_year=1998 AND mc.company_type_id=2;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_info mi,movie_keyword mk,movie_companies mc WHERE t.id=mi.movie_id AND t.id=mk.movie_id AND t.id=mc.movie_id AND mk.keyword_id=398 AND mc.company_type_id=2;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_info mi,title t,movie_keyword mk,movie_companies mc WHERE t.id=mi.movie_id AND t.id=mk.movie_id AND t.id=mc.movie_id AND t.production_year=1998 AND mk.keyword_id=398 AND mc.company_type_id=2;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_info mi,title t WHERE t.id=mi.movie_id AND mi.info_type_id=8 AND t.production_year>2000;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_info_idx mi_idx,title t WHERE t.id=mi_idx.movie_id AND mi_idx.info_type_id=101 AND t.production_year>2000;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t WHERE t.id=mk.movie_id AND t.production_year>2000;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_companies mc,title t WHERE t.id=mc.movie_id AND t.production_year>2000;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_info_idx mi_idx,movie_info mi WHERE t.id=mi_idx.movie_id AND t.id=mi.movie_id AND mi_idx.info_type_id=101 AND mi.info_type_id=8;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_keyword mk,movie_info mi WHERE t.id=mk.movie_id AND t.id=mi.movie_id AND mi.info_type_id=8;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_companies mc,movie_info mi WHERE t.id=mc.movie_id AND t.id=mi.movie_id AND mi.info_type_id=8;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_keyword mk,movie_info_idx mi_idx WHERE t.id=mk.movie_id AND t.id=mi_idx.movie_id AND mi_idx.info_type_id=101;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_companies mc,movie_info_idx mi_idx WHERE t.id=mc.movie_id AND t.id=mi_idx.movie_id AND mi_idx.info_type_id=101;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_companies mc,movie_keyword mk WHERE t.id=mc.movie_id AND t.id=mk.movie_id;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_info_idx mi_idx,title t,movie_info mi WHERE t.id=mi_idx.movie_id AND t.id=mi.movie_id AND mi_idx.info_type_id=101 AND t.production_year>2000 AND mi.info_type_id=8;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t,movie_info mi WHERE t.id=mk.movie_id AND t.id=mi.movie_id AND t.production_year>2000 AND mi.info_type_id=8;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_companies mc,title t,movie_info mi WHERE t.id=mc.movie_id AND t.id=mi.movie_id AND t.production_year>2000 AND mi.info_type_id=8;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t,movie_info_idx mi_idx WHERE t.id=mk.movie_id AND t.id=mi_idx.movie_id AND t.production_year>2000 AND mi_idx.info_type_id=101;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_companies mc,title t,movie_info_idx mi_idx WHERE t.id=mc.movie_id AND t.id=mi_idx.movie_id AND t.production_year>2000 AND mi_idx.info_type_id=101;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_companies mc,title t,movie_keyword mk WHERE t.id=mc.movie_id AND t.id=mk.movie_id AND t.production_year>2000;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_keyword mk,movie_info mi,movie_info_idx mi_idx WHERE t.id=mk.movie_id AND t.id=mi.movie_id AND t.id=mi_idx.movie_id AND mi.info_type_id=8 AND mi_idx.info_type_id=101;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_companies mc,movie_info mi,movie_info_idx mi_idx WHERE t.id=mc.movie_id AND t.id=mi.movie_id AND t.id=mi_idx.movie_id AND mi.info_type_id=8 AND mi_idx.info_type_id=101;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_companies mc,movie_info mi,movie_keyword mk WHERE t.id=mc.movie_id AND t.id=mi.movie_id AND t.id=mk.movie_id AND mi.info_type_id=8;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_companies mc,movie_info_idx mi_idx,movie_keyword mk WHERE t.id=mc.movie_id AND t.id=mi_idx.movie_id AND t.id=mk.movie_id AND mi_idx.info_type_id=101;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t,movie_info mi,movie_info_idx mi_idx WHERE t.id=mk.movie_id AND t.id=mi.movie_id AND t.id=mi_idx.movie_id AND t.production_year>2000 AND mi.info_type_id=8 AND mi_idx.info_type_id=101;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_companies mc,title t,movie_info mi,movie_info_idx mi_idx WHERE t.id=mc.movie_id AND t.id=mi.movie_id AND t.id=mi_idx.movie_id AND t.production_year>2000 AND mi.info_type_id=8 AND mi_idx.info_type_id=101;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_companies mc,title t,movie_info mi,movie_keyword mk WHERE t.id=mc.movie_id AND t.id=mi.movie_id AND t.id=mk.movie_id AND t.production_year>2000 AND mi.info_type_id=8;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_companies mc,title t,movie_info_idx mi_idx,movie_keyword mk WHERE t.id=mc.movie_id AND t.id=mi_idx.movie_id AND t.id=mk.movie_id AND t.production_year>2000 AND mi_idx.info_type_id=101;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_companies mc,movie_info mi,movie_info_idx mi_idx,movie_keyword mk WHERE t.id=mc.movie_id AND t.id=mi.movie_id AND t.id=mi_idx.movie_id AND t.id=mk.movie_id AND mi.info_type_id=8 AND mi_idx.info_type_id=101;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_companies mc,title t,movie_info mi,movie_info_idx mi_idx,movie_keyword mk WHERE t.id=mc.movie_id AND t.id=mi.movie_id AND t.id=mi_idx.movie_id AND t.id=mk.movie_id AND t.production_year>2000 AND mi.info_type_id=8 AND mi_idx.info_type_id=101;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_info mi,title t WHERE t.id=mi.movie_id AND mi.info_type_id=8 AND t.production_year>2005;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_info_idx mi_idx,title t WHERE t.id=mi_idx.movie_id AND mi_idx.info_type_id=101 AND t.production_year>2005;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t WHERE t.id=mk.movie_id AND t.production_year>2005;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_companies mc,title t WHERE t.id=mc.movie_id AND t.production_year>2005;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_info_idx mi_idx,movie_info mi WHERE t.id=mi_idx.movie_id AND t.id=mi.movie_id AND mi_idx.info_type_id=101 AND mi.info_type_id=8;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_keyword mk,movie_info mi WHERE t.id=mk.movie_id AND t.id=mi.movie_id AND mi.info_type_id=8;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_companies mc,movie_info mi WHERE t.id=mc.movie_id AND t.id=mi.movie_id AND mi.info_type_id=8;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_keyword mk,movie_info_idx mi_idx WHERE t.id=mk.movie_id AND t.id=mi_idx.movie_id AND mi_idx.info_type_id=101;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_companies mc,movie_info_idx mi_idx WHERE t.id=mc.movie_id AND t.id=mi_idx.movie_id AND mi_idx.info_type_id=101;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_companies mc,movie_keyword mk WHERE t.id=mc.movie_id AND t.id=mk.movie_id;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_info_idx mi_idx,title t,movie_info mi WHERE t.id=mi_idx.movie_id AND t.id=mi.movie_id AND mi_idx.info_type_id=101 AND t.production_year>2005 AND mi.info_type_id=8;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t,movie_info mi WHERE t.id=mk.movie_id AND t.id=mi.movie_id AND t.production_year>2005 AND mi.info_type_id=8;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_companies mc,title t,movie_info mi WHERE t.id=mc.movie_id AND t.id=mi.movie_id AND t.production_year>2005 AND mi.info_type_id=8;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t,movie_info_idx mi_idx WHERE t.id=mk.movie_id AND t.id=mi_idx.movie_id AND t.production_year>2005 AND mi_idx.info_type_id=101;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_companies mc,title t,movie_info_idx mi_idx WHERE t.id=mc.movie_id AND t.id=mi_idx.movie_id AND t.production_year>2005 AND mi_idx.info_type_id=101;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_companies mc,title t,movie_keyword mk WHERE t.id=mc.movie_id AND t.id=mk.movie_id AND t.production_year>2005;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_keyword mk,movie_info mi,movie_info_idx mi_idx WHERE t.id=mk.movie_id AND t.id=mi.movie_id AND t.id=mi_idx.movie_id AND mi.info_type_id=8 AND mi_idx.info_type_id=101;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_companies mc,movie_info mi,movie_info_idx mi_idx WHERE t.id=mc.movie_id AND t.id=mi.movie_id AND t.id=mi_idx.movie_id AND mi.info_type_id=8 AND mi_idx.info_type_id=101;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_companies mc,movie_info mi,movie_keyword mk WHERE t.id=mc.movie_id AND t.id=mi.movie_id AND t.id=mk.movie_id AND mi.info_type_id=8;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_companies mc,movie_info_idx mi_idx,movie_keyword mk WHERE t.id=mc.movie_id AND t.id=mi_idx.movie_id AND t.id=mk.movie_id AND mi_idx.info_type_id=101;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t,movie_info mi,movie_info_idx mi_idx WHERE t.id=mk.movie_id AND t.id=mi.movie_id AND t.id=mi_idx.movie_id AND t.production_year>2005 AND mi.info_type_id=8 AND mi_idx.info_type_id=101;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_companies mc,title t,movie_info mi,movie_info_idx mi_idx WHERE t.id=mc.movie_id AND t.id=mi.movie_id AND t.id=mi_idx.movie_id AND t.production_year>2005 AND mi.info_type_id=8 AND mi_idx.info_type_id=101;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_companies mc,title t,movie_info mi,movie_keyword mk WHERE t.id=mc.movie_id AND t.id=mi.movie_id AND t.id=mk.movie_id AND t.production_year>2005 AND mi.info_type_id=8;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_companies mc,title t,movie_info_idx mi_idx,movie_keyword mk WHERE t.id=mc.movie_id AND t.id=mi_idx.movie_id AND t.id=mk.movie_id AND t.production_year>2005 AND mi_idx.info_type_id=101;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_companies mc,movie_info mi,movie_info_idx mi_idx,movie_keyword mk WHERE t.id=mc.movie_id AND t.id=mi.movie_id AND t.id=mi_idx.movie_id AND t.id=mk.movie_id AND mi.info_type_id=8 AND mi_idx.info_type_id=101;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_companies mc,title t,movie_info mi,movie_info_idx mi_idx,movie_keyword mk WHERE t.id=mc.movie_id AND t.id=mi.movie_id AND t.id=mi_idx.movie_id AND t.id=mk.movie_id AND t.production_year>2005 AND mi.info_type_id=8 AND mi_idx.info_type_id=101;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_info mi,title t WHERE t.id=mi.movie_id AND mi.info_type_id=16 AND t.production_year>2000 AND t.production_year<2010;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_companies mc,title t WHERE t.id=mc.movie_id AND t.production_year>2000 AND t.production_year<2010;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM cast_info ci,title t WHERE t.id=ci.movie_id AND ci.role_id=2 AND t.production_year>2000 AND t.production_year<2010;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t WHERE t.id=mk.movie_id AND mk.keyword_id=7084 AND t.production_year>2000 AND t.production_year<2010;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_companies mc,movie_info mi WHERE t.id=mc.movie_id AND t.id=mi.movie_id AND mi.info_type_id=16;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,cast_info ci,movie_info mi WHERE t.id=ci.movie_id AND t.id=mi.movie_id AND ci.role_id=2 AND mi.info_type_id=16;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_keyword mk,movie_info mi WHERE t.id=mk.movie_id AND t.id=mi.movie_id AND mk.keyword_id=7084 AND mi.info_type_id=16;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,cast_info ci,movie_companies mc WHERE t.id=ci.movie_id AND t.id=mc.movie_id AND ci.role_id=2;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_keyword mk,movie_companies mc WHERE t.id=mk.movie_id AND t.id=mc.movie_id AND mk.keyword_id=7084;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_keyword mk,cast_info ci WHERE t.id=mk.movie_id AND t.id=ci.movie_id AND mk.keyword_id=7084 AND ci.role_id=2;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_companies mc,title t,movie_info mi WHERE t.id=mc.movie_id AND t.id=mi.movie_id AND t.production_year>2000 AND t.production_year<2010 AND mi.info_type_id=16;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM cast_info ci,title t,movie_info mi WHERE t.id=ci.movie_id AND t.id=mi.movie_id AND ci.role_id=2 AND t.production_year>2000 AND t.production_year<2010 AND mi.info_type_id=16;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t,movie_info mi WHERE t.id=mk.movie_id AND t.id=mi.movie_id AND mk.keyword_id=7084 AND t.production_year>2000 AND t.production_year<2010 AND mi.info_type_id=16;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM cast_info ci,title t,movie_companies mc WHERE t.id=ci.movie_id AND t.id=mc.movie_id AND ci.role_id=2 AND t.production_year>2000 AND t.production_year<2010;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t,movie_companies mc WHERE t.id=mk.movie_id AND t.id=mc.movie_id AND mk.keyword_id=7084 AND t.production_year>2000 AND t.production_year<2010;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t,cast_info ci WHERE t.id=mk.movie_id AND t.id=ci.movie_id AND mk.keyword_id=7084 AND t.production_year>2000 AND t.production_year<2010 AND ci.role_id=2;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,cast_info ci,movie_info mi,movie_companies mc WHERE t.id=ci.movie_id AND t.id=mi.movie_id AND t.id=mc.movie_id AND ci.role_id=2 AND mi.info_type_id=16;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_keyword mk,movie_info mi,movie_companies mc WHERE t.id=mk.movie_id AND t.id=mi.movie_id AND t.id=mc.movie_id AND mk.keyword_id=7084 AND mi.info_type_id=16;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_keyword mk,movie_info mi,cast_info ci WHERE t.id=mk.movie_id AND t.id=mi.movie_id AND t.id=ci.movie_id AND mk.keyword_id=7084 AND mi.info_type_id=16 AND ci.role_id=2;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_keyword mk,movie_companies mc,cast_info ci WHERE t.id=mk.movie_id AND t.id=mc.movie_id AND t.id=ci.movie_id AND mk.keyword_id=7084 AND ci.role_id=2;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM cast_info ci,title t,movie_info mi,movie_companies mc WHERE t.id=ci.movie_id AND t.id=mi.movie_id AND t.id=mc.movie_id AND ci.role_id=2 AND t.production_year>2000 AND t.production_year<2010 AND mi.info_type_id=16;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t,movie_info mi,movie_companies mc WHERE t.id=mk.movie_id AND t.id=mi.movie_id AND t.id=mc.movie_id AND mk.keyword_id=7084 AND t.production_year>2000 AND t.production_year<2010 AND mi.info_type_id=16;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t,movie_info mi,cast_info ci WHERE t.id=mk.movie_id AND t.id=mi.movie_id AND t.id=ci.movie_id AND mk.keyword_id=7084 AND t.production_year>2000 AND t.production_year<2010 AND mi.info_type_id=16 AND ci.role_id=2;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t,movie_companies mc,cast_info ci WHERE t.id=mk.movie_id AND t.id=mc.movie_id AND t.id=ci.movie_id AND mk.keyword_id=7084 AND t.production_year>2000 AND t.production_year<2010 AND ci.role_id=2;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_keyword mk,movie_info mi,movie_companies mc,cast_info ci WHERE t.id=mk.movie_id AND t.id=mi.movie_id AND t.id=mc.movie_id AND t.id=ci.movie_id AND mk.keyword_id=7084 AND mi.info_type_id=16 AND ci.role_id=2;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t,movie_info mi,movie_companies mc,cast_info ci WHERE t.id=mk.movie_id AND t.id=mi.movie_id AND t.id=mc.movie_id AND t.id=ci.movie_id AND mk.keyword_id=7084 AND t.production_year>2000 AND t.production_year<2010 AND mi.info_type_id=16 AND ci.role_id=2;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_info mi,title t WHERE t.id=mi.movie_id AND mi.info_type_id=16 AND t.production_year>2000 AND t.production_year<2005;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_companies mc,title t WHERE t.id=mc.movie_id AND t.production_year>2000 AND t.production_year<2005;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM cast_info ci,title t WHERE t.id=ci.movie_id AND ci.role_id=2 AND t.production_year>2000 AND t.production_year<2005;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t WHERE t.id=mk.movie_id AND mk.keyword_id=7084 AND t.production_year>2000 AND t.production_year<2005;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_companies mc,movie_info mi WHERE t.id=mc.movie_id AND t.id=mi.movie_id AND mi.info_type_id=16;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,cast_info ci,movie_info mi WHERE t.id=ci.movie_id AND t.id=mi.movie_id AND ci.role_id=2 AND mi.info_type_id=16;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_keyword mk,movie_info mi WHERE t.id=mk.movie_id AND t.id=mi.movie_id AND mk.keyword_id=7084 AND mi.info_type_id=16;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,cast_info ci,movie_companies mc WHERE t.id=ci.movie_id AND t.id=mc.movie_id AND ci.role_id=2;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_keyword mk,movie_companies mc WHERE t.id=mk.movie_id AND t.id=mc.movie_id AND mk.keyword_id=7084;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_keyword mk,cast_info ci WHERE t.id=mk.movie_id AND t.id=ci.movie_id AND mk.keyword_id=7084 AND ci.role_id=2;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_companies mc,title t,movie_info mi WHERE t.id=mc.movie_id AND t.id=mi.movie_id AND t.production_year>2000 AND t.production_year<2005 AND mi.info_type_id=16;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM cast_info ci,title t,movie_info mi WHERE t.id=ci.movie_id AND t.id=mi.movie_id AND ci.role_id=2 AND t.production_year>2000 AND t.production_year<2005 AND mi.info_type_id=16;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t,movie_info mi WHERE t.id=mk.movie_id AND t.id=mi.movie_id AND mk.keyword_id=7084 AND t.production_year>2000 AND t.production_year<2005 AND mi.info_type_id=16;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM cast_info ci,title t,movie_companies mc WHERE t.id=ci.movie_id AND t.id=mc.movie_id AND ci.role_id=2 AND t.production_year>2000 AND t.production_year<2005;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t,movie_companies mc WHERE t.id=mk.movie_id AND t.id=mc.movie_id AND mk.keyword_id=7084 AND t.production_year>2000 AND t.production_year<2005;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t,cast_info ci WHERE t.id=mk.movie_id AND t.id=ci.movie_id AND mk.keyword_id=7084 AND t.production_year>2000 AND t.production_year<2005 AND ci.role_id=2;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,cast_info ci,movie_info mi,movie_companies mc WHERE t.id=ci.movie_id AND t.id=mi.movie_id AND t.id=mc.movie_id AND ci.role_id=2 AND mi.info_type_id=16;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_keyword mk,movie_info mi,movie_companies mc WHERE t.id=mk.movie_id AND t.id=mi.movie_id AND t.id=mc.movie_id AND mk.keyword_id=7084 AND mi.info_type_id=16;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_keyword mk,movie_info mi,cast_info ci WHERE t.id=mk.movie_id AND t.id=mi.movie_id AND t.id=ci.movie_id AND mk.keyword_id=7084 AND mi.info_type_id=16 AND ci.role_id=2;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_keyword mk,movie_companies mc,cast_info ci WHERE t.id=mk.movie_id AND t.id=mc.movie_id AND t.id=ci.movie_id AND mk.keyword_id=7084 AND ci.role_id=2;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM cast_info ci,title t,movie_info mi,movie_companies mc WHERE t.id=ci.movie_id AND t.id=mi.movie_id AND t.id=mc.movie_id AND ci.role_id=2 AND t.production_year>2000 AND t.production_year<2005 AND mi.info_type_id=16;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t,movie_info mi,movie_companies mc WHERE t.id=mk.movie_id AND t.id=mi.movie_id AND t.id=mc.movie_id AND mk.keyword_id=7084 AND t.production_year>2000 AND t.production_year<2005 AND mi.info_type_id=16;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t,movie_info mi,cast_info ci WHERE t.id=mk.movie_id AND t.id=mi.movie_id AND t.id=ci.movie_id AND mk.keyword_id=7084 AND t.production_year>2000 AND t.production_year<2005 AND mi.info_type_id=16 AND ci.role_id=2;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t,movie_companies mc,cast_info ci WHERE t.id=mk.movie_id AND t.id=mc.movie_id AND t.id=ci.movie_id AND mk.keyword_id=7084 AND t.production_year>2000 AND t.production_year<2005 AND ci.role_id=2;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_keyword mk,movie_info mi,movie_companies mc,cast_info ci WHERE t.id=mk.movie_id AND t.id=mi.movie_id AND t.id=mc.movie_id AND t.id=ci.movie_id AND mk.keyword_id=7084 AND mi.info_type_id=16 AND ci.role_id=2;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t,movie_info mi,movie_companies mc,cast_info ci WHERE t.id=mk.movie_id AND t.id=mi.movie_id AND t.id=mc.movie_id AND t.id=ci.movie_id AND mk.keyword_id=7084 AND t.production_year>2000 AND t.production_year<2005 AND mi.info_type_id=16 AND ci.role_id=2;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_info mi,title t WHERE t.id=mi.movie_id AND mi.info_type_id=3 AND t.production_year>2000;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_info_idx mi_idx,title t WHERE t.id=mi_idx.movie_id AND mi_idx.info_type_id=100 AND t.production_year>2000;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM cast_info ci,title t WHERE t.id=ci.movie_id AND t.production_year>2000;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t WHERE t.id=mk.movie_id AND t.production_year>2000;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_info_idx mi_idx,movie_info mi WHERE t.id=mi_idx.movie_id AND t.id=mi.movie_id AND mi_idx.info_type_id=100 AND mi.info_type_id=3;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,cast_info ci,movie_info mi WHERE t.id=ci.movie_id AND t.id=mi.movie_id AND mi.info_type_id=3;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_keyword mk,movie_info mi WHERE t.id=mk.movie_id AND t.id=mi.movie_id AND mi.info_type_id=3;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,cast_info ci,movie_info_idx mi_idx WHERE t.id=ci.movie_id AND t.id=mi_idx.movie_id AND mi_idx.info_type_id=100;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_keyword mk,movie_info_idx mi_idx WHERE t.id=mk.movie_id AND t.id=mi_idx.movie_id AND mi_idx.info_type_id=100;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_keyword mk,cast_info ci WHERE t.id=mk.movie_id AND t.id=ci.movie_id;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_info_idx mi_idx,title t,movie_info mi WHERE t.id=mi_idx.movie_id AND t.id=mi.movie_id AND mi_idx.info_type_id=100 AND t.production_year>2000 AND mi.info_type_id=3;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM cast_info ci,title t,movie_info mi WHERE t.id=ci.movie_id AND t.id=mi.movie_id AND t.production_year>2000 AND mi.info_type_id=3;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t,movie_info mi WHERE t.id=mk.movie_id AND t.id=mi.movie_id AND t.production_year>2000 AND mi.info_type_id=3;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM cast_info ci,title t,movie_info_idx mi_idx WHERE t.id=ci.movie_id AND t.id=mi_idx.movie_id AND t.production_year>2000 AND mi_idx.info_type_id=100;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t,movie_info_idx mi_idx WHERE t.id=mk.movie_id AND t.id=mi_idx.movie_id AND t.production_year>2000 AND mi_idx.info_type_id=100;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t,cast_info ci WHERE t.id=mk.movie_id AND t.id=ci.movie_id AND t.production_year>2000;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,cast_info ci,movie_info mi,movie_info_idx mi_idx WHERE t.id=ci.movie_id AND t.id=mi.movie_id AND t.id=mi_idx.movie_id AND mi.info_type_id=3 AND mi_idx.info_type_id=100;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_keyword mk,movie_info mi,movie_info_idx mi_idx WHERE t.id=mk.movie_id AND t.id=mi.movie_id AND t.id=mi_idx.movie_id AND mi.info_type_id=3 AND mi_idx.info_type_id=100;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_keyword mk,movie_info mi,cast_info ci WHERE t.id=mk.movie_id AND t.id=mi.movie_id AND t.id=ci.movie_id AND mi.info_type_id=3;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_keyword mk,movie_info_idx mi_idx,cast_info ci WHERE t.id=mk.movie_id AND t.id=mi_idx.movie_id AND t.id=ci.movie_id AND mi_idx.info_type_id=100;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM cast_info ci,title t,movie_info mi,movie_info_idx mi_idx WHERE t.id=ci.movie_id AND t.id=mi.movie_id AND t.id=mi_idx.movie_id AND t.production_year>2000 AND mi.info_type_id=3 AND mi_idx.info_type_id=100;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t,movie_info mi,movie_info_idx mi_idx WHERE t.id=mk.movie_id AND t.id=mi.movie_id AND t.id=mi_idx.movie_id AND t.production_year>2000 AND mi.info_type_id=3 AND mi_idx.info_type_id=100;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t,movie_info mi,cast_info ci WHERE t.id=mk.movie_id AND t.id=mi.movie_id AND t.id=ci.movie_id AND t.production_year>2000 AND mi.info_type_id=3;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t,movie_info_idx mi_idx,cast_info ci WHERE t.id=mk.movie_id AND t.id=mi_idx.movie_id AND t.id=ci.movie_id AND t.production_year>2000 AND mi_idx.info_type_id=100;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM title t,movie_keyword mk,movie_info mi,movie_info_idx mi_idx,cast_info ci WHERE t.id=mk.movie_id AND t.id=mi.movie_id AND t.id=mi_idx.movie_id AND t.id=ci.movie_id AND mi.info_type_id=3 AND mi_idx.info_type_id=100;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE)
SELECT * FROM movie_keyword mk,title t,movie_info mi,movie_info_idx mi_idx,cast_info ci WHERE t.id=mk.movie_id AND t.id=mi.movie_id AND t.id=mi_idx.movie_id AND t.id=ci.movie_id AND t.production_year>2000 AND mi.info_type_id=3 AND mi_idx.info_type_id=100;

EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE) SELECT * FROM movie_companies mc,title t,movie_info_idx mi_idx WHERE t.id=mc.movie_id AND t.id=mi_idx.movie_id AND mi_idx.info_type_id=112 AND mc.company_type_id=2;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE) SELECT * FROM movie_companies mc,title t,movie_info_idx mi_idx WHERE t.id=mc.movie_id AND t.id=mi_idx.movie_id AND mi_idx.info_type_id=113 AND mc.company_type_id=2 AND t.production_year>2005 AND t.production_year<2010;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE) SELECT * FROM movie_companies mc,title t,movie_info_idx mi_idx WHERE t.id=mc.movie_id AND t.id=mi_idx.movie_id AND mi_idx.info_type_id=112 AND mc.company_type_id=2 AND t.production_year>2010;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE) SELECT * FROM movie_companies mc,title t,movie_info_idx mi_idx WHERE t.id=mc.movie_id AND t.id=mi_idx.movie_id AND mi_idx.info_type_id=113 AND mc.company_type_id=2 AND t.production_year>2000;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE) SELECT * FROM movie_companies mc,title t,movie_keyword mk WHERE t.id=mc.movie_id AND t.id=mk.movie_id AND mk.keyword_id=117;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE) SELECT * FROM title t,movie_info mi,movie_keyword mk WHERE t.id=mi.movie_id AND t.id=mk.movie_id AND t.production_year>2005;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE) SELECT * FROM title t,movie_info mi,movie_keyword mk WHERE t.id=mi.movie_id AND t.id=mk.movie_id AND t.production_year>2010;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE) SELECT * FROM title t,movie_info mi,movie_keyword mk WHERE t.id=mi.movie_id AND t.id=mk.movie_id AND t.production_year>1990;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE) SELECT * FROM title t,movie_info_idx mi_idx,movie_keyword mk WHERE t.id=mi_idx.movie_id AND t.id=mk.movie_id AND t.production_year>2005 AND mi_idx.info_type_id=101;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE) SELECT * FROM title t,movie_info_idx mi_idx,movie_keyword mk WHERE t.id=mi_idx.movie_id AND t.id=mk.movie_id AND t.production_year>2010 AND mi_idx.info_type_id=101;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE) SELECT * FROM title t,movie_info_idx mi_idx,movie_keyword mk WHERE t.id=mi_idx.movie_id AND t.id=mk.movie_id AND t.production_year>1990 AND mi_idx.info_type_id=101;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE) SELECT * FROM title t,movie_info mi,movie_companies mc WHERE t.id=mi.movie_id AND t.id=mc.movie_id AND t.production_year>2005 AND mc.company_type_id=2;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE) SELECT * FROM title t,movie_info mi,movie_companies mc WHERE t.id=mi.movie_id AND t.id=mc.movie_id AND t.production_year>2010 AND mc.company_type_id=2;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE) SELECT * FROM title t,movie_info mi,movie_companies mc WHERE t.id=mi.movie_id AND t.id=mc.movie_id AND t.production_year>1990 AND mc.company_type_id=2;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE) SELECT * FROM movie_keyword mk,title t,cast_info ci WHERE t.id=mk.movie_id AND t.id=ci.movie_id AND t.production_year>2010 AND mk.keyword_id=8200;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE) SELECT * FROM movie_keyword mk,title t,cast_info ci WHERE t.id=mk.movie_id AND t.id=ci.movie_id AND t.production_year>2014;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE) SELECT * FROM movie_keyword mk,title t,cast_info ci WHERE t.id=mk.movie_id AND t.id=ci.movie_id AND t.production_year>2014 AND mk.keyword_id=8200;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE) SELECT * FROM movie_keyword mk,title t,cast_info ci WHERE t.id=mk.movie_id AND t.id=ci.movie_id AND t.production_year>2000 AND mk.keyword_id=8200;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE) SELECT * FROM movie_keyword mk,title t,cast_info ci WHERE t.id=mk.movie_id AND t.id=ci.movie_id AND t.production_year>2000;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE) SELECT * FROM cast_info ci,title t WHERE t.id=ci.movie_id AND t.production_year>1980 AND t.production_year<1995;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE) SELECT * FROM cast_info ci,title t WHERE t.id=ci.movie_id AND t.production_year>1980 AND t.production_year<1984;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE) SELECT * FROM cast_info ci,title t WHERE t.id=ci.movie_id AND t.production_year>1980 AND t.production_year<2010;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE) SELECT * FROM cast_info ci,title t,movie_companies mc WHERE t.id=ci.movie_id AND t.id=mc.movie_id AND ci.role_id=2;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE) SELECT * FROM cast_info ci,title t,movie_companies mc WHERE t.id=ci.movie_id AND t.id=mc.movie_id AND ci.role_id=4;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE) SELECT * FROM cast_info ci,title t,movie_companies mc WHERE t.id=ci.movie_id AND t.id=mc.movie_id AND ci.role_id=7;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE) SELECT * FROM cast_info ci,title t,movie_companies mc WHERE t.id=ci.movie_id AND t.id=mc.movie_id AND t.production_year>2005 AND t.production_year<2015 AND ci.role_id=2;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE) SELECT * FROM cast_info ci,title t,movie_companies mc WHERE t.id=ci.movie_id AND t.id=mc.movie_id AND t.production_year>2007 AND t.production_year<2010 AND ci.role_id=2;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE) SELECT * FROM title t,cast_info ci,movie_companies mc WHERE t.id=mc.movie_id AND t.id=ci.movie_id AND t.production_year>2005 AND ci.role_id=1;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE) SELECT * FROM title t,cast_info ci,movie_companies mc WHERE t.id=mc.movie_id AND t.id=ci.movie_id AND t.production_year>2010 AND ci.role_id=1;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE) SELECT * FROM title t,cast_info ci,movie_companies mc WHERE t.id=mc.movie_id AND t.id=ci.movie_id AND t.production_year>1990;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE) SELECT * FROM title t,movie_keyword mk,movie_companies mc WHERE t.id=mk.movie_id AND t.id=mc.movie_id AND mk.keyword_id=398 AND mc.company_type_id=2 AND t.production_year>1950 AND t.production_year<2000;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE) SELECT * FROM title t,movie_keyword mk,movie_companies mc WHERE t.id=mk.movie_id AND t.id=mc.movie_id AND mk.keyword_id=398 AND mc.company_type_id=2;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE) SELECT * FROM title t,movie_keyword mk,movie_companies mc WHERE t.id=mk.movie_id AND t.id=mc.movie_id AND t.production_year>1950;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE) SELECT * FROM title t,movie_info mi,movie_info_idx mi_idx,movie_companies mc WHERE t.id=mi.movie_id AND t.id=mi_idx.movie_id AND t.id=mc.movie_id AND mi_idx.info_type_id=101 AND mi.info_type_id=3 AND t.production_year>2005 AND t.production_year<2008 AND mc.company_type_id=2;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE) SELECT * FROM title t,movie_info mi,movie_info_idx mi_idx,movie_companies mc WHERE t.id=mi.movie_id AND t.id=mi_idx.movie_id AND t.id=mc.movie_id AND mi_idx.info_type_id=113 AND mi.info_type_id=105;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE) SELECT * FROM title t,movie_info mi,movie_info_idx mi_idx,movie_companies mc WHERE t.id=mi.movie_id AND t.id=mi_idx.movie_id AND t.id=mc.movie_id AND mi_idx.info_type_id=101 AND mi.info_type_id=3 AND t.production_year>2000 AND t.production_year<2010 AND mc.company_type_id=2;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE) SELECT * FROM title t,movie_info mi,movie_companies mc,movie_info_idx mi_idx WHERE t.id=mi.movie_id AND t.id=mc.movie_id AND t.id=mi_idx.movie_id AND t.kind_id=1 AND mc.company_type_id=2 AND mi_idx.info_type_id=101 AND mi.info_type_id=16;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE) SELECT * FROM title t,movie_info mi,movie_info_idx mi_idx,movie_keyword mk WHERE t.id=mi.movie_id AND t.id=mk.movie_id AND t.id=mi_idx.movie_id AND t.production_year>2010 AND t.kind_id=1 AND mi.info_type_id=8 AND mi_idx.info_type_id=101;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE) SELECT * FROM title t,movie_info mi,movie_info_idx mi_idx,movie_keyword mk WHERE t.id=mi.movie_id AND t.id=mk.movie_id AND t.id=mi_idx.movie_id AND t.kind_id=1 AND mi.info_type_id=8 AND mi_idx.info_type_id=101;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE) SELECT * FROM title t,movie_info mi,movie_info_idx mi_idx,movie_keyword mk WHERE t.id=mi.movie_id AND t.id=mk.movie_id AND t.id=mi_idx.movie_id AND t.production_year>2005 AND mi.info_type_id=8 AND mi_idx.info_type_id=101;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE) SELECT * FROM title t,movie_info mi,movie_companies mc,movie_keyword mk WHERE t.id=mi.movie_id AND t.id=mk.movie_id AND t.id=mc.movie_id AND mi.info_type_id=16 AND t.production_year>2000;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE) SELECT * FROM title t,movie_info mi,movie_companies mc,movie_keyword mk WHERE t.id=mi.movie_id AND t.id=mk.movie_id AND t.id=mc.movie_id AND mi.info_type_id=16 AND t.production_year>2005 AND t.production_year<2010;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE) SELECT * FROM title t,movie_info mi,movie_companies mc,movie_keyword mk WHERE t.id=mi.movie_id AND t.id=mk.movie_id AND t.id=mc.movie_id AND mi.info_type_id=16 AND t.production_year>1990;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE) SELECT * FROM cast_info ci,title t,movie_keyword mk,movie_companies mc WHERE t.id=ci.movie_id AND t.id=mk.movie_id AND t.id=mc.movie_id AND mk.keyword_id=117;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE) SELECT * FROM title t,movie_info mi,movie_info_idx mi_idx,cast_info ci WHERE t.id=mi.movie_id AND t.id=mi_idx.movie_id AND t.id=ci.movie_id AND mi.info_type_id=105 AND mi_idx.info_type_id=100;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE) SELECT * FROM title t,movie_info mi,movie_info_idx mi_idx,cast_info ci WHERE t.id=mi.movie_id AND t.id=mi_idx.movie_id AND t.id=ci.movie_id AND mi.info_type_id=3 AND mi_idx.info_type_id=101 AND t.production_year>2008 AND t.production_year<2014;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE) SELECT * FROM title t,movie_info mi,movie_info_idx mi_idx,cast_info ci WHERE t.id=mi.movie_id AND t.id=mi_idx.movie_id AND t.id=ci.movie_id AND mi.info_type_id=3 AND mi_idx.info_type_id=100;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE) SELECT * FROM title t,movie_info mi,movie_companies mc,cast_info ci WHERE t.id=mi.movie_id AND t.id=mc.movie_id AND t.id=ci.movie_id AND ci.role_id=2 AND mi.info_type_id=16 AND t.production_year>2005 AND t.production_year<2009;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE) SELECT * FROM title t,movie_info mi,movie_companies mc,cast_info ci WHERE t.id=mi.movie_id AND t.id=mc.movie_id AND t.id=ci.movie_id AND ci.role_id=2 AND mi.info_type_id=16;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE) SELECT * FROM title t,movie_info mi,movie_companies mc,cast_info ci WHERE t.id=mi.movie_id AND t.id=mc.movie_id AND t.id=ci.movie_id AND ci.role_id=2 AND mi.info_type_id=16 AND t.production_year>2000;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE) SELECT * FROM title t,cast_info ci,movie_keyword mk WHERE t.id=mk.movie_id AND t.id=ci.movie_id AND t.production_year>1950 AND t.kind_id=1;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE) SELECT * FROM title t,cast_info ci,movie_keyword mk WHERE t.id=mk.movie_id AND t.id=ci.movie_id AND t.production_year>2000 AND t.kind_id=1;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE) SELECT * FROM title t,movie_keyword mk,movie_companies mc,movie_info mi WHERE t.id=mk.movie_id AND t.id=mc.movie_id AND t.id=mi.movie_id AND mk.keyword_id=398 AND mc.company_type_id=2 AND t.production_year>1950 AND t.production_year<2000;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE) SELECT * FROM title t,movie_keyword mk,movie_companies mc,movie_info mi WHERE t.id=mk.movie_id AND t.id=mc.movie_id AND t.id=mi.movie_id AND mk.keyword_id=398 AND mc.company_type_id=2 AND t.production_year>2000 AND t.production_year<2010;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE) SELECT * FROM title t,movie_keyword mk,movie_companies mc,movie_info mi WHERE t.id=mk.movie_id AND t.id=mc.movie_id AND t.id=mi.movie_id AND mk.keyword_id=398 AND mc.company_type_id=2 AND t.production_year>1950 AND t.production_year<2010;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE) SELECT * FROM title t,movie_info mi,movie_info_idx mi_idx,movie_keyword mk,movie_companies mc WHERE t.id=mi.movie_id AND t.id=mk.movie_id AND t.id=mi_idx.movie_id AND t.id=mc.movie_id AND t.production_year>2008 AND mi.info_type_id=8 AND mi_idx.info_type_id=101;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE) SELECT * FROM title t,movie_info mi,movie_info_idx mi_idx,movie_keyword mk,movie_companies mc WHERE t.id=mi.movie_id AND t.id=mk.movie_id AND t.id=mi_idx.movie_id AND t.id=mc.movie_id AND t.production_year>2009 AND mi.info_type_id=8 AND mi_idx.info_type_id=101;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE) SELECT * FROM title t,movie_info mi,movie_companies mc,cast_info ci,movie_keyword mk WHERE t.id=mi.movie_id AND t.id=mc.movie_id AND t.id=ci.movie_id AND t.id=mk.movie_id AND ci.role_id=2 AND mi.info_type_id=16 AND t.production_year>2010;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE) SELECT * FROM title t,movie_info mi,movie_companies mc,cast_info ci,movie_keyword mk WHERE t.id=mi.movie_id AND t.id=mc.movie_id AND t.id=ci.movie_id AND t.id=mk.movie_id AND ci.role_id=2 AND mi.info_type_id=16 AND t.production_year>2010 AND mc.company_id=22956;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE) SELECT * FROM title t,movie_info mi,movie_companies mc,cast_info ci,movie_keyword mk WHERE t.id=mi.movie_id AND t.id=mc.movie_id AND t.id=ci.movie_id AND t.id=mk.movie_id AND ci.role_id=2 AND mi.info_type_id=16 AND t.production_year>2000;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE) SELECT * FROM title t,movie_info mi,movie_info_idx mi_idx,cast_info ci,movie_keyword mk WHERE t.id=mi.movie_id AND t.id=mi_idx.movie_id AND t.id=ci.movie_id AND t.id=mk.movie_id AND mi.info_type_id=3 AND mi_idx.info_type_id=100;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE) SELECT * FROM title t,movie_info mi,movie_info_idx mi_idx,cast_info ci,movie_keyword mk WHERE t.id=mi.movie_id AND t.id=mi_idx.movie_id AND t.id=ci.movie_id AND t.id=mk.movie_id AND mi.info_type_id=3 AND mi_idx.info_type_id=100 AND t.production_year>2010;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE) SELECT * FROM title t,cast_info ci,movie_keyword mk,movie_info_idx mi_idx WHERE t.id=mk.movie_id AND t.id=ci.movie_id AND t.id=mi_idx.movie_id AND t.production_year>2000 AND t.kind_id=1 AND mi_idx.info_type_id=101;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE) SELECT * FROM title t,cast_info ci,movie_keyword mk,movie_info_idx mi_idx WHERE t.id=mk.movie_id AND t.id=ci.movie_id AND t.id=mi_idx.movie_id AND t.production_year>2005 AND t.kind_id=1 AND mi_idx.info_type_id=101;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE) SELECT * FROM title t,movie_keyword mk,movie_companies mc,movie_info mi WHERE t.id=mk.movie_id AND t.id=mc.movie_id AND t.id=mi.movie_id AND mk.keyword_id=398 AND mc.company_type_id=2 AND t.production_year=1998;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE) SELECT * FROM title t,movie_info mi,movie_info_idx mi_idx,movie_keyword mk,movie_companies mc WHERE t.id=mi.movie_id AND t.id=mk.movie_id AND t.id=mi_idx.movie_id AND t.id=mc.movie_id AND t.production_year>2000 AND mi.info_type_id=8 AND mi_idx.info_type_id=101;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE) SELECT * FROM title t,movie_info mi,movie_info_idx mi_idx,movie_keyword mk,movie_companies mc WHERE t.id=mi.movie_id AND t.id=mk.movie_id AND t.id=mi_idx.movie_id AND t.id=mc.movie_id AND t.production_year>2005 AND mi.info_type_id=8 AND mi_idx.info_type_id=101;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE) SELECT * FROM title t,movie_info mi,movie_companies mc,cast_info ci,movie_keyword mk WHERE t.id=mi.movie_id AND t.id=mc.movie_id AND t.id=ci.movie_id AND t.id=mk.movie_id AND ci.role_id=2 AND mi.info_type_id=16 AND t.production_year>2000 AND t.production_year<2010 AND mk.keyword_id=7084;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE) SELECT * FROM title t,movie_info mi,movie_companies mc,cast_info ci,movie_keyword mk WHERE t.id=mi.movie_id AND t.id=mc.movie_id AND t.id=ci.movie_id AND t.id=mk.movie_id AND ci.role_id=2 AND mi.info_type_id=16 AND t.production_year>2000 AND t.production_year<2005 AND mk.keyword_id=7084;
EXPLAIN (FORMAT JSON, ANALYZE, VERBOSE) SELECT * FROM title t,movie_info mi,movie_info_idx mi_idx,cast_info ci,movie_keyword mk WHERE t.id=mi.movie_id AND t.id=mi_idx.movie_id AND t.id=ci.movie_id AND t.id=mk.movie_id AND mi.info_type_id=3 AND mi_idx.info_type_id=100 AND t.production_year>2000;

"""
Cross-workload PRICE alias configuration.

Maps all 20 deepdb_augmented database names to {table_name: price_alias} dicts.
Aliases are globally unique across all databases (different prefix per DB).

For imdb and tpc_h, aliases match the existing PRICE statistics.
"""

import json
import os

DEEPDB_BASE = "/root/LLM4QPR/deepdb_augmented"

# ---------------------------------------------------------------------------
# Static alias definitions
# ---------------------------------------------------------------------------

# IMDB: match existing PRICE aliases exactly
IMDB_ABBREV = {
    "aka_name": "imdb_an",
    "aka_title": "imdb_at",
    "cast_info": "imdb_ci",
    "char_name": "imdb_chn",
    "comp_cast_type": "imdb_cct",
    "company_name": "imdb_cpn",
    "company_type": "imdb_ct",
    "complete_cast": "imdb_cc",
    "info_type": "imdb_it",
    "keyword": "imdb_kw",
    "kind_type": "imdb_kt",
    "link_type": "imdb_lt",
    "movie_companies": "imdb_mc",
    "movie_info": "imdb_mi",
    "movie_info_idx": "imdb_mii",
    "movie_keyword": "imdb_mk",
    "movie_link": "imdb_ml",
    "name": "imdb_n",
    "person_info": "imdb_pi",
    "role_type": "imdb_rt",
    "title": "imdb_t",
}

# TPC-H: match existing PRICE aliases exactly
TPCH_ABBREV = {
    "customer": "tpch_c",
    "orders": "tpch_o",
    "lineitem": "tpch_l",
    "part": "tpch_p",
    "partsupp": "tpch_ps",
    "supplier": "tpch_s",
    "nation": "tpch_n",
    "region": "tpch_r",
}

# Stats: match existing PRICE aliases exactly
STATS_ABBREV = {
    "badges": "st_b",
    "comments": "st_c",
    "posthistory": "st_ph",
    "postlinks": "st_pl",
    "posts": "st_p",
    "tags": "st_t",
    "users": "st_u",
    "votes": "st_v",
}

# Accidents
ACCIDENTS_ABBREV = {
    "nesreca": "acc_nes",
    "oseba": "acc_ose",
    "upravna_enota": "acc_ue",
}

# Airline
AIRLINE_ABBREV = {
    "On_Time_On_Time_Performance_2016_1": "air_ot",
    "L_AIRLINE_ID": "air_lai",
    "L_AIRPORT": "air_la",
    "L_AIRPORT_ID": "air_laid",
    "L_AIRPORT_SEQ_ID": "air_lasid",
    "L_CANCELLATION": "air_lcan",
    "L_CITY_MARKET_ID": "air_lcmi",
    "L_DEPARRBLK": "air_ldab",
    "L_DISTANCE_GROUP_250": "air_ldg",
    "L_DIVERSIONS": "air_ldiv",
    "L_MONTHS": "air_lm",
    "L_ONTIME_DELAY_GROUPS": "air_lodg",
    "L_QUARTERS": "air_lq",
    "L_STATE_ABR_AVIATION": "air_lsaa",
    "L_STATE_FIPS": "air_lsf",
    "L_UNIQUE_CARRIERS": "air_luc",
    "L_WEEKDAYS": "air_lwd",
    "L_WORLD_AREA_CODES": "air_lwac",
    "L_YESNO_RESP": "air_lyn",
}

# Baseball
BASEBALL_ABBREV = {
    "allstarfull": "bb_asf",
    "appearances": "bb_app",
    "awardsmanagers": "bb_awm",
    "awardsplayers": "bb_awp",
    "awardssharemanagers": "bb_awsm",
    "awardsshareplayers": "bb_awsp",
    "batting": "bb_bat",
    "battingpost": "bb_batp",
    "els_teamnames": "bb_etn",
    "fielding": "bb_fld",
    "fieldingof": "bb_fldo",
    "fieldingpost": "bb_fldp",
    "halloffame": "bb_hof",
    "managers": "bb_mgr",
    "managershalf": "bb_mgrh",
    "pitching": "bb_pit",
    "pitchingpost": "bb_pitp",
    "players": "bb_ply",
    "salaries": "bb_sal",
    "schools": "bb_sch",
    "schoolsplayers": "bb_schp",
    "seriespost": "bb_sp",
    "teams": "bb_tm",
    "teamsfranchises": "bb_tmf",
    "teamshalf": "bb_tmh",
}

# Basketball
BASKETBALL_ABBREV = {
    "awards_coaches": "bk_awc",
    "awards_players": "bk_awp",
    "coaches": "bk_co",
    "draft": "bk_dr",
    "player_allstar": "bk_pas",
    "players": "bk_ply",
    "players_teams": "bk_pt",
    "series_post": "bk_sp",
    "teams": "bk_tm",
}

# Carcinogenesis
CARCINOGENESIS_ABBREV = {
    "atom": "car_a",
    "canc": "car_c",
    "sbond_1": "car_sb1",
    "sbond_2": "car_sb2",
    "sbond_3": "car_sb3",
    "sbond_7": "car_sb7",
}

# Consumer
CONSUMER_ABBREV = {
    "EXPENDITURES": "con_exp",
    "HOUSEHOLDS": "con_hh",
    "HOUSEHOLD_MEMBERS": "con_hhm",
}

# Credit
CREDIT_ABBREV = {
    "category": "cr_cat",
    "charge": "cr_chg",
    "corporation": "cr_corp",
    "member": "cr_mem",
    "payment": "cr_pay",
    "provider": "cr_prv",
    "region": "cr_reg",
    "statement": "cr_stm",
}

# Employee
EMPLOYEE_ABBREV = {
    "departments": "emp_dep",
    "dept_emp": "emp_de",
    "dept_manager": "emp_dm",
    "employees": "emp_e",
    "salaries": "emp_sal",
    "titles": "emp_ttl",
}

# FHNK
FHNK_ABBREV = {
    "pripady": "fh_pri",
    "vykony": "fh_vyk",
    "zup": "fh_zup",
}

# Financial
FINANCIAL_ABBREV = {
    "account": "fin_a",
    "card": "fin_cd",
    "client": "fin_cl",
    "disp": "fin_d",
    "district": "fin_dt",
    "loan": "fin_l",
    "order": "fin_o",
    "trans": "fin_t",
}

# Geneea
GENEEA_ABBREV = {
    "bod_schuze": "gen_bs",
    "bod_stav": "gen_bst",
    "funkce": "gen_fun",
    "hl_check": "gen_hch",
    "hl_hlasovani": "gen_hhl",
    "hl_poslanec": "gen_hpo",
    "hl_vazby": "gen_hva",
    "hl_zposlanec": "gen_hzp",
    "omluvy": "gen_oml",
    "organy": "gen_org",
    "osoby": "gen_oso",
    "pkgps": "gen_pkg",
    "poslanec": "gen_pos",
    "schuze": "gen_sch",
    "schuze_stav": "gen_sst",
    "typ_funkce": "gen_tf",
    "typ_organu": "gen_to",
    "zarazeni": "gen_zar",
    "zmatecne": "gen_zma",
}

# Genome
GENOME_ABBREV = {
    "ATT_CLASSES": "gno_ac",
    "IMG_OBJ": "gno_io",
    "IMG_OBJ_ATT": "gno_ioa",
    "IMG_REL": "gno_ir",
    "OBJ_CLASSES": "gno_oc",
    "PRED_CLASSES": "gno_pc",
}

# Hepatitis
HEPATITIS_ABBREV = {
    "Bio": "hep_bio",
    "dispat": "hep_dis",
    "indis": "hep_ind",
    "inf": "hep_inf",
    "rel11": "hep_r11",
    "rel12": "hep_r12",
    "rel13": "hep_r13",
}

# Movielens
MOVIELENS_ABBREV = {
    "actors": "ml_act",
    "directors": "ml_dir",
    "movies": "ml_mov",
    "movies2actors": "ml_m2a",
    "movies2directors": "ml_m2d",
    "u2base": "ml_u2b",
    "users": "ml_usr",
}

# Seznam
SEZNAM_ABBREV = {
    "client": "sz_cl",
    "dobito": "sz_dob",
    "probehnuto": "sz_pro",
    "probehnuto_mimo_penezenku": "sz_pmp",
}

# SSB
SSB_ABBREV = {
    "customer": "ssb_c",
    "lineorder": "ssb_lo",
    "part": "ssb_p",
    "supplier": "ssb_s",
}

# Tournament
TOURNAMENT_ABBREV = {
    "regular_season_compact_results": "tn_rscr",
    "regular_season_detailed_results": "tn_rsdr",
    "seasons": "tn_sea",
    "target": "tn_tgt",
    "teams": "tn_tm",
    "tourney_compact_results": "tn_tcr",
    "tourney_detailed_results": "tn_tdr",
    "tourney_seeds": "tn_tsd",
    "tourney_slots": "tn_tsl",
}

# Walmart
WALMART_ABBREV = {
    "key": "wm_k",
    "station": "wm_sta",
    "train": "wm_tr",
}

# ---------------------------------------------------------------------------
# Master mapping: db_name -> abbrev dict
# ---------------------------------------------------------------------------
CROSS_WORKLOAD_ABBREV = {
    "accidents": ACCIDENTS_ABBREV,
    "airline": AIRLINE_ABBREV,
    "baseball": BASEBALL_ABBREV,
    "basketball": BASKETBALL_ABBREV,
    "carcinogenesis": CARCINOGENESIS_ABBREV,
    "consumer": CONSUMER_ABBREV,
    "credit": CREDIT_ABBREV,
    "employee": EMPLOYEE_ABBREV,
    "fhnk": FHNK_ABBREV,
    "financial": FINANCIAL_ABBREV,
    "geneea": GENEEA_ABBREV,
    "genome": GENOME_ABBREV,
    "hepatitis": HEPATITIS_ABBREV,
    "imdb": IMDB_ABBREV,
    "movielens": MOVIELENS_ABBREV,
    "seznam": SEZNAM_ABBREV,
    "ssb": SSB_ABBREV,
    "tournament": TOURNAMENT_ABBREV,
    "tpc_h": TPCH_ABBREV,
    "walmart": WALMART_ABBREV,
}

# All 20 cross-workload database names
ALL_CROSS_WORKLOAD_DBS = sorted(CROSS_WORKLOAD_ABBREV.keys())


def get_abbrev_for_db(db_name):
    """Get the PRICE alias mapping for a cross-workload database."""
    if db_name not in CROSS_WORKLOAD_ABBREV:
        raise ValueError(f"Unknown cross-workload database: {db_name}")
    return CROSS_WORKLOAD_ABBREV[db_name]


def get_reverse_abbrev(db_name):
    """Get reverse mapping: price_alias -> table_name."""
    abbrev = get_abbrev_for_db(db_name)
    return {v: k for k, v in abbrev.items()}


def discover_used_tables_from_json(json_path):
    """Discover which tables are actually referenced in plan trees.

    Returns sorted list of table names that appear as scan nodes.
    """
    with open(json_path) as f:
        data = json.load(f)

    table_stats = data["database_stats"]["table_stats"]
    plans = data["parsed_plans"]

    used_indices = set()

    def traverse(node):
        pp = node.get("plan_parameters", {})
        if pp.get("table") is not None:
            used_indices.add(pp["table"])
        for child in node.get("children", []):
            traverse(child)

    for plan in plans:
        traverse(plan)

    return sorted(set(
        table_stats[i]["relname"]
        for i in used_indices
        if i < len(table_stats)
    ))


def get_json_paths_for_db(db_name):
    """Get all non-index JSON file paths for a database."""
    db_dir = os.path.join(DEEPDB_BASE, db_name)
    if not os.path.isdir(db_dir):
        raise FileNotFoundError(f"Database directory not found: {db_dir}")
    paths = []
    for f in sorted(os.listdir(db_dir)):
        if f.endswith(".json") and not f.startswith("index_"):
            paths.append(os.path.join(db_dir, f))
    return paths


def verify_aliases():
    """Verify all aliases are globally unique across databases."""
    all_aliases = {}
    for db_name, abbrev in CROSS_WORKLOAD_ABBREV.items():
        for table, alias in abbrev.items():
            if alias in all_aliases:
                prev_db, prev_table = all_aliases[alias]
                print(f"CONFLICT: alias '{alias}' used by "
                      f"{prev_db}.{prev_table} and {db_name}.{table}")
            all_aliases[alias] = (db_name, table)
    print(f"Total aliases: {len(all_aliases)}, all unique: "
          f"{len(all_aliases) == sum(len(a) for a in CROSS_WORKLOAD_ABBREV.values())}")


if __name__ == "__main__":
    verify_aliases()
    print()
    for db_name in ALL_CROSS_WORKLOAD_DBS:
        abbrev = CROSS_WORKLOAD_ABBREV[db_name]
        print(f"{db_name}: {len(abbrev)} tables")
        for table, alias in sorted(abbrev.items()):
            print(f"  {table} -> {alias}")

# Registry of data functions for table generation
# Each function takes (loader, start_date, end_date, params) and returns {"headers": [...], "rows": [[...]]}
#
# Design: All functions in a single build cycle share a cached load via _get_data().
# Call clear_cache() before each build cycle (email render, preview, etc.)
# This avoids redundant loader calls when multiple tables use the same dataset.
#
# Date formats (always YYYY-MM-DD):
#   daily_pnl:   start_date == end_date == selected date
#   monthly_paa: start_date = first weekday of month, end_date = last weekday of month
#   weekly_paa:  start_date = Monday, end_date = Friday

_data_cache = {}


def clear_cache():
    """Clear the per-build data cache. Call before each render cycle."""
    _data_cache.clear()


def _get_data(loader, start_date, end_date, report_type):
    """Load data once per (start_date, end_date, report_type) and cache for the build cycle."""
    key = (start_date, end_date, report_type)
    if key not in _data_cache:
        _data_cache[key] = loader.load_dna_data(start_date, end_date, report_type)
    return _data_cache[key]


# --- Daily PnL functions ---

def get_systematic_cash_trading_pnl(loader, start_date, end_date, params):
    data = _get_data(loader, start_date, end_date, params.get("report_type", "daily_pnl"))
    return data.get("systematic_cash_trading_pnl", {"headers": [], "rows": []})


def get_portfolio_metrics(loader, start_date, end_date, params):
    data = _get_data(loader, start_date, end_date, params.get("report_type", "daily_pnl"))
    return data.get("portfolio_metrics", {"headers": [], "rows": []})


def get_paa_by_region(loader, start_date, end_date, params):
    data = _get_data(loader, start_date, end_date, params.get("report_type", "daily_pnl"))
    return data.get("paa_by_region", {"headers": [], "rows": []})


def get_book_flow(loader, start_date, end_date, params):
    book = params.get("book", "apcr").lower()
    data = _get_data(loader, start_date, end_date, params.get("report_type", "daily_pnl"))
    return data.get(f"{book}_flow", {"headers": [], "rows": []})


def get_book_factor_risk(loader, start_date, end_date, params):
    book = params.get("book", "apcr").lower()
    data = _get_data(loader, start_date, end_date, params.get("report_type", "daily_pnl"))
    return data.get(f"{book}_factor_risk", {"headers": [], "rows": []})


def get_book_spec_risk(loader, start_date, end_date, params):
    book = params.get("book", "apcr").lower()
    data = _get_data(loader, start_date, end_date, params.get("report_type", "daily_pnl"))
    return data.get(f"{book}_spec_risk", {"headers": [], "rows": []})


def get_book_net_platform_value(loader, start_date, end_date, params):
    book = params.get("book", "apcr").lower()
    data = _get_data(loader, start_date, end_date, params.get("report_type", "daily_pnl"))
    return data.get(f"{book}_net_platform_value", {"headers": [], "rows": []})


def get_cr_paa_by_strategy(loader, start_date, end_date, params):
    data = _get_data(loader, start_date, end_date, params.get("report_type", "daily_pnl"))
    return data.get("cr_paa_by_strategy", {"headers": [], "rows": []})


def get_cr_flow_paa_by_source_desk(loader, start_date, end_date, params):
    data = _get_data(loader, start_date, end_date, params.get("report_type", "daily_pnl"))
    return data.get("cr_flow_paa_by_source_desk", {"headers": [], "rows": []})


def get_sl_top10_pnl_positions(loader, start_date, end_date, params):
    data = _get_data(loader, start_date, end_date, params.get("report_type", "daily_pnl"))
    return data.get("sl_top10_pnl_positions", {"headers": [], "rows": []})


# --- Monthly/Weekly PAA functions ---
# These work for both monthly_paa and weekly_paa.
# The report_type param determines which dataset to load.

def get_book_pcg_pnl(loader, start_date, end_date, params):
    book = params.get("book", "apcr").lower()
    report_type = params.get("report_type", "monthly_paa")
    data = _get_data(loader, start_date, end_date, report_type)
    return data.get(f"{book}_pcg_pnl", {"headers": [], "rows": []})


def get_book_attribution_by_node(loader, start_date, end_date, params):
    book = params.get("book", "apcr").lower()
    report_type = params.get("report_type", "monthly_paa")
    data = _get_data(loader, start_date, end_date, report_type)
    return data.get(f"{book}_attribution_by_node", {"headers": [], "rows": []})


def get_book_main_attribution(loader, start_date, end_date, params):
    book = params.get("book", "apcr").lower()
    report_type = params.get("report_type", "monthly_paa")
    data = _get_data(loader, start_date, end_date, report_type)
    return data.get(f"{book}_main_attribution", {"headers": [], "rows": []})


def get_book_inventory_attribution(loader, start_date, end_date, params):
    book = params.get("book", "apcr").lower()
    report_type = params.get("report_type", "monthly_paa")
    data = _get_data(loader, start_date, end_date, report_type)
    return data.get(f"{book}_inventory_attribution", {"headers": [], "rows": []})


def get_book_platform_contribution(loader, start_date, end_date, params):
    book = params.get("book", "apcr").lower()
    report_type = params.get("report_type", "monthly_paa")
    data = _get_data(loader, start_date, end_date, report_type)
    return data.get(f"{book}_platform_contribution", {"headers": [], "rows": []})


def get_book_risk(loader, start_date, end_date, params):
    book = params.get("book", "apcr").lower()
    report_type = params.get("report_type", "monthly_paa")
    data = _get_data(loader, start_date, end_date, report_type)
    return data.get(f"{book}_risk", {"headers": [], "rows": []})


def get_market(loader, start_date, end_date, params):
    report_type = params.get("report_type", "monthly_paa")
    data = _get_data(loader, start_date, end_date, report_type)
    return data.get("market", {"headers": [], "rows": []})


def get_index_inventory(loader, start_date, end_date, params):
    report_type = params.get("report_type", "monthly_paa")
    data = _get_data(loader, start_date, end_date, report_type)
    return data.get("index_inventory", {"headers": [], "rows": []})


# Function registry — layout config references these by name
DATA_FUNCTIONS = {
    "get_systematic_cash_trading_pnl": get_systematic_cash_trading_pnl,
    "get_portfolio_metrics": get_portfolio_metrics,
    "get_paa_by_region": get_paa_by_region,
    "get_book_flow": get_book_flow,
    "get_book_factor_risk": get_book_factor_risk,
    "get_book_spec_risk": get_book_spec_risk,
    "get_book_net_platform_value": get_book_net_platform_value,
    "get_cr_paa_by_strategy": get_cr_paa_by_strategy,
    "get_cr_flow_paa_by_source_desk": get_cr_flow_paa_by_source_desk,
    "get_sl_top10_pnl_positions": get_sl_top10_pnl_positions,
    "get_book_pcg_pnl": get_book_pcg_pnl,
    "get_book_attribution_by_node": get_book_attribution_by_node,
    "get_book_main_attribution": get_book_main_attribution,
    "get_book_inventory_attribution": get_book_inventory_attribution,
    "get_book_platform_contribution": get_book_platform_contribution,
    "get_book_risk": get_book_risk,
    "get_market": get_market,
    "get_index_inventory": get_index_inventory,
}

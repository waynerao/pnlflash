# Registry of data functions for table generation
# Each function takes (loader, report_date, params) and returns {"headers": [...], "rows": [[...]]}
# To add a new table type, add a function here and register it in DATA_FUNCTIONS


def transpose_table(table_data):
    # Transpose: first column of each row becomes a header, first header is top-left label
    headers = table_data["headers"]
    rows = table_data["rows"]
    if not rows:
        return table_data
    # New headers: first header (label) + first col of each row
    new_headers = [headers[0]] + [row[0] for row in rows]
    # New rows: one per original data column
    new_rows = []
    for ci in range(1, len(headers)):
        new_row = [headers[ci]] + [row[ci] if ci < len(row) else "" for row in rows]
        new_rows.append(new_row)
    return {"headers": new_headers, "rows": new_rows}


def get_systematic_cash_trading_pnl(loader, report_date, params):
    data = loader.load_dna_data(report_date, params.get("report_type", "daily_pnl"))
    return data.get("systematic_cash_trading_pnl", {"headers": [], "rows": []})


def get_portfolio_metrics(loader, report_date, params):
    data = loader.load_dna_data(report_date, params.get("report_type", "daily_pnl"))
    return data.get("portfolio_metrics", {"headers": [], "rows": []})


def get_paa_by_region(loader, report_date, params):
    data = loader.load_dna_data(report_date, params.get("report_type", "daily_pnl"))
    return data.get("paa_by_region", {"headers": [], "rows": []})


def get_book_flow(loader, report_date, params):
    book = params.get("book", "apcr").lower()
    data = loader.load_dna_data(report_date, params.get("report_type", "daily_pnl"))
    return data.get(f"{book}_flow", {"headers": [], "rows": []})


def get_book_factor_risk(loader, report_date, params):
    book = params.get("book", "apcr").lower()
    data = loader.load_dna_data(report_date, params.get("report_type", "daily_pnl"))
    return data.get(f"{book}_factor_risk", {"headers": [], "rows": []})


def get_book_spec_risk(loader, report_date, params):
    book = params.get("book", "apcr").lower()
    data = loader.load_dna_data(report_date, params.get("report_type", "daily_pnl"))
    return data.get(f"{book}_spec_risk", {"headers": [], "rows": []})


def get_book_net_platform_value(loader, report_date, params):
    book = params.get("book", "apcr").lower()
    data = loader.load_dna_data(report_date, params.get("report_type", "daily_pnl"))
    return data.get(f"{book}_net_platform_value", {"headers": [], "rows": []})


def get_cr_paa_by_strategy(loader, report_date, params):
    data = loader.load_dna_data(report_date, params.get("report_type", "daily_pnl"))
    return data.get("cr_paa_by_strategy", {"headers": [], "rows": []})


def get_cr_flow_paa_by_source_desk(loader, report_date, params):
    data = loader.load_dna_data(report_date, params.get("report_type", "daily_pnl"))
    return data.get("cr_flow_paa_by_source_desk", {"headers": [], "rows": []})


def get_sl_top10_pnl_positions(loader, report_date, params):
    data = loader.load_dna_data(report_date, params.get("report_type", "daily_pnl"))
    return data.get("sl_top10_pnl_positions", {"headers": [], "rows": []})


# Monthly/Weekly PAA functions
def get_book_pcg_pnl(loader, report_date, params):
    book = params.get("book", "apcr").lower()
    report_type = params.get("report_type", "monthly_paa")
    data = loader.load_dna_data(report_date, report_type)
    return data.get(f"{book}_pcg_pnl", {"headers": [], "rows": []})


def get_book_attribution_by_node(loader, report_date, params):
    book = params.get("book", "apcr").lower()
    report_type = params.get("report_type", "monthly_paa")
    data = loader.load_dna_data(report_date, report_type)
    return data.get(f"{book}_attribution_by_node", {"headers": [], "rows": []})


def get_book_main_attribution(loader, report_date, params):
    book = params.get("book", "apcr").lower()
    report_type = params.get("report_type", "monthly_paa")
    data = loader.load_dna_data(report_date, report_type)
    return data.get(f"{book}_main_attribution", {"headers": [], "rows": []})


def get_book_inventory_attribution(loader, report_date, params):
    book = params.get("book", "apcr").lower()
    report_type = params.get("report_type", "monthly_paa")
    data = loader.load_dna_data(report_date, report_type)
    return data.get(f"{book}_inventory_attribution", {"headers": [], "rows": []})


def get_book_platform_contribution(loader, report_date, params):
    book = params.get("book", "apcr").lower()
    report_type = params.get("report_type", "monthly_paa")
    data = loader.load_dna_data(report_date, report_type)
    return data.get(f"{book}_platform_contribution", {"headers": [], "rows": []})


def get_book_risk(loader, report_date, params):
    book = params.get("book", "apcr").lower()
    report_type = params.get("report_type", "monthly_paa")
    data = loader.load_dna_data(report_date, report_type)
    return data.get(f"{book}_risk", {"headers": [], "rows": []})


def get_market(loader, report_date, params):
    report_type = params.get("report_type", "monthly_paa")
    data = loader.load_dna_data(report_date, report_type)
    return data.get("market", {"headers": [], "rows": []})


def get_index_inventory(loader, report_date, params):
    report_type = params.get("report_type", "monthly_paa")
    data = loader.load_dna_data(report_date, report_type)
    return data.get("index_inventory", {"headers": [], "rows": []})


# Function registry — setup page references these by name
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

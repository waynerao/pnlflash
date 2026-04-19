# Registry of data functions for table generation
# Each function takes (data_store, params) and returns {"headers": [...], "rows": [[...]]}
#
# DataStore holds raw DataFrames loaded by the loader.
# These functions filter, transform, and convert DataFrames into
# the headers/rows format for rendering.

import pandas as pd

EMPTY = {"headers": [], "rows": []}


def _df_to_table(df, headers=None):
    """Convert a DataFrame to {headers, rows} dict."""
    if df is None or df.empty:
        return {"headers": [], "rows": []}
    h = headers if headers else list(df.columns)
    return {"headers": h, "rows": df.values.tolist()}


def _with_total(df, label_col, sum_cols):
    """Append a Total row summing specified columns."""
    totals = {label_col: "Total"}
    for c in sum_cols:
        totals[c] = df[c].sum()
    return pd.concat([df, pd.DataFrame([totals])], ignore_index=True)


# --- Daily PnL functions ---

def get_systematic_cash_trading_pnl(data_store, params):
    data = data_store.get_dna_data(params.get("report_type", "daily_pnl"))
    pnl = data.get("pnl")
    if pnl is None:
        return EMPTY
    out = pnl[["label", "td", "mtd", "ytd"]].copy()
    out = _with_total(out, "label", ["td", "mtd", "ytd"])
    return _df_to_table(out, ["", "TD", "MTD", "YTD"])


def get_portfolio_metrics(data_store, params):
    data = data_store.get_dna_data(params.get("report_type", "daily_pnl"))
    df = data.get("portfolio_metrics")
    if df is None:
        return EMPTY
    out = df[["book", "delta", "gross", "long", "short", "total_risk", "factor_risk", "spec_risk"]].copy()
    out = _with_total(out, "book", ["delta", "gross", "long", "short", "total_risk", "factor_risk", "spec_risk"])
    return _df_to_table(out, ["Book", "Delta", "Gross", "Long", "Short", "Total Risk", "Factor Risk", "Spec Risk"])


def get_paa_by_region(data_store, params):
    data = data_store.get_dna_data(params.get("report_type", "daily_pnl"))
    df = data.get("paa_by_region")
    if df is None:
        return EMPTY
    out = df[["region", "td", "mtd", "ytd"]].copy()
    out = _with_total(out, "region", ["td", "mtd", "ytd"])
    return _df_to_table(out, ["", "TD", "MTD", "YTD"])


def get_book_flow(data_store, params):
    book = params.get("book", "APCR").upper()
    data = data_store.get_dna_data(params.get("report_type", "daily_pnl"))

    if book == "SL":
        df = data.get("sl_flow")
        if df is None:
            return EMPTY
        out = df[["market", "td", "mtd_avg", "ytd_avg"]].copy()
        out = _with_total(out, "market", ["td", "mtd_avg", "ytd_avg"])
        return _df_to_table(out, ["Market", "TD", "MTD Avg", "YTD Avg"])
    else:
        df = data.get("cr_flow")
        if df is None:
            return EMPTY
        book_df = df[df["book"] == book][["item", "td", "mtd_avg", "ytd_avg"]].copy()
        # Format CR Retention as percentage strings (other rows stay numeric for mm format)
        rows = []
        for _, row in book_df.iterrows():
            if row["item"] == "CR Retention":
                rows.append([row["item"], f"{row['td']:.1f}%", f"{row['mtd_avg']:.1f}%", f"{row['ytd_avg']:.1f}%"])
            else:
                rows.append([row["item"], row["td"], row["mtd_avg"], row["ytd_avg"]])
        return {"headers": ["", "TD", "MTD Avg", "YTD Avg"], "rows": rows}


def get_book_factor_risk(data_store, params):
    book = params.get("book", "APCR").upper()
    data = data_store.get_dna_data(params.get("report_type", "daily_pnl"))
    df = data.get("factor_risk")
    if df is None:
        return EMPTY
    book_df = df[df["book"] == book][["factor", "exposure", "pnl"]].copy()
    return _df_to_table(book_df, ["Factor", "Exposure", "PnL"])


def get_book_spec_risk(data_store, params):
    book = params.get("book", "APCR").upper()
    data = data_store.get_dna_data(params.get("report_type", "daily_pnl"))
    df = data.get("spec_risk")
    if df is None:
        return EMPTY
    book_df = df[df["book"] == book][["ticker", "exposure", "pnl"]].copy()
    return _df_to_table(book_df, ["Spec", "Exposure", "PnL"])


def get_book_net_platform_value(data_store, params):
    book = params.get("book", "APCR").upper()
    data = data_store.get_dna_data(params.get("report_type", "daily_pnl"))
    df = data.get("net_platform_value")
    if df is None:
        return EMPTY
    book_df = df[df["book"] == book][["item", "td", "mtd", "ytd"]].copy()
    return _df_to_table(book_df, ["", "TD", "MTD", "YTD"])


def get_cr_paa_by_strategy(data_store, params):
    data = data_store.get_dna_data(params.get("report_type", "daily_pnl"))
    df = data.get("cr_strategy_paa")
    if df is None:
        return EMPTY
    out = df[["region", "pnl", "tracking", "inventory"]].copy()
    out = _with_total(out, "region", ["pnl", "tracking", "inventory"])
    return _df_to_table(out, ["", "PnL", "Tracking", "Inventory"])


def get_cr_flow_paa_by_source_desk(data_store, params):
    data = data_store.get_dna_data(params.get("report_type", "daily_pnl"))
    df = data.get("cr_flow_paa")
    if df is None:
        return EMPTY
    out = df[["source", "desk", "value", "pnl"]].copy()
    return _df_to_table(out, ["Source", "Desk", "Value", "PnL"])


def get_sl_top10_pnl_positions(data_store, params):
    data = data_store.get_dna_data(params.get("report_type", "daily_pnl"))
    df = data.get("sl_top_positions")
    if df is None:
        return EMPTY
    out = df.nlargest(10, "value")[["ticker", "pnl", "shares", "value"]].copy()
    return _df_to_table(out, ["Ticker", "PnL", "Shares", "Value"])


# --- Monthly/Weekly PAA functions ---

def _get_paa_period_headers(data, df_key, first_col_header):
    """Build headers using period labels stored in DataFrame attrs."""
    df = data.get(df_key)
    if df is None:
        return [first_col_header, "", ""]
    period = df.attrs.get("period_label", "")
    ytd = df.attrs.get("ytd_label", "")
    return [first_col_header, period, ytd]


def get_book_pcg_pnl(data_store, params):
    book = params.get("book", "APCR").upper()
    data = data_store.get_dna_data(params.get("report_type", "monthly_paa"))
    df = data.get("pcg_pnl")
    if df is None:
        return EMPTY
    row = df[df["book"] == book]
    if row.empty:
        return EMPTY
    out = row[["book", "period_pnl", "ytd_pnl"]].copy()
    out.iloc[0, 0] = "Total"
    headers = _get_paa_period_headers(data, "pcg_pnl", "PCG PNL")
    return _df_to_table(out, headers)


def get_book_attribution_by_node(data_store, params):
    book = params.get("book", "APCR").upper()
    data = data_store.get_dna_data(params.get("report_type", "monthly_paa"))
    df = data.get("attribution_by_node")
    if df is None:
        return EMPTY
    book_df = df[df["book"] == book][["node", "period_pnl", "ytd_pnl"]].copy()
    headers = _get_paa_period_headers(data, "attribution_by_node", "Attribution by Node")
    return _df_to_table(book_df, headers)


def get_book_main_attribution(data_store, params):
    book = params.get("book", "APCR").upper()
    data = data_store.get_dna_data(params.get("report_type", "monthly_paa"))
    df = data.get("main_attribution")
    if df is None:
        return EMPTY
    book_df = df[df["book"] == book][["strategy", "period_pnl", "ytd_pnl"]].copy()
    table_name = f"{book} Main Attribution"
    headers = _get_paa_period_headers(data, "main_attribution", table_name)
    return _df_to_table(book_df, headers)


def get_book_inventory_attribution(data_store, params):
    book = params.get("book", "APCR").upper()
    data = data_store.get_dna_data(params.get("report_type", "monthly_paa"))
    df = data.get("inventory_attribution")
    if df is None:
        return EMPTY
    book_df = df[df["book"] == book][["index", "period_pnl", "ytd_pnl"]].copy()
    table_name = f"{book} Inventory Attribution"
    headers = _get_paa_period_headers(data, "inventory_attribution", table_name)
    return _df_to_table(book_df, headers)


def get_book_platform_contribution(data_store, params):
    book = params.get("book", "APCR").upper()
    data = data_store.get_dna_data(params.get("report_type", "monthly_paa"))
    df = data.get("platform_contribution")
    if df is None:
        return EMPTY
    book_df = df[df["book"] == book][["item", "period_pnl", "ytd_pnl"]].copy()
    book_df = _with_total(book_df, "item", ["period_pnl", "ytd_pnl"])
    headers = _get_paa_period_headers(data, "platform_contribution", "Platform Contribution")
    return _df_to_table(book_df, headers)


def get_book_risk(data_store, params):
    book = params.get("book", "APCR").upper()
    data = data_store.get_dna_data(params.get("report_type", "monthly_paa"))
    df = data.get("risk")
    if df is None:
        return EMPTY
    book_df = df[df["book"] == book][["book", "gross", "risk"]].copy()
    return _df_to_table(book_df, ["Risk", "Gross", "Risk"])


def get_market(data_store, params):
    data = data_store.get_dna_data(params.get("report_type", "monthly_paa"))
    df = data.get("market")
    if df is None:
        return EMPTY
    out = df[["market", "gross"]].copy()
    out = pd.concat([out, pd.DataFrame([{"market": "Total", "gross": f"{out.shape[0]}mm"}])], ignore_index=True)
    return _df_to_table(out, ["Market", "Gross"])


def get_index_inventory(data_store, params):
    data = data_store.get_dna_data(params.get("report_type", "monthly_paa"))
    df = data.get("index_inventory")
    if df is None:
        return EMPTY
    out = df[["index", "gross"]].copy()
    out = pd.concat([out, pd.DataFrame([{"index": "Total", "gross": f"{out.shape[0]}mm"}])], ignore_index=True)
    return _df_to_table(out, ["Index Inventory", "Gross"])


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

from abc import ABC, abstractmethod

import pandas as pd


class BaseLoader(ABC):

    @abstractmethod
    def load_dna_data(self, start_date, end_date, report_type):
        """Load data for a report type.

        Args:
            start_date: YYYY-MM-DD string (first weekday of period)
            end_date: YYYY-MM-DD string (last weekday of period)
            report_type: "daily_pnl", "monthly_paa", or "weekly_paa"

        Returns dict of DataFrames:

        For daily_pnl:
            "pnl"                 - columns: book, label, td, mtd, ytd
            "portfolio_metrics"   - columns: book, delta, gross, long, short, total_risk, factor_risk, spec_risk
            "paa_by_region"       - columns: region, td, mtd, ytd
            "cr_flow"             - columns: book, item, td, mtd_avg, ytd_avg  (APCR/JPCR: Gross Flow, Gross Trade-out, CR Retention)
            "sl_flow"             - columns: market, td, mtd_avg, ytd_avg
            "factor_risk"         - columns: book, factor, exposure, pnl
            "spec_risk"           - columns: book, ticker, exposure, pnl
            "net_platform_value"  - columns: book, item, td, mtd, ytd
            "cr_strategy_paa"     - columns: region, pnl, tracking, inventory
            "cr_flow_paa"         - columns: source, desk, value, pnl
            "sl_top_positions"    - columns: ticker, pnl, shares, value

        For monthly_paa / weekly_paa:
            "pcg_pnl"               - columns: book, period_pnl, ytd_pnl
            "attribution_by_node"   - columns: book, node, period_pnl, ytd_pnl
            "main_attribution"      - columns: book, strategy, period_pnl, ytd_pnl
            "inventory_attribution" - columns: book, index, period_pnl, ytd_pnl
            "platform_contribution" - columns: book, item, period_pnl, ytd_pnl
            "risk"                  - columns: book, gross, risk
            "market"                - columns: market, gross
            "index_inventory"       - columns: index, gross

            Set df.attrs["period_label"] and df.attrs["ytd_label"] on pcg_pnl,
            attribution_by_node, main_attribution, inventory_attribution, and
            platform_contribution DataFrames for dynamic column headers
            (e.g., "March" / "2025-YTD" or "W14" / "2025-YTD").
        """
        pass

    @abstractmethod
    def load_hist_pnl(self, report_date):
        """Load historical PnL data.

        Args:
            report_date: YYYY-MM-DD string

        Returns dict:
            "latest_date": str (YYYY-MM-DD of most recent data)
            "pnl": DataFrame with columns: book, td, mtd, ytd
        """
        pass

    @abstractmethod
    def load_live_pnl(self, report_date):
        """Load real-time PnL data.

        Args:
            report_date: YYYY-MM-DD string

        Returns dict:
            "timestamp": str
            "pnl": DataFrame with columns: book, live_pnl
        """
        pass


# ---------------------------------------------------------------------------
# Mock loader — returns hardcoded DataFrames for development/testing
# ---------------------------------------------------------------------------

class MockLoader(BaseLoader):

    def load_dna_data(self, start_date, end_date, report_type):
        if report_type == "daily_pnl":
            return self._load_daily_pnl()
        elif report_type in ("monthly_paa", "weekly_paa"):
            return self._load_paa(report_type)
        return {}

    def load_hist_pnl(self, report_date):
        pnl = pd.DataFrame([
            {"book": "APCR", "td": -120, "mtd": -450, "ytd": 1350},
            {"book": "JPCR", "td": 55, "mtd": 230, "ytd": -890},
            {"book": "SL", "td": 30, "mtd": 180, "ytd": 2100},
        ])
        return {
            "latest_date": "2026-04-02",
            "pnl": pnl,
        }

    def load_live_pnl(self, report_date):
        pnl = pd.DataFrame([
            {"book": "APCR", "live_pnl": 135},
            {"book": "JPCR", "live_pnl": -72},
            {"book": "SL", "live_pnl": 48},
        ])
        return {
            "timestamp": "2026-04-19 15:30:00",
            "pnl": pnl,
        }

    # --- Daily PnL mock DataFrames ---

    def _load_daily_pnl(self):
        pnl = pd.DataFrame([
            {"book": "APCR", "label": "APCR Trading", "td": -35000, "mtd": 98000, "ytd": -1306000},
            {"book": "JPCR", "label": "JPCR Trading", "td": 4000, "mtd": 12000, "ytd": -546000},
            {"book": "SL", "label": "SL Trading", "td": -4000, "mtd": -46000, "ytd": -206000},
        ])

        portfolio_metrics = pd.DataFrame([
            {"book": "APCR", "delta": 1000000, "gross": 50000000, "long": 25000000, "short": 25000000, "total_risk": 0, "factor_risk": 34000, "spec_risk": 88000},
            {"book": "JPCR", "delta": 0, "gross": 6000000, "long": 3000000, "short": 3000000, "total_risk": 0, "factor_risk": 10000, "spec_risk": 5000},
            {"book": "SL", "delta": 2000000, "gross": 81000000, "long": 41000000, "short": 40000000, "total_risk": 116000, "factor_risk": 113000, "spec_risk": 134000},
        ])

        paa_by_region = pd.DataFrame([
            {"region": "Japan", "td": 0, "mtd": -14000, "ytd": -5000},
            {"region": "China", "td": -4000, "mtd": -37000, "ytd": -36000},
            {"region": "Hong Kong", "td": -4000, "mtd": -32000, "ytd": -44000},
            {"region": "Singapore", "td": 2000, "mtd": 1000, "ytd": -1000},
            {"region": "Taiwan", "td": -3000, "mtd": -2000, "ytd": 0},
        ])

        cr_flow = pd.DataFrame([
            {"book": "APCR", "item": "Gross Flow", "td": 0, "mtd_avg": 55000000, "ytd_avg": 49000000},
            {"book": "APCR", "item": "Gross Trade-out", "td": 0, "mtd_avg": 9000000, "ytd_avg": 11000000},
            {"book": "APCR", "item": "CR Retention", "td": 100.0, "mtd_avg": 83.2, "ytd_avg": 77.8},
            {"book": "JPCR", "item": "Gross Flow", "td": 11000000, "mtd_avg": 13000000, "ytd_avg": 18000000},
            {"book": "JPCR", "item": "Gross Trade-out", "td": 4000000, "mtd_avg": 5000000, "ytd_avg": 6000000},
            {"book": "JPCR", "item": "CR Retention", "td": 62.0, "mtd_avg": 63.8, "ytd_avg": 64.2},
        ])

        sl_flow = pd.DataFrame([
            {"market": "China", "td": 0, "mtd_avg": 9000000, "ytd_avg": 0},
            {"market": "Hong Kong", "td": 3000000, "mtd_avg": -3000000, "ytd_avg": 0},
            {"market": "Singapore", "td": 5000000, "mtd_avg": 4000000, "ytd_avg": 0},
        ])

        factor_risk = pd.DataFrame([
            {"book": "APCR", "factor": "BANKS", "exposure": 1515000, "pnl": 3000},
            {"book": "APCR", "factor": "ELECTRON", "exposure": -891000, "pnl": -1000},
            {"book": "APCR", "factor": "HEALTH", "exposure": 1532000, "pnl": 5000},
            {"book": "APCR", "factor": "HKG", "exposure": -3062000, "pnl": -4000},
            {"book": "APCR", "factor": "SIZE", "exposure": -5503000, "pnl": 2000},
            {"book": "APCR", "factor": "QUALITY", "exposure": 3320000, "pnl": -3000},
            {"book": "APCR", "factor": "UTILITY", "exposure": -6413000, "pnl": 0},
            {"book": "APCR", "factor": "DSBETA", "exposure": 4486000, "pnl": 1000},
            {"book": "APCR", "factor": "MEDIARET", "exposure": 0, "pnl": 0},
            {"book": "APCR", "factor": "ENERGY", "exposure": 1033000, "pnl": -2000},
            {"book": "JPCR", "factor": "HKE", "exposure": 542000, "pnl": 2371},
            {"book": "JPCR", "factor": "JPCAPGOODS", "exposure": 195000, "pnl": 1000},
            {"book": "JPCR", "factor": "JPHEALTH", "exposure": 85000, "pnl": -1000},
            {"book": "JPCR", "factor": "JPELECTRON", "exposure": -814000, "pnl": 0},
            {"book": "JPCR", "factor": "JPMOORING", "exposure": -14000, "pnl": 0},
            {"book": "JPCR", "factor": "JPMOMENTUM", "exposure": 262000, "pnl": 1000},
            {"book": "JPCR", "factor": "JPEARNIYLD", "exposure": 688000, "pnl": -1000},
            {"book": "JPCR", "factor": "JPBTOP", "exposure": -493000, "pnl": 0},
            {"book": "SL", "factor": "CHI", "exposure": 1855000, "pnl": 1000},
            {"book": "SL", "factor": "ELECTRON", "exposure": 2656000, "pnl": -2000},
            {"book": "SL", "factor": "HKG", "exposure": -6006000, "pnl": 3000},
            {"book": "SL", "factor": "OSBETA", "exposure": 13459000, "pnl": -1000},
            {"book": "SL", "factor": "BANKS", "exposure": 0, "pnl": 0},
            {"book": "SL", "factor": "SIZE", "exposure": 0, "pnl": 0},
            {"book": "SL", "factor": "CONSTAP", "exposure": -2060000, "pnl": 0},
            {"book": "SL", "factor": "BETA", "exposure": 10068000, "pnl": -1000},
            {"book": "SL", "factor": "CHK", "exposure": 5818000, "pnl": 0},
            {"book": "SL", "factor": "ENERGY", "exposure": -2399000, "pnl": 0},
        ])

        spec_risk = pd.DataFrame([
            {"book": "APCR", "ticker": "600519.SH", "exposure": 6005000, "pnl": -8000},
            {"book": "APCR", "ticker": "1810.HK", "exposure": 1810000, "pnl": -1000},
            {"book": "APCR", "ticker": "0981.HK", "exposure": 981000, "pnl": 2000},
            {"book": "APCR", "ticker": "300206.SZ", "exposure": 3002000, "pnl": -3000},
            {"book": "APCR", "ticker": "0857.HK", "exposure": 857000, "pnl": 1000},
            {"book": "APCR", "ticker": "9633.HK", "exposure": 963000, "pnl": 0},
            {"book": "APCR", "ticker": "601600.SH", "exposure": 1600000, "pnl": -1000},
            {"book": "APCR", "ticker": "0883.HK", "exposure": 883000, "pnl": 0},
            {"book": "APCR", "ticker": "1398.HK", "exposure": 1398000, "pnl": 1000},
            {"book": "APCR", "ticker": "0005.HK", "exposure": 500000, "pnl": -1000},
            {"book": "JPCR", "ticker": "2371.T", "exposure": 2371000, "pnl": 1116},
            {"book": "JPCR", "ticker": "3343.T", "exposure": 3343000, "pnl": -1000},
            {"book": "JPCR", "ticker": "7731.T", "exposure": 7731000, "pnl": 0},
            {"book": "JPCR", "ticker": "6435.T", "exposure": 6435000, "pnl": -1000},
            {"book": "JPCR", "ticker": "5803.T", "exposure": 5803000, "pnl": 0},
            {"book": "JPCR", "ticker": "9432.T", "exposure": 9432000, "pnl": 1000},
            {"book": "JPCR", "ticker": "7261.T", "exposure": 7261000, "pnl": 0},
            {"book": "JPCR", "ticker": "6762.T", "exposure": 6762000, "pnl": -1000},
            {"book": "SL", "ticker": "1910.HK", "exposure": 1910000, "pnl": 1000},
            {"book": "SL", "ticker": "1632.HK", "exposure": 1632000, "pnl": -2000},
            {"book": "SL", "ticker": "0992.HK", "exposure": 992000, "pnl": 0},
            {"book": "SL", "ticker": "1093.HK", "exposure": 1093000, "pnl": 1000},
            {"book": "SL", "ticker": "1768.HK", "exposure": 1768000, "pnl": -1000},
            {"book": "SL", "ticker": "0069.HK", "exposure": 690000, "pnl": 0},
            {"book": "SL", "ticker": "9999.HK", "exposure": 999000, "pnl": 0},
            {"book": "SL", "ticker": "0388.HK", "exposure": 388000, "pnl": 1000},
            {"book": "SL", "ticker": "2628.HK", "exposure": 2628000, "pnl": -1000},
            {"book": "SL", "ticker": "0857.HK", "exposure": 857000, "pnl": 0},
        ])

        net_platform_value = pd.DataFrame([
            {"book": "APCR", "item": "Trading PnL", "td": -35000, "mtd": 99000, "ytd": -3006000},
            {"book": "APCR", "item": "Stamp Saving", "td": 0, "mtd": 102000, "ytd": 2534000},
            {"book": "APCR", "item": "IOI Comms", "td": 0, "mtd": 1000, "ytd": 36000},
            {"book": "APCR", "item": "Follow-on Comms", "td": 2000, "mtd": 7000, "ytd": 15000},
            {"book": "APCR", "item": "EIC Saving (Internal)", "td": 0, "mtd": 1000, "ytd": 49000},
            {"book": "APCR", "item": "EIC Saving (External)", "td": 0, "mtd": 1000, "ytd": 28000},
            {"book": "APCR", "item": "Net Platform Value", "td": -33000, "mtd": 228000, "ytd": 1794000},
            {"book": "JPCR", "item": "Trading PnL", "td": 4000, "mtd": 12000, "ytd": -2564000},
            {"book": "JPCR", "item": "Stamp Saving", "td": 0, "mtd": 1000, "ytd": 33000},
            {"book": "JPCR", "item": "IOI Comms", "td": 0, "mtd": 0, "ytd": 0},
            {"book": "JPCR", "item": "Follow-on Comms", "td": 0, "mtd": 0, "ytd": 0},
            {"book": "JPCR", "item": "EIC Saving (Internal)", "td": 1000, "mtd": 2000, "ytd": 37000},
            {"book": "JPCR", "item": "EIC Saving (External)", "td": 0, "mtd": 0, "ytd": 0},
            {"book": "JPCR", "item": "Net Platform Value", "td": 5000, "mtd": 15000, "ytd": -2494000},
        ])

        cr_strategy_paa = pd.DataFrame([
            {"region": "Japan", "pnl": 10000, "tracking": -37000, "inventory": 5000},
            {"region": "China", "pnl": -13000, "tracking": -10000, "inventory": -6000},
            {"region": "Hong Kong", "pnl": 0, "tracking": -6000, "inventory": -4000},
            {"region": "Singapore", "pnl": 2000, "tracking": 1000, "inventory": -1000},
            {"region": "Taiwan", "pnl": -3000, "tracking": -2000, "inventory": 0},
        ])

        cr_flow_paa = pd.DataFrame([
            {"source": "JP", "desk": "CR Match", "value": 3655000, "pnl": 0},
            {"source": "JP", "desk": "LH", "value": 811000, "pnl": 0},
            {"source": "JP LH", "desk": "Agency", "value": 5683000, "pnl": -7000},
            {"source": "JP LH", "desk": "Cash", "value": 694000, "pnl": -1000},
            {"source": "JP LH", "desk": "D1", "value": 462000, "pnl": 2000},
        ])

        sl_top_positions = pd.DataFrame([
            {"ticker": "300702.SZ", "pnl": -1000, "shares": 2620, "value": 85000},
            {"ticker": "002594.SZ", "pnl": 4000, "shares": 992, "value": 42000},
            {"ticker": "002475.SZ", "pnl": 0, "shares": 330, "value": 18000},
            {"ticker": "603292.SH", "pnl": -4000, "shares": 450, "value": 35000},
            {"ticker": "601600.SH", "pnl": -1000, "shares": 1693, "value": 28000},
            {"ticker": "300274.SZ", "pnl": -3000, "shares": 1670, "value": 22000},
            {"ticker": "600222.SZ", "pnl": 2000, "shares": 1574, "value": 19000},
            {"ticker": "600276.SH", "pnl": -2000, "shares": 1503, "value": 16000},
        ])

        return {
            "pnl": pnl,
            "portfolio_metrics": portfolio_metrics,
            "paa_by_region": paa_by_region,
            "cr_flow": cr_flow,
            "sl_flow": sl_flow,
            "factor_risk": factor_risk,
            "spec_risk": spec_risk,
            "net_platform_value": net_platform_value,
            "cr_strategy_paa": cr_strategy_paa,
            "cr_flow_paa": cr_flow_paa,
            "sl_top_positions": sl_top_positions,
        }

    # --- Monthly/Weekly PAA mock DataFrames ---

    def _load_paa(self, report_type):
        period = "March" if report_type == "monthly_paa" else "W14"
        ytd_label = "2025-YTD"

        pcg_pnl = pd.DataFrame([
            {"book": "APCR", "period_pnl": -558, "ytd_pnl": -1356},
            {"book": "JPCR", "period_pnl": -29, "ytd_pnl": -289},
            {"book": "SL", "period_pnl": 1211, "ytd_pnl": 1026},
        ])
        pcg_pnl.attrs["period_label"] = period
        pcg_pnl.attrs["ytd_label"] = ytd_label

        attribution_by_node = pd.DataFrame([
            {"book": "APCR", "node": "APCR_MAIN", "period_pnl": -641, "ytd_pnl": -5430},
            {"book": "APCR", "node": "APCR_INVENTORY", "period_pnl": 316, "ytd_pnl": -464},
            {"book": "APCR", "node": "APCR_FUNDING", "period_pnl": 0, "ytd_pnl": 0},
            {"book": "APCR", "node": "APCR_SPARE", "period_pnl": 0, "ytd_pnl": -474},
            {"book": "JPCR", "node": "JPCR_MAIN", "period_pnl": 0, "ytd_pnl": -284},
            {"book": "JPCR", "node": "JPCR_INVENTORY", "period_pnl": -9, "ytd_pnl": 0},
            {"book": "JPCR", "node": "JPCR_SPARE", "period_pnl": 0, "ytd_pnl": 0},
            {"book": "SL", "node": "APSL_AU", "period_pnl": 0, "ytd_pnl": 0},
            {"book": "SL", "node": "APSL_CN", "period_pnl": 0, "ytd_pnl": -1},
            {"book": "SL", "node": "APSL_HK", "period_pnl": 983, "ytd_pnl": 154},
            {"book": "SL", "node": "APSL_SG", "period_pnl": 97, "ytd_pnl": 0},
            {"book": "SL", "node": "APSL_FEE", "period_pnl": 0, "ytd_pnl": 0},
            {"book": "SL", "node": "APSL_SPARE", "period_pnl": 0, "ytd_pnl": 0},
        ])
        attribution_by_node.attrs["period_label"] = period
        attribution_by_node.attrs["ytd_label"] = ytd_label

        main_attribution = pd.DataFrame([
            {"book": "APCR", "strategy": "Tracking Error HK", "period_pnl": -485, "ytd_pnl": -1260},
            {"book": "APCR", "strategy": "Tracking Error SG", "period_pnl": 0, "ytd_pnl": 0},
            {"book": "APCR", "strategy": "Tracking Error CN", "period_pnl": 12, "ytd_pnl": -174},
            {"book": "APCR", "strategy": "PBMM HK", "period_pnl": 109, "ytd_pnl": 245},
            {"book": "APCR", "strategy": "PBMM CN", "period_pnl": 0, "ytd_pnl": 0},
            {"book": "JPCR", "strategy": "Tracking Error JP", "period_pnl": 41, "ytd_pnl": 15},
            {"book": "JPCR", "strategy": "CR IOI", "period_pnl": 2, "ytd_pnl": 12},
            {"book": "JPCR", "strategy": "LH Japan", "period_pnl": -73, "ytd_pnl": 0},
            {"book": "JPCR", "strategy": "CMatch", "period_pnl": 6, "ytd_pnl": 17},
        ])
        main_attribution.attrs["period_label"] = period
        main_attribution.attrs["ytd_label"] = ytd_label

        inventory_attribution = pd.DataFrame([
            {"book": "APCR", "index": "HSI", "period_pnl": -14, "ytd_pnl": 13},
            {"book": "APCR", "index": "HSCEI", "period_pnl": 44, "ytd_pnl": -195},
            {"book": "APCR", "index": "HSTECH", "period_pnl": -49, "ytd_pnl": 64},
            {"book": "APCR", "index": "A50", "period_pnl": 16, "ytd_pnl": -445},
            {"book": "JPCR", "index": "NKY", "period_pnl": 0, "ytd_pnl": -8},
            {"book": "JPCR", "index": "TPX", "period_pnl": -1, "ytd_pnl": 0},
            {"book": "JPCR", "index": "EFP", "period_pnl": 0, "ytd_pnl": 0},
        ])
        inventory_attribution.attrs["period_label"] = period
        inventory_attribution.attrs["ytd_label"] = ytd_label

        platform_contribution = pd.DataFrame([
            {"book": "APCR", "item": "Stamp Saving", "period_pnl": 673, "ytd_pnl": 5562},
            {"book": "APCR", "item": "IOI Commission", "period_pnl": 4, "ytd_pnl": 18},
            {"book": "APCR", "item": "Follow On Commission", "period_pnl": 1, "ytd_pnl": 6},
            {"book": "APCR", "item": "EIC Saving (Internal)", "period_pnl": 122, "ytd_pnl": 265},
            {"book": "JPCR", "item": "HT Commission", "period_pnl": 0, "ytd_pnl": 2},
            {"book": "JPCR", "item": "Follow On Commission", "period_pnl": 1, "ytd_pnl": 0},
            {"book": "JPCR", "item": "EIC Saving (Internal)", "period_pnl": 10, "ytd_pnl": 22},
            {"book": "JPCR", "item": "EIC Saving (Agency)", "period_pnl": 25, "ytd_pnl": 63},
        ])
        platform_contribution.attrs["period_label"] = period
        platform_contribution.attrs["ytd_label"] = ytd_label

        risk = pd.DataFrame([
            {"book": "APCR", "gross": "48mm", "risk": "69K"},
            {"book": "JPCR", "gross": "9mm", "risk": "14K"},
            {"book": "SL", "gross": "109mm", "risk": "242K"},
        ])

        market = pd.DataFrame([
            {"market": "HK", "gross": "27mm"},
            {"market": "CN", "gross": "15mm"},
            {"market": "SG", "gross": "0mm"},
        ])

        index_inventory = pd.DataFrame([
            {"index": "HSI", "gross": "18mm"},
            {"index": "HSCEI", "gross": "25mm"},
            {"index": "HSTECH", "gross": "0mm"},
            {"index": "A50", "gross": "10mm"},
        ])

        return {
            "pcg_pnl": pcg_pnl,
            "attribution_by_node": attribution_by_node,
            "main_attribution": main_attribution,
            "inventory_attribution": inventory_attribution,
            "platform_contribution": platform_contribution,
            "risk": risk,
            "market": market,
            "index_inventory": index_inventory,
        }


# ---------------------------------------------------------------------------
# Real data loader — implement with desktool queries
# ---------------------------------------------------------------------------

class DataLoader(BaseLoader):

    def load_dna_data(self, start_date, end_date, report_type):
        if report_type == "daily_pnl":
            return self._load_daily_pnl(start_date, end_date)
        elif report_type in ("monthly_paa", "weekly_paa"):
            return self._load_paa(start_date, end_date, report_type)
        return {}

    def _load_daily_pnl(self, start_date, end_date):
        # TODO: implement with desktool queries
        raise NotImplementedError

    def _load_paa(self, start_date, end_date, report_type):
        # TODO: implement with desktool queries
        raise NotImplementedError

    def load_hist_pnl(self, report_date):
        # TODO: implement — e.g., read from S3
        raise NotImplementedError

    def load_live_pnl(self, report_date):
        # TODO: implement — e.g., query real-time API
        raise NotImplementedError

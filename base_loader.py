from abc import ABC, abstractmethod


class BaseLoader(ABC):

    @abstractmethod
    def load_dna_data(self, start_date, end_date, report_type):
        # Load KDB+ DNA data for a given date range and report type
        # report_type: 'daily_pnl', 'monthly_paa', 'weekly_paa'
        # start_date / end_date: YYYY-MM-DD strings (first/last weekday of period)
        # For daily: start_date == end_date
        pass

    @abstractmethod
    def load_hist_pnl(self, report_date):
        # Load S3 historical PnL data, returns dict with latest_date and pnl_data
        pass

    @abstractmethod
    def load_live_pnl(self, report_date):
        # Load real-time PnL from internal API (daily PnL only)
        pass

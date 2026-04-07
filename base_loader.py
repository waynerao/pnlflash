from abc import ABC, abstractmethod


class BaseLoader(ABC):

    @abstractmethod
    def load_dna_data(self, report_date, report_type):
        # Load KDB+ DNA data for a given date and report type
        # report_type: 'daily_pnl', 'monthly_paa', 'weekly_paa'
        pass

    @abstractmethod
    def load_hist_pnl(self, report_date):
        # Load S3 historical PnL data, returns dict with latest_date and pnl_data
        pass

    @abstractmethod
    def load_live_pnl(self, report_date):
        # Load real-time PnL from internal API (daily PnL only)
        pass

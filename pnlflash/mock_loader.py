import json
from pathlib import Path

from base_loader import BaseLoader

MOCK_DATA_DIR = Path(__file__).parent / "mock_data"


class MockLoader(BaseLoader):

    def load_dna_data(self, start_date, end_date, report_type):
        # report_type: 'daily_pnl', 'monthly_paa', 'weekly_paa'
        # start_date / end_date ignored for mock data
        file_path = MOCK_DATA_DIR / f"{report_type}.json"
        with open(file_path) as f:
            return json.load(f)

    def load_hist_pnl(self, report_date):
        file_path = MOCK_DATA_DIR / "hist_pnl.json"
        with open(file_path) as f:
            return json.load(f)

    def load_live_pnl(self, report_date):
        file_path = MOCK_DATA_DIR / "live_pnl.json"
        with open(file_path) as f:
            return json.load(f)

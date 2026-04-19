import logging
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)


class DataStore:
    """Server-side data store holding loaded data in memory.

    Data is loaded by a loader (see data_loader.py) and stored here. Data functions access
    this store directly. Supports parallel loading of multiple sources.

    For mock data the stored objects are plain dicts. For real loaders
    they will be pandas DataFrames (with possible MultiIndex).
    """

    def __init__(self):
        self._dna_data = {}   # {report_type: data_dict_or_dataframes}
        self._dates = {}      # {report_type: {"start_date": str, "end_date": str}}
        self._hist_pnl = None
        self._live_pnl = None
        self._status = {
            "dna": {"status": "idle", "timestamp": None, "error": None},
            "hist_pnl": {"status": "idle", "timestamp": None, "error": None},
            "live_pnl": {"status": "idle", "timestamp": None, "error": None},
        }

    # --- Status ---

    def get_status(self, source=None):
        """Return status dict for one source, or all sources."""
        if source:
            return dict(self._status.get(source, {}))
        return {k: dict(v) for k, v in self._status.items()}

    # --- Data access ---

    def get_dna_data(self, report_type):
        """Return loaded DNA data for a report type."""
        return self._dna_data.get(report_type, {})

    def get_dates(self, report_type):
        """Return {start_date, end_date} for a report type."""
        return self._dates.get(report_type, {})

    def get_hist_pnl(self):
        return self._hist_pnl or {}

    def get_live_pnl(self):
        return self._live_pnl or {}

    # --- Loading ---

    def load(self, loader, sources, report_type, start_date, end_date):
        """Load data from specified sources in parallel.

        Args:
            loader: loader instance (MockLoader or DataLoader)
            sources: list of source names ("dna", "hist_pnl", "live_pnl")
            report_type: e.g. "daily_pnl", "monthly_paa"
            start_date, end_date: YYYY-MM-DD strings

        Returns:
            dict of {source_name: status_dict} after all loads complete.
        """
        self._dates[report_type] = {"start_date": start_date, "end_date": end_date}

        def _load_one(source):
            self._status[source] = {
                "status": "loading", "timestamp": None, "error": None,
            }
            try:
                if source == "dna":
                    self._dna_data[report_type] = loader.load_dna_data(
                        start_date, end_date, report_type)
                elif source == "hist_pnl":
                    self._hist_pnl = loader.load_hist_pnl(start_date)
                elif source == "live_pnl":
                    self._live_pnl = loader.load_live_pnl(start_date)
                else:
                    raise ValueError(f"Unknown source: {source}")
                self._status[source] = {
                    "status": "ready",
                    "timestamp": datetime.now().strftime("%H:%M:%S"),
                    "error": None,
                }
            except Exception as e:
                logger.error(f"Failed to load {source}: {e}")
                self._status[source] = {
                    "status": "error",
                    "timestamp": datetime.now().strftime("%H:%M:%S"),
                    "error": str(e),
                }

        with ThreadPoolExecutor(max_workers=len(sources)) as executor:
            futures = {executor.submit(_load_one, src): src for src in sources}
            for future in as_completed(futures):
                future.result()

        return self.get_status()

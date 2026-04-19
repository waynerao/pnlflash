import logging
import json
from datetime import datetime, date, timedelta
from pathlib import Path
from functools import wraps

from flask import Flask, request, jsonify, render_template, abort

from config import APP_HOST, APP_PORT, TOKENS, EMAIL_SUBJECTS, EMAIL_RECIPIENTS, PORTFOLIO_METRICS_PATH, S3_RELOAD_AFTER, REALTIME_RELOAD_AFTER, SETUP_PASSWORD
from data_loader import MockLoader
from data_store import DataStore
from email_builder import build_email, build_preview, render_single_table, compute_email_width
from email_sender import send_email
from data_functions import DATA_FUNCTIONS

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__)
loader = MockLoader()
data_store = DataStore()
LAYOUTS_DIR = Path(__file__).parent / "layouts"


def validate_token(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        token = request.args.get("token") or request.form.get("token")
        if not token or token not in TOKENS.values():
            abort(403)
        user = next((k for k, v in TOKENS.items() if v == token), "unknown")
        kwargs["user"] = user
        kwargs["token"] = token
        return f(*args, **kwargs)
    return wrapper


def _load_layout(report_type):
    layout_path = LAYOUTS_DIR / f"{report_type}.json"
    if layout_path.exists():
        with open(layout_path) as f:
            return json.load(f)
    return None


def _save_layout(report_type, layout_data):
    layout_path = LAYOUTS_DIR / f"{report_type}.json"
    with open(layout_path, "w", encoding="utf-8") as f:
        json.dump(layout_data, f, indent=4, ensure_ascii=False)
    logger.info(f"Layout saved: {layout_path}")


def get_table_formats():
    formats = {}
    for report_type in ["daily_pnl", "monthly_paa", "weekly_paa"]:
        layout = _load_layout(report_type)
        if layout:
            formats[report_type] = {tbl_id: tbl["col_formats"] for tbl_id, tbl in layout.get("tables", {}).items()}
        else:
            formats[report_type] = {}
    return formats


def get_email_config():
    config = {}
    for report_type in ["daily_pnl", "monthly_paa", "weekly_paa"]:
        recipients = EMAIL_RECIPIENTS.get(report_type, {})
        config[report_type] = {
            "subject": EMAIL_SUBJECTS.get(report_type, ""),
            "to": recipients.get("to", []),
            "cc": recipients.get("cc", []),
        }
    return config


def save_portfolio_metrics(report_date):
    """Save portfolio metrics from DataStore to CSV."""
    dna = data_store.get_dna_data("daily_pnl")
    df = dna.get("portfolio_metrics")
    if df is None or (hasattr(df, 'empty') and df.empty):
        return
    PORTFOLIO_METRICS_PATH.mkdir(parents=True, exist_ok=True)
    date_str = report_date.replace("-", "")[:8]
    csv_path = PORTFOLIO_METRICS_PATH / f"{date_str}.csv"
    df.to_csv(csv_path, index=False)
    logger.info(f"Portfolio metrics saved to {csv_path}")


def _get_table_data(report_type):
    """Run all data functions for a report type and return per-table data."""
    layout = _load_layout(report_type)
    if not layout:
        return {}
    tables_def = layout.get("tables", {})
    result = {}
    for tbl_id, tbl_def in tables_def.items():
        func = DATA_FUNCTIONS.get(tbl_def.get("function", ""))
        if func:
            try:
                result[tbl_id] = func(data_store, tbl_def.get("params", {}))
            except Exception as e:
                logger.warning(f"Data function error for {tbl_id}: {e}")
                result[tbl_id] = {"headers": [], "rows": []}
        else:
            result[tbl_id] = {"headers": [], "rows": []}
    return result


def _check_t1_available(report_date, latest_date):
    if not latest_date or not report_date:
        return False
    try:
        report_dt = datetime.strptime(report_date[:10], "%Y-%m-%d").date()
        latest_dt = datetime.strptime(latest_date[:10], "%Y-%m-%d").date()
        t1 = report_dt - timedelta(days=1)
        while t1.weekday() >= 5:
            t1 -= timedelta(days=1)
        return latest_dt >= t1
    except ValueError:
        return False


# --- Dashboard routes ---

@app.route("/")
@validate_token
def dashboard(**kwargs):
    today = date.today()
    return render_template("dashboard.html",
        user=kwargs["user"], token=kwargs["token"],
        today=today.isoformat(),
        today_month=today.strftime("%Y-%m"),
        today_week=today.strftime("%Y-W%W"),
        email_config=get_email_config(),
        table_formats=get_table_formats(),
        data_functions=list(DATA_FUNCTIONS.keys()),
        schedule={"s3_reload_after": S3_RELOAD_AFTER, "realtime_reload_after": REALTIME_RELOAD_AFTER})


@app.route("/load", methods=["POST"])
@validate_token
def load_data(**kwargs):
    """Load data sources in parallel into DataStore, then return per-table data."""
    body = request.get_json()
    report_type = body.get("report_type")
    sources = body.get("sources", ["dna"])
    start_date = body.get("start_date", date.today().isoformat())
    end_date = body.get("end_date", date.today().isoformat())

    # Load requested sources in parallel
    load_status = data_store.load(loader, sources, report_type, start_date, end_date)

    # Auto-save portfolio metrics after daily DNA load
    if "dna" in sources and report_type == "daily_pnl":
        save_portfolio_metrics(start_date)

    # Build hist PnL info if loaded
    hist_info = {}
    if "hist_pnl" in sources:
        hist_data = data_store.get_hist_pnl()
        latest_date = hist_data.get("latest_date", "")
        pnl_df = hist_data.get("pnl")
        pnl_by_book = {}
        if pnl_df is not None and not pnl_df.empty:
            pnl_by_book = pnl_df.set_index("book").to_dict("index")
        hist_info = {
            "latest_date": latest_date,
            "t1_available": _check_t1_available(start_date, latest_date),
            "pnl_data": pnl_by_book,
        }

    # Run data functions to get per-table data for the browser
    table_data = _get_table_data(report_type)

    return jsonify({
        "status": "ok",
        "load_status": load_status,
        "data": table_data,
        "hist_info": hist_info,
    })


@app.route("/load/status")
@validate_token
def load_status(**kwargs):
    """Return current load status per source without triggering a new load."""
    return jsonify({"status": "ok", "load_status": data_store.get_status()})


@app.route("/preview", methods=["POST"])
@validate_token
def preview(**kwargs):
    report_type = request.args.get("report_type")
    body = request.get_json()
    data_override = body.get("data", {})
    html = build_preview(report_type, data_store, data_override if data_override else None)
    return jsonify({"status": "ok", "html": html})


@app.route("/send", methods=["POST"])
@validate_token
def send(**kwargs):
    body = request.get_json()
    report_type = body.get("report_type")
    subject = body.get("subject", "")
    to_str = body.get("to", "")
    cc_str = body.get("cc", "")
    data_override = body.get("data", {})

    to_list = [s.strip() for s in to_str.split(",") if s.strip()]
    cc_list = [s.strip() for s in cc_str.split(",") if s.strip()]
    html = build_email(report_type, data_store, data_override if data_override else None)
    file_path = send_email(html, subject, to_list, cc_list)
    logger.info(f"Email sent by {kwargs['user']}: {subject}")
    return jsonify({"status": "ok", "file_path": file_path})


# --- Setup routes ---

@app.route("/setup/load", methods=["POST"])
@validate_token
def setup_load(**kwargs):
    body = request.get_json()
    password = body.get("password", "")
    if password != SETUP_PASSWORD:
        return jsonify({"status": "error", "message": "Invalid password"})
    report_type = body.get("report_type")
    layout = _load_layout(report_type)
    if not layout:
        layout = {"settings": {"row_gap": 4, "default_table_gap": 4, "font_size": 11}, "tables": {}, "layout": []}
    font_size = layout.get("settings", {}).get("font_size", 11)

    # Ensure DataStore has data for this report type
    today = date.today().isoformat()
    data_store.load(loader, ["dna"], report_type, today, today)

    # Render each table as HTML and compute dimensions
    dimensions = {}
    rendered_tables = {}
    for tbl_id, tbl_def in layout.get("tables", {}).items():
        func = DATA_FUNCTIONS.get(tbl_def.get("function", ""))
        w_px = sum(tbl_def.get("col_widths", [80]))
        rows = 3
        table_data = {"headers": [], "rows": []}
        if func:
            try:
                table_data = func(data_store, tbl_def.get("params", {}))
                rows = len(table_data.get("rows", []))
            except Exception:
                pass
        if "display_rows" not in tbl_def:
            tbl_def["display_rows"] = rows
        dimensions[tbl_id] = {"w_px": w_px, "rows": rows}
        rendered_tables[tbl_id] = render_single_table(tbl_id, tbl_def, table_data, font_size)
    email_width = compute_email_width(layout)
    return jsonify({"status": "ok", "layout": layout, "dimensions": dimensions,
                     "rendered_tables": rendered_tables, "email_width": email_width})


@app.route("/setup/render_table", methods=["POST"])
@validate_token
def setup_render_table(**kwargs):
    body = request.get_json()
    password = body.get("password", "")
    if password != SETUP_PASSWORD:
        return jsonify({"status": "error", "message": "Invalid password"})
    tbl_id = body.get("table_id")
    tbl_def = body.get("table_def")
    if not tbl_id or not tbl_def:
        return jsonify({"status": "error", "message": "Missing table_id or table_def"})
    func = DATA_FUNCTIONS.get(tbl_def.get("function", ""))
    table_data = {"headers": [], "rows": []}
    if func:
        try:
            table_data = func(data_store, tbl_def.get("params", {}))
        except Exception:
            pass
    font_size = body.get("font_size", 11)
    html = render_single_table(tbl_id, tbl_def, table_data, font_size)
    return jsonify({"status": "ok", "html": html})


@app.route("/setup/save", methods=["POST"])
@validate_token
def setup_save(**kwargs):
    body = request.get_json()
    password = body.get("password", "")
    if password != SETUP_PASSWORD:
        return jsonify({"status": "error", "message": "Invalid password"})
    report_type = body.get("report_type")
    layout_data = body.get("layout")
    if not report_type or not layout_data:
        return jsonify({"status": "error", "message": "Missing report_type or layout"})
    _save_layout(report_type, layout_data)
    return jsonify({"status": "ok"})



if __name__ == "__main__":
    app.run(host=APP_HOST, port=APP_PORT, debug=True)

import logging
import json
from datetime import datetime, date
from pathlib import Path
from functools import wraps

from flask import Flask, request, jsonify, render_template, abort

from config import APP_HOST, APP_PORT, TOKENS, EMAIL_SUBJECTS, EMAIL_RECIPIENTS, PORTFOLIO_METRICS_PATH, S3_RELOAD_AFTER, REALTIME_RELOAD_AFTER, SETUP_PASSWORD
from mock_loader import MockLoader
from email_builder import build_email, build_preview, render_single_table, compute_email_width
from email_sender import send_email
from data_functions import DATA_FUNCTIONS

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__)
loader = MockLoader()
LAYOUTS_DIR = Path(__file__).parent / "layouts"

# In-memory cache for hist PnL (shared across tabs)
_hist_pnl_cache = {"data": None, "loaded_at": None}


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


def save_portfolio_metrics(data, report_date):
    portfolio_metrics = data.get("portfolio_metrics")
    if not portfolio_metrics:
        return
    PORTFOLIO_METRICS_PATH.mkdir(parents=True, exist_ok=True)
    date_str = report_date.replace("-", "")[:8]
    csv_path = PORTFOLIO_METRICS_PATH / f"{date_str}.csv"
    headers = portfolio_metrics["headers"]
    rows = portfolio_metrics["rows"]
    with open(csv_path, "w", encoding="utf-8") as f:
        f.write(",".join(str(h) for h in headers) + "\n")
        for row in rows:
            f.write(",".join(str(c) for c in row) + "\n")
    logger.info(f"Portfolio metrics saved to {csv_path}")


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


@app.route("/load")
@validate_token
def load_data(**kwargs):
    report_type = request.args.get("report_type")
    source = request.args.get("source")
    start_date = request.args.get("start_date", date.today().isoformat())
    end_date = request.args.get("end_date", date.today().isoformat())

    if source == "dna":
        data = loader.load_dna_data(start_date, end_date, report_type)
        if report_type == "daily_pnl":
            save_portfolio_metrics(data, start_date)
        return jsonify({"status": "ok", "data": data})
    elif source == "hist":
        result = loader.load_hist_pnl(start_date)
        _hist_pnl_cache["data"] = result
        _hist_pnl_cache["loaded_at"] = datetime.now().isoformat()
        latest_date = result.get("latest_date", "")
        t1_available = _check_t1_available(start_date, latest_date)
        return jsonify({"status": "ok", "latest_date": latest_date, "t1_available": t1_available, "pnl_data": result.get("pnl_by_book", {})})
    elif source == "live":
        result = loader.load_live_pnl(start_date)
        return jsonify({"status": "ok", "data": result})
    return jsonify({"status": "error", "message": f"Unknown source: {source}"})


def _check_t1_available(report_date, latest_date):
    if not latest_date or not report_date:
        return False
    try:
        report_dt = datetime.strptime(report_date[:10], "%Y-%m-%d").date()
        latest_dt = datetime.strptime(latest_date[:10], "%Y-%m-%d").date()
        from datetime import timedelta
        t1 = report_dt - timedelta(days=1)
        while t1.weekday() >= 5:
            t1 -= timedelta(days=1)
        return latest_dt >= t1
    except ValueError:
        return False


@app.route("/preview", methods=["POST"])
@validate_token
def preview(**kwargs):
    report_type = request.args.get("report_type")
    start_date = request.args.get("start_date", date.today().isoformat())
    end_date = request.args.get("end_date", date.today().isoformat())
    body = request.get_json()
    data_override = body.get("data", {})
    html = build_preview(report_type, loader, start_date, end_date, data_override if data_override else None)
    return jsonify({"status": "ok", "html": html})


@app.route("/send", methods=["POST"])
@validate_token
def send(**kwargs):
    body = request.get_json()
    report_type = body.get("report_type")
    start_date = body.get("start_date", date.today().isoformat())
    end_date = body.get("end_date", date.today().isoformat())
    subject = body.get("subject", "")
    to_str = body.get("to", "")
    cc_str = body.get("cc", "")
    data_override = body.get("data", {})

    to_list = [s.strip() for s in to_str.split(",") if s.strip()]
    cc_list = [s.strip() for s in cc_str.split(",") if s.strip()]
    html = build_email(report_type, loader, start_date, end_date, data_override if data_override else None)
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
                today = date.today().isoformat()
                table_data = func(loader, today, today, tbl_def.get("params", {}))
                rows = len(table_data.get("rows", []))
            except Exception:
                pass
        # Set default display_rows from actual data if not configured
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
            today = date.today().isoformat()
            table_data = func(loader, today, today, tbl_def.get("params", {}))
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

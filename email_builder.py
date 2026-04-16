import json
import logging
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from formatter import format_number, is_negative_display
from data_functions import DATA_FUNCTIONS, clear_cache

logger = logging.getLogger(__name__)

TEMPLATE_DIR = Path(__file__).parent / "templates"
LAYOUTS_DIR = Path(__file__).parent / "layouts"

_env = Environment(loader=FileSystemLoader(TEMPLATE_DIR), autoescape=False)
_env.filters["fmt"] = format_number
_env.filters["is_neg"] = is_negative_display


def load_layout(report_type):
    layout_path = LAYOUTS_DIR / f"{report_type}.json"
    with open(layout_path) as f:
        return json.load(f)


def grid_to_rows(layout_items, default_gap=4):
    """Convert layout items [{id, x, y, ...}] to row-based format for email rendering.

    Supports both pixel positions (large y values) and grid positions (small integers).
    For pixel positions, clusters items within ROW_THRESHOLD px into the same row.
    """
    if not layout_items:
        return []
    # Detect format: old row format has 'tables' key
    if layout_items and "tables" in layout_items[0]:
        return layout_items  # Already in row format

    sorted_items = sorted(layout_items, key=lambda i: (i.get("y", 0), i.get("x", 0)))

    # Determine clustering threshold: pixel mode (y > 20) vs grid mode (small integers)
    max_y = max(i.get("y", 0) for i in sorted_items)
    threshold = 30 if max_y > 20 else 0

    # Cluster by consecutive y-gap
    clusters = [[sorted_items[0]]]
    for item in sorted_items[1:]:
        y = item.get("y", 0)
        prev_y = clusters[-1][-1].get("y", 0)
        if y - prev_y <= threshold:
            clusters[-1].append(item)
        else:
            clusters.append([item])

    # Convert clusters to row format
    rows = []
    for cluster in clusters:
        items = sorted(cluster, key=lambda i: i.get("x", 0))
        tables = []
        for i, item in enumerate(items):
            entry = {"id": item["id"]}
            if i < len(items) - 1:
                entry["gap"] = default_gap
            tables.append(entry)
        rows.append({"tables": tables})
    return rows


def _grid_to_pixel_positions(layout_items, tables_def, default_gap, row_gap):
    """Convert small-integer grid positions to pixel positions for preview rendering."""
    rows = grid_to_rows(layout_items, default_gap)
    positions = {}
    current_y = 10
    for row in rows:
        current_x = 10
        max_h = 0
        for i, item in enumerate(row["tables"]):
            tbl_id = item["id"]
            positions[tbl_id] = (current_x, current_y)
            tbl_def = tables_def.get(tbl_id, {})
            tbl_w = sum(tbl_def.get("col_widths", [80]))
            display_rows = tbl_def.get("display_rows", 3)
            tbl_h = (display_rows + 2) * 18
            current_x += tbl_w + item.get("gap", default_gap)
            max_h = max(max_h, tbl_h)
        current_y += max_h + row_gap
    return positions


def build_email(report_type, loader, start_date, end_date, data_override=None, layout_override=None):
    """Build the full email HTML document. Body uses the same absolute-positioned
    layout as the canvas/preview so what users see in the editor matches what they send."""
    body = _render_layout_body(report_type, loader, start_date, end_date,
                               data_override=data_override, layout_override=layout_override)
    return (
        '<!DOCTYPE html><html><head><meta charset="utf-8"></head>'
        '<body style="margin:0;padding:0;">' + body + '</body></html>'
    )


def _render_layout_body(report_type, loader, start_date, end_date,
                        data_override=None, layout_override=None):
    """Render the absolute-positioned tables layout (no <html>/<body> wrapper)."""
    clear_cache()
    layout_config = layout_override if layout_override else load_layout(report_type)
    tables_def = layout_config["tables"]
    layout_items = layout_config.get("layout", [])
    settings = layout_config.get("settings", {})
    font_size = settings.get("font_size", 11)
    default_gap = settings.get("default_table_gap", 4)
    row_gap = settings.get("row_gap", 4)

    # Gather table data and render each table
    rendered = {}
    for tbl_id, tbl_def in tables_def.items():
        if data_override and tbl_id in data_override:
            table_data = data_override[tbl_id]
        else:
            func_name = tbl_def["function"]
            func = DATA_FUNCTIONS.get(func_name)
            if func:
                table_data = func(loader, start_date, end_date, tbl_def.get("params", {}))
            else:
                logger.warning(f"Data function not found: {func_name}")
                table_data = {"headers": [], "rows": []}
        rendered[tbl_id] = render_single_table(tbl_id, tbl_def, table_data, font_size)

    # Detect if layout uses small grid integers (old format) vs pixel positions
    max_y = max((item.get("y", 0) for item in layout_items), default=0) if layout_items else 0
    if max_y <= 20:
        positions = _grid_to_pixel_positions(layout_items, tables_def, default_gap, row_gap)
    else:
        positions = {item["id"]: (item.get("x", 0), item.get("y", 0)) for item in layout_items}

    # Calculate bounding box for the container
    max_w = 0
    max_h = 0
    for tbl_id, (x, y) in positions.items():
        if tbl_id not in tables_def:
            continue
        tbl_def = tables_def[tbl_id]
        col_widths = tbl_def.get("col_widths", [80])
        tbl_w = sum(col_widths)
        display_rows = tbl_def.get("display_rows", 3)
        tbl_h = (display_rows + 2) * 18
        max_w = max(max_w, x + tbl_w + 20)
        max_h = max(max_h, y + tbl_h + 20)

    html = f'<div style="position:relative;width:{max_w}px;height:{max_h}px;font-family:Calibri,Arial,sans-serif;font-size:{font_size}px;color:#333;">'
    for tbl_id, (x, y) in positions.items():
        if tbl_id not in rendered:
            continue
        html += f'<div style="position:absolute;left:{x}px;top:{y}px;">{rendered[tbl_id]}</div>'
    html += '</div>'
    return html


def _apply_display_cols(headers, rows, col_widths, col_headers=None):
    """Truncate or pad headers and rows to match col_widths count."""
    target_cols = len(col_widths)
    if target_cols == len(headers):
        return headers, rows

    if target_cols < len(headers):
        # Truncate
        truncated_headers = list(headers[:target_cols])
        truncated_rows = [list(row[:target_cols]) for row in rows]
        return truncated_headers, truncated_rows

    # Pad headers
    padded_headers = list(headers)
    for i in range(len(headers), target_cols):
        if col_headers and i < len(col_headers):
            padded_headers.append(col_headers[i])
        else:
            padded_headers.append("")
    # Pad each row
    padded_rows = []
    for row in rows:
        padded_row = list(row)
        padded_row.extend(["\u00a0"] * (target_cols - len(padded_row)))
        padded_rows.append(padded_row)
    return padded_headers, padded_rows


def _apply_display_rows(rows, headers, display_rows):
    """Truncate or pad rows to match display_rows count."""
    if display_rows is None:
        return rows
    num_cols = len(headers) if headers else (len(rows[0]) if rows else 0)
    if len(rows) > display_rows:
        rows = rows[:display_rows]
    elif len(rows) < display_rows:
        empty_row = ["\u00a0"] * num_cols  # &nbsp; to maintain row height
        rows = list(rows) + [empty_row] * (display_rows - len(rows))
    return rows


def render_single_table(table_id, table_def, table_data, font_size=11):
    """Render a single table as standalone HTML (same style as email)."""
    headers = table_data.get("headers", [])
    rows = table_data.get("rows", [])
    col_widths = table_def.get("col_widths", [])
    col_formats = table_def.get("col_formats", [])
    col_headers = table_def.get("col_headers")
    name = table_def.get("name", table_id)
    display_rows = table_def.get("display_rows")
    header_font = max(font_size - 1, 8)

    # Truncate or pad columns to match col_widths count
    if col_widths and len(col_widths) != len(headers):
        headers, rows = _apply_display_cols(headers, rows, col_widths, col_headers)

    rows = _apply_display_rows(rows, headers, display_rows)

    html = '<table cellpadding="0" cellspacing="0" style="border-collapse:collapse;">'
    html += f'<tr><td colspan="{len(headers)}" style="font-weight:bold;padding:2px 4px 1px 2px;font-size:{font_size}px;color:#333;">{name}</td></tr>'
    num_cols = len(headers)
    html += '<tr>'
    for i, h in enumerate(headers):
        cw = col_widths[i] if i < len(col_widths) else 60
        align = 'left' if i == 0 else 'right'
        border_l = 'border-left:1px solid #000;' if i == 0 else ''
        border_r = 'border-right:1px solid #000;' if i == num_cols - 1 else ''
        html += f'<td style="background-color:#4a7ebb;color:#fff;font-weight:bold;padding:2px 5px;font-size:{header_font}px;text-align:{align};width:{cw}px;{border_l}{border_r}">{h}</td>'
    html += '</tr>'
    last_ri = len(rows) - 1
    for ri, row_data in enumerate(rows):
        bg = '#f8f9fa' if ri % 2 == 0 else '#ffffff'
        html += f'<tr style="background-color:{bg};">'
        border_bot = 'border-bottom:1px solid #000;' if ri == last_ri else 'border-bottom:1px solid #e8e8e8;'
        for ci, cell in enumerate(row_data):
            fmt = col_formats[ci] if ci < len(col_formats) else 'raw'
            formatted = format_number(cell, fmt)
            cw = col_widths[ci] if ci < len(col_widths) else 60
            align = 'left' if ci == 0 else 'right'
            color = 'color:#cc0000;' if is_negative_display(cell) else ''
            border_l = 'border-left:1px solid #000;' if ci == 0 else ''
            border_r = 'border-right:1px solid #000;' if ci == num_cols - 1 else ''
            html += f'<td style="padding:1px 5px;font-size:{font_size}px;text-align:{align};{color}{border_bot}{border_l}{border_r}white-space:nowrap;width:{cw}px;">{formatted}</td>'
        html += '</tr>'
    html += '</table>'
    return html


def build_preview(report_type, loader, start_date, end_date, data_override=None):
    """Build an absolute-positioned preview matching the canvas layout."""
    return _render_layout_body(report_type, loader, start_date, end_date,
                               data_override=data_override)


def compute_email_width(layout_config):
    """Calculate the pixel width of the widest row in the email layout."""
    tables_def = layout_config.get("tables", {})
    layout_items = layout_config.get("layout", [])
    settings = layout_config.get("settings", {})
    default_gap = settings.get("default_table_gap", 4)

    rows = grid_to_rows(layout_items, default_gap)
    max_width = 0
    for row in rows:
        row_width = 0
        for i, item in enumerate(row["tables"]):
            tbl_id = item["id"]
            tbl_def = tables_def.get(tbl_id, {})
            row_width += sum(tbl_def.get("col_widths", [80]))
            if i < len(row["tables"]) - 1:
                row_width += item.get("gap", default_gap)
        max_width = max(max_width, row_width)
    return max_width

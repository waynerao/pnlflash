# Project Specification: PnL Flash

## 1. Executive Summary

PnL Flash is a high-fidelity reporting engine designed to aggregate financial data from various internal sources (KDB+, S3, internal APIs) and generate professional HTML email reports. The system provides a Flask Web UI for manual triggers, report previews, and utilizes a simple token-based security model for intranet access.

## 2. Technical Stack

- **Backend**: Python 3.12, uv for environment management
- **Web UI**: Flask (manual triggers, report previews, multi-user access)
- **Templating**: Jinja2 (configured for Outlook-compatible HTML)
- **Security**: Simple token per user defined in TOML config (no expiry, no database)
- **Config**: TOML format for environment-specific variables (recipients, tokens, settings)
- **Deployment**: Run as a Python script on Windows intranet

## 3. Books & Data Model

The system tracks three trading books:

| Book | Full Name | Type |
|------|-----------|------|
| **APCR** | Apac Central Risk | Central Risk |
| **JPCR** | Japan Central Risk | Central Risk |
| **SL** | Systematic Liquidity | Systematic |

### Relationships

- APCR and JPCR are both **Central Risk (CR)** books with similar structures but different regions.
- SL is a **Systematic Liquidity** book with its own unique tables.
- Some tables aggregate across all three books; some aggregate only the two CR books.

## 4. Report Types

### 4A. Daily PnL Email (Graph 1)

Outlook-compatible HTML email with dense, professional "financial terminal" aesthetic.

#### Aggregate Tables (All 3 Books: APCR + JPCR + SL)

| Table | Description |
|-------|-------------|
| **Systematic Cash Trading PnL** | TD / MTD / YTD per book, with totals |
| **Portfolio Metrics** | Risk metrics aggregated across all books |
| **PAA By Region** | P&L attribution by region (HK, SG, CN, JP, etc.) |

#### Per-Book Tables

| Table | APCR | JPCR | SL |
|-------|------|------|----|
| Flow | APCR Flow | JPCR Flow | SL Flow |
| Factor Risk | APCR Factor Risk | JPCR Factor Risk | SL Factor Risk |
| Spec Risk | APCR Spec Risk | JPCR Spec Risk | SL Spec Risk |
| Net Platform Value | APCR NPV | JPCR NPV | — |
| Top 10 P&L & Positions | — | — | SL Top 10 |

#### CR Aggregate Tables (APCR + JPCR Only)

| Table | Description |
|-------|-------------|
| **CR PAA By Strategy** | PAA breakdown by strategy for Central Risk |
| **CR Flow & PAA By Source and Desk** | Flow and PAA by source and desk for CR |

### 4B. Monthly PAA Email (Graph 2)

Vertical attribution blocks per book. Columns: Month name / Year-to-Date.

#### APCR Sections
- **PCG PNL**: Total with Month and YTD
- **Attribution by Node**: APCR_MAIN, APCR_INVENTORY, APCR_FUNDING, APCR_SPARE
- **APCR Main Attribution**: Tracking Error HK/SG/CN, PBMM HK/CN
- **APCR Inventory Attribution**: HSI, HSCEI, HSTECH, A50
- **Platform Contribution**: Stamp Saving, IOI Commission, Follow On Commission, EIC Saving (Internal)
- **Risk**: Gross, Risk

#### JPCR Sections
- **PCG PNL**: Total with Month and YTD
- **Attribution by Node**: JPCR_MAIN, JPCR_INVENTORY, JPCR_SPARE
- **JPCR Main Attribution**: Tracking Error JP, CR IOI, LH Japan, CMatch
- **JPCR Inventory Attribution**: NKY, TPX, EFP
- **Platform Contribution**: HT Commission, Follow On Commission, EIC Saving (Internal), EIC Saving (Agency)
- **Risk**: Gross, Risk

#### SL Sections
- **PCG PNL**: Total with Month and YTD
- **Attribution by Node**: APSL_AU, APSL_CN, APSL_HK, APSL_SG, APSL_FEE, APSL_SPARE
- **Risk**: Gross, Risk

#### Bottom Aggregate Sections
- **Market**: HK, CN, SG gross figures
- **Index Inventory**: HSI, HSCEI, HSTECH, A50 gross totals

### 4C. Weekly PAA Email

Same structure as Monthly PAA (4B) but with weekly date ranges instead of monthly.

## 5. Email Engineering

- **Layout (Email)**: Email body uses a 2D grid `<table>` with `colspan` and `rowspan` to reproduce the canvas layout. `_render_email_body()` in `email_builder.py` converts absolute canvas positions into a unified HTML table grid — compatible with Outlook Desktop (Word rendering engine).
- **Layout (Preview)**: Browser preview uses absolute-positioned `<div>` containers (`position:absolute`) for pixel-perfect canvas matching. `_render_layout_body()` handles this path.
- **Dual rendering**: `build_email()` calls `_render_email_body()` (table-based); `build_preview()` calls `_render_layout_body()` (absolute-positioned). Both produce visually similar output from the same layout config.
- **Non-breaking spaces**: All cell content uses `&nbsp;` instead of regular spaces to prevent text wrapping in Outlook's constrained column widths.
- **Styling**: All CSS inlined.
- **Visual Design**:
  - Blue headers (`#4a7ebb`)
  - Alternating row colors for readability
  - Red text for negative values, displayed in parentheses (e.g., `(10K)`)
  - Black borders on left/right of each table, black bottom border on last data row
  - Compact, professional "financial terminal" aesthetic
- **Number Formatting**: K suffix for thousands, mm suffix for millions, parentheses for negatives

## 6. Security & Access

- **Token System**: Each authorized user has a unique token defined in the TOML config file.
- **No Expiry**: Tokens are persistent and do not expire.
- **No Database**: Token validation is done by checking against the config file at runtime.
- **Access Pattern**: Users access the Web UI via `http://<host>:<port>/?token=<user_token>`.

## 7. Web UI (Flask)

### 7A. Tab Structure

Four tabs: **Daily PnL Flash** | **Monthly PAA** | **Weekly PAA** | **Layout Config**

### 7B. Data Sources & Loading

Three independent data sources:

| Source | Data | Used By | Notes |
|--------|------|---------|-------|
| **KDB+ (DNA Data)** | All data except PnL | All 3 tabs | Loaded per tab independently |
| **S3 (Hist PnL)** | Historical PnL by account | All 3 tabs | Shared across tabs; may not include T-1 |
| **Internal API (Live PnL)** | Real-time PnL | Daily PnL only | Today's live numbers |

#### Auto-Load Behavior

- All tabs auto-load DNA data on initial page load (Daily PnL also loads Live PnL and Hist PnL).
- Two configurable timestamps in TOML trigger an automatic **second reload** after the configured time:
  - `s3_reload_after` — auto-reload S3 Hist PnL after this time
  - `realtime_reload_after` — auto-reload Live PnL after this time
- Auto-reload happens **once** on page load (not polling).

#### S3 Hist PnL — T-1 Availability

- S3 always returns data, but may not yet include the last business day (T-1).
- The UI shows a clear status: whether T-1 data is present or not.
- If T-1 is missing, user can:
  - Click `[Load Hist PnL]` to retry later.
  - Enter manual adjustment per book in the Adjustment Table (Daily PnL tab only).

#### Adjustment Table (Daily PnL Tab Only)

- One adjustment value per book (APCR / JPCR / SL) — book-level override, not account-level.
- The adjustment represents the manually entered T-1 PnL value.
- Impact rules:
  - **TD**: Never impacted (TD comes from Live PnL).
  - **MTD**: Impacted unless T-1 is the last day of the prior month (i.e., today is the first day of a month).
  - **YTD**: Impacted unless T-1 is the last day of the prior year (i.e., today is the first day of a year).

### 7C. Daily PnL Flash Tab

```
[Date picker]

Status:
  ✓ DNA loaded (08:31)                     [Load DNA Data]
  ✓ Live PnL loaded (08:31)                [Load Live PnL]
  ✓ Hist PnL loaded - latest: 02 Apr 2026  [Load Hist PnL]
  -- or --
  ⚠ T-1 Hist PnL not available             [Load Hist PnL]

Adjustment Table:
  APCR: [___]    JPCR: [___]    SL: [___]

--- Data Tables (all cells editable, changed cells highlighted) ---

[Reset]  [Send Email]
```

### 7D. Monthly PAA Tab

```
[Period picker (month)]

Status:
  ✓ DNA loaded (08:31)                     [Load DNA Data]
  ✓ Hist PnL loaded - latest: 02 Apr 2026  [Load Hist PnL]

--- Data Tables (all cells editable, changed cells highlighted) ---

[Reset]  [Send Email]
```

### 7E. Weekly PAA Tab

```
[Period picker (week)]

Status:
  ✓ DNA loaded (08:31)                     [Load DNA Data]
  ✓ Hist PnL loaded - latest: 02 Apr 2026  [Load Hist PnL]

--- Data Tables (all cells editable, changed cells highlighted) ---

[Reset]  [Send Email]
```

### 7F. Email Send Flow (Two-Step Confirmation)

Clicking `[Send Email]` on any tab opens a **Preview Window** (modal or new page) with:

```
+-------------------------------------------------+
| Email Preview                                   |
+-------------------------------------------------+
| Subject: [Systematic Cash Trading PnL 20260403] | (editable)
| To:      [team@internal.com]                    | (editable)
| CC:      [manager@internal.com]                 | (editable)
+-------------------------------------------------+
|                                                 |
| (rendered HTML email content — read-only)       |
|                                                 |
+-------------------------------------------------+
|                        [Cancel]  [Confirm Send]  |
+-------------------------------------------------+
```

- **Subject, To, CC** fields are pre-filled from TOML config but editable before sending.
- **Email content** is the fully rendered HTML — read-only in preview.
- `[Confirm Send]` triggers the actual email send.
- `[Cancel]` returns to the tab without sending.
- This two-step flow prevents accidental sends from a misclick.

### 7G. Editable Data Tables

- All cells in data tables are editable (click to edit).
- Manually changed cells are highlighted (e.g., yellow background).
- Original value shown as **tooltip on hover**.
- Edits are preserved when switching between tabs.
- `[Reset]` button reverts all manual edits back to loaded data.

### 7I. Portfolio Metrics Auto-Save

- Every time Daily PnL data is loaded (or reloaded), the **Portfolio Metrics** table is saved to a CSV file.
- File name: `YYYYMMDD.csv` (based on the selected reporting date).
- Save path: Configurable in TOML config (`[output] portfolio_metrics_path`).
- Always overwrites with the latest data for that date.

### 7J. Layout Config Tab

Integrated as a tab in the dashboard (alongside Daily PnL Flash, Monthly PAA, Weekly PAA). Protected by a shared password defined in `config.toml` — entered once per browser session (stored in `sessionStorage`).

Controls **email layout only** — the dashboard data tables layout is not affected.

One layout config per report type (Daily PnL / Monthly PAA / Weekly PAA), each edited independently.

#### Table Definitions

Each table is defined with:

| Field | Description | Example |
|-------|-------------|---------|
| **Name** | Display title in email | `"APCR Factor Risk"` |
| **Data function** | Function name built into the project | `get_apcr_factor_risk` |
| **Function params** | Dict of parameters to pass | `{"book": "APCR"}` |
| **Column formats** | Scale per column: `raw`, `K`, `mm` | `["raw", "K", "K"]` |
| **Column widths** | Pixel width per column | `[80, 60, 60]` |
| **Column headers** | Optional override for column header names | `["", "TD", "MTD", "YTD"]` |
| **Display rows** | Number of rows to display (pad or truncate) | `10` |

- Column headers default to the data function return values, but can be overridden via `col_headers`.
- `col_widths` drives column count: fewer entries than data columns truncates columns, more entries pads with empty columns.
- `display_rows` controls the exact number of rows shown: pads with empty rows if data is short, truncates if data exceeds.
- To add new data functions, a developer adds the function to the project code. Setup page only references existing functions.
- Users can add, edit, and delete table definitions.

#### Layout Configuration (Free-Form Canvas)

Tables are arranged on a **free-form canvas** with absolute pixel positioning and mouse-based drag:

| Field | Description | Example |
|-------|-------------|---------|
| **x** | Horizontal pixel position on canvas | `304` |
| **y** | Vertical pixel position on canvas | `10` |

- Table pixel width is the sum of its `col_widths`.
- Tables can be placed anywhere on the canvas without row or grid constraints.
- PowerPoint-style alignment guide lines appear when dragging (snap to other table edges within 5px).
- At email render time, `_render_email_body()` converts canvas positions into a 2D grid table with `colspan`/`rowspan` for Outlook compatibility. Tables sharing vertical space use `rowspan`; tables sharing horizontal space use `colspan`. Gap columns and rows are real grid cells.
- Backward compatible: detects old grid format (small integer y values) vs pixel format (large y values).

Global layout settings:

| Field | Description | Default |
|-------|-------------|---------|
| **Row gap** | Vertical gap between rows in email (px) | `4` |
| **Table gap** | Horizontal gap between tables in email (px) | `4` |
| **Font size** | Font size for all table text (px), header font = max(font_size-1, 8) | `11` |

#### Data Functions

- Data functions are registered in `data_functions.py` and referenced by name in layout config.
- Each function takes `(loader, start_date, end_date, params)` and returns `{"headers": [...], "rows": [[...]]}`.
- All dates are `YYYY-MM-DD` strings:
  - Daily: `start_date == end_date == selected date`
  - Monthly: `start_date = first weekday of month`, `end_date = last weekday of month`
  - Weekly: `start_date = Monday`, `end_date = Friday`
- Per-build cache (`_get_data()`) ensures `loader.load_dna_data()` is called once per `(start_date, end_date, report_type)`, shared across all tables in the same build cycle.
- Column formats and widths must match the output shape of the data function.

#### Layout Example (Daily PnL — Graph 1)

```
y=0:  [Systematic Cash Trading PnL w=6] [Portfolio Metrics w=10] [APCR Factor Risk w=4] [APCR Spec Risk w=4]
y=8:  [APCR NPV w=5] [CR PAA By Strategy w=6] [PAA By Region w=5] [JPCR Factor Risk w=4] [JPCR Spec Risk w=4]
y=17: [JPCR NPV w=5] [CR Flow PAA w=6] [SL Flow w=5]
y=25: [APCR Flow w=5] [SL Top 10 w=7] [SL Factor Risk w=4] [SL Spec Risk w=4]
y=38: [JPCR Flow w=5]
```

#### Persistence

- Layout configs saved as JSON files: `layouts/daily_pnl.json`, `layouts/monthly_paa.json`, `layouts/weekly_paa.json`.
- Layout JSON stores: `settings`, `tables` (definitions), `layout` (flat array of `{id, x, y}`).
- `settings.table_order` array persists the table definitions list ordering.
- Email templates are **data-driven** — a single generic template (`email_generic.html`) renders any layout from its JSON config.
- The `get_table_formats()` in `app.py` reads column formats from layout JSON.

#### Layout Config Tab UI

Integrated as a tab in the dashboard. Pure CSS/JS implementation (no external libraries).

```
[Daily PnL Flash] [Monthly PAA] [Weekly PAA] [Layout Config]

[Password field] [Report Type: Daily PnL v] [Load]

--- Table Definitions (drag to reorder) ---
[+ Add Table] [Save Order]
| ID | Name | Function | Rows | Col Formats | Col Widths | [Edit] [Del] |

--- Email Layout (free-form canvas, drag to move, alignment guides) ---
Row Gap: [4]px   Table Gap: [4]px   Font Size: [11]px   [Apply]

+---------------------+  +---------------------------+  +--------+  +--------+
| Syst Cash Trading   |  | Portfolio Metrics          |  | APCR   |  | APCR   |
| PnL (rendered HTML) |  | (rendered HTML)            |  | Factor |  | Spec   |
+---------------------+  +---------------------------+  +--------+  +--------+

[Select table v] [+ Add to Layout]

[Save]
```

- **Apply** button re-renders all tables server-side with current font_size, repositions with current gaps, and auto-saves.

Canvas drag snapping:
- Vertical: 9px increments (half a row height of 18px)
- Horizontal: 5px increments
- Alignment guide snap overrides grid snap when within 5px of another table edge

#### Table Borders

All tables have black borders:
- Left border on first column, right border on last column (header + data rows)
- Black bottom border on last data row
- Title row above blue headers has no border

#### Send Email Preview

The Send Email button (on Flash/PAA tabs) opens a modal with:
- Editable Subject, To, CC fields (pre-filled from config per report type)
- Email body rendered with absolute-positioned tables matching the canvas layout exactly (`build_preview()`)
- Modal auto-sizes to fit content (bounding box calculated from layout positions)
- Actual email sent via `build_email()` uses 2D grid table with colspan/rowspan for Outlook compatibility
- Sent emails saved as `.eml` files (openable directly in Outlook)

### 7H. General UI Features

- **Multi-User**: Supports up to ~10 concurrent users on intranet.
- Reports are triggered manually — not automated by cron.
- All email sends go through the two-step preview/confirm flow.

## 8. Data Architecture

- **BaseLoader Interface**: Abstract base class defining the data loading contract.
- **Mock Data**: Initial implementation uses mock CSV/JSON data inferred from reference graphs.
- **Future Integration**: Real data loaders for KDB+, S3, internal APIs to be implemented later, conforming to the BaseLoader interface.

## 9. Configuration (TOML)

```toml
[app]
host = "0.0.0.0"
port = 5000

[tokens]
user1 = "abc123"
user2 = "def456"

[schedule]
s3_reload_after = "08:30"
realtime_reload_after = "07:00"

[email]
smtp_host = "smtp.internal.com"
smtp_port = 25
from_address = "pnlflash@internal.com"

[email.subjects]
daily_pnl = "Systematic Cash Trading PnL"
monthly_paa = "Monthly PAA Report"
weekly_paa = "Weekly PAA Report"
# Rendered as: "Systematic Cash Trading PnL 20260403"

[email.recipients.daily_pnl]
to = ["team@internal.com"]
cc = ["manager@internal.com"]

[email.recipients.monthly_paa]
to = ["team@internal.com"]
cc = ["manager@internal.com"]

[email.recipients.weekly_paa]
to = ["team@internal.com"]
cc = ["manager@internal.com"]

[output]
portfolio_metrics_path = "C:/data/portfolio_metrics"
```

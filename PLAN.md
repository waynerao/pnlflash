# PnL Flash — Implementation Plan

## Phase 1: Project Scaffolding & Config

- [x] Update spec.md with finalized requirements
- [x] Initialize uv project (`pyproject.toml`, dependencies)
- [x] Create TOML config file (`config.toml`) with all sections
- [x] Create `config.py` to load and expose TOML config as constants
- [x] Create project directory structure

### Target Structure

Repo root holds docs and project metadata; all source code lives under `pnlflash/`.

```
.                           # repo root
├── PLAN.md
├── spec.md
├── pyproject.toml
├── uv.lock
├── .python-version
├── .gitignore
└── pnlflash/               # application source
    ├── app.py              # Flask app entry point
    ├── config.py           # Config loader (reads config.toml)
    ├── config.toml         # TOML configuration
    ├── base_loader.py      # Abstract BaseLoader interface
    ├── mock_loader.py      # Mock data implementation
    ├── email_builder.py    # HTML email generation
    ├── email_sender.py     # Stub email sending
    ├── formatter.py        # Financial number formatting helpers
    ├── data_functions.py   # Registry of named data functions
    ├── templates/
    │   ├── layout.html         # Base Flask UI layout
    │   ├── dashboard.html      # Main dashboard with all tabs (incl. Layout Config)
    │   └── email_generic.html  # (unused; legacy row-based template)
    ├── static/
    │   └── style.css       # Flask UI styles
    ├── layouts/            # per-report layout JSONs
    ├── mock_data/          # mock JSON datasets
    └── output/             # generated previews/sent emails (gitignored)
```

Run from repo root: `uv run python pnlflash/app.py`

## Phase 2: Mock Data & Data Loader

- [x] Define `BaseLoader` abstract class with methods:
  - `load_dna_data(date)` — KDB+ data (everything except PnL)
  - `load_hist_pnl(date)` — S3 historical PnL (shared across tabs)
  - `load_live_pnl(date)` — Internal real-time PnL (Daily only)
- [x] Create mock JSON data files matching Graph 1 and Graph 2 structures
- [x] Implement `MockLoader` that reads from JSON files
- [x] Verify data shapes with simple test scripts

### Data Structures

**Daily PnL data keys:**
- `systematic_cash_trading_pnl` — per book (APCR/JPCR/SL), columns: TD/MTD/YTD
- `portfolio_metrics` — aggregated risk metrics
- `paa_by_region` — region breakdown (HK, SG, CN, JP)
- `{book}_flow` — flow table per book
- `{book}_factor_risk` — factor risk per book
- `{book}_spec_risk` — spec risk per book
- `apcr_net_platform_value` — APCR NPV
- `jpcr_net_platform_value` — JPCR NPV
- `cr_paa_by_strategy` — CR aggregate
- `cr_flow_paa_by_source_desk` — CR aggregate
- `sl_top10_pnl_positions` — SL specific

**Monthly/Weekly PAA data keys (per book):**
- `{book}_pcg_pnl` — total with period/YTD
- `{book}_attribution_by_node` — node-level attribution
- `{book}_main_attribution` — main attribution detail (CR books only)
- `{book}_inventory_attribution` — inventory attribution detail (CR books only)
- `{book}_platform_contribution` — platform contribution (CR books only)
- `{book}_risk` — gross and risk
- `market` — market gross figures
- `index_inventory` — index inventory totals

### Hist PnL & Adjustment Logic

- S3 Hist PnL is stored by account level per book
- System checks if T-1 business day data is present
- If T-1 missing, user enters book-level adjustment in Adjustment Table
- Adjustment impact rules:
  - TD: never impacted
  - MTD: impacted unless today is first day of month
  - YTD: impacted unless today is first day of year

## Phase 3: Email Templates (Jinja2, Outlook-Compatible)

- [x] Create `formatter.py` — financial number formatting:
  - K suffix for thousands, mm suffix for millions
  - Parentheses for negatives with red text
  - Consistent decimal places
- [x] Build `email_daily_pnl.html` — table-based layout matching Graph 1
  - All CSS inlined
  - Blue headers (#4a7ebb), alternating rows, red negatives in parens
  - Dense grid: aggregate tables top, per-book sections below
- [x] Build `email_monthly_paa.html` — vertical blocks matching Graph 2
  - Three columns: APCR, JPCR, SL
  - Each with stacked attribution sections
  - Bottom: Market and Index Inventory
- [x] Build `email_weekly_paa.html` — same as monthly, weekly date range
- [x] Create `email_builder.py` — renders templates with data from loader
  - Applies formatter to all numeric values
  - Adds email subject with YYYYMMDD suffix from config

## Phase 4: Flask Web UI

- [x] Create `app.py` with Flask routes:
  - `GET /?token=<token>` — dashboard (validate token from config)
  - `POST /load/<source>` — load DNA / Hist PnL / Live PnL data
  - `POST /preview` — render email preview
  - `POST /send` — trigger email send (stubbed)
- [x] Token validation middleware (check token against config.toml)
- [x] Server-side data cache:
  - DNA data: per-tab independent
  - Hist PnL: shared across all tabs
  - Live PnL: Daily tab only
  - Auto-load all sources on page load
  - Auto-reload after configured timestamps (once, not polling)
- [x] Build `dashboard.html` with three tabs:
  - **Daily PnL Flash**: Date picker, status with load buttons, adjustment table, data tables, [Reset] + [Send Email]
  - **Monthly PAA**: Month picker, status with load buttons, data tables, [Reset] + [Send Email]
  - **Weekly PAA**: Week picker, status with load buttons, data tables, [Reset] + [Send Email]
- [x] Editable data tables:
  - All cells clickable and editable
  - Changed cells highlighted (yellow background)
  - Original value shown as tooltip on hover
  - Edits preserved across tab switches
  - `[Reset]` button reverts all edits to loaded data
- [x] Build email preview window (modal or page):
  - Shows Subject, To, CC fields (pre-filled from config, editable)
  - Shows rendered HTML email content (read-only)
  - `[Confirm Send]` triggers actual send
  - `[Cancel]` returns to tab without sending
  - Two-step flow prevents accidental sends
- [x] Portfolio Metrics auto-save:
  - On each Daily PnL data load/reload, save Portfolio Metrics to `YYYYMMDD.csv`
  - Path from config (`[output] portfolio_metrics_path`)
  - Overwrites with latest data for that date
- [x] Static CSS for the UI (clean, minimal — separate from email styles)

## Phase 5: Email Sending (Stub)

- [x] Create `email_sender.py` with `send_email(html, subject, to, cc)` interface
- [x] Subject, To, CC come from the preview window (user may have edited them)
- [x] Stub implementation: log the send, save HTML to local file for inspection
- [x] Email subject default = config subject + " YYYYMMDD" (e.g., "Systematic Cash Trading PnL 20260403")
- [x] SMTP settings read from config.toml (for future real implementation)

## Phase 6: Testing & Polish

- [ ] Test email templates render correctly (visual inspection)
- [ ] Test token validation (valid/invalid/missing)
- [ ] Test mock data loading
- [ ] Test adjustment table logic (TD/MTD/YTD impact rules)
- [ ] Test editable cells (highlight, tooltip, reset)
- [ ] Test auto-reload timing logic
- [ ] Verify Outlook compatibility (table layouts, inlined CSS)
- [ ] End-to-end: load → edit → preview → send flow

## Phase 7: Data Functions & Layout Infrastructure

- [x] Create `data_functions.py` — registry of named data functions
  - Each function takes `(loader, date, params)` and returns a dict with headers/rows
  - 18 functions for all existing tables (daily PnL, monthly/weekly PAA)
  - Registered in `DATA_FUNCTIONS` dict
- [x] Create `layouts/` directory
- [x] Define JSON schema for layout config:
  - `tables`: dict of table definitions (name, function, params, col_formats, col_widths)
  - `layout`: list of rows, each row has `tables` list of `{id, gap}`
  - `settings`: row_gap, default_table_gap
- [x] Create default layout JSON files for all 3 report types
- [x] Build generic email template `email_generic.html` that renders from layout JSON
  - Independent table widths via col_widths, configurable gaps per table
- [x] Update `email_builder.py` to use layout JSON + data functions
- [x] Replace hardcoded `get_table_formats()` in `app.py` with layout-driven version

## Phase 8: Setup Page UI

- [x] Add `setup_password` to config.toml and config.py
- [x] Build Layout Config tab in dashboard (integrated, no separate page)
  - Report type selector, password field
  - Table definitions section: add/edit/delete tables (name, function, params, col_formats, col_widths)
  - Layout section with WYSIWYG canvas editor
  - Global settings: row_gap, default_table_gap
- [x] Preview button: renders email using current setup config (via `/setup/preview`)
- [x] Save button: writes layout JSON to `layouts/<report_type>.json` (via `/setup/save`)
- [ ] Auto-recommend: when adding a table, suggest row/order/widths based on content (deferred)

## Phase 9: Grid Layout & Transpose

- [x] Convert layout JSON format from row-based to grid-based
  - Layout now stores flat array of `{id, x, y, w, h}` per table
  - `x/y` = grid position, `w/h` = grid span (24-column grid, 20px cell height)
  - Updated all 3 layout files (daily_pnl, monthly_paa, weekly_paa)
- [x] Update `email_builder.py` with `grid_to_rows()` conversion
  - Groups items by y-coordinate, sorts by x within each row
  - Backward compatible: detects old row format and passes through
  - Email template unchanged — still renders row-based HTML for Outlook
- [x] Layout editor evolved from GridStack.js to free-form canvas (now integrated as tab)
  - Server returns `dimensions` (pixel width + row count) per table via setup/load endpoint
- [x] Add `transpose_table()` function to `data_functions.py`
  - Swaps rows and columns for transposed display
  - Used by `get_portfolio_metrics()` with `transpose: true` param
  - Updated daily_pnl.json col_formats/col_widths for transposed shape (7 cols × 4 rows)

## Phase 10: WYSIWYG Free-Form Layout Editor

- [x] Replace GridStack.js with free-form canvas (CSS absolute positioning + mouse events)
  - Tables displayed as actual rendered HTML (same style as email output)
  - Fixed-width container matching email body pixel width
  - Free-form drag to move tables anywhere on the canvas (no row/grid constraints)
  - PowerPoint-style alignment guide lines when dragging (snap to other table edges within 5px)
- [x] Add `render_single_table()` to `email_builder.py`
  - Renders individual table HTML matching email template style
  - Used by setup/load endpoint to provide per-table previews
- [x] Add `compute_email_width()` to `email_builder.py`
  - Calculates widest row pixel width from col_widths + gaps
  - Returned by setup/load endpoint for fixed-width container
- [x] Update `grid_to_rows()` for pixel-based y-proximity clustering
  - Auto-detects pixel mode (y > 20) vs grid mode (small integers)
  - Clusters items within 30px y-gap into the same row for email rendering
- [x] Display rows control (`display_rows` field)
  - Pad empty rows with `\u00a0` when data rows < display_rows
  - Truncate rows when data rows > display_rows
  - Editable in Edit Table modal, persisted in layout JSON
  - Applied in both `render_single_table()` and `email_generic.html` template
- [x] Column truncation & padding (`_apply_display_cols()`)
  - `col_widths` drives column count: fewer = truncate, more = pad
  - Supports optional `col_headers` override for padded column names
  - Applied in both `render_single_table()` and `email_generic.html` template
- [x] Table definitions reordering
  - HTML5 drag-and-drop to reorder table definitions list
  - "Save Order" button persists `table_order` array in settings
- [x] Edit Table modal with comprehensive fields
  - Name, Display Rows, Position (X/Y), Function, Params, Col Headers, Col Formats, Col Widths
  - Auto-saves layout and re-renders table on save
- [x] ~~Full Email Preview as popup modal~~ (removed — Send Email preview serves this purpose)
- [x] Update setup/load endpoint to return rendered_tables and email_width
- [x] `/setup/render_table` endpoint for re-rendering individual tables after edits
- [x] Grid snapping for canvas drag
  - Vertical: 9px increments (half a row height)
  - Horizontal: 5px increments
  - Alignment guide snap still takes priority when within 5px of another table edge

## Phase 11: Layout Config Tab Integration

- [x] Merge setup page into dashboard as "Layout Config" tab
  - Removed standalone `/setup` route and `templates/setup.html`
  - Layout Config is now a tab alongside Daily PnL Flash, Monthly PAA, Weekly PAA
  - Same styling and switching behavior as other tabs
  - No "Back to Dashboard" button needed
- [x] Password persistence via `sessionStorage`
  - Password entered once, remembered for the browser session
  - Used automatically for all layout API calls (load, save, render_table, auto-save)
  - Cleared from input field after successful authentication
- [x] Updated dashboard route to pass layout config template variables
  - `data_functions` now passed from dashboard route

## Phase 12: Preview, Formatting & Polish

- [x] Send Email preview uses absolute positioning (matching canvas layout)
  - `build_preview()` renders absolute-positioned HTML instead of row-based
  - `/preview` endpoint uses `build_preview()`, `/send` still uses `build_email()` (row-based for Outlook)
  - Preview modal auto-sizes to content (bounding box calculated from layout positions)
  - Replaced iframe with div (`modal-preview-body`) for inline HTML rendering
- [x] Removed Full Email Preview from Layout Config tab (redundant with Send Email preview)
  - Removed `openPreviewModal()`, `closePreviewModal()`, preview modal HTML
  - Removed `/setup/preview` route from app.py
- [x] Black borders on all tables
  - Left border on first column, right border on last column (header + data rows)
  - Black bottom border on last data row
  - Title row above blue headers has no border
  - Applied in both `render_single_table()` and `email_generic.html`
- [x] Removed transpose from portfolio_metrics
  - `get_portfolio_metrics()` returns raw shape directly (no transpose)
  - Removed `transpose_table()` usage; layout config updated to match raw 5-col shape
- [x] Global settings improvements
  - Renamed "Default Table Gap" to "Table Gap"
  - Added `font_size` setting (saved in layout JSON `settings.font_size`, default 11)
  - Font size propagated through all rendering paths: `render_single_table()`, `build_preview()`, `build_email()`, `email_generic.html`
  - Header font = `max(font_size - 1, 8)`
- [x] "Apply" button replaces "Auto Layout"
  - Re-renders all tables server-side with current `font_size`
  - Keeps existing table positions (no repositioning)
  - Saves gap/font settings to layout JSON
- [x] Removed unused files and routes
  - Deleted `templates/setup.html`
  - Removed `/setup` page route
  - Removed `/setup/preview` route
  - Removed `static/style.css` `.email-preview-frame` class
  - Removed `EMAIL_SUBJECTS` and `EMAIL_RECIPIENTS` JS constants from dashboard

## Phase 13: Data Functions & Date Range Refactor

- [x] Removed `transpose_table()` from `data_functions.py` (no longer used)
- [x] Added per-build data cache (`_get_data()` / `clear_cache()`)
  - Caches `loader.load_dna_data()` by `(start_date, end_date, report_type)` key
  - Multiple tables sharing the same dataset only trigger one loader call
  - `clear_cache()` called at start of `build_email()` and `build_preview()`
- [x] Replaced `report_date` with `start_date` / `end_date` across all layers
  - JS `getDateRange(reportType)` computes weekday-bounded ranges from picker values
  - Daily: start = end = selected date
  - Monthly: first weekday of month → last weekday of month
  - Weekly: Monday → Friday of selected week
  - All dates are `YYYY-MM-DD` strings throughout
  - Updated: data functions, `BaseLoader`, `MockLoader`, `email_builder`, `app.py` routes, dashboard JS
- [x] Fixed PAA tab email preview (monthly/weekly layouts used small grid integers)
  - Added `_grid_to_pixel_positions()` to convert grid layout to pixel positions for preview
  - `build_preview()` auto-detects grid vs pixel format and converts accordingly
- [x] Auto-load PAA tabs on page load (monthly/weekly DNA data loads alongside daily)
- [x] Added fallback handling in `getDateRange()` for browsers that don't support `<input type="week">`

## Phase 14: Unified Email Rendering

- [x] Email body now uses absolute-positioned layout matching the canvas/preview
  - Extracted `_render_layout_body()` helper as single source of truth
  - `build_email()` wraps it in `<!DOCTYPE><html><body>`; `build_preview()` returns it directly
  - Editor/preview/sent email all render identically
  - Note: `position:absolute` has limited support in Outlook Desktop (Word renderer); test before relying on Outlook
- [x] `email_generic.html` template is now unused (kept for reference, can be deleted)

## Build Order

Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5 → Phase 6 → Phase 7 → Phase 8 → Phase 9 → Phase 10 → Phase 11 → Phase 12 → Phase 13 → Phase 14

## Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Framework | Flask | Simple routing, native Jinja2, good for token URLs and multi-user |
| Config format | TOML | Clean, readable, supports nested sections |
| Auth | Token in TOML | No DB, no expiry — simplest approach for intranet |
| Data | Mock JSON | Build templates first, plug in real loaders later |
| Email | Stub sender | Focus on HTML generation; real SMTP later |
| Env | uv | User's preferred Python environment tool |
| Hist PnL | Shared across tabs | Single S3 load, all tabs read from same cache |
| DNA Data | Per-tab independent | Each tab loads its own DNA data |
| Auto-reload | Once on page load | After configured timestamp, not polling |
| Cell editing | All cells editable | Yellow highlight + tooltip for original value |

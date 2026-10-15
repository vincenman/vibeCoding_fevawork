# Prompt: Build a SQLite database for HK stock screening

Build a single Python script that creates a local SQLite database for HK stock screening.

## Goal

From the universe file `HSI_Constituents_yfinance_v2.xlsx`, load each Hang Seng Index constituent into SQLite using the schema below, then download the last 1 year of daily bars from yfinance and store them.

## Schema (exact column names — do not rename)

### `instruments`

| Column | Type | Notes |
| --- | --- | --- |
| `instrument_id` | INTEGER PRIMARY KEY AUTOINCREMENT | Identifies the row |
| `symbol` | TEXT UNIQUE NOT NULL | yfinance ticker, e.g. `0700.HK` |
| `name` | TEXT | English name from the Excel |
| `chinese_name` | TEXT | Chinese name from the Excel |
| `exchange` | TEXT | `HKEX` |
| `sector` | TEXT | from the Excel Sector column |
| `listing_status` | TEXT | `active` |
| `listed_at` | TEXT | NULL if unknown |

### `daily_bars`

| Column | Type | Notes |
| --- | --- | --- |
| `bar_id` | INTEGER PRIMARY KEY AUTOINCREMENT | Identifies the row |
| `instrument_id` | INTEGER NOT NULL | REFERENCES `instruments(instrument_id)` |
| `trade_date` | TEXT NOT NULL | ISO date `YYYY-MM-DD` |
| `close` | REAL | |
| `volume` | INTEGER | |
| `avg_volume_20d` | REAL | 20-session trailing average of volume |
| | UNIQUE(`instrument_id`, `trade_date`) | one bar per stock per day |

`UNIQUE` means the database itself rejects duplicates:

- `instruments.symbol` → one row per ticker
- `(instrument_id, trade_date)` → one bar per stock per day

## Input file

- Path: `HSI_Constituents_yfinance_v2.xlsx`
- Sheet: `HSI Constituents`

Columns (use these headers exactly):

- `Stock code (yfinance)`
- `Stock name`
- `Chinese name`
- `Sector`

Map them as:

| Excel column | Database column |
| --- | --- |
| Stock code (yfinance) | `instruments.symbol` |
| Stock name | `instruments.name` |
| Chinese name | `instruments.chinese_name` |
| Sector | `instruments.sector` |

Do **not** convert tickers. They are already in yfinance format (4-digit code + `.HK`), e.g. `0005.HK`, `0700.HK`, `9988.HK`.

Universe size: 93 Hang Seng Index constituents (effective 8 June 2026).  
Skip blank rows. Skip the Notes sheet.

## Phased implementation

### Phase 1 — Project setup

- One script, e.g. `build_hk_sqlite.py`
- Dependencies: `pandas`, `yfinance`, `openpyxl`
- Output DB: `hk_stocks.sqlite` in the same folder
- Logging to console: progress, skips, failures
- Idempotent: if the DB exists, upsert instruments by symbol and replace bars for that symbol (or skip already-loaded symbols unless `--refresh` is set)

### Phase 2 — Create schema

- `CREATE TABLE IF NOT EXISTS` for both tables, including `name` and `chinese_name`
- Indexes: `daily_bars(instrument_id, trade_date)`, `instruments(symbol)`

### Phase 3 — Load universe from Excel

- Read sheet `HSI Constituents` with pandas
- Drop rows with empty `Stock code (yfinance)`
- Insert/upsert into `instruments`: `symbol`, `name`, `chinese_name`, `sector`, `exchange='HKEX'`, `listing_status='active'`
- Use `INSERT ... ON CONFLICT(symbol) DO UPDATE` so re-running refreshes names and sector without duplicating tickers

### Phase 4 — Download 1 year of daily data

- Period: last 365 calendar days from today (or `period="1y"` in yfinance)
- Fields needed: date, close, volume
- Use `Close` consistently (not Adj Close unless documented)
- Batch in groups of 20–30 tickers to reduce rate limits
- Sleep 0.5–1s between batches
- Skip tickers that return empty frames
- Print a summary of successes vs failures
- If a ticker fails, log it and continue; never abort the whole run

### Phase 5 — Write bars + 20-day average volume

- For each symbol, sort by date
- `avg_volume_20d = volume.rolling(20, min_periods=1).mean()`
- Insert rows into `daily_bars` linked by `instrument_id`
- Do not insert duplicate `(instrument_id, trade_date)`
- On conflict, replace the existing bar (so `--refresh` works)

### Phase 6 — Validation + sample query

At the end print:

- number of instruments
- number of daily_bars
- date min/max
- run this check query and print the first 10 rows:

```sql
SELECT i.symbol, i.name, i.chinese_name, i.sector,
       b.trade_date, b.close, b.volume, b.avg_volume_20d
FROM instruments i
JOIN daily_bars b ON b.instrument_id = i.instrument_id
WHERE b.trade_date = (SELECT MAX(trade_date) FROM daily_bars)
  AND b.close > 50
  AND b.volume > b.avg_volume_20d
ORDER BY b.volume DESC
LIMIT 10;
```

That query is the sample screen: last available bar, close > 50, volume above the 20-day average.

## Constraints

- Do not invent extra tables.
- Do not require an API key.
- Handle network errors per ticker.
- Use `if __name__ == "__main__"` and argparse with:
  - `--excel`
  - `--db`
  - `--period` (default `1y`)
  - `--refresh`
- Include a short docstring at the top explaining usage.

Generate the complete script only.  
No notebook.  
No extra README unless a 5-line usage comment is inside the script.

## How to run after the script is generated

```bash
pip install pandas yfinance openpyxl
python build_hk_sqlite.py --excel HSI_Constituents_yfinance_v2.xlsx --db hk_stocks.sqlite
```

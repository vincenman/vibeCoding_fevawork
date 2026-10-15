"""
Read AASTOCKS export, normalize HK tickers for yfinance, and build a price table.
"""

from pathlib import Path

import pandas as pd
import yfinance as yf

EXCEL_PATH = Path(r"C:/temp/AASTOCKS_Export_2025-7-13.xlsx")


def strip_leftmost_zero(code: str) -> str:
    """Remove the leftmost leading zero from an AAStocks ticker (e.g. 00388.HK -> 0388.HK)."""
    code = str(code).strip()
    if "." in code:
        num, suffix = code.split(".", 1)
        if num.startswith("0") and len(num) > 1:
            num = num[1:]
        return f"{num}.{suffix}"
    if code.startswith("0") and len(code) > 1:
        return code[1:]
    return code


def ticker_candidates(code: str) -> list[str]:
    """Build Yahoo ticker candidates: strip one leading zero, then keep stripping if needed."""
    primary = strip_leftmost_zero(code)
    candidates = [primary]
    if "." in primary:
        num, suffix = primary.split(".", 1)
        while num.startswith("0") and len(num) > 1:
            num = num[1:]
            alt = f"{num}.{suffix}"
            if alt not in candidates:
                candidates.append(alt)
    return candidates


def fetch_price_and_return(ticker: str) -> tuple[float | None, float | None]:
    """Return (latest close, daily return %) for a Yahoo Finance ticker."""
    try:
        hist = yf.Ticker(ticker).history(period="5d")
        if hist is None or hist.empty or "Close" not in hist.columns:
            return None, None

        closes = hist["Close"].dropna()
        if closes.empty:
            return None, None

        latest = float(closes.iloc[-1])
        if len(closes) < 2:
            return latest, None

        prev = float(closes.iloc[-2])
        if prev == 0:
            return latest, None

        daily_return_pct = (latest - prev) / prev * 100.0
        return latest, daily_return_pct
    except Exception as exc:
        print(f"Warning: failed to fetch {ticker}: {exc}")
        return None, None


def resolve_ticker_and_data(code: str) -> tuple[str, float | None, float | None]:
    """Try ticker candidates until price data is found."""
    candidates = ticker_candidates(code)
    for ticker in candidates:
        close, daily_ret = fetch_price_and_return(ticker)
        if close is not None:
            return ticker, close, daily_ret
    return candidates[0], None, None


def main() -> None:
    df = pd.read_excel(EXCEL_PATH, usecols=["名稱", "代號"])
    df = df.dropna(subset=["代號"]).copy()
    df["代號"] = df["代號"].astype(str).str.strip()
    df["名稱"] = df["名稱"].astype(str).str.strip()

    rows = []
    for _, row in df.iterrows():
        ticker, close, daily_ret = resolve_ticker_and_data(row["代號"])
        rows.append(
            {
                "Stock code": ticker,
                "Stock name": row["名稱"],
                "Latest close price": close,
                "Daily return (%)": round(daily_ret, 4) if daily_ret is not None else None,
            }
        )

    result = pd.DataFrame(rows)
    result = result.sort_values(
        by="Daily return (%)", ascending=False, na_position="last"
    ).reset_index(drop=True)

    pd.set_option("display.max_rows", None)
    pd.set_option("display.width", None)
    pd.set_option("display.unicode.east_asian_width", True)
    print(result.to_string(index=False))

    out_path = Path(r"C:/temp/stock_result.xlsx")
    result.to_excel(out_path, index=False, sheet_name="Stock Data")
    print(f"\nSaved result to {out_path}")


if __name__ == "__main__":
    main()

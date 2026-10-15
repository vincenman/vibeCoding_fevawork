import sys
import yfinance as yf


def get_latest_close(ticker: str) -> None:
    stock = yf.Ticker(ticker)
    hist = stock.history(period="5d")

    if hist.empty:
        print(f"No data found for ticker: {ticker}")
        return

    latest = hist["Close"].iloc[-1]
    date_str = hist.index[-1].strftime("%Y-%m-%d")
    print(f"{ticker.upper()} latest close: ${latest:.2f} (as of {date_str})")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python stock_price.py <TICKER>")
        print("Example: python stock_price.py AAPL")
        sys.exit(1)

    get_latest_close(sys.argv[1])
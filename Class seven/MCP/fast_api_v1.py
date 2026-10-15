# -*- coding: utf-8 -*-
"""
Created on Fri Sep 26 09:46:51 2025

@author: user
"""

import yfinance as yf
from fastapi import FastAPI, Request, HTTPException

app = FastAPI(title="Mini MCP Server")


# --- Minimal tool registry: name -> callable ---
def tool_get_market_data(args):
    """Fetch the latest daily close price for a stock ticker via yfinance."""
    symbol = str(args.get("symbol", "")).strip().upper()
    if not symbol:
        raise HTTPException(400, "Missing required field: symbol")

    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="5d")
    except Exception as exc:
        raise HTTPException(502, f"Failed to fetch market data for {symbol}: {exc}") from exc

    if hist.empty or "Close" not in hist.columns:
        raise HTTPException(404, f"No market data found for symbol: {symbol}")

    last_row = hist.iloc[-1]
    close = float(last_row["Close"])
    as_of = hist.index[-1].date().isoformat()

    currency = None
    try:
        info = ticker.info or {}
        currency = info.get("currency") or info.get("financialCurrency")
    except Exception:
        currency = None
    if not currency:
        try:
            currency = getattr(ticker.fast_info, "currency", None)
        except Exception:
            currency = None

    return {
        "symbol": symbol,
        "close": round(close, 2),
        "last": round(close, 2),
        "as_of": as_of,
        "currency": currency or "UNKNOWN",
    }


def tool_place_order(args):
    # No real side effects here—just echo back what would be placed
    required = ["symbol", "side", "quantity", "order_type"]
    missing = [k for k in required if k not in args]
    if missing:
        raise HTTPException(400, f"Missing fields: {missing}")
    return {
        "status": "submitted",
        "order_id": "PAPER-123456",
        **args,
    }


TOOL_META = {
    "get_market_data": {
        "description": "Get the latest daily stock close price for a ticker symbol (Yahoo Finance).",
        "args": {
            "symbol": {
                "type": "string",
                "required": True,
                "description": "Stock ticker symbol, e.g. AAPL, MSFT, TSLA",
            }
        },
    },
    "place_order": {
        "description": "Submit a paper trading order (simulated; no real brokerage).",
        "args": {
            "symbol": {"type": "string", "required": True},
            "side": {"type": "string", "required": True, "description": "buy or sell"},
            "quantity": {"type": "number", "required": True},
            "order_type": {"type": "string", "required": True, "description": "e.g. market, limit"},
        },
    },
}

TOOLS = {
    "get_market_data": tool_get_market_data,
    "place_order": tool_place_order,
}


@app.get("/tools")
def list_tools():
    return [
        {"name": name, **TOOL_META.get(name, {"description": fn.__name__})}
        for name, fn in TOOLS.items()
    ]


@app.post("/call")
async def call_tool(req: Request):
    body = await req.json()
    tool = body.get("tool")
    args = body.get("args", {}) or {}
    if tool not in TOOLS:
        raise HTTPException(404, f"Unknown tool: {tool}")
    return TOOLS[tool](args)


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)

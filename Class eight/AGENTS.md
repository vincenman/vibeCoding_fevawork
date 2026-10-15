# AGENTS.md

Teaching-oriented web scraping project with two entry points and n8n automation workflows.

## Project structure

| File | Role |
|---|---|
| `IT_news_update_v6(students).py` | Standalone script: scrapes HKET tech news, summarizes via Azure OpenAI GPT-4o-mini, outputs to `result_YYYYMMDD.txt` |
| `news_app.py` | FastAPI server (`POST /scrape-latest-news`, `GET /health`) that scrapes Google News RSS articles with Selenium + BeautifulSoup |
| `Daily News Summary_Telegram.json` | n8n workflow: hits the FastAPI server, formats + summarizes via Azure OpenAI agent, sends to Telegram (1 article) |
| `Daily News Summary_multiple_telegram.json` | n8n workflow: same pipeline but 2 articles with richer summarization prompt |
| `Web scraping with Python_students_25032025.ipynb` | Teaching notebook |
| `*.pptx`, `*.pdf` | Course slides |

## Commands

```bash
# Run the standalone HKET scraper
python "IT_news_update_v6(students).py"

# Start the FastAPI server (port 8787)
uvicorn news_app:app --host 127.0.0.1 --port 8787

# Get latest stock close price
python stock_price.py <TICKER>
```

## Stock price lookup

When asked for a stock price (any ticker, e.g. "what's AAPL price", "check 0700.HK"):
- Use `stock_price.py` — run `python stock_price.py <TICKER>`
- For Hong Kong stocks, append `.HK` (e.g. Tencent = `0700.HK`)
- Common ticker mappings: Tencent=0700.HK, Alibaba=9988.HK, Meituan=3690.HK, HSBC=0005.HK
- Run the script and return the price to the user

## Dependencies

The standalone script requires: `selenium`, `webdriver-manager`, `openai`, `beautifulsoup4`, `pandas`. Telegram is optional (import is guarded).

The FastAPI server additionally requires: `fastapi`, `pydantic`, `feedparser`, `uvicorn`.

## Architecture notes

- **Both scripts spin up their own Selenium Chrome driver** — they do not share a driver instance.
- `IT_news_update_v6(students).py` uses a visible browser (non-headless) with anti-detection flags. `news_app.py` uses `--headless=new` mode.
- **Hardcoded Azure OpenAI credentials** in `IT_news_update_v6(students).py` line 46 — do not commit these to a public repo.
- The n8n workflows expect the FastAPI server running at `http://127.0.0.1:8787`.
- The Telegram `chat_id` in the n8n JSON files (`727270924`) and the `TOKEN`/`chat_id` in the standalone script are empty/hardcoded — they are example values.

## Gotchas

- `telegram` import will fail if not installed. The script has a try/except guard now, but if you revert that change, `pip install python-telegram-bot` is needed even when Telegram isn't used.
- `IT_news_update_v6(students).py` overwrites `result_YYYYMMDD.txt` in the working directory each run.
- The HKET scraper depends on specific CSS class names (`main-component`, `template-default`, `listing-title`, etc.). If HKET changes their HTML, the scraper breaks.
- `IT_news_update_v6(students).py` was originally authored for macOS (`user-agent` says `Macintosh`). Running on Windows uses `ChromeDriverManager` auto-download.
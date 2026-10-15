"""
Reporting engine CLI (thin wrapper around backend modular service).

Edit the USER INPUTS block below, then run:
    python reporting_engine.py
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

from app.services.reporting import run_report_async  # noqa: E402

# ---------------------------------------------------------------------------
# USER INPUTS — set these at the start of the script
# ---------------------------------------------------------------------------

# Folder containing the input Markdown (.md) files
MD_FOLDER = ROOT / "MD_files"

# Optional: process only these filenames inside MD_FOLDER.
# Leave empty to process every .md file in the folder.
INPUT_MD_FILES: list[str] = []

# Location and name of the exported Excel file
EXCEL_OUTPUT_PATH = ROOT / "OCR_report_v1.xlsx"

# Telegram bot credentials (optional; can also be set in .env)
TELEGRAM_BOT_TOKEN = ""
TELEGRAM_CHAT_ID = ""


async def _main_async() -> None:
    result = await run_report_async(
        md_folder=MD_FOLDER,
        excel_path=EXCEL_OUTPUT_PATH,
        filenames=INPUT_MD_FILES or None,
        send_telegram=True,
        telegram_token=TELEGRAM_BOT_TOKEN or None,
        telegram_chat_id=TELEGRAM_CHAT_ID or None,
    )

    print(f"MD folder: {MD_FOLDER}")
    print(f"Files ({len(result.source_files)}): {', '.join(result.source_files)}")
    print(f"Model: {result.model}")
    print(f"Excel: {result.excel_path}")
    for row in result.rows:
        print(
            f"  {row.get('source_filename')}: "
            f"invoice_no={row.get('invoice_no')}  total_due={row.get('total_due')}"
        )
    print(f"Saved {result.row_count} row(s) to {result.excel_path}")
    print(result.telegram_message)


def main() -> None:
    asyncio.run(_main_async())


if __name__ == "__main__":
    main()

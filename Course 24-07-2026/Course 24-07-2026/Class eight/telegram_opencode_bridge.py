import os
import sys
import asyncio
import logging
import platform

from dotenv import load_dotenv
load_dotenv()

import httpx
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("telegram-opencode")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ALLOWED_USERS = set(
    int(uid.strip())
    for uid in os.getenv("TELEGRAM_ALLOWED_USERS", "").split(",")
    if uid.strip()
)
OPENCODE_URL = os.getenv("OPENCODE_SERVER_URL", "http://127.0.0.1:4096").rstrip("/")
OPENCODE_PASSWORD = os.getenv("OPENCODE_SERVER_PASSWORD", "")
OPENCODE_USERNAME = os.getenv("OPENCODE_SERVER_USERNAME", "opencode")

WORKING_DIR = os.path.dirname(os.path.abspath(__file__))

if not TELEGRAM_BOT_TOKEN:
    logger.error("TELEGRAM_BOT_TOKEN not set in .env")
    sys.exit(1)


def auth():
    if OPENCODE_PASSWORD:
        return httpx.BasicAuth(username=OPENCODE_USERNAME, password=OPENCODE_PASSWORD)
    return None


def is_allowed(user_id: int) -> bool:
    if not ALLOWED_USERS:
        return True
    return user_id in ALLOWED_USERS


async def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if not is_allowed(user_id):
        await update.message.reply_text("Access denied. You are not an allowed user.")
        return

    await update.message.reply_text(
        "OpenCode Telegram Bridge is running.\n\n"
        "Send any message and I'll forward it to OpenCode.\n\n"
        "Commands:\n"
        "/new — start a new OpenCode session\n"
        "/status — check session status\n"
    )
    context.user_data.setdefault("session_id", None)


async def new_session(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if not is_allowed(user_id):
        return

    status_msg = await update.message.reply_text("Creating new session...")

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{OPENCODE_URL}/session",
                json={"title": f"Telegram session from {user_id}"},
                auth=auth(),
            )
            if resp.status_code == 200:
                data = resp.json()
                context.user_data["session_id"] = data["id"]
                await status_msg.edit_text(f"New session created: `{data['id']}`")
            elif resp.status_code == 422 and "no active project" in resp.text.lower():
                await status_msg.edit_text(
                    "No active project. Start OpenCode in the project directory first.\n\n"
                    f"Example: `cd \"{WORKING_DIR}\" && opencode serve`"
                )
            else:
                await status_msg.edit_text(f"Failed to create session: {resp.status_code} {resp.text[:200]}")
    except httpx.ConnectError:
        await status_msg.edit_text(
            f"Cannot connect to OpenCode server at {OPENCODE_URL}\n\n"
            "Make sure `opencode serve` is running."
        )
    except Exception as e:
        await status_msg.edit_text(f"Error: {e}")


async def status(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if not is_allowed(user_id):
        return

    session_id = context.user_data.get("session_id")
    if not session_id:
        await update.message.reply_text("No active session. Use /new first.")
        return

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                f"{OPENCODE_URL}/session/{session_id}",
                auth=auth(),
            )
            if resp.status_code == 200:
                data = resp.json()
                await update.message.reply_text(
                    f"Session: `{session_id}`\nTitle: {data.get('title', 'N/A')}\nMessages: {len(data.get('messages', []))}"
                )
            else:
                await update.message.reply_text(f"Error: {resp.status_code}")
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")


async def handle_message(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if not is_allowed(user_id):
        return

    text = update.message.text
    if not text:
        return

    session_id = context.user_data.get("session_id")
    if not session_id:
        await update.message.reply_text("No active session. Use /new to create one first.")
        return

    logger.info(f"User {user_id}: {text[:100]}")

    thinking_msg = await update.message.reply_text("Thinking...")

    try:
        async with httpx.AsyncClient(timeout=300) as client:
            resp = await client.post(
                f"{OPENCODE_URL}/session/{session_id}/message",
                json={"parts": [{"type": "text", "text": text}]},
                auth=auth(),
            )
            if resp.status_code == 200:
                data = resp.json()
                reply_text = extract_reply(data)
                if reply_text:
                    await send_long_message(update, reply_text)
                else:
                    await thinking_msg.edit_text("Done. (Check project for changes.)")
            else:
                await thinking_msg.edit_text(f"OpenCode error: {resp.status_code}\n{resp.text[:500]}")

    except httpx.ReadTimeout:
        await thinking_msg.edit_text("OpenCode is taking too long. It may still be processing. Check the TUI or wait and retry.")
    except httpx.ConnectError:
        await thinking_msg.edit_text("Lost connection to OpenCode server. Is `opencode serve` still running?")
    except Exception as e:
        await thinking_msg.edit_text(f"Error: {e}")
        logger.exception("Unexpected error")


def extract_reply(data: dict) -> str:
    parts = data.get("parts", [])
    texts = []
    for part in parts:
        if part.get("type") == "text":
            texts.append(part.get("text", ""))
        elif part.get("type") == "tool_use":
            tool_name = part.get("name", "unknown")
            tool_input = part.get("input", {})
            texts.append(f"\U0001f6e0 *[{tool_name}]* `{str(tool_input)[:200]}`")
        elif part.get("type") == "tool_result":
            result = part.get("content", "")
            preview = str(result)[:300]
            if len(str(result)) > 300:
                preview += "..."
            texts.append(f"\u2192 {preview}")

    return "\n\n".join(texts) if texts else ""


async def send_long_message(update: Update, text: str):
    max_len = 4000
    if len(text) <= max_len:
        await update.message.reply_text(text)
        return

    for i in range(0, len(text), max_len):
        chunk = text[i:i + max_len]
        await update.message.reply_text(chunk)


async def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("new", new_session))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Starting Telegram-OpenCode bridge...")
    logger.info(f"OpenCode server: {OPENCODE_URL}")
    logger.info(f"Allowed users: {ALLOWED_USERS or 'ALL'}")

    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    logger.info("Bridge is running. Send messages to your bot on Telegram.")
    await asyncio.Event().wait()  # run forever


if __name__ == "__main__":
    if platform.system() == "Windows":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
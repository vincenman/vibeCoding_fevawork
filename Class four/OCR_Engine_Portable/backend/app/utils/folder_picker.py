"""Native folder picker for local desktop deployments."""

from __future__ import annotations

import asyncio
import platform
import subprocess
from concurrent.futures import ThreadPoolExecutor

_executor = ThreadPoolExecutor(max_workers=1)


def _pick_folder_macos() -> str | None:
    script = 'POSIX path of (choose folder with prompt "Select OCR output folder")'
    result = subprocess.run(
        ["osascript", "-e", script],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def _pick_folder_tkinter() -> str | None:
    import tkinter as tk
    from tkinter import filedialog

    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    try:
        folder = filedialog.askdirectory(title="Select OCR output folder")
    finally:
        root.destroy()
    return folder or None


def pick_output_folder_sync() -> str | None:
    """Open a native folder dialog and return the selected path, or None if cancelled."""
    if platform.system() == "Darwin":
        return _pick_folder_macos()
    return _pick_folder_tkinter()


async def pick_output_folder() -> str | None:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(_executor, pick_output_folder_sync)

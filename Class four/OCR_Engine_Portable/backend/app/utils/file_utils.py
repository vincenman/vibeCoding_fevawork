import re
from pathlib import Path

ALLOWED_MIME_TYPES = {
    "image/png",
    "image/jpeg",
    "image/webp",
    "image/tiff",
    "application/pdf",
}

ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".tiff", ".tif", ".pdf"}


def sanitize_filename(filename: str) -> str:
    """Remove path components and unsafe characters from a filename."""
    name = Path(filename).name
    name = re.sub(r"[^\w.\- ]", "_", name)
    return name or "upload"


def get_file_type(filename: str, content_type: str | None = None) -> str:
    ext = Path(filename).suffix.lower()
    if ext == ".pdf" or content_type == "application/pdf":
        return "pdf"
    return "image"


def is_allowed_file(filename: str, content_type: str | None = None) -> bool:
    ext = Path(filename).suffix.lower()
    if ext in ALLOWED_EXTENSIONS:
        return True
    if content_type and content_type in ALLOWED_MIME_TYPES:
        return True
    return False

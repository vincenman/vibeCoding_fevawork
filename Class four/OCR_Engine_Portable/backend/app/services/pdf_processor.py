"""PDF page rendering — adapted from OCR_minimal_Azure_v4.ipynb."""

from pathlib import Path

import pymupdf


def pdf_to_png_bytes(pdf_path: str | Path, dpi: int = 200) -> list[bytes]:
    """Render each PDF page to PNG bytes."""
    zoom = dpi / 72.0
    matrix = pymupdf.Matrix(zoom, zoom)
    pages: list[bytes] = []
    with pymupdf.open(pdf_path) as doc:
        for page in doc:
            pix = page.get_pixmap(matrix=matrix, alpha=False)
            pages.append(pix.tobytes("png"))
    return pages


def get_pdf_page_count(pdf_path: str | Path) -> int:
    with pymupdf.open(pdf_path) as doc:
        return len(doc)

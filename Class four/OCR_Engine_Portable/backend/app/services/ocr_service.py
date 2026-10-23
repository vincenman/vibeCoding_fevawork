"""OCR orchestration service — combines PDF/image processing with provider calls."""

from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Callable

from app.config import settings
from app.models.schemas import FileOCRResult, JobProgress
from app.services import azure_client, openrouter_client
from app.services.md_export_service import export_results_to_md
from app.services.pdf_processor import get_pdf_page_count, pdf_to_png_bytes
from app.utils.file_utils import get_file_type
from app.utils.path_utils import normalize_output_folder
from app.utils.prompts import DEFAULT_OCR_PROMPT

_executor = ThreadPoolExecutor(max_workers=2)

ProgressCallback = Callable[[JobProgress], None]


def _emit(on_progress: ProgressCallback | None, progress: JobProgress) -> None:
    if on_progress:
        on_progress(progress)


async def _ocr_png(png_bytes: bytes, model: str, prompt: str) -> str:
    if settings.ocr_provider == "openrouter":
        return await openrouter_client.ocr_png_bytes(png_bytes, model, prompt)
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        _executor, azure_client.ocr_png_bytes, png_bytes, model, prompt
    )


async def ocr_pdf_file(
    pdf_path: Path,
    model: str,
    prompt: str,
    dpi: int,
    on_progress: ProgressCallback | None = None,
    *,
    file_index: int = 1,
    total_files: int = 1,
    filename: str = "",
) -> tuple[str, int]:
    """OCR all pages of a PDF. Returns (combined_text, page_count)."""
    loop = asyncio.get_event_loop()
    pages: list[bytes] = await loop.run_in_executor(
        _executor, pdf_to_png_bytes, pdf_path, dpi
    )
    results: list[str] = []
    page_count = len(pages)

    for i, png in enumerate(pages, 1):
        page_fraction = (i - 0.5) / max(page_count, 1)
        file_fraction = (file_index - 1 + page_fraction) / max(total_files, 1)
        percent = max(5, min(85, int(file_fraction * 85)))
        page_label = f" (page {i}/{page_count})" if page_count > 1 else ""
        _emit(
            on_progress,
            JobProgress(
                stage="processing",
                current_file=file_index,
                total_files=total_files,
                current_filename=filename,
                current_page=i,
                total_pages=page_count,
                percent=percent,
                message=f"OCR processing {filename}{page_label}…",
            ),
        )

        text = await _ocr_png(png, model, prompt)
        if page_count == 1:
            results.append(text)
        else:
            results.append(f"## Page {i}\n\n{text}")

    return "\n\n".join(results), page_count


async def ocr_image_path(image_path: Path, model: str, prompt: str) -> tuple[str, int]:
    png_bytes = image_path.read_bytes()
    text = await _ocr_png(png_bytes, model, prompt)
    return text, 1


async def process_single_file(
    file_path: Path,
    original_filename: str,
    model: str,
    prompt: str = DEFAULT_OCR_PROMPT,
    on_progress: ProgressCallback | None = None,
    *,
    file_index: int = 1,
    total_files: int = 1,
) -> FileOCRResult:
    file_type = get_file_type(original_filename)
    try:
        if file_type == "pdf":
            text, page_count = await ocr_pdf_file(
                file_path,
                model,
                prompt,
                settings.ocr_dpi,
                on_progress,
                file_index=file_index,
                total_files=total_files,
                filename=original_filename,
            )
        else:
            file_fraction = (file_index - 0.5) / max(total_files, 1)
            percent = max(5, min(85, int(file_fraction * 85)))
            _emit(
                on_progress,
                JobProgress(
                    stage="processing",
                    current_file=file_index,
                    total_files=total_files,
                    current_filename=original_filename,
                    current_page=1,
                    total_pages=1,
                    percent=percent,
                    message=f"OCR processing {original_filename}…",
                ),
            )
            text, page_count = await ocr_image_path(file_path, model, prompt)

        return FileOCRResult(
            filename=original_filename,
            success=True,
            text=text,
            page_count=page_count,
        )
    except Exception as exc:
        page_count = None
        if file_type == "pdf":
            try:
                page_count = get_pdf_page_count(file_path)
            except Exception:
                pass
        return FileOCRResult(
            filename=original_filename,
            success=False,
            error=str(exc),
            page_count=page_count,
        )


async def process_job_files(
    job_id: str,
    saved_files: list[tuple[Path, str]],
    output_folder: str,
    on_progress: ProgressCallback | None = None,
) -> tuple[list[FileOCRResult], list[str], str | None]:
    """Process all files and export successful results as .md files."""
    model = settings.effective_model
    results: list[FileOCRResult] = []
    total_files = len(saved_files)

    _emit(
        on_progress,
        JobProgress(
            stage="processing",
            current_file=0,
            total_files=total_files,
            percent=0,
            message=f"Starting OCR for {total_files} file(s)…",
        ),
    )

    for index, (file_path, original_name) in enumerate(saved_files, 1):
        result = await process_single_file(
            file_path,
            original_name,
            model,
            on_progress=on_progress,
            file_index=index,
            total_files=total_files,
        )
        results.append(result)

        completed_fraction = index / max(total_files, 1)
        _emit(
            on_progress,
            JobProgress(
                stage="processing",
                current_file=index,
                total_files=total_files,
                current_filename=original_name,
                percent=min(85, int(completed_fraction * 85)),
                message=f"Finished {original_name} ({index}/{total_files})",
            ),
        )

    md_files: list[str] = []
    export_error: str | None = None

    _emit(
        on_progress,
        JobProgress(
            stage="exporting",
            current_file=total_files,
            total_files=total_files,
            percent=90,
            message="Saving Markdown files…",
        ),
    )

    try:
        folder = normalize_output_folder(output_folder)
        md_files, export_error = export_results_to_md(folder, results)
    except Exception as exc:
        export_error = str(exc)

    _emit(
        on_progress,
        JobProgress(
            stage="completed",
            current_file=total_files,
            total_files=total_files,
            percent=100,
            message="OCR job completed",
        ),
    )

    return results, md_files, export_error

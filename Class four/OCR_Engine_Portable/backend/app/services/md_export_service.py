"""Save OCR results as Markdown files in the output folder."""

from pathlib import Path

from app.models.schemas import FileOCRResult


def md_filename_for_source(source_filename: str) -> str:
    return f"{Path(source_filename).stem}.md"


def save_md_file(output_folder: Path, source_filename: str, text: str) -> Path:
    """Write OCR text to {source_stem}.md in the output folder."""
    md_path = output_folder / md_filename_for_source(source_filename)
    md_path.write_text(text, encoding="utf-8")
    return md_path


def export_results_to_md(
    output_folder: Path,
    results: list[FileOCRResult],
) -> tuple[list[str], str | None]:
    """
    Save successful OCR results as .md files.
    Returns (list of saved file paths, error message if any write failed).
    """
    saved_paths: list[str] = []
    errors: list[str] = []

    for result in results:
        if not result.success or not result.text:
            continue
        try:
            md_path = save_md_file(output_folder, result.filename, result.text)
            saved_paths.append(str(md_path))
            result.md_path = str(md_path)
        except OSError as exc:
            errors.append(f"{result.filename}: {exc}")

    export_error = "; ".join(errors) if errors else None
    return saved_paths, export_error

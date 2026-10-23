from pathlib import Path

from app.config import settings


class PathValidationError(ValueError):
    pass


def normalize_output_folder(path_str: str) -> Path:
    """Validate and resolve an output folder path."""
    if not path_str or not path_str.strip():
        raise PathValidationError("Output folder path is required")

    raw = path_str.strip()
    if ".." in raw:
        raise PathValidationError("Path traversal (..) is not allowed")

    resolved = Path(raw).expanduser().resolve()

    allowed = settings.allowed_base_dirs
    if allowed and not any(resolved == base or base in resolved.parents for base in allowed):
        raise PathValidationError(
            f"Output folder must be under one of: {', '.join(str(b) for b in allowed)}"
        )

    if not resolved.exists():
        if settings.create_output_folder_if_missing:
            resolved.mkdir(parents=True, exist_ok=True)
        else:
            raise PathValidationError(f"Output folder does not exist: {resolved}")

    if not resolved.is_dir():
        raise PathValidationError(f"Path is not a directory: {resolved}")

    test_file = resolved / ".ocr_write_test"
    try:
        test_file.touch()
        test_file.unlink()
    except OSError as exc:
        raise PathValidationError(f"Output folder is not writable: {resolved}") from exc

    return resolved


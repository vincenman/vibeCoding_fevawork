from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, UploadFile

from app.config import settings
from app.models.job import job_store
from app.models.schemas import (
    BrowseFolderResponse,
    JobCreated,
    JobProgress,
    JobStatus,
    JobSummary,
    OCRResult,
    PathValidationRequest,
    PathValidationResponse,
)
from app.services.ocr_service import process_job_files
from app.utils.file_utils import is_allowed_file, sanitize_filename
from app.utils.folder_picker import pick_output_folder
from app.utils.path_utils import PathValidationError, normalize_output_folder

router = APIRouter(prefix="/ocr", tags=["ocr"])


async def _save_uploads(job_id: str, files: list[UploadFile]) -> list[tuple[Path, str]]:
    if len(files) > settings.max_files_per_job:
        raise HTTPException(
            status_code=400,
            detail=f"Maximum {settings.max_files_per_job} files per job",
        )

    job_dir = settings.temp_path / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    saved: list[tuple[Path, str]] = []

    for upload in files:
        if not upload.filename:
            continue

        original_name = sanitize_filename(upload.filename)
        if not is_allowed_file(original_name, upload.content_type):
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {original_name}",
            )

        content = await upload.read()
        if len(content) > settings.max_file_size_bytes:
            raise HTTPException(
                status_code=400,
                detail=f"File too large: {original_name} (max {settings.max_file_size_mb} MB)",
            )

        dest = job_dir / original_name
        dest.write_bytes(content)
        saved.append((dest, original_name))

    if not saved:
        raise HTTPException(status_code=400, detail="No valid files uploaded")

    return saved


def _on_progress(job_id: str, progress: JobProgress) -> None:
    job_store.update_progress(job_id, progress)


async def _run_job(
    job_id: str,
    saved_files: list[tuple[Path, str]],
    output_folder: str,
) -> None:
    job = job_store.get(job_id)
    if not job:
        return

    job.status = JobStatus.PROCESSING
    job_store.update(job)

    try:
        results, md_files, export_error = await process_job_files(
            job_id,
            saved_files,
            output_folder,
            on_progress=lambda progress: _on_progress(job_id, progress),
        )
        job.files = results
        job.md_files = md_files
        job.export_error = export_error
        job.status = JobStatus.COMPLETED
        job.completed_at = datetime.now(timezone.utc)
        job.progress = JobProgress(
            stage="completed",
            current_file=len(saved_files),
            total_files=len(saved_files),
            percent=100,
            message="OCR job completed",
        )
    except Exception as exc:
        job.status = JobStatus.FAILED
        job.completed_at = datetime.now(timezone.utc)
        job.export_error = str(exc)
        job.progress = JobProgress(
            stage="failed",
            current_file=job.progress.current_file,
            total_files=len(saved_files),
            percent=job.progress.percent,
            message=f"Job failed: {exc}",
        )

    job_store.update(job)


@router.post("/upload", response_model=JobCreated)
async def upload_and_ocr(
    background_tasks: BackgroundTasks,
    files: list[UploadFile] = File(...),
    output_folder: str = Form(...),
):
    try:
        normalize_output_folder(output_folder)
    except PathValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    job = job_store.create(file_count=len(files))
    job.output_folder = output_folder
    job.progress = JobProgress(
        stage="uploading",
        total_files=len(files),
        percent=2,
        message="Uploading files…",
    )
    job_store.update(job)

    saved_files = await _save_uploads(job.job_id, files)
    job.file_count = len(saved_files)
    job.progress = JobProgress(
        stage="queued",
        total_files=len(saved_files),
        percent=5,
        message="Upload complete. Starting OCR…",
    )
    job_store.update(job)

    background_tasks.add_task(_run_job, job.job_id, saved_files, output_folder)

    return JobCreated(
        job_id=job.job_id,
        status=JobStatus.PROCESSING,
        file_count=len(saved_files),
    )


@router.post("/folder", response_model=JobCreated)
async def folder_upload_and_ocr(
    background_tasks: BackgroundTasks,
    files: list[UploadFile] = File(...),
    output_folder: str = Form(...),
):
    """Same as upload — browser folder picker sends multiple files."""
    return await upload_and_ocr(background_tasks, files, output_folder)


@router.get("/jobs/{job_id}", response_model=OCRResult)
async def get_job(job_id: str):
    job = job_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job.to_result()


@router.get("/jobs", response_model=list[JobSummary])
async def list_jobs():
    jobs = job_store.list_recent()
    return [
        JobSummary(
            job_id=j.job_id,
            status=j.status,
            file_count=j.file_count,
            created_at=j.created_at,
            completed_at=j.completed_at,
            md_files=j.md_files,
        )
        for j in jobs
    ]


@router.get("/browse-folder", response_model=BrowseFolderResponse)
async def browse_folder():
    """Open a native folder picker on the machine running the backend."""
    try:
        folder = await pick_output_folder()
        if not folder:
            return BrowseFolderResponse(cancelled=True)
        resolved = normalize_output_folder(folder)
        return BrowseFolderResponse(folder_path=str(resolved))
    except PathValidationError as exc:
        return BrowseFolderResponse(error=str(exc))
    except Exception as exc:
        return BrowseFolderResponse(
            error=f"Could not open folder picker: {exc}. "
            "Ensure the backend is running locally with GUI access, or type the path manually."
        )


@router.post("/validate-path", response_model=PathValidationResponse)
async def validate_path(body: PathValidationRequest):
    try:
        resolved = normalize_output_folder(body.output_folder)
        return PathValidationResponse(valid=True, resolved_path=str(resolved))
    except PathValidationError as exc:
        return PathValidationResponse(valid=False, error=str(exc))

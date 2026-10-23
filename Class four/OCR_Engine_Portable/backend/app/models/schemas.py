from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class FileOCRResult(BaseModel):
    filename: str
    success: bool
    text: str | None = None
    structured: dict[str, Any] | None = None
    error: str | None = None
    page_count: int | None = None
    md_path: str | None = None


class JobProgress(BaseModel):
    stage: str = "queued"
    current_file: int = 0
    total_files: int = 0
    current_filename: str | None = None
    current_page: int | None = None
    total_pages: int | None = None
    percent: int = 0
    message: str = "Waiting to start…"


class OCRResult(BaseModel):
    job_id: str
    status: JobStatus
    files: list[FileOCRResult] = Field(default_factory=list)
    created_at: datetime
    completed_at: datetime | None = None
    md_files: list[str] = Field(default_factory=list)
    export_error: str | None = None
    progress: JobProgress | None = None


class JobCreated(BaseModel):
    job_id: str
    status: JobStatus
    file_count: int


class PathValidationRequest(BaseModel):
    output_folder: str


class PathValidationResponse(BaseModel):
    valid: bool
    resolved_path: str | None = None
    error: str | None = None


class BrowseFolderResponse(BaseModel):
    cancelled: bool = False
    folder_path: str | None = None
    error: str | None = None


class JobSummary(BaseModel):
    job_id: str
    status: JobStatus
    file_count: int
    created_at: datetime
    completed_at: datetime | None = None
    md_files: list[str] = Field(default_factory=list)

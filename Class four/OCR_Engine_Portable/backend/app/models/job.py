from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from app.config import settings
from app.models.schemas import FileOCRResult, JobProgress, JobStatus, OCRResult

ProgressCallback = Callable[[JobProgress], None]


@dataclass
class JobRecord:
    job_id: str
    status: JobStatus
    file_count: int
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime | None = None
    files: list[FileOCRResult] = field(default_factory=list)
    md_files: list[str] = field(default_factory=list)
    export_error: str | None = None
    output_folder: str | None = None
    progress: JobProgress = field(default_factory=JobProgress)

    def to_result(self) -> OCRResult:
        return OCRResult(
            job_id=self.job_id,
            status=self.status,
            files=self.files,
            created_at=self.created_at,
            completed_at=self.completed_at,
            md_files=self.md_files,
            export_error=self.export_error,
            progress=self.progress,
        )


class JobStore:
    """Job store with disk persistence so jobs survive server reloads."""

    def __init__(self) -> None:
        self._jobs: dict[str, JobRecord] = {}
        self._dir = settings.temp_path / "job_records"
        self._dir.mkdir(parents=True, exist_ok=True)

    def _record_path(self, job_id: str) -> Path:
        return self._dir / f"{job_id}.json"

    def _persist(self, job: JobRecord) -> None:
        payload = job.to_result().model_dump(mode="json")
        payload["output_folder"] = job.output_folder
        payload["file_count"] = job.file_count
        self._record_path(job.job_id).write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _load(self, job_id: str) -> JobRecord | None:
        path = self._record_path(job_id)
        if not path.exists():
            return None

        payload = json.loads(path.read_text(encoding="utf-8"))
        result = OCRResult.model_validate(payload)
        return JobRecord(
            job_id=result.job_id,
            status=result.status,
            file_count=payload.get("file_count", len(result.files) or 1),
            created_at=result.created_at,
            completed_at=result.completed_at,
            files=result.files,
            md_files=result.md_files,
            export_error=result.export_error,
            output_folder=payload.get("output_folder"),
            progress=result.progress or JobProgress(),
        )

    def create(self, file_count: int) -> JobRecord:
        job_id = str(uuid.uuid4())
        job = JobRecord(
            job_id=job_id,
            status=JobStatus.QUEUED,
            file_count=file_count,
            progress=JobProgress(total_files=file_count, message="Job queued"),
        )
        self._jobs[job_id] = job
        self._persist(job)
        return job

    def get(self, job_id: str) -> JobRecord | None:
        job = self._jobs.get(job_id)
        if job:
            return job

        job = self._load(job_id)
        if job:
            self._jobs[job_id] = job
        return job

    def list_recent(self, limit: int = 20) -> list[JobRecord]:
        jobs: list[JobRecord] = []
        for path in sorted(self._dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
            job = self._load(path.stem)
            if job:
                self._jobs[job.job_id] = job
                jobs.append(job)
            if len(jobs) >= limit:
                break
        return jobs

    def update(self, job: JobRecord) -> None:
        self._jobs[job.job_id] = job
        self._persist(job)

    def update_progress(self, job_id: str, progress: JobProgress) -> None:
        job = self.get(job_id)
        if job:
            job.progress = progress
            self.update(job)


job_store = JobStore()

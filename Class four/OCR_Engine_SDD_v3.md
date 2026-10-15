# Software Design Document (SDD)
**OCR Detection Engine with Web Portal**

**Version:** 3.0  
**Date:** 2026-08-10  
**Status:** Implemented (MVP)  
**Supersedes:** `OCR_Engine_SDD_v2.md`

**Changelog (v3.0):**
- Reflects **implemented** architecture (not draft/planned).
- Markdown (`.md`) export only — Excel output removed.
- **Async background jobs** with frontend polling and live progress bar.
- **Disk-persisted job store** (JSON) so jobs survive process restarts.
- **Native folder Browse** via backend (macOS `osascript`; tkinter fallback).
- **Azure OpenAI** as primary OCR provider (from `OCR_minimal_Azure_v4.ipynb`); OpenRouter as alternative.
- Multi-file / multi-PDF batch processing with per-file and per-page progress.

---

## 1. Introduction

### 1.1 Purpose

This document defines the software design for an **OCR Detection Engine** with a web-based portal. Users select files or folders for OCR processing; the system extracts text from images and PDFs via multimodal vision LLMs; displays results in the browser; and **writes one Markdown (`.md`) file per successfully processed source file** into a **local output folder** specified by the user.

OCR logic is adapted from **`OCR_minimal_Azure_v4.ipynb`** (PDF → PNG pages → Azure OpenAI vision → Markdown).

### 1.2 Scope

**In scope (implemented):**
- React SPA: file/folder upload, output folder selection (type or Browse), progress bar, results viewer, job history
- FastAPI backend: upload handling, async OCR jobs, progress tracking, Markdown export
- OCR for PNG, JPG, WEBP, TIFF, PDF (including multi-page PDFs and multiple invoice PDFs in one job)
- Azure OpenAI vision (primary) and OpenRouter (alternative)
- Job status API with live progress (`percent`, stage, current file/page)
- Output path validation and native folder picker (local desktop deployment)
- Disk-backed job persistence

**Out of scope (v1):**
- User authentication / multi-tenancy
- Real-time collaborative editing
- Full document management system (DMS)
- Mobile native apps
- Structured JSON extraction (schema present; not fully implemented in UI)

### 1.3 Definitions

| Term | Meaning |
|------|---------|
| OCR | Optical Character Recognition — extracting text from images/scanned PDFs |
| VLM | Vision-Language Model (multimodal LLM that can process images) |
| Job | One OCR request (one or more uploaded source files) |
| Output Folder | Server-local directory where `.md` result files are written |
| Results MD | One `{source_stem}.md` file per successfully OCR'd source file |
| Job Store | Component tracking job status, progress, and results (memory + JSON on disk) |

---

## 2. System Overview

### 2.1 High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                     Browser (React SPA)                           │
│  • Output folder: type path OR Browse (native picker via backend)  │
│  • Source upload: drag-drop / Select Files / Select Folder         │
│  • Processing Status: progress bar + file/page messages            │
│  • Results viewer: Plain Text | Markdown Preview | JSON            │
│  • Job history (recent jobs)                                       │
└────────────────────────────┬─────────────────────────────────────┘
                             │ HTTP REST (Vite dev proxy → :8000)
┌────────────────────────────▼─────────────────────────────────────┐
│                     FastAPI Backend (:8000)                         │
│  • POST /ocr/upload → save files, create job, start background OCR │
│  • GET  /ocr/jobs/{id} → poll status + progress + results          │
│  • GET  /ocr/browse-folder → native folder dialog (macOS/Linux)    │
│  • Path validation, temp storage, job store (memory + disk JSON)   │
└────────────┬───────────────────────────────┬───────────────────────┘
             │                               │
    ┌────────▼────────┐            ┌─────────▼─────────┐
    │  Azure OpenAI   │            │  Local Filesystem  │
    │  (primary VLM)  │            │  • /tmp/ocr_jobs/  │
    │  or OpenRouter  │            │    uploads + jobs  │
    └─────────────────┘            │  • user output/    │
                                   │    *.md files      │
                                   └────────────────────┘
```

### 2.2 Technology Stack

| Layer | Technology |
|-------|------------|
| Frontend | React 18, JavaScript, Vite, Tailwind CSS, `react-markdown` |
| Backend | Python 3.11+, FastAPI, Uvicorn |
| OCR / LLM | **Azure OpenAI** vision (primary, `gpt-4o`); **OpenRouter** (alternative) |
| PDF handling | `pymupdf` (fitz) — render pages to PNG |
| Markdown output | Plain file write (`{stem}.md`) |
| Job persistence | JSON files under `{TEMP_DIR}/job_records/` |
| HTTP client (backend) | `openai` SDK (Azure); `httpx` (OpenRouter) |
| Config | `pydantic-settings`, project root `.env` |

### 2.3 Reference Implementation

| Artifact | Role |
|----------|------|
| `OCR_minimal_Azure_v4.ipynb` | Reference for `pdf_to_png_bytes`, Azure vision OCR, multi-PDF batch |
| `backend/app/services/azure_client.py` | Productionized notebook OCR calls |
| `backend/app/services/pdf_processor.py` | PDF page rendering |

---

## 3. Functional Requirements

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-01 | Select one or multiple image files (PNG, JPG, WEBP, TIFF) | Must | Done |
| FR-02 | Select a folder and process all supported files inside | Must | Done |
| FR-03 | Upload PDFs; extract text from all pages | Must | Done |
| FR-04 | Process **multiple PDF invoices** in one job | Must | Done |
| FR-05 | Perform OCR and return extracted text to UI | Must | Done |
| FR-06 | Results in UI: plain text + rendered Markdown + JSON | Must | Done |
| FR-07 | Copy / download OCR result from UI | Must | Done |
| FR-08 | **Live progress bar** with stage, file name, page, percent | Must | Done |
| FR-09 | User specifies **local output folder path** | Must | Done |
| FR-10 | **Browse button** opens native folder picker (via backend) | Must | Done |
| FR-11 | After OCR, save **one `.md` file per source file** in output folder | Must | Done |
| FR-12 | Markdown filename = source stem (e.g. `invoice.pdf` → `invoice.md`) | Must | Done |
| FR-13 | Configurable OCR provider/model via `.env` | Should | Done |
| FR-14 | Job history list (recent jobs) | Could | Done |
| FR-15 | Validate output folder exists and is writable | Should | Done |
| FR-16 | Optional structured JSON output for forms/invoices | Should | Planned |

---

## 4. Non-Functional Requirements

| Category | Requirement |
|----------|-------------|
| Performance | Single-page OCR ~10–15 s (Azure); multi-file jobs sequential; progress updated during processing |
| Scalability | Single-instance v1; job store design allows DB/queue upgrade later |
| Security | File type whitelist, size limits, path traversal blocked, optional `ALLOWED_OUTPUT_BASE_DIRS` |
| Reliability | Per-file error isolation; failed files don't block others; jobs persisted to disk |
| Usability | Drag-drop, folder pickers, Browse for output, disabled-state hints, `localStorage` for last path |
| Data durability | `.md` files on disk persist after browser session; job JSON survives backend restart |

### 4.1 Local Path Constraint

Browsers **cannot** write arbitrary filesystem paths. The **output folder** must be a path **writable by the FastAPI backend** (same machine in desktop deployment, or mounted volume in container deployment).

**Browse folder:** Because pure browser APIs don't expose full paths, the UI calls `GET /api/v1/ocr/browse-folder`, which opens a **native dialog on the backend host** (macOS: `osascript`; others: tkinter) and returns the selected path.

### 4.2 Backend Reload Warning

Do **not** run Uvicorn with `--reload` during OCR jobs in production-like use. Auto-reload kills in-flight background tasks. Job metadata survives reload (disk JSON), but OCR processing is interrupted. Use:

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

---

## 5. Frontend Design

### 5.1 Application Structure

Single-page application (`frontend/src/`):

```
App.jsx
├── OutputPathForm       # path input, Browse, Validate, localStorage
├── UploadZone           # drag-drop, Select Files, Select Folder
├── ProcessingStatus     # progress bar, stage, file/page, messages
├── ResultsViewer        # Text | Markdown | JSON tabs, copy, download
└── JobHistory           # recent jobs with expandable details
```

### 5.2 Key Behaviours

**Output folder**
- Text input with placeholder (`/home/user/ocr_output` or `C:\OCR_Results`)
- **Browse…** → `GET /ocr/browse-folder` → fills path + validates
- **Validate** → `POST /ocr/validate-path`
- Last path saved in `localStorage` (`ocr_output_folder`)

**Source files**
- Filters to supported extensions; warns if folder has no supported files
- Resets file input after selection (allows re-selecting same files)

**OCR start**
1. `POST /ocr/upload` with `files` + `output_folder`
2. Receives `{ job_id, status: "processing", file_count }`
3. Polls `GET /ocr/jobs/{job_id}` every ~800 ms
4. Updates progress bar from `job.progress`
5. On `completed`, shows results and saved `.md` paths

**Progress display**
- Bar: 0–100% (`progress.percent`)
- Stage label: Uploading | Processing | Saving | Completed
- Detail: current filename, file N of M, page P of Q (multi-page PDFs)

### 5.3 API Client (`frontend/src/api/client.js`)

| Function | Description |
|----------|-------------|
| `startOcrJob(files, outputFolder)` | Multipart upload, returns `JobCreated` |
| `fetchJob(jobId)` | Get job; retries on transient 404 |
| `pollJobUntilComplete(jobId, onUpdate)` | Poll until completed/failed |
| `uploadAndOcr(files, outputFolder, onProgress)` | Upload + poll wrapper |
| `browseOutputFolder()` | Native folder picker |
| `validateOutputPath(path)` | Path validation |

### 5.4 Dev Proxy

Vite (`frontend/vite.config.js`) proxies `/api` → `http://127.0.0.1:8000`.

---

## 6. Backend Design

### 6.1 Project Structure (as implemented)

```
backend/
├── app/
│   ├── main.py                    # FastAPI app, CORS, lifespan
│   ├── config.py                  # Settings from .env
│   ├── api/routes/
│   │   ├── ocr.py                 # Upload, jobs, browse, validate
│   │   └── health.py
│   ├── models/
│   │   ├── schemas.py             # Pydantic request/response models
│   │   └── job.py                 # JobRecord + JobStore (disk-backed)
│   ├── services/
│   │   ├── ocr_service.py         # Orchestration + progress callbacks
│   │   ├── azure_client.py        # Azure OpenAI vision OCR
│   │   ├── openrouter_client.py   # OpenRouter vision OCR
│   │   ├── pdf_processor.py       # PDF → PNG bytes (pymupdf)
│   │   └── md_export_service.py   # Write {stem}.md files
│   └── utils/
│       ├── path_utils.py          # Output path validation
│       ├── folder_picker.py       # Native folder dialog
│       ├── file_utils.py          # Type checks, sanitize filenames
│       └── prompts.py             # OCR prompts
├── requirements.txt
└── .env.example
```

### 6.2 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/health` | Health check |
| `POST` | `/api/v1/ocr/upload` | Upload files + `output_folder`; returns `JobCreated`; OCR runs in background |
| `POST` | `/api/v1/ocr/folder` | Same as upload (browser folder picker) |
| `GET` | `/api/v1/ocr/jobs/{job_id}` | Job status, progress, files, `md_files` |
| `GET` | `/api/v1/ocr/jobs` | List recent jobs |
| `POST` | `/api/v1/ocr/validate-path` | Validate output folder exists and is writable |
| `GET` | `/api/v1/ocr/browse-folder` | Open native folder picker; return selected path |

### 6.3 Request / Response Schemas

```python
class JobCreated(BaseModel):
    job_id: str
    status: JobStatus          # "processing" on create
    file_count: int

class JobProgress(BaseModel):
    stage: str                   # uploading | queued | processing | exporting | completed | failed
    current_file: int
    total_files: int
    current_filename: str | None
    current_page: int | None
    total_pages: int | None
    percent: int               # 0–100
    message: str

class FileOCRResult(BaseModel):
    filename: str
    success: bool
    text: str | None
    error: str | None
    page_count: int | None
    md_path: str | None          # full path of written .md (if success)

class OCRResult(BaseModel):
    job_id: str
    status: JobStatus
    files: list[FileOCRResult]
    created_at: datetime
    completed_at: datetime | None
    md_files: list[str]          # paths of all saved .md files
    export_error: str | None
    progress: JobProgress | None

class BrowseFolderResponse(BaseModel):
    cancelled: bool
    folder_path: str | None
    error: str | None
```

**Upload form fields (multipart):**
- `files`: one or more files
- `output_folder`: string (required)

### 6.4 OCR Processing Flow

```
1. POST /upload: validate output_folder
2. Create job → persist JSON → save uploads to {TEMP_DIR}/{job_id}/
3. Return JobCreated immediately
4. Background task (_run_job):
   a. For each source file (sequential):
      - PDF: render pages to PNG (pymupdf, DPI from config)
      - Each page/image: call vision LLM with OCR prompt
      - Multi-page PDF: combine with "## Page N" sections
      - Update JobProgress after each page/file
   b. Export: for each successful result, write {stem}.md to output_folder
   c. Set status completed/failed → persist JSON
5. Frontend polls GET /jobs/{id} until terminal state
```

### 6.5 Markdown Export

**Service:** `md_export_service.py`

| Rule | Behaviour |
|------|-----------|
| Filename | `{Path(source_filename).stem}.md` |
| Content | Full OCR text (Markdown from LLM) |
| Failed OCR | No `.md` written for that file |
| Overwrite | Existing `.md` with same name is overwritten |

**Example output folder after processing `invoice_a.pdf`, `invoice_b.pdf`:**
```
output/
  invoice_a.md
  invoice_b.md
```

### 6.6 Job Store (Disk-Backed)

**Location:** `{TEMP_DIR}/job_records/{job_id}.json`

- Every job create/update writes JSON to disk
- `get(job_id)` loads from memory or disk (handles restarts / polling after reload)
- `list_recent()` scans JSON files by modification time

**Progress updates** are persisted on each callback so polling always reflects current state.

### 6.7 OCR Providers

**Primary: Azure OpenAI** (`OCR_PROVIDER=azure`)

- Client: `azure_client.py` (from notebook pattern)
- Config: `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_DEPLOYMENT_NAME`
- Images sent as base64 data URLs to chat completions vision API

**Alternative: OpenRouter** (`OCR_PROVIDER=openrouter`)

- Client: `openrouter_client.py`
- Config: `OPENROUTER_API_KEY`, `OCR_MODEL`

**Default prompt** (`prompts.py`):
```
Extract all text from this document/image exactly as it appears.
Preserve reading order and structure.
Output clean Markdown. Tables should be Markdown tables.
Do not add explanations.
```

### 6.8 Configuration (`.env`)

```bash
# Azure OpenAI (primary)
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_ENDPOINT=https://<resource>.services.ai.azure.com
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o
AZURE_OPENAI_API_VERSION=2024-08-01-preview

# OpenRouter (alternative)
OPENROUTER_API_KEY=sk-or-...
OCR_PROVIDER=azure
OCR_MODEL=gpt-4o
OCR_DPI=200

# Limits
MAX_FILE_SIZE_MB=20
MAX_FILES_PER_JOB=50
TEMP_DIR=/tmp/ocr_jobs
RESULT_TTL_SECONDS=3600

# Output path security
ALLOWED_OUTPUT_BASE_DIRS=
CREATE_OUTPUT_FOLDER_IF_MISSING=false

# CORS
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

---

## 7. Data Flow (Sequence)

```
User          React UI           FastAPI              OCR Service         Azure/OpenRouter    Local Disk
 │               │                  │                      │                    │                │
 │── Browse ────►│── GET /browse ──►│── osascript dialog ──────────────────────────────────────►│
 │◄── path ──────│◄── folder_path ──│                      │                    │                │
 │── select PDFs ►│                  │                      │                    │                │
 │── Start OCR ──►│── POST /upload ─►│── save temp files ───────────────────────────────────────►│
 │               │◄── job_id ────────│── start background ─►│                    │                │
 │               │                  │                      │── OCR page ───────►│                │
 │               │── GET /jobs/id ─►│◄── progress JSON ────│◄── text ───────────│                │
 │◄── progress bar                  │                      │── write .md ───────────────────────────►│
 │               │  (poll ~800ms)   │                      │                    │           (*.md)
 │               │◄── completed ─────│                      │                    │                │
 │◄── results ───│                  │                      │                    │                │
```

---

## 8. UI/UX Guidelines

- **Output Location** section above upload zone
- Browse + Validate + manual path entry supported
- Helper: "Path must be accessible and writable by the OCR server"
- Show warning when output path missing and Start is disabled
- Show warning when selected folder has no supported files
- Progress bar with percent, stage, filename, file/page counters
- Success banner lists full paths of saved `.md` files
- Export warning (amber) if Markdown write fails but OCR text available in UI
- Remember last output path in `localStorage`
- Desktop-first responsive layout

---

## 9. Security Considerations

| Area | Measure |
|------|---------|
| Source files | Whitelist: PNG, JPG, WEBP, TIFF, PDF |
| Size limits | `MAX_FILE_SIZE_MB`, `MAX_FILES_PER_JOB` |
| Filenames | Sanitized (strip path components, unsafe chars) |
| Output path | Resolve absolute; block `..`; optional base-dir allowlist; writability test |
| Secrets | API keys backend-only; never exposed to frontend |
| CORS | Restricted to configured frontend origins |
| Temp files | Under `{TEMP_DIR}` outside web root |

---

## 10. Deployment

### 10.1 Development (current)

```bash
# Terminal 1 — Backend (no --reload recommended during OCR testing)
cd backend && source ../.venv/bin/activate
uvicorn app.main:app --host 127.0.0.1 --port 8000

# Terminal 2 — Frontend
cd frontend && npm run dev
```

- Frontend: http://127.0.0.1:5173  
- Backend: http://127.0.0.1:8000  
- `.env` at project root (backend reads `../.env`)

### 10.2 Production (suggested)

- Frontend: `npm run build` → static files (Nginx/CDN)
- Backend: Uvicorn/Gunicorn behind reverse proxy
- Docker Compose with volume mount for output folder
- Set `ALLOWED_OUTPUT_BASE_DIRS` to mounted volume path
- Use Redis/PostgreSQL for job store if scaling beyond single instance

---

## 11. Extensibility Points

| Extension | Approach |
|-----------|----------|
| Local OCR (PaddleOCR-VL) | New provider in `services/`; switch via `OCR_PROVIDER` |
| Structured JSON extraction | JSON-mode prompt + extra UI tab + optional fields in `FileOCRResult.structured` |
| SSE instead of polling | Stream progress from `/jobs/{id}/events` |
| Persistent job DB | Replace JSON job store with PostgreSQL |
| Auth | JWT/OAuth; tie jobs to users |
| Task queue | Celery/ARQ for heavy workloads |
| Parallel file OCR | Process files concurrently with semaphore (watch API rate limits) |

---

## 12. Implementation Status

| Phase | Scope | Status |
|-------|-------|--------|
| Phase 1 | Single/multi file upload, Azure OCR, Markdown export, basic UI | **Complete** |
| Phase 2 | Multi-PDF batch, job polling, progress bar, path validation, Browse folder | **Complete** |
| Phase 3 | Disk job persistence, per-page progress, error retry on poll | **Complete** |
| Phase 4 | Structured JSON, SSE, Docker, auth, queue | Planned |

---

## 13. Assumptions & Decisions

1. **Source documents** = browser upload (files or folder picker).
2. **Output folder** = server-local path; backend writes `.md` files.
3. **Primary OCR** = Azure OpenAI (matches notebook); OpenRouter optional.
4. **One `.md` per source file**; multi-page PDFs merged into one `.md`.
5. **Sequential OCR** per job (simple, predictable progress).
6. **No user accounts** in v1.
7. **Async jobs + polling** (not blocking upload response).
8. **Excel output removed** — Markdown files only.

---

## 14. Related Files

| File | Description |
|------|-------------|
| `OCR_Engine_SDD_v2.md` | Previous SDD (partially outdated) |
| `OCR_minimal_Azure_v4.ipynb` | Reference OCR notebook |
| `README.md` | Quick start and run instructions |
| `backend/` | FastAPI application |
| `frontend/` | React application |

---

*End of Software Design Document (v3.0)*

# Software Design Document (SDD)
**OCR Detection Engine with Web Portal**

**Version:** 1.2  
**Date:** 2026-08-10  
**Status:** Draft for Development  
**Changelog (v1.2):** Replaced Excel output with Markdown (.md) file export per source file.  
**Changelog (v1.1):** Added result persistence; user-specified local output folder path via web UI.

---

## 1. Introduction

### 1.1 Purpose
This document defines the software design for an **OCR Detection Engine** with a web-based front-end portal. Users select files or folders for OCR processing, the system extracts text from images and PDFs via multimodal LLM / OCR models, displays results in the browser UI, and **writes OCR results as Markdown (.md) files** in a **local folder path specified by the user** in the web interface.

### 1.2 Scope
**In scope:**
- Web UI for file/folder selection and upload
- Web UI input for **local output folder path** (where Markdown results are written)
- Backend OCR processing pipeline (images + PDFs)
- Integration with OCR/LLM providers (primarily OpenRouter multimodal models; extensible to local models such as PaddleOCR-VL / GLM-OCR)
- Display of extracted text (plain text, Markdown, optional structured JSON)
- **Export OCR results as Markdown (.md) files** in the user-specified local folder (one file per source file)
- Basic job status tracking and result viewing

**Out of scope (v1):**
- User authentication / multi-tenancy
- Real-time collaborative editing
- Full document management system (DMS) features
- Mobile native apps

### 1.3 Definitions
| Term | Meaning |
|------|---------|
| OCR | Optical Character Recognition – extracting text from images/scanned PDFs |
| VLM | Vision-Language Model (multimodal LLM that can “see” images) |
| Job | One OCR processing request (single file or batch from folder) |
| OpenRouter | Unified API gateway used to call vision models for OCR |
| Output Folder | Local directory path entered by the user; Markdown results are written here |
| Results MD | `.md` file per source file containing extracted OCR text |

---

## 2. System Overview

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Browser (React SPA)                      │
│  • File / Folder picker (source documents)                   │
│  • Output folder path input (local path for Excel)           │
│  • Upload progress                                           │
│  • Results viewer (text / Markdown / JSON)                   │
│  • Job history                                               │
└───────────────────────────┬─────────────────────────────────┘
                            │ HTTPS (REST + optional SSE)
┌───────────────────────────▼─────────────────────────────────┐
│                  FastAPI Backend                             │
│  • File upload & temporary storage                           │
│  • Job queue / status management                             │
│  • PDF page rendering (if needed)                            │
│  • OCR orchestration (OpenRouter / local model)              │
│  • Result formatting & return to UI                          │
│  • Excel writer: create / append results to user path        │
└───────────────────────────┬─────────────────────────────────┘
                            │
     ┌──────────────────────┼──────────────────────┐
     ▼                      ▼                      ▼
OpenRouter API        Local OCR Model       Local Filesystem
(Gemini / Qwen /      (optional:            • Temp uploads
 Claude / GPT)         PaddleOCR-VL)        • User output folder
                                            • Excel .xlsx file
```

### 2.2 Technology Stack

| Layer | Technology |
|-------|------------|
| Frontend | React 18+, JavaScript (or TypeScript recommended), Vite, Tailwind CSS or CSS Modules |
| Backend | Python 3.11+, FastAPI, Uvicorn |
| OCR / LLM | OpenRouter (primary), optional local PaddleOCR-VL / GLM-OCR via vLLM |
| PDF handling | `pymupdf` (fitz) or `pdf2image` + Pillow |
| Excel I/O | `openpyxl` (preferred for append) or `pandas` + openpyxl engine |
| Storage | Local temp directory for uploads; **user-specified local folder** for Excel output |
| HTTP client | `httpx` (async) for OpenRouter calls |
| Optional queue | In-memory (v1) → Redis + Celery / ARQ later |

---

## 3. Functional Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-01 | User can select one or multiple image files (PNG, JPG, WEBP, TIFF) | Must |
| FR-02 | User can select a folder (browser folder picker) and process all supported files inside | Must |
| FR-03 | User can upload PDF files; system extracts text from all pages | Must |
| FR-04 | System performs OCR and returns extracted text | Must |
| FR-05 | Results shown in web UI (raw text + rendered Markdown) | Must |
| FR-06 | User can copy / download OCR result | Must |
| FR-07 | Progress indicator while processing | Must |
| FR-08 | **User can input a local output folder path in the web UI** | Must |
| FR-09 | **After OCR, results are saved as Markdown files in the specified folder** | Must |
| FR-10 | **One `.md` file is created per successfully processed source file** | Must |
| FR-11 | Support configurable OCR model via backend config / env | Should |
| FR-12 | Optional structured output (JSON) for forms/invoices | Should |
| FR-13 | Job history list (recent jobs) | Could |
| FR-14 | Markdown filename derived from source filename (e.g. `invoice.pdf` → `invoice.md`) | Should |

---

## 4. Non-Functional Requirements

- **Performance:** Single-page image OCR < 10 s (typical); multi-page PDF depends on page count and model.
- **Scalability:** v1 single-instance; design allows horizontal scaling later.
- **Security:** Validate file types and size limits. Output folder path must be validated (existence, writability, path traversal protection). Restrict writes to allowed base directories when possible.
- **Reliability:** Graceful error handling; clear messages for failed OCR, missing/invalid output path, or Excel write failures.
- **Usability:** Clean, modern single-page UI; drag-and-drop + folder select + clear path input field.
- **Data durability:** OCR results persist in Excel even after browser session ends (as long as the local folder is accessible to the backend process).

### 4.1 Important Constraint – Local Path Access
Browsers **cannot** write to arbitrary paths on the user’s machine for security reasons.  
Therefore the **output folder path** is interpreted as a path **accessible to the FastAPI backend process** (server-local path, shared volume, or mapped drive).

**Typical deployment models:**
1. **Local desktop-style deployment** – Frontend + Backend run on the same machine; user enters a path such as `C:\OCR_Results` or `/home/user/ocr_output`.
2. **Server with shared storage** – User enters a network/shared path the server can write to.
3. **Fallback** – If path is invalid or not writable, system still returns results to the UI and optionally offers Excel download.

The UI must clearly label the field as **“Server / local output folder path (must be writable by the backend)”**.

---

## 5. Frontend Design (React + JS)

### 5.1 Pages / Views
Single-page application with these main sections:

1. **Output Folder Path Input**
   - Text input for local folder path (e.g. `D:\OCR_Output` or `/data/ocr_results`)
   - Optional “Browse” helper is not available in pure browser; path is typed or pasted
   - Validation feedback (required before starting OCR)
   - Optional Excel filename input (default: `ocr_results.xlsx`)

2. **Upload Zone**
   - Drag-and-drop area
   - “Select Files” button
   - “Select Folder” button (`webkitdirectory` / `directory` attribute) for source documents

3. **Processing Panel**
   - Progress bar / spinner
   - Current file name + page status
   - Excel write status (success / failure message)

4. **Results Viewer**
   - Tabbed view: **Plain Text** | **Markdown Preview** | **JSON** (if structured)
   - Copy button, Download `.txt` / `.md` / `.json`
   - Confirmation that data was appended to Excel (path + filename shown)

5. **Job History** (sidebar or bottom list)
   - Recent jobs with status and quick re-view

### 5.2 Key React Components

```
App
├── Header
├── OutputPathForm          // folder path + Excel filename inputs
├── UploadZone              // file input + folder input + drag-drop
├── ProcessingStatus        // progress, current job, Excel status
├── ResultsViewer
│   ├── TextTab
│   ├── MarkdownTab
│   └── JsonTab
├── JobHistory
└── SettingsModal           // optional model selection
```

### 5.3 State Management
- React `useState` / `useReducer` for v1
- Persist last-used output path in `localStorage` for convenience

### 5.4 API Client
`fetch` / Axios wrapper. Upload requests must include:
- Multipart files
- `output_folder` (string)
- `excel_filename` (optional string)

### 5.5 Browser Constraints (Reminder)
- Source files: uploaded via browser file/folder picker.
- Output path: typed path sent to backend; backend writes Excel on the server filesystem.

---

## 6. Backend Design (FastAPI)

### 6.1 Project Structure

```
backend/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── api/
│   │   ├── routes/
│   │   │   ├── ocr.py
│   │   │   └── health.py
│   │   └── deps.py
│   ├── services/
│   │   ├── ocr_service.py
│   │   ├── openrouter_client.py
│   │   ├── pdf_processor.py
│   │   ├── md_export_service.py  # export OCR results as .md files
│   │   └── local_ocr.py
│   ├── models/
│   │   ├── schemas.py
│   │   └── job.py
│   └── utils/
│       ├── file_utils.py
│       ├── path_utils.py         # NEW: validate output paths
│       └── prompts.py
├── requirements.txt
└── .env.example
```

### 6.2 Core API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/ocr/upload` | Upload files + `output_folder` → OCR → export Markdown → return result |
| `POST` | `/api/v1/ocr/folder` | Same as upload for multi-file folder selection |
| `GET`  | `/api/v1/ocr/jobs/{job_id}` | Get job status + result (includes Excel path status) |
| `GET`  | `/api/v1/ocr/jobs` | List recent jobs |
| `GET`  | `/api/v1/health` | Health check |
| `POST` | `/api/v1/ocr/server-path` | (Optional) Process source files already on server path |
| `POST` | `/api/v1/ocr/validate-path` | (Optional) Check that output folder exists and is writable |

### 6.3 Request / Response Schemas (Pydantic)

```python
class OCRUploadForm(BaseModel):
    """Additional form fields alongside multipart files"""
    output_folder: str
    excel_filename: str = "ocr_results.xlsx"

class JobCreated(BaseModel):
    job_id: str
    status: str          # "queued" | "processing" | "completed" | "failed"
    file_count: int

class FileOCRResult(BaseModel):
    filename: str
    success: bool
    text: str | None
    structured: dict | None
    error: str | None
    page_count: int | None

class OCRResult(BaseModel):
    job_id: str
    status: str
    files: list[FileOCRResult]
    created_at: datetime
    completed_at: datetime | None
    excel_path: str | None          # full path written
    excel_status: str | None        # "created" | "appended" | "failed"
    excel_error: str | None
```

### 6.4 OCR + Excel Processing Flow

```
1. Receive uploaded file(s) + output_folder + excel_filename
2. Validate output_folder:
   - Normalize path
   - Reject path traversal (e.g. ..)
   - Optionally restrict to allowed base directories (config)
   - Check directory exists (or create if policy allows)
   - Check write permission
3. Validate source file types & sizes
4. Save uploads to temp directory under job_id
5. Create job record
6. For each file:
   a. If PDF → process pages / send to OCR provider
   b. Call OCR provider (OpenRouter or local)
   c. Collect text / structured output
7. Aggregate results
8. Call Excel service:
   a. Resolve full path = output_folder / excel_filename
   b. If file does not exist → create workbook with header row
   c. Append one row per source file (or one row per page – configurable)
   d. Save workbook
9. Mark job completed (include excel_path & excel_status)
10. Return result to frontend
11. Clean up temp upload files after TTL
```

### 6.5 Excel Schema (Default)

Recommended columns (one row per processed source file):

| Column | Description |
|--------|-------------|
| `job_id` | Unique job identifier |
| `processed_at` | Timestamp (ISO or local) |
| `source_filename` | Original uploaded file name |
| `file_type` | `image` / `pdf` |
| `page_count` | Number of pages (PDF) or 1 |
| `success` | `TRUE` / `FALSE` |
| `ocr_text` | Full extracted text (Markdown or plain) |
| `error_message` | Error detail if failed |
| `model_used` | OCR model name |
| `output_folder` | Path used for this write |

**Append behavior:**
- Use `openpyxl` to open existing workbook or create new one.
- Always write header row only when creating a new file.
- Append data rows; do not overwrite existing data.
- Handle concurrent writes carefully (v1: simple file lock or sequential processing).

Optional future: separate sheet per job, or one row per page.

### 6.6 Excel Service (`excel_service.py`) – Responsibilities

- `validate_output_folder(path: str) -> None` (raises on invalid)
- `ensure_excel_file(path: Path) -> Workbook` (create with headers if missing)
- `append_ocr_results(path: Path, rows: list[dict]) -> str` (returns status: created/appended)
- Safe path joining and filename sanitization

### 6.7 OpenRouter Integration (Primary OCR Path)

- Endpoint: `https://openrouter.ai/api/v1/chat/completions`
- Models (configurable): `google/gemini-2.5-flash`, `qwen/qwen2.5-vl-72b-instruct`, Claude Sonnet, etc.
- Images: `image_url` (base64 data URL)
- PDFs: file content + `file-parser` plugin (`mistral-ocr` or `cloudflare-ai`)
- Prompt example:

```
Extract all text from this document/image exactly as it appears.
Preserve reading order and structure.
Output clean Markdown. Tables should be Markdown tables.
Do not add explanations.
```

### 6.8 Configuration (`config.py` / env)

```
OPENROUTER_API_KEY=sk-or-...
OCR_MODEL=google/gemini-2.5-flash
PDF_ENGINE=mistral-ocr
MAX_FILE_SIZE_MB=20
MAX_FILES_PER_JOB=50
TEMP_DIR=/tmp/ocr_jobs
RESULT_TTL_SECONDS=3600
DEFAULT_EXCEL_FILENAME=ocr_results.xlsx
# Optional security:
ALLOWED_OUTPUT_BASE_DIRS=/data/ocr,/home/shared/ocr_output
CREATE_OUTPUT_FOLDER_IF_MISSING=false
```

---

## 7. Data Flow (Sequence)

```
User                React UI              FastAPI               OpenRouter          Local Disk
 │                     │                     │                      │                   │
 │── enter output path ►│                     │                      │                   │
 │── select files ────►│                     │                      │                   │
 │                     │── POST /upload ────►│                      │                   │
 │                     │  (files + path)     │── validate path ─────────────────────────►│
 │                     │                     │── save temp files ───────────────────────►│
 │                     │                     │── create job          │                   │
 │                     │◄── job_id ──────────│                      │                   │
 │                     │                     │── OCR request ───────►│                   │
 │                     │                     │◄── text ─────────────│                   │
 │                     │                     │── append Excel ──────────────────────────►│
 │                     │                     │                      │            (xlsx)
 │                     │── GET /jobs/{id} ──►│                      │                   │
 │                     │◄── result + excel ──│                      │                   │
 │◄── show results ────│                     │                      │                   │
 │   + Excel path OK   │                     │                      │                   │
```

---

## 8. UI/UX Guidelines

- Clear section **“Output Location”** above the upload zone
- Placeholder example: `C:\OCR_Results` or `/home/user/ocr_output`
- Helper text: “Path must be accessible and writable by the OCR server”
- After success: green banner – `Results appended to: D:\OCR_Results\ocr_results.xlsx`
- On Excel write failure: show warning but still display OCR text in UI
- Remember last used path via `localStorage`
- Responsive, desktop-first layout

---

## 9. Security Considerations

- Strict source file type whitelist: `image/png`, `image/jpeg`, `image/webp`, `image/tiff`, `application/pdf`
- Max file size and max files per request
- Sanitize source filenames
- **Output path validation:**
  - Resolve to absolute path
  - Block `..` and other traversal patterns
  - Optionally enforce `ALLOWED_OUTPUT_BASE_DIRS`
  - Verify directory exists and is writable before processing
- Temp files outside web root; delete after TTL
- CORS limited to frontend origin
- OpenRouter API key only on backend
- Excel filename sanitized (no path separators)

---

## 10. Deployment Outline

**Development**
- Frontend: `npm run dev` (Vite)
- Backend: `uvicorn app.main:app --reload`
- User enters local paths on the same machine

**Production (suggested)**
- Frontend: static build (Nginx / CDN)
- Backend: Uvicorn + Gunicorn behind Nginx
- Docker Compose (`frontend`, `backend`)
- For Excel output: mount a host volume into the backend container and instruct users to use that mounted path
- Environment variables / secrets for API keys and allowed base dirs

---

## 11. Extensibility Points

| Extension | How |
|-----------|-----|
| Local OCR models | `LocalOCRProvider` interface; switch via config |
| Structured extraction | Extra prompt + JSON mode; extra Excel columns |
| Persistent job DB | PostgreSQL instead of in-memory |
| Auth | JWT / OAuth; tie jobs to users |
| Queue | Celery / ARQ for heavy OCR |
| Excel templates | User-selectable column mapping / multiple sheets |
| Download Excel | Always offer browser download of the generated/updated file as backup |

---

## 12. Development Phases (Suggested)

**Phase 1 – MVP**
- React UI: file upload + output folder path input
- FastAPI: upload + single-file OCR via OpenRouter
- Results display (plain text + Markdown)
- Create / append Excel with basic columns

**Phase 2**
- Multi-file / folder batch
- Job status + history
- PDF multi-page support
- Path validation endpoint + better error messages

**Phase 3**
- Structured JSON output + richer Excel columns
- Optional local OCR model
- Progress via SSE
- Docker packaging with volume mount for output folder
- Optional Excel download fallback

---

## 13. Open Decisions / Assumptions

1. **Source documents** = browser upload (files or folder picker).
2. **Output folder** = path string entered by user; must be writable by the **backend process**.
3. Primary OCR provider = **OpenRouter**.
4. Markdown format = one `.md` file per source file in the output folder.
5. No user accounts in v1.
6. Multi-page PDFs produce a single combined `.md` file per source PDF.

---

## 14. Next Steps

1. Generate project skeleton (React + FastAPI) including `excel_service.py`
2. Implement path validation utilities and Excel append logic
3. Update API schemas to accept `output_folder` and return `excel_path` / `excel_status`
4. Build React `OutputPathForm` + wire it into the upload request
5. Add end-to-end test: upload sample image → verify Excel row appended

---

*End of Software Design Document (v1.1)*

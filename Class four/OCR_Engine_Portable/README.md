# OCR Detection Engine

Web portal + FastAPI backend for OCR processing of images and PDFs, with Markdown file export.

Based on **OCR_Engine_SDD_v2.md**; OCR logic adapted from **OCR_minimal_Azure_v4.ipynb**.

## Architecture

- **Frontend:** React + Vite + Tailwind CSS (`frontend/`)
- **Backend:** FastAPI + Azure OpenAI / OpenRouter (`backend/`)
- **Output:** One `.md` file per processed source file in the user-specified output folder

## Quick Start

### 1. Environment

Copy credentials to project root `.env` (the backend reads `../.env`):

```bash
cp backend/.env.example .env
# Edit .env with your Azure OpenAI or OpenRouter keys
```

### 2. Backend

```bash
cd backend
source ../.venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

### 4. Usage

1. Enter a **server-local output folder path** (e.g. `/Users/you/ocr_output`)
2. Upload images/PDFs or select a folder
3. Click **Start OCR**
4. View results in the UI; each file is saved as `{filename}.md` in the output folder

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/ocr/upload` | Upload files + OCR + export Markdown |
| POST | `/api/v1/ocr/folder` | Same as upload (folder picker) |
| GET | `/api/v1/ocr/jobs/{job_id}` | Job status + results |
| GET | `/api/v1/ocr/jobs` | Recent jobs |
| POST | `/api/v1/ocr/validate-path` | Validate output folder |
| GET | `/api/v1/health` | Health check |

## OCR Providers

Set `OCR_PROVIDER` in `.env`:

- `azure` (default) — uses Azure OpenAI vision (same as notebook)
- `openrouter` — uses OpenRouter multimodal API

## Output Path Note

The output folder path must be **writable by the backend process**, not the browser. For local development, run frontend and backend on the same machine and use a path like `/Users/you/ocr_output`.

Optional security: set `ALLOWED_OUTPUT_BASE_DIRS` to restrict writable paths.

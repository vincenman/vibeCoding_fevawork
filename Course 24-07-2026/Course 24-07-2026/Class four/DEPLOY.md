# OCR Engine — Deploy on a New PC

This package runs a local FastAPI backend and a Vite frontend for OCR.

**Project root** is the folder that contains `DEPLOY.md`, `backend/`, and `frontend/`. Run every command from that folder unless a step says otherwise.

Do not paste comments onto the same line as a shell command. In zsh those `#` fragments are treated as extra arguments.

## Prerequisites

- **Python 3.11+** — `python3 --version` (Windows: `py -3 --version`)
- **Node.js 18+** and npm — `node --version` / `npm --version`
- **Azure OpenAI** credentials, or an **OpenRouter** API key

Conda is fine. Leave `(base)` active if you want; the commands below call `.venv` directly so Conda does not intercept `python`, `pip`, or `uvicorn`.

## 1. Unzip

macOS / Linux:

```bash
unzip OCR_Engine_Portable.zip -d ~/ocr-engine
cd ~/ocr-engine
```

Windows: unzip the zip in Explorer, then `cd` into the extracted folder.

You are in the right place when `ls` (or `dir`) shows `DEPLOY.md`, `backend`, and `frontend`.

## 2. Configure environment

```bash
cp .env.example .env
```

Windows: `copy .env.example .env`

Keep `.env` at the **project root**. The backend reads `../.env` when it is started from `backend/`.

### Azure OpenAI (default)

Set these in `.env`:

- `OCR_PROVIDER=azure`
- `AZURE_OPENAI_API_KEY`
- `AZURE_OPENAI_ENDPOINT`
- `AZURE_OPENAI_DEPLOYMENT_NAME`

### OpenRouter (alternative)

Set these instead:

- `OCR_PROVIDER=openrouter`
- `OPENROUTER_API_KEY`

On Windows, also change `TEMP_DIR` from `/tmp/ocr_jobs` to a local folder such as `C:\Temp\ocr_jobs`.

## 3. Backend setup (once)

Use **one** virtualenv at the project root named `.venv`. Do not create `backend/.venv`.

macOS / Linux:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r backend/requirements.txt
mkdir -p output
```

Windows (PowerShell or cmd):

```bat
py -3 -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
mkdir output
```

## 4. Frontend setup (once)

```bash
cd frontend
npm install
cd ..
```

## 5. Run

Open **two terminals**. Both must start at the project root.

If `./start_backend.sh` says `Permission denied`, run `chmod +x start_backend.sh start_frontend.sh` once, or use `bash start_backend.sh`.

### Terminal 1 — Backend

macOS / Linux:

```bash
bash start_backend.sh
```

Manual equivalent:

```bash
cd backend
../.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Windows:

```bat
cd backend
..\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Wait for: `Uvicorn running on http://127.0.0.1:8000`

### Terminal 2 — Frontend

macOS / Linux:

```bash
bash start_frontend.sh
```

Manual equivalent (all platforms):

```bash
cd frontend
npm run dev -- --host 127.0.0.1 --port 5173
```

Wait for: `Local: http://127.0.0.1:5173/`

### Open the app

Open **http://127.0.0.1:5173**

Use `127.0.0.1`, not `localhost`. On macOS `localhost` often resolves to IPv6 (`::1`), and this stack is bound to IPv4 only.

Optional checks:

- http://127.0.0.1:8000/api/v1/health should return `{"status":"ok"}`
- http://127.0.0.1:8000/docs is the API UI

## 6. Usage

1. Set the **output folder** — click **Browse…** or type an absolute path that already exists (for example the `output` folder created in step 3).
2. Upload PDF/images, or select a folder of them.
3. Click **Start OCR**.
4. Results are written as `{filename}.md` in that output folder.

The output path is written by the **backend process** on this machine, not by the browser. Relative paths are resolved from the backend working directory (`backend/`), so prefer **Browse…** or an absolute path.

The folder must already exist unless you set `CREATE_OUTPUT_FOLDER_IF_MISSING=true` in `.env`.

## Test samples

- `samples/test_invoice.pdf`
- `samples/test_invoice2.pdf`

## Notes

- Do not add `--reload` to Uvicorn while running OCR jobs. Reload kills in-flight work.
- **Browse…** needs a desktop session (macOS uses a native dialog; Windows/Linux use tkinter).
- See `OCR_Engine_SDD_v3.md` for architecture.

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `Permission denied` on `./start_*.sh` | `chmod +x start_backend.sh start_frontend.sh`, or run `bash start_backend.sh` |
| `uvicorn: command not found` | Do not call bare `uvicorn`. Use `bash start_backend.sh` or `.venv/.../python -m uvicorn` from `backend/` |
| `ModuleNotFoundError: No module named 'app'` | Start Uvicorn from the `backend/` folder |
| `ModuleNotFoundError: No module named 'uvicorn'` | The wrong venv is in use, or step 3 was skipped. Remove `backend/.venv` if it exists: `rm -rf backend/.venv` |
| Browser cannot open `127.0.0.1:5173` | Frontend is not running, or it is bound to IPv6. Restart with `bash start_frontend.sh` |
| Port 8000 or 5173 already in use | `lsof -iTCP:8000 -sTCP:LISTEN` / `lsof -iTCP:5173 -sTCP:LISTEN` (Windows: `netstat -ano \| findstr :8000`) then stop that process |
| Job not found | Only one backend on port 8000; do not use `--reload` |
| Connection / auth error during OCR | Check `.env` keys, `OCR_PROVIDER`, and network access |
| Output folder error | Path must exist and be writable. Use **Browse…** or an absolute path |
| Browse does nothing | Backend must be local, with a GUI session |
| Start button disabled | Set an output folder and select at least one PDF/image |

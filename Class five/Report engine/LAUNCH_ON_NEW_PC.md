# OCR Workspace — Launch on another PC

Portable package: frontend + backend + reporting engine (no secrets, no `node_modules`, no virtualenv).

## Requirements

- **Python** 3.11+ (3.12 recommended)
- **Node.js** 18+ (includes `npm`)
- Network access for Azure OpenAI (and optional Telegram)

## 1. Unzip

```bash
unzip OCR_Workspace_portable_v1.zip
cd OCR_Workspace_portable_v1
```

## 2. Configure credentials

```bash
cp .env.example .env
```

Edit `.env` and set at least:

- `AZURE_OPENAI_API_KEY`
- `AZURE_OPENAI_ENDPOINT`
- `AZURE_OPENAI_DEPLOYMENT_NAME`

Optional:

- `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID` for Excel delivery

## 3. Backend

```bash
python3 -m venv .venv

# macOS / Linux
source .venv/bin/activate

# Windows (PowerShell)
# .\.venv\Scripts\Activate.ps1

pip install -r backend/requirements.txt
cd backend
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Leave this terminal open. API: http://127.0.0.1:8000/docs

## 4. Frontend (new terminal)

```bash
cd frontend
npm install
npm run dev -- --host 127.0.0.1 --port 5173
```

Open: **http://127.0.0.1:5173/**

## 5. First-run checklist

1. In the UI, set **output folder** to a path that exists on that PC (e.g. a local `MD_files` or any writable folder).
2. Upload a PDF/image → **Start OCR** → Markdown is written to that folder.
3. Stage 03 → **Generate Excel report** → edit cells → **Update Excel**.

Sample Markdown for report-only testing is included under `MD_files/`.

## 6. Optional CLI report

From the package root (with `.venv` activated and `.env` configured):

```bash
python reporting_engine.py
```

Edit `MD_FOLDER` / `EXCEL_OUTPUT_PATH` at the top of `reporting_engine.py` if needed.

## Notes

- Do **not** copy a real `.env` into shared zips; recreate it on each machine.
- Output folder must be writable by the **backend** process (same machine as the API).
- Frontend proxies `/api` to `http://127.0.0.1:8000` (see `frontend/vite.config.js`).

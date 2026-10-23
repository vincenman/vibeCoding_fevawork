# OCR Engine — Deploy on a New PC

This package contains everything needed to run the OCR Detection Engine on another machine.

## Prerequisites

- **Python 3.11+**
- **Node.js 18+** and npm
- **Azure OpenAI** credentials (or OpenRouter key)

## 1. Unzip

```bash
unzip OCR_Engine_Portable.zip -d ~/ocr-engine
cd ~/ocr-engine
```

## 2. Configure environment

```bash
cp .env.example .env
# Edit .env with your Azure OpenAI keys:
#   AZURE_OPENAI_API_KEY
#   AZURE_OPENAI_ENDPOINT
#   AZURE_OPENAI_DEPLOYMENT_NAME
```

## 3. Backend setup

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r backend/requirements.txt
mkdir -p output                  # example output folder
```

## 4. Frontend setup

```bash
cd frontend
npm install
cd ..
```

## 5. Run

**Terminal 1 — Backend:**
```bash
source .venv/bin/activate
cd backend
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

**Terminal 2 — Frontend:**
```bash
cd frontend
npm run dev
```

Open http://127.0.0.1:5173

## 6. Usage

1. Set **output folder** (type path or click **Browse…**)
2. Upload PDF/images or select a folder
3. Click **Start OCR**
4. Results saved as `{filename}.md` in your output folder

## Test samples

Included sample files for testing:
- `samples/test_invoice.pdf`
- `samples/test_invoice2.pdf`

## Notes

- Output folder must be writable by the backend (server-local path).
- On macOS, **Browse…** uses the native folder picker.
- Do **not** use `uvicorn --reload` during OCR jobs (can interrupt processing).
- See `OCR_Engine_SDD_v3.md` for full architecture documentation.

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Job not found | Restart backend without `--reload`; ensure only one backend on port 8000 |
| Connection error (OCR) | Check `.env` Azure keys and network access |
| Browse does nothing | Backend must run locally with GUI access (macOS/Linux desktop) |
| Start button disabled | Enter output folder path first |

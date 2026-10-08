# Structured Data Extractor

## Requirements
- Python 3.10+
- Internet access
- Google AI Studio API key

## Setup

### 1) Create virtual environment
Windows PowerShell:
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

macOS/Linux:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2) Install dependencies
```bash
pip install -r requirements.txt
```

### 3) Create `.env`
```bash
copy .env.example .env
```
Then update `.env`:
```env
GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-3.5-flash-lite
```

### 4) Run the app
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 5) Open the app
- Home: http://127.0.0.1:8000/
- Swagger docs: http://127.0.0.1:8000/docs

### 6) Test the API
```bash
curl -X POST http://127.0.0.1:8000/extract \
  -H "Content-Type: application/json" \
  -d '{"text":"Paid INR 1,250 to AWS India Pvt Ltd on 12 March 2024. Invoice #INV-2024-0312. Services: cloud compute."}'
```

### 7) Run tests
```bash
pytest -q
```

## Dependency list
```bash
pip install fastapi google-genai python-dotenv uvicorn pytest httpx
```

# Quick Start Guide

## Prerequisites
- Python 3.13+ installed
- Virtual environment created in `.venv-new`

## Setup (One-time)

1. **Create virtual environment** (if not already done):
   ```bash
   python -m venv .venv-new
   ```

2. **Install dependencies**:
   ```bash
   .\.venv-new\Scripts\python.exe -m pip install --upgrade pip
   .\.venv-new\Scripts\python.exe -m pip install anthropic==0.58.2 chromadb==1.0.15 sentence-transformers==5.0.0 fastapi==0.116.1 uvicorn==0.35.0 python-multipart==0.0.20 python-dotenv==1.1.1
   ```

3. **Configure API key**:
   - Copy `.env.example` to `.env`
   - Add your Anthropic API key to `.env`

## Running the Application

### Option 1: Git Bash (Recommended for Git Bash users)
```bash
./run.sh
```

### Option 2: PowerShell (Recommended for PowerShell users)
```powershell
.\run.ps1
```

### Option 3: Direct Command
```bash
cd backend
../.venv-new/Scripts/python.exe -m uvicorn app:app --reload --port 8000
```

## Accessing the Application

Once running, the application will be available at:
- **API**: http://127.0.0.1:8000
- **Interactive Docs**: http://127.0.0.1:8000/docs

## Troubleshooting

### "Virtual environment not found"
Run: `python -m venv .venv-new`

### "ANTHROPIC_API_KEY not set"
Make sure you have a `.env` file with your API key

### "Module not found" errors
Reinstall dependencies:
```bash
.\.venv-new\Scripts\python.exe -m pip install -r requirements.txt
```

### Port already in use
Change the port in the run script or kill the existing process:
```powershell
Get-Process -Name python | Stop-Process -Force
```

## Running Tests

```bash
.\.venv-new\Scripts\python.exe -m pytest backend/tests/test_ai_generator.py -v
```

## Notes

- The application uses `.venv-new` (not `.venv`) due to previous environment corruption
- Both `run.sh` (for Git Bash) and `run.ps1` (for PowerShell) are provided for convenience
- Server runs with auto-reload enabled for development

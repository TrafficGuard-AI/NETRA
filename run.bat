@echo off
REM Launch the backend with the project's virtualenv (Windows).
REM Auto-detects whichever venv (.venv or venv) actually has uvicorn installed.
cd /d "%~dp0backend"

if exist "..\.venv\Scripts\uvicorn.exe" (
    set "UVICORN=..\.venv\Scripts\uvicorn.exe"
) else if exist "..\venv\Scripts\uvicorn.exe" (
    set "UVICORN=..\venv\Scripts\uvicorn.exe"
) else (
    echo [ERROR] uvicorn not found in .venv or venv.
    echo Create a venv with Python 3.10-3.12 and run: pip install -r backend\requirements.txt
    exit /b 1
)
"%UVICORN%" app.main:app --reload --port 8000

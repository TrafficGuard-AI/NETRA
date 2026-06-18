@echo off
REM Launch the backend with the project's .venv (Windows).
cd /d "%~dp0backend"
..\.venv\Scripts\uvicorn app.main:app --reload --port 8000

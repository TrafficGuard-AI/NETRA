#!/usr/bin/env bash
# Launch the backend with the project's virtualenv (avoids anaconda PATH clashes).
# Auto-detects whichever venv (.venv or venv) actually has uvicorn installed.
set -e
cd "$(dirname "$0")/backend"

if [ -x "../.venv/bin/uvicorn" ]; then
    exec ../.venv/bin/uvicorn app.main:app --reload --port 8000
elif [ -x "../venv/bin/uvicorn" ]; then
    exec ../venv/bin/uvicorn app.main:app --reload --port 8000
else
    echo "[ERROR] uvicorn not found in .venv or venv." >&2
    echo "Create a venv with Python 3.10-3.12 and run: pip install -r backend/requirements.txt" >&2
    exit 1
fi

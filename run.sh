#!/usr/bin/env bash
# Launch the backend with the project's .venv (avoids anaconda PATH clashes).
set -e
cd "$(dirname "$0")/backend"
exec ../.venv/bin/uvicorn app.main:app --reload --port 8000

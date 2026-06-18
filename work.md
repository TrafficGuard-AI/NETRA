# 🛠️ Work Log — TrafficGuard AI

Running log of what's built. Newest entries at the bottom of each phase.

---

## Phase 1 — Foundation & Setup

### ✅ Backend skeleton (FastAPI)

Project structure scaffolded and byte-compiles clean.

```
backend/
├── requirements.txt
├── weights/                  # YOLO weights (gitignored)
└── app/
    ├── main.py               # FastAPI app, CORS, routers, static evidence mount
    ├── config.py             # pydantic-settings + storage dir bootstrap
    ├── schemas.py            # API response models (ViolationOut, AnalysisResult)
    ├── routes/
    │   ├── upload.py         # POST /api/upload — full analysis pipeline
    │   ├── violations.py     # GET /api/violations[, /{id}] with filters
    │   └── analytics.py      # GET /api/analytics/summary, /by-type
    ├── models/
    │   ├── preprocessor.py   # CLAHE enhance + Laplacian quality score
    │   ├── detector.py       # YOLOv8 wrapper (lazy-loaded), COCO→category map
    │   ├── violation.py      # rule engine — triple-riding (IoU) shipped
    │   └── ocr.py            # EasyOCR plate reader + Indian-format regex
    ├── database/
    │   ├── db.py             # SQLAlchemy engine/session, init_db
    │   └── models.py         # Violation table
    └── utils/
        ├── annotator.py      # draw detection/violation boxes
        └── evidence.py       # save uploads + annotated evidence
```

**Design notes**
- Heavy ML deps (ultralytics, easyocr, cv2) are lazy-loaded so the API boots without weights present.
- Pipeline: upload → preprocess (CLAHE + conditional denoise) → YOLO detect → rule-based violation analysis → annotate → persist to SQLite.
- Phase 1 ships **triple-riding** detection only; helmet/seatbelt/red-light land in Phase 4.

### ✅ Repo scaffold
- `.gitignore` (Python, node, weights, data artifacts, secrets)
- `data/{uploads,evidence,sample_images,annotations}`, `notebooks/`, `docs/`

### ✅ Frontend skeleton (Vite + React)

Builds clean (`npm run build`). Editorial light theme — off-white surfaces,
Fraunces serif headings, single teal accent, generous whitespace. No neon.

```
frontend/src/
├── main.jsx                 # BrowserRouter bootstrap
├── App.jsx                  # routes
├── api.js                   # axios client (VITE_API_URL)
├── index.css                # design tokens (palette, fonts, radius)
├── App.css                  # component styles
├── components/
│   ├── Layout.jsx           # sidebar nav + content outlet
│   ├── StatCard.jsx
│   ├── ViolationCard.jsx
│   └── UploadPanel.jsx      # drag-and-drop upload
└── pages/
    ├── Dashboard.jsx        # stat cards + recent activity
    ├── Analyze.jsx          # upload → evidence + violations
    ├── Violations.jsx       # filterable register table
    └── Analytics.jsx        # recharts bar (by type)
```

### ✅ Environment + end-to-end smoke test

- Root `.venv` (Python 3.13). Installed `backend/requirements.txt` — torch 2.12,
  ultralytics 8.3, easyocr, opencv 4.10, fastapi 0.115 all import clean.
- Wired `yolo_weights` to `backend/weights/` (config.py); weights auto-download
  there on first inference (`yolov8n.pt`, 6.2 MB ✓).
- Booted `uvicorn app.main:app` and verified the full path:
  - `GET /health` → `{"status":"ok"}`
  - `POST /api/upload` (blank test frame) → valid `AnalysisResult`
    (quality 0, 0 detections, evidence image generated)
  - `GET /evidence/<id>.jpg` → `200`
  - `GET /api/analytics/summary` → `{"total":0,...}`
  - SQLite `trafficguard.db` created at repo root with `violations` table
- No errors/warnings in server log.

> Run: `cd backend && ../.venv/bin/python -m uvicorn app.main:app --reload`
> (must run from `backend/` for the `app.*` imports to resolve)

### ✅ Cross-platform support (Mac + Windows team)

- `run.sh` (macOS/Linux) + `run.bat` (Windows) — launch the backend via the
  project `.venv` regardless of the shell's default `python`/`uvicorn`.
  Fixes the anaconda-PATH clash that caused `ModuleNotFoundError: ultralytics`.
- `config.py` SQLite URL now uses `.as_posix()` so it's valid on Windows paths.
- `.gitattributes` normalizes line endings (`.sh` → LF, `.bat` → CRLF, weights/
  images marked binary).
- README setup rewritten with macOS/Linux **and** Windows (PowerShell) steps;
  venv lives at repo root.

> Note: run the backend with the **`.venv`**, not anaconda. Either use the
> launcher (`./run.sh` / `run.bat`) or activate the venv first.

### ⏭️ Next
- Phase 4: helmet / red-light / seatbelt detectors (the score drivers)
- Wire license-plate OCR into the upload pipeline
- Add a few real sample traffic images to `data/sample_images/` for a live demo

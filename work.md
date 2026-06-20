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

### ✅ Frontend redesign — editorial polish

Full visual pass on the dashboard. Builds + runs clean (Vite HMR on :5173).

- **Design system** (`index.css`): warm paper palette, layered soft shadows,
  Fraunces display + Inter body + JetBrains Mono for plates, motion tokens,
  `rise` entrance animation, custom scrollbar, subtle radial background.
- **Layout**: refined sidebar (gradient brand mark, active-route accent bar,
  nav heading) + sticky blurred topbar with date + "New analysis" CTA + a
  **live backend status dot** (polls `/health` every 15s).
- **Dashboard**: icon stat cards (hover-lift, accent variant, trend chips),
  a donut "violation mix" with center total + legend, a gradient "get started"
  panel, and a recent-activity grid.
- **Analyze**: image-preview on drop, before/after compare (original ↔
  annotated), result metric chips, loader state, feature hint chips.
- **Records**: live search + type filter + count pill, polished sticky-header
  table with severity badges and mono plate/IDs.
- **Analytics**: donut + bar charts side by side.
- New shared components: `PageHeader`, `EmptyState`, `StatCard`, `Donut`,
  refined `ViolationCard` + `UploadPanel`.
- Responsive: collapses to single column under 940px.

> Note: couldn't auto-screenshot from here — verified via `npm run build`
> (clean) and a dev-server boot (HTTP 200, no errors). View at
> http://localhost:5173.

---

## Phase 2 — Image Preprocessing Pipeline

### ✅ Adaptive preprocessor (`preprocessor.py`)

Assess the frame, then apply **only** the corrections it needs.

- **Quality assessment** → `QualityReport` (0-100): overall `score` plus
  `sharpness` (Laplacian var), `brightness` (mean), `contrast` (std).
- **CLAHE** low-light enhancement (L channel) — fires on low brightness / flat contrast.
- **Denoise** (`fastNlMeansDenoisingColored`) — low-light / low overall score.
- **Dehaze** — per-channel percentile contrast stretch (washed-out frames).
- **Deblur** — unsharp mask when Laplacian variance < 100 (motion blur).
- **`normalize()`** — aspect-preserving 640×640 letterbox utility (YOLO does its
  own resize, so kept off the main path).

`preprocess()` returns `(image, QualityReport)` and records which fixes ran.

### ✅ Wired through the stack
- `schemas.py`: new `QualityReport`; `AnalysisResult.quality_score` → `quality`.
- `upload.py`: passes `asdict(report)` into the response.
- Frontend `Analyze.jsx`: quality score chip + **"Auto-corrected:"** chips
  listing applied fixes (great demo moment) — styled in `App.css`.

### ✅ Verified
- Unit test on synthetic dark / hazy / blurry / flat frames — correct
  corrections fire for each (e.g. dark → Denoise + CLAHE; blurry → +Sharpen).
- `normalize()` → `(640, 640, 3) uint8`.
- Full serialization path (`pipeline → asdict → AnalysisResult.model_dump_json`)
  produces the nested `quality` object.
- Frontend build clean.

---

## Phase 3 — Vehicle & Person Detection

### ✅ Structured detector (`detector.py`)

- `COCO_MAP`: COCO id → `(kind, label, category)` for person, bicycle, car,
  motorcycle (→ Two-Wheeler), bus (→ Public Transport), truck (→ Heavy Vehicle).
- Each detection now carries `kind` / `label` / `category` / `bbox` /
  `confidence` / `occupants` (conf filter + NMS handled by YOLO).
- **Occupant counting**: `_assign_occupants()` attributes each person to the
  vehicle whose box best *contains* them (intersection ÷ person area ≥ 0.2).
  Containment (not IoU) is used since a rider is far smaller than the vehicle.
- `summarize()`: road-user counts grouped by category.

### ✅ Wired through the stack
- `violation.py`: triple-riding now reads `occupants >= 3` from detection
  (no more recomputing IoU).
- `annotator.py`: switched `class` → `kind`; shows `xN` occupant count on
  vehicles with ≥ 2 riders.
- `schemas.py` + `upload.py`: response gains a `road_users` breakdown.
- Frontend `Analyze.jsx`: **"Road users:"** chip row (count × category).

### ✅ Verified
- Crafted scene (two-wheeler + 3 overlapping persons + a car) → moto
  `occupants = 3`, car `0`, triple-riding fires with correct description.
- `summarize()` groups correctly; full `AnalysisResult` (with `road_users`)
  serializes; frontend build clean.

---

## Phase 4 — Violation Detection Models ⭐ CORE

### ✅ Extensible rule framework (`models/rules/` + `violation.py`)

Each rule is a self-contained module exposing `CODE` / `NAME` / `SEVERITY`,
`status()` and `check(scene)`. `violation.py` registers them, runs them all via
`analyze(detections, image)`, and exposes `catalog()`. Add a violation type by
dropping a module in `rules/` and registering it — no other code changes.

`Scene` (rules/base.py) gives each rule `vehicles` / `persons` / `signals`.

| Rule | Status | How it works |
|------|--------|--------------|
| Triple riding | **active** | `occupants >= 3` on a Two-Wheeler |
| Helmet non-compliance | needs-weight | auto-enables when `weights/helmet.pt` exists; runs a helmet YOLO on each rider crop |
| Red-light running | needs-config | HSV signal-colour classify + stop-line; opt-in via `red_light_enforcement` |
| Seatbelt | planned | needs a driver-region classifier |
| Wrong-side driving | planned | needs per-camera lane direction |
| Illegal parking | planned | needs no-parking zone polygons |

### ✅ Supporting changes
- `detector.py`: traffic lights now detected as `kind="signal"` (COCO 9);
  `summarize()` excludes signals.
- `config.py`: `helmet_weights`, `red_light_enforcement`, `stop_line_frac`.
- `GET /api/rules` (+ `RuleInfo` schema) returns the catalogue with statuses.
- Frontend `Dashboard.jsx`: **"Detection coverage"** panel — all 6 rules with
  Active / Needs weight / Needs config / Planned tags ("N of 6 active").

### ✅ Verified
- `catalog()` → 6 rules with correct statuses.
- Triple riding fires via the coordinator (`analyze(dets, img)`).
- Red-light: with enforcement on + a synthetic red signal, only the vehicle
  past the stop line is flagged (the one above the line is not).
- Upload route runs end-to-end in-process; `/api/rules` returns 6; FE build clean.

### ✅ Helmet rule live with a real model
Wired a trained helmet weight (`helmet.pt`, classes `Plate / WithHelmet /
WithoutHelmet`). Fixes made when it didn't fire:
- Class-name matching generalised (`WithoutHelmet`, `head`, "no … helmet").
- Runs on the **full frame** (heads sit above the bike box) and attributes each
  bare-head box to the nearest two-wheeler by IoU.
- Runs at **imgsz=960** (config `helmet_imgsz`; heads were missed at 640),
  conf floor 0.3; dedupes to one helmet violation per vehicle.
- Verified on a real triple-riding photo → TRIPLE_RIDING + HELMET both fire.
- Note: the model also emits `Plate` boxes — reuse for Phase 5 OCR.

### To enable the model-backed rules
- **Helmet**: drop a helmet-detection YOLO at `backend/weights/helmet.pt`
  (e.g. from Roboflow Universe) — the rule flips to *active* automatically.
- **Red-light**: set `red_light_enforcement=true` (and tune `stop_line_frac`)
  once the camera's stop line is known.

---

## Phase 5 — License Plate Recognition

### ✅ Plate detection + OCR (`plates.py`, `ocr.py`)

- **Detection** (`PlateService`): uses a dedicated `plate.pt` if present, else
  **reuses the helmet model's `Plate` class** (no extra weight needed). Config:
  `plate_weights`, `plate_conf`.
- **Preprocess** (`_prep`): upscale small crops to ~96px height + CLAHE contrast.
- **OCR** (`PlateReader`): EasyOCR with an A-Z0-9 **allowlist**, keeps only
  fragments with conf ≥ 0.3 (no more garbage), strips the embossed "IND" tag.
  Dropped the old blanket O→0/B→8 correction (it corrupted the letter section).
- **Matching**: each plate is attached to the violation whose **vehicle box**
  best contains it → `Violation.license_plate` is now populated and shown on
  cards / Records table.
- **Evidence**: annotator draws plate boxes (teal) with the OCR text.

### ✅ Verified
- Synthetic legible plate → reads `MH12AB1234` exactly (OCR path correct).
- Real wide-shot photo: plate region detected but only `02` legible at this
  resolution (54×31px) → correctly returns "No plate" instead of guessing.
- False-positive plate on a shop sign is filtered (low conf + outside vehicles).
- Full upload route runs end-to-end with plates wired in.

> ⚠️ Demo note: OCR accuracy depends on plate resolution. Use images where a
> plate is reasonably close/large to show real plate numbers. Distant plates in
> wide shots are too small to read (shown as "No plate", not wrong text).

---

## Phase 6 — Evidence Generation & Storage

### ✅ Evidence provenance + packaging
- `annotator.watermark()`: burns a bottom bar onto evidence —
  `TrafficGuard AI | <location> | <timestamp>`.
- `evidence.save_metadata()` / `load_metadata()`: a JSON **evidence package**
  sidecar per upload (evidence_id, timestamp, location, image names, quality,
  road users, violations).
- `upload.py`: accepts a `location` form field, sets `location` + `timestamp`
  on each record, watermarks the image, writes the package JSON.

### ✅ Review workflow (pending / confirmed / dismissed)
- `PATCH /api/violations/{id}` (`ViolationStatusUpdate`) — confirm/dismiss.
- `GET /api/violations/{id}/evidence` — returns the evidence package.
- Frontend `Records`: status tag + ✓/✗ review buttons (dismissed rows dim),
  new **Location** column; `Analyze` has a **camera location** input that flows
  through to storage + watermark.

### ✅ Verified
- Upload with `location="Dadar TT Junction"` → record stores location, evidence
  package JSON written with all 8 keys (2 violations inside).
- `PATCH` flips status `pending → confirmed`.
- Backend compiles, full route + status + evidence endpoints run, FE build clean.

---

## Phase 7 — Backend API (completed the gaps)

### ✅ New endpoints
- `POST /api/batch-upload` — runs the pipeline over many images; returns
  `BatchResult {processed, total_violations, results[]}`. Pipeline extracted
  into shared `process_image()` (used by both `/upload` and `/batch-upload`).
- `GET /api/analytics/trends` — violations per day (`func.date`), oldest first.
- `GET /api/analytics/top-plates?limit=` — top offenders by plate.

Full API surface now: upload, batch-upload, violations (list/get/patch/evidence),
rules, analytics (summary/by-type/trends/top-plates), static `/evidence`.

### ✅ Surfaced on the Analytics page
- Trend line chart (violations/day) + **Top offenders** ranked list, alongside
  the existing donut + bar. `api.js`: `getTrends`, `getTopPlates`.

### ✅ Verified
- Batch of 2 → processed 2, total_violations 4.
- Trends groups by day correctly; top-plates returns [] here (test images have
  unreadable plates — expected). Backend compiles, FE build clean.

---

## Frontend polish pass (judge-ready)

- **Animated count-up** on all dashboard stat numbers (`useCountUp` hook +
  `StatCard` with numeric value + suffix).
- **Pipeline visualizer** on Analyze (`Pipeline.jsx`): the 5 ML stages
  (Enhance → Detect → Classify → Read plates → Evidence) animate while
  processing, then show ✓ + real per-stage stats (quality, users, flags,
  plates, evidence). Replaces the old static hint chips.
- Verified visually via Playwright screenshots of all pages — dashboard,
  analyze (result), analytics, records all render cleanly and cohesively.
  (Installed playwright `--no-save`; not in package.json. Chromium cached in
  ~/Library, outside the repo.)

### ⏭️ Next (Phases 9-11)
- Phase 9: test real sample images, edge cases, measure inference time
- Phase 10: deploy (Vercel + Render/Railway)
- Phase 11: pitch deck, demo video, README polish
- Optional: evidence export/download, per-position OCR correction

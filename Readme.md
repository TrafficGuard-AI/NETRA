# 🚦 TrafficGuard AI

Automated photo identification & classification of traffic violations — built for
the Flipkart Gridlock Hackathon 2.0 (Round 2).

Upload a roadside camera frame and TrafficGuard runs a weather-adaptive
preprocessor (fog / night / rain), detects vehicles and riders with YOLOv8,
flags violations (triple-riding today; helmet, seatbelt, red-light next), reads
license plates, and stores annotated evidence with a confidence score.

## Stack

| Layer      | Tech                                   |
|------------|----------------------------------------|
| Detection  | YOLOv8 (Ultralytics)                   |
| OCR        | EasyOCR + Indian-plate regex           |
| Backend    | FastAPI · SQLAlchemy · SQLite          |
| Frontend   | React + Vite · Recharts                |
| Imaging    | OpenCV — weather-adaptive edge preprocessor + quality score |

## Project layout

```
ultimate_edge_preprocessor.py   weather-adaptive edge preprocessor (repo root)
backend/                        FastAPI app — pipeline, models, DB, routes
frontend/                       React dashboard (Vite)
data/                           uploads + generated evidence
```

## Weather-adaptive preprocessing

Every uploaded frame first passes through `DynamicTrafficPreprocessor`
([ultimate_edge_preprocessor.py](ultimate_edge_preprocessor.py)), which detects
the scene condition from image statistics and routes it through the matching
correction chain:

| Condition  | Detected by                     | Chain                                  |
|------------|---------------------------------|----------------------------------------|
| `FOG`      | low contrast + bright           | inverted-image dehaze → unsharp        |
| `NIGHT`    | low mean + bright point sources | adaptive low-light → denoise → unsharp |
| `DAY/RAIN` | everything else                 | edge-preserving denoise → unsharp      |

Detection, violation rules and annotated evidence run on a fast 640×640
letterboxed frame, while **ANPR (plate OCR) runs on the full-resolution,
weather-corrected frame** — detection boxes are mapped back from 640×640 to
original pixels so plate detail isn't lost to downscaling. The detected
condition is logged, stored in the evidence metadata, burned onto the evidence
image, and returned as `weather_condition` in the `/api/upload` response.

## Run locally

Works on macOS / Linux and Windows. Create the virtualenv once at the repo root.

> **Use Python 3.10–3.12.** The pinned `numpy`/`ultralytics` versions have no
> Python 3.13 wheels — a 3.13 venv segfaults importing numpy. The launchers
> (`run.bat` / `run.sh`) auto-detect either a `.venv` or `venv` directory.

**1. Set up the backend env** (from the repo root)

macOS / Linux:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
```

Windows (PowerShell):
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
```

**2. Start the backend**

Use the launcher (picks the right interpreter automatically):
```bash
./run.sh      # macOS / Linux
run.bat       # Windows
```
…or run it directly: `cd backend` then `uvicorn app.main:app --reload`
(with the venv activated). Serves http://localhost:8000 — docs at `/docs`.
The YOLO weights (`yolov8n.pt`) download automatically on first inference.

**3. Start the frontend** (any OS)
```bash
cd frontend
npm install
npm run dev                            # http://localhost:5173
```

## API

| Method | Endpoint                  | Description                  |
|--------|---------------------------|------------------------------|
| POST   | `/api/upload`             | Analyze one image            |
| GET    | `/api/violations`         | List records (type/severity) |
| GET    | `/api/violations/{id}`    | Single record                |
| GET    | `/api/analytics/summary`  | Totals                       |
| GET    | `/api/analytics/by-type`  | Counts grouped by type       |

See [implementation_plan.md](implementation_plan.md) for the full roadmap and
[work.md](work.md) for the build log.

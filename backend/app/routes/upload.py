from dataclasses import asdict
from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.database.models import Violation
from app.models import preprocessor
from app.models.detector import detector, summarize
from app.models.plates import plate_service
from app.models.violation import analyze
from app.schemas import AnalysisResult, BatchResult, ViolationOut
from app.utils.annotator import annotate, label_condition, watermark
from app.utils.evidence import save_evidence, save_metadata, save_upload

# Repo-root module (see app.config for the sys.path wiring that makes this import
# work when the backend runs with CWD=backend/).
from ultimate_edge_preprocessor import DynamicTrafficPreprocessor

router = APIRouter()

# Weather-adaptive edge preprocessor. Instantiated ONCE at import time — never
# per request — so its prebuilt gamma LUT / CLAHE objects are reused across all
# frames, keeping per-image latency low.
edge_preprocessor = DynamicTrafficPreprocessor()


def process_image(raw: bytes, location: str, db: Session) -> AnalysisResult:
    """The full pipeline for one image — shared by /upload and /batch-upload."""
    upload_path, image = save_upload(raw)
    # Handle a missing / undecodable frame gracefully instead of crashing.
    if image is None:
        raise HTTPException(status_code=400, detail="Could not decode the uploaded image.")

    # ── Weather-adaptive edge preprocessing ──────────────────────────────
    # Detect the scene condition (FOG / NIGHT / DAY-RAIN) and return a cleaned,
    # 640x640 letterboxed frame. Every downstream stage — detection, violation
    # analysis, ANPR, annotation and evidence — runs on this single clean frame,
    # so all bounding boxes live in the same 640x640 coordinate space and no
    # rescaling is needed.
    processed = edge_preprocessor.process(image)
    clean_frame = processed["processed_uint8"]
    weather_condition = processed["condition"]
    print(f"[edge-preprocess] {upload_path.name}: weather condition = {weather_condition}")

    # Quality report for the UI/metadata, scored on the cleaned frame (the edge
    # preprocessor has already applied the condition-specific correction chain).
    quality = preprocessor.assess(clean_frame, weather_condition)

    detections = detector.detect(clean_frame)
    violations = analyze(detections, clean_frame)
    road_users = summarize(detections)

    # ANPR runs on the FULL-RESOLUTION, weather-corrected frame — letterboxing to
    # 640x640 for detection throws away the plate detail OCR needs. Detection
    # boxes are in 640x640 space, so each is mapped back to original pixels
    # before cropping. (Built lazily: skipped entirely when there are no
    # violations to read plates for.)
    anpr_frame = (
        edge_preprocessor.enhance_full_resolution(image, weather_condition)
        if violations else None
    )

    vehicles_by_id = {d["id"]: d for d in detections}
    for v in violations:
        vehicle = vehicles_by_id.get(v["vehicle_id"])
        bbox = vehicle["bbox"] if vehicle else v.get("bbox")
        if bbox:
            orig_bbox = edge_preprocessor.unletterbox_bbox(bbox, image.shape)
            v["license_plate"] = plate_service.read_from_vehicle(anpr_frame, orig_bbox)
        else:
            v["license_plate"] = None

    captured_at = datetime.utcnow()
    annotated = annotate(clean_frame, detections, violations)
    annotated = watermark(annotated, location, captured_at.strftime("%Y-%m-%d %H:%M"))
    annotated = label_condition(annotated, weather_condition)
    evidence_path = save_evidence(annotated)
    evidence_id = evidence_path.stem

    records = [
        Violation(
            image_path=str(upload_path),
            annotated_image_path=str(evidence_path),
            violation_type=v["type"],
            severity=v["severity"],
            confidence=v["confidence"],
            vehicle_type=v["vehicle_type"],
            license_plate=v.get("license_plate"),
            location=location,
            timestamp=captured_at,
        )
        for v in violations
    ]
    db.add_all(records)
    db.commit()

    save_metadata(evidence_id, {
        "evidence_id": evidence_id,
        "timestamp": captured_at.isoformat(),
        "location": location,
        "original_image": upload_path.name,
        "annotated_image": evidence_path.name,
        "weather_condition": weather_condition,
        "quality": asdict(quality),
        "road_users": road_users,
        "violations": [
            {k: v[k] for k in ("type", "severity", "confidence", "vehicle_type", "license_plate")}
            for v in violations
        ],
    })

    return AnalysisResult(
        quality=asdict(quality),
        weather_condition=weather_condition,
        detections=sum(r["count"] for r in road_users),
        road_users=road_users,
        violations=[ViolationOut.model_validate(r) for r in records],
        evidence_url=f"/evidence/{evidence_path.name}",
    )


@router.post("/upload", response_model=AnalysisResult)
async def analyze_image(
    file: UploadFile = File(...),
    location: str = Form("Unknown"),
    db: Session = Depends(get_db),
):
    """Upload → preprocess → detect → flag violations → store evidence."""
    return process_image(await file.read(), location, db)


@router.post("/batch-upload", response_model=BatchResult)
async def analyze_batch(
    files: list[UploadFile] = File(...),
    location: str = Form("Unknown"),
    db: Session = Depends(get_db),
):
    """Run the pipeline over several images in one request."""
    results = [process_image(await f.read(), location, db) for f in files]
    return BatchResult(
        processed=len(results),
        total_violations=sum(len(r.violations) for r in results),
        results=results,
    )

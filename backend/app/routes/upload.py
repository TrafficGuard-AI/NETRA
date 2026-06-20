from dataclasses import asdict
from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.database.models import Violation
from app.models import preprocessor
from app.models.detector import detector, summarize
from app.models.plates import plate_service
from app.models.violation import analyze
from app.schemas import AnalysisResult, BatchResult, ViolationOut
from app.utils.annotator import annotate, watermark
from app.utils.evidence import save_evidence, save_metadata, save_upload

router = APIRouter()


def process_image(raw: bytes, location: str, db: Session) -> AnalysisResult:
    """The full pipeline for one image — shared by /upload and /batch-upload."""
    upload_path, image = save_upload(raw)

    enhanced, quality = preprocessor.preprocess(image)
    detections = detector.detect(enhanced)
    violations = analyze(detections, enhanced)
    road_users = summarize(detections)

    # For each violation, OCR the plate from the offending vehicle's crop only
    vehicles_by_id = {d["id"]: d for d in detections}
    for v in violations:
        vehicle = vehicles_by_id.get(v["vehicle_id"])
        bbox = vehicle["bbox"] if vehicle else v.get("bbox")
        v["license_plate"] = plate_service.read_from_vehicle(enhanced, bbox) if bbox else None

    captured_at = datetime.utcnow()
    annotated = annotate(enhanced, detections, violations)
    annotated = watermark(annotated, location, captured_at.strftime("%Y-%m-%d %H:%M"))
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
        "quality": asdict(quality),
        "road_users": road_users,
        "violations": [
            {k: v[k] for k in ("type", "severity", "confidence", "vehicle_type", "license_plate")}
            for v in violations
        ],
    })

    return AnalysisResult(
        quality=asdict(quality),
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

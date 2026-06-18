from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.database.models import Violation
from app.models import preprocessor
from app.models.detector import detector
from app.models.violation import analyze
from app.schemas import AnalysisResult, ViolationOut
from app.utils.annotator import annotate
from app.utils.evidence import save_evidence, save_upload

router = APIRouter()


@router.post("/upload", response_model=AnalysisResult)
async def analyze_image(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Upload → preprocess → detect → flag violations → store evidence."""
    raw = await file.read()
    upload_path, image = save_upload(raw)

    enhanced, score = preprocessor.preprocess(image)
    detections = detector.detect(enhanced)
    violations = analyze(detections)

    annotated = annotate(enhanced, detections, violations)
    evidence_path = save_evidence(annotated)

    records = [
        Violation(
            image_path=str(upload_path),
            annotated_image_path=str(evidence_path),
            violation_type=v["type"],
            severity=v["severity"],
            confidence=v["confidence"],
            vehicle_type=v["vehicle_type"],
        )
        for v in violations
    ]
    db.add_all(records)
    db.commit()

    return AnalysisResult(
        quality_score=score,
        detections=len(detections),
        violations=[ViolationOut.model_validate(r) for r in records],
        evidence_url=f"/evidence/{evidence_path.name}",
    )

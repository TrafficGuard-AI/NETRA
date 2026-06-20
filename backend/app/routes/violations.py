from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.database.models import Violation
from app.models.violation import catalog
from app.schemas import RuleInfo, ViolationOut, ViolationStatusUpdate
from app.utils.evidence import load_metadata

router = APIRouter()

ALLOWED_STATUS = {"pending", "confirmed", "dismissed"}


@router.get("/rules", response_model=list[RuleInfo])
def list_rules():
    """The violation catalogue and each rule's current status."""
    return catalog()


@router.get("/violations", response_model=list[ViolationOut])
def list_violations(
    type: str | None = None,
    severity: str | None = None,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    stmt = select(Violation).order_by(Violation.timestamp.desc())
    if type:
        stmt = stmt.where(Violation.violation_type == type)
    if severity:
        stmt = stmt.where(Violation.severity == severity)
    return db.scalars(stmt.limit(limit)).all()


@router.get("/violations/{violation_id}", response_model=ViolationOut)
def get_violation(violation_id: int, db: Session = Depends(get_db)):
    violation = db.get(Violation, violation_id)
    if violation is None:
        raise HTTPException(status_code=404, detail="Violation not found")
    return violation


@router.patch("/violations/{violation_id}", response_model=ViolationOut)
def update_status(violation_id: int, body: ViolationStatusUpdate, db: Session = Depends(get_db)):
    """Review action: confirm or dismiss a violation."""
    if body.status not in ALLOWED_STATUS:
        raise HTTPException(status_code=422, detail=f"status must be one of {ALLOWED_STATUS}")
    violation = db.get(Violation, violation_id)
    if violation is None:
        raise HTTPException(status_code=404, detail="Violation not found")
    violation.status = body.status
    db.commit()
    return violation


@router.get("/violations/{violation_id}/evidence")
def get_evidence(violation_id: int, db: Session = Depends(get_db)):
    """The evidence package (metadata + image links) for a violation."""
    violation = db.get(Violation, violation_id)
    if violation is None:
        raise HTTPException(status_code=404, detail="Violation not found")
    evidence_id = Path(violation.annotated_image_path).stem
    meta = load_metadata(evidence_id)
    if meta is None:
        raise HTTPException(status_code=404, detail="Evidence package not found")
    return meta

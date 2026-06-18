from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.database.models import Violation
from app.schemas import ViolationOut

router = APIRouter()


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

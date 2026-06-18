from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.database.models import Violation

router = APIRouter()


@router.get("/analytics/summary")
def summary(db: Session = Depends(get_db)):
    total = db.scalar(select(func.count(Violation.id))) or 0
    high = db.scalar(
        select(func.count(Violation.id)).where(Violation.severity == "HIGH")
    ) or 0
    return {"total": total, "high_severity": high}


@router.get("/analytics/by-type")
def by_type(db: Session = Depends(get_db)):
    rows = db.execute(
        select(Violation.violation_type, func.count(Violation.id))
        .group_by(Violation.violation_type)
    ).all()
    return [{"type": t, "count": c} for t, c in rows]

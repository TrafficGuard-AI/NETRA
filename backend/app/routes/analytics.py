from datetime import datetime, time

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
    avg_conf = db.scalar(select(func.avg(Violation.confidence))) or 0.0
    midnight = datetime.combine(datetime.utcnow().date(), time.min)
    today = db.scalar(
        select(func.count(Violation.id)).where(Violation.timestamp >= midnight)
    ) or 0
    return {
        "total": total,
        "high_severity": high,
        "avg_confidence": round(avg_conf, 3),
        "today": today,
    }


@router.get("/analytics/by-type")
def by_type(db: Session = Depends(get_db)):
    rows = db.execute(
        select(Violation.violation_type, func.count(Violation.id))
        .group_by(Violation.violation_type)
    ).all()
    return [{"type": t, "count": c} for t, c in rows]


@router.get("/analytics/trends")
def trends(db: Session = Depends(get_db)):
    """Violations per day, oldest first — powers the trend line."""
    day = func.date(Violation.timestamp)
    rows = db.execute(
        select(day, func.count(Violation.id)).group_by(day).order_by(day)
    ).all()
    return [{"date": d, "count": c} for d, c in rows]


@router.get("/analytics/top-plates")
def top_plates(limit: int = 5, db: Session = Depends(get_db)):
    """Most frequently flagged plates (top offenders)."""
    rows = db.execute(
        select(Violation.license_plate, func.count(Violation.id))
        .where(Violation.license_plate.isnot(None))
        .group_by(Violation.license_plate)
        .order_by(func.count(Violation.id).desc())
        .limit(limit)
    ).all()
    return [{"plate": p, "count": c} for p, c in rows]

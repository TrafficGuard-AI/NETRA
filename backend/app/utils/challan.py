"""Challan-evidence store.

For every detected violation we file a challan-ready record:
  • the offending-vehicle crop is saved on disk under
        challans/<two_wheeler|four_wheeler>/<VIOLATION_TYPE>/<uuid>.jpg
  • a document with all the challan details is inserted into MongoDB.

Mongo writes are best-effort — if the DB is down, the crops are still saved.
"""

import uuid
from datetime import datetime

import cv2
import numpy as np

from app.config import settings
from app.database.mongo import challans

# The two top-level "folders" the user asked for.
_TWO_WHEELER = {"Two-Wheeler", "Bicycle"}


def vehicle_class(category: str | None) -> str:
    return "two_wheeler" if category in _TWO_WHEELER else "four_wheeler"


def _save_crop(annotated: np.ndarray, bbox, vclass: str, vtype: str) -> str:
    """Save the offending vehicle's crop into the class/violation folder tree."""
    folder = settings.challan_dir / vclass / vtype
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{uuid.uuid4().hex}.jpg"
    x1, y1, x2, y2 = bbox
    crop = annotated[max(0, y1):y2, max(0, x1):x2]
    cv2.imwrite(str(path), crop if crop.size else annotated)
    return str(path)


def build_challan(violation: dict, annotated: np.ndarray, ctx: dict) -> dict:
    """Save the evidence crop and return the challan document (no DB write yet)."""
    h, w = annotated.shape[:2]
    bbox = violation.get("bbox") or [0, 0, w, h]
    vclass = vehicle_class(violation.get("vehicle_type"))
    vtype = violation["type"]
    return {
        "violation_id": None,  # filled in by the caller once the SQL row has an id
        "vehicle_class": vclass,
        "vehicle_type": violation.get("vehicle_type"),
        "violation_type": vtype,
        "severity": violation.get("severity"),
        "confidence": violation.get("confidence"),
        "license_plate": violation.get("license_plate"),
        "location": ctx.get("location"),
        "weather_condition": ctx.get("weather_condition"),
        "source": ctx.get("source", "image"),
        "status": "pending",
        "bbox": bbox,
        "evidence_path": _save_crop(annotated, bbox, vclass, vtype),
        "annotated_image": ctx.get("annotated_image"),
        "timestamp": ctx.get("timestamp"),
        "created_at": datetime.utcnow(),
    }


def save_challans(docs: list[dict]) -> None:
    """Best-effort bulk insert of challan documents into MongoDB."""
    if not docs:
        return
    col = challans()
    if col is None:
        return
    try:
        col.insert_many([dict(d) for d in docs])  # copy so caller's dicts keep no _id
    except Exception as exc:  # noqa: BLE001
        print(f"[mongo] challan insert failed: {exc}")

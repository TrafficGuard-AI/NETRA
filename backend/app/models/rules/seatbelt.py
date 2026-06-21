"""Seatbelt non-compliance.

Auto-enables when a seatbelt-detection YOLO weight is present at
`settings.seatbelt_weights`. The model has a single ``seat_belt`` class, so the
violation is the *absence* of a belt: each car is cropped, upscaled and run
through the model, and flagged when no belt is found.

Because this is absence-based it is inherently false-positive-prone (a car seen
from behind, or heavily occluded, has no visible belt). To limit that we only
inspect cars large enough for a belt to be resolvable.
"""

from pathlib import Path

import cv2

from app.config import settings

from .base import Scene, violation

CODE = "SEATBELT_NON_COMPLIANCE"
NAME = "Seatbelt non-compliance"
SEVERITY = "MEDIUM"


def status() -> str:
    return "active" if Path(settings.seatbelt_weights).exists() else "needs-weight"


class _SeatbeltModel:
    def __init__(self):
        self._model = None

    @property
    def model(self):
        if self._model is None:
            from ultralytics import YOLO

            self._model = YOLO(settings.seatbelt_weights)
        return self._model

    def has_belt(self, crop) -> bool:
        result = self.model(
            crop, imgsz=settings.seatbelt_imgsz, conf=settings.seatbelt_conf, verbose=False
        )[0]
        return len(result.boxes) > 0


_model = _SeatbeltModel()


def _upscale(crop):
    """Enlarge a small car crop so the belt is resolvable for the detector."""
    h = crop.shape[0]
    scale = 192.0 / h if h else 1.0
    if scale > 1.0:
        crop = cv2.resize(crop, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    return crop


def check(scene: Scene) -> list[dict]:
    if status() != "active":
        return []

    out = []
    for v in scene.vehicles:
        if v["category"] != "Car":
            continue
        x1, y1, x2, y2 = v["bbox"]
        if (y2 - y1) < settings.seatbelt_min_car_height:
            continue
        crop = scene.image[max(0, y1):y2, max(0, x1):x2]
        if not crop.size:
            continue
        if _model.has_belt(_upscale(crop)):
            continue  # belt found → compliant
        out.append(violation(CODE, SEVERITY, v, "Driver without a seatbelt"))
    return out

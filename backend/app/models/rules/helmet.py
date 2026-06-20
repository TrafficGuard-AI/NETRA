"""Helmet non-compliance.

Auto-enables when a helmet-detection YOLO weight is present at
`settings.helmet_weights`. The model runs on the full frame (heads sit above
the bike box, so cropping the vehicle misses them) at a higher resolution
(small heads vanish at 640). Each "no helmet" box is attributed to the
nearest two-wheeler.
"""

from pathlib import Path

from app.config import settings

from .base import Scene, violation

CODE = "HELMET_NON_COMPLIANCE"
NAME = "Helmet non-compliance"
SEVERITY = "HIGH"


def status() -> str:
    return "active" if Path(settings.helmet_weights).exists() else "needs-weight"


def _is_no_helmet(label: str) -> bool:
    l = label.lower()
    return ("helmet" in l and ("without" in l or "no" in l)) or l == "head"


def _iou(a: list[int], b: list[int]) -> float:
    ix1, iy1 = max(a[0], b[0]), max(a[1], b[1])
    ix2, iy2 = min(a[2], b[2]), min(a[3], b[3])
    inter = max(0, ix2 - ix1) * max(0, iy2 - iy1)
    if not inter:
        return 0.0
    area_a = (a[2] - a[0]) * (a[3] - a[1])
    area_b = (b[2] - b[0]) * (b[3] - b[1])
    return inter / (area_a + area_b - inter)


class _HelmetModel:
    def __init__(self):
        self._model = None

    @property
    def model(self):
        if self._model is None:
            from ultralytics import YOLO

            self._model = YOLO(settings.helmet_weights)
        return self._model

    def no_helmet_boxes(self, image) -> list[tuple[list[int], float]]:
        result = self.model(
            image, imgsz=settings.helmet_imgsz, conf=settings.helmet_conf, verbose=False
        )[0]
        names = result.names
        return [
            ([int(v) for v in b.xyxy[0].tolist()], float(b.conf[0]))
            for b in result.boxes
            if _is_no_helmet(names[int(b.cls[0])])
        ]


_model = _HelmetModel()


def _match_vehicle(box: list[int], vehicles: list[dict]) -> dict | None:
    """Two-wheeler that best overlaps the bare-head box."""
    best, best_iou = None, 0.0
    for v in vehicles:
        if v["category"] != "Two-Wheeler":
            continue
        score = _iou(box, v["bbox"])
        if score > best_iou:
            best, best_iou = v, score
    return best


def check(scene: Scene) -> list[dict]:
    if status() != "active":
        return []

    seen_vehicles: set[int] = set()
    out = []
    for box, conf in _model.no_helmet_boxes(scene.image):
        match = _match_vehicle(box, scene.vehicles)
        vid = match["id"] if match else -1
        if vid in seen_vehicles and vid != -1:
            continue
        seen_vehicles.add(vid)
        veh = {
            "id": vid,
            "category": "Two-Wheeler",
            "bbox": box,
            "confidence": round(conf, 3),
        }
        out.append(violation(CODE, SEVERITY, veh, "Rider without a helmet"))
    return out

"""Wrong-side driving.

Auto-enables when a rear-detection YOLO weight is present at
`settings.wrong_side_weights`. Enforcement cameras face oncoming traffic, so a
compliant vehicle shows its FRONT. A vehicle whose REAR faces the camera is
heading away against the flow — i.e. driving on the wrong side. The model emits
a "back"/"rear" class; each such box is attributed to the vehicle it overlaps.

Note: this assumes a one-way / oncoming-traffic camera. On a genuine two-way
road, seeing a rear is normal — there it should be scoped to a lane ROI.
"""

from pathlib import Path

from app.config import settings

from .base import Scene, violation

CODE = "WRONG_SIDE_DRIVING"
NAME = "Wrong-side driving"
SEVERITY = "HIGH"


def status() -> str:
    # Active via a rear-detection model (images) OR motion-based enforcement (video).
    if Path(settings.wrong_side_weights).exists() or settings.wrong_side_enforcement:
        return "active"
    return "needs-config"


def _is_rear(label: str) -> bool:
    l = label.lower()
    return "back" in l or "rear" in l


def _iou(a: list[int], b: list[int]) -> float:
    ix1, iy1 = max(a[0], b[0]), max(a[1], b[1])
    ix2, iy2 = min(a[2], b[2]), min(a[3], b[3])
    inter = max(0, ix2 - ix1) * max(0, iy2 - iy1)
    if not inter:
        return 0.0
    area_a = (a[2] - a[0]) * (a[3] - a[1])
    area_b = (b[2] - b[0]) * (b[3] - b[1])
    return inter / (area_a + area_b - inter)


class _WrongSideModel:
    def __init__(self):
        self._model = None
        self._all_rear = None  # True if every class is a rear class (single-class model)

    @property
    def model(self):
        if self._model is None:
            from ultralytics import YOLO

            self._model = YOLO(settings.wrong_side_weights)
            names = self._model.names.values()
            # A single-class "rear" detector may not name its class back/rear —
            # if none of the classes look front-facing, treat every box as rear.
            self._all_rear = not any(_is_rear(n) for n in names)
        return self._model

    def rear_boxes(self, image) -> list[tuple[list[int], float]]:
        result = self.model(
            image, imgsz=settings.wrong_side_imgsz, conf=settings.wrong_side_conf, verbose=False
        )[0]
        names = result.names
        return [
            ([int(v) for v in b.xyxy[0].tolist()], float(b.conf[0]))
            for b in result.boxes
            if self._all_rear or _is_rear(names[int(b.cls[0])])
        ]


_model = _WrongSideModel()


def _match_vehicle(box: list[int], vehicles: list[dict]) -> dict | None:
    """Vehicle that best overlaps the rear box."""
    best, best_iou = None, 0.2
    for v in vehicles:
        score = _iou(box, v["bbox"])
        if score > best_iou:
            best, best_iou = v, score
    return best


def check(scene: Scene) -> list[dict]:
    # This is the model-based (single-image) path: it needs the rear-detection
    # weight. Motion-based enforcement (video) is handled by the video tracker,
    # so do NOT run the model just because enforcement is on.
    if not Path(settings.wrong_side_weights).exists():
        return []

    seen_vehicles: set[int] = set()
    out = []
    for box, conf in _model.rear_boxes(scene.image):
        match = _match_vehicle(box, scene.vehicles)
        if match:
            vid = match["id"]
            if vid in seen_vehicles:
                continue
            seen_vehicles.add(vid)
            veh = match
        else:
            veh = {"id": -1, "category": "Vehicle", "bbox": box, "confidence": round(conf, 3)}
        out.append(violation(CODE, SEVERITY, veh, "Vehicle facing away — driving against traffic"))
    return out

"""YOLOv8 detection wrapper.

Detects road users (COCO), maps them to display categories, and counts
occupants per vehicle by how much each person box sits inside it.
"""

from collections import Counter

import numpy as np

from app.config import settings

# COCO class id -> (kind, label, display category)
COCO_MAP = {
    0: ("person", "person", "Person"),
    1: ("vehicle", "bicycle", "Bicycle"),
    2: ("vehicle", "car", "Car"),
    3: ("vehicle", "motorcycle", "Two-Wheeler"),
    5: ("vehicle", "bus", "Public Transport"),
    7: ("vehicle", "truck", "Heavy Vehicle"),
    9: ("signal", "traffic light", "Signal"),
}

# A person counts as an occupant if at least this fraction sits inside a vehicle.
MIN_CONTAINMENT = 0.2


def _containment(person: list[int], vehicle: list[int]) -> float:
    """Fraction of the person box area that lies inside the vehicle box."""
    ix1, iy1 = max(person[0], vehicle[0]), max(person[1], vehicle[1])
    ix2, iy2 = min(person[2], vehicle[2]), min(person[3], vehicle[3])
    inter = max(0, ix2 - ix1) * max(0, iy2 - iy1)
    area = (person[2] - person[0]) * (person[3] - person[1])
    return inter / area if area else 0.0


def _assign_occupants(detections: list[dict]) -> None:
    """Attribute each person to the vehicle that best contains them."""
    vehicles = [d for d in detections if d["kind"] == "vehicle"]
    for person in (d for d in detections if d["kind"] == "person"):
        best, best_c = None, MIN_CONTAINMENT
        for v in vehicles:
            c = _containment(person["bbox"], v["bbox"])
            if c > best_c:
                best, best_c = v, c
        if best is not None:
            best["occupants"] += 1


def summarize(detections: list[dict]) -> list[dict]:
    """Road-user counts grouped by category, most common first (no signals)."""
    counts = Counter(
        d["category"] for d in detections if d["kind"] in ("vehicle", "person")
    )
    return [{"category": k, "count": v} for k, v in counts.most_common()]


class Detector:
    """Thin YOLOv8 wrapper. The model is loaded lazily on first use."""

    def __init__(self):
        self._model = None

    @property
    def model(self):
        if self._model is None:
            from ultralytics import YOLO

            self._model = YOLO(settings.yolo_weights)
        return self._model

    def detect(self, image: np.ndarray) -> list[dict]:
        """Run inference (conf filter + NMS are built into YOLO)."""
        results = self.model(image, conf=settings.confidence_threshold, verbose=False)[0]

        detections = []
        for i, box in enumerate(results.boxes):
            cls = int(box.cls[0])
            if cls not in COCO_MAP:
                continue
            kind, label, category = COCO_MAP[cls]
            detections.append({
                "id": i,
                "kind": kind,
                "label": label,
                "category": category,
                "bbox": [int(v) for v in box.xyxy[0].tolist()],
                "confidence": round(float(box.conf[0]), 3),
                "occupants": 0,
            })

        _assign_occupants(detections)
        return detections


detector = Detector()

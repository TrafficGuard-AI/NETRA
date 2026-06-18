import numpy as np

from app.config import settings

# COCO class id -> our category label
VEHICLE_CATEGORIES = {
    2: "Car",
    3: "Two-Wheeler",
    5: "Public Transport",
    7: "Heavy Vehicle",
    1: "Bicycle",
}
PERSON_CLASS = 0


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
        """Run inference and return vehicle + person detections."""
        results = self.model(image, conf=settings.confidence_threshold, verbose=False)[0]

        detections = []
        for i, box in enumerate(results.boxes):
            cls = int(box.cls[0])
            if cls != PERSON_CLASS and cls not in VEHICLE_CATEGORIES:
                continue
            detections.append({
                "id": i,
                "class": "person" if cls == PERSON_CLASS else "vehicle",
                "category": VEHICLE_CATEGORIES.get(cls, "Person"),
                "bbox": [int(v) for v in box.xyxy[0].tolist()],
                "confidence": round(float(box.conf[0]), 3),
            })
        return detections


detector = Detector()

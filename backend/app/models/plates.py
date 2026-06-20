"""License-plate detection + OCR.

For each violation, the offending vehicle's bounding box is cropped from the
frame and plate detection + OCR runs on that crop only — more accurate and
cheaper than scanning the whole frame.
"""

from pathlib import Path

import cv2
import numpy as np

from app.config import settings
from app.models.ocr import plate_reader


def _containment(inner: list[int], outer: list[int]) -> float:
    ix1, iy1 = max(inner[0], outer[0]), max(inner[1], outer[1])
    ix2, iy2 = min(inner[2], outer[2]), min(inner[3], outer[3])
    inter = max(0, ix2 - ix1) * max(0, iy2 - iy1)
    area = (inner[2] - inner[0]) * (inner[3] - inner[1])
    return inter / area if area else 0.0


def _prep(crop: np.ndarray) -> np.ndarray:
    """Upscale small plate crops to a workable height, then boost contrast."""
    scale = max(2.0, 96.0 / max(crop.shape[0], 1))
    up = cv2.resize(crop, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    gray = cv2.cvtColor(up, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    return clahe.apply(gray)


class PlateService:
    def __init__(self):
        self._dedicated = None

    def _model(self):
        """Dedicated plate model if available, else the shared helmet model."""
        if Path(settings.plate_weights).exists():
            if self._dedicated is None:
                from ultralytics import YOLO

                self._dedicated = YOLO(settings.plate_weights)
            return self._dedicated
        if Path(settings.helmet_weights).exists():
            from app.models.rules.helmet import _model as helmet_model

            return helmet_model.model
        return None

    def detect(self, image: np.ndarray) -> list[list[int]]:
        model = self._model()
        if model is None:
            return []
        result = model(image, imgsz=settings.helmet_imgsz, conf=settings.plate_conf, verbose=False)[0]
        names = result.names
        return [
            [int(v) for v in b.xyxy[0].tolist()]
            for b in result.boxes
            if "plate" in names[int(b.cls[0])].lower()
        ]

    def read_from_vehicle(self, image: np.ndarray, vehicle_bbox: list[int]) -> str | None:
        """Crop the vehicle region, detect plate within it, OCR and return text."""
        x1, y1, x2, y2 = vehicle_bbox
        vehicle_crop = image[max(0, y1):y2, max(0, x1):x2]
        if not vehicle_crop.size:
            return None
        for box in self.detect(vehicle_crop):
            bx1, by1, bx2, by2 = box
            plate_crop = vehicle_crop[max(0, by1):by2, max(0, bx1):bx2]
            if not plate_crop.size:
                continue
            text = plate_reader.read(_prep(plate_crop))
            if text:
                return text
        return None


plate_service = PlateService()

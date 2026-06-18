import cv2
import numpy as np

VIOLATION_COLOR = (0, 0, 255)  # red (BGR)
OK_COLOR = (0, 200, 0)  # green


def annotate(image: np.ndarray, detections: list[dict], violations: list[dict]) -> np.ndarray:
    """Draw detection boxes (green) and violation boxes (red) onto a copy."""
    canvas = image.copy()
    flagged = {v["vehicle_id"] for v in violations}

    for d in detections:
        if d["id"] in flagged or d["class"] != "vehicle":
            continue
        _box(canvas, d["bbox"], f"{d['category']} {d['confidence']:.0%}", OK_COLOR)

    for v in violations:
        label = f"{v['type']} {v['confidence']:.0%}"
        _box(canvas, v["bbox"], label, VIOLATION_COLOR)

    return canvas


def _box(img: np.ndarray, bbox: list[int], label: str, color: tuple) -> None:
    x1, y1, x2, y2 = bbox
    cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
    (w, h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
    cv2.rectangle(img, (x1, y1 - h - 6), (x1 + w + 4, y1), color, -1)
    cv2.putText(img, label, (x1 + 2, y1 - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

import cv2
import numpy as np

VIOLATION_COLOR = (0, 0, 255)  # red (BGR)
OK_COLOR = (0, 200, 0)  # green


def annotate(
    image: np.ndarray,
    detections: list[dict],
    violations: list[dict],
) -> np.ndarray:
    """Draw detection (green), violation (red) and plate (teal) boxes on a copy."""
    canvas = image.copy()
    flagged = {v["vehicle_id"] for v in violations}

    for d in detections:
        if d["id"] in flagged or d["kind"] != "vehicle":
            continue
        label = f"{d['category']} {d['confidence']:.0%}"
        if d["occupants"] >= 2:
            label += f" x{d['occupants']}"
        _box(canvas, d["bbox"], label, OK_COLOR)

    for v in violations:
        label = f"{v['type']} {v['confidence']:.0%}"
        if v.get("license_plate"):
            label += f" [{v['license_plate']}]"
        _box(canvas, v["bbox"], label, VIOLATION_COLOR)

    return canvas


def _box(img: np.ndarray, bbox: list[int], label: str, color: tuple) -> None:
    x1, y1, x2, y2 = bbox
    cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
    (w, h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
    cv2.rectangle(img, (x1, y1 - h - 6), (x1 + w + 4, y1), color, -1)
    cv2.putText(img, label, (x1 + 2, y1 - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)


def label_condition(image: np.ndarray, condition: str) -> np.ndarray:
    """Burn the active weather condition into the top-left of the evidence frame.

    Drawn in place (callers pass an already-copied annotated frame). A black
    outline under coloured text keeps it legible over any background.
    """
    text = f"Weather: {condition}"
    org = (10, 26)
    cv2.putText(image, text, org, cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 3, cv2.LINE_AA)
    cv2.putText(image, text, org, cv2.FONT_HERSHEY_SIMPLEX, 0.6, (60, 220, 255), 1, cv2.LINE_AA)
    return image


def watermark(image: np.ndarray, location: str, timestamp: str) -> np.ndarray:
    """Burn a provenance bar (brand · location · time) along the bottom."""
    h, w = image.shape[:2]
    bar = max(28, h // 26)
    overlay = image.copy()
    cv2.rectangle(overlay, (0, h - bar), (w, h), (0, 0, 0), -1)
    image = cv2.addWeighted(overlay, 0.55, image, 0.45, 0)

    scale = bar / 42
    y = h - int(bar * 0.32)
    cv2.putText(image, "TrafficGuard AI", (12, y), cv2.FONT_HERSHEY_SIMPLEX, scale, (120, 220, 200), 1, cv2.LINE_AA)
    right = f"{location}  |  {timestamp}"
    (tw, _), _ = cv2.getTextSize(right, cv2.FONT_HERSHEY_SIMPLEX, scale, 1)
    cv2.putText(image, right, (w - tw - 12, y), cv2.FONT_HERSHEY_SIMPLEX, scale, (240, 240, 240), 1, cv2.LINE_AA)
    return image

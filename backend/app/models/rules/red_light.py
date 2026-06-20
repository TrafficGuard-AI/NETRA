"""Red-light running.

Classifies each detected traffic light by HSV colour. When a red signal is
present, vehicles past the configured stop line are flagged. Opt-in via
`settings.red_light_enforcement` since the stop line is camera-specific.
"""

import cv2
import numpy as np

from app.config import settings

from .base import Scene, violation

CODE = "RED_LIGHT_VIOLATION"
NAME = "Red-light running"
SEVERITY = "HIGH"


def status() -> str:
    return "active" if settings.red_light_enforcement else "needs-config"


def _is_red(crop: np.ndarray) -> bool:
    hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
    red = cv2.inRange(hsv, (0, 90, 90), (10, 255, 255)) | cv2.inRange(
        hsv, (160, 90, 90), (179, 255, 255)
    )
    green = cv2.inRange(hsv, (40, 60, 60), (90, 255, 255))
    return int(red.sum()) > int(green.sum()) and red.sum() > 0


def check(scene: Scene) -> list[dict]:
    if status() != "active" or not scene.signals:
        return []

    red_on = any(
        _is_red(scene.image[max(0, s["bbox"][1]):s["bbox"][3], max(0, s["bbox"][0]):s["bbox"][2]])
        for s in scene.signals
        if scene.image[max(0, s["bbox"][1]):s["bbox"][3], max(0, s["bbox"][0]):s["bbox"][2]].size
    )
    if not red_on:
        return []

    stop_line = int(scene.image.shape[0] * settings.stop_line_frac)
    return [
        violation(CODE, SEVERITY, v, "Vehicle past the stop line on a red signal")
        for v in scene.vehicles
        if v["bbox"][3] > stop_line
    ]

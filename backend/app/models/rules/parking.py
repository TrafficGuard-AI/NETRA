"""Illegal parking — zone-based detection.

No-parking zones are defined in settings.parking_zones as a JSON array of
polygons. Each polygon is a list of [x, y] fractions of the frame size
(0.0–1.0), so the zones are resolution-independent.

A vehicle whose bounding-box centre falls inside any zone is flagged.

For VIDEO: the VideoTracker handles dwell-time filtering (N consecutive
frames inside a zone → flag). For IMAGES: single-frame, instant flag.
"""

import json
from typing import List, Tuple

from app.config import settings

from .base import Scene, violation

CODE = "ILLEGAL_PARKING"
NAME = "Illegal parking"
SEVERITY = "MEDIUM"

# Parsed once at import time so JSON parsing doesn't happen per frame.
_zones: List[List[Tuple[float, float]]] = []


def _load_zones() -> List[List[Tuple[float, float]]]:
    try:
        raw = json.loads(settings.parking_zones)
        return [[(float(p[0]), float(p[1])) for p in poly] for poly in raw if len(poly) >= 3]
    except Exception:
        return []


_zones = _load_zones()


def status() -> str:
    if _zones:
        return "active"
    return "needs-config"


def _point_in_polygon(px: float, py: float, polygon: List[Tuple[float, float]]) -> bool:
    """Ray-casting algorithm for point-in-polygon test."""
    n = len(polygon)
    inside = False
    j = n - 1
    for i in range(n):
        xi, yi = polygon[i]
        xj, yj = polygon[j]
        if ((yi > py) != (yj > py)) and (px < (xj - xi) * (py - yi) / (yj - yi + 1e-9) + xi):
            inside = not inside
        j = i
    return inside


def point_in_any_zone(fx: float, fy: float) -> bool:
    """Check whether normalised (0–1) point falls in any no-parking zone."""
    return any(_point_in_polygon(fx, fy, z) for z in _zones)


def check(scene: Scene) -> list[dict]:
    if not _zones:
        return []

    h, w = scene.image.shape[:2]
    out = []
    seen: set[int] = set()

    for vehicle in scene.vehicles:
        vid = vehicle["id"]
        if vid in seen:
            continue
        x1, y1, x2, y2 = vehicle["bbox"]
        cx = ((x1 + x2) / 2) / w
        cy = ((y1 + y2) / 2) / h
        if point_in_any_zone(cx, cy):
            seen.add(vid)
            out.append(violation(CODE, SEVERITY, vehicle, "Vehicle parked in a no-parking zone"))

    return out

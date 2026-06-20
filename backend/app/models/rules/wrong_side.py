"""Wrong-side driving — planned.

Needs per-camera lane direction (ROI zones or lane-marking detection) to know
the expected heading. Static single frames lack motion, so this is config-led.
"""

from .base import Scene

CODE = "WRONG_SIDE_DRIVING"
NAME = "Wrong-side driving"
SEVERITY = "HIGH"


def status() -> str:
    return "planned"


def check(scene: Scene) -> list[dict]:
    return []

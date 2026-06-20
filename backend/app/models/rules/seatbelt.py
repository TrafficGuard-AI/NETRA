"""Seatbelt non-compliance — planned.

Needs a driver-region seatbelt/no-seatbelt classifier (Roboflow or a small
fine-tuned CNN). Crop each car's windshield region and classify when wired.
"""

from .base import Scene

CODE = "SEATBELT_NON_COMPLIANCE"
NAME = "Seatbelt non-compliance"
SEVERITY = "MEDIUM"


def status() -> str:
    return "planned"


def check(scene: Scene) -> list[dict]:
    return []

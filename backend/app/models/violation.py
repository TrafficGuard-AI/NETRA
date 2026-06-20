"""Violation coordinator — runs every rule against a frame.

Each rule module exposes CODE / NAME / SEVERITY, a `status()` and a
`check(scene)`. Add a new violation type by dropping a module in `rules/`
and registering it here.
"""

import numpy as np

from app.models.rules import (
    base,
    helmet,
    parking,
    red_light,
    seatbelt,
    triple_riding,
    wrong_side,
)

RULES = [triple_riding, helmet, red_light, seatbelt, wrong_side, parking]


def analyze(detections: list[dict], image: np.ndarray) -> list[dict]:
    scene = base.Scene(image=image, detections=detections)
    out: list[dict] = []
    for rule in RULES:
        out.extend(rule.check(scene))
    return out


def catalog() -> list[dict]:
    """The full violation catalogue with each rule's current status."""
    return [
        {"code": r.CODE, "name": r.NAME, "severity": r.SEVERITY, "status": r.status()}
        for r in RULES
    ]

"""Illegal parking — planned.

Needs configurable no-parking zones per camera; a vehicle inside a zone is a
violation. Wire up once zone polygons are defined in settings.
"""

from .base import Scene

CODE = "ILLEGAL_PARKING"
NAME = "Illegal parking"
SEVERITY = "MEDIUM"


def status() -> str:
    return "planned"


def check(scene: Scene) -> list[dict]:
    return []

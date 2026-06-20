from dataclasses import dataclass

import numpy as np


@dataclass
class Scene:
    """Everything a violation rule needs about one frame."""

    image: np.ndarray
    detections: list[dict]

    @property
    def vehicles(self) -> list[dict]:
        return [d for d in self.detections if d["kind"] == "vehicle"]

    @property
    def persons(self) -> list[dict]:
        return [d for d in self.detections if d["kind"] == "person"]

    @property
    def signals(self) -> list[dict]:
        return [d for d in self.detections if d["kind"] == "signal"]


def violation(code: str, severity: str, vehicle: dict, description: str) -> dict:
    """Build a violation record tied to the offending vehicle."""
    return {
        "type": code,
        "severity": severity,
        "confidence": vehicle["confidence"],
        "vehicle_id": vehicle["id"],
        "vehicle_type": vehicle["category"],
        "bbox": vehicle["bbox"],
        "description": description,
    }

from datetime import datetime

from pydantic import BaseModel


class ViolationOut(BaseModel):
    id: int
    violation_type: str
    severity: str
    confidence: float
    vehicle_type: str
    license_plate: str | None
    location: str | None
    status: str
    annotated_image_path: str
    timestamp: datetime

    class Config:
        from_attributes = True


class AnalysisResult(BaseModel):
    quality_score: int
    detections: int
    violations: list[ViolationOut]
    evidence_url: str

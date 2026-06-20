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


class QualityReport(BaseModel):
    score: int
    sharpness: int
    brightness: int
    contrast: int
    corrections: list[str]


class RoadUserCount(BaseModel):
    category: str
    count: int


class RuleInfo(BaseModel):
    code: str
    name: str
    severity: str
    status: str  # active | needs-weight | needs-config | planned


class ViolationStatusUpdate(BaseModel):
    status: str  # pending | confirmed | dismissed


class AnalysisResult(BaseModel):
    quality: QualityReport
    detections: int
    road_users: list[RoadUserCount]
    violations: list[ViolationOut]
    evidence_url: str


class BatchResult(BaseModel):
    processed: int
    total_violations: int
    results: list[AnalysisResult]

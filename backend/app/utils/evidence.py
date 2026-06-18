import uuid
from pathlib import Path

import cv2
import numpy as np

from app.config import settings


def save_upload(raw: bytes, suffix: str = ".jpg") -> tuple[Path, np.ndarray]:
    """Persist an uploaded file and decode it into a BGR array."""
    path = settings.upload_dir / f"{uuid.uuid4().hex}{suffix}"
    path.write_bytes(raw)
    image = cv2.imread(str(path))
    return path, image


def save_evidence(annotated: np.ndarray) -> Path:
    """Write an annotated evidence image and return its path."""
    path = settings.evidence_dir / f"{uuid.uuid4().hex}.jpg"
    cv2.imwrite(str(path), annotated)
    return path

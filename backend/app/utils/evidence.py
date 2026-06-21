import json
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


def save_binary_upload(raw: bytes, suffix: str = ".mp4") -> Path:
    """Persist a non-image upload, such as a video, and return its path."""
    path = settings.upload_dir / f"{uuid.uuid4().hex}{suffix}"
    path.write_bytes(raw)
    return path


def save_evidence(annotated: np.ndarray) -> Path:
    """Write an annotated evidence image and return its path."""
    path = settings.evidence_dir / f"{uuid.uuid4().hex}.jpg"
    cv2.imwrite(str(path), annotated)
    return path


def save_metadata(evidence_id: str, meta: dict) -> Path:
    """Write a JSON sidecar (the evidence package) next to the image."""
    path = settings.evidence_dir / f"{evidence_id}.json"
    path.write_text(json.dumps(meta, indent=2))
    return path


def load_metadata(evidence_id: str) -> dict | None:
    path = settings.evidence_dir / f"{evidence_id}.json"
    return json.loads(path.read_text()) if path.exists() else None

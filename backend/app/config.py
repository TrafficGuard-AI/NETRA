from pathlib import Path

from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"


class Settings(BaseSettings):
    app_name: str = "TrafficGuard AI"
    api_prefix: str = "/api"

    # Storage
    upload_dir: Path = DATA_DIR / "uploads"
    evidence_dir: Path = DATA_DIR / "evidence"
    # as_posix() keeps the SQLite URL valid on Windows (forward slashes)
    database_url: str = f"sqlite:///{(BASE_DIR / 'trafficguard.db').as_posix()}"

    # Detection
    weights_dir: Path = BASE_DIR / "backend" / "weights"
    yolo_weights: str = str(BASE_DIR / "backend" / "weights" / "yolov8n.pt")
    confidence_threshold: float = 0.4
    ocr_languages: list[str] = ["en"]

    class Config:
        env_file = ".env"


settings = Settings()

# Ensure storage dirs exist on import
settings.upload_dir.mkdir(parents=True, exist_ok=True)
settings.evidence_dir.mkdir(parents=True, exist_ok=True)
settings.weights_dir.mkdir(parents=True, exist_ok=True)

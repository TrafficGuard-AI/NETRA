import sys
from pathlib import Path

from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"

# The backend runs with CWD=backend/ (see run.bat / run.sh), so repo-root
# modules like `ultimate_edge_preprocessor` aren't importable by default.
# Put the repo root on sys.path so they can be imported package-wide.
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))


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
    # Plate OCR uses TrOCR (transformer OCR). Swap to "microsoft/trocr-small-printed"
    # for a faster, lighter model on CPU at some accuracy cost.
    trocr_model: str = "microsoft/trocr-base-printed"

    # Violation rules
    # Drop a helmet-detection YOLO weight here to auto-enable the helmet rule.
    helmet_weights: str = str(BASE_DIR / "backend" / "weights" / "helmet.pt")
    helmet_imgsz: int = 960    # higher res — small heads are missed at 640
    helmet_conf: float = 0.3

    # License plates: a dedicated plate weight if you have one, else the helmet
    # model's "Plate" class is reused automatically.
    plate_weights: str = str(BASE_DIR / "backend" / "weights" / "plate.pt")
    plate_conf: float = 0.25
    # Red-light running needs a known stop line, so it's opt-in per camera.
    red_light_enforcement: bool = False
    stop_line_frac: float = 0.6  # stop line as a fraction of image height

    class Config:
        env_file = ".env"


settings = Settings()

# Ensure storage dirs exist on import
settings.upload_dir.mkdir(parents=True, exist_ok=True)
settings.evidence_dir.mkdir(parents=True, exist_ok=True)
settings.weights_dir.mkdir(parents=True, exist_ok=True)

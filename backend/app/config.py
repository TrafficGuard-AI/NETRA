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

    # Challan evidence store (MongoDB). Documents hold the challan-ready details;
    # the offending-vehicle crops are filed under challan_dir as
    #   <two_wheeler|four_wheeler>/<VIOLATION_TYPE>/<uuid>.jpg
    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_db: str = "netra"
    mongodb_collection: str = "challans"
    challan_dir: Path = DATA_DIR / "challans"

    # Detection
    weights_dir: Path = BASE_DIR / "backend" / "weights"
    yolo_weights: str = str(BASE_DIR / "backend" / "weights" / "yolov8n.pt")
    confidence_threshold: float = 0.4
    # Plate OCR uses TrOCR (transformer OCR). Swap to "microsoft/trocr-small-printed"
    # for a faster, lighter model on CPU at some accuracy cost.
    trocr_model: str = "microsoft/trocr-base-printed"

    # Violation rules
    # Helmet/no-helmet detector. The bundled YOLO11 weight emits rider classes
    # such as driver_without_helmet and passenger_with_helmet.
    helmet_weights: str = str(BASE_DIR / "backend" / "weights" / "helmet_yolo11n_v2_best.pt")
    helmet_imgsz: int = 960    # higher res — small heads are missed at 640
    helmet_conf: float = 0.3

    # Seatbelt detector: a single-class "seat_belt" YOLO weight. A car with no
    # belt found in its (upscaled) crop is flagged, so this is absence-based.
    seatbelt_weights: str = str(BASE_DIR / "backend" / "weights" / "seatbelt.pt")
    seatbelt_imgsz: int = 320
    seatbelt_conf: float = 0.35
    # Cars shorter than this (in the 640 detection frame) are too small to
    # resolve a belt — skipped to limit false positives.
    seatbelt_min_car_height: int = 80

    # Wrong-side driving: a YOLO weight that detects a vehicle's REAR facing the
    # camera (class name containing "back"/"rear"). Seeing a rear means the
    # vehicle is heading away against oncoming-traffic cameras → wrong side.
    wrong_side_weights: str = str(BASE_DIR / "backend" / "weights" / "wrong_side.pt")
    wrong_side_imgsz: int = 640
    wrong_side_conf: float = 0.35

    # License plates: a dedicated plate weight if you have one, else the helmet
    # model's "Plate" class is reused automatically.
    plate_weights: str = str(BASE_DIR / "backend" / "weights" / "plate.pt")
    plate_conf: float = 0.25
    # Red-light running needs a known stop line, so it's opt-in per camera.
    red_light_enforcement: bool = False
    stop_line_frac: float = 0.6  # stop line as a fraction of image height

    # Wrong-side (motion-based, video only): flag vehicles moving against the
    # lane's legal flow. Opt-in per camera since the heading is camera-specific.
    wrong_side_enforcement: bool = False
    wrong_side_direction: str = "down"  # legal flow in image space: down|up|left|right
    wrong_side_min_travel: int = 60     # min net px against the flow before flagging

    video_sample_fps: float = 2.0
    max_video_frames: int = 120
    max_video_violations: int = 30

    # Illegal parking: JSON array of no-parking zones, each a list of [x, y]
    # fractions of frame size (0.0–1.0). Example for one roadside zone:
    #   PARKING_ZONES=[ [[0.0,0.7],[0.4,0.7],[0.4,1.0],[0.0,1.0]] ]
    # Empty list = parking detection disabled.
    parking_zones: str = "[]"
    # Video: how many consecutive sampled frames a vehicle must sit in a zone
    # before it is flagged (avoids flagging cars briefly stopped at traffic).
    parking_dwell_frames: int = 3

    class Config:
        env_file = ".env"


settings = Settings()

# Ensure storage dirs exist on import
settings.upload_dir.mkdir(parents=True, exist_ok=True)
settings.evidence_dir.mkdir(parents=True, exist_ok=True)
settings.weights_dir.mkdir(parents=True, exist_ok=True)
settings.challan_dir.mkdir(parents=True, exist_ok=True)

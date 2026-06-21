from dataclasses import asdict
from datetime import datetime, timedelta
from pathlib import Path
from collections import Counter

import cv2
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session

from app.config import settings
from app.database.db import get_db
from app.database.models import Violation
from app.models import preprocessor
from app.models.detector import detector, summarize
from app.models.plates import plate_service
from app.models.rules.parking import point_in_any_zone
from app.models.violation import analyze
from app.schemas import AnalysisResult, BatchResult, VideoAnalysisResult, ViolationOut
from app.utils.annotator import annotate, label_condition, watermark
from app.utils.challan import build_challan, save_challans
from app.utils.evidence import save_binary_upload, save_evidence, save_metadata, save_upload

from ultimate_edge_preprocessor import DynamicTrafficPreprocessor

router = APIRouter()

# Weather-adaptive edge preprocessor. Instantiated ONCE at import time — never
# per request — so its prebuilt gamma LUT / CLAHE objects are reused across all
# frames, keeping per-image latency low.
edge_preprocessor = DynamicTrafficPreprocessor()


def _safe_suffix(filename: str | None, default: str) -> str:
    suffix = Path(filename or "").suffix.lower()
    return suffix if suffix else default


def _is_red_signal_on(image, detections: list[dict]) -> bool:
    """Detect whether any traffic-light crop is predominantly red."""
    for signal in (d for d in detections if d["kind"] == "signal"):
        x1, y1, x2, y2 = signal["bbox"]
        crop = image[max(0, y1):y2, max(0, x1):x2]
        if not crop.size:
            continue
        hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
        red = cv2.inRange(hsv, (0, 90, 90), (10, 255, 255)) | cv2.inRange(
            hsv, (160, 90, 90), (179, 255, 255)
        )
        green = cv2.inRange(hsv, (40, 60, 60), (90, 255, 255))
        if int(red.sum()) > int(green.sum()) and red.sum() > 0:
            return True
    return False


def _bbox_center(bbox: list[int]) -> tuple[float, float]:
    return ((bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2)


# Legal traffic-flow direction (in image space) → unit vector.
_DIRECTION_VECTORS = {"down": (0.0, 1.0), "up": (0.0, -1.0), "left": (-1.0, 0.0), "right": (1.0, 0.0)}


class VideoTracker:
    """Centroid tracker for sampled video frames. Detects stop-line crossings
    (red-light) and, when an expected flow direction is given, direction-of-motion
    wrong-way driving."""

    def __init__(
        self,
        stop_line: int,
        expected_dir: tuple[float, float] | None = None,
        min_travel: int = 60,
    ):
        self.stop_line = stop_line
        self.expected_dir = expected_dir  # unit vector of legal flow, or None to disable
        self.min_travel = min_travel
        self._next_id = 1
        self._tracks: dict[int, dict] = {}

    def _match(self, vehicle: dict) -> int | None:
        cx, cy = _bbox_center(vehicle["bbox"])
        best_id, best_dist = None, 90.0
        for tid, track in self._tracks.items():
            if track["category"] != vehicle["category"]:
                continue
            tx, ty = track["center"]
            dist = ((cx - tx) ** 2 + (cy - ty) ** 2) ** 0.5
            if dist < best_dist:
                best_id, best_dist = tid, dist
        return best_id

    def best_track_id(self, bbox: list[int] | None, category: str | None = None) -> int | None:
        if not bbox:
            return None
        cx, cy = _bbox_center(bbox)
        best_id, best_dist = None, 100.0
        for tid, track in self._tracks.items():
            if category and track["category"] != category:
                continue
            tx, ty = track["center"]
            dist = ((cx - tx) ** 2 + (cy - ty) ** 2) ** 0.5
            if dist < best_dist:
                best_id, best_dist = tid, dist
        return best_id

    def update(self, detections: list[dict], red_on: bool) -> list[dict]:
        crossings: list[dict] = []
        for vehicle in (d for d in detections if d["kind"] == "vehicle"):
            tid = self._match(vehicle)
            if tid is None:
                tid = self._next_id
                self._next_id += 1
                center = _bbox_center(vehicle["bbox"])
                self._tracks[tid] = {
                    "center": center,
                    "start_center": center,
                    "bottom": vehicle["bbox"][3],
                    "category": vehicle["category"],
                    "red_flagged": False,
                    "wrong_flagged": False,
                    "park_dwell": 0,
                    "park_flagged": False,
                }
                continue

            track = self._tracks[tid]
            previous_bottom = track["bottom"]
            current_bottom = vehicle["bbox"][3]
            crossed = previous_bottom <= self.stop_line < current_bottom
            if red_on and crossed and not track["red_flagged"]:
                crossings.append({
                    "type": "RED_LIGHT_VIOLATION",
                    "severity": "HIGH",
                    "confidence": vehicle["confidence"],
                    "vehicle_id": vehicle["id"],
                    "vehicle_type": vehicle["category"],
                    "bbox": vehicle["bbox"],
                    "description": "Vehicle crossed the stop line while the signal was red",
                })
                track["red_flagged"] = True

            # Wrong-way: net travel projected onto the expected flow is negative
            # (moved against it) by more than the threshold.
            cx, cy = _bbox_center(vehicle["bbox"])
            if self.expected_dir and not track["wrong_flagged"]:
                sx, sy = track["start_center"]
                proj = (cx - sx) * self.expected_dir[0] + (cy - sy) * self.expected_dir[1]
                if proj <= -self.min_travel:
                    crossings.append({
                        "type": "WRONG_SIDE_DRIVING",
                        "severity": "HIGH",
                        "confidence": vehicle["confidence"],
                        "vehicle_id": vehicle["id"],
                        "vehicle_type": vehicle["category"],
                        "bbox": vehicle["bbox"],
                        "description": "Vehicle moving against the lane's expected direction",
                    })
                    track["wrong_flagged"] = True

            # Illegal parking: count consecutive frames inside a no-parking zone.
            # cx/cy are absolute pixels in the 640-px preprocessed frame.
            if not track["park_flagged"]:
                ncx, ncy = cx / 640, cy / 640
                if point_in_any_zone(ncx, ncy):
                    track["park_dwell"] += 1
                    if track["park_dwell"] >= settings.parking_dwell_frames:
                        crossings.append({
                            "type": "ILLEGAL_PARKING",
                            "severity": "MEDIUM",
                            "confidence": vehicle["confidence"],
                            "vehicle_id": vehicle["id"],
                            "vehicle_type": vehicle["category"],
                            "bbox": vehicle["bbox"],
                            "description": "Vehicle stationary in a no-parking zone",
                        })
                        track["park_flagged"] = True
                else:
                    track["park_dwell"] = 0

            track["center"] = (cx, cy)
            track["bottom"] = current_bottom
            track["category"] = vehicle["category"]
        return crossings


def _attach_license_plates(
    image,
    weather_condition: str,
    detections: list[dict],
    violations: list[dict],
) -> None:
    """Read plates for each violation in-place, using full-resolution crops."""
    anpr_frame = (
        edge_preprocessor.enhance_full_resolution(image, weather_condition)
        if violations else None
    )
    vehicles_by_id = {d["id"]: d for d in detections}
    for v in violations:
        vehicle = vehicles_by_id.get(v["vehicle_id"])
        bbox = vehicle["bbox"] if vehicle else v.get("bbox")
        if bbox and anpr_frame is not None:
            orig_bbox = edge_preprocessor.unletterbox_bbox(bbox, image.shape)
            v["license_plate"] = plate_service.read_from_vehicle(anpr_frame, orig_bbox)
        else:
            v["license_plate"] = None


def process_image(raw: bytes, location: str, db: Session) -> AnalysisResult:
    """The full pipeline for one image — shared by /upload and /batch-upload."""
    upload_path, image = save_upload(raw)
    # Handle a missing / undecodable frame gracefully instead of crashing.
    if image is None:
        raise HTTPException(status_code=400, detail="Could not decode the uploaded image.")

    # ── Weather-adaptive edge preprocessing ──────────────────────────────
    # Detect the scene condition (FOG / NIGHT / DAY-RAIN) and return a cleaned,
    # 640x640 letterboxed frame. Every downstream stage — detection, violation
    # analysis, ANPR, annotation and evidence — runs on this single clean frame,
    # so all bounding boxes live in the same 640x640 coordinate space and no
    # rescaling is needed.
    processed = edge_preprocessor.process(image)
    clean_frame = processed["processed_uint8"]
    weather_condition = processed["condition"]
    print(f"[edge-preprocess] {upload_path.name}: weather condition = {weather_condition}")

    # Quality report for the UI/metadata, scored on the cleaned frame (the edge
    # preprocessor has already applied the condition-specific correction chain).
    quality = preprocessor.assess(clean_frame, weather_condition)

    detections = detector.detect(clean_frame)
    violations = analyze(detections, clean_frame)
    road_users = summarize(detections)

    # ANPR runs on the full-resolution, weather-corrected frame so small plates
    # are not lost to the 640x640 detection canvas.
    _attach_license_plates(image, weather_condition, detections, violations)

    captured_at = datetime.utcnow()
    annotated = annotate(clean_frame, detections, violations)
    annotated = watermark(annotated, location, captured_at.strftime("%Y-%m-%d %H:%M"))
    annotated = label_condition(annotated, weather_condition)
    evidence_path = save_evidence(annotated)
    evidence_id = evidence_path.stem

    records = [
        Violation(
            image_path=str(upload_path),
            annotated_image_path=str(evidence_path),
            violation_type=v["type"],
            severity=v["severity"],
            confidence=v["confidence"],
            vehicle_type=v["vehicle_type"],
            license_plate=v.get("license_plate"),
            location=location,
            timestamp=captured_at,
        )
        for v in violations
    ]
    db.add_all(records)
    db.commit()

    # Challan-evidence store: file each offending vehicle's crop under
    # challans/<class>/<violation>/ and record the details in MongoDB.
    challan_ctx = {
        "location": location,
        "weather_condition": weather_condition,
        "source": "image",
        "annotated_image": str(evidence_path),
        "timestamp": captured_at,
    }
    challan_docs = []
    for v, rec in zip(violations, records):
        doc = build_challan(v, annotated, challan_ctx)
        doc["violation_id"] = rec.id
        challan_docs.append(doc)
    save_challans(challan_docs)

    save_metadata(evidence_id, {
        "evidence_id": evidence_id,
        "timestamp": captured_at.isoformat(),
        "location": location,
        "original_image": upload_path.name,
        "annotated_image": evidence_path.name,
        "weather_condition": weather_condition,
        "quality": asdict(quality),
        "road_users": road_users,
        "violations": [
            {k: v[k] for k in ("type", "severity", "confidence", "vehicle_type", "license_plate")}
            for v in violations
        ],
    })

    return AnalysisResult(
        quality=asdict(quality),
        weather_condition=weather_condition,
        detections=sum(r["count"] for r in road_users),
        road_users=road_users,
        violations=[ViolationOut.model_validate(r) for r in records],
        evidence_url=f"/evidence/{evidence_path.name}",
    )


def process_video(raw: bytes, filename: str | None, location: str, db: Session) -> VideoAnalysisResult:
    """Sample a video and run the traffic-violation pipeline over its frames."""
    video_path = save_binary_upload(raw, _safe_suffix(filename, ".mp4"))
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise HTTPException(status_code=400, detail="Could not decode the uploaded video.")

    fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    duration = round(frame_count / fps, 2) if fps > 0 and frame_count else None
    sample_every = max(1, int(round(fps / settings.video_sample_fps))) if fps > 0 else 15
    sampled_fps = round(fps / sample_every, 2) if fps > 0 else settings.video_sample_fps

    records: list[Violation] = []
    challan_docs: list[dict] = []
    seen_events: set[tuple] = set()
    road_counts: Counter[str] = Counter()
    condition_counts: Counter[str] = Counter()
    quality_scores: list[dict] = []
    first_evidence_path = None
    first_preview = None
    frames_processed = 0
    captured_at = datetime.utcnow()
    tracker: VideoTracker | None = None
    flow_dir = (
        _DIRECTION_VECTORS.get(settings.wrong_side_direction)
        if settings.wrong_side_enforcement else None
    )

    try:
        frame_index = 0
        while len(records) < settings.max_video_violations:
            ok, frame = cap.read()
            if not ok:
                break
            if frame_index % sample_every != 0:
                frame_index += 1
                continue

            processed = edge_preprocessor.process(frame)
            clean_frame = processed["processed_uint8"]
            weather_condition = processed["condition"]
            quality = preprocessor.assess(clean_frame, weather_condition)
            detections = detector.detect(clean_frame)
            road_users = summarize(detections)
            for row in road_users:
                road_counts[row["category"]] += row["count"]
            condition_counts[weather_condition] += 1
            quality_scores.append(asdict(quality))

            if tracker is None:
                tracker = VideoTracker(
                    stop_line=int(clean_frame.shape[0] * settings.stop_line_frac),
                    expected_dir=flow_dir,
                    min_travel=settings.wrong_side_min_travel,
                )

            red_on = _is_red_signal_on(clean_frame, detections)
            # Red-light and (when enabled) wrong-side are tracker-driven over frames,
            # so drop any single-frame versions from the per-frame rule pass.
            exclude = {"RED_LIGHT_VIOLATION"}
            if settings.wrong_side_enforcement:
                exclude.add("WRONG_SIDE_DRIVING")
            frame_violations = [
                v for v in analyze(detections, clean_frame) if v["type"] not in exclude
            ]
            frame_violations.extend(tracker.update(detections, red_on))

            deduped: list[dict] = []
            for v in frame_violations:
                track_id = tracker.best_track_id(v.get("bbox"), v.get("vehicle_type"))
                fallback = v.get("vehicle_id")
                if fallback is None and v.get("bbox"):
                    cx, cy = _bbox_center(v["bbox"])
                    fallback = (round(cx / 80), round(cy / 80), v.get("vehicle_type"))
                key = (v["type"], track_id or fallback)
                if key in seen_events:
                    continue
                seen_events.add(key)
                deduped.append(v)

            if len(records) + len(deduped) > settings.max_video_violations:
                deduped = deduped[: settings.max_video_violations - len(records)]

            if deduped:
                _attach_license_plates(frame, weather_condition, detections, deduped)

            annotated = annotate(clean_frame, detections, deduped)
            frame_time = frame_index / fps if fps > 0 else frames_processed / sampled_fps
            timestamp = captured_at + timedelta(seconds=frame_time)
            annotated = watermark(
                annotated,
                location,
                f"{timestamp:%Y-%m-%d %H:%M:%S} · t={frame_time:.1f}s",
            )
            annotated = label_condition(annotated, weather_condition)

            if first_preview is None:
                first_preview = annotated

            if deduped:
                evidence_path = save_evidence(annotated)
                if first_evidence_path is None:
                    first_evidence_path = evidence_path
                evidence_id = evidence_path.stem
                save_metadata(evidence_id, {
                    "evidence_id": evidence_id,
                    "timestamp": timestamp.isoformat(),
                    "location": location,
                    "source_video": video_path.name,
                    "frame_index": frame_index,
                    "frame_time_seconds": round(frame_time, 2),
                    "annotated_image": evidence_path.name,
                    "weather_condition": weather_condition,
                    "red_signal_detected": red_on,
                    "quality": asdict(quality),
                    "road_users": road_users,
                    "violations": [
                        {
                            k: v.get(k)
                            for k in ("type", "severity", "confidence", "vehicle_type", "license_plate", "description")
                        }
                        for v in deduped
                    ],
                })

                challan_ctx = {
                    "location": location,
                    "weather_condition": weather_condition,
                    "source": "video",
                    "annotated_image": str(evidence_path),
                    "timestamp": timestamp,
                }
                for v in deduped:
                    records.append(Violation(
                        image_path=str(video_path),
                        annotated_image_path=str(evidence_path),
                        violation_type=v["type"],
                        severity=v["severity"],
                        confidence=v["confidence"],
                        vehicle_type=v["vehicle_type"],
                        license_plate=v.get("license_plate"),
                        location=location,
                        timestamp=timestamp,
                    ))
                    challan_docs.append(build_challan(v, annotated, challan_ctx))

            frames_processed += 1
            frame_index += 1
            if frames_processed >= settings.max_video_frames:
                break
    finally:
        cap.release()

    if frames_processed == 0:
        raise HTTPException(status_code=400, detail="No readable frames found in the uploaded video.")

    if first_evidence_path is None and first_preview is not None:
        first_evidence_path = save_evidence(first_preview)
        save_metadata(first_evidence_path.stem, {
            "evidence_id": first_evidence_path.stem,
            "timestamp": captured_at.isoformat(),
            "location": location,
            "source_video": video_path.name,
            "annotated_image": first_evidence_path.name,
            "frames_processed": frames_processed,
            "violations": [],
        })

    if records:
        db.add_all(records)
        db.commit()
        # records and challan_docs are appended in lockstep, so they align by index.
        for doc, rec in zip(challan_docs, records):
            doc["violation_id"] = rec.id
        save_challans(challan_docs)

    dominant_condition = condition_counts.most_common(1)[0][0] if condition_counts else None
    avg_quality = {
        "score": round(sum(q["score"] for q in quality_scores) / len(quality_scores)),
        "sharpness": round(sum(q["sharpness"] for q in quality_scores) / len(quality_scores)),
        "brightness": round(sum(q["brightness"] for q in quality_scores) / len(quality_scores)),
        "contrast": round(sum(q["contrast"] for q in quality_scores) / len(quality_scores)),
        "corrections": [
            f"Video sampled: {frames_processed} frames",
            f"Weather-adaptive: {dominant_condition}",
        ],
    }

    return VideoAnalysisResult(
        quality=avg_quality,
        weather_condition=dominant_condition,
        detections=sum(road_counts.values()),
        road_users=[
            {"category": category, "count": count}
            for category, count in road_counts.most_common()
        ],
        violations=[ViolationOut.model_validate(r) for r in records],
        evidence_url=f"/evidence/{first_evidence_path.name}",
        frames_processed=frames_processed,
        sampled_fps=sampled_fps,
        duration_seconds=duration,
    )


def _process_batch(raws: list[bytes], location: str, db: Session) -> BatchResult:
    results = [process_image(raw, location, db) for raw in raws]
    return BatchResult(
        processed=len(results),
        total_violations=sum(len(r.violations) for r in results),
        results=results,
    )


# The pipelines do heavy, synchronous CPU work (OpenCV decode, YOLO, TrOCR) — a
# video can take minutes. Running that inline in an async endpoint would block the
# event loop and stall every other request, so we read the upload asynchronously
# and hand the blocking work to a worker thread.
@router.post("/upload", response_model=AnalysisResult)
async def analyze_image(
    file: UploadFile = File(...),
    location: str = Form("Unknown"),
    db: Session = Depends(get_db),
):
    """Upload → preprocess → detect → flag violations → store evidence."""
    raw = await file.read()
    return await run_in_threadpool(process_image, raw, location, db)


@router.post("/video-upload", response_model=VideoAnalysisResult)
async def analyze_video(
    file: UploadFile = File(...),
    location: str = Form("Unknown"),
    db: Session = Depends(get_db),
):
    """Upload a video → sample frames → detect violations and red-light crossings."""
    raw = await file.read()
    return await run_in_threadpool(process_video, raw, file.filename, location, db)


@router.post("/batch-upload", response_model=BatchResult)
async def analyze_batch(
    files: list[UploadFile] = File(...),
    location: str = Form("Unknown"),
    db: Session = Depends(get_db),
):
    """Run the pipeline over several images in one request."""
    raws = [await f.read() for f in files]
    return await run_in_threadpool(_process_batch, raws, location, db)

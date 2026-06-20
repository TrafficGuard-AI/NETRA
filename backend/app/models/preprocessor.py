"""Adaptive image preprocessing.

Assess a frame's quality, then apply only the corrections it needs:
CLAHE (low-light), dehaze (contrast stretch), unsharp (motion blur), denoise.
Returns the cleaned image plus a 0-100 quality report for the UI.
"""

from dataclasses import dataclass, field

import cv2
import numpy as np

# Quality thresholds (tuned for roadside camera frames)
SHARP_FULL = 300.0   # Laplacian variance treated as "fully sharp"
BLUR_VAR = 100.0     # below this → motion/defocus blur
LOWLIGHT_MEAN = 90   # mean luminance below this → low-light
HAZE_STD = 35        # low contrast + bright → hazy/washed out
CONTRAST_FULL = 60.0 # luminance std treated as "full contrast"


@dataclass
class QualityReport:
    score: int
    sharpness: int
    brightness: int
    contrast: int
    corrections: list[str] = field(default_factory=list)


def _metrics(image: np.ndarray) -> tuple[float, float, float]:
    """Raw sharpness (Laplacian var), brightness (mean), contrast (std)."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return cv2.Laplacian(gray, cv2.CV_64F).var(), float(gray.mean()), float(gray.std())


def _score(sharp: float, mean: float, std: float) -> tuple[int, int, int, int]:
    """Map raw metrics to 0-100 sub-scores and a weighted overall score."""
    s = min(100, sharp / SHARP_FULL * 100)
    b = max(0.0, 100 - abs(mean - 128) / 1.28)  # peaks at mid-grey
    c = min(100, std / CONTRAST_FULL * 100)
    overall = round(0.5 * s + 0.25 * b + 0.25 * c)
    return overall, round(s), round(b), round(c)


def enhance(image: np.ndarray) -> np.ndarray:
    """CLAHE on the L channel — lifts detail in low-light/flat frames."""
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    return cv2.cvtColor(cv2.merge((clahe.apply(l), a, b)), cv2.COLOR_LAB2BGR)


def dehaze(image: np.ndarray) -> np.ndarray:
    """Per-channel percentile contrast stretch to cut haze/wash-out."""
    out = np.empty_like(image)
    for ch in range(3):
        lo, hi = np.percentile(image[:, :, ch], (1, 99))
        if hi > lo:
            out[:, :, ch] = np.clip((image[:, :, ch] - lo) * 255.0 / (hi - lo), 0, 255)
        else:
            out[:, :, ch] = image[:, :, ch]
    return out.astype(np.uint8)


def deblur(image: np.ndarray) -> np.ndarray:
    """Unsharp mask — recovers edges lost to mild motion blur."""
    blurred = cv2.GaussianBlur(image, (0, 0), 3)
    return cv2.addWeighted(image, 1.5, blurred, -0.5, 0)


def denoise(image: np.ndarray) -> np.ndarray:
    return cv2.fastNlMeansDenoisingColored(image, None, 5, 5, 7, 21)


def normalize(image: np.ndarray, size: int = 640) -> np.ndarray:
    """Aspect-preserving letterbox to size×size (YOLO-style 114 padding).

    Detection uses YOLO's own resizing, so this is exposed for callers that
    need a fixed-shape model input rather than wired into the main path.
    """
    h, w = image.shape[:2]
    scale = size / max(h, w)
    nw, nh = int(round(w * scale)), int(round(h * scale))
    resized = cv2.resize(image, (nw, nh), interpolation=cv2.INTER_AREA)
    canvas = np.full((size, size, 3), 114, np.uint8)
    y, x = (size - nh) // 2, (size - nw) // 2
    canvas[y:y + nh, x:x + nw] = resized
    return canvas


def assess(image: np.ndarray, condition: str | None = None) -> QualityReport:
    """Score a frame's quality (0-100) WITHOUT modifying it.

    Used after the weather-adaptive edge preprocessor has already cleaned and
    resized the frame: we only want a quality report for the UI/metadata, not a
    second round of enhancement. `condition` (FOG/NIGHT/DAY-RAIN), when given,
    is surfaced as the applied correction.
    """
    sharp, mean, std = _metrics(image)
    overall, s, b, c = _score(sharp, mean, std)
    corrections = [f"Weather-adaptive: {condition}"] if condition else []
    return QualityReport(score=overall, sharpness=s, brightness=b, contrast=c, corrections=corrections)


def preprocess(image: np.ndarray) -> tuple[np.ndarray, QualityReport]:
    """Assess the frame, apply needed corrections, return (image, report)."""
    sharp, mean, std = _metrics(image)
    overall, s, b, c = _score(sharp, mean, std)

    out = image
    corrections: list[str] = []

    if mean < LOWLIGHT_MEAN or overall < 55:
        out = denoise(out)
        corrections.append("Denoised")
    if mean < LOWLIGHT_MEAN or c < 55:
        out = enhance(out)
        corrections.append("Low-light enhanced (CLAHE)")
    if std < HAZE_STD and mean > 120:
        out = dehaze(out)
        corrections.append("Dehazed")
    if sharp < BLUR_VAR:
        out = deblur(out)
        corrections.append("Sharpened")

    return out, QualityReport(score=overall, sharpness=s, brightness=b, contrast=c, corrections=corrections)

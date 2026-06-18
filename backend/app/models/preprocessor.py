import cv2
import numpy as np

# Below this Laplacian variance an image is considered blurry.
BLUR_THRESHOLD = 100.0


def quality_score(image: np.ndarray) -> int:
    """0-100 sharpness score from Laplacian variance."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    variance = cv2.Laplacian(gray, cv2.CV_64F).var()
    return int(min(100, variance / BLUR_THRESHOLD * 100))


def enhance(image: np.ndarray) -> np.ndarray:
    """Apply CLAHE on the luminance channel to fix low-light/contrast."""
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l = clahe.apply(l)
    return cv2.cvtColor(cv2.merge((l, a, b)), cv2.COLOR_LAB2BGR)


def preprocess(image: np.ndarray) -> tuple[np.ndarray, int]:
    """Return an enhanced image plus its pre-enhancement quality score."""
    score = quality_score(image)
    enhanced = enhance(image)
    if score < 60:  # denoise only when the image is visibly degraded
        enhanced = cv2.fastNlMeansDenoisingColored(enhanced, None, 5, 5, 7, 21)
    return enhanced, score

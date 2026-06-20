"""
ultimate_edge_preprocessor.py — Final Edge-Preprocessing Pipeline
==================================================================
A weather-adaptive, condition-aware preprocessing pipeline for traffic
enforcement cameras.  The system dynamically detects the environmental
condition (FOG · NIGHT · DAY/RAIN) from image statistics and routes
the frame through the optimal algorithmic chain.

Condition detection:
  • FOG   — low RMS contrast + moderate-to-high mean intensity
            (the hallmark of atmospheric scattering)
  • NIGHT — low mean intensity regardless of contrast
  • DAY / RAIN — everything else (well-lit, adequate contrast)

Processing chains:
  FOG   → fast_dehaze → unsharp_mask
  NIGHT → adaptive_lowlight_enhancement → edge_preserving_denoise → unsharp_mask
  DAY   → edge_preserving_denoise → unsharp_mask

Dependencies : opencv-python, numpy, matplotlib
Author       : Auto-generated for Gridlock project
Date         : 2026-06-20
"""

from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Dict, Tuple, Union

import cv2
import numpy as np
# NOTE: matplotlib is only needed by the CLI visualisation (`_show_comparison`)
# and is imported lazily there. Keeping it out of the module top-level lets the
# headless backend import `DynamicTrafficPreprocessor` without matplotlib
# installed (it is not in backend/requirements.txt).


# ──────────────────────────────────────────────────────────────────────
# Core Preprocessor Class
# ──────────────────────────────────────────────────────────────────────
class DynamicTrafficPreprocessor:
    """
    Production-grade, weather-adaptive image preprocessor.

    Every public method is self-contained and can be individually
    replaced with a deep-learning alternative (e.g., swap
    `fast_dehaze` for a learned dehazing network) without touching the
    rest of the pipeline.

    Parameters
    ----------
    target_size : Tuple[int, int]
        (width, height) of the YOLO input canvas.  Default (640, 640).
    fog_contrast_threshold : float
        RMS contrast below which the scene is considered foggy
        (provided mean intensity is also above `fog_mean_floor`).
        Default 50.
    fog_mean_floor : float
        Minimum mean intensity required for the fog classification.
        Fog scatters light → the frame is *not* dark.  Default 80.
    night_mean_threshold : float
        Mean intensity below which the scene is classified as night /
        low-light.  Default 75.
    clahe_clip : float
        CLAHE clip limit used inside the inverted-image dehaze.
        Default 3.0.
    clahe_grid : Tuple[int, int]
        CLAHE tile-grid size.  Default (8, 8).
    gamma : float
        Gamma exponent for the non-linear low-light curve.  Values
        > 1.0 lift shadows.  Default 2.0.
    bilateral_d : int
        Bilateral filter neighbourhood diameter.  Default 5.
    bilateral_sigma_color : float
        Bilateral colour-space sigma.  Default 40.
    bilateral_sigma_space : float
        Bilateral coordinate-space sigma.  Default 40.
    unsharp_ksize : Tuple[int, int]
        Gaussian kernel for the Unsharp Mask.  Default (3, 3).
    unsharp_sigma : float
        Gaussian sigma for the Unsharp Mask.  Default 1.0.
    unsharp_weight : float
        High-frequency amplification factor.  Default 0.5
        (mild — just enough to crisp licence-plate glyphs).
    """

    def __init__(
        self,
        target_size: Tuple[int, int] = (640, 640),
        fog_contrast_threshold: float = 50.0,
        fog_mean_floor: float = 80.0,
        night_mean_threshold: float = 75.0,
        clahe_clip: float = 3.0,
        clahe_grid: Tuple[int, int] = (8, 8),
        gamma: float = 2.0,
        bilateral_d: int = 5,
        bilateral_sigma_color: float = 40.0,
        bilateral_sigma_space: float = 40.0,
        unsharp_ksize: Tuple[int, int] = (3, 3),
        unsharp_sigma: float = 1.0,
        unsharp_weight: float = 0.5,
    ) -> None:
        self.target_size = target_size
        self.fog_contrast_threshold = fog_contrast_threshold
        self.fog_mean_floor = fog_mean_floor
        self.night_mean_threshold = night_mean_threshold
        self.clahe_clip = clahe_clip
        self.clahe_grid = clahe_grid
        self.gamma = gamma
        self.bilateral_d = bilateral_d
        self.bilateral_sigma_color = bilateral_sigma_color
        self.bilateral_sigma_space = bilateral_sigma_space
        self.unsharp_ksize = unsharp_ksize
        self.unsharp_sigma = unsharp_sigma
        self.unsharp_weight = unsharp_weight

        # Pre-build the gamma look-up table once (used by low-light path).
        self._gamma_lut = self._build_gamma_lut(self.gamma)

    # ──────────────────────────────────────────────────────────────────
    # Internal helpers
    # ──────────────────────────────────────────────────────────────────
    @staticmethod
    def _build_gamma_lut(gamma: float) -> np.ndarray:
        """
        256-entry uint8 LUT: output = 255 × (input / 255) ^ (1/gamma).

        With gamma = 2.0:
          • input  10 → output  50  (dark shadow lifted 5×)
          • input 200 → output 226  (bright pixel barely moves)
          • input 255 → output 255  (headlight stays at max)
        """
        inv_gamma = 1.0 / gamma
        table = np.array(
            [np.clip(((i / 255.0) ** inv_gamma) * 255, 0, 255) for i in range(256)],
            dtype=np.uint8,
        )
        return table

    # ──────────────────────────────────────────────────────────────────
    # Geometry — Letterbox parameters & inverse mapping
    # ──────────────────────────────────────────────────────────────────
    def letterbox_params(
        self, image_shape: Tuple[int, ...], size: Tuple[int, int] = None
    ) -> Tuple[float, int, int]:
        """
        Compute the (scale, pad_left, pad_top) used by `letterbox` for an
        image of shape *image_shape*.

        Exposed so callers can map coordinates between the original frame
        and the letterboxed canvas without re-deriving (and risking
        diverging from) the resize math.  `letterbox` itself uses this,
        guaranteeing the forward resize and the inverse mapping agree.
        """
        if size is None:
            size = self.target_size

        target_w, target_h = size
        h, w = image_shape[:2]

        scale = min(target_w / w, target_h / h)
        new_w = int(w * scale)
        new_h = int(h * scale)

        pad_left = (target_w - new_w) // 2
        pad_top = (target_h - new_h) // 2
        return scale, pad_left, pad_top

    def unletterbox_bbox(
        self,
        bbox: list,
        image_shape: Tuple[int, ...],
        size: Tuple[int, int] = None,
    ) -> list:
        """
        Map a bounding box from letterboxed space (e.g. 640×640) back to
        the original image's pixel coordinates, clamped to image bounds.

        Inverse of the letterbox transform:
            orig = (coord − pad) / scale

        Parameters
        ----------
        bbox        : [x1, y1, x2, y2] in letterboxed-canvas pixels.
        image_shape : shape of the ORIGINAL image, (h, w, ...).
        size        : letterbox canvas size.  Defaults to self.target_size.

        Returns
        -------
        list[int] — [x1, y1, x2, y2] in original-image pixels.
        """
        scale, pad_left, pad_top = self.letterbox_params(image_shape, size)
        h, w = image_shape[:2]
        x1, y1, x2, y2 = bbox

        ox1 = (x1 - pad_left) / scale
        oy1 = (y1 - pad_top) / scale
        ox2 = (x2 - pad_left) / scale
        oy2 = (y2 - pad_top) / scale

        return [
            int(round(max(0, min(w, ox1)))),
            int(round(max(0, min(h, oy1)))),
            int(round(max(0, min(w, ox2)))),
            int(round(max(0, min(h, oy2)))),
        ]

    # ──────────────────────────────────────────────────────────────────
    # Stage 1 — Letterbox Resize
    # ──────────────────────────────────────────────────────────────────
    def letterbox(
        self, image: np.ndarray, size: Tuple[int, int] = None
    ) -> np.ndarray:
        """
        Resize *image* to fit inside *size* while preserving the aspect
        ratio, padding the remainder with black bars.

        This is always the FIRST step so every downstream filter
        operates on the compact 640×640 canvas, not the raw megapixel
        frame.

        Parameters
        ----------
        image : np.ndarray  — BGR uint8, any resolution.
        size  : (w, h)      — target canvas.  Defaults to self.target_size.

        Returns
        -------
        np.ndarray — BGR uint8, exactly (size[1], size[0], 3).
        """
        if size is None:
            size = self.target_size

        target_w, target_h = size
        h, w = image.shape[:2]

        # Shared geometry: identical to what unletterbox_bbox inverts.
        scale, pad_left, pad_top = self.letterbox_params(image.shape, size)
        new_w = int(w * scale)
        new_h = int(h * scale)

        # Choose interpolation: INTER_AREA for shrinking (antialiased),
        # INTER_LINEAR for enlarging.
        interp = cv2.INTER_AREA if scale < 1.0 else cv2.INTER_LINEAR
        resized = cv2.resize(image, (new_w, new_h), interpolation=interp)

        # Centre on a black canvas.
        pad_bottom = target_h - new_h - pad_top
        pad_right = target_w - new_w - pad_left

        letterboxed = cv2.copyMakeBorder(
            resized,
            top=pad_top,
            bottom=pad_bottom,
            left=pad_left,
            right=pad_right,
            borderType=cv2.BORDER_CONSTANT,
            value=(0, 0, 0),
        )
        return letterboxed

    # ──────────────────────────────────────────────────────────────────
    # Stage 2a — FOG: Inverted-Image Dehazing
    # ──────────────────────────────────────────────────────────────────
    def fast_dehaze(self, image: np.ndarray) -> np.ndarray:
        """
        Remove atmospheric haze / fog using the **inverted-image**
        trick, which avoids the computationally expensive Dark Channel
        Prior.

        Algorithm
        ---------
        1.  Invert the image:  I' = 255 − I
            • Fog is additive white light → inversion turns it into
              dark regions, which is exactly what CLAHE excels at
              enhancing.
        2.  Convert I' to LAB and apply CLAHE to the L-channel.
            • This stretches the contrast of the (now-dark) fog regions
              while leaving saturated areas (vehicles, signs) intact.
        3.  Convert back to BGR and invert again:  result = 255 − I''
            • The double inversion cancels out, but the CLAHE
              enhancement survives — effectively subtracting the
              atmospheric scattering.

        Parameters
        ----------
        image : np.ndarray — BGR uint8, 640×640.

        Returns
        -------
        np.ndarray — Dehazed BGR uint8, 640×640.
        """
        # Step 1 — Invert the image.
        # np.clip is not needed here because 255 - uint8 is always [0, 255].
        inverted = cv2.bitwise_not(image)

        # Step 2 — CLAHE on the L-channel of the inverted image.
        lab = cv2.cvtColor(inverted, cv2.COLOR_BGR2LAB)
        l_ch, a_ch, b_ch = cv2.split(lab)

        clahe = cv2.createCLAHE(
            clipLimit=self.clahe_clip,
            tileGridSize=self.clahe_grid,
        )
        l_enhanced = clahe.apply(l_ch)

        lab_enhanced = cv2.merge([l_enhanced, a_ch, b_ch])
        enhanced_bgr = cv2.cvtColor(lab_enhanced, cv2.COLOR_LAB2BGR)

        # Step 3 — Invert back to recover the original colour polarity.
        dehazed = cv2.bitwise_not(enhanced_bgr)

        return dehazed

    # ──────────────────────────────────────────────────────────────────
    # Stage 2b — NIGHT: Adaptive Low-Light Enhancement
    # ──────────────────────────────────────────────────────────────────
    def adaptive_lowlight_enhancement(self, image: np.ndarray) -> np.ndarray:
        """
        Lift dark shadows using gamma correction while leaving bright
        pixels (headlights, streetlamps, reflective signs) untouched.

        How it works
        ------------
        1.  Convert to grayscale to compute a per-pixel brightness map.
        2.  Build a **dark-pixel weight mask**:
                weight = 1.0 − (gray / 255)
            Dark pixels get weight ≈ 1.0 (full gamma lift).
            Bright pixels get weight ≈ 0.0 (no change).
        3.  Apply the gamma LUT to the entire image to get a brightened
            version.
        4.  Blend:  output = weight × gamma_image + (1 − weight) × original
            This applies the correction *only where it is needed*.

        The result: road surfaces and vehicles in shadow are clearly
        visible, while headlights remain at their original intensity
        with zero blooming.

        Parameters
        ----------
        image : np.ndarray — BGR uint8, 640×640.

        Returns
        -------
        np.ndarray — Low-light enhanced BGR uint8, 640×640.
        """
        # Compute per-pixel brightness (single-channel, fast).
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Weight mask: dark pixels → 1.0, bright pixels → 0.0.
        # Shape: (H, W, 1) so it broadcasts over 3 BGR channels.
        weight = (1.0 - gray.astype(np.float32) / 255.0)[:, :, np.newaxis]

        # Apply gamma LUT uniformly (the mask will limit where it takes
        # effect).  cv2.LUT is a single vectorised C++ pass — ~0.05 ms.
        gamma_image = cv2.LUT(image, self._gamma_lut)

        # Blend: selective correction weighted by darkness.
        blended = (
            weight * gamma_image.astype(np.float32)
            + (1.0 - weight) * image.astype(np.float32)
        )

        # Clip to [0, 255] to guarantee mathematical safety, then cast.
        result = np.clip(blended, 0, 255).astype(np.uint8)

        return result

    # ──────────────────────────────────────────────────────────────────
    # Stage 3 — RAIN / NOISE: Edge-Preserving Denoise
    # ──────────────────────────────────────────────────────────────────
    def edge_preserving_denoise(self, image: np.ndarray) -> np.ndarray:
        """
        Suppress sensor noise and thin rain streaks using a carefully
        tuned bilateral filter.

        Why bilateral?
        --------------
        The bilateral filter applies a Gaussian in *both* the spatial
        domain and the colour-intensity domain simultaneously.  This
        means:
          • Smooth, homogeneous regions (sky, wet road, noise) are
            blurred effectively → noise / streaks vanish.
          • Strong edges (vehicle contours, licence-plate glyphs) see
            a large colour-intensity difference across the boundary →
            the filter refuses to blur across them.

        The parameters (d=5, σ_color=40, σ_space=40) are deliberately
        conservative — enough to clean rain but not enough to melt
        fine detail.

        Parameters
        ----------
        image : np.ndarray — BGR uint8.

        Returns
        -------
        np.ndarray — Denoised BGR uint8.
        """
        denoised = cv2.bilateralFilter(
            image,
            d=self.bilateral_d,
            sigmaColor=self.bilateral_sigma_color,
            sigmaSpace=self.bilateral_sigma_space,
        )
        return denoised

    # ──────────────────────────────────────────────────────────────────
    # Stage 4 — Final Sharpening: Unsharp Mask
    # ──────────────────────────────────────────────────────────────────
    def unsharp_mask(self, image: np.ndarray) -> np.ndarray:
        """
        Apply a mild Unsharp Mask to crisp up licence-plate text,
        vehicle contours, and lane markings.

        Formula:  sharpened = image + weight × (image − blur)

        A weight of 0.5 with a small 3×3 kernel gives just enough
        edge pop without reintroducing noise or producing ringing
        artefacts.

        Parameters
        ----------
        image : np.ndarray — BGR uint8.

        Returns
        -------
        np.ndarray — Sharpened BGR uint8.
        """
        blurred = cv2.GaussianBlur(
            image,
            ksize=self.unsharp_ksize,
            sigmaX=self.unsharp_sigma,
        )

        # Compute in float64 to avoid uint8 underflow in the subtraction.
        sharp = (
            image.astype(np.float64)
            + self.unsharp_weight
            * (image.astype(np.float64) - blurred.astype(np.float64))
        )

        # Absolute safety: clip to valid range before casting.
        return np.clip(sharp, 0, 255).astype(np.uint8)

    # ──────────────────────────────────────────────────────────────────
    # Condition-specific enhancement chain (size-agnostic)
    # ──────────────────────────────────────────────────────────────────
    def _apply_chain(self, frame: np.ndarray, condition: str) -> np.ndarray:
        """
        Run the enhancement chain for *condition* on a frame of ANY size.

        Shared by `process` (on the 640×640 canvas) and
        `enhance_full_resolution` (on the native-resolution frame), so the
        two can never drift apart.

          FOG       → dehaze   → sharpen
          NIGHT     → lowlight → denoise → sharpen
          DAY/RAIN  → denoise  → sharpen   (the default / fallback)
        """
        if condition == "FOG":
            frame = self.fast_dehaze(frame)
            frame = self.unsharp_mask(frame)
        elif condition == "NIGHT":
            frame = self.adaptive_lowlight_enhancement(frame)
            frame = self.edge_preserving_denoise(frame)
            frame = self.unsharp_mask(frame)
        else:  # DAY/RAIN and any unexpected label
            frame = self.edge_preserving_denoise(frame)
            frame = self.unsharp_mask(frame)
        return frame

    def enhance_full_resolution(
        self, image: np.ndarray, condition: str
    ) -> np.ndarray:
        """
        Apply the SAME condition chain at the image's native resolution,
        WITHOUT letterboxing/downsizing.

        Detection runs on the compact 640×640 canvas for speed, but ANPR
        needs every pixel of plate detail — downscaling to 640×640 first
        would make small plates unreadable.  This produces a full-res,
        weather-corrected frame to crop plates from, using the condition
        already detected by `process`.

        Parameters
        ----------
        image     : np.ndarray — raw BGR uint8, any resolution.
        condition : str        — "FOG" / "NIGHT" / "DAY/RAIN" from process().

        Returns
        -------
        np.ndarray — weather-corrected BGR uint8 at the ORIGINAL resolution.
        """
        return self._apply_chain(image.copy(), condition)

    # ──────────────────────────────────────────────────────────────────
    # Orchestrator — Dynamic Condition Routing
    # ──────────────────────────────────────────────────────────────────
    def process(self, image: np.ndarray) -> Dict[str, Union[np.ndarray, str]]:
        """
        Analyse the image and dynamically route it through the optimal
        processing chain based on detected weather / lighting.

        Detection metrics (computed on the 640×640 letterboxed frame):
          • **mean_intensity** — average grayscale pixel value.
          • **rms_contrast**   — standard deviation of grayscale pixels.
            (Technically σ, not RMS, but it serves the same purpose:
            low σ in a bright image is the signature of fog.)

        Routing:
          FOG   (low contrast, bright) → dehaze   → sharpen
          NIGHT (dark)                 → lowlight  → denoise → sharpen
          DAY   (everything else)      → denoise   → sharpen

        Parameters
        ----------
        image : np.ndarray — Raw BGR uint8, any resolution.

        Returns
        -------
        dict with keys:
            "processed_uint8"   — final 640×640 BGR uint8.
            "processed_float32" — final 640×640 BGR float32 [0, 1].
            "condition"         — one of "FOG", "NIGHT", "DAY/RAIN".
        """
        # ── Step 0: Letterbox ────────────────────────────────────────
        frame = self.letterbox(image)

        # ── Step 1: Analyse scene statistics ─────────────────────────
        # IMPORTANT: Compute stats ONLY on the content region, excluding
        # the black letterbox padding bars.  The padding pixels (value 0)
        # would drag mean_intensity down and inflate rms_contrast,
        # causing misclassification (e.g. a foggy scene wrongly detected
        # as night because the padded mean drops below the threshold).
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        content_mask = gray > 5  # pixels above 5 are real content
        if np.any(content_mask):
            content_pixels = gray[content_mask]
            mean_intensity = float(np.mean(content_pixels))
            rms_contrast = float(np.std(content_pixels))
        else:
            # Extremely dark frame — fall back to full-image stats.
            mean_intensity = float(np.mean(gray))
            rms_contrast = float(np.std(gray))

        # ── Step 2: Route through the correct chain ──────────────────
        # Decision tree:
        #   1. Low contrast + moderate mean → FOG (atmospheric scattering
        #      washes out contrast but keeps brightness above black).
        #   2. Low mean + high contrast → NIGHT (dark scene with bright
        #      point sources like headlights producing high σ).
        #   3. Everything else → DAY/RAIN (well-lit, or dark-but-uniform
        #      rain which benefits from bilateral denoise, not gamma).
        if rms_contrast < self.fog_contrast_threshold and mean_intensity > self.fog_mean_floor:
            # FOG: atmospheric scattering washes out contrast but keeps
            # brightness above black.
            condition = "FOG"
        elif mean_intensity < self.night_mean_threshold and rms_contrast >= self.fog_contrast_threshold:
            # NIGHT: dark scene with bright point sources (headlights,
            # streetlamps) producing high σ → needs the selective gamma
            # lift that protects bright pixels.
            condition = "NIGHT"
        else:
            # DAY/RAIN: well-lit daytime, or dark-but-uniform rain which
            # benefits from bilateral denoise + sharpen rather than gamma.
            condition = "DAY/RAIN"

        # Apply the matching enhancement chain (shared with the full-res
        # ANPR path via _apply_chain, so both stay in lock-step).
        frame = self._apply_chain(frame, condition)

        # ── Step 3: Normalise ────────────────────────────────────────
        processed_uint8 = frame
        processed_float32 = frame.astype(np.float32) / 255.0

        return {
            "processed_uint8": processed_uint8,
            "processed_float32": processed_float32,
            "condition": condition,
        }


# ──────────────────────────────────────────────────────────────────────
# Visualisation Helper
# ──────────────────────────────────────────────────────────────────────
def _show_comparison(
    original_bgr: np.ndarray,
    processed_bgr: np.ndarray,
    condition: str,
    elapsed_ms: float,
) -> None:
    """
    Render a polished side-by-side comparison with condition and timing
    in the figure title.
    """
    import matplotlib.pyplot as plt  # lazy: only the CLI demo needs it

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    axes[0].imshow(cv2.cvtColor(original_bgr, cv2.COLOR_BGR2RGB))
    axes[0].set_title("Original", fontsize=14, fontweight="bold")
    axes[0].axis("off")

    axes[1].imshow(cv2.cvtColor(processed_bgr, cv2.COLOR_BGR2RGB))
    axes[1].set_title("Processed (640×640)", fontsize=14, fontweight="bold")
    axes[1].axis("off")

    fig.suptitle(
        f"Detected: {condition}  ·  {elapsed_ms:.1f} ms",
        fontsize=16,
        fontweight="bold",
        color="#1a73e8",
        y=0.98,
    )
    plt.tight_layout(rect=[0, 0, 1, 0.93])
    plt.show()


# ──────────────────────────────────────────────────────────────────────
# Entry Point
# ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # ---- Resolve image path ------------------------------------------------
    if len(sys.argv) > 1:
        image_path = Path(sys.argv[1])
    else:
        image_path = Path("sample_traffic.jpg")

    # ---- Graceful error handling -------------------------------------------
    if not image_path.exists():
        print(
            f"[ERROR] Image not found: {image_path.resolve()}\n"
            f"Usage:  python ultimate_edge_preprocessor.py <path_to_image>"
        )
        sys.exit(1)

    raw_image = cv2.imread(str(image_path))
    if raw_image is None:
        print(
            f"[ERROR] OpenCV could not decode: {image_path.resolve()}\n"
            "Make sure the file is a valid image (JPEG, PNG, BMP, etc.)."
        )
        sys.exit(1)

    h, w = raw_image.shape[:2]
    print(f"[INFO] Loaded image    : {image_path.resolve()}")
    print(f"[INFO] Original size   : {w}×{h} ({raw_image.shape[2]} ch)")

    # ---- Run pipeline ------------------------------------------------------
    preprocessor = DynamicTrafficPreprocessor()

    t_start = time.perf_counter()
    result = preprocessor.process(raw_image)
    t_end = time.perf_counter()

    elapsed_ms = (t_end - t_start) * 1000.0

    processed_uint8 = result["processed_uint8"]
    processed_float32 = result["processed_float32"]
    condition = result["condition"]

    print(f"[INFO] Detected        : {condition}")
    print(f"[INFO] Processed size  : {processed_uint8.shape[1]}×{processed_uint8.shape[0]}")
    print(f"[INFO] float32 range   : [{processed_float32.min():.4f}, {processed_float32.max():.4f}]")
    print(f"[INFO] Pipeline time   : {elapsed_ms:.2f} ms")

    # ---- Diagnostic: print the scene statistics for tuning ----------------
    gray_diag = cv2.cvtColor(preprocessor.letterbox(raw_image), cv2.COLOR_BGR2GRAY)
    mask = gray_diag > 5
    if np.any(mask):
        print(f"[DIAG] mean_intensity  : {float(np.mean(gray_diag[mask])):.2f}")
        print(f"[DIAG] rms_contrast    : {float(np.std(gray_diag[mask])):.2f}")

    # ---- Visualise ---------------------------------------------------------
    _show_comparison(raw_image, processed_uint8, condition, elapsed_ms)

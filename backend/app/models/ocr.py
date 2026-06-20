import re

import numpy as np
from PIL import Image

from app.config import settings

# Indian plate format, e.g. "MH 12 AB 1234"
PLATE_PATTERN = re.compile(r"^[A-Z]{2}\d{1,2}[A-Z]{1,3}\d{4}$")
_NON_ALNUM = re.compile(r"[^A-Z0-9]")


def is_valid(plate: str) -> bool:
    return bool(PLATE_PATTERN.match(plate))


class PlateReader:
    """TrOCR wrapper for license-plate text recognition (lazy-loaded).

    TrOCR is recognition-only — it expects a single, tightly cropped plate
    image and returns the full string. Detection is handled upstream by YOLO.
    """

    def __init__(self):
        self._processor = None
        self._model = None

    def _load(self):
        if self._model is None:
            import torch
            from transformers import TrOCRProcessor, VisionEncoderDecoderModel

            self._processor = TrOCRProcessor.from_pretrained(settings.trocr_model)
            self._model = VisionEncoderDecoderModel.from_pretrained(settings.trocr_model)
            self._model.eval()
            self._torch = torch
        return self._processor, self._model

    def read(self, plate_image: np.ndarray) -> str | None:
        processor, model = self._load()

        # TrOCR wants an RGB PIL image; crops arrive grayscale (CLAHE) or BGR.
        if plate_image.ndim == 2:
            pil = Image.fromarray(plate_image).convert("RGB")
        else:
            pil = Image.fromarray(plate_image[..., ::-1]).convert("RGB")  # BGR→RGB

        pixel_values = processor(images=pil, return_tensors="pt").pixel_values
        with self._torch.no_grad():
            generated = model.generate(pixel_values, max_new_tokens=16)
        raw = processor.batch_decode(generated, skip_special_tokens=True)[0]

        text = _NON_ALNUM.sub("", raw.upper())
        if text.startswith("IND"):  # the embossed "IND" tag, not part of the number
            text = text[3:]
        return text if len(text) >= 4 else None


plate_reader = PlateReader()

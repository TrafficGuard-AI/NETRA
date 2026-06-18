import re

import numpy as np

from app.config import settings

# Indian plate format, e.g. "MH 12 AB 1234"
PLATE_PATTERN = re.compile(r"^[A-Z]{2}\s?\d{1,2}\s?[A-Z]{1,3}\s?\d{4}$")
# Common OCR confusions to normalise before validating.
CORRECTIONS = str.maketrans({"O": "0", "I": "1", "S": "5", "B": "8"})


class PlateReader:
    """EasyOCR wrapper for license-plate text extraction (lazy-loaded)."""

    def __init__(self):
        self._reader = None

    @property
    def reader(self):
        if self._reader is None:
            import easyocr

            self._reader = easyocr.Reader(settings.ocr_languages, gpu=False)
        return self._reader

    def read(self, plate_image: np.ndarray) -> str | None:
        results = self.reader.readtext(plate_image, detail=0)
        if not results:
            return None
        text = "".join(results).upper().replace(" ", "")
        if PLATE_PATTERN.match(text):
            return text
        corrected = text.translate(CORRECTIONS)
        return corrected if PLATE_PATTERN.match(corrected) else text


plate_reader = PlateReader()

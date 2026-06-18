SEVERITY = {
    "TRIPLE_RIDING": "HIGH",
    "HELMET_NON_COMPLIANCE": "HIGH",
    "OVERLOADING": "MEDIUM",
}


def _iou(a: list[int], b: list[int]) -> float:
    """Intersection-over-union of two [x1, y1, x2, y2] boxes."""
    ix1, iy1 = max(a[0], b[0]), max(a[1], b[1])
    ix2, iy2 = min(a[2], b[2]), min(a[3], b[3])
    inter = max(0, ix2 - ix1) * max(0, iy2 - iy1)
    if inter == 0:
        return 0.0
    area_a = (a[2] - a[0]) * (a[3] - a[1])
    area_b = (b[2] - b[0]) * (b[3] - b[1])
    return inter / (area_a + area_b - inter)


def analyze(detections: list[dict]) -> list[dict]:
    """Rule-based violation analysis over raw detections.

    Phase 1 ships triple-riding only; helmet/seatbelt models land in Phase 4.
    """
    vehicles = [d for d in detections if d["class"] == "vehicle"]
    persons = [d for d in detections if d["class"] == "person"]

    violations = []
    for v in vehicles:
        if v["category"] != "Two-Wheeler":
            continue
        riders = [p for p in persons if _iou(p["bbox"], v["bbox"]) > 0.1]
        if len(riders) >= 3:
            violations.append({
                "type": "TRIPLE_RIDING",
                "severity": SEVERITY["TRIPLE_RIDING"],
                "confidence": v["confidence"],
                "vehicle_id": v["id"],
                "vehicle_type": v["category"],
                "bbox": v["bbox"],
                "description": f"{len(riders)} riders detected on a two-wheeler",
            })
    return violations

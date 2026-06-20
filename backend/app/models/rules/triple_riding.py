from .base import Scene, violation

CODE = "TRIPLE_RIDING"
NAME = "Triple riding"
SEVERITY = "HIGH"


def status() -> str:
    return "active"


def check(scene: Scene) -> list[dict]:
    out = []
    for v in scene.vehicles:
        if v["category"] == "Two-Wheeler" and v["occupants"] >= 3:
            out.append(violation(CODE, SEVERITY, v, f"{v['occupants']} riders on a two-wheeler"))
    return out

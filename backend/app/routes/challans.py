"""Browse and issue challans from the MongoDB evidence store.

The store is organised by the two top-level "folders" — two_wheeler /
four_wheeler — each with a sub-folder per violation type.
"""

from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException

from app.config import settings
from app.database.mongo import challans

router = APIRouter()


def _serialize(doc: dict) -> dict:
    doc = dict(doc)
    doc["_id"] = str(doc["_id"])
    path = doc.get("evidence_path")
    if path:
        try:
            rel = Path(path).relative_to(settings.challan_dir)
            doc["evidence_url"] = "/challans/" + str(rel).replace("\\", "/")
        except ValueError:
            doc["evidence_url"] = None
    return doc


@router.get("/challans")
def challan_tree():
    """The folder tree: counts per vehicle class → violation type."""
    col = challans()
    if col is None:
        return {"available": False, "tree": {}, "total": 0}
    tree: dict[str, dict[str, int]] = {}
    pipeline = [{"$group": {"_id": {"c": "$vehicle_class", "t": "$violation_type"}, "n": {"$sum": 1}}}]
    for row in col.aggregate(pipeline):
        tree.setdefault(row["_id"]["c"], {})[row["_id"]["t"]] = row["n"]
    return {"available": True, "tree": tree, "total": col.estimated_document_count()}


@router.get("/challans/list")
def challan_list(
    vehicle_class: str | None = None,
    violation_type: str | None = None,
    status: str | None = None,
    limit: int = 100,
):
    """Challan documents, newest first, filtered by folder / sub-folder / status."""
    col = challans()
    if col is None:
        return []
    query = {}
    if vehicle_class:
        query["vehicle_class"] = vehicle_class
    if violation_type:
        query["violation_type"] = violation_type
    if status:
        query["status"] = status
    cursor = col.find(query).sort("created_at", -1).limit(limit)
    return [_serialize(d) for d in cursor]


@router.patch("/challans/{challan_id}/issue")
def issue_challan(challan_id: str):
    """Mark a challan as issued."""
    col = challans()
    if col is None:
        raise HTTPException(status_code=503, detail="Challan store (MongoDB) is unavailable.")
    from bson import ObjectId
    from bson.errors import InvalidId

    try:
        oid = ObjectId(challan_id)
    except InvalidId:
        raise HTTPException(status_code=422, detail="Invalid challan id.")
    result = col.find_one_and_update(
        {"_id": oid},
        {"$set": {"status": "issued", "issued_at": datetime.utcnow()}},
        return_document=True,
    )
    if result is None:
        raise HTTPException(status_code=404, detail="Challan not found.")
    return _serialize(result)

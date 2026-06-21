"""MongoDB connection for the challan-evidence store.

Best-effort: if Mongo is unreachable, helpers return None and callers no-op, so
the detection pipeline keeps working even without a database.
"""

from app.config import settings

_client = None
_unavailable = False


def get_client():
    global _client, _unavailable
    if _unavailable:
        return None
    if _client is None:
        try:
            from pymongo import MongoClient

            client = MongoClient(settings.mongodb_uri, serverSelectionTimeoutMS=5000)
            client.admin.command("ping")  # fail fast if the server isn't there
            _client = client
        except Exception as exc:  # noqa: BLE001 — any connection issue → disable
            print(f"[mongo] challan store unavailable: {exc}")
            _unavailable = True
            return None
    return _client


def challans():
    """The challan collection, or None when Mongo is unavailable."""
    client = get_client()
    if client is None:
        return None
    return client[settings.mongodb_db][settings.mongodb_collection]

"""
Mantis UI — a small, read-only dashboard over the Mantis MongoDB.

Design goals:
- Read-only. Every Mongo operation here is a find/aggregate; the service is
  meant to run as a user with only the `read` role on the mantis database.
- No credentials in code. The connection string comes from MANTIS_UI_MONGO_URI
  (falls back to MANTIS_MONGO_URI), exactly like the scanner.
- Self-contained. Serves a single static page; no external CDNs.
"""
import os
import logging

from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from motor.motor_asyncio import AsyncIOMotorClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mantis-ui")

MONGO_URI = os.environ.get("MANTIS_UI_MONGO_URI") or os.environ.get("MANTIS_MONGO_URI")
if not MONGO_URI:
    raise RuntimeError("Set MANTIS_UI_MONGO_URI (or MANTIS_MONGO_URI) to the Mantis MongoDB")

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")

# A hard cap so a huge collection can never be pulled into the browser in one go.
MAX_PAGE = 500

client = AsyncIOMotorClient(MONGO_URI, serverSelectionTimeoutMS=5000)
db = client.mantis
assets = db.get_collection("assets_collection")
findings = db.get_collection("findings_collection")

app = FastAPI(title="Mantis UI", docs_url=None, redoc_url=None)


def _clean(doc: dict) -> dict:
    """Drop Mongo's _id (an ObjectId or raw string) so responses are JSON-safe."""
    doc.pop("_id", None)
    return doc


@app.get("/api/health")
async def health():
    try:
        await db.command("ping")
        return {"ok": True}
    except Exception as exc:  # surfaced to the page as a red banner
        return JSONResponse(status_code=503, content={"ok": False, "error": str(exc)})


@app.get("/api/orgs")
async def orgs():
    """Distinct org names, so the page can offer an org filter."""
    values = await assets.distinct("org")
    return sorted(v for v in values if v)


@app.get("/api/stats")
async def stats(org: str | None = Query(default=None)):
    match: dict = {}
    if org:
        match["org"] = org

    asset_match = {"$match": match} if match else {"$match": {}}

    by_type = await assets.aggregate([
        asset_match,
        {"$group": {"_id": "$asset_type", "count": {"$sum": 1}}},
    ]).to_list(length=None)

    # A host is "live" if httpx recorded at least one active host for it.
    live = await assets.count_documents({**match, "active_hosts.0": {"$exists": True}})
    total_assets = await assets.count_documents(match)

    by_severity = await findings.aggregate([
        asset_match,
        {"$match": {"status": {"$ne": "Fixed"}}},
        {"$group": {"_id": "$severity", "count": {"$sum": 1}}},
    ]).to_list(length=None)

    by_status = await findings.aggregate([
        asset_match,
        {"$group": {"_id": "$status", "count": {"$sum": 1}}},
    ]).to_list(length=None)

    by_ftype = await findings.aggregate([
        asset_match,
        {"$match": {"status": {"$ne": "Fixed"}}},
        {"$group": {"_id": "$type", "count": {"$sum": 1}}},
    ]).to_list(length=None)

    def as_map(rows):
        return {(r["_id"] or "unknown"): r["count"] for r in rows}

    return {
        "total_assets": total_assets,
        "live_hosts": live,
        "assets_by_type": as_map(by_type),
        "open_findings": sum(r["count"] for r in by_status if r["_id"] != "Fixed"),
        "findings_by_severity": as_map(by_severity),
        "findings_by_status": as_map(by_status),
        "findings_by_type": as_map(by_ftype),
    }


@app.get("/api/assets")
async def list_assets(
    org: str | None = Query(default=None),
    asset_type: str | None = Query(default=None),
    q: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=MAX_PAGE),
    skip: int = Query(default=0, ge=0),
):
    query: dict = {}
    if org:
        query["org"] = org
    if asset_type:
        query["asset_type"] = asset_type
    if q:
        # Anchored, escaped substring match on the asset name — not a raw regex
        # from the user, so it can't inject operators.
        import re
        query["asset"] = {"$regex": re.escape(q), "$options": "i"}

    total = await assets.count_documents(query)
    cursor = assets.find(query).sort("asset", 1).skip(skip).limit(limit)
    rows = [_clean(d) async for d in cursor]
    return {"total": total, "skip": skip, "limit": limit, "rows": rows}


@app.get("/api/findings")
async def list_findings(
    org: str | None = Query(default=None),
    severity: str | None = Query(default=None),
    status: str | None = Query(default=None),
    type: str | None = Query(default=None),
    q: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=MAX_PAGE),
    skip: int = Query(default=0, ge=0),
):
    query: dict = {}
    if org:
        query["org"] = org
    if severity:
        query["severity"] = severity
    if status:
        query["status"] = status
    if type:
        query["type"] = type
    if q:
        import re
        rx = {"$regex": re.escape(q), "$options": "i"}
        query["$or"] = [{"title": rx}, {"host": rx}]

    total = await findings.count_documents(query)
    cursor = findings.find(query).sort("created_timestamp", -1).skip(skip).limit(limit)
    rows = [_clean(d) async for d in cursor]
    return {"total": total, "skip": skip, "limit": limit, "rows": rows}


# Mounted last so the API routes above take precedence.
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")

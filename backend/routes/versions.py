from fastapi import APIRouter, HTTPException, Request
from datetime import datetime, timezone

from database import db
from auth_utils import get_current_user
from models import WorldVersion

router = APIRouter()


@router.post("/worlds/{world_id}/versions")
async def create_world_version(world_id: str, request: Request):
    user = await get_current_user(request)
    world = await db.worlds.find_one({"id": world_id}, {"_id": 0})
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    version_count = await db.world_versions.count_documents({"world_id": world_id})
    version = WorldVersion(
        world_id=world_id, version_number=version_count + 1,
        name=f"Version {version_count + 1}", snapshot=world,
        created_by=user["id"] if user else None
    )
    doc = version.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.world_versions.insert_one(doc)
    old_versions = await db.world_versions.find({"world_id": world_id}).sort([("version_number", 1)]).to_list(100)
    if len(old_versions) > 20:
        for v in old_versions[:-20]:
            await db.world_versions.delete_one({"id": v["id"]})
    return {"message": "Version created", "version": version_count + 1}


@router.get("/worlds/{world_id}/versions")
async def list_world_versions(world_id: str):
    versions = await db.world_versions.find(
        {"world_id": world_id}, {"_id": 0, "snapshot": 0}
    ).sort([("version_number", -1)]).to_list(20)
    return {"versions": versions}


@router.get("/worlds/{world_id}/versions/{version_id}")
async def get_world_version(world_id: str, version_id: str):
    version = await db.world_versions.find_one({"id": version_id, "world_id": world_id}, {"_id": 0})
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
    return version


@router.post("/worlds/{world_id}/versions/{version_id}/restore")
async def restore_world_version(world_id: str, version_id: str, request: Request):
    user = await get_current_user(request)
    version = await db.world_versions.find_one({"id": version_id, "world_id": world_id}, {"_id": 0})
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
    snapshot = version.get("snapshot", {})
    update_data = {
        "zones": snapshot.get("zones", []),
        "prefabs": snapshot.get("prefabs", []),
        "terrain": snapshot.get("terrain", {}),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    await db.worlds.update_one({"id": world_id}, {"$set": update_data})
    return {"message": "World restored to version", "version": version.get("version_number")}

from fastapi import APIRouter, HTTPException, Request
from typing import Optional
from datetime import datetime, timezone

from database import db
from auth_utils import get_current_user, require_auth
from models import GalleryWorld, GalleryPublish

router = APIRouter()


async def track_analytics(event_type: str, world_id: str = None, data: dict = None):
    event = {"event_type": event_type, "world_id": world_id, "data": data or {}, "timestamp": datetime.now(timezone.utc).isoformat()}
    await db.analytics.insert_one(event)


@router.post("/gallery/publish")
async def publish_to_gallery(request_data: GalleryPublish, request: Request):
    world = await db.worlds.find_one({"id": request_data.world_id}, {"_id": 0})
    if not world:
        raise HTTPException(status_code=404, detail="World not found")

    # Permission: only owner or unowned worlds can be published
    user = await get_current_user(request)
    if world.get("owner_id") and user:
        if world["owner_id"] != user["id"] and user.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Only the world owner can publish")

    existing = await db.gallery.find_one({"world_id": request_data.world_id})
    if existing:
        raise HTTPException(status_code=400, detail="World already published")

    gallery_entry = GalleryWorld(
        world_id=request_data.world_id, name=world.get("name", "Unnamed World"),
        description=request_data.description,
        creator_name=request_data.creator_name,
        creator_id=user["id"] if user else None,
        tags=request_data.tags,
        zone_count=len(world.get("zones", [])),
        prefab_count=len(world.get("prefabs", [])),
        map_size=f"{world.get('map_width', 64)}x{world.get('map_height', 64)}",
        template_used=world.get("template")
    )

    doc = gallery_entry.model_dump()
    doc['published_at'] = doc['published_at'].isoformat()
    await db.gallery.insert_one(doc)
    await track_analytics("gallery_publish", request_data.world_id, {"tags": request_data.tags})

    # Notify followers
    if user:
        followers = await db.follows.find({"following_id": user["id"]}).to_list(500)
        for f in followers:
            await db.notifications.insert_one({
                "user_id": f["follower_id"], "type": "new_publication",
                "data": {"publisher_name": user.get("name", "Someone"), "world_name": world.get("name"), "gallery_id": gallery_entry.id},
                "read": False, "created_at": datetime.now(timezone.utc).isoformat()
            })

    return {"message": "Published to gallery", "gallery_id": gallery_entry.id}


@router.get("/gallery")
async def browse_gallery(query: Optional[str] = None, tags: Optional[str] = None, sort_by: str = "recent", limit: int = 20, offset: int = 0):
    filter_query = {}
    if query:
        filter_query["$or"] = [
            {"name": {"$regex": query, "$options": "i"}},
            {"description": {"$regex": query, "$options": "i"}},
            {"creator_name": {"$regex": query, "$options": "i"}}
        ]
    if tags:
        filter_query["tags"] = {"$in": tags.split(",")}
    sort_options = {"recent": [("published_at", -1)], "popular": [("views", -1)], "downloads": [("downloads", -1)], "likes": [("likes", -1)]}
    sort = sort_options.get(sort_by, [("published_at", -1)])
    total = await db.gallery.count_documents(filter_query)
    entries = await db.gallery.find(filter_query, {"_id": 0}).sort(sort).skip(offset).limit(limit).to_list(limit)
    return {"total": total, "entries": entries, "limit": limit, "offset": offset}


@router.get("/gallery/featured")
async def get_featured_worlds():
    featured = await db.gallery.find({"featured": True}, {"_id": 0}).sort([("likes", -1)]).to_list(10)
    if len(featured) < 5:
        top_downloads = await db.gallery.find({}, {"_id": 0}).sort([("downloads", -1)]).limit(5).to_list(5)
        featured.extend([w for w in top_downloads if w not in featured])
    return {"featured": featured[:10]}


@router.get("/gallery/{gallery_id}")
async def get_gallery_entry(gallery_id: str):
    entry = await db.gallery.find_one({"id": gallery_id}, {"_id": 0})
    if not entry:
        raise HTTPException(status_code=404, detail="Gallery entry not found")
    await db.gallery.update_one({"id": gallery_id}, {"$inc": {"views": 1}})
    updated_entry = await db.gallery.find_one({"id": gallery_id}, {"_id": 0})
    return updated_entry


@router.post("/gallery/{gallery_id}/like")
async def like_gallery_entry(gallery_id: str, request: Request):
    result = await db.gallery.update_one({"id": gallery_id}, {"$inc": {"likes": 1}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Gallery entry not found")

    # Notify creator
    entry = await db.gallery.find_one({"id": gallery_id}, {"_id": 0})
    user = await get_current_user(request)
    if entry and entry.get("creator_id") and user and entry["creator_id"] != user.get("id"):
        await db.notifications.insert_one({
            "user_id": entry["creator_id"], "type": "world_liked",
            "data": {"liker_name": user.get("name", "Someone"), "world_name": entry.get("name")},
            "read": False, "created_at": datetime.now(timezone.utc).isoformat()
        })

    return {"message": "Liked", "gallery_id": gallery_id}


@router.post("/gallery/{gallery_id}/download")
async def download_from_gallery(gallery_id: str, request: Request):
    entry = await db.gallery.find_one({"id": gallery_id}, {"_id": 0})
    if not entry:
        raise HTTPException(status_code=404, detail="Gallery entry not found")
    world = await db.worlds.find_one({"id": entry["world_id"]}, {"_id": 0})
    if not world:
        raise HTTPException(status_code=404, detail="World data not found")
    await db.gallery.update_one({"id": gallery_id}, {"$inc": {"downloads": 1}})
    await track_analytics("gallery_download", entry["world_id"], {"gallery_id": gallery_id})

    # Notify creator
    user = await get_current_user(request)
    if entry.get("creator_id") and user and entry["creator_id"] != user.get("id"):
        await db.notifications.insert_one({
            "user_id": entry["creator_id"], "type": "world_downloaded",
            "data": {"downloader_name": user.get("name", "Someone"), "world_name": entry.get("name")},
            "read": False, "created_at": datetime.now(timezone.utc).isoformat()
        })

    return {"world": world, "gallery_info": entry}

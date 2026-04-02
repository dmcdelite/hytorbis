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


async def create_notification(user_id: str, ntype: str, data: dict):
    """Create a notification and push via WebSocket if user is connected."""
    notification = {
        "user_id": user_id, "type": ntype, "data": data,
        "read": False, "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.notifications.insert_one(notification)
    # Real-time push
    from websocket_manager import ws_manager
    notification.pop("_id", None)
    await ws_manager.push_notification(user_id, notification)


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

    # Auto-generate thumbnail
    from thumbnail import generate_thumbnail
    gallery_entry.thumbnail = generate_thumbnail(world)

    doc = gallery_entry.model_dump()
    doc['published_at'] = doc['published_at'].isoformat()
    await db.gallery.insert_one(doc)

    # Also store thumbnail on the world itself
    await db.worlds.update_one({"id": request_data.world_id}, {"$set": {"thumbnail": gallery_entry.thumbnail}})

    await track_analytics("gallery_publish", request_data.world_id, {"tags": request_data.tags})

    # Notify followers
    if user:
        followers = await db.follows.find({"following_id": user["id"]}).to_list(500)
        for f in followers:
            await create_notification(f["follower_id"], "new_publication", {
                "publisher_name": user.get("name", "Someone"),
                "world_name": world.get("name"), "gallery_id": gallery_entry.id
            })

    return {"message": "Published to gallery", "gallery_id": gallery_entry.id}


@router.get("/gallery")
async def browse_gallery(
    query: Optional[str] = None, tags: Optional[str] = None,
    sort_by: str = "recent", limit: int = 20, offset: int = 0,
    zone_types: Optional[str] = None,
    map_size_min: Optional[int] = None, map_size_max: Optional[int] = None,
    min_rating: Optional[float] = None,
    following_only: bool = False, request: Request = None
):
    filter_query = {}
    if query:
        filter_query["$or"] = [
            {"name": {"$regex": query, "$options": "i"}},
            {"description": {"$regex": query, "$options": "i"}},
            {"creator_name": {"$regex": query, "$options": "i"}}
        ]
    if tags:
        filter_query["tags"] = {"$in": tags.split(",")}
    if min_rating:
        filter_query["avg_rating"] = {"$gte": min_rating}
    if zone_types:
        # Filter by zone_types - need to check the source world
        zone_list = zone_types.split(",")
        # We'll filter in the entries that have matching zone types in their worlds
        world_ids_with_zones = []
        for zt in zone_list:
            matching = await db.worlds.find(
                {"zones": {"$elemMatch": {"type": zt.strip()}}}, {"id": 1, "_id": 0}
            ).to_list(500)
            world_ids_with_zones.extend([w["id"] for w in matching])
        if world_ids_with_zones:
            filter_query["world_id"] = {"$in": list(set(world_ids_with_zones))}
        else:
            return {"total": 0, "entries": [], "limit": limit, "offset": offset}
    if map_size_min or map_size_max:
        size_filter = {}
        valid_sizes = []
        all_entries_raw = await db.gallery.find({}, {"_id": 0, "id": 1, "map_size": 1}).to_list(1000)
        for e in all_entries_raw:
            ms = e.get("map_size", "64x64")
            try:
                w, h = ms.split("x")
                total = int(w) * int(h)
                if map_size_min and total < map_size_min * map_size_min:
                    continue
                if map_size_max and total > map_size_max * map_size_max:
                    continue
                valid_sizes.append(e["id"])
            except:
                valid_sizes.append(e["id"])
        if "id" not in filter_query:
            filter_query["id"] = {"$in": valid_sizes}
    if following_only and request:
        from auth_utils import get_current_user as gcu
        current = await gcu(request)
        if current:
            follows = await db.follows.find({"follower_id": current["id"]}).to_list(500)
            following_ids = [f["following_id"] for f in follows]
            filter_query["creator_id"] = {"$in": following_ids}

    sort_options = {
        "recent": [("published_at", -1)], "popular": [("views", -1)],
        "downloads": [("downloads", -1)], "likes": [("likes", -1)],
        "rating": [("avg_rating", -1)]
    }
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
        await create_notification(entry["creator_id"], "world_liked", {
            "liker_name": user.get("name", "Someone"), "world_name": entry.get("name")
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
        await create_notification(entry["creator_id"], "world_downloaded", {
            "downloader_name": user.get("name", "Someone"), "world_name": entry.get("name")
        })

    return {"world": world, "gallery_info": entry}


@router.post("/gallery/{gallery_id}/fork")
async def fork_from_gallery(gallery_id: str, request: Request):
    from auth_utils import require_auth as ra
    user = await ra(request)
    entry = await db.gallery.find_one({"id": gallery_id}, {"_id": 0})
    if not entry:
        raise HTTPException(status_code=404, detail="Gallery entry not found")
    world = await db.worlds.find_one({"id": entry["world_id"]}, {"_id": 0})
    if not world:
        raise HTTPException(status_code=404, detail="World data not found")

    import uuid
    body = None
    try:
        body = await request.json()
    except:
        pass
    fork_name = f"{world.get('name', 'World')} (Fork)"
    if body and body.get("name"):
        fork_name = body["name"]

    new_id = str(uuid.uuid4())
    forked = {
        **world,
        "id": new_id,
        "name": fork_name,
        "owner_id": user["id"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "forked_from": entry["world_id"],
        "collaborators": []
    }
    forked.pop("_id", None)
    await db.worlds.insert_one(forked)
    await db.gallery.update_one({"id": gallery_id}, {"$inc": {"downloads": 1}})

    # Notify creator
    if entry.get("creator_id") and entry["creator_id"] != user["id"]:
        await db.notifications.insert_one({
            "user_id": entry["creator_id"], "type": "world_forked",
            "data": {"forker_name": user.get("name", "Someone"), "world_name": world.get("name")},
            "read": False, "created_at": datetime.now(timezone.utc).isoformat()
        })

    return {"message": "World forked", "world_id": new_id, "name": fork_name}

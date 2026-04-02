from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from datetime import datetime, timezone
import uuid
import os

from database import db
from auth_utils import get_current_user, require_auth

router = APIRouter()

FRONTEND_URL = os.environ.get("CORS_ORIGINS", "https://hytorbisworldbuilder.com").split(",")[0].strip()


@router.get("/og/{share_token}", response_class=HTMLResponse)
async def og_page(share_token: str):
    """Serve HTML with Open Graph meta tags for social media crawlers. Redirects humans to frontend."""
    world = await db.worlds.find_one(
        {"share_token": share_token, "share_enabled": True},
        {"_id": 0, "id": 1, "name": 1, "description": 1, "map_width": 1, "map_height": 1, "zones": 1, "prefabs": 1}
    )
    if not world:
        raise HTTPException(status_code=404, detail="World not found")

    name = world.get("name", "Untitled World")
    desc = world.get("description", "")
    zones = len(world.get("zones", []))
    prefabs = len(world.get("prefabs", []))
    size = f"{world.get('map_width', 64)}x{world.get('map_height', 64)}"
    og_desc = desc if desc else f"A {size} world with {zones} zones and {prefabs} prefabs — built with Hyt Orbis World Builder"
    share_url = f"{FRONTEND_URL}?share={share_token}"
    logo = f"{FRONTEND_URL}/hytorbis-logo.png"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{name} — Hyt Orbis World Builder</title>
<meta property="og:title" content="{name} — Built with Hyt Orbis">
<meta property="og:description" content="{og_desc}">
<meta property="og:image" content="{logo}">
<meta property="og:url" content="{share_url}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Hyt Orbis World Builder">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{name} — Hyt Orbis">
<meta name="twitter:description" content="{og_desc}">
<meta name="twitter:image" content="{logo}">
<meta http-equiv="refresh" content="0;url={share_url}">
</head>
<body><p>Redirecting to <a href="{share_url}">{name} on Hyt Orbis</a>...</p></body>
</html>"""
    return HTMLResponse(content=html)


@router.post("/worlds/{world_id}/share")
async def toggle_share(world_id: str, request: Request):
    """Toggle sharing on/off for a world. Generates share_token if not present."""
    user = await require_auth(request)
    world = await db.worlds.find_one({"id": world_id}, {"_id": 0})
    if not world:
        raise HTTPException(status_code=404, detail="World not found")

    if world.get("owner_id") and world["owner_id"] != user["id"] and user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only the owner can manage sharing")

    currently_shared = world.get("share_enabled", False)
    share_token = world.get("share_token")

    if not share_token:
        share_token = str(uuid.uuid4())[:12]

    await db.worlds.update_one(
        {"id": world_id},
        {"$set": {
            "share_enabled": not currently_shared,
            "share_token": share_token,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )

    return {
        "share_enabled": not currently_shared,
        "share_token": share_token,
        "world_id": world_id
    }


@router.get("/worlds/{world_id}/share")
async def get_share_info(world_id: str, request: Request):
    """Get share status for a world (authenticated)."""
    user = await require_auth(request)
    world = await db.worlds.find_one({"id": world_id}, {"_id": 0})
    if not world:
        raise HTTPException(status_code=404, detail="World not found")

    return {
        "share_enabled": world.get("share_enabled", False),
        "share_token": world.get("share_token"),
        "world_id": world_id
    }


@router.get("/shared/{share_token}")
async def get_shared_world(share_token: str):
    """Public endpoint — no auth required. Returns world data for preview."""
    world = await db.worlds.find_one(
        {"share_token": share_token, "share_enabled": True},
        {"_id": 0}
    )
    if not world:
        raise HTTPException(status_code=404, detail="Shared world not found or sharing is disabled")

    # Get creator info
    creator = None
    if world.get("owner_id"):
        creator_doc = await db.users.find_one(
            {"id": world["owner_id"]},
            {"_id": 0, "id": 1, "name": 1, "avatar_url": 1, "bio": 1}
        )
        if creator_doc:
            creator = {
                "id": creator_doc.get("id"),
                "name": creator_doc.get("name", "Anonymous"),
                "avatar_url": creator_doc.get("avatar_url"),
                "bio": creator_doc.get("bio", "")
            }

    # Get thumbnail
    thumbnail = None
    thumb_doc = await db.worlds.find_one({"id": world["id"]}, {"_id": 0, "thumbnail": 1})
    if thumb_doc:
        thumbnail = thumb_doc.get("thumbnail")

    return {
        "world": {
            "id": world["id"],
            "name": world["name"],
            "seed": world.get("seed", ""),
            "description": world.get("description", ""),
            "map_width": world.get("map_width", 64),
            "map_height": world.get("map_height", 64),
            "zones": world.get("zones", []),
            "prefabs": world.get("prefabs", []),
            "terrain": world.get("terrain", {}),
            "created_at": world.get("created_at"),
        },
        "creator": creator,
        "thumbnail": thumbnail,
        "stats": {
            "zones": len(world.get("zones", [])),
            "prefabs": len(world.get("prefabs", [])),
            "map_size": f"{world.get('map_width', 64)}x{world.get('map_height', 64)}"
        }
    }

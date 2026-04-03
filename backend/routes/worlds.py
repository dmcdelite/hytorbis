from fastapi import APIRouter, HTTPException, Request
from typing import List, Optional
from datetime import datetime, timezone
from bson import ObjectId
import json
import base64
import io
import zipfile

from database import db
from auth_utils import get_current_user, require_auth
from models import (
    WorldConfig, WorldCreate, WorldUpdate, WorldFromTemplate, WorldImport,
    TerrainSettings, ZoneConfig, PrefabPlacement
)
from utils import generate_seed, generate_world_from_template
from templates import WORLD_TEMPLATES

router = APIRouter()


# ==================== WORLD CRUD ====================

@router.post("/worlds", response_model=WorldConfig)
async def create_world(world: WorldCreate, request: Request):
    seed = world.seed or generate_seed()
    user = await get_current_user(request)

    world_config = WorldConfig(
        name=world.name, seed=seed, description=world.description,
        map_width=world.map_width, map_height=world.map_height,
        owner_id=user["id"] if user else None
    )

    doc = world_config.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['updated_at'] = doc['updated_at'].isoformat()

    await db.worlds.insert_one(doc)
    return world_config


@router.get("/worlds")
async def list_worlds(request: Request):
    user = await get_current_user(request)
    if user:
        query = {"$or": [{"owner_id": user["id"]}, {"owner_id": None}, {"owner_id": {"$exists": False}}, {"is_public": True}]}
    else:
        query = {"$or": [{"owner_id": None}, {"owner_id": {"$exists": False}}, {"is_public": True}]}
    worlds = await db.worlds.find(query, {"_id": 0}).to_list(100)
    for world in worlds:
        if isinstance(world.get('created_at'), str):
            world['created_at'] = datetime.fromisoformat(world['created_at'])
        if isinstance(world.get('updated_at'), str):
            world['updated_at'] = datetime.fromisoformat(world['updated_at'])
    return worlds


@router.get("/worlds/{world_id}", response_model=WorldConfig)
async def get_world(world_id: str):
    world = await db.worlds.find_one({"id": world_id}, {"_id": 0})
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    if isinstance(world.get('created_at'), str):
        world['created_at'] = datetime.fromisoformat(world['created_at'])
    if isinstance(world.get('updated_at'), str):
        world['updated_at'] = datetime.fromisoformat(world['updated_at'])
    return world


@router.put("/worlds/{world_id}", response_model=WorldConfig)
async def update_world(world_id: str, update: WorldUpdate, request: Request):
    world = await db.worlds.find_one({"id": world_id}, {"_id": 0})
    if not world:
        raise HTTPException(status_code=404, detail="World not found")

    # Permission check: owner, admin, or editor collaborator
    user = await get_current_user(request)
    if world.get("owner_id") and user:
        is_owner = world["owner_id"] == user["id"]
        is_admin = user.get("role") == "admin"
        is_editor = any(c["user_id"] == user["id"] and c["role"] == "editor" for c in world.get("collaborators", []))
        if not (is_owner or is_admin or is_editor):
            raise HTTPException(status_code=403, detail="Not authorized to edit this world")

    update_data = update.model_dump(exclude_unset=True)
    update_data['updated_at'] = datetime.now(timezone.utc).isoformat()

    if 'terrain' in update_data and update_data['terrain']:
        update_data['terrain'] = update_data['terrain'] if isinstance(update_data['terrain'], dict) else update_data['terrain'].model_dump()
    if 'zones' in update_data and update_data['zones']:
        update_data['zones'] = [z if isinstance(z, dict) else z.model_dump() for z in update_data['zones']]
    if 'prefabs' in update_data and update_data['prefabs']:
        update_data['prefabs'] = [p if isinstance(p, dict) else p.model_dump() for p in update_data['prefabs']]

    await db.worlds.update_one({"id": world_id}, {"$set": update_data})

    updated_world = await db.worlds.find_one({"id": world_id}, {"_id": 0})
    if isinstance(updated_world.get('created_at'), str):
        updated_world['created_at'] = datetime.fromisoformat(updated_world['created_at'])
    if isinstance(updated_world.get('updated_at'), str):
        updated_world['updated_at'] = datetime.fromisoformat(updated_world['updated_at'])
    return updated_world


@router.delete("/worlds/{world_id}")
async def delete_world(world_id: str, request: Request):
    world = await db.worlds.find_one({"id": world_id}, {"_id": 0})
    if not world:
        raise HTTPException(status_code=404, detail="World not found")

    user = await get_current_user(request)
    if world.get("owner_id") and user:
        if world["owner_id"] != user["id"] and user.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Not authorized to delete this world")

    result = await db.worlds.delete_one({"id": world_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="World not found")
    return {"message": "World deleted", "id": world_id}


# ==================== ZONE & PREFAB MANAGEMENT ====================

@router.post("/worlds/{world_id}/zones", response_model=WorldConfig)
async def add_zone(world_id: str, zone: ZoneConfig):
    world = await db.worlds.find_one({"id": world_id}, {"_id": 0})
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    zones = world.get('zones', [])
    zones.append(zone.model_dump())
    await db.worlds.update_one({"id": world_id}, {"$set": {"zones": zones, "updated_at": datetime.now(timezone.utc).isoformat()}})
    return await get_world(world_id)


@router.delete("/worlds/{world_id}/zones/{zone_id}")
async def remove_zone(world_id: str, zone_id: str):
    world = await db.worlds.find_one({"id": world_id}, {"_id": 0})
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    zones = [z for z in world.get('zones', []) if z.get('id') != zone_id]
    await db.worlds.update_one({"id": world_id}, {"$set": {"zones": zones, "updated_at": datetime.now(timezone.utc).isoformat()}})
    return {"message": "Zone removed", "zone_id": zone_id}


@router.post("/worlds/{world_id}/prefabs", response_model=WorldConfig)
async def add_prefab(world_id: str, prefab: PrefabPlacement):
    world = await db.worlds.find_one({"id": world_id}, {"_id": 0})
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    prefabs = world.get('prefabs', [])
    prefabs.append(prefab.model_dump())
    await db.worlds.update_one({"id": world_id}, {"$set": {"prefabs": prefabs, "updated_at": datetime.now(timezone.utc).isoformat()}})
    return await get_world(world_id)


@router.delete("/worlds/{world_id}/prefabs/{prefab_id}")
async def remove_prefab(world_id: str, prefab_id: str):
    world = await db.worlds.find_one({"id": world_id}, {"_id": 0})
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    prefabs = [p for p in world.get('prefabs', []) if p.get('id') != prefab_id]
    await db.worlds.update_one({"id": world_id}, {"$set": {"prefabs": prefabs, "updated_at": datetime.now(timezone.utc).isoformat()}})
    return {"message": "Prefab removed", "prefab_id": prefab_id}


# ==================== VISIBILITY ====================

@router.put("/worlds/{world_id}/visibility")
async def update_world_visibility(world_id: str, is_public: bool, request: Request):
    user = await require_auth(request)
    world = await db.worlds.find_one({"id": world_id}, {"_id": 0})
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    if world.get("owner_id") and world["owner_id"] != user["id"] and user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    await db.worlds.update_one({"id": world_id}, {"$set": {"is_public": is_public, "updated_at": datetime.now(timezone.utc).isoformat()}})
    return {"message": "Visibility updated", "is_public": is_public}


# ==================== THUMBNAIL ====================

@router.post("/worlds/{world_id}/thumbnail")
async def generate_world_thumbnail(world_id: str):
    world = await db.worlds.find_one({"id": world_id}, {"_id": 0})
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    from thumbnail import generate_thumbnail
    thumb = generate_thumbnail(world)
    await db.worlds.update_one({"id": world_id}, {"$set": {"thumbnail": thumb}})
    return {"thumbnail": thumb}


@router.get("/worlds/{world_id}/thumbnail")
async def get_world_thumbnail(world_id: str):
    world = await db.worlds.find_one({"id": world_id}, {"_id": 0, "thumbnail": 1})
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    if world.get("thumbnail"):
        return {"thumbnail": world["thumbnail"]}
    # Generate on-the-fly if not cached
    full_world = await db.worlds.find_one({"id": world_id}, {"_id": 0})
    from thumbnail import generate_thumbnail
    thumb = generate_thumbnail(full_world)
    await db.worlds.update_one({"id": world_id}, {"$set": {"thumbnail": thumb}})
    return {"thumbnail": thumb}


# ==================== WORLD FORK/CLONE ====================

@router.post("/worlds/{world_id}/fork")
async def fork_world(world_id: str, request: Request):
    user = await require_auth(request)
    source = await db.worlds.find_one({"id": world_id}, {"_id": 0})
    if not source:
        raise HTTPException(status_code=404, detail="World not found")

    import uuid
    fork_name = f"{source.get('name', 'World')} (Fork)"

    body = None
    try:
        body = await request.json()
    except:
        pass
    if body and body.get("name"):
        fork_name = body["name"]

    new_id = str(uuid.uuid4())
    forked = {
        **source,
        "id": new_id,
        "name": fork_name,
        "owner_id": user["id"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "forked_from": world_id,
        "collaborators": []
    }
    forked.pop("_id", None)
    await db.worlds.insert_one(forked)
    return {"message": "World forked", "world_id": new_id, "name": fork_name}


# ==================== COLLABORATOR MANAGEMENT ====================

@router.get("/worlds/{world_id}/collaborators")
async def get_collaborators(world_id: str):
    world = await db.worlds.find_one({"id": world_id}, {"_id": 0})
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    collabs = world.get("collaborators", [])
    result = []
    for c in collabs:
        u = await db.users.find_one({"_id": ObjectId(c["user_id"])}, {"password_hash": 0})
        if u:
            result.append({
                "user_id": c["user_id"], "role": c["role"],
                "name": u.get("name", ""), "email": u.get("email", ""),
                "added_at": c.get("added_at", "")
            })
    owner_id = world.get("owner_id")
    owner = None
    if owner_id:
        o = await db.users.find_one({"_id": ObjectId(owner_id)}, {"password_hash": 0})
        if o:
            owner = {"user_id": owner_id, "name": o.get("name", ""), "role": "owner"}
    return {"owner": owner, "collaborators": result}


@router.post("/worlds/{world_id}/collaborators")
async def add_collaborator(world_id: str, request: Request):
    user = await require_auth(request)
    world = await db.worlds.find_one({"id": world_id}, {"_id": 0})
    if not world:
        raise HTTPException(status_code=404, detail="World not found")

    # Only owner or admin can add collaborators
    if world.get("owner_id") and world["owner_id"] != user["id"] and user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only the owner can manage collaborators")

    body = await request.json()
    target_user_id = body.get("user_id")
    role = body.get("role", "viewer")
    if role not in ("editor", "viewer"):
        raise HTTPException(status_code=400, detail="Role must be 'editor' or 'viewer'")

    target = await db.users.find_one({"_id": ObjectId(target_user_id)})
    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    collabs = world.get("collaborators", [])
    if any(c["user_id"] == target_user_id for c in collabs):
        raise HTTPException(status_code=400, detail="User is already a collaborator")

    collabs.append({"user_id": target_user_id, "role": role, "added_at": datetime.now(timezone.utc).isoformat()})
    await db.worlds.update_one({"id": world_id}, {"$set": {"collaborators": collabs}})

    # Notify the invited user with real-time push
    from routes.gallery import create_notification
    await create_notification(target_user_id, "collab_invite", {
        "world_name": world.get("name"), "world_id": world_id,
        "role": role, "inviter_name": user.get("name", "Someone")
    })

    return {"message": f"Added {role} collaborator"}


@router.put("/worlds/{world_id}/collaborators/{collab_user_id}")
async def update_collaborator_role(world_id: str, collab_user_id: str, request: Request):
    user = await require_auth(request)
    world = await db.worlds.find_one({"id": world_id}, {"_id": 0})
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    if world.get("owner_id") and world["owner_id"] != user["id"] and user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only the owner can manage collaborators")

    body = await request.json()
    new_role = body.get("role", "viewer")
    if new_role not in ("editor", "viewer"):
        raise HTTPException(status_code=400, detail="Role must be 'editor' or 'viewer'")

    collabs = world.get("collaborators", [])
    found = False
    for c in collabs:
        if c["user_id"] == collab_user_id:
            c["role"] = new_role
            found = True
            break
    if not found:
        raise HTTPException(status_code=404, detail="Collaborator not found")

    await db.worlds.update_one({"id": world_id}, {"$set": {"collaborators": collabs}})
    return {"message": f"Updated role to {new_role}"}


@router.delete("/worlds/{world_id}/collaborators/{collab_user_id}")
async def remove_collaborator(world_id: str, collab_user_id: str, request: Request):
    user = await require_auth(request)
    world = await db.worlds.find_one({"id": world_id}, {"_id": 0})
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    if world.get("owner_id") and world["owner_id"] != user["id"] and user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only the owner can manage collaborators")

    collabs = world.get("collaborators", [])
    new_collabs = [c for c in collabs if c["user_id"] != collab_user_id]
    if len(new_collabs) == len(collabs):
        raise HTTPException(status_code=404, detail="Collaborator not found")

    await db.worlds.update_one({"id": world_id}, {"$set": {"collaborators": new_collabs}})
    return {"message": "Collaborator removed"}


# ==================== TEMPLATES ====================

@router.get("/templates")
async def get_templates():
    return {
        "templates": [
            {"id": tid, "name": t["name"], "description": t["description"],
             "terrain_preview": t["terrain"], "difficulty_range": t["difficulty_range"]}
            for tid, t in WORLD_TEMPLATES.items()
        ]
    }


@router.post("/worlds/from-template", response_model=WorldConfig)
async def create_world_from_template(req: WorldFromTemplate, request: Request):
    if req.template not in WORLD_TEMPLATES:
        raise HTTPException(status_code=400, detail=f"Unknown template: {req.template}")
    template = WORLD_TEMPLATES[req.template]
    seed = generate_seed(req.template)
    zones, prefabs, terrain = generate_world_from_template(req.template, req.map_width, req.map_height)
    user = await get_current_user(request)

    world_config = WorldConfig(
        name=req.name, seed=seed, description=template["description"],
        terrain=terrain, zones=zones, prefabs=prefabs,
        map_width=req.map_width, map_height=req.map_height,
        owner_id=user["id"] if user else None
    )

    doc = world_config.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['updated_at'] = doc['updated_at'].isoformat()
    doc['zones'] = [z.model_dump() if hasattr(z, 'model_dump') else z for z in doc['zones']]
    doc['prefabs'] = [p.model_dump() if hasattr(p, 'model_dump') else p for p in doc['prefabs']]
    doc['terrain'] = terrain.model_dump() if hasattr(terrain, 'model_dump') else doc['terrain']

    await db.worlds.insert_one(doc)
    return world_config


# ==================== IMPORT ====================

@router.post("/worlds/import", response_model=WorldConfig)
async def import_world(req: WorldImport, request: Request):
    config = req.config
    world_name = req.name or config.get("name") or config.get("worldgen", {}).get("name") or "Imported World"
    seed = config.get("seed") or config.get("worldgen", {}).get("seed") or generate_seed()
    user = await get_current_user(request)

    if "worldgen" in config:
        hytale_config = config["worldgen"]
        map_width = min(512, max(5, hytale_config.get("size", {}).get("x", 256) // 256))
        map_height = min(512, max(5, hytale_config.get("size", {}).get("z", 256) // 256))
        terrain_data = hytale_config.get("terrain", {})
        terrain = TerrainSettings(
            height_scale=terrain_data.get("heightScale", 1.0),
            cave_density=terrain_data.get("caveDensity", 0.5),
            river_frequency=terrain_data.get("riverFrequency", 0.3),
            mountain_scale=terrain_data.get("mountainScale", 0.5),
            ocean_level=terrain_data.get("oceanLevel", 0.3)
        )
        zones = [ZoneConfig(type=z.get("type", "emerald_grove"), x=z.get("bounds", {}).get("x", 0) // 256, y=z.get("bounds", {}).get("z", 0) // 256, difficulty=z.get("difficulty", 1)) for z in config.get("zones", [])]
        prefabs = [PrefabPlacement(type=s.get("type", "dungeon"), x=s.get("position", {}).get("x", 0) // 256, y=s.get("position", {}).get("z", 0) // 256, rotation=s.get("rotation", 0), scale=s.get("scale", 1.0)) for s in config.get("structures", [])]
    else:
        map_width = min(512, max(5, config.get("map_width", 64)))
        map_height = min(512, max(5, config.get("map_height", 64)))
        terrain_data = config.get("terrain", {})
        terrain = TerrainSettings(**terrain_data) if terrain_data else TerrainSettings()
        zones = [ZoneConfig(**z) for z in config.get("zones", [])]
        prefabs = [PrefabPlacement(**p) for p in config.get("prefabs", [])]

    world_config = WorldConfig(
        name=world_name, seed=seed, description=config.get("description", "Imported world"),
        terrain=terrain, zones=zones, prefabs=prefabs,
        map_width=map_width, map_height=map_height,
        owner_id=user["id"] if user else None
    )

    doc = world_config.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['updated_at'] = doc['updated_at'].isoformat()
    doc['zones'] = [z.model_dump() if hasattr(z, 'model_dump') else z for z in doc['zones']]
    doc['prefabs'] = [p.model_dump() if hasattr(p, 'model_dump') else p for p in doc['prefabs']]
    doc['terrain'] = terrain.model_dump() if hasattr(terrain, 'model_dump') else doc['terrain']

    await db.worlds.insert_one(doc)
    return world_config


# ==================== EXPORTS ====================

@router.get("/worlds/{world_id}/export/json")
async def export_world_json(world_id: str):
    world = await db.worlds.find_one({"id": world_id}, {"_id": 0})
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    if isinstance(world.get('created_at'), datetime):
        world['created_at'] = world['created_at'].isoformat()
    if isinstance(world.get('updated_at'), datetime):
        world['updated_at'] = world['updated_at'].isoformat()
    return {"format": "json", "version": "1.0", "world": world}


@router.get("/worlds/{world_id}/export/hytale")
async def export_world_hytale(world_id: str):
    world = await db.worlds.find_one({"id": world_id}, {"_id": 0})
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    hytale_config = {
        "worldgen": {
            "seed": world.get('seed', ''), "name": world.get('name', 'Unnamed World'),
            "size": {"x": world.get('map_width', 20) * 256, "z": world.get('map_height', 20) * 256},
            "terrain": {
                "heightScale": world.get('terrain', {}).get('height_scale', 1.0),
                "caveDensity": world.get('terrain', {}).get('cave_density', 0.5),
                "riverFrequency": world.get('terrain', {}).get('river_frequency', 0.3),
                "mountainScale": world.get('terrain', {}).get('mountain_scale', 0.5),
                "oceanLevel": world.get('terrain', {}).get('ocean_level', 0.3)
            }
        },
        "zones": [{"type": z.get('type'), "bounds": {"x": z.get('x', 0) * 256, "z": z.get('y', 0) * 256, "width": z.get('width', 1) * 256, "height": z.get('height', 1) * 256}, "difficulty": z.get('difficulty', 1), "biomes": z.get('biomes', [])} for z in world.get('zones', [])],
        "structures": [{"type": p.get('type'), "position": {"x": p.get('x', 0) * 256 + 128, "z": p.get('y', 0) * 256 + 128}, "rotation": p.get('rotation', 0), "scale": p.get('scale', 1.0)} for p in world.get('prefabs', [])],
        "metadata": {"generator": "Hyt Orbis World Builder", "version": "1.0.0", "created": world.get('created_at', ''), "description": world.get('description', '')}
    }
    return {"format": "hytale", "version": "1.0", "config": hytale_config}


@router.get("/worlds/{world_id}/export/prefab")
async def export_world_prefab(world_id: str):
    world = await db.worlds.find_one({"id": world_id}, {"_id": 0})
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    prefab_export = {
        "formatVersion": 1, "prefabType": "world_prefabs",
        "metadata": {"name": world.get('name', 'Unnamed World'), "author": "Hyt Orbis World Builder", "version": "1.0.0", "seed": world.get('seed', ''), "created": world.get('created_at', ''), "description": world.get('description', '')},
        "worldSettings": {"dimensions": {"width": world.get('map_width', 64) * 256, "height": 256, "depth": world.get('map_height', 64) * 256}, "terrain": {"heightScale": world.get('terrain', {}).get('height_scale', 1.0), "caveDensity": world.get('terrain', {}).get('cave_density', 0.5), "riverFrequency": world.get('terrain', {}).get('river_frequency', 0.3), "mountainScale": world.get('terrain', {}).get('mountain_scale', 0.5), "oceanLevel": world.get('terrain', {}).get('ocean_level', 0.3)}},
        "prefabs": [{"id": p.get('id', ''), "type": p.get('type', 'dungeon'), "name": f"{p.get('type', 'structure').replace('_', ' ').title()} at ({p.get('x', 0)}, {p.get('y', 0)})", "position": {"x": p.get('x', 0) * 256 + 128, "y": 64, "z": p.get('y', 0) * 256 + 128}, "rotation": {"y": p.get('rotation', 0)}, "scale": {"x": p.get('scale', 1.0), "y": p.get('scale', 1.0), "z": p.get('scale', 1.0)}, "properties": {"spawnable": True, "destructible": p.get('type') not in ['portal'], "lootTable": f"loot/{p.get('type', 'generic')}"}} for p in world.get('prefabs', [])],
        "zoneConfigs": [{"id": z.get('id', ''), "zoneType": z.get('type', 'emerald_grove'), "bounds": {"minX": z.get('x', 0) * 256, "minZ": z.get('y', 0) * 256, "maxX": (z.get('x', 0) + z.get('width', 1)) * 256, "maxZ": (z.get('y', 0) + z.get('height', 1)) * 256}, "difficulty": z.get('difficulty', 1), "biomes": [{"type": b.get('type', 'plains'), "weight": b.get('density', 0.5), "variation": b.get('variation', 0.3)} for b in z.get('biomes', [])]} for z in world.get('zones', [])]
    }
    return {"format": "prefab.json", "version": "1.0", "filename": f"{world.get('name', 'world').replace(' ', '_').lower()}.prefab.json", "data": prefab_export}


@router.get("/worlds/{world_id}/export/jar")
async def export_world_jar(world_id: str):
    world = await db.worlds.find_one({"id": world_id}, {"_id": 0})
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    world_name = world.get('name', 'HytaleWorld').replace(' ', '')
    world_name_lower = world_name.lower()
    pkg = f"com.hytorbis.worldgen.{world_name_lower}"
    pkg_path = pkg.replace('.', '/')

    # Build zone registry entries
    zones = world.get('zones', [])
    prefabs = world.get('prefabs', [])
    terrain = world.get('terrain', {})

    # Group zones by type for unique zone definitions
    zone_types_used = {}
    for z in zones:
        zt = z.get('type', 'emerald_grove')
        if zt not in zone_types_used:
            zone_types_used[zt] = []
        zone_types_used[zt].append(z)

    # Generate main plugin Java class — matches Hytale Server Plugin API
    main_java = f"""package {pkg};

import com.hytale.server.plugin.Plugin;
import com.hytale.server.worldgen.*;
import com.hytale.server.worldgen.zone.*;
import com.hytale.server.worldgen.biome.*;
import com.hytale.server.worldgen.cave.*;

/**
 * {world.get('name')} — Generated by Hyt Orbis World Builder
 * Seed: {world.get('seed', '')}
 * Size: {world.get('map_width', 64)}x{world.get('map_height', 64)}
 */
public class {world_name}Plugin extends Plugin {{

    @Override
    public void onEnable() {{
        getLogger().info("{world.get('name')} world generation loaded");
        registerZones();
        registerCaves();
    }}

    private void registerZones() {{
        ZonePatternGenerator zoneGen = getWorldGenerator().getZoneGenerator();
"""
    # Add zone registrations
    zone_id_counter = 100
    for zt, zone_list in zone_types_used.items():
        class_name = ''.join(w.capitalize() for w in zt.split('_'))
        discovery = zone_list[0].get('discovery', {}) or {}
        display_name = discovery.get('display_name', zt.replace('_', ' ').title())
        sound_event = discovery.get('sound_event', f'zone.{zt}.discover')
        major = str(discovery.get('major_zone', True)).lower()
        duration = discovery.get('duration', 5.0)
        fade_in = discovery.get('fade_in', 2.0)
        fade_out = discovery.get('fade_out', 1.5)
        border_fade = zone_list[0].get('border_fade', 0.3)

        # Biome config
        biomes = zone_list[0].get('biomes', [])
        biome_lines = ""
        for b in biomes[:6]:
            biome_lines += f"""
            new TileBiome("{b.get('type', 'plains')}", {b.get('density', 0.5)}f, {b.get('variation', 0.3)}f),"""

        # Cave config
        caves = zone_list[0].get('caves', [])
        cave_lines = ""
        for c in caves[:4]:
            mask_str = ', '.join(f'"{m}"' for m in c.get('biome_mask', [])[:6])
            cave_lines += f"""
            new CaveType("{c.get('type', 'natural')}", {c.get('density', 0.5)}f, {c.get('min_depth', 10)}, {c.get('max_depth', 64)}, new String[]{{{mask_str}}}),"""

        main_java += f"""
        // {class_name} Zone (ID: {zone_id_counter})
        ZoneDiscoveryConfig {zt}Discovery = new ZoneDiscoveryConfig(
            true, "{display_name}", "{sound_event}",
            "icons/{zt}.png", {major}, {duration}f, {fade_in}f, {fade_out}f
        );

        BiomePatternGenerator {zt}Biomes = new BiomePatternGenerator(
            new TileBiome[]{{{biome_lines}
            }}
        );

        CaveGenerator {zt}Caves = new CaveGenerator(
            new CaveType[]{{{cave_lines}
            }}
        );

        Zone {zt}Zone = new Zone(
            {zone_id_counter}, "{zt}", {zt}Discovery,
            {zt}Caves, {zt}Biomes, null
        );
        {zt}Zone.setBorderFade({border_fade}f);
        zoneGen.registerZone({zt}Zone);
"""
        zone_id_counter += 1

    main_java += """    }

    private void registerCaves() {
        // Cave biome masks are configured per-zone above
        // Additional global cave configuration can be added here
    }

    @Override
    public void onDisable() {
        getLogger().info("World generation unloaded");
    }
}
"""

    # Generate zone placement config
    zone_placement = {
        "seed": world.get('seed', ''),
        "dimensions": {"width": world.get('map_width', 64), "height": world.get('map_height', 64)},
        "zonePlacements": [],
        "structurePlacements": []
    }
    for z in zones[:200]:
        caves_data = [{"type": c.get("type", "natural"), "density": c.get("density", 0.5), "minDepth": c.get("min_depth", 10), "maxDepth": c.get("max_depth", 64), "biomeMask": c.get("biome_mask", [])} for c in z.get("caves", [])[:4]]
        zone_placement["zonePlacements"].append({
            "type": z.get("type"), "x": z.get("x", 0), "z": z.get("y", 0),
            "difficulty": z.get("difficulty", 1), "borderFade": z.get("border_fade", 0.3),
            "biomes": [{"type": b.get("type"), "density": b.get("density", 0.5), "variation": b.get("variation", 0.3)} for b in z.get("biomes", [])[:6]],
            "caves": caves_data,
            "discovery": z.get("discovery") or {}
        })
    for p in prefabs[:100]:
        zone_placement["structurePlacements"].append({
            "type": p.get("type"), "position": {"x": p.get("x", 0) * 256 + 128, "y": 64, "z": p.get("y", 0) * 256 + 128},
            "rotation": p.get("rotation", 0), "scale": p.get("scale", 1.0)
        })

    # Build JAR
    jar_buffer = io.BytesIO()
    with zipfile.ZipFile(jar_buffer, 'w', zipfile.ZIP_DEFLATED) as jar:
        jar.writestr("META-INF/MANIFEST.MF", f"Manifest-Version: 1.0\nCreated-By: Hyt Orbis World Builder\nMain-Class: {pkg}.{world_name}Plugin\n")
        jar.writestr("mod.json", json.dumps({
            "id": world_name_lower, "name": world.get('name'), "version": "1.0.0",
            "description": world.get('description', ''), "authors": ["Hyt Orbis World Builder"],
            "dependencies": {"hytale": ">=1.0.0"},
            "entrypoints": {"main": f"{pkg}.{world_name}Plugin"},
            "worldgen": {"seed": world.get('seed', ''), "type": "custom", "systems": ["zones", "biomes", "caves"]}
        }, indent=2))
        jar.writestr(f"{pkg_path}/{world_name}Plugin.java", main_java)
        jar.writestr(f"worldgen/{world_name_lower}/placement.json", json.dumps(zone_placement, indent=2))
        jar.writestr(f"worldgen/{world_name_lower}/terrain.json", json.dumps({
            "heightScale": terrain.get('height_scale', 1.0), "caveDensity": terrain.get('cave_density', 0.5),
            "riverFrequency": terrain.get('river_frequency', 0.3), "mountainScale": terrain.get('mountain_scale', 0.5),
            "oceanLevel": terrain.get('ocean_level', 0.3), "biomeBlending": True, "structureSpacing": 256
        }, indent=2))
        jar.writestr("README.md", f"""# {world.get('name')}
Generated by [Hyt Orbis World Builder](https://hytorbisworldbuilder.com)

**Seed:** {world.get('seed')}
**Size:** {world.get('map_width')}x{world.get('map_height')}
**Zones:** {len(zones)} | **Structures:** {len(prefabs)}

## Installation
1. Place this .jar in your Hytale server's `mods/` folder
2. Restart the server
3. The world generation will be applied automatically

## Architecture
This mod uses Hytale's world generation API:
- `ZonePatternGenerator` for zone registration
- `BiomePatternGenerator` for biome patterns within zones
- `CaveGenerator` with `CaveType[]` and biome masks
- `ZoneDiscoveryConfig` for player notifications on zone entry
- Border fade transitions between zones

See `placement.json` for zone coordinates and cave configurations.
""")
    jar_buffer.seek(0)
    jar_bytes = jar_buffer.getvalue()
    return {"format": "jar", "version": "2.0", "filename": f"{world_name_lower}_worldgen.jar", "size_bytes": len(jar_bytes), "data_base64": base64.b64encode(jar_bytes).decode('utf-8')}


# ==================== 3D PREVIEW ====================

@router.get("/worlds/{world_id}/preview-3d")
async def get_3d_preview_data(world_id: str):
    world = await db.worlds.find_one({"id": world_id}, {"_id": 0})
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    terrain = world.get("terrain", {})
    zones = world.get("zones", [])
    map_width = world.get("map_width", 64)
    map_height = world.get("map_height", 64)
    height_map = []
    zone_map = {(z.get("x"), z.get("y")): z for z in zones}
    for y in range(map_height):
        row = []
        for x in range(map_width):
            base_height = 0.5
            zone = zone_map.get((x, y))
            if zone:
                zone_heights = {"emerald_grove": 0.5, "borea": 0.7, "desert": 0.3, "arctic": 0.8, "corrupted": 0.4}
                base_height = zone_heights.get(zone.get("type", "emerald_grove"), 0.5)
            height = base_height * terrain.get("height_scale", 1.0)
            height += terrain.get("mountain_scale", 0.5) * 0.2 * (((x + y) % 7) / 7)
            row.append(round(min(1.0, max(0.0, height)), 2))
        height_map.append(row)
    prefabs_3d = [{"type": p.get("type"), "position": {"x": p.get("x"), "y": p.get("y")}, "rotation": p.get("rotation", 0), "scale": p.get("scale", 1.0), "height": height_map[p.get("y", 0)][p.get("x", 0)] if p.get("y", 0) < map_height and p.get("x", 0) < map_width else 0.5} for p in world.get("prefabs", [])]
    return {"world_id": world_id, "dimensions": {"width": map_width, "height": map_height}, "terrain": terrain, "height_map": height_map, "zones": zones, "prefabs": prefabs_3d, "render_settings": {"water_level": terrain.get("ocean_level", 0.3), "fog_density": 0.02, "ambient_light": 0.4}}


# ==================== REFERENCE ====================

@router.get("/reference/zones")
async def get_zone_types():
    return {"zones": [
        {"id": "emerald_grove", "name": "Emerald Grove", "color": "#10B981", "description": "Lush forests and green valleys"},
        {"id": "borea", "name": "Borea", "color": "#06B6D4", "description": "Icy tundra and frozen peaks"},
        {"id": "desert", "name": "Desert", "color": "#F59E0B", "description": "Scorching sands and ancient ruins"},
        {"id": "arctic", "name": "Arctic", "color": "#E2E8F0", "description": "Snow-covered landscapes"},
        {"id": "corrupted", "name": "Corrupted", "color": "#8B5CF6", "description": "Dark magic-infused lands"}
    ]}


@router.get("/reference/prefabs")
async def get_prefab_types():
    return {"prefabs": [
        {"id": "dungeon", "name": "Dungeon", "icon": "castle", "description": "Underground challenge areas"},
        {"id": "village", "name": "Village", "icon": "home", "description": "NPC settlements"},
        {"id": "ruins", "name": "Ruins", "icon": "landmark", "description": "Ancient structures"},
        {"id": "tower", "name": "Tower", "icon": "building", "description": "Vertical structures"},
        {"id": "cave_entrance", "name": "Cave Entrance", "icon": "mountain", "description": "Underground access points"},
        {"id": "portal", "name": "Portal", "icon": "sparkles", "description": "Zone transition points"}
    ]}


@router.get("/reference/biomes")
async def get_biome_types():
    return {"biomes": [
        {"id": "forest", "name": "Forest", "zones": ["emerald_grove"]},
        {"id": "plains", "name": "Plains", "zones": ["emerald_grove", "desert"]},
        {"id": "swamp", "name": "Swamp", "zones": ["emerald_grove"]},
        {"id": "mountains", "name": "Mountains", "zones": ["emerald_grove", "borea", "arctic"]},
        {"id": "tundra", "name": "Tundra", "zones": ["borea", "arctic"]},
        {"id": "glacier", "name": "Glacier", "zones": ["arctic"]},
        {"id": "dunes", "name": "Dunes", "zones": ["desert"]},
        {"id": "oasis", "name": "Oasis", "zones": ["desert"]},
        {"id": "void", "name": "Void", "zones": ["corrupted"]},
        {"id": "wasteland", "name": "Wasteland", "zones": ["corrupted"]}
    ]}


@router.post("/seed/generate")
async def generate_world_seed(style: Optional[str] = None):
    from models import SeedGenerateRequest
    seed = generate_seed(style)
    return {"seed": seed, "style": style}


@router.get("/seed/random")
async def get_random_seed():
    return {"seed": generate_seed()}

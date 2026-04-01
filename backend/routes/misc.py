from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Optional, Dict, Any
from datetime import datetime, timezone

from database import db
from models import CollabSession, CustomPrefab, CustomPrefabCreate, AnalyticsEvent
from websocket_manager import ws_manager

router = APIRouter()

# In-memory collaboration sessions
collab_sessions: Dict[str, Dict[str, Any]] = {}


# ==================== COLLABORATION ====================

@router.post("/collab/join")
async def join_collab_session(session: CollabSession):
    world_id = session.world_id
    user_id = session.user_id
    if world_id not in collab_sessions:
        collab_sessions[world_id] = {"users": {}, "created_at": datetime.now(timezone.utc).isoformat()}
    collab_sessions[world_id]["users"][user_id] = {"joined_at": datetime.now(timezone.utc).isoformat(), "cursor": {"x": 0, "y": 0}}
    return {"session_id": world_id, "users": list(collab_sessions[world_id]["users"].keys()), "user_count": len(collab_sessions[world_id]["users"])}


@router.post("/collab/leave")
async def leave_collab_session(session: CollabSession):
    world_id = session.world_id
    user_id = session.user_id
    if world_id in collab_sessions and user_id in collab_sessions[world_id]["users"]:
        del collab_sessions[world_id]["users"][user_id]
        if not collab_sessions[world_id]["users"]:
            del collab_sessions[world_id]
            return {"message": "Session ended", "users": []}
    return {"message": "Left session", "users": list(collab_sessions.get(world_id, {}).get("users", {}).keys())}


@router.post("/collab/update")
async def update_collab_session(session: CollabSession):
    world_id = session.world_id
    if world_id not in collab_sessions:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Session not found")
    if "updates" not in collab_sessions[world_id]:
        collab_sessions[world_id]["updates"] = []
    collab_sessions[world_id]["updates"].append({"user_id": session.user_id, "action": session.action, "data": session.data, "timestamp": datetime.now(timezone.utc).isoformat()})
    collab_sessions[world_id]["updates"] = collab_sessions[world_id]["updates"][-100:]
    return {"message": "Update sent", "update_count": len(collab_sessions[world_id]["updates"])}


@router.get("/collab/{world_id}/status")
async def get_collab_status(world_id: str, since: Optional[str] = None):
    if world_id not in collab_sessions:
        return {"active": False, "users": [], "updates": []}
    session = collab_sessions[world_id]
    updates = session.get("updates", [])
    if since:
        updates = [u for u in updates if u["timestamp"] > since]
    return {"active": True, "users": list(session["users"].keys()), "user_count": len(session["users"]), "updates": updates[-20:]}


# ==================== WEBSOCKET ====================

@router.websocket("/ws/collab/{world_id}/{user_id}")
async def websocket_collab(websocket: WebSocket, world_id: str, user_id: str):
    await ws_manager.connect(websocket, world_id, user_id)
    try:
        await websocket.send_json({"type": "connected", "user_id": user_id, "users": ws_manager.get_users(world_id)})
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")
            if msg_type == "cursor_move":
                await ws_manager.update_cursor(world_id, user_id, data.get("x", 0), data.get("y", 0))
                await ws_manager.broadcast(world_id, {"type": "cursor_update", "user_id": user_id, "x": data.get("x", 0), "y": data.get("y", 0)}, exclude=websocket)
            elif msg_type == "zone_add":
                await ws_manager.broadcast(world_id, {"type": "zone_added", "user_id": user_id, "zone": data.get("zone")}, exclude=websocket)
            elif msg_type == "zone_remove":
                await ws_manager.broadcast(world_id, {"type": "zone_removed", "user_id": user_id, "zone_id": data.get("zone_id")}, exclude=websocket)
            elif msg_type == "prefab_add":
                await ws_manager.broadcast(world_id, {"type": "prefab_added", "user_id": user_id, "prefab": data.get("prefab")}, exclude=websocket)
            elif msg_type == "prefab_remove":
                await ws_manager.broadcast(world_id, {"type": "prefab_removed", "user_id": user_id, "prefab_id": data.get("prefab_id")}, exclude=websocket)
            elif msg_type == "chat":
                await ws_manager.broadcast(world_id, {"type": "chat_message", "user_id": user_id, "message": data.get("message")}, exclude=websocket)
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, world_id, user_id)
        await ws_manager.broadcast(world_id, {"type": "user_left", "user_id": user_id, "users": ws_manager.get_users(world_id)})


# ==================== CUSTOM PREFABS ====================

@router.get("/prefabs/custom")
async def list_custom_prefabs(include_public: bool = True):
    query = {}
    if include_public:
        query = {"$or": [{"is_public": True}, {"is_public": {"$exists": False}}]}
    prefabs = await db.custom_prefabs.find(query, {"_id": 0}).to_list(100)
    return {"prefabs": prefabs}


@router.post("/prefabs/custom", response_model=CustomPrefab)
async def create_custom_prefab(prefab: CustomPrefabCreate):
    custom_prefab = CustomPrefab(
        name=prefab.name, description=prefab.description, icon=prefab.icon,
        color=prefab.color, category=prefab.category,
        size=prefab.size or {"width": 1, "height": 1, "depth": 1},
        properties=prefab.properties or {}, is_public=prefab.is_public, tags=prefab.tags
    )
    doc = custom_prefab.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.custom_prefabs.insert_one(doc)
    return custom_prefab


@router.get("/prefabs/custom/{prefab_id}")
async def get_custom_prefab(prefab_id: str):
    prefab = await db.custom_prefabs.find_one({"id": prefab_id}, {"_id": 0})
    if not prefab:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Custom prefab not found")
    return prefab


@router.delete("/prefabs/custom/{prefab_id}")
async def delete_custom_prefab(prefab_id: str):
    result = await db.custom_prefabs.delete_one({"id": prefab_id})
    if result.deleted_count == 0:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Custom prefab not found")
    return {"message": "Custom prefab deleted", "id": prefab_id}


# ==================== ANALYTICS ====================

@router.post("/analytics/track")
async def track_event(event: AnalyticsEvent):
    doc = event.model_dump()
    doc['timestamp'] = doc['timestamp'].isoformat()
    await db.analytics.insert_one(doc)
    return {"message": "Event tracked"}


@router.get("/analytics/world/{world_id}")
async def get_world_analytics(world_id: str):
    pipeline = [{"$match": {"world_id": world_id}}, {"$group": {"_id": "$event_type", "count": {"$sum": 1}}}]
    event_counts = await db.analytics.aggregate(pipeline).to_list(100)
    recent = await db.analytics.find({"world_id": world_id}, {"_id": 0}).sort([("timestamp", -1)]).limit(50).to_list(50)
    world = await db.worlds.find_one({"id": world_id}, {"_id": 0})
    return {
        "world_id": world_id,
        "event_counts": {e["_id"]: e["count"] for e in event_counts},
        "recent_events": recent,
        "world_stats": {"zones": len(world.get("zones", [])) if world else 0, "prefabs": len(world.get("prefabs", [])) if world else 0, "map_size": f"{world.get('map_width', 0)}x{world.get('map_height', 0)}" if world else "0x0"}
    }


@router.get("/analytics/summary")
async def get_analytics_summary():
    total_worlds = await db.worlds.count_documents({})
    total_published = await db.gallery.count_documents({})
    total_prefabs = await db.custom_prefabs.count_documents({})
    pipeline = [{"$group": {"_id": "$event_type", "count": {"$sum": 1}}}]
    event_counts = await db.analytics.aggregate(pipeline).to_list(100)
    yesterday = datetime.now(timezone.utc).isoformat()[:10]
    recent_events = await db.analytics.count_documents({"timestamp": {"$gte": yesterday}})
    tag_pipeline = [{"$unwind": "$tags"}, {"$group": {"_id": "$tags", "count": {"$sum": 1}}}, {"$sort": {"count": -1}}, {"$limit": 10}]
    popular_tags = await db.gallery.aggregate(tag_pipeline).to_list(10)
    return {
        "total_worlds": total_worlds, "total_published": total_published,
        "total_custom_prefabs": total_prefabs,
        "event_counts": {e["_id"]: e["count"] for e in event_counts},
        "recent_activity_24h": recent_events,
        "popular_tags": [{"tag": t["_id"], "count": t["count"]} for t in popular_tags]
    }

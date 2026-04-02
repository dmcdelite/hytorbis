from fastapi import APIRouter, HTTPException, Request
from datetime import datetime, timezone
import random

from database import db
from models import (
    AIChatRequest, AIChatResponse, AIAutoGenerateRequest, TerrainSettings
)
from utils import get_ai_response, ai_auto_generate
from templates import WORLD_TEMPLATES
from auth_utils import require_subscription

router = APIRouter()


@router.post("/ai/chat", response_model=AIChatResponse)
async def ai_chat(request: AIChatRequest, req: Request):
    await require_subscription(req, feature="ai")
    world = await db.worlds.find_one({"id": request.world_id}, {"_id": 0})
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    result = await get_ai_response(request.message, world, request.provider)
    return AIChatResponse(**result)


@router.post("/ai/auto-generate")
async def ai_auto_generate_world(request: AIAutoGenerateRequest, req: Request):
    await require_subscription(req, feature="ai")
    world = await db.worlds.find_one({"id": request.world_id}, {"_id": 0})
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    generated = await ai_auto_generate(request.prompt, world, request.provider)
    update_data = {"zones": generated["zones"], "prefabs": generated["prefabs"], "updated_at": datetime.now(timezone.utc).isoformat()}
    if generated.get("terrain"):
        update_data["terrain"] = generated["terrain"]
    if generated.get("description"):
        update_data["description"] = generated["description"]
    await db.worlds.update_one({"id": request.world_id}, {"$set": update_data})
    updated_world = await db.worlds.find_one({"id": request.world_id}, {"_id": 0})
    return {"world": updated_world, "generated": generated}


@router.post("/generate/preview")
async def generate_procedural_preview(template: str = "adventure", map_width: int = 32, map_height: int = 32, steps: int = 5):
    if template not in WORLD_TEMPLATES:
        template = "adventure"
    tmpl = WORLD_TEMPLATES[template]
    generation_steps = []
    terrain = TerrainSettings(**tmpl["terrain"])
    generation_steps.append({"step": 1, "name": "Terrain Generation", "description": "Creating base terrain heightmap", "terrain": terrain.model_dump(), "zones": [], "prefabs": []})
    zones = []
    zone_types = list(tmpl["zone_distribution"].keys())
    zone_weights = list(tmpl["zone_distribution"].values())
    zones_per_step = max(1, int(map_width * map_height * 0.15))
    for step in range(2, min(steps, 5)):
        for _ in range(zones_per_step):
            x = random.randint(0, map_width - 1)
            y = random.randint(0, map_height - 1)
            zone_type = random.choices(zone_types, weights=zone_weights, k=1)[0]
            if tmpl["zone_distribution"].get(zone_type, 0) > 0:
                zones.append({"type": zone_type, "x": x, "y": y})
        generation_steps.append({"step": step, "name": f"Zone Layer {step - 1}", "description": f"Placing {len(zones)} zones", "terrain": terrain.model_dump(), "zones": list(zones), "prefabs": []})
    prefab_types = list(tmpl["prefab_weights"].keys())
    prefab_weights_list = list(tmpl["prefab_weights"].values())
    prefabs = []
    if zones:
        for _ in range(int(len(zones) * tmpl["prefab_density"])):
            z = random.choice(zones)
            ptype = random.choices(prefab_types, weights=prefab_weights_list, k=1)[0]
            prefabs.append({"type": ptype, "x": z["x"], "y": z["y"]})
    generation_steps.append({"step": min(steps, 5), "name": "Structure Placement", "description": f"Placing {len(prefabs)} structures", "terrain": terrain.model_dump(), "zones": zones, "prefabs": prefabs})
    return {"template": template, "map_size": f"{map_width}x{map_height}", "steps": generation_steps, "total_zones": len(zones), "total_prefabs": len(prefabs)}

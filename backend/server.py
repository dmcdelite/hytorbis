from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone
import random
import json

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app
app = FastAPI(title="Hytale World Builder API")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# ==================== MODELS ====================

class TerrainSettings(BaseModel):
    height_scale: float = Field(default=1.0, ge=0.1, le=3.0)
    cave_density: float = Field(default=0.5, ge=0.0, le=1.0)
    river_frequency: float = Field(default=0.3, ge=0.0, le=1.0)
    mountain_scale: float = Field(default=0.5, ge=0.0, le=1.0)
    ocean_level: float = Field(default=0.3, ge=0.0, le=1.0)

class BiomeConfig(BaseModel):
    type: str  # forest, desert, arctic, swamp, plains, etc.
    density: float = Field(default=0.5, ge=0.0, le=1.0)
    variation: float = Field(default=0.3, ge=0.0, le=1.0)

class ZoneConfig(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str  # emerald_grove, borea, desert, arctic, corrupted
    x: int
    y: int
    width: int = 1
    height: int = 1
    biomes: List[BiomeConfig] = []
    difficulty: int = Field(default=1, ge=1, le=10)

class PrefabPlacement(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str  # dungeon, village, ruins, tower, cave_entrance, portal
    x: int
    y: int
    rotation: int = 0
    scale: float = 1.0
    zone_id: Optional[str] = None

class WorldConfig(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    seed: str
    description: Optional[str] = ""
    terrain: TerrainSettings = Field(default_factory=TerrainSettings)
    zones: List[ZoneConfig] = []
    prefabs: List[PrefabPlacement] = []
    map_width: int = Field(default=64, ge=5, le=512)
    map_height: int = Field(default=64, ge=5, le=512)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    ai_provider: Optional[str] = "openai"
    thumbnail: Optional[str] = None

class WorldCreate(BaseModel):
    name: str
    seed: Optional[str] = None
    description: Optional[str] = ""
    map_width: int = Field(default=64, ge=5, le=512)
    map_height: int = Field(default=64, ge=5, le=512)

class WorldUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    terrain: Optional[TerrainSettings] = None
    zones: Optional[List[ZoneConfig]] = None
    prefabs: Optional[List[PrefabPlacement]] = None
    map_width: Optional[int] = Field(default=None, ge=5, le=512)
    map_height: Optional[int] = Field(default=None, ge=5, le=512)
    ai_provider: Optional[str] = None

class AIMessage(BaseModel):
    role: str  # user or assistant
    content: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class AIChatRequest(BaseModel):
    world_id: str
    message: str
    provider: str = "openai"  # openai, anthropic, gemini

class AIChatResponse(BaseModel):
    response: str
    suggestions: Optional[Dict[str, Any]] = None

class SeedGenerateRequest(BaseModel):
    style: Optional[str] = None  # adventure, peaceful, challenging, exploration

# ==================== UTILITIES ====================

def generate_seed(style: Optional[str] = None) -> str:
    """Generate a unique world seed"""
    adjectives = ["Ancient", "Mystic", "Frozen", "Burning", "Hidden", "Lost", "Sacred", "Dark", "Golden", "Crystal"]
    nouns = ["Valley", "Peak", "Grove", "Depths", "Realm", "Lands", "Kingdom", "Forest", "Desert", "Tundra"]
    
    if style:
        style_words = {
            "adventure": ["Epic", "Quest", "Hero", "Legend"],
            "peaceful": ["Tranquil", "Serene", "Calm", "Gentle"],
            "challenging": ["Brutal", "Harsh", "Deadly", "Perilous"],
            "exploration": ["Vast", "Unknown", "Endless", "Mysterious"]
        }
        if style in style_words:
            adjectives = style_words[style] + adjectives[:3]
    
    seed = f"{random.choice(adjectives)}{random.choice(nouns)}{random.randint(1000, 9999)}"
    return seed

def get_zone_color(zone_type: str) -> str:
    """Return color hex for zone type"""
    colors = {
        "emerald_grove": "#10B981",
        "borea": "#06B6D4",
        "desert": "#F59E0B",
        "arctic": "#E2E8F0",
        "corrupted": "#8B5CF6"
    }
    return colors.get(zone_type, "#6B7280")

def get_prefab_icon(prefab_type: str) -> str:
    """Return icon name for prefab type"""
    icons = {
        "dungeon": "castle",
        "village": "home",
        "ruins": "landmark",
        "tower": "tower-control",
        "cave_entrance": "mountain",
        "portal": "sparkles"
    }
    return icons.get(prefab_type, "map-pin")

# ==================== AI INTEGRATION ====================

async def get_ai_response(message: str, world_config: dict, provider: str) -> dict:
    """Get AI response for world building suggestions"""
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    
    api_key = os.environ.get('EMERGENT_LLM_KEY')
    if not api_key:
        raise HTTPException(status_code=500, detail="AI service not configured")
    
    # Map provider to model
    provider_models = {
        "openai": ("openai", "gpt-5.2"),
        "anthropic": ("anthropic", "claude-sonnet-4-5-20250929"),
        "gemini": ("gemini", "gemini-3-flash-preview")
    }
    
    if provider not in provider_models:
        provider = "openai"
    
    llm_provider, model = provider_models[provider]
    
    system_message = """You are a Hytale World Builder AI assistant. You help users create amazing game worlds by suggesting:
- Zone placements and configurations (Emerald Grove, Borea, Desert, Arctic, Corrupted)
- Biome settings and mixing
- Prefab placements (dungeons, villages, ruins, towers, caves, portals)
- Terrain settings (height, caves, rivers, mountains)
- World themes and narratives

When making suggestions, provide specific values and coordinates when possible.
Format suggestions as actionable items the user can apply to their world.
Keep responses concise but helpful. If suggesting world changes, format them as JSON when appropriate."""

    # Include current world state in context
    world_context = f"""
Current World State:
- Name: {world_config.get('name', 'Unnamed')}
- Seed: {world_config.get('seed', 'None')}
- Map Size: {world_config.get('map_width', 20)}x{world_config.get('map_height', 20)}
- Zones: {len(world_config.get('zones', []))}
- Prefabs: {len(world_config.get('prefabs', []))}
- Terrain: {json.dumps(world_config.get('terrain', {}))}
"""
    
    chat = LlmChat(
        api_key=api_key,
        session_id=f"world-{world_config.get('id', 'new')}",
        system_message=system_message
    ).with_model(llm_provider, model)
    
    full_message = f"{world_context}\n\nUser Request: {message}"
    user_message = UserMessage(text=full_message)
    
    response = await chat.send_message(user_message)
    
    # Try to extract any JSON suggestions from the response
    suggestions = None
    try:
        if "```json" in response:
            json_start = response.find("```json") + 7
            json_end = response.find("```", json_start)
            if json_end > json_start:
                json_str = response[json_start:json_end].strip()
                suggestions = json.loads(json_str)
    except:
        pass
    
    return {
        "response": response,
        "suggestions": suggestions
    }

# ==================== ROUTES ====================

@api_router.get("/")
async def root():
    return {"message": "Hytale World Builder API", "version": "1.0.0"}

@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}

# Seed Generation
@api_router.post("/seed/generate")
async def generate_world_seed(request: SeedGenerateRequest):
    seed = generate_seed(request.style)
    return {"seed": seed, "style": request.style}

@api_router.get("/seed/random")
async def get_random_seed():
    return {"seed": generate_seed()}

# World CRUD
@api_router.post("/worlds", response_model=WorldConfig)
async def create_world(world: WorldCreate):
    seed = world.seed or generate_seed()
    
    world_config = WorldConfig(
        name=world.name,
        seed=seed,
        description=world.description,
        map_width=world.map_width,
        map_height=world.map_height
    )
    
    doc = world_config.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['updated_at'] = doc['updated_at'].isoformat()
    
    await db.worlds.insert_one(doc)
    return world_config

@api_router.get("/worlds", response_model=List[WorldConfig])
async def list_worlds():
    worlds = await db.worlds.find({}, {"_id": 0}).to_list(100)
    for world in worlds:
        if isinstance(world.get('created_at'), str):
            world['created_at'] = datetime.fromisoformat(world['created_at'])
        if isinstance(world.get('updated_at'), str):
            world['updated_at'] = datetime.fromisoformat(world['updated_at'])
    return worlds

@api_router.get("/worlds/{world_id}", response_model=WorldConfig)
async def get_world(world_id: str):
    world = await db.worlds.find_one({"id": world_id}, {"_id": 0})
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    if isinstance(world.get('created_at'), str):
        world['created_at'] = datetime.fromisoformat(world['created_at'])
    if isinstance(world.get('updated_at'), str):
        world['updated_at'] = datetime.fromisoformat(world['updated_at'])
    return world

@api_router.put("/worlds/{world_id}", response_model=WorldConfig)
async def update_world(world_id: str, update: WorldUpdate):
    world = await db.worlds.find_one({"id": world_id}, {"_id": 0})
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    
    update_data = update.model_dump(exclude_unset=True)
    update_data['updated_at'] = datetime.now(timezone.utc).isoformat()
    
    # Handle nested models
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

@api_router.delete("/worlds/{world_id}")
async def delete_world(world_id: str):
    result = await db.worlds.delete_one({"id": world_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="World not found")
    return {"message": "World deleted", "id": world_id}

# Zone Management
@api_router.post("/worlds/{world_id}/zones", response_model=WorldConfig)
async def add_zone(world_id: str, zone: ZoneConfig):
    world = await db.worlds.find_one({"id": world_id}, {"_id": 0})
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    
    zones = world.get('zones', [])
    zone_dict = zone.model_dump()
    zones.append(zone_dict)
    
    await db.worlds.update_one(
        {"id": world_id}, 
        {"$set": {"zones": zones, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return await get_world(world_id)

@api_router.delete("/worlds/{world_id}/zones/{zone_id}")
async def remove_zone(world_id: str, zone_id: str):
    world = await db.worlds.find_one({"id": world_id}, {"_id": 0})
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    
    zones = [z for z in world.get('zones', []) if z.get('id') != zone_id]
    
    await db.worlds.update_one(
        {"id": world_id},
        {"$set": {"zones": zones, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"message": "Zone removed", "zone_id": zone_id}

# Prefab Management
@api_router.post("/worlds/{world_id}/prefabs", response_model=WorldConfig)
async def add_prefab(world_id: str, prefab: PrefabPlacement):
    world = await db.worlds.find_one({"id": world_id}, {"_id": 0})
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    
    prefabs = world.get('prefabs', [])
    prefab_dict = prefab.model_dump()
    prefabs.append(prefab_dict)
    
    await db.worlds.update_one(
        {"id": world_id},
        {"$set": {"prefabs": prefabs, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return await get_world(world_id)

@api_router.delete("/worlds/{world_id}/prefabs/{prefab_id}")
async def remove_prefab(world_id: str, prefab_id: str):
    world = await db.worlds.find_one({"id": world_id}, {"_id": 0})
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    
    prefabs = [p for p in world.get('prefabs', []) if p.get('id') != prefab_id]
    
    await db.worlds.update_one(
        {"id": world_id},
        {"$set": {"prefabs": prefabs, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"message": "Prefab removed", "prefab_id": prefab_id}

# AI Chat
@api_router.post("/ai/chat", response_model=AIChatResponse)
async def ai_chat(request: AIChatRequest):
    world = await db.worlds.find_one({"id": request.world_id}, {"_id": 0})
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    
    result = await get_ai_response(request.message, world, request.provider)
    return AIChatResponse(**result)

# Export
@api_router.get("/worlds/{world_id}/export/json")
async def export_world_json(world_id: str):
    world = await db.worlds.find_one({"id": world_id}, {"_id": 0})
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    
    # Convert datetime objects to strings for JSON export
    if isinstance(world.get('created_at'), datetime):
        world['created_at'] = world['created_at'].isoformat()
    if isinstance(world.get('updated_at'), datetime):
        world['updated_at'] = world['updated_at'].isoformat()
    
    return {
        "format": "json",
        "version": "1.0",
        "world": world
    }

@api_router.get("/worlds/{world_id}/export/hytale")
async def export_world_hytale(world_id: str):
    """Export in Hytale-compatible format"""
    world = await db.worlds.find_one({"id": world_id}, {"_id": 0})
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    
    # Convert to Hytale world structure format
    hytale_config = {
        "worldgen": {
            "seed": world.get('seed', ''),
            "name": world.get('name', 'Unnamed World'),
            "size": {
                "x": world.get('map_width', 20) * 256,
                "z": world.get('map_height', 20) * 256
            },
            "terrain": {
                "heightScale": world.get('terrain', {}).get('height_scale', 1.0),
                "caveDensity": world.get('terrain', {}).get('cave_density', 0.5),
                "riverFrequency": world.get('terrain', {}).get('river_frequency', 0.3),
                "mountainScale": world.get('terrain', {}).get('mountain_scale', 0.5),
                "oceanLevel": world.get('terrain', {}).get('ocean_level', 0.3)
            }
        },
        "zones": [
            {
                "type": z.get('type'),
                "bounds": {
                    "x": z.get('x', 0) * 256,
                    "z": z.get('y', 0) * 256,
                    "width": z.get('width', 1) * 256,
                    "height": z.get('height', 1) * 256
                },
                "difficulty": z.get('difficulty', 1),
                "biomes": z.get('biomes', [])
            }
            for z in world.get('zones', [])
        ],
        "structures": [
            {
                "type": p.get('type'),
                "position": {
                    "x": p.get('x', 0) * 256 + 128,
                    "z": p.get('y', 0) * 256 + 128
                },
                "rotation": p.get('rotation', 0),
                "scale": p.get('scale', 1.0)
            }
            for p in world.get('prefabs', [])
        ],
        "metadata": {
            "generator": "Hytale World Builder",
            "version": "1.0.0",
            "created": world.get('created_at', ''),
            "description": world.get('description', '')
        }
    }
    
    return {
        "format": "hytale",
        "version": "1.0",
        "config": hytale_config
    }

# Reference Data
@api_router.get("/reference/zones")
async def get_zone_types():
    return {
        "zones": [
            {"id": "emerald_grove", "name": "Emerald Grove", "color": "#10B981", "description": "Lush forests and green valleys"},
            {"id": "borea", "name": "Borea", "color": "#06B6D4", "description": "Icy tundra and frozen peaks"},
            {"id": "desert", "name": "Desert", "color": "#F59E0B", "description": "Scorching sands and ancient ruins"},
            {"id": "arctic", "name": "Arctic", "color": "#E2E8F0", "description": "Snow-covered landscapes"},
            {"id": "corrupted", "name": "Corrupted", "color": "#8B5CF6", "description": "Dark magic-infused lands"}
        ]
    }

@api_router.get("/reference/prefabs")
async def get_prefab_types():
    return {
        "prefabs": [
            {"id": "dungeon", "name": "Dungeon", "icon": "castle", "description": "Underground challenge areas"},
            {"id": "village", "name": "Village", "icon": "home", "description": "NPC settlements"},
            {"id": "ruins", "name": "Ruins", "icon": "landmark", "description": "Ancient structures"},
            {"id": "tower", "name": "Tower", "icon": "building", "description": "Vertical structures"},
            {"id": "cave_entrance", "name": "Cave Entrance", "icon": "mountain", "description": "Underground access points"},
            {"id": "portal", "name": "Portal", "icon": "sparkles", "description": "Zone transition points"}
        ]
    }

@api_router.get("/reference/biomes")
async def get_biome_types():
    return {
        "biomes": [
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
        ]
    }

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()

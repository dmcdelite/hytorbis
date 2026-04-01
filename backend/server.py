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

class WorldFromTemplate(BaseModel):
    name: str
    template: str  # adventure, peaceful, challenge, exploration, dungeon_crawler
    map_width: int = Field(default=64, ge=5, le=512)
    map_height: int = Field(default=64, ge=5, le=512)

class WorldImport(BaseModel):
    config: Dict[str, Any]
    name: Optional[str] = None

class AIAutoGenerateRequest(BaseModel):
    world_id: str
    prompt: str
    provider: str = "openai"

class CollabSession(BaseModel):
    world_id: str
    user_id: str
    action: str  # join, leave, update
    data: Optional[Dict[str, Any]] = None

# ==================== WORLD TEMPLATES ====================

WORLD_TEMPLATES = {
    "adventure": {
        "name": "Adventure World",
        "description": "A balanced world with diverse zones and structures for exploration",
        "terrain": {"height_scale": 1.2, "cave_density": 0.5, "river_frequency": 0.4, "mountain_scale": 0.6, "ocean_level": 0.25},
        "zone_distribution": {"emerald_grove": 0.4, "desert": 0.2, "borea": 0.2, "arctic": 0.1, "corrupted": 0.1},
        "prefab_density": 0.08,
        "prefab_weights": {"dungeon": 0.25, "village": 0.25, "ruins": 0.2, "tower": 0.15, "cave_entrance": 0.1, "portal": 0.05},
        "difficulty_range": (2, 7)
    },
    "peaceful": {
        "name": "Peaceful World",
        "description": "A calm world focused on building and exploration with minimal danger",
        "terrain": {"height_scale": 0.8, "cave_density": 0.3, "river_frequency": 0.5, "mountain_scale": 0.4, "ocean_level": 0.35},
        "zone_distribution": {"emerald_grove": 0.6, "desert": 0.15, "borea": 0.15, "arctic": 0.1, "corrupted": 0.0},
        "prefab_density": 0.05,
        "prefab_weights": {"dungeon": 0.1, "village": 0.4, "ruins": 0.2, "tower": 0.15, "cave_entrance": 0.1, "portal": 0.05},
        "difficulty_range": (1, 3)
    },
    "challenge": {
        "name": "Challenge World",
        "description": "A difficult world with harsh terrain and dangerous areas",
        "terrain": {"height_scale": 1.5, "cave_density": 0.7, "river_frequency": 0.2, "mountain_scale": 0.8, "ocean_level": 0.2},
        "zone_distribution": {"emerald_grove": 0.2, "desert": 0.2, "borea": 0.2, "arctic": 0.2, "corrupted": 0.2},
        "prefab_density": 0.12,
        "prefab_weights": {"dungeon": 0.35, "village": 0.1, "ruins": 0.2, "tower": 0.2, "cave_entrance": 0.1, "portal": 0.05},
        "difficulty_range": (5, 10)
    },
    "exploration": {
        "name": "Exploration World",
        "description": "A vast world with many points of interest to discover",
        "terrain": {"height_scale": 1.3, "cave_density": 0.6, "river_frequency": 0.45, "mountain_scale": 0.7, "ocean_level": 0.3},
        "zone_distribution": {"emerald_grove": 0.35, "desert": 0.2, "borea": 0.2, "arctic": 0.15, "corrupted": 0.1},
        "prefab_density": 0.1,
        "prefab_weights": {"dungeon": 0.2, "village": 0.15, "ruins": 0.25, "tower": 0.15, "cave_entrance": 0.15, "portal": 0.1},
        "difficulty_range": (3, 8)
    },
    "dungeon_crawler": {
        "name": "Dungeon Crawler",
        "description": "A world focused on underground exploration and combat",
        "terrain": {"height_scale": 1.0, "cave_density": 0.9, "river_frequency": 0.15, "mountain_scale": 0.5, "ocean_level": 0.15},
        "zone_distribution": {"emerald_grove": 0.15, "desert": 0.15, "borea": 0.15, "arctic": 0.15, "corrupted": 0.4},
        "prefab_density": 0.15,
        "prefab_weights": {"dungeon": 0.45, "village": 0.05, "ruins": 0.2, "tower": 0.1, "cave_entrance": 0.15, "portal": 0.05},
        "difficulty_range": (4, 10)
    }
}

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

def generate_world_from_template(template_id: str, map_width: int, map_height: int) -> tuple:
    """Generate zones and prefabs based on a template"""
    template = WORLD_TEMPLATES.get(template_id)
    if not template:
        return [], [], TerrainSettings()
    
    zones = []
    prefabs = []
    zone_types = list(template["zone_distribution"].keys())
    zone_weights = list(template["zone_distribution"].values())
    prefab_types = list(template["prefab_weights"].keys())
    prefab_weights = list(template["prefab_weights"].values())
    
    # Generate zones - cover about 60% of the map
    total_cells = map_width * map_height
    target_zones = int(total_cells * 0.6)
    
    # Use a noise-like pattern for natural zone distribution
    placed = set()
    zone_seeds = []
    
    # Place zone seeds
    num_seeds = max(5, int(total_cells / 100))
    for _ in range(num_seeds):
        x = random.randint(0, map_width - 1)
        y = random.randint(0, map_height - 1)
        zone_type = random.choices(zone_types, weights=zone_weights, k=1)[0]
        if zone_weights[zone_types.index(zone_type)] > 0:
            zone_seeds.append((x, y, zone_type))
    
    # Grow zones from seeds
    for seed_x, seed_y, zone_type in zone_seeds:
        radius = random.randint(2, max(3, min(map_width, map_height) // 8))
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                if dx*dx + dy*dy <= radius*radius:
                    nx, ny = seed_x + dx, seed_y + dy
                    if 0 <= nx < map_width and 0 <= ny < map_height:
                        key = (nx, ny)
                        if key not in placed and len(zones) < target_zones:
                            placed.add(key)
                            difficulty = random.randint(template["difficulty_range"][0], template["difficulty_range"][1])
                            zones.append(ZoneConfig(
                                id=f"zone-{uuid.uuid4()}",
                                type=zone_type,
                                x=nx,
                                y=ny,
                                difficulty=difficulty
                            ))
    
    # Generate prefabs in zones
    target_prefabs = int(len(zones) * template["prefab_density"])
    zone_positions = [(z.x, z.y) for z in zones]
    
    if zone_positions:
        for _ in range(target_prefabs):
            pos = random.choice(zone_positions)
            prefab_type = random.choices(prefab_types, weights=prefab_weights, k=1)[0]
            # Check no prefab at this position
            if not any(p.x == pos[0] and p.y == pos[1] for p in prefabs):
                prefabs.append(PrefabPlacement(
                    id=f"prefab-{uuid.uuid4()}",
                    type=prefab_type,
                    x=pos[0],
                    y=pos[1],
                    rotation=random.choice([0, 90, 180, 270]),
                    scale=round(random.uniform(0.8, 1.2), 1)
                ))
    
    terrain = TerrainSettings(**template["terrain"])
    return zones, prefabs, terrain

async def ai_auto_generate(prompt: str, world_config: dict, provider: str) -> dict:
    """Use AI to generate world content based on natural language prompt"""
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    
    api_key = os.environ.get('EMERGENT_LLM_KEY')
    if not api_key:
        raise HTTPException(status_code=500, detail="AI service not configured")
    
    provider_models = {
        "openai": ("openai", "gpt-5.2"),
        "anthropic": ("anthropic", "claude-sonnet-4-5-20250929"),
        "gemini": ("gemini", "gemini-3-flash-preview")
    }
    
    if provider not in provider_models:
        provider = "openai"
    
    llm_provider, model = provider_models[provider]
    
    system_message = """You are a Hytale World Generator AI. Generate world configurations based on user prompts.

ZONE TYPES: emerald_grove, borea, desert, arctic, corrupted
PREFAB TYPES: dungeon, village, ruins, tower, cave_entrance, portal

You MUST respond with valid JSON only, no other text. Format:
{
  "terrain": {"height_scale": 1.0, "cave_density": 0.5, "river_frequency": 0.3, "mountain_scale": 0.5, "ocean_level": 0.3},
  "zones": [{"type": "emerald_grove", "x": 5, "y": 5, "difficulty": 3}],
  "prefabs": [{"type": "dungeon", "x": 10, "y": 10, "rotation": 0, "scale": 1.0}],
  "description": "Brief description of the generated world"
}

Generate zones covering 40-70% of the map area. Place prefabs strategically within zones.
Use coordinates between 0 and map_width/map_height - 1.
Create interesting patterns - clusters, gradients, themed regions based on the prompt."""

    world_context = f"""
Map Size: {world_config.get('map_width', 64)}x{world_config.get('map_height', 64)}
Current zones: {len(world_config.get('zones', []))}
Current prefabs: {len(world_config.get('prefabs', []))}

USER PROMPT: {prompt}

Generate world content that matches this prompt. Return ONLY valid JSON."""

    chat = LlmChat(
        api_key=api_key,
        session_id=f"autogen-{world_config.get('id', 'new')}",
        system_message=system_message
    ).with_model(llm_provider, model)
    
    user_message = UserMessage(text=world_context)
    response = await chat.send_message(user_message)
    
    # Parse JSON from response
    try:
        # Try to extract JSON from response
        json_str = response.strip()
        if "```json" in json_str:
            json_str = json_str.split("```json")[1].split("```")[0]
        elif "```" in json_str:
            json_str = json_str.split("```")[1].split("```")[0]
        
        generated = json.loads(json_str)
        
        # Validate and convert to proper models
        zones = []
        for z in generated.get("zones", []):
            zones.append({
                "id": f"zone-{uuid.uuid4()}",
                "type": z.get("type", "emerald_grove"),
                "x": max(0, min(z.get("x", 0), world_config.get("map_width", 64) - 1)),
                "y": max(0, min(z.get("y", 0), world_config.get("map_height", 64) - 1)),
                "difficulty": max(1, min(z.get("difficulty", 1), 10)),
                "biomes": []
            })
        
        prefabs = []
        for p in generated.get("prefabs", []):
            prefabs.append({
                "id": f"prefab-{uuid.uuid4()}",
                "type": p.get("type", "dungeon"),
                "x": max(0, min(p.get("x", 0), world_config.get("map_width", 64) - 1)),
                "y": max(0, min(p.get("y", 0), world_config.get("map_height", 64) - 1)),
                "rotation": p.get("rotation", 0),
                "scale": max(0.5, min(p.get("scale", 1.0), 2.0))
            })
        
        terrain = generated.get("terrain", {})
        description = generated.get("description", "AI-generated world")
        
        return {
            "zones": zones,
            "prefabs": prefabs,
            "terrain": terrain,
            "description": description
        }
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="AI returned invalid JSON. Please try again.")

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

@api_router.get("/worlds/{world_id}/export/prefab")
async def export_world_prefab(world_id: str):
    """Export prefabs in .prefab.json format for Hytale modding"""
    world = await db.worlds.find_one({"id": world_id}, {"_id": 0})
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    
    # Generate prefab.json format - Hytale prefab structure
    prefab_export = {
        "formatVersion": 1,
        "prefabType": "world_prefabs",
        "metadata": {
            "name": world.get('name', 'Unnamed World'),
            "author": "Hytale World Builder",
            "version": "1.0.0",
            "seed": world.get('seed', ''),
            "created": world.get('created_at', ''),
            "description": world.get('description', '')
        },
        "worldSettings": {
            "dimensions": {
                "width": world.get('map_width', 64) * 256,
                "height": 256,
                "depth": world.get('map_height', 64) * 256
            },
            "terrain": {
                "heightScale": world.get('terrain', {}).get('height_scale', 1.0),
                "caveDensity": world.get('terrain', {}).get('cave_density', 0.5),
                "riverFrequency": world.get('terrain', {}).get('river_frequency', 0.3),
                "mountainScale": world.get('terrain', {}).get('mountain_scale', 0.5),
                "oceanLevel": world.get('terrain', {}).get('ocean_level', 0.3)
            }
        },
        "prefabs": [
            {
                "id": p.get('id', ''),
                "type": p.get('type', 'dungeon'),
                "name": f"{p.get('type', 'structure').replace('_', ' ').title()} at ({p.get('x', 0)}, {p.get('y', 0)})",
                "position": {
                    "x": p.get('x', 0) * 256 + 128,
                    "y": 64,  # Ground level
                    "z": p.get('y', 0) * 256 + 128
                },
                "rotation": {
                    "y": p.get('rotation', 0)
                },
                "scale": {
                    "x": p.get('scale', 1.0),
                    "y": p.get('scale', 1.0),
                    "z": p.get('scale', 1.0)
                },
                "properties": {
                    "spawnable": True,
                    "destructible": p.get('type') not in ['portal'],
                    "lootTable": f"loot/{p.get('type', 'generic')}"
                }
            }
            for p in world.get('prefabs', [])
        ],
        "zoneConfigs": [
            {
                "id": z.get('id', ''),
                "zoneType": z.get('type', 'emerald_grove'),
                "bounds": {
                    "minX": z.get('x', 0) * 256,
                    "minZ": z.get('y', 0) * 256,
                    "maxX": (z.get('x', 0) + z.get('width', 1)) * 256,
                    "maxZ": (z.get('y', 0) + z.get('height', 1)) * 256
                },
                "difficulty": z.get('difficulty', 1),
                "biomes": [
                    {
                        "type": b.get('type', 'plains'),
                        "weight": b.get('density', 0.5),
                        "variation": b.get('variation', 0.3)
                    }
                    for b in z.get('biomes', [])
                ]
            }
            for z in world.get('zones', [])
        ]
    }
    
    return {
        "format": "prefab.json",
        "version": "1.0",
        "filename": f"{world.get('name', 'world').replace(' ', '_').lower()}.prefab.json",
        "data": prefab_export
    }

@api_router.get("/worlds/{world_id}/export/jar")
async def export_world_jar(world_id: str):
    """Export world as a JAR-compatible mod package structure"""
    import base64
    import io
    import zipfile
    
    world = await db.worlds.find_one({"id": world_id}, {"_id": 0})
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    
    world_name = world.get('name', 'HytaleWorld').replace(' ', '')
    world_name_lower = world_name.lower()
    
    # Create JAR structure in memory
    jar_buffer = io.BytesIO()
    
    with zipfile.ZipFile(jar_buffer, 'w', zipfile.ZIP_DEFLATED) as jar:
        # META-INF/MANIFEST.MF
        manifest = f"""Manifest-Version: 1.0
Created-By: Hytale World Builder
Main-Class: com.hytale.worldbuilder.{world_name}
Implementation-Title: {world.get('name', 'Hytale World')}
Implementation-Version: 1.0.0
"""
        jar.writestr("META-INF/MANIFEST.MF", manifest)
        
        # mod.json - Hytale mod descriptor
        mod_json = {
            "id": world_name_lower,
            "name": world.get('name', 'Hytale World'),
            "version": "1.0.0",
            "description": world.get('description', 'Generated by Hytale World Builder'),
            "authors": ["Hytale World Builder"],
            "dependencies": {
                "hytale": ">=1.0.0"
            },
            "entrypoints": {
                "main": f"com.hytale.worldbuilder.{world_name}"
            },
            "worldgen": {
                "seed": world.get('seed', ''),
                "type": "custom"
            }
        }
        jar.writestr("mod.json", json.dumps(mod_json, indent=2))
        
        # worldgen/world.json - World generation config
        worldgen_config = {
            "seed": world.get('seed', ''),
            "dimensions": {
                "width": world.get('map_width', 64),
                "height": world.get('map_height', 64)
            },
            "terrain": world.get('terrain', {}),
            "zones": world.get('zones', []),
            "structures": world.get('prefabs', [])
        }
        jar.writestr(f"worldgen/{world_name_lower}/world.json", json.dumps(worldgen_config, indent=2))
        
        # worldgen/terrain.json
        terrain_config = {
            "heightScale": world.get('terrain', {}).get('height_scale', 1.0),
            "caveDensity": world.get('terrain', {}).get('cave_density', 0.5),
            "riverFrequency": world.get('terrain', {}).get('river_frequency', 0.3),
            "mountainScale": world.get('terrain', {}).get('mountain_scale', 0.5),
            "oceanLevel": world.get('terrain', {}).get('ocean_level', 0.3),
            "biomeBlending": True,
            "structureSpacing": 256
        }
        jar.writestr(f"worldgen/{world_name_lower}/terrain.json", json.dumps(terrain_config, indent=2))
        
        # worldgen/zones/*.json - Individual zone configs
        for i, zone in enumerate(world.get('zones', [])[:100]):  # Limit for performance
            zone_config = {
                "type": zone.get('type', 'emerald_grove'),
                "position": {"x": zone.get('x', 0), "z": zone.get('y', 0)},
                "difficulty": zone.get('difficulty', 1),
                "biomes": zone.get('biomes', [])
            }
            jar.writestr(f"worldgen/{world_name_lower}/zones/zone_{i}.json", json.dumps(zone_config, indent=2))
        
        # worldgen/structures/*.json - Structure placements
        for i, prefab in enumerate(world.get('prefabs', [])[:50]):  # Limit for performance
            structure_config = {
                "type": prefab.get('type', 'dungeon'),
                "position": {
                    "x": prefab.get('x', 0) * 256 + 128,
                    "y": 64,
                    "z": prefab.get('y', 0) * 256 + 128
                },
                "rotation": prefab.get('rotation', 0),
                "scale": prefab.get('scale', 1.0)
            }
            jar.writestr(f"worldgen/{world_name_lower}/structures/structure_{i}.json", json.dumps(structure_config, indent=2))
        
        # README.txt
        readme = f"""# {world.get('name', 'Hytale World')}

Generated by Hytale World Builder

## World Info
- Seed: {world.get('seed', 'N/A')}
- Size: {world.get('map_width', 64)}x{world.get('map_height', 64)} chunks
- Zones: {len(world.get('zones', []))}
- Structures: {len(world.get('prefabs', []))}

## Installation
1. Place this .jar file in your Hytale mods folder
2. Launch Hytale
3. Create a new world and select this mod's world generator

## Description
{world.get('description', 'A custom world generated with Hytale World Builder.')}
"""
        jar.writestr("README.txt", readme)
    
    # Get the JAR bytes and encode to base64
    jar_buffer.seek(0)
    jar_bytes = jar_buffer.getvalue()
    jar_base64 = base64.b64encode(jar_bytes).decode('utf-8')
    
    return {
        "format": "jar",
        "version": "1.0",
        "filename": f"{world_name_lower}_worldgen.jar",
        "size_bytes": len(jar_bytes),
        "data_base64": jar_base64,
        "contents": [
            "META-INF/MANIFEST.MF",
            "mod.json",
            f"worldgen/{world_name_lower}/world.json",
            f"worldgen/{world_name_lower}/terrain.json",
            f"worldgen/{world_name_lower}/zones/*.json",
            f"worldgen/{world_name_lower}/structures/*.json",
            "README.txt"
        ]
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

# ==================== P2: TEMPLATES ====================

@api_router.get("/templates")
async def get_templates():
    """Get available world templates"""
    return {
        "templates": [
            {
                "id": tid,
                "name": t["name"],
                "description": t["description"],
                "terrain_preview": t["terrain"],
                "difficulty_range": t["difficulty_range"]
            }
            for tid, t in WORLD_TEMPLATES.items()
        ]
    }

@api_router.post("/worlds/from-template", response_model=WorldConfig)
async def create_world_from_template(request: WorldFromTemplate):
    """Create a world using a template"""
    if request.template not in WORLD_TEMPLATES:
        raise HTTPException(status_code=400, detail=f"Unknown template: {request.template}")
    
    template = WORLD_TEMPLATES[request.template]
    seed = generate_seed(request.template)
    
    zones, prefabs, terrain = generate_world_from_template(
        request.template, 
        request.map_width, 
        request.map_height
    )
    
    world_config = WorldConfig(
        name=request.name,
        seed=seed,
        description=template["description"],
        terrain=terrain,
        zones=zones,
        prefabs=prefabs,
        map_width=request.map_width,
        map_height=request.map_height
    )
    
    doc = world_config.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['updated_at'] = doc['updated_at'].isoformat()
    
    # Convert zone/prefab models to dicts
    doc['zones'] = [z.model_dump() if hasattr(z, 'model_dump') else z for z in doc['zones']]
    doc['prefabs'] = [p.model_dump() if hasattr(p, 'model_dump') else p for p in doc['prefabs']]
    doc['terrain'] = terrain.model_dump() if hasattr(terrain, 'model_dump') else doc['terrain']
    
    await db.worlds.insert_one(doc)
    return world_config

# ==================== P2: IMPORT ====================

@api_router.post("/worlds/import", response_model=WorldConfig)
async def import_world(request: WorldImport):
    """Import a world from JSON configuration"""
    config = request.config
    
    # Extract or generate required fields
    world_name = request.name or config.get("name") or config.get("worldgen", {}).get("name") or "Imported World"
    seed = config.get("seed") or config.get("worldgen", {}).get("seed") or generate_seed()
    
    # Handle Hytale format
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
        
        zones = []
        for z in config.get("zones", []):
            zones.append(ZoneConfig(
                type=z.get("type", "emerald_grove"),
                x=z.get("bounds", {}).get("x", 0) // 256,
                y=z.get("bounds", {}).get("z", 0) // 256,
                difficulty=z.get("difficulty", 1)
            ))
        
        prefabs = []
        for s in config.get("structures", []):
            prefabs.append(PrefabPlacement(
                type=s.get("type", "dungeon"),
                x=s.get("position", {}).get("x", 0) // 256,
                y=s.get("position", {}).get("z", 0) // 256,
                rotation=s.get("rotation", 0),
                scale=s.get("scale", 1.0)
            ))
    else:
        # Handle our JSON format
        map_width = min(512, max(5, config.get("map_width", 64)))
        map_height = min(512, max(5, config.get("map_height", 64)))
        
        terrain_data = config.get("terrain", {})
        terrain = TerrainSettings(**terrain_data) if terrain_data else TerrainSettings()
        
        zones = [ZoneConfig(**z) for z in config.get("zones", [])]
        prefabs = [PrefabPlacement(**p) for p in config.get("prefabs", [])]
    
    world_config = WorldConfig(
        name=world_name,
        seed=seed,
        description=config.get("description", "Imported world"),
        terrain=terrain,
        zones=zones,
        prefabs=prefabs,
        map_width=map_width,
        map_height=map_height
    )
    
    doc = world_config.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['updated_at'] = doc['updated_at'].isoformat()
    doc['zones'] = [z.model_dump() if hasattr(z, 'model_dump') else z for z in doc['zones']]
    doc['prefabs'] = [p.model_dump() if hasattr(p, 'model_dump') else p for p in doc['prefabs']]
    doc['terrain'] = terrain.model_dump() if hasattr(terrain, 'model_dump') else doc['terrain']
    
    await db.worlds.insert_one(doc)
    return world_config

# ==================== P2: AI AUTO-GENERATE ====================

@api_router.post("/ai/auto-generate")
async def ai_auto_generate_world(request: AIAutoGenerateRequest):
    """Use AI to auto-populate a world based on a prompt"""
    world = await db.worlds.find_one({"id": request.world_id}, {"_id": 0})
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    
    generated = await ai_auto_generate(request.prompt, world, request.provider)
    
    # Update the world with generated content
    update_data = {
        "zones": generated["zones"],
        "prefabs": generated["prefabs"],
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    if generated.get("terrain"):
        update_data["terrain"] = generated["terrain"]
    
    if generated.get("description"):
        update_data["description"] = generated["description"]
    
    await db.worlds.update_one({"id": request.world_id}, {"$set": update_data})
    
    # Return updated world
    updated_world = await db.worlds.find_one({"id": request.world_id}, {"_id": 0})
    return {
        "world": updated_world,
        "generated": generated
    }

# ==================== P2: COLLABORATION (Session-based) ====================

# In-memory collaboration sessions (for demo - use Redis in production)
collab_sessions: Dict[str, Dict[str, Any]] = {}

@api_router.post("/collab/join")
async def join_collab_session(session: CollabSession):
    """Join a collaborative editing session"""
    world_id = session.world_id
    user_id = session.user_id
    
    if world_id not in collab_sessions:
        collab_sessions[world_id] = {
            "users": {},
            "created_at": datetime.now(timezone.utc).isoformat()
        }
    
    collab_sessions[world_id]["users"][user_id] = {
        "joined_at": datetime.now(timezone.utc).isoformat(),
        "cursor": {"x": 0, "y": 0}
    }
    
    return {
        "session_id": world_id,
        "users": list(collab_sessions[world_id]["users"].keys()),
        "user_count": len(collab_sessions[world_id]["users"])
    }

@api_router.post("/collab/leave")
async def leave_collab_session(session: CollabSession):
    """Leave a collaborative editing session"""
    world_id = session.world_id
    user_id = session.user_id
    
    if world_id in collab_sessions and user_id in collab_sessions[world_id]["users"]:
        del collab_sessions[world_id]["users"][user_id]
        
        if not collab_sessions[world_id]["users"]:
            del collab_sessions[world_id]
            return {"message": "Session ended", "users": []}
    
    return {
        "message": "Left session",
        "users": list(collab_sessions.get(world_id, {}).get("users", {}).keys())
    }

@api_router.post("/collab/update")
async def update_collab_session(session: CollabSession):
    """Send an update to collaborators"""
    world_id = session.world_id
    user_id = session.user_id
    
    if world_id not in collab_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Store the update for polling
    if "updates" not in collab_sessions[world_id]:
        collab_sessions[world_id]["updates"] = []
    
    collab_sessions[world_id]["updates"].append({
        "user_id": user_id,
        "action": session.action,
        "data": session.data,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    
    # Keep only last 100 updates
    collab_sessions[world_id]["updates"] = collab_sessions[world_id]["updates"][-100:]
    
    return {"message": "Update sent", "update_count": len(collab_sessions[world_id]["updates"])}

@api_router.get("/collab/{world_id}/status")
async def get_collab_status(world_id: str, since: Optional[str] = None):
    """Get collaboration session status and recent updates"""
    if world_id not in collab_sessions:
        return {"active": False, "users": [], "updates": []}
    
    session = collab_sessions[world_id]
    updates = session.get("updates", [])
    
    if since:
        updates = [u for u in updates if u["timestamp"] > since]
    
    return {
        "active": True,
        "users": list(session["users"].keys()),
        "user_count": len(session["users"]),
        "updates": updates[-20:]  # Return last 20 updates
    }

# ==================== P2: 3D PREVIEW DATA ====================

@api_router.get("/worlds/{world_id}/preview-3d")
async def get_3d_preview_data(world_id: str):
    """Get data formatted for 3D preview rendering"""
    world = await db.worlds.find_one({"id": world_id}, {"_id": 0})
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    
    # Generate height map data based on zones and terrain
    terrain = world.get("terrain", {})
    zones = world.get("zones", [])
    map_width = world.get("map_width", 64)
    map_height = world.get("map_height", 64)
    
    # Create a simplified height map
    height_map = []
    zone_map = {(z.get("x"), z.get("y")): z for z in zones}
    
    for y in range(map_height):
        row = []
        for x in range(map_width):
            base_height = 0.5
            zone = zone_map.get((x, y))
            
            if zone:
                zone_type = zone.get("type", "emerald_grove")
                # Different zones have different base heights
                zone_heights = {
                    "emerald_grove": 0.5,
                    "borea": 0.7,
                    "desert": 0.3,
                    "arctic": 0.8,
                    "corrupted": 0.4
                }
                base_height = zone_heights.get(zone_type, 0.5)
            
            # Apply terrain modifiers
            height = base_height * terrain.get("height_scale", 1.0)
            height += terrain.get("mountain_scale", 0.5) * 0.2 * (((x + y) % 7) / 7)
            
            row.append(round(min(1.0, max(0.0, height)), 2))
        height_map.append(row)
    
    # Format prefabs for 3D
    prefabs_3d = []
    for p in world.get("prefabs", []):
        prefabs_3d.append({
            "type": p.get("type"),
            "position": {"x": p.get("x"), "y": p.get("y")},
            "rotation": p.get("rotation", 0),
            "scale": p.get("scale", 1.0),
            "height": height_map[p.get("y", 0)][p.get("x", 0)] if p.get("y", 0) < map_height and p.get("x", 0) < map_width else 0.5
        })
    
    return {
        "world_id": world_id,
        "dimensions": {"width": map_width, "height": map_height},
        "terrain": terrain,
        "height_map": height_map,
        "zones": zones,
        "prefabs": prefabs_3d,
        "render_settings": {
            "water_level": terrain.get("ocean_level", 0.3),
            "fog_density": 0.02,
            "ambient_light": 0.4
        }
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

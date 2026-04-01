import random
import uuid
import json
import os
from typing import Optional, Dict, List
from fastapi import HTTPException
from models import TerrainSettings, ZoneConfig, PrefabPlacement
from templates import WORLD_TEMPLATES


def generate_seed(style: Optional[str] = None) -> str:
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
    colors = {
        "emerald_grove": "#10B981",
        "borea": "#06B6D4",
        "desert": "#F59E0B",
        "arctic": "#E2E8F0",
        "corrupted": "#8B5CF6"
    }
    return colors.get(zone_type, "#6B7280")


def get_prefab_icon(prefab_type: str) -> str:
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
    template = WORLD_TEMPLATES.get(template_id)
    if not template:
        return [], [], TerrainSettings()

    zones = []
    prefabs = []
    zone_types = list(template["zone_distribution"].keys())
    zone_weights = list(template["zone_distribution"].values())
    prefab_types = list(template["prefab_weights"].keys())
    prefab_weights = list(template["prefab_weights"].values())

    total_cells = map_width * map_height
    target_zones = int(total_cells * 0.6)

    placed = set()
    zone_seeds = []
    num_seeds = max(5, int(total_cells / 100))
    for _ in range(num_seeds):
        x = random.randint(0, map_width - 1)
        y = random.randint(0, map_height - 1)
        zone_type = random.choices(zone_types, weights=zone_weights, k=1)[0]
        if zone_weights[zone_types.index(zone_type)] > 0:
            zone_seeds.append((x, y, zone_type))

    for seed_x, seed_y, zone_type in zone_seeds:
        radius = random.randint(2, max(3, min(map_width, map_height) // 8))
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                if dx * dx + dy * dy <= radius * radius:
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

    target_prefabs = int(len(zones) * template["prefab_density"])
    zone_positions = [(z.x, z.y) for z in zones]

    if zone_positions:
        for _ in range(target_prefabs):
            pos = random.choice(zone_positions)
            prefab_type = random.choices(prefab_types, weights=prefab_weights, k=1)[0]
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

    try:
        json_str = response.strip()
        if "```json" in json_str:
            json_str = json_str.split("```json")[1].split("```")[0]
        elif "```" in json_str:
            json_str = json_str.split("```")[1].split("```")[0]

        generated = json.loads(json_str)

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


async def get_ai_response(message: str, world_config: dict, provider: str) -> dict:
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

    system_message = """You are a Hytale World Builder AI assistant. You help users create amazing game worlds by suggesting:
- Zone placements and configurations (Emerald Grove, Borea, Desert, Arctic, Corrupted)
- Biome settings and mixing
- Prefab placements (dungeons, villages, ruins, towers, caves, portals)
- Terrain settings (height, caves, rivers, mountains)
- World themes and narratives

When making suggestions, provide specific values and coordinates when possible.
Format suggestions as actionable items the user can apply to their world.
Keep responses concise but helpful. If suggesting world changes, format them as JSON when appropriate."""

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

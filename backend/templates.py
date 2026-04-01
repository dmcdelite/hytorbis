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

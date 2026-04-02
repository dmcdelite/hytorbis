"""Generates mini-map thumbnail images from world data."""
import io
import base64
from PIL import Image, ImageDraw

ZONE_COLORS = {
    "emerald_grove": (16, 185, 129),
    "borea": (6, 182, 212),
    "desert": (245, 158, 11),
    "arctic": (200, 210, 220),
    "corrupted": (139, 92, 246),
}

PREFAB_COLOR = (255, 255, 255)
BG_COLOR = (26, 29, 42)
WATER_COLOR = (30, 64, 175)


def generate_thumbnail(world: dict, size: int = 128) -> str:
    """Generate a base64 PNG thumbnail from world zone/prefab data."""
    map_w = world.get("map_width", 64)
    map_h = world.get("map_height", 64)
    zones = world.get("zones", [])
    prefabs = world.get("prefabs", [])
    terrain = world.get("terrain", {})
    ocean_level = terrain.get("ocean_level", 0.3)

    img = Image.new("RGB", (size, size), BG_COLOR)
    draw = ImageDraw.Draw(img)

    sx = size / map_w
    sy = size / map_h

    # Build zone lookup
    zone_map = {}
    for z in zones:
        zone_map[(z.get("x", 0), z.get("y", 0))] = z.get("type", "emerald_grove")

    # Draw zones
    for (zx, zy), ztype in zone_map.items():
        color = ZONE_COLORS.get(ztype, (107, 114, 128))
        px = int(zx * sx)
        py = int(zy * sy)
        pw = max(1, int(sx))
        ph = max(1, int(sy))
        draw.rectangle([px, py, px + pw, py + ph], fill=color)

    # Draw water for uncovered cells (simple deterministic pattern)
    if ocean_level > 0.1:
        for y in range(0, size, max(1, int(sy))):
            for x in range(0, size, max(1, int(sx))):
                mx = int(x / sx)
                my = int(y / sy)
                if (mx, my) not in zone_map:
                    # Simple hash to decide water vs land
                    h = ((mx * 7 + my * 13) % 100) / 100
                    if h < ocean_level * 0.6:
                        pw = max(1, int(sx))
                        ph = max(1, int(sy))
                        draw.rectangle([x, y, x + pw, y + ph], fill=WATER_COLOR)

    # Draw prefabs as bright dots
    for p in prefabs:
        px = int(p.get("x", 0) * sx + sx / 2)
        py = int(p.get("y", 0) * sy + sy / 2)
        r = max(1, int(min(sx, sy) * 0.4))
        draw.ellipse([px - r, py - r, px + r, py + r], fill=PREFAB_COLOR)

    # Encode to base64
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    buf.seek(0)
    b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{b64}"

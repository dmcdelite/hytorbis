import {
  TreePine, Snowflake, Sun, Skull, Castle, Home, Landmark, Building, Mountain, Sparkles,
  Compass, Heart, Swords, Map, Pickaxe
} from "lucide-react";

export const ZONE_CONFIG = {
  emerald_grove: { name: "Emerald Grove", color: "#10B981", icon: TreePine, id: 1 },
  borea: { name: "Borea", color: "#06B6D4", icon: Snowflake, id: 2 },
  desert: { name: "Desert", color: "#F59E0B", icon: Sun, id: 3 },
  arctic: { name: "Arctic", color: "#E2E8F0", icon: Snowflake, id: 4 },
  corrupted: { name: "Corrupted", color: "#8B5CF6", icon: Skull, id: 5 }
};

export const PREFAB_CONFIG = {
  dungeon: { name: "Dungeon", icon: Castle },
  village: { name: "Village", icon: Home },
  ruins: { name: "Ruins", icon: Landmark },
  tower: { name: "Tower", icon: Building },
  cave_entrance: { name: "Cave", icon: Mountain },
  portal: { name: "Portal", icon: Sparkles }
};

export const BIOME_CONFIG = {
  forest: { name: "Forest", zones: ["emerald_grove"], color: "#22C55E" },
  plains: { name: "Plains", zones: ["emerald_grove", "desert"], color: "#84CC16" },
  swamp: { name: "Swamp", zones: ["emerald_grove"], color: "#65A30D" },
  mountains: { name: "Mountains", zones: ["emerald_grove", "borea", "arctic"], color: "#78716C" },
  tundra: { name: "Tundra", zones: ["borea", "arctic"], color: "#A5F3FC" },
  glacier: { name: "Glacier", zones: ["arctic"], color: "#E0F2FE" },
  dunes: { name: "Dunes", zones: ["desert"], color: "#FCD34D" },
  oasis: { name: "Oasis", zones: ["desert"], color: "#34D399" },
  void: { name: "Void", zones: ["corrupted"], color: "#7C3AED" },
  wasteland: { name: "Wasteland", zones: ["corrupted"], color: "#A855F7" }
};

// Hytale Cave System — matches CaveGenerator / CaveType API
export const CAVE_TYPES = {
  natural: { name: "Natural Cave", color: "#78716C", description: "Standard underground tunnels", defaultBiomes: ["forest", "plains", "mountains"] },
  crystal: { name: "Crystal Cavern", color: "#818CF8", description: "Luminescent crystal formations", defaultBiomes: ["mountains", "glacier"] },
  lava: { name: "Lava Tube", color: "#EF4444", description: "Volcanic underground channels", defaultBiomes: ["dunes", "wasteland"] },
  ice: { name: "Ice Cave", color: "#7DD3FC", description: "Frozen underground passages", defaultBiomes: ["tundra", "glacier"] },
  corrupted: { name: "Corrupted Depths", color: "#A855F7", description: "Dark magic-infused caverns", defaultBiomes: ["void", "wasteland"] },
  flooded: { name: "Flooded Grotto", color: "#2DD4BF", description: "Partially submerged cave system", defaultBiomes: ["swamp", "oasis"] },
};

// Default cave configs per zone type — matches Hytale's zone.caveGenerator() pattern
export const ZONE_DEFAULT_CAVES = {
  emerald_grove: ["natural", "flooded"],
  borea: ["natural", "ice"],
  desert: ["natural", "lava"],
  arctic: ["ice"],
  corrupted: ["corrupted", "lava"],
};

// Zone Discovery Config — matches Hytale's ZoneDiscoveryConfig
export const ZONE_DISCOVERY_DEFAULTS = {
  emerald_grove: { showNotification: true, displayName: "Emerald Grove", soundEvent: "zone.emerald.discover", majorZone: true, duration: 5.0, fadeIn: 2.0, fadeOut: 1.5 },
  borea: { showNotification: true, displayName: "Borea", soundEvent: "zone.borea.discover", majorZone: true, duration: 5.0, fadeIn: 2.0, fadeOut: 1.5 },
  desert: { showNotification: true, displayName: "Howling Sands", soundEvent: "zone.desert.discover", majorZone: true, duration: 5.0, fadeIn: 2.0, fadeOut: 1.5 },
  arctic: { showNotification: true, displayName: "Frozen Wastes", soundEvent: "zone.arctic.discover", majorZone: true, duration: 5.0, fadeIn: 2.0, fadeOut: 1.5 },
  corrupted: { showNotification: true, displayName: "The Corruption", soundEvent: "zone.corrupted.discover", majorZone: true, duration: 5.0, fadeIn: 2.0, fadeOut: 1.5 },
};

export const MAP_SIZE_PRESETS = [
  { label: "Small (32x32)", width: 32, height: 32 },
  { label: "Medium (64x64)", width: 64, height: 64 },
  { label: "Large (128x128)", width: 128, height: 128 },
  { label: "Huge (256x256)", width: 256, height: 256 },
  { label: "Max (512x512)", width: 512, height: 512 }
];

export const TEMPLATE_ICONS = {
  adventure: Compass,
  peaceful: Heart,
  challenge: Swords,
  exploration: Map,
  dungeon_crawler: Pickaxe
};

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
export const API = `${BACKEND_URL}/api`;
export const WS_URL = BACKEND_URL.replace('https://', 'wss://').replace('http://', 'ws://');

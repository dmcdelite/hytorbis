import {
  TreePine, Snowflake, Sun, Skull, Castle, Home, Landmark, Building, Mountain, Sparkles,
  Compass, Heart, Swords, Map, Pickaxe
} from "lucide-react";

export const ZONE_CONFIG = {
  emerald_grove: { name: "Emerald Grove", color: "#10B981", icon: TreePine },
  borea: { name: "Borea", color: "#06B6D4", icon: Snowflake },
  desert: { name: "Desert", color: "#F59E0B", icon: Sun },
  arctic: { name: "Arctic", color: "#E2E8F0", icon: Snowflake },
  corrupted: { name: "Corrupted", color: "#8B5CF6", icon: Skull }
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

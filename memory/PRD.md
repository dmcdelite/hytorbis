# Hytale World Builder - Product Requirements Document

## Original Problem Statement
Build a Hytale World Builder web application - a comprehensive tool for creating and generating Hytale game worlds similar to Minecraft world builders.

## User Requests
1. Both visual seed-based generator AND interactive map builder
2. All features: zones, biomes, prefabs, terrain, seeds, 2D map preview
3. All export options: Hytale-compatible files, JSON config files, and visualization
4. AI assistance with user-selectable providers (GPT-5.2, Gemini, Claude)
5. **Map sizes up to 512x512** (requested April 1, 2026)
6. **P1 Features** (requested April 1, 2026): biome mixing, drag-to-paint, properties panel, undo/redo

## User Personas
1. **Hytale Modders** - Create custom adventure maps and worlds
2. **Server Admins** - Design world configurations for community servers
3. **Casual Players** - Plan and visualize dream worlds before building
4. **Content Creators** - Generate unique worlds for videos/streams

## Core Requirements (Static)
- Interactive 2D map canvas for zone/prefab placement
- 5 Zone types: Emerald Grove, Borea, Desert, Arctic, Corrupted
- 6 Prefab types: Dungeon, Village, Ruins, Tower, Cave Entrance, Portal
- Terrain controls: Height, Caves, Rivers, Mountains, Ocean
- World seed management (create, save, load, delete)
- Export to JSON and Hytale-compatible formats
- AI assistant with multi-LLM support

## Architecture
- **Frontend**: React 19 + Tailwind CSS + Radix UI components
- **Backend**: FastAPI (Python) with async MongoDB
- **Database**: MongoDB for world storage
- **AI**: emergentintegrations library with Emergent LLM Key

## What's Been Implemented

### MVP (April 1, 2026)
- [x] World CRUD (create, read, update, delete, list)
- [x] Seed generation (random and styled)
- [x] Zone management (add/remove)
- [x] Prefab management (add/remove)
- [x] Export endpoints (JSON and Hytale format)
- [x] AI chat with multi-provider support (OpenAI, Anthropic, Gemini)
- [x] Interactive 20x20 map canvas
- [x] Dark theme with professional gaming UI

### P1 Features (April 1, 2026)
- [x] **512x512 Map Support** - Maps from 32x32 to 512x512
- [x] **Map Size Presets** - Small (32), Medium (64), Large (128), Huge (256), Max (512)
- [x] **Virtualized Rendering** - Efficient rendering for large maps
- [x] **Zoom Controls** - 10% to 200% zoom with slider
- [x] **Pan Tool** - Navigate large maps (also Alt+drag)
- [x] **Auto-zoom** - Automatically adjusts zoom for map size
- [x] **Undo/Redo** - History stack with 50 states
- [x] **Drag-to-Paint** - Click and drag to paint zones
- [x] **Zone Properties Panel** - Edit zone difficulty, biomes
- [x] **Biome Mixing** - Add compatible biomes to zones with density/variation
- [x] **Prefab Properties Panel** - Edit rotation (0/90/180/270°) and scale (0.5x-2x)
- [x] **Stats Display** - Shows zone and prefab counts

## Testing Status
- Backend: 100% functional
- Frontend: All P1 features working
- 512x512 maps verified

## Prioritized Backlog

### P0 (Critical) - COMPLETE
- [x] Core world CRUD
- [x] Map canvas with zone/prefab placement
- [x] AI integration

### P1 (High Priority) - COMPLETE
- [x] 512x512 map support
- [x] Biome mixing/blending within zones
- [x] Drag-to-paint for zones
- [x] Zone/prefab property editing panel
- [x] Undo/redo functionality
- [x] Pan and zoom for large maps

### P2 (Medium Priority)
- [ ] World templates (Adventure, Peaceful, Challenge)
- [ ] Import existing Hytale world configs
- [ ] 3D preview mode
- [ ] Collaborative editing (real-time)
- [ ] AI auto-generation (populate entire map from prompt)

### P3 (Nice to Have)
- [ ] World sharing/community gallery
- [ ] Custom prefab definitions
- [ ] Procedural generation preview
- [ ] Performance stats/analytics

## Next Tasks
1. World templates (Adventure, Peaceful, Challenge)
2. AI auto-generation feature
3. Import existing configs

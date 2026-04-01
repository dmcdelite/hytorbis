# Hytale World Builder - Product Requirements Document

## Original Problem Statement
Build a Hytale World Builder web application - a comprehensive tool for creating and generating Hytale game worlds similar to Minecraft world builders. User requested:
1. Both visual seed-based generator AND interactive map builder
2. All features: zones, biomes, prefabs, terrain, seeds, 2D map preview
3. All export options: Hytale-compatible files, JSON config files, and visualization
4. AI assistance with user-selectable providers (GPT-5.2, Gemini, Claude)

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

## What's Been Implemented (April 1, 2026)

### Backend API (/app/backend/server.py)
- [x] Health check endpoint
- [x] World CRUD (create, read, update, delete, list)
- [x] Seed generation (random and styled)
- [x] Zone management (add/remove)
- [x] Prefab management (add/remove)
- [x] Export endpoints (JSON and Hytale format)
- [x] Reference data endpoints (zones, prefabs, biomes)
- [x] AI chat with multi-provider support (OpenAI, Anthropic, Gemini)

### Frontend (/app/frontend/src/App.js)
- [x] World list sidebar with CRUD operations
- [x] Interactive 20x20 map canvas
- [x] Zone placement tool with type selector
- [x] Prefab placement tool with type selector
- [x] Terrain settings panel with 5 sliders
- [x] Save and export functionality
- [x] AI chat panel with provider selector
- [x] Dark theme with professional gaming UI

## Testing Status
- Backend: 100% (15/15 tests passed)
- Frontend: 95% (19/20 features working)

## Prioritized Backlog

### P0 (Critical) - DONE
- [x] Core world CRUD
- [x] Map canvas with zone/prefab placement
- [x] AI integration

### P1 (High Priority)
- [ ] Biome mixing/blending within zones
- [ ] Multi-cell zone painting (drag to paint)
- [ ] Zone/prefab property editing panel
- [ ] Undo/redo functionality

### P2 (Medium Priority)
- [ ] World templates (Adventure, Peaceful, Challenge)
- [ ] Import existing Hytale world configs
- [ ] 3D preview mode
- [ ] Collaborative editing (real-time)

### P3 (Nice to Have)
- [ ] World sharing/community gallery
- [ ] Custom prefab definitions
- [ ] Procedural generation preview
- [ ] Performance stats/analytics

## Next Tasks
1. Add biome configuration to zones
2. Implement drag-to-paint for zones
3. Add zone/prefab properties panel
4. Create world templates

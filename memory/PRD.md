# Hytale World Builder - Product Requirements Document

## Original Problem Statement
Build a "Hytale Worlds" app — a world builder generator similar to Minecraft's — using React + FastAPI + MongoDB. Features include AI assistance (GPT, Gemini, Claude), up to 512x512 map grid support, exports in `.prefab.json` and `.jar` formats, and multi-phase feature sets.

## Architecture
- **Frontend**: React 19, Tailwind CSS, Radix UI (Shadcn), Lucide icons
- **Backend**: FastAPI, Motor (Async MongoDB), WebSockets
- **Database**: MongoDB
- **AI**: OpenAI/Anthropic/Gemini via `emergentintegrations` (Emergent LLM Key)
- **Auth**: Custom JWT with httpOnly cookies, bcrypt password hashing

## File Structure
```
/app/backend/server.py    — All backend routes, models, websockets (~2500 lines)
/app/frontend/src/App.js  — All frontend UI, state, dialogs (~2700 lines)
/app/frontend/src/App.css — All styling (~1550 lines)
```

## Completed Phases

### MVP (DONE)
- Basic world builder grid with biome zones
- MongoDB CRUD for worlds
- LLM AI integration (GPT-5.2, Claude Sonnet, Gemini Flash) for world design assistance
- World save/load/delete

### P1: Advanced Map Tools (DONE)
- 512x512 grid support with virtualized rendering
- Drag-to-paint functionality
- Biome mixing and properties panel
- Undo/Redo history (50 states)
- Zoom and pan controls

### P2: Templates & Exports (DONE)
- 5 world templates (Adventure, Peaceful, Challenge, Exploration, Dungeon Crawler)
- Config importing from JSON
- Export formats: JSON, Hytale (.hytale), Prefab (.prefab.json), JAR (.jar)
- AI auto-generation for full world population

### P3: Collaboration & Gallery (DONE)
- Real-time WebSocket collaboration (multi-user editing)
- Custom prefab creation/management
- 3D/height-map terrain preview
- Procedural generation preview with step-by-step animation
- Community gallery with publish/download/like
- Performance analytics dashboard

### P4: Authentication, Profiles & Versioning (DONE - April 1, 2026)
- User registration/login with JWT httpOnly cookies
- Brute force protection (5 attempts lockout)
- Token refresh mechanism
- User profiles with stats (worlds, published, downloads, likes)
- Profile editing (name, bio)
- World version history (create/list/restore snapshots, max 20)
- World public/private visibility toggle
- World reviews with star ratings and comments
- Duplicate review prevention
- Admin user auto-seeded on startup

## Key API Endpoints
- `GET /api/worlds` - List worlds
- `POST /api/worlds` - Create world
- `GET /api/worlds/{id}` - Get world
- `PUT /api/worlds/{id}` - Update world
- `DELETE /api/worlds/{id}` - Delete world
- `POST /api/chat` - AI chat proxy
- `POST /api/generate/auto` - AI auto-generate world
- `GET /api/worlds/export/{format}` - Export world
- `GET /api/templates` - List templates
- `POST /api/gallery/publish/{id}` - Publish to gallery
- `GET /api/gallery` - Browse gallery
- `WS /api/ws/{world_id}/{user_id}` - WebSocket collaboration
- `POST /api/auth/register` - Register
- `POST /api/auth/login` - Login
- `POST /api/auth/logout` - Logout
- `GET /api/auth/me` - Current user
- `POST /api/auth/refresh` - Refresh token
- `GET /api/users/{id}/profile` - User profile
- `PUT /api/users/profile` - Update profile
- `POST /api/worlds/{id}/versions` - Create version
- `GET /api/worlds/{id}/versions` - List versions
- `POST /api/worlds/{id}/versions/{vid}/restore` - Restore version
- `PUT /api/worlds/{id}/visibility` - Toggle visibility
- `POST /api/reviews` - Create review
- `GET /api/reviews/{gallery_id}` - Get reviews

## DB Collections
- `worlds` - World data (zones, prefabs, terrain, settings)
- `templates` - World templates
- `gallery` - Published gallery entries
- `custom_prefabs` - User-created prefabs
- `users` - User accounts (email, password_hash, name, role, bio)
- `login_attempts` - Brute force tracking
- `world_versions` - Version snapshots
- `reviews` - Gallery reviews with ratings

## Backlog
- **P1 (Refactoring)**: Split `App.js` (~2700 lines) and `server.py` (~2500 lines) into modular components/routers
- **P2**: Enhanced permissions (world ownership, role-based access)
- **P2**: Social features (follow users, notifications)

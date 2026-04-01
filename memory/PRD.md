# Hytale World Builder - Product Requirements Document

## Original Problem Statement
Build a "Hytale Worlds" app — a world builder generator similar to Minecraft's — using React + FastAPI + MongoDB. Features include AI assistance (GPT, Gemini, Claude), up to 512x512 map grid support, exports in `.prefab.json` and `.jar` formats, and multi-phase feature sets.

## Architecture (Post-Refactor v2)

### Backend (Modular Routers)
```
/app/backend/
├── server.py              # Slim entry (~65 lines): app, CORS, router includes, startup
├── database.py            # MongoDB connection (Motor)
├── auth_utils.py          # JWT, bcrypt, get_current_user, require_auth
├── models.py              # All Pydantic models
├── templates.py           # WORLD_TEMPLATES constant
├── utils.py               # AI functions, world generation, seed helpers
├── websocket_manager.py   # WebSocket ConnectionManager
└── routes/
    ├── auth.py            # /auth/* (register, login, logout, me, refresh) + admin seeding
    ├── users.py           # /users/* (profile, follow/unfollow, notifications)
    ├── worlds.py          # /worlds/* (CRUD, zones, prefabs, export, import, visibility, templates, 3D preview)
    ├── ai.py              # /ai/* (chat, auto-generate, procedural preview)
    ├── gallery.py         # /gallery/* (publish, browse, like, download) + follower notifications
    ├── reviews.py         # /reviews/* (create, list, delete)
    ├── versions.py        # /worlds/*/versions (create, list, restore)
    └── misc.py            # WebSocket, custom prefabs, analytics, collaboration
```

### Frontend (Component Architecture)
```
/app/frontend/src/
├── App.js                     # Thin wrapper (~30 lines)
├── App.css                    # All global styles
├── config.js                  # Zone/Prefab/Biome configs, API URL
├── contexts/
│   └── AppContext.js           # All shared state + functions
└── components/app/
    ├── Header.jsx              # App header, auth buttons, notifications bell
    ├── Sidebar.jsx             # Worlds list, tools, zoom, actions, exports
    ├── AIPanel.jsx             # AI chat panel
    ├── MapArea.jsx             # Map canvas (virtualized), terrain, properties sheets
    ├── Dialogs.jsx             # All dialog components + sub-canvases
    └── CollabChat.jsx          # Collaboration chat overlay
```

### Tech Stack
- Frontend: React 19, Tailwind CSS, Radix UI (Shadcn), Lucide icons
- Backend: FastAPI, Motor (Async MongoDB), WebSockets
- Database: MongoDB
- AI: OpenAI/Anthropic/Gemini via `emergentintegrations` (Emergent LLM Key)
- Auth: Custom JWT with httpOnly cookies, bcrypt password hashing

## Completed Phases

### MVP (DONE)
- Basic world builder grid with biome zones
- MongoDB CRUD for worlds
- LLM AI integration for world design assistance

### P1: Advanced Map Tools (DONE)
- 512x512 grid support with virtualized rendering
- Drag-to-paint, biome mixing, properties panel, undo/redo, zoom/pan

### P2: Templates & Exports (DONE)
- 5 world templates, config importing
- Export: JSON, Hytale, Prefab (.prefab.json), JAR (.jar)
- AI auto-generation

### P3: Collaboration & Gallery (DONE)
- Real-time WebSocket collaboration
- Custom prefabs, 3D preview, procedural generation preview
- Community gallery, analytics

### P4: Auth, Profiles & Versioning (DONE)
- JWT auth with httpOnly cookies, brute force protection
- User profiles with stats, editing
- World version history (create/list/restore, max 20)
- Public/private visibility toggle, world reviews

### P5: Refactoring + Permissions + Social (DONE - April 1, 2026)
- **Refactoring**: Split server.py (2500 lines) into 8 route modules + 5 shared modules
- **Refactoring**: Split App.js (2700 lines) into 6 React components + shared context
- **Enhanced Permissions**: World ownership (owner_id), 403 for non-owner edit/delete/publish
- **Social Features**: Follow/unfollow users, notifications (follower, publication, like, download, review), notification bell with unread count, mark-all-read
- **Profile**: Now includes followers_count and following_count

## DB Collections
- `worlds` - World data (zones, prefabs, terrain, owner_id, is_public)
- `templates` - World templates
- `gallery` - Published entries (creator_id)
- `custom_prefabs` - User-created prefabs
- `users` - User accounts (email, password_hash, name, role, bio)
- `login_attempts` - Brute force tracking
- `world_versions` - Version snapshots
- `reviews` - Gallery reviews with ratings
- `follows` - Follow relationships (follower_id, following_id)
- `notifications` - Activity notifications (user_id, type, data, read)
- `analytics` - Event tracking

## Backlog
- **P1**: Add aria-describedby to all Dialog components (accessibility)
- **P2**: Enhanced social (activity feed page, user search, suggested users)
- **P2**: World forking/cloning from gallery
- **P3**: Advanced search/filtering in gallery (by zone type, map size)
- **P3**: Real-time notifications via WebSocket

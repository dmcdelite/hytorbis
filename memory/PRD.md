# Hytale World Builder - Product Requirements Document

## Original Problem Statement
Build a "Hytale Worlds" app — a world builder generator similar to Minecraft's — using React + FastAPI + MongoDB. Features include AI assistance (GPT, Gemini, Claude), up to 512x512 map grid support, exports in `.prefab.json` and `.jar` formats, and multi-phase feature sets.

## Architecture (Post-Refactor v2)

### Backend (Modular Routers)
```
/app/backend/
├── server.py              # Slim entry (~65 lines)
├── database.py            # MongoDB connection (Motor)
├── auth_utils.py          # JWT, bcrypt, get_current_user, require_auth
├── models.py              # All Pydantic models (WorldConfig, UserProfile, etc.)
├── templates.py           # WORLD_TEMPLATES constant
├── utils.py               # AI functions, world generation, seed helpers
├── websocket_manager.py   # WebSocket ConnectionManager + notification channels
├── thumbnail.py           # Pillow-based thumbnail generation
└── routes/
    ├── auth.py            # /auth/* (register, login, logout, me, refresh) + admin seeding
    ├── users.py           # /users/* (profile, search, suggested, follow, notifications, activity feed)
    ├── worlds.py          # /worlds/* (CRUD, zones, prefabs, export, import, visibility, templates, fork, collaborators, thumbnails)
    ├── ai.py              # /ai/* (chat, auto-generate, procedural preview)
    ├── gallery.py         # /gallery/* (publish, browse with filters, like, download, fork)
    ├── reviews.py         # /reviews/* (create, list, delete)
    ├── versions.py        # /worlds/*/versions (create, list, restore)
    └── misc.py            # WebSocket (collab + notifications), custom prefabs, analytics
```

### Frontend (Component Architecture)
```
/app/frontend/src/
├── App.js                     # Wrapper with mobile sidebar logic
├── App.css                    # All global styles + responsive breakpoints
├── config.js                  # Zone/Prefab/Biome configs, API URL
├── contexts/
│   └── AppContext.js           # All shared state + functions (~970 lines)
└── components/app/
    ├── Header.jsx              # Header: auth, notifications, activity, search, collaborators, mobile toggle
    ├── Sidebar.jsx             # Worlds list, tools, zoom, actions, exports
    ├── AIPanel.jsx             # AI chat panel
    ├── MapArea.jsx             # Map canvas (virtualized), terrain, properties sheets
    ├── Dialogs.jsx             # All dialogs (auth, profile, gallery, reviews, versions, user search, activity feed, collaborators) — all with DialogDescription
    └── CollabChat.jsx          # Collaboration chat overlay
```

### Tech Stack
- Frontend: React 19, Tailwind CSS, Radix UI (Shadcn), Lucide icons
- Backend: FastAPI, Motor (Async MongoDB), WebSockets
- Database: MongoDB (10+ collections)
- AI: OpenAI/Anthropic/Gemini via `emergentintegrations` (Emergent LLM Key)
- Auth: Custom JWT with httpOnly cookies, bcrypt

## Completed Phases

### MVP (DONE) - Basic world builder, CRUD, AI integration
### P1 (DONE) - 512x512 grid, drag-to-paint, undo/redo, zoom/pan
### P2 (DONE) - Templates, exports (JSON, Hytale, Prefab, JAR), AI auto-gen
### P3 (DONE) - WebSocket collaboration, gallery, analytics, 3D preview
### P4 (DONE) - Auth, profiles, versions, reviews, visibility
### P5 (DONE) - Backend + Frontend refactoring into modular architecture
### P6 (DONE - April 2, 2026) - Enhancements:
1. Dialog Accessibility — DialogDescription on all dialogs
2. Enhanced Social — User search, activity feed, suggested users
3. World Forking — Fork worlds directly or from gallery
4. Advanced Gallery Filtering — Zone types, map size range, min rating, following-only
5. Real-time Notifications — WebSocket push, auto-reconnect, ping/pong
6. Multiplayer World Permissions — Collaborator management, editor/viewer roles
7. Auto-generated World Thumbnails — Pillow-based mini-map thumbnails

### P7 (DONE - April 2, 2026) - Polish:
1. Full Accessibility Compliance — HiddenDesc on all 17 dialogs
2. Mobile Responsiveness — Breakpoints at 1200/900/768/480px, slide-in sidebars, hamburger menu, mobile overlay
3. Enhanced Collaborator UI — Search dropdown, role descriptions, improved empty states

## DB Collections
worlds, templates, gallery, custom_prefabs, users, login_attempts, world_versions, reviews, follows, notifications, analytics

## All API Endpoints

### Auth
- POST /api/auth/register, /api/auth/login, /api/auth/logout, /api/auth/refresh
- GET /api/auth/me

### Users & Social
- GET /api/users/search?q=, /api/users/suggested, /api/users/{id}/profile
- PUT /api/users/profile
- POST /api/users/{id}/follow, /api/users/{id}/unfollow
- GET /api/users/{id}/followers, /api/users/{id}/following, /api/users/{id}/is-following
- GET /api/notifications, POST /api/notifications/read-all
- GET /api/activity-feed

### Worlds
- CRUD: GET/POST /api/worlds, GET/PUT/DELETE /api/worlds/{id}
- Zones: POST/DELETE /api/worlds/{id}/zones(/{zone_id})
- Prefabs: POST/DELETE /api/worlds/{id}/prefabs(/{prefab_id})
- PUT /api/worlds/{id}/visibility
- POST /api/worlds/{id}/fork
- GET/POST/PUT/DELETE /api/worlds/{id}/collaborators(/{user_id})
- GET/POST /api/worlds/{id}/versions, POST /api/worlds/{id}/versions/{vid}/restore
- GET/POST /api/worlds/{id}/thumbnail

### Templates & Exports
- GET /api/templates, POST /api/worlds/from-template, POST /api/worlds/import
- GET /api/worlds/{id}/export/{json|hytale|prefab|jar}
- GET /api/worlds/{id}/preview-3d
- GET /api/reference/{zones|prefabs|biomes}, GET /api/seed/random

### AI
- POST /api/ai/chat, /api/ai/auto-generate, /api/generate/preview

### Gallery
- POST /api/gallery/publish, GET /api/gallery (with filters), GET /api/gallery/featured
- GET/POST /api/gallery/{id}(/like|/download|/fork)
- POST/GET /api/reviews(/{gallery_id}), DELETE /api/reviews/{id}

### WebSockets
- WS /api/ws/collab/{world_id}/{user_id}
- WS /api/ws/notifications/{user_id}

### Analytics
- POST /api/analytics/track, GET /api/analytics/world/{id}, GET /api/analytics/summary
- GET/POST/DELETE /api/prefabs/custom(/{id})

## Backlog
- All requested features are now COMPLETE
- Potential future: Further split AppContext.js (~970 lines) into smaller context providers

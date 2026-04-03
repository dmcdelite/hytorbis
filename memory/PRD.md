# Hytale World Builder - Product Requirements Document

## Original Problem Statement
Build a "Hytale Worlds" app — a world builder generator similar to Minecraft's — using React + FastAPI + MongoDB. Features include AI assistance (GPT, Gemini, Claude), up to 512x512 map grid support, exports in `.prefab.json` and `.jar` formats, and multi-phase feature sets.

## Architecture (Post-Refactor v2)

### Backend (Modular Routers)
```
/app/backend/
├── server.py              # Slim entry (~65 lines)
├── database.py            # MongoDB connection (Motor)
├── auth_utils.py          # JWT, bcrypt, get_current_user, require_auth, require_subscription
├── models.py              # All Pydantic models (WorldConfig, UserProfile, etc.)
├── templates.py           # WORLD_TEMPLATES constant
├── utils.py               # AI functions, world generation, seed helpers
├── websocket_manager.py   # WebSocket ConnectionManager + notification channels
├── thumbnail.py           # Pillow-based thumbnail generation
└── routes/
    ├── auth.py            # /auth/* (register, login, logout, me, refresh) + admin seeding
    ├── users.py           # /users/* (profile, search, suggested, follow, notifications, activity feed)
    ├── worlds.py          # /worlds/* (CRUD, zones, prefabs, export, import, visibility, templates, fork, collaborators, thumbnails)
    ├── ai.py              # /ai/* (chat, auto-generate, procedural preview) — GATED by subscription
    ├── gallery.py         # /gallery/* (publish, browse with filters, like, download, fork)
    ├── reviews.py         # /reviews/* (create, list, delete)
    ├── versions.py        # /worlds/*/versions (create, list, restore)
    ├── subscription.py    # /subscription/* (plans, status, checkout, webhooks)
    └── misc.py            # WebSocket (collab + notifications), custom prefabs, analytics
```

### Frontend (Component Architecture)
```
/app/frontend/src/
├── App.js                     # Wrapper with auth gate + mobile sidebar logic
├── App.css                    # All global styles + responsive breakpoints
├── config.js                  # Zone/Prefab/Biome configs, API URL
├── contexts/
│   └── AppContext.js           # All shared state + functions (~1040 lines)
└── components/app/
    ├── AuthGate.jsx            # Full-screen login/register gate (mandatory auth)
    ├── PricingModal.jsx        # Subscription pricing dialog (3 tiers)
    ├── Header.jsx              # Header: auth, notifications, activity, search, collaborators, upgrade btn
    ├── Sidebar.jsx             # Worlds list, tools, zoom, actions, exports
    ├── AIPanel.jsx             # AI chat panel — shows gated message for free users
    ├── MapArea.jsx             # Map canvas (virtualized), terrain, properties sheets
    ├── Dialogs.jsx             # All dialogs (auth, profile, gallery, reviews, versions, user search, activity feed, collaborators)
    └── CollabChat.jsx          # Collaboration chat overlay
```

### Tech Stack
- Frontend: React 19, Tailwind CSS, Radix UI (Shadcn), Lucide icons
- Backend: FastAPI, Motor (Async MongoDB), WebSockets
- Database: MongoDB (10+ collections)
- AI: OpenAI/Anthropic/Gemini via `emergentintegrations` (Emergent LLM Key)
- Auth: Custom JWT with httpOnly cookies, bcrypt
- Payments: Stripe (via emergentintegrations)
- Hosting/Deployment: Render (Backend) and Vercel (Frontend)

## Completed Phases

### MVP (DONE) - Basic world builder, CRUD, AI integration
### P1 (DONE) - 512x512 grid, drag-to-paint, undo/redo, zoom/pan
### P2 (DONE) - Templates, exports (JSON, Hytale, Prefab, JAR), AI auto-gen
### P3 (DONE) - WebSocket collaboration, gallery, analytics, 3D preview
### P4 (DONE) - Auth, profiles, versions, reviews, visibility
### P5 (DONE) - Backend + Frontend refactoring into modular architecture
### P6 (DONE) - Enhancements: Dialog Accessibility, Social, Forking, Gallery Filtering, Notifications, Collaborators, Thumbnails
### P7 (DONE) - Polish: Full Accessibility, Mobile Responsiveness, Enhanced Collaborator UI
### P8 (DONE - April 2, 2026) - Subscription & Monetization:
1. Mandatory Auth Gate — Full-screen login/register before accessing app
2. Subscription Plans — Explorer (Free), Creator ($9/mo), Developer ($29/mo)
3. AI Feature Gating — Free users blocked from AI chat & auto-generate (403 backend + frontend UI)
4. Stripe Checkout Integration — Checkout URL generation, status verification, webhook handling
5. PayPal Checkout Integration — Sandbox order creation, capture, subscription activation
6. 2-Step Pricing Modal — Plan selection → Payment method (Stripe or PayPal)
7. Header Upgrade Button — Visible for free users, plan badge for paid users
8. AI Panel Gating UI — Shows upgrade message with crown icon instead of chat for free users
9. Manage Subscription Dialog — Shows current plan, payment history, and deliberately subtle cancel option
10. Payment History — Tracks all Stripe/PayPal transactions per user

## Subscription Tiers
| Feature | Explorer (Free) | Creator ($9/mo) | Developer ($29/mo) |
|---|---|---|---|
| Worlds | 5 max | Unlimited | Unlimited |
| Map Size | 128x128 | 512x512 | 512x512 |
| AI Generation | No | Yes | Yes |
| Collaboration | No | Yes | Yes |
| Version History | No | Yes | Yes |
| Analytics | No | No | Yes |
| Export Formats | JSON, Prefab | All | All |

## DB Collections
worlds, templates, gallery, custom_prefabs, users, login_attempts, world_versions, reviews, follows, notifications, analytics, subscriptions, payment_transactions

## Backlog
- Monitor production CORS logs for new subdomain issues

## P11 (DONE - April 2, 2026) - Architecture & Infrastructure:
1. AppContext split — AuthContext, SubscriptionContext, SocialContext extracted. useApp() facade keeps all imports unchanged
2. OG meta tags — /api/og/{token} serves HTML with og:title, og:description, og:image, twitter:card for social crawlers + client-side meta injection
3. Facebook share button added to Share dialog
4. CORS monitoring — Middleware logs rejected origins
5. Code obfuscation — GENERATE_SOURCEMAP=false for production

## P12 (DONE - April 3, 2026) - Hytale Modding API Alignment:
1. Cave System — 6 cave types (Natural, Crystal Cavern, Lava Tube, Ice Cave, Corrupted Depths, Flooded Grotto) configurable per-zone with density, depth range, and biome masks
2. Zone Discovery Config — Display name, sound event, notification settings, major zone toggle, fade in/out/duration timings — matches Hytale's ZoneDiscoveryConfig API
3. Border Transitions — Opacity gradient visualization at zone edges with configurable border_fade per zone
4. Map Layer Toggles — Show/hide caves and borders independently via toggle buttons
5. Hytale-Accurate JAR Export v2.0 — Generates real Java code using Zone, BiomePatternGenerator, CaveGenerator, ZoneDiscoveryConfig classes. Includes mod.json, placement.json, terrain.json, README.md
6. Updated config.js with CAVE_TYPES, ZONE_DEFAULT_CAVES, ZONE_DISCOVERY_DEFAULTS
7. Updated backend models with CaveConfig and ZoneDiscoveryConfig

## P10 (DONE - April 2, 2026) - Share World Feature:
1. Per-world share toggle — Owner enables/disables public sharing with unique share token
2. Share dialog — Copy link, Facebook/Twitter/Discord/Reddit social share buttons, iframe embed code
3. Public shared page — World preview with mini-map, stats, creator info, description, seed
4. Marketing CTA — "Start Building — It's Free" with feature highlights
5. Embed mode — Compact iframe-friendly view with "View on Hyt Orbis" link
6. Backend: POST /api/worlds/{id}/share (toggle), GET /api/shared/{token} (public, no auth)

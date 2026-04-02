from fastapi import FastAPI, APIRouter
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from pathlib import Path
import os
import logging

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Create the main app
app = FastAPI(title="Hyt Orbis World Builder API")

# CORS
cors_origins = os.environ.get("CORS_ORIGINS", "")
if not cors_origins or cors_origins == "*":
    origins = [
        "https://hytale-frontend-b661.vercel.app",
        "https://hytaleworldbuilder.com",
        "https://hytorbisworldbuilder.com",
        "https://www.hytaleworldbuilder.com",
        "https://www.hytorbisworldbuilder.com",
        "http://localhost:3000",
    ]
else:
    origins = [o.strip() for o in cors_origins.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger = logging.getLogger("server")

# CORS monitoring middleware
@app.middleware("http")
async def cors_monitor(request, call_next):
    origin = request.headers.get("origin")
    response = await call_next(request)
    if origin and origin not in origins:
        logger.warning(f"CORS_REJECTED origin={origin} path={request.url.path} method={request.method}")
    return response

# Create the main API router
api_router = APIRouter(prefix="/api")

# Import route modules
from routes.auth import router as auth_router, seed_admin
from routes.users import router as users_router
from routes.worlds import router as worlds_router
from routes.ai import router as ai_router
from routes.gallery import router as gallery_router
from routes.reviews import router as reviews_router
from routes.versions import router as versions_router
from routes.misc import router as misc_router
from routes.subscription import router as subscription_router
from routes.share import router as share_router

# Include all routers
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(worlds_router)
api_router.include_router(ai_router)
api_router.include_router(gallery_router)
api_router.include_router(reviews_router)
api_router.include_router(versions_router)
api_router.include_router(misc_router)
api_router.include_router(subscription_router)
api_router.include_router(share_router)


@api_router.get("/")
async def root():
    return {"message": "Hyt Orbis World Builder API", "version": "2.0.0"}


@api_router.get("/health")
async def health_check():
    from datetime import datetime, timezone
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}


# Include the API router into the app
app.include_router(api_router)


@app.on_event("startup")
async def startup_event():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.info("Starting Hyt Orbis World Builder API v2.0")
    await seed_admin()
    logger.info("Admin user seeded")

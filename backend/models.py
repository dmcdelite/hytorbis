from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import uuid


# ==================== WORLD MODELS ====================

class TerrainSettings(BaseModel):
    height_scale: float = Field(default=1.0, ge=0.1, le=3.0)
    cave_density: float = Field(default=0.5, ge=0.0, le=1.0)
    river_frequency: float = Field(default=0.3, ge=0.0, le=1.0)
    mountain_scale: float = Field(default=0.5, ge=0.0, le=1.0)
    ocean_level: float = Field(default=0.3, ge=0.0, le=1.0)


class BiomeConfig(BaseModel):
    type: str
    density: float = Field(default=0.5, ge=0.0, le=1.0)
    variation: float = Field(default=0.3, ge=0.0, le=1.0)


class CaveConfig(BaseModel):
    type: str = "natural"
    density: float = Field(default=0.5, ge=0.0, le=1.0)
    min_depth: int = Field(default=10, ge=0, le=256)
    max_depth: int = Field(default=64, ge=0, le=256)
    biome_mask: List[str] = []


class ZoneDiscoveryConfig(BaseModel):
    show_notification: bool = True
    display_name: str = ""
    sound_event: str = ""
    major_zone: bool = True
    duration: float = Field(default=5.0, ge=0.5, le=20.0)
    fade_in: float = Field(default=2.0, ge=0.0, le=10.0)
    fade_out: float = Field(default=1.5, ge=0.0, le=10.0)


class ZoneConfig(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str
    x: int
    y: int
    width: int = 1
    height: int = 1
    biomes: List[BiomeConfig] = []
    caves: List[CaveConfig] = []
    discovery: Optional[ZoneDiscoveryConfig] = None
    difficulty: int = Field(default=1, ge=1, le=10)
    border_fade: float = Field(default=0.3, ge=0.0, le=1.0)


class PrefabPlacement(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str
    x: int
    y: int
    rotation: int = 0
    scale: float = 1.0
    zone_id: Optional[str] = None


class WorldConfig(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    seed: str
    description: Optional[str] = ""
    terrain: TerrainSettings = Field(default_factory=TerrainSettings)
    zones: List[ZoneConfig] = []
    prefabs: List[PrefabPlacement] = []
    map_width: int = Field(default=64, ge=5, le=512)
    map_height: int = Field(default=64, ge=5, le=512)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    ai_provider: Optional[str] = "openai"
    thumbnail: Optional[str] = None
    owner_id: Optional[str] = None
    is_public: bool = True
    forked_from: Optional[str] = None
    collaborators: List[dict] = []


class WorldCreate(BaseModel):
    name: str
    seed: Optional[str] = None
    description: Optional[str] = ""
    map_width: int = Field(default=64, ge=5, le=512)
    map_height: int = Field(default=64, ge=5, le=512)


class WorldUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    terrain: Optional[TerrainSettings] = None
    zones: Optional[List[ZoneConfig]] = None
    prefabs: Optional[List[PrefabPlacement]] = None
    map_width: Optional[int] = Field(default=None, ge=5, le=512)
    map_height: Optional[int] = Field(default=None, ge=5, le=512)
    ai_provider: Optional[str] = None


# ==================== AI MODELS ====================

class AIMessage(BaseModel):
    role: str
    content: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AIChatRequest(BaseModel):
    world_id: str
    message: str
    provider: str = "openai"


class AIChatResponse(BaseModel):
    response: str
    suggestions: Optional[Dict[str, Any]] = None


class SeedGenerateRequest(BaseModel):
    style: Optional[str] = None


class WorldFromTemplate(BaseModel):
    name: str
    template: str
    map_width: int = Field(default=64, ge=5, le=512)
    map_height: int = Field(default=64, ge=5, le=512)


class WorldImport(BaseModel):
    config: Dict[str, Any]
    name: Optional[str] = None


class AIAutoGenerateRequest(BaseModel):
    world_id: str
    prompt: str
    provider: str = "openai"


# ==================== COLLABORATION MODELS ====================

class CollabSession(BaseModel):
    world_id: str
    user_id: str
    action: str
    data: Optional[Dict[str, Any]] = None


# ==================== AUTH MODELS ====================

class UserRegister(BaseModel):
    email: str
    password: str
    name: str


class UserLogin(BaseModel):
    email: str
    password: str


class UserProfile(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    name: str
    role: str = "user"
    avatar_url: Optional[str] = None
    bio: Optional[str] = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    worlds_count: int = 0
    published_count: int = 0
    total_downloads: int = 0
    total_likes: int = 0


class UserProfileUpdate(BaseModel):
    name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None


class PasswordReset(BaseModel):
    email: str


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str


# ==================== VERSION MODELS ====================

class WorldVersion(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    world_id: str
    version_number: int
    name: str
    description: Optional[str] = ""
    snapshot: Dict[str, Any]
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: Optional[str] = None


# ==================== REVIEW MODELS ====================

class WorldReview(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    gallery_id: str
    user_id: str
    user_name: str
    rating: int = Field(ge=1, le=5)
    comment: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ReviewCreate(BaseModel):
    gallery_id: str
    rating: int = Field(ge=1, le=5)
    comment: str


# ==================== PREFAB MODELS ====================

class CustomPrefab(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = ""
    icon: str = "cube"
    color: str = "#6B7280"
    category: str = "custom"
    size: Dict[str, int] = Field(default_factory=lambda: {"width": 1, "height": 1, "depth": 1})
    properties: Dict[str, Any] = Field(default_factory=dict)
    creator_id: Optional[str] = None
    is_public: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    tags: List[str] = []


class CustomPrefabCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    icon: str = "cube"
    color: str = "#6B7280"
    category: str = "custom"
    size: Optional[Dict[str, int]] = None
    properties: Optional[Dict[str, Any]] = None
    is_public: bool = False
    tags: List[str] = []


# ==================== GALLERY MODELS ====================

class GalleryWorld(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    world_id: str
    name: str
    description: str
    thumbnail: Optional[str] = None
    creator_name: str = "Anonymous"
    creator_id: Optional[str] = None
    tags: List[str] = []
    zone_count: int = 0
    prefab_count: int = 0
    map_size: str = "64x64"
    template_used: Optional[str] = None
    downloads: int = 0
    likes: int = 0
    views: int = 0
    featured: bool = False
    avg_rating: float = 0
    review_count: int = 0
    published_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class GalleryPublish(BaseModel):
    world_id: str
    description: str
    creator_name: str = "Anonymous"
    tags: List[str] = []


class GallerySearch(BaseModel):
    query: Optional[str] = None
    tags: Optional[List[str]] = None
    sort_by: str = "recent"
    limit: int = 20
    offset: int = 0


# ==================== ANALYTICS MODELS ====================

class AnalyticsEvent(BaseModel):
    event_type: str
    world_id: Optional[str] = None
    user_id: Optional[str] = None
    data: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ==================== SOCIAL MODELS ====================

class FollowRequest(BaseModel):
    user_id: str


# ==================== WORLD PERMISSIONS MODELS ====================

class WorldCollaborator(BaseModel):
    user_id: str
    role: str = "viewer"  # "editor" or "viewer"
    added_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AddCollaboratorRequest(BaseModel):
    user_id: str
    role: str = "viewer"


class WorldForkRequest(BaseModel):
    name: Optional[str] = None

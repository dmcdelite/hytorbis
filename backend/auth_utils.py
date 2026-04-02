import os
import jwt
import bcrypt
from datetime import datetime, timezone, timedelta
from typing import Optional
from fastapi import Request, HTTPException
from bson import ObjectId
from database import db

JWT_SECRET = os.environ.get('JWT_SECRET', 'fallback-secret-key-change-in-production')
JWT_ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def create_access_token(user_id: str, email: str) -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=60),
        "type": "access"
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def create_refresh_token(user_id: str) -> str:
    payload = {
        "sub": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(days=7),
        "type": "refresh"
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


async def get_current_user(request: Request) -> Optional[dict]:
    token = request.cookies.get("access_token")
    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
    if not token:
        return None
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "access":
            return None
        user = await db.users.find_one({"_id": ObjectId(payload["sub"])})
        if not user:
            return None
        user["id"] = str(user["_id"])
        del user["_id"]
        user.pop("password_hash", None)
        return user
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None


async def require_auth(request: Request) -> dict:
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


async def require_subscription(request: Request, feature: str = "ai") -> dict:
    user = await require_auth(request)

    # Admins bypass all subscription gates
    if user.get("role") == "admin":
        user["subscription_plan"] = "developer"
        return user

    sub = await db.subscriptions.find_one(
        {"user_id": user["id"], "status": "active"}, {"_id": 0}
    )
    plan_id = sub.get("plan_id", "free") if sub else "free"
    user["subscription_plan"] = plan_id

    PLAN_FEATURES = {
        "free": {"ai": False, "collab": False, "analytics": False, "version_history": False},
        "creator": {"ai": True, "collab": True, "analytics": False, "version_history": True},
        "developer": {"ai": True, "collab": True, "analytics": True, "version_history": True},
    }
    plan_perms = PLAN_FEATURES.get(plan_id, PLAN_FEATURES["free"])
    if not plan_perms.get(feature, False):
        raise HTTPException(
            status_code=403,
            detail=f"Upgrade to a paid plan to access {feature} features"
        )
    return user

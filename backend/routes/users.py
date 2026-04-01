from fastapi import APIRouter, HTTPException, Request
from bson import ObjectId
from datetime import datetime, timezone

from database import db
from auth_utils import get_current_user, require_auth
from models import UserProfileUpdate, FollowRequest

router = APIRouter()


@router.get("/users/{user_id}/profile")
async def get_user_profile(user_id: str):
    user = await db.users.find_one({"_id": ObjectId(user_id)}, {"password_hash": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    worlds_count = await db.worlds.count_documents({"owner_id": user_id})
    published = await db.gallery.find({"creator_id": user_id}).to_list(100)
    published_count = len(published)
    total_downloads = sum(p.get("downloads", 0) for p in published)
    total_likes = sum(p.get("likes", 0) for p in published)
    followers_count = await db.follows.count_documents({"following_id": user_id})
    following_count = await db.follows.count_documents({"follower_id": user_id})

    return {
        "id": str(user["_id"]), "name": user.get("name", ""),
        "bio": user.get("bio", ""), "avatar_url": user.get("avatar_url"),
        "role": user.get("role", "user"), "created_at": user.get("created_at"),
        "worlds_count": worlds_count, "published_count": published_count,
        "total_downloads": total_downloads, "total_likes": total_likes,
        "followers_count": followers_count, "following_count": following_count
    }


@router.put("/users/profile")
async def update_profile(profile: UserProfileUpdate, request: Request):
    user = await require_auth(request)
    update_data = {}
    if profile.name is not None:
        update_data["name"] = profile.name
    if profile.bio is not None:
        update_data["bio"] = profile.bio
    if profile.avatar_url is not None:
        update_data["avatar_url"] = profile.avatar_url
    if update_data:
        await db.users.update_one({"_id": ObjectId(user["id"])}, {"$set": update_data})
    return {"message": "Profile updated"}


@router.get("/users/{user_id}/worlds")
async def get_user_worlds(user_id: str):
    worlds = await db.worlds.find({"owner_id": user_id, "is_public": True}, {"_id": 0}).to_list(50)
    return {"worlds": worlds}


@router.get("/users/{user_id}/published")
async def get_user_published(user_id: str):
    entries = await db.gallery.find({"creator_id": user_id}, {"_id": 0}).to_list(50)
    return {"entries": entries}


# ==================== SOCIAL: FOLLOW ====================

@router.post("/users/{user_id}/follow")
async def follow_user(user_id: str, request: Request):
    current = await require_auth(request)
    if current["id"] == user_id:
        raise HTTPException(status_code=400, detail="Cannot follow yourself")

    target = await db.users.find_one({"_id": ObjectId(user_id)})
    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    existing = await db.follows.find_one({"follower_id": current["id"], "following_id": user_id})
    if existing:
        raise HTTPException(status_code=400, detail="Already following this user")

    await db.follows.insert_one({
        "follower_id": current["id"],
        "following_id": user_id,
        "created_at": datetime.now(timezone.utc).isoformat()
    })

    # Create notification
    await db.notifications.insert_one({
        "user_id": user_id,
        "type": "new_follower",
        "data": {"follower_id": current["id"], "follower_name": current.get("name", "Someone")},
        "read": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    })

    return {"message": "Followed"}


@router.post("/users/{user_id}/unfollow")
async def unfollow_user(user_id: str, request: Request):
    current = await require_auth(request)
    result = await db.follows.delete_one({"follower_id": current["id"], "following_id": user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=400, detail="Not following this user")
    return {"message": "Unfollowed"}


@router.get("/users/{user_id}/followers")
async def get_followers(user_id: str):
    follows = await db.follows.find({"following_id": user_id}, {"_id": 0}).to_list(100)
    follower_ids = [f["follower_id"] for f in follows]
    users = []
    for fid in follower_ids:
        u = await db.users.find_one({"_id": ObjectId(fid)}, {"password_hash": 0})
        if u:
            users.append({"id": str(u["_id"]), "name": u.get("name", ""), "avatar_url": u.get("avatar_url")})
    return {"followers": users}


@router.get("/users/{user_id}/following")
async def get_following(user_id: str):
    follows = await db.follows.find({"follower_id": user_id}, {"_id": 0}).to_list(100)
    following_ids = [f["following_id"] for f in follows]
    users = []
    for fid in following_ids:
        u = await db.users.find_one({"_id": ObjectId(fid)}, {"password_hash": 0})
        if u:
            users.append({"id": str(u["_id"]), "name": u.get("name", ""), "avatar_url": u.get("avatar_url")})
    return {"following": users}


@router.get("/users/{user_id}/is-following")
async def check_following(user_id: str, request: Request):
    current = await get_current_user(request)
    if not current:
        return {"is_following": False}
    existing = await db.follows.find_one({"follower_id": current["id"], "following_id": user_id})
    return {"is_following": existing is not None}


# ==================== NOTIFICATIONS ====================

@router.get("/notifications")
async def get_notifications(request: Request):
    user = await require_auth(request)
    notifications = await db.notifications.find(
        {"user_id": user["id"]}, {"_id": 0}
    ).sort([("created_at", -1)]).limit(50).to_list(50)
    unread = await db.notifications.count_documents({"user_id": user["id"], "read": False})
    return {"notifications": notifications, "unread_count": unread}


@router.post("/notifications/read-all")
async def mark_all_read(request: Request):
    user = await require_auth(request)
    await db.notifications.update_many(
        {"user_id": user["id"], "read": False},
        {"$set": {"read": True}}
    )
    return {"message": "All notifications marked as read"}

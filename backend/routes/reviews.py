from fastapi import APIRouter, HTTPException, Request
from datetime import datetime, timezone

from database import db
from auth_utils import require_auth, get_current_user
from models import WorldReview, ReviewCreate

router = APIRouter()


@router.post("/reviews")
async def create_review(review: ReviewCreate, request: Request):
    user = await require_auth(request)
    entry = await db.gallery.find_one({"id": review.gallery_id})
    if not entry:
        raise HTTPException(status_code=404, detail="Gallery entry not found")
    existing = await db.reviews.find_one({"gallery_id": review.gallery_id, "user_id": user["id"]})
    if existing:
        raise HTTPException(status_code=400, detail="You already reviewed this world")

    review_doc = WorldReview(
        gallery_id=review.gallery_id, user_id=user["id"],
        user_name=user.get("name", "Anonymous"),
        rating=review.rating, comment=review.comment
    )
    doc = review_doc.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.reviews.insert_one(doc)

    all_reviews = await db.reviews.find({"gallery_id": review.gallery_id}).to_list(1000)
    avg_rating = sum(r["rating"] for r in all_reviews) / len(all_reviews)
    await db.gallery.update_one({"id": review.gallery_id}, {"$set": {"avg_rating": round(avg_rating, 1), "review_count": len(all_reviews)}})

    # Notify creator
    if entry.get("creator_id") and entry["creator_id"] != user["id"]:
        from routes.gallery import create_notification
        await create_notification(entry["creator_id"], "new_review", {
            "reviewer_name": user.get("name", "Someone"),
            "world_name": entry.get("name", ""), "rating": review.rating
        })

    return {"message": "Review created", "review_id": review_doc.id}


@router.get("/reviews/{gallery_id}")
async def get_reviews(gallery_id: str):
    reviews = await db.reviews.find({"gallery_id": gallery_id}, {"_id": 0}).sort([("created_at", -1)]).to_list(50)
    return {"reviews": reviews}


@router.delete("/reviews/{review_id}")
async def delete_review(review_id: str, request: Request):
    user = await require_auth(request)
    review = await db.reviews.find_one({"id": review_id})
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    if review["user_id"] != user["id"] and user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    await db.reviews.delete_one({"id": review_id})
    gallery_id = review["gallery_id"]
    all_reviews = await db.reviews.find({"gallery_id": gallery_id}).to_list(1000)
    avg_rating = sum(r["rating"] for r in all_reviews) / len(all_reviews) if all_reviews else 0
    await db.gallery.update_one({"id": gallery_id}, {"$set": {"avg_rating": round(avg_rating, 1), "review_count": len(all_reviews)}})
    return {"message": "Review deleted"}

from fastapi import APIRouter, HTTPException, Request
from datetime import datetime, timezone
from database import db
from auth_utils import get_current_user, require_auth
import os
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# Subscription Plans - defined server-side only (security)
PLANS = {
    "free": {
        "name": "Explorer",
        "price": 0.0,
        "max_map_size": 128,
        "max_worlds": 5,
        "ai_enabled": False,
        "collab_enabled": False,
        "export_formats": ["json", "prefab"],
        "version_history": False,
        "analytics": False,
    },
    "creator": {
        "name": "Creator",
        "price": 9.00,
        "max_map_size": 512,
        "max_worlds": -1,
        "ai_enabled": True,
        "collab_enabled": True,
        "export_formats": ["json", "prefab", "hytale", "jar"],
        "version_history": True,
        "analytics": False,
    },
    "developer": {
        "name": "Developer",
        "price": 29.00,
        "max_map_size": 512,
        "max_worlds": -1,
        "ai_enabled": True,
        "collab_enabled": True,
        "export_formats": ["json", "prefab", "hytale", "jar"],
        "version_history": True,
        "analytics": True,
    }
}


@router.get("/subscription/plans")
async def get_plans():
    return {"plans": PLANS}


@router.get("/subscription/status")
async def get_subscription_status(request: Request):
    user = await get_current_user(request)
    if not user:
        return {"plan": "free", "limits": PLANS["free"]}

    sub = await db.subscriptions.find_one({"user_id": user["id"], "status": "active"}, {"_id": 0})
    if not sub:
        return {"plan": "free", "limits": PLANS["free"]}

    plan_id = sub.get("plan_id", "free")
    return {
        "plan": plan_id,
        "limits": PLANS.get(plan_id, PLANS["free"]),
        "subscription": {
            "provider": sub.get("provider"),
            "started_at": sub.get("started_at"),
            "expires_at": sub.get("expires_at"),
        }
    }


@router.get("/subscription/history")
async def get_payment_history(request: Request):
    user = await require_auth(request)
    cursor = db.payment_transactions.find(
        {"user_id": user["id"]}, {"_id": 0}
    ).sort("created_at", -1).limit(20)
    transactions = await cursor.to_list(length=20)
    return {"transactions": transactions}


@router.post("/subscription/cancel")
async def cancel_subscription(request: Request):
    user = await require_auth(request)
    sub = await db.subscriptions.find_one({"user_id": user["id"], "status": "active"})
    if not sub:
        raise HTTPException(status_code=400, detail="No active subscription to cancel")

    await db.subscriptions.update_one(
        {"user_id": user["id"], "status": "active"},
        {"$set": {"status": "cancelled", "cancelled_at": datetime.now(timezone.utc).isoformat()}}
    )
    await db.users.update_one(
        {"_id": __import__("bson").ObjectId(user["id"])},
        {"$set": {"subscription_plan": "free"}}
    )
    logger.info(f"Subscription cancelled: user={user['id']}")
    return {"status": "cancelled", "plan": "free"}


@router.post("/subscription/checkout/stripe")
async def create_stripe_checkout(request: Request):
    user = await require_auth(request)
    body = await request.json()
    plan_id = body.get("plan_id")
    origin_url = body.get("origin_url")

    if plan_id not in ["creator", "developer"]:
        raise HTTPException(status_code=400, detail="Invalid plan")
    if not origin_url:
        raise HTTPException(status_code=400, detail="Origin URL required")

    plan = PLANS[plan_id]
    api_key = os.environ.get("STRIPE_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Stripe not configured")

    from emergentintegrations.payments.stripe.checkout import StripeCheckout, CheckoutSessionRequest

    host_url = str(request.base_url).rstrip("/")
    webhook_url = f"{host_url}/api/webhook/stripe"
    stripe_checkout = StripeCheckout(api_key=api_key, webhook_url=webhook_url)

    success_url = f"{origin_url}/subscription?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{origin_url}/subscription?cancelled=true"

    checkout_request = CheckoutSessionRequest(
        amount=plan["price"],
        currency="usd",
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={
            "user_id": user["id"],
            "plan_id": plan_id,
            "user_email": user.get("email", ""),
        }
    )

    session = await stripe_checkout.create_checkout_session(checkout_request)

    await db.payment_transactions.insert_one({
        "session_id": session.session_id,
        "user_id": user["id"],
        "plan_id": plan_id,
        "amount": plan["price"],
        "currency": "usd",
        "provider": "stripe",
        "payment_status": "pending",
        "metadata": {"user_email": user.get("email", "")},
        "created_at": datetime.now(timezone.utc).isoformat(),
    })

    return {"url": session.url, "session_id": session.session_id}


@router.get("/subscription/checkout/status/{session_id}")
async def check_stripe_status(session_id: str, request: Request):
    user = await require_auth(request)

    txn = await db.payment_transactions.find_one(
        {"session_id": session_id, "user_id": user["id"]}, {"_id": 0}
    )
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")

    if txn.get("payment_status") == "paid":
        return {"status": "paid", "plan_id": txn["plan_id"]}

    api_key = os.environ.get("STRIPE_API_KEY")
    from emergentintegrations.payments.stripe.checkout import StripeCheckout

    host_url = str(request.base_url).rstrip("/")
    webhook_url = f"{host_url}/api/webhook/stripe"
    stripe_checkout = StripeCheckout(api_key=api_key, webhook_url=webhook_url)

    status = await stripe_checkout.get_checkout_status(session_id)

    if status.payment_status == "paid":
        await db.payment_transactions.update_one(
            {"session_id": session_id},
            {"$set": {"payment_status": "paid", "paid_at": datetime.now(timezone.utc).isoformat()}}
        )
        await _activate_subscription(txn["user_id"], txn["plan_id"], "stripe", session_id)
        return {"status": "paid", "plan_id": txn["plan_id"]}

    if status.status == "expired":
        await db.payment_transactions.update_one(
            {"session_id": session_id},
            {"$set": {"payment_status": "expired"}}
        )
        return {"status": "expired"}

    return {"status": "pending"}


@router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    body = await request.body()
    sig = request.headers.get("Stripe-Signature", "")

    api_key = os.environ.get("STRIPE_API_KEY")
    from emergentintegrations.payments.stripe.checkout import StripeCheckout

    host_url = str(request.base_url).rstrip("/")
    webhook_url = f"{host_url}/api/webhook/stripe"
    stripe_checkout = StripeCheckout(api_key=api_key, webhook_url=webhook_url)

    try:
        event = await stripe_checkout.handle_webhook(body, sig)
        if event.payment_status == "paid":
            txn = await db.payment_transactions.find_one({"session_id": event.session_id})
            if txn and txn.get("payment_status") != "paid":
                await db.payment_transactions.update_one(
                    {"session_id": event.session_id},
                    {"$set": {"payment_status": "paid", "paid_at": datetime.now(timezone.utc).isoformat()}}
                )
                await _activate_subscription(txn["user_id"], txn["plan_id"], "stripe", event.session_id)
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Stripe webhook error: {e}")
        return {"status": "error"}


async def _activate_subscription(user_id: str, plan_id: str, provider: str, session_id: str):
    existing = await db.subscriptions.find_one({"user_id": user_id, "status": "active"})
    if existing:
        await db.subscriptions.update_one(
            {"user_id": user_id, "status": "active"},
            {"$set": {"status": "replaced", "replaced_at": datetime.now(timezone.utc).isoformat()}}
        )

    await db.subscriptions.insert_one({
        "user_id": user_id,
        "plan_id": plan_id,
        "provider": provider,
        "session_id": session_id,
        "status": "active",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": None,
    })

    await db.users.update_one(
        {"_id": __import__("bson").ObjectId(user_id)},
        {"$set": {"subscription_plan": plan_id}}
    )
    logger.info(f"Subscription activated: user={user_id}, plan={plan_id}, provider={provider}")


# ========== PAYPAL ==========

def _get_paypal_client():
    from paypalserversdk.paypal_serversdk_client import PaypalServersdkClient
    from paypalserversdk.http.auth.o_auth_2 import ClientCredentialsAuthCredentials
    from paypalserversdk.configuration import Environment

    client_id = os.environ.get("PAYPAL_CLIENT_ID")
    secret = os.environ.get("PAYPAL_SECRET")
    if not client_id or not secret:
        return None

    return PaypalServersdkClient(
        client_credentials_auth_credentials=ClientCredentialsAuthCredentials(
            o_auth_client_id=client_id,
            o_auth_client_secret=secret,
        ),
        environment=Environment.SANDBOX
    )


@router.post("/subscription/checkout/paypal")
async def create_paypal_checkout(request: Request):
    user = await require_auth(request)
    body = await request.json()
    plan_id = body.get("plan_id")
    origin_url = body.get("origin_url")

    if plan_id not in ["creator", "developer"]:
        raise HTTPException(status_code=400, detail="Invalid plan")
    if not origin_url:
        raise HTTPException(status_code=400, detail="Origin URL required")

    plan = PLANS[plan_id]
    paypal_client = _get_paypal_client()
    if not paypal_client:
        raise HTTPException(status_code=500, detail="PayPal not configured")

    from paypalserversdk.models.order_request import OrderRequest
    from paypalserversdk.models.checkout_payment_intent import CheckoutPaymentIntent
    from paypalserversdk.models.purchase_unit_request import PurchaseUnitRequest
    from paypalserversdk.models.amount_with_breakdown import AmountWithBreakdown

    order_request = OrderRequest(
        intent=CheckoutPaymentIntent.CAPTURE,
        purchase_units=[
            PurchaseUnitRequest(
                amount=AmountWithBreakdown(
                    currency_code="USD",
                    value=f"{plan['price']:.2f}"
                ),
                description=f"Hyt Orbis - {plan['name']} Plan (Monthly)",
                custom_id=f"{user['id']}|{plan_id}",
            )
        ]
    )

    result = paypal_client.orders.create_order({"body": order_request})
    order = result.body

    approve_url = None
    for link in order.links:
        if link.rel == "approve":
            approve_url = link.href
            break

    if not approve_url:
        raise HTTPException(status_code=500, detail="Failed to get PayPal approval URL")

    await db.payment_transactions.insert_one({
        "session_id": order.id,
        "user_id": user["id"],
        "plan_id": plan_id,
        "amount": plan["price"],
        "currency": "usd",
        "provider": "paypal",
        "payment_status": "pending",
        "metadata": {"user_email": user.get("email", "")},
        "created_at": datetime.now(timezone.utc).isoformat(),
    })

    return {"url": approve_url, "order_id": order.id}


@router.post("/subscription/paypal/capture/{order_id}")
async def capture_paypal_order(order_id: str, request: Request):
    user = await require_auth(request)

    txn = await db.payment_transactions.find_one(
        {"session_id": order_id, "user_id": user["id"], "provider": "paypal"}, {"_id": 0}
    )
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")

    if txn.get("payment_status") == "paid":
        return {"status": "paid", "plan_id": txn["plan_id"]}

    paypal_client = _get_paypal_client()
    if not paypal_client:
        raise HTTPException(status_code=500, detail="PayPal not configured")

    try:
        result = paypal_client.orders.capture_order({"id": order_id})
        captured = result.body

        if captured.status == "COMPLETED":
            await db.payment_transactions.update_one(
                {"session_id": order_id},
                {"$set": {"payment_status": "paid", "paid_at": datetime.now(timezone.utc).isoformat()}}
            )
            await _activate_subscription(txn["user_id"], txn["plan_id"], "paypal", order_id)
            return {"status": "paid", "plan_id": txn["plan_id"]}
        else:
            return {"status": captured.status.lower()}
    except Exception as e:
        logger.error(f"PayPal capture error: {e}")
        raise HTTPException(status_code=400, detail="Failed to capture PayPal payment")


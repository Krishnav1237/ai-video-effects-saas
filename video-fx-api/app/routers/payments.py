"""Stripe payment routes for subscription management."""

from fastapi import APIRouter, HTTPException

from app.models.schemas import CheckoutRequest, PlanTier
from app.services.stripe_service import (
    get_plans,
    get_plan,
    create_checkout_session,
    get_subscription_status,
    upgrade_subscription,
)

router = APIRouter(tags=["payments"])


@router.get("/payments/plans")
async def list_plans():
    """Get all available pricing plans."""
    plans = get_plans()
    return {"plans": [p.model_dump() for p in plans]}


@router.post("/payments/create-checkout")
async def create_checkout(request: CheckoutRequest):
    """Create a Stripe checkout session for subscription."""
    result = await create_checkout_session(
        plan=request.plan,
        success_url=request.success_url,
        cancel_url=request.cancel_url,
    )

    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result.get("error"))

    return result


@router.get("/user/subscription")
async def get_subscription():
    """Get current user subscription status."""
    status = get_subscription_status()
    return {"subscription": status.model_dump()}


@router.post("/user/subscription/upgrade")
async def upgrade_plan(tier: PlanTier):
    """Upgrade subscription tier (demo mode)."""
    plan = get_plan(tier)
    if not plan:
        raise HTTPException(status_code=400, detail="Invalid plan tier")

    status = upgrade_subscription(tier)
    return {
        "status": "upgraded",
        "subscription": status.model_dump(),
        "message": f"Upgraded to {plan.name}",
    }

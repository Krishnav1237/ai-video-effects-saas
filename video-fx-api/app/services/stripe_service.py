"""Stripe payment service for subscription management."""

import os
import stripe

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")

if STRIPE_SECRET_KEY:
    stripe.api_key = STRIPE_SECRET_KEY

from app.models.schemas import PlanTier, PricingPlan, SubscriptionStatus

PRICING_PLANS: dict[PlanTier, PricingPlan] = {
    PlanTier.FREE: PricingPlan(
        tier=PlanTier.FREE,
        name="Starter",
        price_inr=0,
        price_display="Free",
        features=[
            "5 video exports/month",
            "720p max resolution",
            "Basic AI effects",
            "500MB storage",
            "Watermarked exports",
        ],
        max_video_size_mb=100,
        max_monthly_exports=5,
        ai_models_available=["gemini"],
    ),
    PlanTier.PRO: PricingPlan(
        tier=PlanTier.PRO,
        name="Pro Creator",
        price_inr=499,
        price_display="Rs 499/mo",
        features=[
            "50 video exports/month",
            "1080p max resolution",
            "All AI effects (Gemini + Claude)",
            "5GB IPFS storage",
            "No watermark",
            "Priority processing",
        ],
        max_video_size_mb=500,
        max_monthly_exports=50,
        ai_models_available=["gemini", "claude"],
    ),
    PlanTier.ENTERPRISE: PricingPlan(
        tier=PlanTier.ENTERPRISE,
        name="Studio",
        price_inr=1999,
        price_display="Rs 1,999/mo",
        features=[
            "Unlimited exports",
            "4K resolution",
            "All AI effects + custom models",
            "50GB IPFS storage",
            "No watermark",
            "Priority processing",
            "API access",
            "Team collaboration",
        ],
        max_video_size_mb=500,
        max_monthly_exports=9999,
        ai_models_available=["gemini", "claude"],
    ),
}

# Demo subscription state
_demo_subscription = SubscriptionStatus(
    tier=PlanTier.FREE,
    active=True,
    exports_used=2,
    exports_limit=5,
    storage_used_mb=45.2,
    storage_limit_mb=500.0,
)


def get_plans() -> list[PricingPlan]:
    """Get all available pricing plans."""
    return list(PRICING_PLANS.values())


def get_plan(tier: PlanTier) -> PricingPlan | None:
    """Get a specific pricing plan."""
    return PRICING_PLANS.get(tier)


async def create_checkout_session(
    plan: PlanTier, success_url: str, cancel_url: str
) -> dict:
    """Create a Stripe checkout session."""
    plan_info = PRICING_PLANS.get(plan)
    if not plan_info:
        return {"status": "error", "error": "Invalid plan"}

    if plan == PlanTier.FREE:
        return {"status": "error", "error": "Free plan does not require payment"}

    if not STRIPE_SECRET_KEY:
        return {
            "status": "demo_mode",
            "message": "Stripe not configured. Returning demo checkout.",
            "checkout_url": f"{success_url}?session_id=demo_session_123",
            "session_id": "demo_session_123",
            "plan": plan_info.model_dump(),
        }

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": "inr",
                        "product_data": {
                            "name": f"VideoFX AI - {plan_info.name}",
                            "description": ", ".join(plan_info.features[:3]),
                        },
                        "unit_amount": plan_info.price_inr * 100,
                        "recurring": {"interval": "month"},
                    },
                    "quantity": 1,
                }
            ],
            mode="subscription",
            success_url=success_url,
            cancel_url=cancel_url,
        )
        return {
            "status": "success",
            "checkout_url": session.url,
            "session_id": session.id,
        }
    except stripe.StripeError as e:
        return {"status": "error", "error": str(e)}


def get_subscription_status() -> SubscriptionStatus:
    """Get current subscription status."""
    return _demo_subscription


def upgrade_subscription(tier: PlanTier) -> SubscriptionStatus:
    """Upgrade subscription tier (demo)."""
    global _demo_subscription
    plan = PRICING_PLANS.get(tier)
    if plan:
        _demo_subscription = SubscriptionStatus(
            tier=tier,
            active=True,
            exports_used=_demo_subscription.exports_used,
            exports_limit=plan.max_monthly_exports,
            storage_used_mb=_demo_subscription.storage_used_mb,
            storage_limit_mb=float(plan.max_video_size_mb) * 10,
        )
    return _demo_subscription

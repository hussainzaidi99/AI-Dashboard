
from fastapi import APIRouter, Depends, HTTPException
from typing import Any
from app.api import deps
from app.models.mongodb_models import User
from app.core.billing import BillingService

router = APIRouter()

@router.get("/")
async def get_user_credits(
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Get current user credit balance.
    Display credits = Active Tokens / 70,000 (Gemini 2.0 Flash Rate Logic)
    """
    billing = BillingService()
    user = await billing.get_user_for_billing(current_user.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Force a fresh recalculation in case of DB desync
    await billing.recalculate_and_save(user)
    
    # Calculate Display Credits
    # 70,000 tokens = 1 Credit
    # 700,000 tokens = 10 Credits
    display_credits = round(user.active_balance / 70000, 2)
    
    return {
        "user_id": current_user.user_id,
        "active_tokens": user.active_balance,
        "display_credits": display_credits,
        "batches": user.batches
    }

@router.post("/grant-free-tier")
async def grant_free_tier(
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    One-time grant of monthly free tier (Testing/Dev convenience)
    Ideally this happens on signup.
    """
    billing = BillingService()
    await billing.grant_initial_credits(current_user.user_id)
    return {"message": "Free tier granted"}

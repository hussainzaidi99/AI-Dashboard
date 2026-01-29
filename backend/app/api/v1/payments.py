from fastapi import APIRouter, Depends, HTTPException, Request
from typing import Any, Optional
import stripe
import os
from datetime import datetime, timezone, timedelta
from app.api import deps
from app.models.mongodb_models import User, CreditBatch, CreditBatchType
from app.core.billing import BillingService
from app.config import settings

router = APIRouter()

stripe.api_key = settings.STRIPE_SECRET_KEY

# Pricing Plan Configuration
PLANS = {
    "basic": {
        "name": "Basic Plan",
        "price": 999,  # $9.99 in cents
        "tokens": 10000000, # 10,000,000 tokens
        "expiry_days": 30,
        "type": CreditBatchType.PAID_BASIC
    },
    "premium": {
        "name": "Premium Plan",
        "price": 1999, # $19.99 in cents
        "tokens": 20000000, # 20,000,000 tokens
        "expiry_days": 90,
        "type": CreditBatchType.PAID_PREMIUM
    }
}

@router.post("/create-checkout-session")
async def create_checkout_session(
    plan_id: str,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    """
    Create a Stripe Checkout Session for a specific plan.
    """
    if plan_id not in PLANS:
        raise HTTPException(status_code=400, detail="Invalid plan selected")
    
    plan = PLANS[plan_id]
    frontend_url = settings.FRONTEND_URL
    credits_amount = round(plan["tokens"] / 70000, 2)
    
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": plan["name"],
                        "description": f"Add {credits_amount} Credits to your account",
                    },
                    "unit_amount": plan["price"],
                },
                "quantity": 1,
            }],
            mode="payment",
            success_url=f"{frontend_url}/payment/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{frontend_url}/pricing",
            metadata={
                "user_id": current_user.user_id,
                "plan_id": plan_id,
                "token_amount": str(plan["tokens"])
            }
        )
        return {"session_id": session.id, "url": session.url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/confirm")
async def confirm_payment(
    session_id: str,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    """
    Verify the Stripe Checkout Session and award credits.
    """
    try:
        # 1. Retrieve the session from Stripe
        session = stripe.checkout.Session.retrieve(session_id)
        
        if session.payment_status != "paid":
             return {
                "success": False,
                "message": f"Payment not completed. Status: {session.payment_status}"
            }

        # 2. Check if already processed (Deduplication)
        if session_id in current_user.processed_payments:
            return {
                "success": True,
                "already_processed": True,
                "message": "Payment already processed",
                "active_balance": current_user.active_balance
            }

        # 3. Extract metadata
        user_id = session.metadata.get("user_id")
        plan_id = session.metadata.get("plan_id")
        token_amount = int(session.metadata.get("token_amount", 0))

        if user_id != current_user.user_id:
            raise HTTPException(status_code=403, detail="User ID mismatch in payment metadata")

        # 4. Award credits
        plan_config = PLANS[plan_id]
        new_batch = CreditBatch(
            type=plan_config["type"],
            amount_tokens=token_amount,
            remaining_tokens=token_amount,
            expires_at=datetime.now(timezone.utc) + timedelta(days=plan_config["expiry_days"]),
            stripe_session_id=session_id
        )
        
        current_user.batches.append(new_batch)
        current_user.processed_payments.append(session_id)
        
        # Save triggers recalculation
        await current_user.save()

        return {
            "success": True,
            "message": f"Successfully added {token_amount:,} tokens!",
            "added_tokens": token_amount,
            "new_balance": current_user.active_balance
        }

    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Confirmation failed: {str(e)}")

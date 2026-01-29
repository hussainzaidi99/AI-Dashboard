
import logging
from datetime import datetime, timezone
from typing import Optional, List
from app.models.mongodb_models import User, CreditBatch, TokenUsage, CreditBatchType, logger as model_logger

logger = logging.getLogger(__name__)

class BillingService:
    """
    Handles all credit deduction, validation, and ledger management.
    """

    @staticmethod
    async def get_user_for_billing(user_id: str) -> User:
        """
        Get the user document for billing purposes (contains balance and batches)
        """
        if not user_id:
            logger.warning("get_user_for_billing called with null user_id. Defaulting to anonymous.")
            user_id = "anonymous"

        user = await User.find_one(User.user_id == user_id)
        if not user:
            # Note: In a real system, we'd expect the user to already exist via auth.
            # But for flexibility/anonymous flows, we handle it.
            logger.warning(f"User {user_id} not found in identity collection.")
            # If user doesn't exist, we can't really do billing. 
            # In consolidation mode, we return None or raise.
            return None
        return user

    @staticmethod
    async def has_sufficient_balance(user_id: str, estimated_cost: int = 1000) -> bool:
        """
        Check if user has enough tokens for an operation.
        """
        user = await BillingService.get_user_for_billing(user_id)
        if not user:
            return False
        
        # Cleanup expired batches first (lazy cleanup)
        await BillingService._cleanup_expired_batches(user)
        
        return user.active_balance >= estimated_cost

    @staticmethod
    async def deduct_tokens(user_id: str, amount: int, endpoint: str, model: str) -> None:
        """
        Deduct tokens from user's ledger using FIFO (Expiring First) strategy.
        Also records the usage transaction.
        """
        if amount <= 0:
            return

        user = await BillingService.get_user_for_billing(user_id)
        if not user:
            logger.error(f"Cannot deduct tokens: User {user_id} not found.")
            return

        # Log initial balance
        initial_balance = user.active_balance
        logger.info(f"Deducting {amount} tokens from user {user_id} (balance: {initial_balance})")
        
        # 1. Cleanup expired
        await BillingService._cleanup_expired_batches(user)

        # 2. Sort batches by expiry (Ascending) - Burn closest expiry first
        # Standardize 'now' to be timezone-aware UTC
        now = datetime.now(timezone.utc)

        # Filter out empty or expired batches just in case
        valid_batches = []
        for b in user.batches:
            expiry = b.expires_at
            if expiry.tzinfo is None:
                expiry = expiry.replace(tzinfo=timezone.utc)
            
            if b.remaining_tokens > 0 and expiry > now:
                valid_batches.append(b)
                
        valid_batches.sort(key=lambda b: b.expires_at)

        remaining_to_deduct = amount
        transaction_batches = [] # Track which batches were touched

        for batch in valid_batches:
            if remaining_to_deduct <= 0:
                break
            
            deduction = min(batch.remaining_tokens, remaining_to_deduct)
            batch.remaining_tokens -= deduction
            remaining_to_deduct -= deduction
            transaction_batches.append(batch)

        # 3. Update the main object (batches list is typically reference, but we assign back just to be safe)
        # We need to reflect the changes in the original list order or id
        # Simpler approach: Map changes back to the main list by Batch ID
        for modified_batch in transaction_batches:
            for i, original_batch in enumerate(user.batches):
                if original_batch.batch_id == modified_batch.batch_id:
                    user.batches[i] = modified_batch
                    break
        
        # 4. Save User (triggers update_and_recalculate recalc)
        await user.save()
        
        # 5. Invalidate cache after deduction
        try:
            from app.core.credit_cache import invalidate_balance_cache
            await invalidate_balance_cache(user_id)
        except Exception as e:
            logger.error(f"Failed to invalidate cache (non-critical): {str(e)}")
        
        # Log final balance
        final_balance = user.active_balance
        logger.info(f"Deduction complete. User {user_id} balance: {initial_balance} -> {final_balance}")

        # 6. Log Usage
        # Note: We record the *actual* usage here. Even if they ran out of tokens mid-way,
        # we log what was used. The negative balance handling is a policy decision for later.
        usage_log = TokenUsage(
            user_id=user_id,
            endpoint=endpoint,
            model=model,
            input_tokens=0, # We might not know split here, usually caller logs Usage details separately
            output_tokens=0, 
            total_tokens=amount
        )
        # Note: Ideally, the caller provides split. Overloading this method to handle split logging
        pass 

    @staticmethod
    async def log_usage(user_id: str, input_tokens: int, output_tokens: int, endpoint: str, model: str):
        """
        High-level method to Deduct AND Log in one go.
        """
        logger.info(f"BillingService: API Request received for user={user_id}. Tokens: Input={input_tokens}, Output={output_tokens}, Endpoint={endpoint}")
        total_tokens = input_tokens + output_tokens
        
        # Deduct
        await BillingService.deduct_tokens(user_id, total_tokens, endpoint, model)
        
        # Log
        log = TokenUsage(
            user_id=user_id,
            endpoint=endpoint,
            model=model,
            input_tokens=input_tokens, 
            output_tokens=output_tokens,
            total_tokens=total_tokens
        )
        await log.save()


    @staticmethod
    async def _cleanup_expired_batches(user: User):
        """
        Helper to zero out expired batches.
        Does NOT save (caller must save).
        """
        now = datetime.now(timezone.utc)
        changed = False
        for batch in user.batches:
            expiry = batch.expires_at
            if expiry.tzinfo is None:
                expiry = expiry.replace(tzinfo=timezone.utc)
                
            if expiry < now and batch.remaining_tokens > 0:
                batch.remaining_tokens = 0
                changed = True
        
        if changed:
            # We don't save here to batch writes, but we could.
            pass

    @staticmethod
    async def grant_initial_credits(user_id: str):
        """
        Grant initial free tier credits (10 credits / 700k tokens).
        Idempotent - only grants if user has no existing monthly free batch.
        """
        from datetime import timedelta
        
        user = await BillingService.get_user_for_billing(user_id)
        if not user:
            return
        
        # Check if user already has a monthly free batch
        has_monthly_free = any(
            batch.type == CreditBatchType.MONTHLY_FREE 
            for batch in user.batches
        )
        
        if has_monthly_free:
            logger.info(f"User {user_id} already has monthly free credits, skipping grant")
            return
        
        # Grant new monthly free tier batch
        new_batch = CreditBatch(
            type=CreditBatchType.MONTHLY_FREE,
            amount_tokens=700000,  # 10 credits
            remaining_tokens=700000,
            expires_at=datetime.now(timezone.utc) + timedelta(days=30)
        )
        user.batches.append(new_batch)
        
        # Save User (triggers recalculate)
        await user.save()
        
        logger.info(f"Granted 700k tokens (10 credits) to user {user_id}")

    @staticmethod
    async def recalculate_and_save(user: User) -> User:
        """
        Force a fresh recalculation of active_balance and save to DB.
        Useful for fixing any desyncs.
        """
        user.update_and_recalculate()
        await user.save()
        return user

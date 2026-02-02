from celery import Task
from typing import Optional, List
from src.celery_app import celery_app
from src.database import AsyncSessionLocal
from src.repositories.product import ProductRepository
from src.repositories.batch import BatchRepository


@celery_app.task(bind=True, max_retries=3)
def aggregate_products_batch(
    self: Task,
    batch_id: int,
    unique_codes: List[str],
    user_id: Optional[int] = None
) -> dict:
    """
    Асинхронная массовая аггрегация продукции.
    
    Args:
        batch_id: ID партии
        unique_codes: Список уникальных кодов для аггрегации
        user_id: ID пользователя (для уведомлений)
    
    Returns:
        {
            "success": True,
            "total": 1000,
            "aggregated": 950,
            "failed": 50,
            "errors": [...]
        }
    """
    import asyncio
    
    async def _aggregate():
        async with AsyncSessionLocal() as session:
            await session.begin()
            try:
                # Verify batch exists
                batch_repo = BatchRepository(session)
                batch = await batch_repo.get_by_id(batch_id)
                if not batch:
                    return {
                        "success": False,
                        "error": f"Batch {batch_id} not found"
                    }
                
                # Bulk aggregate
                product_repo = ProductRepository(session)
                result = await product_repo.bulk_aggregate(batch_id, unique_codes)
                
                await session.commit()
                
                # Send webhook events for aggregated products
                from src.services.webhook_service import webhook_service
                from src.repositories.webhook import WebhookRepository
                from src.tasks.webhooks import send_webhook_delivery
                
                webhook_repo = WebhookRepository(session)
                subscriptions = await webhook_repo.get_active_subscriptions_for_event("product_aggregated")
                
                # Get aggregated product codes
                aggregated_codes = [code for code in unique_codes if code not in [e.get("code") for e in result.get("errors", [])]]
                
                for subscription in subscriptions:
                    # Send event for batch aggregation completion
                    payload = webhook_service.create_webhook_payload("product_aggregated", {
                        "batch_id": batch_id,
                        "batch_number": batch.batch_number,
                        "total": result["total"],
                        "aggregated": result["aggregated"],
                        "failed": result["failed"]
                    })
                    delivery = await webhook_repo.create_delivery(
                        subscription_id=subscription.id,
                        event_type="product_aggregated",
                        payload=payload
                    )
                    send_webhook_delivery.delay(delivery.id)
                
                # Update progress
                self.update_state(
                    state="PROGRESS",
                    meta={
                        "current": result["aggregated"],
                        "total": result["total"],
                        "progress": int((result["aggregated"] / result["total"]) * 100) if result["total"] > 0 else 0
                    }
                )
                
                return result
            except Exception as e:
                await session.rollback()
                raise e
    
    try:
        result = asyncio.run(_aggregate())
        return result
    except Exception as exc:
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)

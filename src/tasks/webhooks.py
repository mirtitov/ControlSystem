from celery import Task
from src.celery_app import celery_app
from src.database import AsyncSessionLocal
from src.repositories.webhook import WebhookRepository
from src.models.webhook import WebhookDelivery
from src.services.webhook_service import webhook_service
import asyncio


@celery_app.task(bind=True, max_retries=3)
def send_webhook_delivery(self: Task, delivery_id: int):
    """
    Отправка webhook с retry логикой.

    Args:
        delivery_id: ID записи WebhookDelivery
    """

    async def _send():
        async with AsyncSessionLocal() as session:
            await session.begin()
            try:
                webhook_repo = WebhookRepository(session)
                delivery = await session.get(WebhookDelivery, delivery_id)

                if not delivery:
                    return {"success": False, "error": "Delivery not found"}

                subscription = delivery.subscription

                if not subscription.is_active:
                    return {"success": False, "error": "Subscription is inactive"}

                # Send webhook
                (
                    success,
                    status_code,
                    response_body,
                    error_message,
                ) = await webhook_service.send_webhook(
                    url=subscription.url,
                    payload=delivery.payload,
                    secret_key=subscription.secret_key,
                    timeout=subscription.timeout,
                )

                # Update delivery
                if success:
                    await webhook_repo.update_delivery(
                        delivery_id=delivery_id,
                        status="success",
                        response_status=status_code,
                        response_body=response_body,
                    )
                else:
                    await webhook_repo.update_delivery(
                        delivery_id=delivery_id,
                        status="failed",
                        response_status=status_code,
                        response_body=response_body,
                        error_message=error_message,
                    )

                await session.commit()

                return {
                    "success": success,
                    "status_code": status_code,
                    "error": error_message,
                }

            except Exception as e:
                await session.rollback()
                raise e

    try:
        result = asyncio.run(_send())

        # If failed and retries available, retry
        if not result.get("success") and self.request.retries < self.max_retries:
            raise self.retry(exc=Exception(result.get("error", "Unknown error")))

        return result
    except Exception as exc:
        raise self.retry(exc=exc, countdown=2**self.request.retries)

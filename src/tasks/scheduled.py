from datetime import datetime

from src.celery_app import celery_app
from src.database import AsyncSessionLocal
from src.repositories.batch import BatchRepository
from src.services.cache_service import cache_service
from src.services.minio_service import minio_service
from src.tasks.webhooks import send_webhook_delivery


@celery_app.task
def auto_close_expired_batches():
    """
    Закрывает партии, у которых shift_end < now().
    Запускается: каждый день в 01:00
    """
    import asyncio

    async def _close():
        async with AsyncSessionLocal() as session:
            await session.begin()
            try:
                batch_repo = BatchRepository(session)
                expired_batches = await batch_repo.get_expired_batches()

                closed_count = 0
                for batch in expired_batches:
                    batch.is_closed = True
                    batch.closed_at = datetime.utcnow()
                    closed_count += 1

                await session.commit()
                return {"closed_count": closed_count}
            except Exception as e:
                await session.rollback()
                raise e

    return asyncio.run(_close())


@celery_app.task
def cleanup_old_files():
    """
    Удаляет файлы старше 30 дней из MinIO.
    Запускается: каждый день в 02:00
    """
    from datetime import timedelta

    cutoff_date = datetime.utcnow() - timedelta(days=30)
    deleted_count = 0

    for bucket in ["reports", "exports", "imports"]:
        try:
            files = minio_service.list_files(bucket)
            for file_obj in files:
                if file_obj.last_modified < cutoff_date:
                    minio_service.delete_file(bucket, file_obj.object_name)
                    deleted_count += 1
        except Exception as e:
            print(f"Error cleaning bucket {bucket}: {e}")

    return {"deleted_count": deleted_count}


@celery_app.task
def update_cached_statistics():
    """
    Обновляет кэшированную статистику в Redis.
    Запускается: каждые 5 минут
    """
    import asyncio

    async def _update():
        async with AsyncSessionLocal() as session:
            from sqlalchemy import func, select

            from src.models.batch import Batch
            from src.models.product import Product

            # Get statistics
            total_batches_result = await session.execute(select(func.count(Batch.id)))
            total_batches = total_batches_result.scalar() or 0

            active_batches_result = await session.execute(
                select(func.count(Batch.id)).where(~Batch.is_closed)
            )
            active_batches = active_batches_result.scalar() or 0

            total_products_result = await session.execute(select(func.count(Product.id)))
            total_products = total_products_result.scalar() or 0

            aggregated_products_result = await session.execute(
                select(func.count(Product.id)).where(Product.is_aggregated)
            )
            aggregated_products = aggregated_products_result.scalar() or 0

            stats = {
                "total_batches": total_batches,
                "active_batches": active_batches,
                "closed_batches": total_batches - active_batches,
                "total_products": total_products,
                "aggregated_products": aggregated_products,
                "aggregation_rate": (aggregated_products / total_products * 100)
                if total_products > 0
                else 0.0,
                "cached_at": datetime.utcnow().isoformat() + "Z",
            }

            await cache_service.set("dashboard_stats", stats, ttl=300)
            return stats

    return asyncio.run(_update())


@celery_app.task
def retry_failed_webhooks():
    """
    Повторная отправка неудачных webhook delivery.
    Запускается: каждые 15 минут
    """
    import asyncio

    async def _retry():
        async with AsyncSessionLocal() as session:
            from src.repositories.webhook import WebhookRepository

            webhook_repo = WebhookRepository(session)
            failed_deliveries = await webhook_repo.get_failed_deliveries(limit=100)

            retried_count = 0
            for delivery in failed_deliveries:
                if delivery.attempts < delivery.subscription.retry_count:
                    # Send webhook task
                    send_webhook_delivery.delay(delivery.id)
                    retried_count += 1

            return {"retried_count": retried_count}

    return asyncio.run(_retry())

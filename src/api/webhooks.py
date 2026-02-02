from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from src.database import get_db
from src.repositories.webhook import WebhookRepository
from src.schemas.webhook import (
    WebhookSubscriptionCreate,
    WebhookSubscriptionUpdate,
    WebhookSubscriptionResponse,
    WebhookDeliveryResponse,
)

router = APIRouter(prefix="/api/v1/webhooks", tags=["webhooks"])


@router.post("", response_model=WebhookSubscriptionResponse, status_code=201)
async def create_webhook(
    data: WebhookSubscriptionCreate,
    db: AsyncSession = Depends(get_db)
):
    """Создание webhook подписки"""
    webhook_repo = WebhookRepository(db)
    subscription = await webhook_repo.create_subscription(data)
    await db.commit()
    return subscription


@router.get("", response_model=dict)
async def list_webhooks(
    is_active: Optional[bool] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Список webhook подписок"""
    webhook_repo = WebhookRepository(db)
    subscriptions = await webhook_repo.list_subscriptions(is_active=is_active)
    
    return {
        "items": subscriptions,
        "total": len(subscriptions)
    }


@router.get("/{webhook_id}", response_model=WebhookSubscriptionResponse)
async def get_webhook(
    webhook_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Получение webhook подписки"""
    webhook_repo = WebhookRepository(db)
    subscription = await webhook_repo.get_subscription(webhook_id)
    
    if not subscription:
        raise HTTPException(status_code=404, detail="Webhook subscription not found")
    
    return subscription


@router.patch("/{webhook_id}", response_model=WebhookSubscriptionResponse)
async def update_webhook(
    webhook_id: int,
    data: WebhookSubscriptionUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Обновление webhook подписки"""
    webhook_repo = WebhookRepository(db)
    subscription = await webhook_repo.update_subscription(webhook_id, data)
    
    if not subscription:
        raise HTTPException(status_code=404, detail="Webhook subscription not found")
    
    await db.commit()
    return subscription


@router.delete("/{webhook_id}", status_code=204)
async def delete_webhook(
    webhook_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Удаление webhook подписки"""
    webhook_repo = WebhookRepository(db)
    success = await webhook_repo.delete_subscription(webhook_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Webhook subscription not found")
    
    await db.commit()
    return None


@router.get("/{webhook_id}/deliveries", response_model=dict)
async def get_webhook_deliveries(
    webhook_id: int,
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db)
):
    """История доставок webhook"""
    webhook_repo = WebhookRepository(db)
    
    # Verify subscription exists
    subscription = await webhook_repo.get_subscription(webhook_id)
    if not subscription:
        raise HTTPException(status_code=404, detail="Webhook subscription not found")
    
    deliveries = await webhook_repo.get_deliveries_by_subscription(webhook_id, limit=limit)
    
    return {
        "items": deliveries,
        "total": len(deliveries)
    }

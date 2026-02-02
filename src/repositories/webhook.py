from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Optional
from src.models.webhook import WebhookSubscription, WebhookDelivery
from src.schemas.webhook import WebhookSubscriptionCreate, WebhookSubscriptionUpdate


class WebhookRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_subscription(
        self, data: WebhookSubscriptionCreate
    ) -> WebhookSubscription:
        subscription = WebhookSubscription(**data.model_dump())
        self.session.add(subscription)
        await self.session.flush()
        await self.session.refresh(subscription)
        return subscription

    async def get_subscription(
        self, subscription_id: int
    ) -> WebhookSubscription | None:
        result = await self.session.execute(
            select(WebhookSubscription).where(WebhookSubscription.id == subscription_id)
        )
        return result.scalar_one_or_none()

    async def list_subscriptions(
        self, is_active: Optional[bool] = None
    ) -> List[WebhookSubscription]:
        query = select(WebhookSubscription)
        if is_active is not None:
            query = query.where(WebhookSubscription.is_active == is_active)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update_subscription(
        self, subscription_id: int, data: WebhookSubscriptionUpdate
    ) -> WebhookSubscription | None:
        subscription = await self.get_subscription(subscription_id)
        if not subscription:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(subscription, key, value)

        await self.session.flush()
        await self.session.refresh(subscription)
        return subscription

    async def delete_subscription(self, subscription_id: int) -> bool:
        subscription = await self.get_subscription(subscription_id)
        if not subscription:
            return False

        await self.session.delete(subscription)
        await self.session.flush()
        return True

    async def get_active_subscriptions_for_event(
        self, event_type: str
    ) -> List[WebhookSubscription]:
        """Get all active subscriptions that listen to a specific event"""
        result = await self.session.execute(
            select(WebhookSubscription).where(
                and_(
                    WebhookSubscription.is_active,
                    WebhookSubscription.events.contains([event_type]),
                )
            )
        )
        return list(result.scalars().all())

    async def create_delivery(
        self,
        subscription_id: int,
        event_type: str,
        payload: dict,
        status: str = "pending",
    ) -> WebhookDelivery:
        delivery = WebhookDelivery(
            subscription_id=subscription_id,
            event_type=event_type,
            payload=payload,
            status=status,
        )
        self.session.add(delivery)
        await self.session.flush()
        await self.session.refresh(delivery)
        return delivery

    async def get_failed_deliveries(self, limit: int = 100) -> List[WebhookDelivery]:
        """Get failed deliveries for retry"""
        result = await self.session.execute(
            select(WebhookDelivery)
            .where(
                and_(WebhookDelivery.status == "failed", WebhookDelivery.attempts < 3)
            )
            .limit(limit)
        )
        return list(result.scalars().all())

    async def update_delivery(
        self,
        delivery_id: int,
        status: str,
        response_status: Optional[int] = None,
        response_body: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> WebhookDelivery | None:
        delivery = await self.session.get(WebhookDelivery, delivery_id)
        if not delivery:
            return None

        delivery.status = status
        delivery.attempts += 1
        if response_status:
            delivery.response_status = response_status
        if response_body:
            delivery.response_body = response_body
        if error_message:
            delivery.error_message = error_message

        if status == "success":
            from datetime import datetime

            delivery.delivered_at = datetime.utcnow()

        await self.session.flush()
        await self.session.refresh(delivery)
        return delivery

    async def get_deliveries_by_subscription(
        self, subscription_id: int, limit: int = 100
    ) -> List[WebhookDelivery]:
        result = await self.session.execute(
            select(WebhookDelivery)
            .where(WebhookDelivery.subscription_id == subscription_id)
            .order_by(WebhookDelivery.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

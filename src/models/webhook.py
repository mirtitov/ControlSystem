from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, JSON, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import ARRAY as PG_ARRAY
from src.database import Base


class WebhookSubscription(Base):
    __tablename__ = "webhook_subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, nullable=False)
    events = Column(PG_ARRAY(String), nullable=False)
    secret_key = Column(String, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    retry_count = Column(Integer, default=3, nullable=False)
    timeout = Column(Integer, default=10, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    deliveries = relationship("WebhookDelivery", back_populates="subscription", cascade="all, delete-orphan")


class WebhookDelivery(Base):
    __tablename__ = "webhook_deliveries"

    id = Column(Integer, primary_key=True, index=True)
    subscription_id = Column(Integer, ForeignKey("webhook_subscriptions.id"), nullable=False)
    event_type = Column(String, nullable=False)
    payload = Column(JSON, nullable=False)
    
    status = Column(String, nullable=False)  # "pending", "success", "failed"
    attempts = Column(Integer, default=0, nullable=False)
    response_status = Column(Integer, nullable=True)
    response_body = Column(String, nullable=True)
    error_message = Column(String, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    subscription = relationship("WebhookSubscription", back_populates="deliveries")

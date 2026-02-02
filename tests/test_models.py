"""
Тесты для моделей SQLAlchemy
"""

import sys
import os
from datetime import datetime, date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models.work_center import WorkCenter
from src.models.batch import Batch
from src.models.product import Product
from src.models.webhook import WebhookSubscription, WebhookDelivery


def test_work_center_model():
    """Тест модели WorkCenter"""
    work_center = WorkCenter(identifier="RC-001", name="Цех №1")

    assert work_center.identifier == "RC-001"
    assert work_center.name == "Цех №1"
    assert hasattr(work_center, "id")
    assert hasattr(work_center, "created_at")
    print("✅ WorkCenter model structure is correct")


def test_batch_model():
    """Тест модели Batch"""
    batch = Batch(
        is_closed=False,
        task_description="Тестовое задание",
        work_center_id=1,
        shift="1 смена",
        team="Бригада Иванова",
        batch_number=12345,
        batch_date=date(2024, 1, 30),
        nomenclature="Болт М10",
        ekn_code="EKN-123",
        shift_start=datetime(2024, 1, 30, 8, 0, 0),
        shift_end=datetime(2024, 1, 30, 20, 0, 0),
    )

    assert batch.batch_number == 12345
    assert not batch.is_closed
    assert batch.closed_at is None
    assert hasattr(batch, "products")
    print("✅ Batch model structure is correct")


def test_product_model():
    """Тест модели Product"""
    product = Product(unique_code="TEST-CODE-123", batch_id=1, is_aggregated=False)

    assert product.unique_code == "TEST-CODE-123"
    assert product.batch_id == 1
    assert not product.is_aggregated
    assert product.aggregated_at is None
    print("✅ Product model structure is correct")


def test_webhook_subscription_model():
    """Тест модели WebhookSubscription"""
    subscription = WebhookSubscription(
        url="https://example.com/webhook",
        events=["batch_created"],
        secret_key="secret123",
        is_active=True,
        retry_count=3,
        timeout=10,
    )

    assert subscription.url == "https://example.com/webhook"
    assert len(subscription.events) == 1
    assert subscription.is_active
    print("✅ WebhookSubscription model structure is correct")


def test_webhook_delivery_model():
    """Тест модели WebhookDelivery"""
    delivery = WebhookDelivery(
        subscription_id=1,
        event_type="batch_created",
        payload={"test": "data"},
        status="pending",
        attempts=0,
    )

    assert delivery.event_type == "batch_created"
    assert delivery.status == "pending"
    assert delivery.attempts == 0
    print("✅ WebhookDelivery model structure is correct")


if __name__ == "__main__":
    print("=" * 50)
    print("Running model structure tests...")
    print("=" * 50)

    try:
        test_work_center_model()
        test_batch_model()
        test_product_model()
        test_webhook_subscription_model()
        test_webhook_delivery_model()

        print("=" * 50)
        print("✅ All model tests passed!")
        print("=" * 50)
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)

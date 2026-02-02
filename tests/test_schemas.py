"""
Тесты для Pydantic схем
"""

import sys
import os
from datetime import datetime, date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.schemas.batch import BatchCreate, BatchCreateRequest
from src.schemas.product import ProductCreate
from src.schemas.webhook import WebhookSubscriptionCreate


def test_batch_create_request():
    """Тест создания BatchCreateRequest"""
    data = {
        "СтатусЗакрытия": False,
        "ПредставлениеЗаданияНаСмену": "Тестовое задание",
        "РабочийЦентр": "Цех №1",
        "Смена": "1 смена",
        "Бригада": "Бригада Иванова",
        "НомерПартии": 12345,
        "ДатаПартии": "2024-01-30",
        "Номенклатура": "Болт М10",
        "КодЕКН": "EKN-123",
        "ИдентификаторРЦ": "RC-001",
        "ДатаВремяНачалаСмены": "2024-01-30T08:00:00",
        "ДатаВремяОкончанияСмены": "2024-01-30T20:00:00",
    }

    request = BatchCreateRequest(**data)
    assert not request.СтатусЗакрытия
    assert request.НомерПартии == 12345
    assert request.ДатаПартии == date(2024, 1, 30)
    print("✅ BatchCreateRequest validation works")


def test_batch_create():
    """Тест создания BatchCreate"""
    data = {
        "is_closed": False,
        "task_description": "Тестовое задание",
        "work_center_id": 1,
        "shift": "1 смена",
        "team": "Бригада Иванова",
        "batch_number": 12345,
        "batch_date": date(2024, 1, 30),
        "nomenclature": "Болт М10",
        "ekn_code": "EKN-123",
        "shift_start": datetime(2024, 1, 30, 8, 0, 0),
        "shift_end": datetime(2024, 1, 30, 20, 0, 0),
    }

    batch = BatchCreate(**data)
    assert batch.batch_number == 12345
    assert not batch.is_closed
    print("✅ BatchCreate validation works")


def test_product_create():
    """Тест создания ProductCreate"""
    data = {"unique_code": "TEST-CODE-123", "batch_id": 1}

    product = ProductCreate(**data)
    assert product.unique_code == "TEST-CODE-123"
    assert product.batch_id == 1
    print("✅ ProductCreate validation works")


def test_webhook_subscription_create():
    """Тест создания WebhookSubscriptionCreate"""
    data = {
        "url": "https://example.com/webhook",
        "events": ["batch_created", "batch_closed"],
        "secret_key": "secret123",
        "retry_count": 3,
        "timeout": 10,
    }

    subscription = WebhookSubscriptionCreate(**data)
    assert subscription.url == "https://example.com/webhook"
    assert len(subscription.events) == 2
    print("✅ WebhookSubscriptionCreate validation works")


if __name__ == "__main__":
    print("=" * 50)
    print("Running schema validation tests...")
    print("=" * 50)

    try:
        test_batch_create_request()
        test_batch_create()
        test_product_create()
        test_webhook_subscription_create()

        print("=" * 50)
        print("✅ All schema tests passed!")
        print("=" * 50)
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)

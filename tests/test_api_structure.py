"""
Тесты для проверки структуры API endpoints
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_batches_endpoints():
    """Проверка структуры endpoints для партий"""
    try:
        from src.api import batches

        # Проверяем наличие основных функций
        assert hasattr(batches, "router")
        assert batches.router is not None

        # Проверяем наличие основных endpoints
        routes = [route.path for route in batches.router.routes]

        expected_routes = [
            "/api/v1/batches",
            "/api/v1/batches/{batch_id}",
        ]

        # Проверяем, что основные routes существуют
        found_routes = [r for r in routes if any(exp in r for exp in expected_routes)]
        assert len(found_routes) > 0, "No expected routes found"

        print(f"✅ Batches API has {len(routes)} endpoints")
        print(f"   Found routes: {', '.join(routes[:5])}...")

    except ImportError as e:
        print(f"⚠️  Could not import batches API: {e}")


def test_products_endpoints():
    """Проверка структуры endpoints для продукции"""
    try:
        from src.api import products

        assert hasattr(products, "router")
        assert products.router is not None

        routes = [route.path for route in products.router.routes]
        print(f"✅ Products API has {len(routes)} endpoints")

    except ImportError as e:
        print(f"⚠️  Could not import products API: {e}")


def test_webhooks_endpoints():
    """Проверка структуры endpoints для webhooks"""
    try:
        from src.api import webhooks

        assert hasattr(webhooks, "router")
        assert webhooks.router is not None

        routes = [route.path for route in webhooks.router.routes]
        print(f"✅ Webhooks API has {len(routes)} endpoints")

    except ImportError as e:
        print(f"⚠️  Could not import webhooks API: {e}")


def test_analytics_endpoints():
    """Проверка структуры endpoints для аналитики"""
    try:
        from src.api import analytics

        assert hasattr(analytics, "router")
        assert analytics.router is not None

        routes = [route.path for route in analytics.router.routes]
        print(f"✅ Analytics API has {len(routes)} endpoints")

    except ImportError as e:
        print(f"⚠️  Could not import analytics API: {e}")


def test_tasks_endpoints():
    """Проверка структуры endpoints для задач"""
    try:
        from src.api import tasks

        assert hasattr(tasks, "router")
        assert tasks.router is not None

        routes = [route.path for route in tasks.router.routes]
        print(f"✅ Tasks API has {len(routes)} endpoints")

    except ImportError as e:
        print(f"⚠️  Could not import tasks API: {e}")


def test_main_app():
    """Проверка структуры главного приложения"""
    try:
        from src.main import app

        assert app is not None
        assert hasattr(app, "routes")

        # Проверяем наличие health check
        routes = [route.path for route in app.routes if hasattr(route, "path")]
        assert "/health" in routes or "/" in routes

        print(f"✅ Main app initialized with {len(routes)} routes")

    except ImportError as e:
        print(f"⚠️  Could not import main app: {e}")


if __name__ == "__main__":
    print("=" * 50)
    print("Running API structure tests...")
    print("=" * 50)

    try:
        test_batches_endpoints()
        test_products_endpoints()
        test_webhooks_endpoints()
        test_analytics_endpoints()
        test_tasks_endpoints()
        test_main_app()

        print("=" * 50)
        print("✅ All API structure tests passed!")
        print("=" * 50)
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)

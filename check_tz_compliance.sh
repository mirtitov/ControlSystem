#!/bin/bash
# Скрипт для проверки соответствия ТЗ

echo "📋 Проверка соответствия Техническому Заданию"
echo "=============================================="
echo ""

BASE_URL="http://localhost:8000/api/v1"
ERRORS=0
PASSED=0

# Функция для проверки
check() {
    if [ $? -eq 0 ]; then
        echo "✅ $1"
        ((PASSED++))
    else
        echo "❌ $1"
        ((ERRORS++))
    fi
}

# 1. Проверка базовых endpoints
echo "1. Базовые API Endpoints:"
echo "-------------------------"

# 1.1 Создание партий
echo -n "   Создание партий (POST /api/v1/batches)... "
RESPONSE=$(curl -s -X POST "$BASE_URL/batches" \
  -H "Content-Type: application/json" \
  -d '[{
    "СтатусЗакрытия": false,
    "ПредставлениеЗаданияНаСмену": "Проверка ТЗ",
    "РабочийЦентр": "Цех №1",
    "Смена": "1 смена",
    "Бригада": "Бригада Тест",
    "НомерПартии": 99999,
    "ДатаПартии": "2024-01-30",
    "Номенклатура": "Тест",
    "КодЕКН": "EKN-TEST",
    "ИдентификаторРЦ": "RC-TEST",
    "ДатаВремяНачалаСмены": "2024-01-30T08:00:00",
    "ДатаВремяОкончанияСмены": "2024-01-30T20:00:00"
  }]' 2>&1)

if echo "$RESPONSE" | grep -q '"id"'; then
    BATCH_ID=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)[0]['id'])" 2>/dev/null)
    echo "✅ (ID: $BATCH_ID)"
    ((PASSED++))
else
    echo "❌"
    ((ERRORS++))
fi

# 1.2 Получение партии
echo -n "   Получение партии (GET /api/v1/batches/{id})... "
if [ ! -z "$BATCH_ID" ]; then
    curl -s "$BASE_URL/batches/$BATCH_ID" | grep -q '"id"' && check "   Получение партии работает" || ((ERRORS++))
else
    echo "⚠️  Пропущено (нет ID)"
fi

# 1.3 Список партий
echo -n "   Список партий (GET /api/v1/batches)... "
curl -s "$BASE_URL/batches?limit=5" | grep -q '"items"' && check "   Список партий работает" || ((ERRORS++))

# 1.4 Обновление партии
echo -n "   Обновление партии (PATCH /api/v1/batches/{id})... "
if [ ! -z "$BATCH_ID" ]; then
    curl -s -X PATCH "$BASE_URL/batches/$BATCH_ID" \
      -H "Content-Type: application/json" \
      -d '{"is_closed": true}' | grep -q '"is_closed":true' && check "   Обновление партии работает" || ((ERRORS++))
else
    echo "⚠️  Пропущено"
fi

# 2. Проверка асинхронных задач
echo ""
echo "2. Асинхронные задачи (Celery):"
echo "-------------------------------"

# 2.1 Статус задач
echo -n "   Endpoint статуса задач (GET /api/v1/tasks/{id})... "
curl -s "$BASE_URL/tasks/test-123" 2>&1 | grep -q '"status"' && check "   Endpoint задач существует" || ((ERRORS++))

# 3. Проверка Webhooks
echo ""
echo "3. Webhook система:"
echo "-------------------"

# 3.1 Список webhooks
echo -n "   Список webhooks (GET /api/v1/webhooks)... "
curl -s "$BASE_URL/webhooks" | grep -q '"items"' && check "   Webhook endpoints работают" || ((ERRORS++))

# 4. Проверка аналитики
echo ""
echo "4. Аналитика:"
echo "-------------"

# 4.1 Dashboard
echo -n "   Dashboard статистика (GET /api/v1/analytics/dashboard)... "
curl -s "$BASE_URL/analytics/dashboard" | grep -q '"summary"' && check "   Dashboard работает" || ((ERRORS++))

# 5. Проверка сервисов
echo ""
echo "5. Внешние сервисы:"
echo "-------------------"

# 5.1 Redis
echo -n "   Redis кэширование... "
docker-compose ps redis | grep -q "healthy" && check "   Redis работает" || ((ERRORS++))

# 5.2 RabbitMQ
echo -n "   RabbitMQ... "
docker-compose ps rabbitmq | grep -q "healthy" && check "   RabbitMQ работает" || ((ERRORS++))

# 5.3 MinIO
echo -n "   MinIO... "
docker-compose ps minio | grep -q "healthy" && check "   MinIO работает" || ((ERRORS++))

# 5.4 PostgreSQL
echo -n "   PostgreSQL... "
docker-compose ps postgres | grep -q "healthy" && check "   PostgreSQL работает" || ((ERRORS++))

# 6. Проверка Celery
echo ""
echo "6. Celery компоненты:"
echo "---------------------"

# 6.1 Worker
echo -n "   Celery Worker... "
docker-compose ps celery_worker | grep -q "Up" && check "   Worker запущен" || ((ERRORS++))

# 6.2 Beat
echo -n "   Celery Beat... "
docker-compose ps celery_beat | grep -q "Up" && check "   Beat запущен" || ((ERRORS++))

# 6.3 Flower
echo -n "   Flower (мониторинг)... "
docker-compose ps flower | grep -q "Up" && check "   Flower запущен" || ((ERRORS++))

# Итоги
echo ""
echo "=============================================="
echo "📊 Итоги проверки:"
echo "   ✅ Пройдено: $PASSED"
echo "   ❌ Ошибок: $ERRORS"
echo "=============================================="

if [ $ERRORS -eq 0 ]; then
    echo "🎉 Все проверки пройдены успешно!"
    exit 0
else
    echo "⚠️  Обнаружены проблемы. Проверьте логи выше."
    exit 1
fi

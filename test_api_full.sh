#!/bin/bash
# Полное тестирование API

BASE_URL="http://localhost:8000/api/v1"

echo "🧪 Полное тестирование API Production Control System"
echo "=================================================="
echo ""

# 1. Health check
echo "✅ 1. Health check:"
curl -s "http://localhost:8000/health" | python3 -m json.tool
echo ""

# 2. Создание партии
echo "✅ 2. Создание партии:"
BATCH_RESPONSE=$(curl -s -X POST "$BASE_URL/batches" \
  -H "Content-Type: application/json" \
  -d '[
    {
      "СтатусЗакрытия": false,
      "ПредставлениеЗаданияНаСмену": "Изготовить 500 гаек М10",
      "РабочийЦентр": "Цех №2",
      "Смена": "2 смена",
      "Бригада": "Бригада Петрова",
      "НомерПартии": 33333,
      "ДатаПартии": "2024-02-01",
      "Номенклатура": "Гайка М10",
      "КодЕКН": "EKN-54321",
      "ИдентификаторРЦ": "RC-002",
      "ДатаВремяНачалаСмены": "2024-02-01T14:00:00",
      "ДатаВремяОкончанияСмены": "2024-02-01T22:00:00"
    }
  ]')

BATCH_ID=$(echo "$BATCH_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)[0]['id'])" 2>/dev/null)
echo "Создана партия ID: $BATCH_ID"
echo "$BATCH_RESPONSE" | python3 -m json.tool | head -15
echo ""

# 3. Получение партии
echo "✅ 3. Получение партии ID=$BATCH_ID:"
curl -s "$BASE_URL/batches/$BATCH_ID" | python3 -m json.tool | head -20
echo ""

# 4. Список партий
echo "✅ 4. Список партий (limit=3):"
curl -s "$BASE_URL/batches?limit=3" | python3 -m json.tool | head -30
echo ""

# 5. Добавление продукции
echo "✅ 5. Добавление продукции:"
PRODUCT_RESPONSE=$(curl -s -X POST "$BASE_URL/products" \
  -H "Content-Type: application/json" \
  -d "{
    \"unique_code\": \"PROD-$(date +%s)\",
    \"batch_id\": $BATCH_ID
  }")
echo "$PRODUCT_RESPONSE" | python3 -m json.tool
echo ""

# 6. Аггрегация продукции
echo "✅ 6. Аггрегация продукции:"
AGG_RESPONSE=$(curl -s -X POST "$BASE_URL/batches/$BATCH_ID/aggregate" \
  -H "Content-Type: application/json" \
  -d "{
    \"unique_codes\": [\"PROD-$(date +%s)\"]
  }")
echo "$AGG_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$AGG_RESPONSE"
echo ""

# 7. Dashboard статистика
echo "✅ 7. Dashboard статистика:"
curl -s "$BASE_URL/analytics/dashboard" | python3 -m json.tool | head -25
echo ""

# 8. Статистика по партии
echo "✅ 8. Статистика по партии ID=$BATCH_ID:"
curl -s "$BASE_URL/analytics/batches/$BATCH_ID/statistics" | python3 -m json.tool | head -30
echo ""

# 9. Обновление партии
echo "✅ 9. Обновление партии (закрытие):"
curl -s -X PATCH "$BASE_URL/batches/$BATCH_ID" \
  -H "Content-Type: application/json" \
  -d '{"is_closed": true}' | python3 -m json.tool | head -15
echo ""

# 10. Список webhook подписок
echo "✅ 10. Список webhook подписок:"
curl -s "$BASE_URL/webhooks" | python3 -m json.tool
echo ""

echo "=================================================="
echo "✅ Тестирование завершено!"
echo ""
echo "📊 Доступные интерфейсы:"
echo "   - API Docs: http://localhost:8000/docs"
echo "   - RabbitMQ: http://localhost:15672 (admin/admin)"
echo "   - MinIO: http://localhost:9001 (minioadmin/minioadmin)"
echo "   - Flower: http://localhost:5555"

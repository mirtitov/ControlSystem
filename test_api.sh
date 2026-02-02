#!/bin/bash
# Скрипт для тестирования API

BASE_URL="http://localhost:8000/api/v1"

echo "🧪 Тестирование API..."
echo ""

# 1. Health check
echo "1. Health check:"
curl -s "$BASE_URL/../health" | python3 -m json.tool
echo ""

# 2. Создание партии
echo "2. Создание партии:"
BATCH_RESPONSE=$(curl -s -X POST "$BASE_URL/batches" \
  -H "Content-Type: application/json" \
  -d '[
    {
      "СтатусЗакрытия": false,
      "ПредставлениеЗаданияНаСмену": "Изготовить 1000 болтов М10",
      "РабочийЦентр": "Цех №1",
      "Смена": "1 смена",
      "Бригада": "Бригада Иванова",
      "НомерПартии": 22222,
      "ДатаПартии": "2024-01-30",
      "Номенклатура": "Болт М10х50",
      "КодЕКН": "EKN-12345",
      "ИдентификаторРЦ": "RC-001",
      "ДатаВремяНачалаСмены": "2024-01-30T08:00:00",
      "ДатаВремяОкончанияСмены": "2024-01-30T20:00:00"
    }
  ]')

echo "$BATCH_RESPONSE" | python3 -m json.tool
BATCH_ID=$(echo "$BATCH_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)[0]['id'])" 2>/dev/null || echo "1")
echo ""

# 3. Получение партии
echo "3. Получение партии ID=$BATCH_ID:"
curl -s "$BASE_URL/batches/$BATCH_ID" | python3 -m json.tool | head -30
echo ""

# 4. Список партий
echo "4. Список партий:"
curl -s "$BASE_URL/batches?limit=5" | python3 -m json.tool | head -20
echo ""

# 5. Dashboard статистика
echo "5. Dashboard статистика:"
curl -s "$BASE_URL/../analytics/dashboard" | python3 -m json.tool | head -20
echo ""

echo "✅ Тестирование завершено!"

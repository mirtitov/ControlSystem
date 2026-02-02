#!/bin/bash
# Скрипт для ожидания запуска Docker

echo "⏳ Ожидание запуска Docker..."
MAX_ATTEMPTS=30
ATTEMPT=0

while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    if docker ps &>/dev/null; then
        echo "✅ Docker запущен!"
        exit 0
    fi
    ATTEMPT=$((ATTEMPT + 1))
    echo "   Попытка $ATTEMPT/$MAX_ATTEMPTS..."
    sleep 2
done

echo "❌ Docker не запустился за отведенное время"
exit 1

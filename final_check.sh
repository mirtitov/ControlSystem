#!/bin/bash
# Финальная проверка проекта перед сдачей

echo "🔍 Финальная проверка проекта"
echo "=============================="
echo ""

ERRORS=0
WARNINGS=0

# 1. Проверка синтаксиса
echo "1. Проверка синтаксиса Python..."
find src tests -name "*.py" -exec python3 -m py_compile {} \; 2>&1 | while read line; do
    if [ ! -z "$line" ]; then
        echo "   ❌ $line"
        ((ERRORS++))
    fi
done
if [ $ERRORS -eq 0 ]; then
    echo "   ✅ Все файлы компилируются"
fi
echo ""

# 2. Проверка линтера
echo "2. Проверка линтера (ruff)..."
RUFF_OUTPUT=$(python3 -m ruff check src/ tests/ 2>&1)
if [ $? -eq 0 ]; then
    echo "   ✅ Все проверки ruff пройдены"
else
    echo "   ⚠️  Найдены проблемы:"
    echo "$RUFF_OUTPUT" | head -10
    ((WARNINGS++))
fi
echo ""

# 3. Проверка структуры проекта
echo "3. Проверка структуры проекта..."
REQUIRED_FILES=("README.md" "requirements.txt" "docker-compose.yml" "Dockerfile")
for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "   ✅ $file"
    else
        echo "   ❌ Отсутствует: $file"
        ((ERRORS++))
    fi
done
echo ""

# 4. Проверка тестов
echo "4. Проверка тестов..."
if [ -d "tests" ] && [ "$(ls -A tests/*.py 2>/dev/null)" ]; then
    echo "   ✅ Тесты найдены"
    python3 run_tests.py 2>&1 | tail -5
else
    echo "   ⚠️  Тесты не найдены"
    ((WARNINGS++))
fi
echo ""

# 5. Проверка Docker
echo "5. Проверка Docker конфигурации..."
if docker-compose config > /dev/null 2>&1; then
    echo "   ✅ docker-compose.yml валиден"
else
    echo "   ⚠️  Проблемы с docker-compose.yml"
    ((WARNINGS++))
fi
echo ""

# 6. Статистика кода
echo "6. Статистика проекта..."
PY_FILES=$(find src -name "*.py" | wc -l | tr -d ' ')
LINES=$(find src -name "*.py" -exec cat {} \; | wc -l | tr -d ' ')
echo "   📊 Файлов Python: $PY_FILES"
echo "   📊 Строк кода: $LINES"
echo ""

# Итоги
echo "=============================="
echo "📊 Итоги проверки:"
echo "   Ошибок: $ERRORS"
echo "   Предупреждений: $WARNINGS"
echo "=============================="

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo "🎉 Проект готов к сдаче!"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo "✅ Проект готов, но есть предупреждения"
    exit 0
else
    echo "⚠️  Требуется исправление ошибок"
    exit 1
fi

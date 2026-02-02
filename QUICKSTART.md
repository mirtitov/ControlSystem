# Быстрый старт 🚀

## 1. Запуск через Docker Compose

```bash
# Запустить все сервисы
docker-compose up -d

# Проверить статус
docker-compose ps

# Просмотр логов
docker-compose logs -f api
```

## 2. Инициализация базы данных

```bash
# Создать миграцию
docker-compose exec api alembic revision --autogenerate -m "Initial migration"

# Применить миграции
docker-compose exec api alembic upgrade head
```

## 3. Инициализация MinIO

```bash
docker-compose exec api python scripts/init_minio.py
```

## 4. Проверка работы

```bash
# Health check
curl http://localhost:8000/health

# API документация
open http://localhost:8000/docs
```

## 5. Примеры использования

### Создание партии

```bash
curl -X POST "http://localhost:8000/api/v1/batches" \
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
  ]'
```

### Получение партии

```bash
curl http://localhost:8000/api/v1/batches/1
```

### Список партий

```bash
curl "http://localhost:8000/api/v1/batches?is_closed=false&limit=10"
```

### Аггрегация продукции

```bash
curl -X POST "http://localhost:8000/api/v1/batches/1/aggregate" \
  -H "Content-Type: application/json" \
  -d '{
    "unique_codes": ["CODE1", "CODE2", "CODE3"]
  }'
```

### Асинхронная аггрегация

```bash
# Запустить задачу
curl -X POST "http://localhost:8000/api/v1/batches/1/aggregate-async" \
  -H "Content-Type: application/json" \
  -d '{
    "unique_codes": ["CODE1", "CODE2", ..., "CODE1000"]
  }'

# Проверить статус (используйте task_id из ответа)
curl http://localhost:8000/api/v1/tasks/{task_id}
```

### Dashboard статистика

```bash
curl http://localhost:8000/api/v1/analytics/dashboard
```

## 6. Мониторинг

- **API**: http://localhost:8000/docs
- **RabbitMQ Management**: http://localhost:15672 (admin/admin)
- **MinIO Console**: http://localhost:9001 (minioadmin/minioadmin)
- **Flower (Celery)**: http://localhost:5555

## 7. Остановка

```bash
docker-compose down

# С удалением volumes (БД и данные будут удалены!)
docker-compose down -v
```

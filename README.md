# Система контроля заданий на выпуск продукции 🚀

Веб-приложение для управления сменными заданиями на производстве с асинхронной обработкой задач, файловым хранилищем и внешними интеграциями.

## 🛠 Технологический стек

### Backend
- **API**: Python 3.11+, FastAPI
- **ORM**: SQLAlchemy 2.0+ (async)
- **Валидация**: Pydantic v2
- **База данных**: PostgreSQL 16
- **Миграции**: Alembic

### Асинхронная обработка
- **Message Broker**: RabbitMQ
- **Task Queue**: Celery 5.3+
- **Result Backend**: Redis
- **Scheduler**: Celery Beat

### Кэширование и хранилище
- **Cache**: Redis 7+ (для кэширования + Celery backend)
- **File Storage**: MinIO (S3-compatible)

### Контейнеризация
- **Container**: Docker
- **Orchestration**: Docker Compose

## 📋 Быстрый старт

### 1. Клонирование и настройка

```bash
git clone <repository>
cd ControlSystem
cp .env.example .env
# Отредактируйте .env при необходимости
```

### 2. Запуск через Docker Compose

```bash
docker-compose up -d
```

Это запустит все сервисы:
- **API**: http://localhost:8000
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379
- **RabbitMQ Management**: http://localhost:15672 (admin/admin)
- **MinIO Console**: http://localhost:9001 (minioadmin/minioadmin)
- **Flower (Celery Monitoring)**: http://localhost:5555

### 3. Инициализация базы данных

```bash
# Создать миграцию
docker-compose exec api alembic revision --autogenerate -m "Initial migration"

# Применить миграции
docker-compose exec api alembic upgrade head
```

### 4. Инициализация MinIO buckets

```bash
docker-compose exec api python scripts/init_minio.py
```

## 📊 Модели данных

### WorkCenter (Рабочий центр)
- `id`: int (PK)
- `identifier`: str (unique) - ИдентификаторРЦ
- `name`: str - Название рабочего центра

### Batch (Сменное задание / Партия)
- `id`: int (PK)
- `is_closed`: bool - Статус закрытия
- `closed_at`: datetime | None
- `task_description`: str - ПредставлениеЗаданияНаСмену
- `work_center_id`: int (FK)
- `shift`: str - Смена
- `team`: str - Бригада
- `batch_number`: int - НомерПартии
- `batch_date`: date - ДатаПартии
- `nomenclature`: str - Номенклатура
- `ekn_code`: str - КодЕКН
- `shift_start`: datetime
- `shift_end`: datetime

### Product (Продукция)
- `id`: int (PK)
- `unique_code`: str (unique) - Уникальный код
- `batch_id`: int (FK)
- `is_aggregated`: bool
- `aggregated_at`: datetime | None

### WebhookSubscription
- `id`: int (PK)
- `url`: str
- `events`: List[str]
- `secret_key`: str
- `is_active`: bool
- `retry_count`: int
- `timeout`: int

### WebhookDelivery
- `id`: int (PK)
- `subscription_id`: int (FK)
- `event_type`: str
- `payload`: JSON
- `status`: str ("pending", "success", "failed")
- `attempts`: int
- `response_status`: int | None
- `response_body`: str | None
- `error_message`: str | None

## 🔌 API Endpoints

### Базовые операции с партиями

#### Создание партий
```http
POST /api/v1/batches
Content-Type: application/json

[
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
]
```

#### Получение партии
```http
GET /api/v1/batches/{batch_id}
```

#### Обновление партии
```http
PATCH /api/v1/batches/{batch_id}
Content-Type: application/json

{
  "is_closed": true,
  "team": "Бригада Петрова"
}
```

#### Список партий
```http
GET /api/v1/batches?is_closed=false&offset=0&limit=20
```

### Асинхронные задачи

#### Массовая аггрегация
```http
POST /api/v1/batches/{batch_id}/aggregate-async
Content-Type: application/json

{
  "unique_codes": ["CODE1", "CODE2", ..., "CODE1000"]
}

# Проверка статуса
GET /api/v1/tasks/{task_id}
```

#### Генерация отчета
```http
POST /api/v1/batches/{batch_id}/reports
Content-Type: application/json

{
  "format": "excel",  // или "pdf"
  "email": "user@example.com"  // опционально
}
```

#### Импорт партий
```http
POST /api/v1/batches/import
Content-Type: multipart/form-data

file: batches.xlsx
```

#### Экспорт партий
```http
POST /api/v1/batches/export
Content-Type: application/json

{
  "format": "excel",
  "filters": {
    "is_closed": false,
    "date_from": "2024-01-01",
    "date_to": "2024-01-31"
  }
}
```

### Webhooks

#### Создание подписки
```http
POST /api/v1/webhooks
Content-Type: application/json

{
  "url": "https://external-system.com/webhooks/production",
  "events": ["batch_created", "batch_closed"],
  "secret_key": "your-secret-key",
  "retry_count": 3,
  "timeout": 10
}
```

#### Список подписок
```http
GET /api/v1/webhooks
```

#### История доставок
```http
GET /api/v1/webhooks/{webhook_id}/deliveries
```

### Аналитика

#### Dashboard статистика
```http
GET /api/v1/analytics/dashboard
```

#### Статистика по партии
```http
GET /api/v1/analytics/batches/{batch_id}/statistics
```

#### Сравнение партий
```http
POST /api/v1/analytics/compare-batches
Content-Type: application/json

{
  "batch_ids": [123, 124, 125]
}
```

## 🔔 Webhook события

Система отправляет следующие события:

1. **batch_created** - При создании партии
2. **batch_updated** - При обновлении партии
3. **batch_closed** - При закрытии партии
4. **product_aggregated** - При аггрегации продукции
5. **report_generated** - При генерации отчета
6. **import_completed** - При завершении импорта

### Верификация webhook

Webhook подписывается HMAC SHA256. Проверка на стороне получателя:

```python
import hmac
import hashlib

def verify_webhook(payload: str, signature: str, secret_key: str) -> bool:
    expected_signature = hmac.new(
        secret_key.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected_signature, signature)
```

## ⏰ Scheduled Tasks (Celery Beat)

- **01:00** - Автоматическое закрытие просроченных партий
- **02:00** - Очистка старых файлов из MinIO (старше 30 дней)
- **Каждые 5 минут** - Обновление кэшированной статистики
- **Каждые 15 минут** - Повторная отправка неудачных webhooks

## 💾 Кэширование

Система использует Redis для кэширования:

- **Dashboard статистика**: TTL 5 минут
- **Список партий**: TTL 1 минута
- **Детали партии**: TTL 10 минут
- **Статистика партии**: TTL 5 минут

Кэш автоматически инвалидируется при изменениях данных.

## 📦 MinIO Storage

Buckets:
- `reports` - Сгенерированные отчеты
- `exports` - Экспортированные данные
- `imports` - Загруженные файлы для импорта

Файлы доступны через pre-signed URLs с истечением через 7 дней.

## 🧪 Разработка

### Локальная разработка (без Docker)

```bash
# Установка зависимостей
pip install -r requirements.txt

# Настройка переменных окружения
cp .env.example .env

# Запуск миграций
alembic upgrade head

# Запуск API
uvicorn src.main:app --reload

# Запуск Celery Worker (в отдельном терминале)
celery -A src.celery_app worker --loglevel=info

# Запуск Celery Beat (в отдельном терминале)
celery -A src.celery_app beat --loglevel=info
```

### Структура проекта

```
ControlSystem/
├── src/
│   ├── api/              # API endpoints
│   ├── models/           # SQLAlchemy модели
│   ├── schemas/          # Pydantic схемы
│   ├── repositories/     # Репозитории для работы с БД
│   ├── services/         # Бизнес-логика и сервисы
│   ├── tasks/            # Celery задачи
│   ├── celery_app.py     # Celery конфигурация
│   ├── config.py         # Настройки приложения
│   ├── database.py       # Настройка БД
│   └── main.py           # FastAPI приложение
├── alembic/              # Миграции БД
├── scripts/              # Вспомогательные скрипты
├── docker-compose.yml    # Docker Compose конфигурация
├── Dockerfile            # Docker образ
├── requirements.txt      # Python зависимости
└── README.md
```

## 📝 Документация API

После запуска приложения доступна интерактивная документация:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔒 Безопасность

⚠️ **Важно**: В production обязательно:
1. Измените `SECRET_KEY` в `.env`
2. Настройте правильные пароли для всех сервисов
3. Используйте HTTPS
4. Настройте firewall
5. Регулярно обновляйте зависимости

## 📄 Лицензия

[Укажите лицензию]

## 🤝 Вклад

[Инструкции по внесению вклада]

## 📞 Контакты

[Контактная информация]

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from datetime import date, datetime
from src.database import get_db
from src.repositories.batch import BatchRepository
from src.repositories.work_center import WorkCenterRepository
from src.repositories.product import ProductRepository
from src.schemas.batch import (
    BatchCreateRequest,
    BatchCreate,
    BatchUpdate,
    BatchResponse,
    BatchListResponse,
)
from src.schemas.aggregation import AggregateRequest, AggregateAsyncRequest
from src.schemas.reports import GenerateReportRequest
from src.schemas.export import ExportRequest
from src.services.cache_service import cache_service
from src.tasks.aggregation import aggregate_products_batch
from src.tasks.reports import generate_batch_report
from src.tasks.import_export import import_batches_from_file, export_batches_to_file
from src.tasks.webhooks import send_webhook_delivery
from src.services.webhook_service import webhook_service
from src.repositories.webhook import WebhookRepository

router = APIRouter(prefix="/api/v1/batches", tags=["batches"])


@router.post("", response_model=List[BatchResponse], status_code=201)
async def create_batches(
    requests: List[BatchCreateRequest], db: AsyncSession = Depends(get_db)
):
    """Создание сменных заданий"""
    batch_repo = BatchRepository(db)
    work_center_repo = WorkCenterRepository(db)

    created_batches = []

    async with db.begin():
        for req in requests:
            # Get or create work center
            work_center = await work_center_repo.get_or_create(
                identifier=req.ИдентификаторРЦ, name=req.РабочийЦентр
            )

            # Create batch
            batch_data = BatchCreate(
                is_closed=req.СтатусЗакрытия,
                task_description=req.ПредставлениеЗаданияНаСмену,
                work_center_id=work_center.id,
                shift=req.Смена,
                team=req.Бригада,
                batch_number=req.НомерПартии,
                batch_date=req.ДатаПартии,
                nomenclature=req.Номенклатура,
                ekn_code=req.КодЕКН,
                shift_start=req.ДатаВремяНачалаСмены,
                shift_end=req.ДатаВремяОкончанияСмены,
            )

            batch = await batch_repo.create(batch_data)
            created_batches.append(batch)

        await db.commit()

    # Invalidate cache
    await cache_service.delete("dashboard_stats")
    await cache_service.delete_pattern("batches_list:*")

    # Send webhook events
    webhook_repo = WebhookRepository(db)
    for batch in created_batches:
        subscriptions = await webhook_repo.get_active_subscriptions_for_event(
            "batch_created"
        )
        for subscription in subscriptions:
            payload = webhook_service.create_webhook_payload(
                "batch_created",
                {
                    "id": batch.id,
                    "batch_number": batch.batch_number,
                    "batch_date": str(batch.batch_date),
                    "nomenclature": batch.nomenclature,
                    "work_center": batch.work_center.name if batch.work_center else "",
                },
            )
            delivery = await webhook_repo.create_delivery(
                subscription_id=subscription.id,
                event_type="batch_created",
                payload=payload,
            )
            send_webhook_delivery.delay(delivery.id)

    return created_batches


@router.get("/{batch_id}", response_model=BatchResponse)
async def get_batch(batch_id: int, db: AsyncSession = Depends(get_db)):
    """Получение партии по ID"""
    batch_repo = BatchRepository(db)
    batch = await batch_repo.get_by_id(batch_id, with_products=True)

    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    # Явно загружаем products чтобы избежать lazy loading проблем
    await db.refresh(batch, ["products"])

    return batch


@router.patch("/{batch_id}", response_model=BatchResponse)
async def update_batch(
    batch_id: int, data: BatchUpdate, db: AsyncSession = Depends(get_db)
):
    """Обновление партии"""
    batch_repo = BatchRepository(db)
    batch = await batch_repo.update(batch_id, data)

    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    await db.commit()

    # Invalidate cache
    await cache_service.delete(f"batch_detail:{batch_id}")
    await cache_service.delete(f"batch_statistics:{batch_id}")
    await cache_service.delete("dashboard_stats")
    await cache_service.delete_pattern("batches_list:*")

    # Send webhook event
    webhook_repo = WebhookRepository(db)
    subscriptions = await webhook_repo.get_active_subscriptions_for_event(
        "batch_updated"
    )
    for subscription in subscriptions:
        payload = webhook_service.create_webhook_payload(
            "batch_updated",
            {
                "id": batch.id,
                "batch_number": batch.batch_number,
                "changes": data.model_dump(exclude_unset=True),
            },
        )
        delivery = await webhook_repo.create_delivery(
            subscription_id=subscription.id, event_type="batch_updated", payload=payload
        )
        send_webhook_delivery.delay(delivery.id)

    # Check if batch was closed
    if data.is_closed and batch.is_closed:
        subscriptions = await webhook_repo.get_active_subscriptions_for_event(
            "batch_closed"
        )
        for subscription in subscriptions:
            product_repo = ProductRepository(db)
            stats = await product_repo.get_statistics(batch_id)
            payload = webhook_service.create_webhook_payload(
                "batch_closed",
                {
                    "id": batch.id,
                    "batch_number": batch.batch_number,
                    "closed_at": batch.closed_at.isoformat()
                    if batch.closed_at
                    else None,
                    "statistics": stats,
                },
            )
            delivery = await webhook_repo.create_delivery(
                subscription_id=subscription.id,
                event_type="batch_closed",
                payload=payload,
            )
            send_webhook_delivery.delay(delivery.id)

    return batch


@router.get("", response_model=BatchListResponse)
async def list_batches(
    is_closed: Optional[bool] = Query(None),
    batch_number: Optional[int] = Query(None),
    batch_date: Optional[date] = Query(None),
    work_center_id: Optional[int] = Query(None),
    shift: Optional[str] = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Список партий с фильтрацией"""
    # Try cache first
    cache_key = f"batches_list:{is_closed}:{batch_number}:{batch_date}:{work_center_id}:{shift}:{offset}:{limit}"
    cached = await cache_service.get(cache_key)
    if cached:
        return cached

    batch_repo = BatchRepository(db)
    items, total = await batch_repo.list(
        is_closed=is_closed,
        batch_number=batch_number,
        batch_date=batch_date,
        work_center_id=work_center_id,
        shift=shift,
        offset=offset,
        limit=limit,
    )

    result = BatchListResponse(items=items, total=total, offset=offset, limit=limit)

    # Cache for 1 minute
    await cache_service.set(cache_key, result.model_dump(), ttl=60)

    return result


@router.post("/{batch_id}/aggregate")
async def aggregate_batch(
    batch_id: int, data: AggregateRequest, db: AsyncSession = Depends(get_db)
):
    """Аггрегация продукции (синхронная, для малых объемов)"""
    unique_codes = data.unique_codes
    if len(unique_codes) > 100:
        raise HTTPException(
            status_code=400,
            detail="For more than 100 codes, use /aggregate-async endpoint",
        )

    product_repo = ProductRepository(db)
    result = await product_repo.bulk_aggregate(batch_id, unique_codes)

    await db.commit()

    # Invalidate cache
    await cache_service.delete(f"batch_detail:{batch_id}")
    await cache_service.delete(f"batch_statistics:{batch_id}")
    await cache_service.delete("dashboard_stats")

    # Send webhook events for aggregated products
    webhook_repo = WebhookRepository(db)
    subscriptions = await webhook_repo.get_active_subscriptions_for_event(
        "product_aggregated"
    )

    # Get batch info for webhook
    batch = await batch_repo.get_by_id(batch_id)

    if subscriptions and result.get("aggregated", 0) > 0:
        for subscription in subscriptions:
            # Send summary event for batch aggregation
            payload = webhook_service.create_webhook_payload(
                "product_aggregated",
                {
                    "batch_id": batch_id,
                    "batch_number": batch.batch_number if batch else None,
                    "total": result.get("total", 0),
                    "aggregated": result.get("aggregated", 0),
                    "failed": result.get("failed", 0),
                    "aggregated_at": datetime.utcnow().isoformat() + "Z",
                },
            )
            delivery = await webhook_repo.create_delivery(
                subscription_id=subscription.id,
                event_type="product_aggregated",
                payload=payload,
            )
            send_webhook_delivery.delay(delivery.id)

    return result


@router.post("/{batch_id}/aggregate-async")
async def aggregate_batch_async(
    batch_id: int, data: AggregateAsyncRequest, db: AsyncSession = Depends(get_db)
):
    """Асинхронная массовая аггрегация продукции"""
    unique_codes = data.unique_codes
    # Verify batch exists
    batch_repo = BatchRepository(db)
    batch = await batch_repo.get_by_id(batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    # Start async task
    task = aggregate_products_batch.delay(batch_id, unique_codes)

    return {
        "task_id": task.id,
        "status": "PENDING",
        "message": "Aggregation task started",
    }


@router.post("/{batch_id}/reports")
async def generate_report(
    batch_id: int, data: GenerateReportRequest, db: AsyncSession = Depends(get_db)
):
    """Генерация отчета по партии"""
    if data.format not in ["excel", "pdf"]:
        raise HTTPException(status_code=400, detail="Format must be 'excel' or 'pdf'")

    # Verify batch exists
    batch_repo = BatchRepository(db)
    batch = await batch_repo.get_by_id(batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    # Start async task
    task = generate_batch_report.delay(batch_id, data.format, data.email)

    return {
        "task_id": task.id,
        "status": "PENDING",
        "message": "Report generation started",
    }


@router.post("/import")
async def import_batches(
    file_url: str,
    user_id: int = 1,  # In production, get from auth
    db: AsyncSession = Depends(get_db),
):
    """Импорт партий из файла"""
    task = import_batches_from_file.delay(file_url, user_id)

    return {
        "task_id": task.id,
        "status": "PENDING",
        "message": "File uploaded, import started",
    }


@router.post("/export")
async def export_batches(data: ExportRequest, db: AsyncSession = Depends(get_db)):
    """Экспорт партий в файл"""
    if data.format not in ["excel", "csv"]:
        raise HTTPException(status_code=400, detail="Format must be 'excel' or 'csv'")

    filters = data.filters or {}
    task = export_batches_to_file.delay(filters, data.format)

    return {"task_id": task.id, "status": "PENDING", "message": "Export started"}

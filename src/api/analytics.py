from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from src.database import get_db
from src.repositories.batch import BatchRepository
from src.repositories.product import ProductRepository
from src.services.cache_service import cache_service
from datetime import datetime, timedelta

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])


@router.get("/dashboard")
async def get_dashboard_statistics(db: AsyncSession = Depends(get_db)):
    """Статистика дашборда (из кэша)"""
    # Try cache first
    cached = await cache_service.get("dashboard_stats")
    if cached:
        return cached
    
    # If not cached, calculate (should be updated by Celery Beat)
    from sqlalchemy import select, func
    from src.models.batch import Batch
    from src.models.product import Product
    
    total_batches_result = await db.execute(select(func.count(Batch.id)))
    total_batches = total_batches_result.scalar() or 0
    
    active_batches_result = await db.execute(
        select(func.count(Batch.id)).where(Batch.is_closed == False)
    )
    active_batches = active_batches_result.scalar() or 0
    
    total_products_result = await db.execute(select(func.count(Product.id)))
    total_products = total_products_result.scalar() or 0
    
    aggregated_products_result = await db.execute(
        select(func.count(Product.id)).where(Product.is_aggregated == True)
    )
    aggregated_products = aggregated_products_result.scalar() or 0
    
    stats = {
        "summary": {
            "total_batches": total_batches,
            "active_batches": active_batches,
            "closed_batches": total_batches - active_batches,
            "total_products": total_products,
            "aggregated_products": aggregated_products,
            "aggregation_rate": (aggregated_products / total_products * 100) if total_products > 0 else 0.0
        },
        "cached_at": datetime.utcnow().isoformat() + "Z"
    }
    
    # Cache for 5 minutes
    await cache_service.set("dashboard_stats", stats, ttl=300)
    
    return stats


@router.get("/batches/{batch_id}/statistics")
async def get_batch_statistics(
    batch_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Статистика по партии"""
    # Try cache first
    cache_key = f"batch_statistics:{batch_id}"
    cached = await cache_service.get(cache_key)
    if cached:
        return cached
    
    batch_repo = BatchRepository(db)
    batch = await batch_repo.get_by_id(batch_id)
    
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    
    product_repo = ProductRepository(db)
    stats = await product_repo.get_statistics(batch_id)
    
    # Calculate timeline
    now = datetime.utcnow()
    shift_duration = (batch.shift_end - batch.shift_start).total_seconds() / 3600
    elapsed = (now - batch.shift_start).total_seconds() / 3600 if now > batch.shift_start else 0
    
    products_per_hour = stats["aggregated"] / elapsed if elapsed > 0 else 0
    remaining_hours = stats["remaining"] / products_per_hour if products_per_hour > 0 else 0
    estimated_completion = now + timedelta(hours=remaining_hours) if remaining_hours > 0 else None
    
    result = {
        "batch_info": {
            "id": batch.id,
            "batch_number": batch.batch_number,
            "batch_date": str(batch.batch_date),
            "is_closed": batch.is_closed
        },
        "production_stats": stats,
        "timeline": {
            "shift_duration_hours": shift_duration,
            "elapsed_hours": elapsed,
            "products_per_hour": products_per_hour,
            "estimated_completion": estimated_completion.isoformat() if estimated_completion else None
        },
        "team_performance": {
            "team": batch.team,
            "avg_products_per_hour": products_per_hour,
            "efficiency_score": min(100, (stats["aggregation_rate"] / 100) * 100)
        }
    }
    
    # Cache for 5 minutes
    await cache_service.set(cache_key, result, ttl=300)
    
    return result


@router.post("/compare-batches")
async def compare_batches(
    batch_ids: List[int],
    db: AsyncSession = Depends(get_db)
):
    """Сравнение партий"""
    batch_repo = BatchRepository(db)
    product_repo = ProductRepository(db)
    
    comparison = []
    
    for batch_id in batch_ids:
        batch = await batch_repo.get_by_id(batch_id)
        if not batch:
            continue
        
        stats = await product_repo.get_statistics(batch_id)
        shift_duration = (batch.shift_end - batch.shift_start).total_seconds() / 3600
        
        comparison.append({
            "batch_id": batch.id,
            "batch_number": batch.batch_number,
            "total_products": stats["total_products"],
            "aggregated": stats["aggregated"],
            "rate": stats["aggregation_rate"],
            "duration_hours": shift_duration,
            "products_per_hour": stats["aggregated"] / shift_duration if shift_duration > 0 else 0
        })
    
    if not comparison:
        raise HTTPException(status_code=404, detail="No valid batches found")
    
    # Calculate averages
    avg_rate = sum(c["rate"] for c in comparison) / len(comparison)
    avg_products_per_hour = sum(c["products_per_hour"] for c in comparison) / len(comparison)
    
    return {
        "comparison": comparison,
        "average": {
            "aggregation_rate": avg_rate,
            "products_per_hour": avg_products_per_hour
        }
    }

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.repositories.batch import BatchRepository
from src.repositories.product import ProductRepository
from src.schemas.product import ProductCreate, ProductResponse
from src.services.cache_service import cache_service

router = APIRouter(prefix="/api/v1/products", tags=["products"])


@router.post("", response_model=ProductResponse, status_code=201)
async def create_product(data: ProductCreate, db: AsyncSession = Depends(get_db)):
    """Добавление продукции"""
    # Verify batch exists
    batch_repo = BatchRepository(db)
    batch = await batch_repo.get_by_id(data.batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    # Check if code already exists
    product_repo = ProductRepository(db)
    existing = await product_repo.get_by_code(data.unique_code)
    if existing:
        raise HTTPException(status_code=400, detail="Product with this code already exists")

    product = await product_repo.create(data)
    await db.commit()

    # Invalidate cache
    await cache_service.delete(f"batch_detail:{data.batch_id}")
    await cache_service.delete(f"batch_statistics:{data.batch_id}")
    await cache_service.delete("dashboard_stats")

    return product

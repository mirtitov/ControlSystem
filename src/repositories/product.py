from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import List
from src.models.product import Product
from src.schemas.product import ProductCreate


class ProductRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, data: ProductCreate) -> Product:
        product = Product(**data.model_dump())
        self.session.add(product)
        await self.session.flush()
        await self.session.refresh(product)
        return product

    async def get_by_code(self, unique_code: str) -> Product | None:
        result = await self.session.execute(
            select(Product).where(Product.unique_code == unique_code)
        )
        return result.scalar_one_or_none()

    async def get_by_batch_id(self, batch_id: int) -> List[Product]:
        result = await self.session.execute(
            select(Product).where(Product.batch_id == batch_id)
        )
        return list(result.scalars().all())

    async def aggregate(self, batch_id: int, unique_code: str) -> Product | None:
        product = await self.session.execute(
            select(Product).where(
                and_(Product.batch_id == batch_id, Product.unique_code == unique_code)
            )
        )
        product = product.scalar_one_or_none()

        if not product:
            return None

        if product.is_aggregated:
            return product

        from datetime import datetime

        product.is_aggregated = True
        product.aggregated_at = datetime.utcnow()

        await self.session.flush()
        await self.session.refresh(product)
        return product

    async def bulk_aggregate(self, batch_id: int, unique_codes: List[str]) -> dict:
        """Bulk aggregate products. Returns success/failed counts."""
        from datetime import datetime

        result = await self.session.execute(
            select(Product).where(
                and_(
                    Product.batch_id == batch_id, Product.unique_code.in_(unique_codes)
                )
            )
        )
        products = result.scalars().all()

        aggregated = 0
        failed = 0
        errors = []

        for product in products:
            if product.is_aggregated:
                failed += 1
                errors.append(
                    {"code": product.unique_code, "reason": "already aggregated"}
                )
            else:
                product.is_aggregated = True
                product.aggregated_at = datetime.utcnow()
                aggregated += 1

        # Check for codes that don't exist
        found_codes = {p.unique_code for p in products}
        for code in unique_codes:
            if code not in found_codes:
                failed += 1
                errors.append({"code": code, "reason": "not found in batch"})

        await self.session.flush()

        return {
            "success": True,
            "total": len(unique_codes),
            "aggregated": aggregated,
            "failed": failed,
            "errors": errors,
        }

    async def get_statistics(self, batch_id: int) -> dict:
        """Get aggregation statistics for a batch"""
        result = await self.session.execute(
            select(
                func.count(Product.id).label("total"),
                func.sum(func.cast(Product.is_aggregated, func.Integer)).label(
                    "aggregated"
                ),
            ).where(Product.batch_id == batch_id)
        )
        stats = result.first()

        total = stats.total or 0
        aggregated = stats.aggregated or 0

        return {
            "total_products": total,
            "aggregated": aggregated,
            "remaining": total - aggregated,
            "aggregation_rate": (aggregated / total * 100) if total > 0 else 0.0,
        }

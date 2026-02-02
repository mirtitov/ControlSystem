from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
from typing import Optional
from datetime import date, datetime
from src.models.batch import Batch
from src.schemas.batch import BatchCreate, BatchUpdate


class BatchRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, data: BatchCreate) -> Batch:
        batch = Batch(**data.model_dump())
        self.session.add(batch)
        await self.session.flush()
        await self.session.refresh(batch)
        return batch

    async def get_by_id(self, batch_id: int, with_products: bool = False) -> Batch | None:
        query = select(Batch).where(Batch.id == batch_id)
        if with_products:
            query = query.options(selectinload(Batch.products))
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def update(self, batch_id: int, data: BatchUpdate) -> Batch | None:
        batch = await self.get_by_id(batch_id)
        if not batch:
            return None
        
        update_data = data.model_dump(exclude_unset=True)
        
        # Handle is_closed logic
        if "is_closed" in update_data:
            if update_data["is_closed"] and not batch.is_closed:
                batch.closed_at = datetime.utcnow()
            elif not update_data["is_closed"] and batch.is_closed:
                batch.closed_at = None
        
        for key, value in update_data.items():
            setattr(batch, key, value)
        
        await self.session.flush()
        await self.session.refresh(batch)
        return batch

    async def list(
        self,
        is_closed: Optional[bool] = None,
        batch_number: Optional[int] = None,
        batch_date: Optional[date] = None,
        work_center_id: Optional[int] = None,
        shift: Optional[str] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[Batch], int]:
        query = select(Batch)
        count_query = select(func.count(Batch.id))
        
        conditions = []
        
        if is_closed is not None:
            conditions.append(Batch.is_closed == is_closed)
        if batch_number is not None:
            conditions.append(Batch.batch_number == batch_number)
        if batch_date is not None:
            conditions.append(Batch.batch_date == batch_date)
        if work_center_id is not None:
            conditions.append(Batch.work_center_id == work_center_id)
        if shift is not None:
            conditions.append(Batch.shift == shift)
        
        if conditions:
            query = query.where(and_(*conditions))
            count_query = count_query.where(and_(*conditions))
        
        # Get total count
        total_result = await self.session.execute(count_query)
        total = total_result.scalar()
        
        # Get items with pagination
        query = query.options(selectinload(Batch.products))
        query = query.offset(offset).limit(limit).order_by(Batch.created_at.desc())
        
        result = await self.session.execute(query)
        items = result.scalars().all()
        
        return list(items), total

    async def get_expired_batches(self) -> list[Batch]:
        """Get batches where shift_end < now() and is_closed = False"""
        query = select(Batch).where(
            and_(
                Batch.is_closed == False,
                Batch.shift_end < datetime.utcnow()
            )
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

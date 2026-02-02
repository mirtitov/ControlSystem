from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from src.database import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    unique_code = Column(String, unique=True, nullable=False, index=True)
    batch_id = Column(Integer, ForeignKey("batches.id"), nullable=False, index=True)

    # Aggregation
    is_aggregated = Column(Boolean, default=False, nullable=False, index=True)
    aggregated_at = Column(DateTime(timezone=True), nullable=True)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    batch = relationship("Batch", back_populates="products")

    __table_args__ = (Index("idx_product_batch_aggregated", "batch_id", "is_aggregated"),)

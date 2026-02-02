from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from src.database import Base


class Batch(Base):
    __tablename__ = "batches"

    id = Column(Integer, primary_key=True, index=True)

    # Status
    is_closed = Column(Boolean, default=False, nullable=False)
    closed_at = Column(DateTime(timezone=True), nullable=True)

    # Description
    task_description = Column(String, nullable=False)
    work_center_id = Column(Integer, ForeignKey("work_centers.id"), nullable=False)
    shift = Column(String, nullable=False)
    team = Column(String, nullable=False)

    # Identification
    batch_number = Column(Integer, nullable=False, index=True)
    batch_date = Column(Date, nullable=False, index=True)

    # Product
    nomenclature = Column(String, nullable=False)
    ekn_code = Column(String, nullable=False)

    # Time frames
    shift_start = Column(DateTime(timezone=True), nullable=False)
    shift_end = Column(DateTime(timezone=True), nullable=False)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    products = relationship("Product", back_populates="batch", cascade="all, delete-orphan")
    work_center = relationship("WorkCenter", backref="batches")

    __table_args__ = (
        UniqueConstraint("batch_number", "batch_date", name="uq_batch_number_date"),
        Index("idx_batch_closed", "is_closed"),
        Index("idx_batch_shift_times", "shift_start", "shift_end"),
    )

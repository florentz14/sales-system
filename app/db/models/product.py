from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.mixins import AuditedSoftDeleteMixin

if TYPE_CHECKING:
    from app.db.models.inventory import Inventory


class Product(AuditedSoftDeleteMixin, Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    sku: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    price: Mapped[float] = mapped_column(Float, nullable=False)

    inventory_rows: Mapped[list[Inventory]] = relationship(
        "Inventory",
        back_populates="product",
    )

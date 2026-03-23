from __future__ import annotations

from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.mixins import AuditedSoftDeleteMixin

if TYPE_CHECKING:
    from app.db.models.customer import Customer
    from app.db.models.product import Product


class InvoiceItem(AuditedSoftDeleteMixin, Base):
    __tablename__ = "invoice_items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    invoice_id: Mapped[int] = mapped_column(ForeignKey("invoices.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    discount_percent: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    invoice: Mapped[Invoice] = relationship(
        "Invoice",
        back_populates="items",
    )
    product: Mapped[Product] = relationship("Product")


class Invoice(AuditedSoftDeleteMixin, Base):
    __tablename__ = "invoices"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    invoice_number: Mapped[str | None] = mapped_column(String(32), unique=True, nullable=True)
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="confirmed",
        server_default=sa.text("'confirmed'"),
    )
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), nullable=False)
    subtotal: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    discount_amount: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    tax_rate: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    tax_amount: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    total: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    customer: Mapped[Customer] = relationship(
        "Customer",
        back_populates="invoices",
    )
    items: Mapped[list[InvoiceItem]] = relationship(
        "InvoiceItem",
        back_populates="invoice",
        cascade="all, delete-orphan",
    )

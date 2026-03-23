from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class InvoiceLineIn(BaseModel):
    product_id: int = Field(ge=1)
    quantity: int = Field(ge=1)
    discount_percent: float = Field(default=0.0, ge=0, le=100)


class InvoiceCreate(BaseModel):
    customer_id: int = Field(ge=1)
    items: list[InvoiceLineIn] = Field(min_length=1)
    notes: str | None = None
    discount_amount: float = Field(default=0.0, ge=0, description="Descuento global en importe")
    tax_rate: float = Field(
        default=0.0,
        ge=0,
        le=100,
        description="Tipo impositivo (porcentaje, ej. 21 para IVA 21%)",
    )


class InvoiceItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    quantity: int
    price: float
    discount_percent: float = 0.0
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None
    created_by_id: int | None = None
    updated_by_id: int | None = None
    deleted_by_id: int | None = None


class InvoiceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    invoice_number: str | None = None
    status: str
    customer_id: int
    subtotal: float
    discount_amount: float
    tax_rate: float
    tax_amount: float
    total: float
    notes: str | None = None
    items: list[InvoiceItemRead] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None
    created_by_id: int | None = None
    updated_by_id: int | None = None
    deleted_by_id: int | None = None

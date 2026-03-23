from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ProductCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    sku: str | None = Field(default=None, max_length=64)
    description: str | None = None
    price: float = Field(gt=0)
    initial_stock: int = Field(default=0, ge=0)


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    sku: str | None = Field(default=None, max_length=64)
    description: str | None = None
    price: float | None = Field(default=None, gt=0)


class ProductRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sku: str | None = None
    name: str
    description: str | None = None
    price: float
    stock: int = 0
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None
    created_by_id: int | None = None
    updated_by_id: int | None = None
    deleted_by_id: int | None = None

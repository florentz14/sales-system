from pydantic import BaseModel


class DailySalesRow(BaseModel):
    day: str
    total: float
    invoices: int


class ProductRankRow(BaseModel):
    product_id: int
    name: str
    units: int
    revenue: float


class CustomerRankRow(BaseModel):
    customer_id: int
    name: str
    invoices: int
    total: float


class SalesKpis(BaseModel):
    invoice_count: int
    total_revenue: float
    total_tax: float
    avg_ticket: float


class ReportSummary(BaseModel):
    start: str
    end: str
    period_label: str
    kpis: SalesKpis
    daily: list[DailySalesRow]
    products: list[ProductRankRow]
    customers: list[CustomerRankRow]

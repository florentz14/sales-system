from __future__ import annotations

from datetime import date, datetime, time, timedelta
from typing import Any

from sqlalchemy import Float, func, select
from sqlalchemy.orm import Session

from app.db.models.customer import Customer
from app.db.models.invoice import Invoice, InvoiceItem
from app.db.models.product import Product


def resolve_period(
    *,
    days: int = 30,
    start: date | None = None,
    end: date | None = None,
) -> tuple[datetime, datetime]:
    if start is not None and end is not None:
        return (
            datetime.combine(start, time.min),
            datetime.combine(end, time.max),
        )
    end_d = date.today()
    start_d = end_d - timedelta(days=max(1, days) - 1)
    return (
        datetime.combine(start_d, time.min),
        datetime.combine(end_d, time.max),
    )


def sales_daily(db: Session, start_dt: datetime, end_dt: datetime) -> list[dict[str, Any]]:
    day_col = func.date(Invoice.created_at)
    stmt = (
        select(
            day_col.label("day"),
            func.coalesce(func.sum(Invoice.total), 0.0).label("total"),
            func.count(Invoice.id).label("invoices"),
        )
        .where(
            Invoice.deleted_at.is_(None),
            Invoice.created_at >= start_dt,
            Invoice.created_at <= end_dt,
        )
        .group_by(day_col)
        .order_by(day_col)
    )
    rows = db.execute(stmt).all()
    out: list[dict[str, Any]] = []
    for r in rows:
        d = r.day
        out.append(
            {
                "day": str(d) if d is not None else "",
                "total": float(r.total or 0),
                "invoices": int(r.invoices or 0),
            }
        )
    return out


def sales_kpis(db: Session, start_dt: datetime, end_dt: datetime) -> dict[str, Any]:
    stmt = select(
        func.count(Invoice.id),
        func.coalesce(func.sum(Invoice.total), 0.0),
        func.coalesce(func.sum(Invoice.tax_amount), 0.0),
    ).where(
        Invoice.deleted_at.is_(None),
        Invoice.created_at >= start_dt,
        Invoice.created_at <= end_dt,
    )
    row = db.execute(stmt).one()
    n = int(row[0] or 0)
    gross = float(row[1] or 0)
    tax = float(row[2] or 0)
    return {
        "invoice_count": n,
        "total_revenue": round(gross, 2),
        "total_tax": round(tax, 2),
        "avg_ticket": round(gross / n, 2) if n else 0.0,
    }


def _line_revenue_expr():
    q = func.cast(InvoiceItem.quantity, Float)
    p = func.cast(InvoiceItem.price, Float)
    d = func.cast(InvoiceItem.discount_percent, Float)
    return q * p * (1.0 - d / 100.0)


def product_rankings(
    db: Session,
    start_dt: datetime,
    end_dt: datetime,
    *,
    limit: int = 20,
) -> list[dict[str, Any]]:
    rev = _line_revenue_expr()
    stmt = (
        select(
            Product.id.label("product_id"),
            Product.name.label("name"),
            func.sum(InvoiceItem.quantity).label("units"),
            func.coalesce(func.sum(rev), 0.0).label("revenue"),
        )
        .select_from(InvoiceItem)
        .join(Invoice, InvoiceItem.invoice_id == Invoice.id)
        .join(Product, InvoiceItem.product_id == Product.id)
        .where(
            Invoice.deleted_at.is_(None),
            InvoiceItem.deleted_at.is_(None),
            Product.deleted_at.is_(None),
            Invoice.created_at >= start_dt,
            Invoice.created_at <= end_dt,
        )
        .group_by(Product.id, Product.name)
        .order_by(func.sum(rev).desc())
        .limit(limit)
    )
    return [
        {
            "product_id": int(r.product_id),
            "name": str(r.name),
            "units": int(r.units or 0),
            "revenue": round(float(r.revenue or 0), 2),
        }
        for r in db.execute(stmt).all()
    ]


def customer_rankings(
    db: Session,
    start_dt: datetime,
    end_dt: datetime,
    *,
    limit: int = 20,
) -> list[dict[str, Any]]:
    stmt = (
        select(
            Customer.id.label("customer_id"),
            Customer.name.label("name"),
            func.count(Invoice.id).label("invoices"),
            func.coalesce(func.sum(Invoice.total), 0.0).label("total"),
        )
        .join(Invoice, Invoice.customer_id == Customer.id)
        .where(
            Invoice.deleted_at.is_(None),
            Customer.deleted_at.is_(None),
            Invoice.created_at >= start_dt,
            Invoice.created_at <= end_dt,
        )
        .group_by(Customer.id, Customer.name)
        .order_by(func.sum(Invoice.total).desc())
        .limit(limit)
    )
    return [
        {
            "customer_id": int(r.customer_id),
            "name": str(r.name),
            "invoices": int(r.invoices or 0),
            "total": round(float(r.total or 0), 2),
        }
        for r in db.execute(stmt).all()
    ]


def load_report_bundle(
    db: Session,
    *,
    days: int = 30,
    start: date | None = None,
    end: date | None = None,
    ranking_limit: int = 20,
) -> dict[str, Any]:
    start_dt, end_dt = resolve_period(days=days, start=start, end=end)
    daily = sales_daily(db, start_dt, end_dt)
    kpis = sales_kpis(db, start_dt, end_dt)
    products = product_rankings(
        db, start_dt, end_dt, limit=ranking_limit
    )
    customers = customer_rankings(
        db, start_dt, end_dt, limit=ranking_limit
    )
    period_label = f"{start_dt.date()} — {end_dt.date()}"
    return {
        "start": start_dt.isoformat(),
        "end": end_dt.isoformat(),
        "period_label": period_label,
        "daily": daily,
        "kpis": kpis,
        "products": products,
        "customers": customers,
    }

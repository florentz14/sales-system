from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.customer import Customer
from app.db.models.invoice import Invoice
from app.schemas.customer import CustomerCreate, CustomerUpdate
from app.utils.audit import apply_create_audit, apply_soft_delete, apply_update_audit


def create_customer(
    db: Session,
    data: CustomerCreate,
    *,
    actor_id: int | None = None,
) -> Customer:
    c = Customer(
        name=data.name,
        email=data.email,
        phone=data.phone,
        address=data.address,
    )
    apply_create_audit(c, user_id=actor_id)
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


def update_customer(
    db: Session,
    customer_id: int,
    data: CustomerUpdate,
    *,
    actor_id: int | None = None,
) -> Customer | None:
    c = db.get(Customer, customer_id)
    if c is None or c.deleted_at is not None:
        return None
    if data.name is not None:
        c.name = data.name
    if data.email is not None:
        c.email = data.email
    if data.phone is not None:
        c.phone = data.phone
    if data.address is not None:
        c.address = data.address
    apply_update_audit(c, user_id=actor_id)
    db.commit()
    db.refresh(c)
    return c


def list_customers(db: Session, skip: int = 0, limit: int = 200) -> list[Customer]:
    stmt = (
        select(Customer)
        .where(Customer.deleted_at.is_(None))
        .order_by(Customer.id)
        .offset(skip)
        .limit(limit)
    )
    return list(db.scalars(stmt).all())


def get_customer(db: Session, customer_id: int) -> Customer | None:
    c = db.get(Customer, customer_id)
    if c is None or c.deleted_at is not None:
        return None
    return c


def soft_delete_customer(
    db: Session,
    customer_id: int,
    *,
    actor_id: int | None = None,
) -> bool:
    c = db.get(Customer, customer_id)
    if c is None or c.deleted_at is not None:
        return False
    has_open_invoice = db.scalar(
        select(Invoice.id).where(
            Invoice.customer_id == customer_id,
            Invoice.deleted_at.is_(None),
        ).limit(1)
    )
    if has_open_invoice is not None:
        raise ValueError(
            "Customer has active invoices; delete invoices first or void them"
        )
    apply_soft_delete(c, user_id=actor_id)
    db.commit()
    return True

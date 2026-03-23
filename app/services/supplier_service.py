from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.supplier import Supplier
from app.utils.audit import apply_create_audit, apply_soft_delete, apply_update_audit


def create_supplier(
    db: Session,
    name: str,
    *,
    email: str | None = None,
    phone: str | None = None,
    address: str | None = None,
    actor_id: int | None = None,
) -> Supplier:
    s = Supplier(name=name, email=email, phone=phone, address=address)
    apply_create_audit(s, user_id=actor_id)
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


def update_supplier(
    db: Session,
    supplier_id: int,
    *,
    name: str | None = None,
    email: str | None = None,
    phone: str | None = None,
    address: str | None = None,
    actor_id: int | None = None,
) -> Supplier | None:
    s = db.get(Supplier, supplier_id)
    if s is None or s.deleted_at is not None:
        return None
    if name is not None:
        s.name = name
    if email is not None:
        s.email = email
    if phone is not None:
        s.phone = phone
    if address is not None:
        s.address = address
    apply_update_audit(s, user_id=actor_id)
    db.commit()
    db.refresh(s)
    return s


def list_suppliers(db: Session, skip: int = 0, limit: int = 200) -> list[Supplier]:
    stmt = (
        select(Supplier)
        .where(Supplier.deleted_at.is_(None))
        .order_by(Supplier.id)
        .offset(skip)
        .limit(limit)
    )
    return list(db.scalars(stmt).all())


def get_supplier(db: Session, supplier_id: int) -> Supplier | None:
    s = db.get(Supplier, supplier_id)
    if s is None or s.deleted_at is not None:
        return None
    return s


def soft_delete_supplier(
    db: Session,
    supplier_id: int,
    *,
    actor_id: int | None = None,
) -> bool:
    s = db.get(Supplier, supplier_id)
    if s is None or s.deleted_at is not None:
        return False
    apply_soft_delete(s, user_id=actor_id)
    db.commit()
    return True

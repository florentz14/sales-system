from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.inventory import Inventory
from app.utils.audit import apply_update_audit


def get_stock(db: Session, product_id: int) -> int:
    rows = db.scalars(select(Inventory).where(Inventory.product_id == product_id)).all()
    return sum(r.quantity for r in rows)


def ensure_inventory_row(db: Session, product_id: int) -> Inventory:
    row = db.scalar(
        select(Inventory).where(Inventory.product_id == product_id).limit(1)
    )
    if row is None:
        row = Inventory(product_id=product_id, quantity=0)
        db.add(row)
        db.commit()
        db.refresh(row)
    return row


def set_product_stock(
    db: Session,
    product_id: int,
    quantity: int,
    *,
    actor_id: int | None = None,
) -> Inventory | None:
    """Set quantity on the first active inventory row for the product."""
    if quantity < 0:
        raise ValueError("Stock cannot be negative")
    inv = db.scalar(
        select(Inventory).where(
            Inventory.product_id == product_id,
            Inventory.deleted_at.is_(None),
        )
    )
    if inv is None:
        return None
    inv.quantity = quantity
    apply_update_audit(inv, user_id=actor_id)
    db.commit()
    db.refresh(inv)
    return inv

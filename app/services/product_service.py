from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.inventory import Inventory
from app.db.models.invoice import InvoiceItem
from app.db.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate
from app.utils.audit import apply_create_audit, apply_soft_delete, apply_update_audit


def _total_stock(db: Session, product_id: int) -> int:
    stmt = select(Inventory).where(
        Inventory.product_id == product_id,
        Inventory.deleted_at.is_(None),
    )
    rows = db.scalars(stmt).all()
    return sum(r.quantity for r in rows)


def list_products(db: Session) -> list[tuple[Product, int]]:
    stmt = (
        select(Product)
        .where(Product.deleted_at.is_(None))
        .order_by(Product.id)
    )
    products = db.scalars(stmt).all()
    return [(p, _total_stock(db, p.id)) for p in products]


def get_product(db: Session, product_id: int) -> tuple[Product, int] | None:
    p = db.get(Product, product_id)
    if p is None or p.deleted_at is not None:
        return None
    return p, _total_stock(db, p.id)


def create_product(
    db: Session,
    data: ProductCreate,
    *,
    actor_id: int | None = None,
) -> tuple[Product, int]:
    p = Product(
        name=data.name,
        price=data.price,
        sku=data.sku,
        description=data.description,
    )
    apply_create_audit(p, user_id=actor_id)
    db.add(p)
    db.flush()
    inv = Inventory(product_id=p.id, quantity=data.initial_stock)
    apply_create_audit(inv, user_id=actor_id)
    db.add(inv)
    db.commit()
    db.refresh(p)
    return p, _total_stock(db, p.id)


def update_product(
    db: Session,
    product_id: int,
    data: ProductUpdate,
    *,
    actor_id: int | None = None,
) -> tuple[Product, int] | None:
    p = db.get(Product, product_id)
    if p is None or p.deleted_at is not None:
        return None
    if data.name is not None:
        p.name = data.name
    if data.price is not None:
        p.price = data.price
    if data.sku is not None:
        p.sku = data.sku
    if data.description is not None:
        p.description = data.description
    apply_update_audit(p, user_id=actor_id)
    db.commit()
    db.refresh(p)
    return p, _total_stock(db, p.id)


def delete_product(
    db: Session,
    product_id: int,
    *,
    actor_id: int | None = None,
) -> bool:
    p = db.get(Product, product_id)
    if p is None or p.deleted_at is not None:
        return False
    if db.scalar(
        select(InvoiceItem.id).where(
            InvoiceItem.product_id == product_id,
            InvoiceItem.deleted_at.is_(None),
        ).limit(1)
    ):
        raise ValueError("Cannot delete product referenced by invoices")
    for inv in db.scalars(
        select(Inventory).where(
            Inventory.product_id == product_id,
            Inventory.deleted_at.is_(None),
        )
    ):
        apply_soft_delete(inv, user_id=actor_id)
    apply_soft_delete(p, user_id=actor_id)
    db.commit()
    return True

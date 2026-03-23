from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.models.inventory import Inventory
from app.db.models.invoice import Invoice, InvoiceItem
from app.db.models.product import Product
from app.utils.audit import apply_create_audit, apply_soft_delete, apply_update_audit


def _money(value: float) -> float:
    return round(float(value), 2)


def create_invoice(
    db: Session,
    customer_id: int,
    items: list[dict],
    *,
    notes: str | None = None,
    discount_amount: float = 0.0,
    tax_rate: float = 0.0,
    actor_id: int | None = None,
) -> Invoice:
    """Create an invoice, decrement inventory, and persist in one transaction.

    Per line: ``discount_percent`` (0–100) reduces that line's extension before summing.
    Global ``discount_amount`` is subtracted from the subtotal before applying ``tax_rate``.
    """
    disc_global = _money(max(0.0, float(discount_amount)))
    tax_pct = max(0.0, min(100.0, float(tax_rate)))

    invoice = Invoice(
        customer_id=customer_id,
        subtotal=0.0,
        discount_amount=disc_global,
        tax_rate=tax_pct,
        tax_amount=0.0,
        total=0.0,
        notes=notes,
    )
    apply_create_audit(invoice, user_id=actor_id)
    db.add(invoice)
    db.flush()
    invoice.invoice_number = f"INV-{invoice.id:08d}"
    subtotal = 0.0

    try:
        for item in items:
            product = db.get(Product, item["product_id"])
            if product is None or product.deleted_at is not None:
                raise ValueError("Product not found")

            inventory = db.scalar(
                select(Inventory).where(
                    Inventory.product_id == product.id,
                    Inventory.deleted_at.is_(None),
                )
            )
            if inventory is None or inventory.quantity < item["quantity"]:
                raise ValueError("Not enough stock")

            qty = int(item["quantity"])
            line_disc = max(0.0, min(100.0, float(item.get("discount_percent") or 0.0)))
            unit = float(product.price)
            line_gross = _money(qty * unit)
            line_net = _money(line_gross * (1.0 - line_disc / 100.0))

            inventory.quantity -= qty
            apply_update_audit(inventory, user_id=actor_id)

            subtotal = _money(subtotal + line_net)

            invoice_item = InvoiceItem(
                product_id=product.id,
                quantity=qty,
                price=unit,
                discount_percent=line_disc,
            )
            apply_create_audit(invoice_item, user_id=actor_id)
            invoice.items.append(invoice_item)

        if disc_global > subtotal + 0.001:
            raise ValueError("El descuento global no puede superar el subtotal")

        taxable = _money(subtotal - disc_global)
        tax_amt = _money(taxable * (tax_pct / 100.0))
        total = _money(taxable + tax_amt)

        invoice.subtotal = subtotal
        invoice.discount_amount = disc_global
        invoice.tax_rate = tax_pct
        invoice.tax_amount = tax_amt
        invoice.total = total
        db.commit()
        db.refresh(invoice)
        return invoice
    except Exception:
        db.rollback()
        raise


def list_invoices(db: Session, skip: int = 0, limit: int = 100) -> list[Invoice]:
    stmt = (
        select(Invoice)
        .where(Invoice.deleted_at.is_(None))
        .options(
            selectinload(Invoice.items),
            selectinload(Invoice.customer),
        )
        .order_by(Invoice.id.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(db.scalars(stmt).all())


def get_invoice(db: Session, invoice_id: int) -> Invoice | None:
    stmt = (
        select(Invoice)
        .where(Invoice.id == invoice_id, Invoice.deleted_at.is_(None))
        .options(
            selectinload(Invoice.items),
            selectinload(Invoice.customer),
        )
    )
    return db.scalars(stmt).first()


def soft_delete_invoice(
    db: Session,
    invoice_id: int,
    *,
    actor_id: int | None = None,
) -> bool:
    inv = db.get(Invoice, invoice_id)
    if inv is None or inv.deleted_at is not None:
        return False
    inv.status = "voided"
    for line in inv.items:
        if line.deleted_at is None:
            apply_soft_delete(line, user_id=actor_id)
    apply_soft_delete(inv, user_id=actor_id)
    db.commit()
    return True

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.core import permissions as perms
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.invoice import InvoiceCreate, InvoiceItemRead, InvoiceRead
from app.services import customer_service, invoice_service

router = APIRouter(prefix="/invoices", tags=["invoices"])


def _invoice_to_read(inv) -> InvoiceRead:
    items = [
        InvoiceItemRead(
            id=i.id,
            product_id=i.product_id,
            quantity=i.quantity,
            price=float(i.price),
            discount_percent=float(i.discount_percent),
            created_at=i.created_at,
            updated_at=i.updated_at,
            deleted_at=i.deleted_at,
            created_by_id=i.created_by_id,
            updated_by_id=i.updated_by_id,
            deleted_by_id=i.deleted_by_id,
        )
        for i in inv.items
        if i.deleted_at is None
    ]
    return InvoiceRead(
        id=inv.id,
        invoice_number=inv.invoice_number,
        status=inv.status,
        customer_id=inv.customer_id,
        total=float(inv.total),
        notes=inv.notes,
        items=items,
        created_at=inv.created_at,
        updated_at=inv.updated_at,
        deleted_at=inv.deleted_at,
        created_by_id=inv.created_by_id,
        updated_by_id=inv.updated_by_id,
        deleted_by_id=inv.deleted_by_id,
    )


@router.get("/", response_model=list[InvoiceRead])
def list_invoices(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(perms.READ_INVOICE)),
) -> list[InvoiceRead]:
    return [_invoice_to_read(i) for i in invoice_service.list_invoices(db, skip=skip, limit=limit)]


@router.get("/{invoice_id}", response_model=InvoiceRead)
def get_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(perms.READ_INVOICE)),
) -> InvoiceRead:
    inv = invoice_service.get_invoice(db, invoice_id)
    if inv is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    return _invoice_to_read(inv)


@router.post("/", response_model=InvoiceRead, status_code=status.HTTP_201_CREATED)
def create_invoice(
    body: InvoiceCreate,
    db: Session = Depends(get_db),
    current: User = Depends(require_permission(perms.CREATE_INVOICE)),
) -> InvoiceRead:
    if customer_service.get_customer(db, body.customer_id) is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Customer not found",
        )
    try:
        items = [
            {
                "product_id": i.product_id,
                "quantity": i.quantity,
                "discount_percent": i.discount_percent,
            }
            for i in body.items
        ]
        inv = invoice_service.create_invoice(
            db,
            body.customer_id,
            items,
            notes=body.notes,
            discount_amount=body.discount_amount,
            tax_rate=body.tax_rate,
            actor_id=current.id,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    inv = invoice_service.get_invoice(db, inv.id)
    assert inv is not None
    return _invoice_to_read(inv)


@router.delete("/{invoice_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(require_permission(perms.DELETE_INVOICE)),
) -> None:
    ok = invoice_service.soft_delete_invoice(db, invoice_id, actor_id=current.id)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found",
        )

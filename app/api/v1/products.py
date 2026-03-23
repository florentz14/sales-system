from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.core import permissions as perms
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.product import ProductCreate, ProductRead, ProductUpdate
from app.services import product_service

router = APIRouter(prefix="/products", tags=["products"])


def _to_read(row: tuple) -> ProductRead:
    p, stock = row
    return ProductRead(
        id=p.id,
        sku=p.sku,
        name=p.name,
        description=p.description,
        price=float(p.price),
        stock=stock,
        created_at=p.created_at,
        updated_at=p.updated_at,
        deleted_at=p.deleted_at,
        created_by_id=p.created_by_id,
        updated_by_id=p.updated_by_id,
        deleted_by_id=p.deleted_by_id,
    )


@router.get("/", response_model=list[ProductRead])
def list_products(
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(perms.READ_PRODUCT)),
) -> list[ProductRead]:
    return [_to_read(row) for row in product_service.list_products(db)]


@router.get("/{product_id}", response_model=ProductRead)
def get_product(
    product_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(perms.READ_PRODUCT)),
) -> ProductRead:
    row = product_service.get_product(db, product_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return _to_read(row)


@router.post("/", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
def create_product(
    body: ProductCreate,
    db: Session = Depends(get_db),
    current: User = Depends(require_permission(perms.CREATE_PRODUCT)),
) -> ProductRead:
    row = product_service.create_product(db, body, actor_id=current.id)
    return _to_read(row)


@router.patch("/{product_id}", response_model=ProductRead)
def update_product(
    product_id: int,
    body: ProductUpdate,
    db: Session = Depends(get_db),
    current: User = Depends(require_permission(perms.UPDATE_PRODUCT)),
) -> ProductRead:
    if all(
        getattr(body, f) is None
        for f in ("name", "price", "sku", "description")
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide at least one field to update",
        )
    row = product_service.update_product(
        db, product_id, body, actor_id=current.id
    )
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return _to_read(row)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(require_permission(perms.DELETE_PRODUCT)),
) -> None:
    try:
        ok = product_service.delete_product(db, product_id, actor_id=current.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

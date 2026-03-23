from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.core import permissions as perms
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.customer import CustomerCreate, CustomerRead, CustomerUpdate
from app.services import customer_service

router = APIRouter(prefix="/customers", tags=["customers"])


@router.get("/", response_model=list[CustomerRead])
def list_customers(
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(perms.READ_CUSTOMER)),
) -> list[CustomerRead]:
    return customer_service.list_customers(db)


@router.get("/{customer_id}", response_model=CustomerRead)
def get_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(perms.READ_CUSTOMER)),
) -> CustomerRead:
    c = customer_service.get_customer(db, customer_id)
    if c is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
    return c


@router.post("/", response_model=CustomerRead, status_code=status.HTTP_201_CREATED)
def create_customer(
    body: CustomerCreate,
    db: Session = Depends(get_db),
    current: User = Depends(require_permission(perms.CREATE_CUSTOMER)),
) -> CustomerRead:
    return customer_service.create_customer(db, body, actor_id=current.id)


@router.patch("/{customer_id}", response_model=CustomerRead)
def patch_customer(
    customer_id: int,
    body: CustomerUpdate,
    db: Session = Depends(get_db),
    current: User = Depends(require_permission(perms.UPDATE_CUSTOMER)),
) -> CustomerRead:
    if all(
        getattr(body, f) is None
        for f in ("name", "email", "phone", "address")
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide at least one field to update",
        )
    c = customer_service.update_customer(
        db, customer_id, body, actor_id=current.id
    )
    if c is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found",
        )
    return c


@router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(require_permission(perms.DELETE_CUSTOMER)),
) -> None:
    try:
        ok = customer_service.soft_delete_customer(
            db, customer_id, actor_id=current.id
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found",
        )

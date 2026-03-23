from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.core import permissions as perms
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.user import UserCreate, UserRead
from app.services import user_service

router = APIRouter(prefix="/users", tags=["users"])


def _user_to_read(user: User) -> UserRead:
    return UserRead(
        id=user.id,
        username=user.username,
        is_active=user.is_active,
        roles=[r.name for r in user.roles],
    )


@router.post("/", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(
    body: UserCreate,
    db: Session = Depends(get_db),
    current: User = Depends(require_permission(perms.MANAGE_USERS)),
) -> UserRead:
    try:
        user = user_service.create_user(
            db,
            username=body.username,
            password=body.password,
            role_names=body.role_names,
            actor_id=current.id,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    user = user_service.get_user_with_rbac(db, user.id)
    assert user is not None
    return _user_to_read(user)

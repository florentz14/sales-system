from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.security import create_access_token
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.auth import Token
from app.schemas.user import UserRead
from app.services import user_service

router = APIRouter()


def _user_to_read(user) -> UserRead:
    return UserRead(
        id=user.id,
        username=user.username,
        is_active=user.is_active,
        roles=[r.name for r in user.roles],
    )


@router.post("/login", response_model=Token)
def login(
    db: Session = Depends(get_db),
    form: OAuth2PasswordRequestForm = Depends(),
) -> Token:
    user = user_service.authenticate(db, form.username, form.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    return Token(access_token=create_access_token(user.id))


@router.get("/me", response_model=UserRead)
def read_me(current: User = Depends(get_current_user)) -> UserRead:
    return _user_to_read(current)

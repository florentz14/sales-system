from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.security import hash_password, verify_password
from app.db.models.role import Role
from app.db.models.user import User
from app.utils.audit import apply_create_audit


def get_user_with_rbac(db: Session, user_id: int) -> User | None:
    stmt = (
        select(User)
        .where(User.id == user_id, User.deleted_at.is_(None))
        .options(
            selectinload(User.roles).selectinload(Role.permissions),
        )
    )
    return db.scalars(stmt).first()


def get_by_username(db: Session, username: str) -> User | None:
    stmt = (
        select(User)
        .where(User.username == username, User.deleted_at.is_(None))
        .options(
            selectinload(User.roles).selectinload(Role.permissions),
        )
    )
    return db.scalars(stmt).first()


def authenticate(db: Session, username: str, password: str) -> User | None:
    user = get_by_username(db, username)
    if user is None or not user.is_active:
        return None
    if not verify_password(password, user.password):
        return None
    return user


def create_user(
    db: Session,
    *,
    username: str,
    password: str,
    role_names: list[str],
    actor_id: int | None = None,
) -> User:
    if get_by_username(db, username):
        raise ValueError("Username already taken")
    user = User(username=username, password=hash_password(password), is_active=True)
    apply_create_audit(user, user_id=actor_id)
    if role_names:
        roles = list(
            db.scalars(
                select(Role).where(
                    Role.name.in_(role_names),
                    Role.deleted_at.is_(None),
                )
            ).all()
        )
        found = {r.name for r in roles}
        missing = set(role_names) - found
        if missing:
            raise ValueError(f"Unknown roles: {', '.join(sorted(missing))}")
        user.roles.extend(roles)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

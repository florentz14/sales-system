from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.models.permission import Permission
from app.db.models.role import Role


def list_permissions(db: Session) -> list[Permission]:
    stmt = (
        select(Permission)
        .where(Permission.deleted_at.is_(None))
        .order_by(Permission.name)
    )
    return list(db.scalars(stmt).all())


def list_roles(db: Session) -> list[Role]:
    stmt = (
        select(Role)
        .where(Role.deleted_at.is_(None))
        .options(selectinload(Role.permissions))
        .order_by(Role.name)
    )
    return list(db.scalars(stmt).all())

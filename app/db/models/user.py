from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.mixins import AuditedSoftDeleteMixin
from app.db.models.rbac import user_roles

if TYPE_CHECKING:
    from app.db.models.profile import Profile
    from app.db.models.role import Role


class User(AuditedSoftDeleteMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    roles: Mapped[list[Role]] = relationship(
        "Role",
        secondary=user_roles,
        back_populates="users",
    )
    profile: Mapped[Profile | None] = relationship(
        "Profile",
        foreign_keys="Profile.user_id",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )

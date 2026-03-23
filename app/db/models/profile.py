from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.mixins import AuditedSoftDeleteMixin

if TYPE_CHECKING:
    from app.db.models.user import User


class Profile(AuditedSoftDeleteMixin, Base):
    __tablename__ = "profiles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    bio: Mapped[str | None] = mapped_column(String(2000), nullable=True)

    user: Mapped[User] = relationship(
        "User",
        foreign_keys=[user_id],
        back_populates="profile",
    )

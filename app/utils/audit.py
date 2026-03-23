from __future__ import annotations

from datetime import UTC, datetime


def apply_create_audit(entity: object, *, user_id: int | None) -> None:
    if user_id is None:
        return
    setattr(entity, "created_by_id", user_id)
    setattr(entity, "updated_by_id", user_id)


def apply_update_audit(entity: object, *, user_id: int | None) -> None:
    if user_id is None:
        return
    setattr(entity, "updated_by_id", user_id)


def apply_soft_delete(entity: object, *, user_id: int | None) -> None:
    setattr(entity, "deleted_at", datetime.now(UTC))
    setattr(entity, "deleted_by_id", user_id)
    if user_id is not None:
        setattr(entity, "updated_by_id", user_id)

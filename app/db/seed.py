"""Idempotent RBAC + default admin user + demo customer."""

from __future__ import annotations

from collections.abc import Callable

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.core.permissions import (
    ALL_PERMISSIONS,
    CREATE_CUSTOMER,
    CREATE_INVOICE,
    PERMISSION_DESCRIPTIONS,
    READ_CUSTOMER,
    READ_INVOICE,
    READ_PRODUCT,
    READ_REPORT,
    ROLE_DESCRIPTIONS,
)
from app.core.security import hash_password
from app.db.models.customer import Customer
from app.db.models.permission import Permission
from app.db.models.role import Role
from app.db.models.user import User


def run_seed(session_factory: Callable[[], Session] | sessionmaker[Session]) -> None:
    db = session_factory()
    try:
        for name in ALL_PERMISSIONS:
            p = db.scalar(
                select(Permission).where(
                    Permission.name == name,
                    Permission.deleted_at.is_(None),
                )
            )
            desc = PERMISSION_DESCRIPTIONS.get(name)
            if p is None:
                db.add(Permission(name=name, description=desc))
            elif desc and not (p.description and p.description.strip()):
                p.description = desc
        db.commit()

        all_perms = list(
            db.scalars(select(Permission).where(Permission.deleted_at.is_(None))).all()
        )
        perm_by_name = {p.name: p for p in all_perms}

        admin_role = db.scalar(
            select(Role).where(Role.name == "admin", Role.deleted_at.is_(None))
        )
        if admin_role is None:
            admin_role = Role(
                name="admin",
                description=ROLE_DESCRIPTIONS.get("admin"),
            )
            db.add(admin_role)
            db.flush()
        elif ROLE_DESCRIPTIONS.get("admin") and not (
            admin_role.description and admin_role.description.strip()
        ):
            admin_role.description = ROLE_DESCRIPTIONS["admin"]
        admin_role.permissions.clear()
        admin_role.permissions.extend(all_perms)

        cashier_role = db.scalar(
            select(Role).where(Role.name == "cashier", Role.deleted_at.is_(None))
        )
        if cashier_role is None:
            cashier_role = Role(
                name="cashier",
                description=ROLE_DESCRIPTIONS.get("cashier"),
            )
            db.add(cashier_role)
            db.flush()
        elif ROLE_DESCRIPTIONS.get("cashier") and not (
            cashier_role.description and cashier_role.description.strip()
        ):
            cashier_role.description = ROLE_DESCRIPTIONS["cashier"]
        cashier_role.permissions.clear()
        for key in (
            READ_PRODUCT,
            CREATE_INVOICE,
            READ_INVOICE,
            CREATE_CUSTOMER,
            READ_CUSTOMER,
        ):
            if key in perm_by_name:
                cashier_role.permissions.append(perm_by_name[key])

        viewer_role = db.scalar(
            select(Role).where(Role.name == "viewer", Role.deleted_at.is_(None))
        )
        if viewer_role is None:
            viewer_role = Role(
                name="viewer",
                description=ROLE_DESCRIPTIONS.get("viewer"),
            )
            db.add(viewer_role)
            db.flush()
        elif ROLE_DESCRIPTIONS.get("viewer") and not (
            viewer_role.description and viewer_role.description.strip()
        ):
            viewer_role.description = ROLE_DESCRIPTIONS["viewer"]
        viewer_role.permissions.clear()
        for key in (READ_PRODUCT, READ_INVOICE, READ_CUSTOMER, READ_REPORT):
            if key in perm_by_name:
                viewer_role.permissions.append(perm_by_name[key])

        db.commit()

        if (
            db.scalar(
                select(User.id).where(
                    User.username == "admin",
                    User.deleted_at.is_(None),
                )
            )
            is None
        ):
            admin_user = User(
                username="admin",
                password=hash_password("admin"),
                is_active=True,
            )
            admin_user.roles.append(admin_role)
            db.add(admin_user)
            db.commit()

        if (
            db.scalar(
                select(Customer.id).where(
                    Customer.name == "Walk-in",
                    Customer.deleted_at.is_(None),
                )
            )
            is None
        ):
            db.add(Customer(name="Walk-in"))
            db.commit()
    finally:
        db.close()

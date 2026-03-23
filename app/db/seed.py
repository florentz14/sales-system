"""Seeder idempotente: permisos, roles, usuarios, perfiles, catálogo y factura demo."""

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
from app.db.models.invoice import Invoice
from app.db.models.permission import Permission
from app.db.models.product import Product
from app.db.models.profile import Profile
from app.db.models.role import Role
from app.db.models.supplier import Supplier
from app.db.models.user import User
from app.schemas.product import ProductCreate
from app.services import invoice_service, product_service
from app.utils.audit import apply_create_audit

_SEED_INVOICE_MARKER = "Factura de demostración (seed)."
_DEMO_SUPPLIER_NAME = "Proveedor central (seed)"
_DEMO_CUSTOMER_NAME = "Cliente demo (seed)"

_DEMO_USERS: tuple[tuple[str, str], ...] = (
    ("admin", "admin"),
    ("cashier", "cashier"),
    ("viewer", "viewer"),
)

_PROFILE_DISPLAY_NAMES: dict[str, str] = {
    "admin": "Administrador",
    "cashier": "Cajero demo",
    "viewer": "Consulta demo",
}

_DEMO_PRODUCTS: tuple[dict[str, object], ...] = (
    {
        "sku": "SEED-001",
        "name": "Producto demo A",
        "description": "Artículo de prueba (seed)",
        "price": 10.5,
        "initial_stock": 50,
    },
    {
        "sku": "SEED-002",
        "name": "Producto demo B",
        "description": "Artículo de prueba (seed)",
        "price": 25.0,
        "initial_stock": 30,
    },
)


def _seed_permissions(db: Session) -> dict[str, Permission]:
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
    rows = list(db.scalars(select(Permission).where(Permission.deleted_at.is_(None))).all())
    return {p.name: p for p in rows}


def _seed_roles(db: Session, perm_by_name: dict[str, Permission]) -> tuple[Role, Role, Role]:
    admin_role = db.scalar(select(Role).where(Role.name == "admin", Role.deleted_at.is_(None)))
    if admin_role is None:
        admin_role = Role(name="admin", description=ROLE_DESCRIPTIONS.get("admin"))
        db.add(admin_role)
        db.flush()
    elif ROLE_DESCRIPTIONS.get("admin") and not (
        admin_role.description and admin_role.description.strip()
    ):
        admin_role.description = ROLE_DESCRIPTIONS["admin"]
    admin_role.permissions.clear()
    admin_role.permissions.extend(perm_by_name.values())

    cashier_role = db.scalar(select(Role).where(Role.name == "cashier", Role.deleted_at.is_(None)))
    if cashier_role is None:
        cashier_role = Role(name="cashier", description=ROLE_DESCRIPTIONS.get("cashier"))
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

    viewer_role = db.scalar(select(Role).where(Role.name == "viewer", Role.deleted_at.is_(None)))
    if viewer_role is None:
        viewer_role = Role(name="viewer", description=ROLE_DESCRIPTIONS.get("viewer"))
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
    return admin_role, cashier_role, viewer_role


def _ensure_user(
    db: Session,
    username: str,
    password_plain: str,
    role: Role,
) -> User:
    u = db.scalar(
        select(User).where(User.username == username, User.deleted_at.is_(None))
    )
    if u is not None:
        return u
    user = User(username=username, password=hash_password(password_plain), is_active=True)
    user.roles.append(role)
    db.add(user)
    db.flush()
    return user


def _seed_demo_users(
    db: Session,
    admin_role: Role,
    cashier_role: Role,
    viewer_role: Role,
) -> None:
    role_by_username = {
        "admin": admin_role,
        "cashier": cashier_role,
        "viewer": viewer_role,
    }
    for username, password_plain in _DEMO_USERS:
        role = role_by_username[username]
        _ensure_user(db, username, password_plain, role)
    db.commit()


def _admin_actor_id(db: Session) -> int | None:
    return db.scalar(
        select(User.id).where(User.username == "admin", User.deleted_at.is_(None))
    )


def _ensure_profiles(db: Session, actor_id: int | None) -> None:
    for username, display in _PROFILE_DISPLAY_NAMES.items():
        uid = db.scalar(
            select(User.id).where(User.username == username, User.deleted_at.is_(None))
        )
        if uid is None:
            continue
        exists = db.scalar(
            select(Profile.id).where(Profile.user_id == uid, Profile.deleted_at.is_(None))
        )
        if exists is not None:
            continue
        prof = Profile(user_id=uid, display_name=display)
        apply_create_audit(prof, user_id=actor_id)
        db.add(prof)
    db.commit()


def _ensure_walk_in_customer(db: Session) -> None:
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


def _ensure_demo_customer_supplier(db: Session, actor_id: int | None) -> None:
    if (
        db.scalar(
            select(Customer.id).where(
                Customer.name == _DEMO_CUSTOMER_NAME,
                Customer.deleted_at.is_(None),
            )
        )
        is None
    ):
        c = Customer(
            name=_DEMO_CUSTOMER_NAME,
            email="cliente.demo@example.local",
            phone="+1-555-0200",
            address="Calle Demo 123",
        )
        apply_create_audit(c, user_id=actor_id)
        db.add(c)
    if (
        db.scalar(
            select(Supplier.id).where(
                Supplier.name == _DEMO_SUPPLIER_NAME,
                Supplier.deleted_at.is_(None),
            )
        )
        is None
    ):
        s = Supplier(
            name=_DEMO_SUPPLIER_NAME,
            email="proveedor@example.local",
            phone="+1-555-0100",
            address="Polígono Demo, nave 1",
        )
        apply_create_audit(s, user_id=actor_id)
        db.add(s)
    db.commit()


def _ensure_demo_products(db: Session, actor_id: int | None) -> None:
    for spec in _DEMO_PRODUCTS:
        sku = str(spec["sku"])
        exists = db.scalar(
            select(Product.id).where(Product.sku == sku, Product.deleted_at.is_(None))
        )
        if exists is not None:
            continue
        product_service.create_product(
            db,
            ProductCreate(
                name=str(spec["name"]),
                sku=sku,
                description=str(spec["description"]),
                price=float(spec["price"]),
                initial_stock=int(spec["initial_stock"]),
            ),
            actor_id=actor_id,
        )


def _ensure_demo_invoice(db: Session, actor_id: int | None) -> None:
    if actor_id is None:
        return
    if (
        db.scalar(
            select(Invoice.id).where(
                Invoice.notes == _SEED_INVOICE_MARKER,
                Invoice.deleted_at.is_(None),
            )
        )
        is not None
    ):
        return
    walk = db.scalar(
        select(Customer).where(
            Customer.name == "Walk-in",
            Customer.deleted_at.is_(None),
        )
    )
    prod = db.scalar(
        select(Product).where(Product.sku == "SEED-001", Product.deleted_at.is_(None))
    )
    if walk is None or prod is None:
        return
    invoice_service.create_invoice(
        db,
        walk.id,
        [{"product_id": prod.id, "quantity": 2, "discount_percent": 0.0}],
        notes=_SEED_INVOICE_MARKER,
        discount_amount=0.0,
        tax_rate=21.0,
        actor_id=actor_id,
    )


def run_seed(session_factory: Callable[[], Session] | sessionmaker[Session]) -> None:
    db = session_factory()
    try:
        perm_by_name = _seed_permissions(db)
        admin_role, cashier_role, viewer_role = _seed_roles(db, perm_by_name)
        _seed_demo_users(db, admin_role, cashier_role, viewer_role)

        actor_id = _admin_actor_id(db)
        _ensure_profiles(db, actor_id)
        _ensure_walk_in_customer(db)
        _ensure_demo_customer_supplier(db, actor_id)
        _ensure_demo_products(db, actor_id)
        _ensure_demo_invoice(db, actor_id)
    finally:
        db.close()

"""ORM models — import submodules so Alembic discovers metadata."""

from app.db.base import Base
from app.db.models.customer import Customer
from app.db.models.inventory import Inventory
from app.db.models.invoice import Invoice, InvoiceItem
from app.db.models.permission import Permission
from app.db.models.product import Product
from app.db.models.profile import Profile
from app.db.models.rbac import role_permissions, user_roles
from app.db.models.role import Role
from app.db.models.supplier import Supplier
from app.db.models.user import User

__all__ = [
    "Base",
    "Customer",
    "Inventory",
    "Invoice",
    "InvoiceItem",
    "Permission",
    "Product",
    "Profile",
    "Role",
    "Supplier",
    "User",
    "role_permissions",
    "user_roles",
]

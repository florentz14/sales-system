"""Permission names for RBAC (must match DB `permissions.name`)."""

CREATE_PRODUCT = "create_product"
READ_PRODUCT = "read_product"
UPDATE_PRODUCT = "update_product"
DELETE_PRODUCT = "delete_product"

CREATE_CUSTOMER = "create_customer"
READ_CUSTOMER = "read_customer"
UPDATE_CUSTOMER = "update_customer"
DELETE_CUSTOMER = "delete_customer"

CREATE_INVOICE = "create_invoice"
READ_INVOICE = "read_invoice"
DELETE_INVOICE = "delete_invoice"

READ_REPORT = "read_report"

MANAGE_USERS = "manage_users"

ALL_PERMISSIONS: tuple[str, ...] = (
    CREATE_PRODUCT,
    READ_PRODUCT,
    UPDATE_PRODUCT,
    DELETE_PRODUCT,
    CREATE_CUSTOMER,
    READ_CUSTOMER,
    UPDATE_CUSTOMER,
    DELETE_CUSTOMER,
    CREATE_INVOICE,
    READ_INVOICE,
    DELETE_INVOICE,
    READ_REPORT,
    MANAGE_USERS,
)

PERMISSION_DESCRIPTIONS: dict[str, str] = {
    CREATE_PRODUCT: "Alta de productos en el catálogo.",
    READ_PRODUCT: "Consultar productos y precios.",
    UPDATE_PRODUCT: "Modificar datos de productos.",
    DELETE_PRODUCT: "Eliminar (lógicamente) productos.",
    CREATE_CUSTOMER: "Registrar clientes.",
    READ_CUSTOMER: "Consultar clientes.",
    UPDATE_CUSTOMER: "Modificar datos de clientes.",
    DELETE_CUSTOMER: "Eliminar (lógicamente) clientes.",
    CREATE_INVOICE: "Emitir facturas y descontar stock.",
    READ_INVOICE: "Consultar facturas.",
    DELETE_INVOICE: "Anular facturas.",
    READ_REPORT: "Ver reportes, exportaciones y análisis de ventas.",
    MANAGE_USERS: "Gestionar usuarios, roles y permisos.",
}

ROLE_DESCRIPTIONS: dict[str, str] = {
    "admin": "Acceso completo al sistema y a la administración de usuarios.",
    "cashier": "Ventas, facturación y altas de clientes.",
    "viewer": "Solo lectura de catálogo, clientes y facturas.",
}

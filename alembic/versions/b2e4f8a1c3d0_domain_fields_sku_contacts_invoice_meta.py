"""domain fields: sku, contacts, invoice number/status/notes, supplier contacts

Revision ID: b2e4f8a1c3d0
Revises: 7cfca3b8bb0d
Create Date: 2026-03-23

SQLite: idempotent ADD COLUMN; backfill invoice_number; unique indexes.
PostgreSQL: add columns, backfill, unique constraints.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b2e4f8a1c3d0"
down_revision: Union[str, Sequence[str], None] = "7cfca3b8bb0d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _sqlite_columns(table: str) -> set[str]:
    conn = op.get_bind()
    rows = conn.execute(sa.text(f"PRAGMA table_info({table})")).fetchall()
    return {r[1] for r in rows}


def _sqlite_add_column(table: str, name: str, ddl: str) -> None:
    if name in _sqlite_columns(table):
        return
    op.execute(sa.text(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}"))


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        _sqlite_add_column("products", "sku", "VARCHAR(64) NULL")
        _sqlite_add_column("products", "description", "TEXT NULL")
        _sqlite_add_column("customers", "email", "VARCHAR(255) NULL")
        _sqlite_add_column("customers", "phone", "VARCHAR(64) NULL")
        _sqlite_add_column("customers", "address", "VARCHAR(500) NULL")
        _sqlite_add_column("invoices", "invoice_number", "VARCHAR(32) NULL")
        _sqlite_add_column(
            "invoices",
            "status",
            "VARCHAR(32) NOT NULL DEFAULT 'confirmed'",
        )
        _sqlite_add_column("invoices", "notes", "TEXT NULL")
        _sqlite_add_column("suppliers", "email", "VARCHAR(255) NULL")
        _sqlite_add_column("suppliers", "phone", "VARCHAR(64) NULL")
        _sqlite_add_column("suppliers", "address", "VARCHAR(500) NULL")
        op.execute(
            sa.text(
                "UPDATE invoices SET invoice_number = 'INV-' || printf('%08d', id) "
                "WHERE invoice_number IS NULL OR TRIM(COALESCE(invoice_number, '')) = ''"
            )
        )
        op.execute(
            sa.text(
                "CREATE UNIQUE INDEX IF NOT EXISTS uq_products_sku ON products (sku) "
                "WHERE sku IS NOT NULL AND TRIM(sku) != ''"
            )
        )
        op.execute(
            sa.text(
                "CREATE UNIQUE INDEX IF NOT EXISTS uq_invoices_invoice_number "
                "ON invoices (invoice_number) "
                "WHERE invoice_number IS NOT NULL"
            )
        )
    else:
        op.add_column("products", sa.Column("sku", sa.String(64), nullable=True))
        op.add_column("products", sa.Column("description", sa.Text(), nullable=True))
        op.add_column("customers", sa.Column("email", sa.String(255), nullable=True))
        op.add_column("customers", sa.Column("phone", sa.String(64), nullable=True))
        op.add_column("customers", sa.Column("address", sa.String(500), nullable=True))
        op.add_column(
            "invoices",
            sa.Column("invoice_number", sa.String(32), nullable=True),
        )
        op.add_column(
            "invoices",
            sa.Column(
                "status",
                sa.String(32),
                nullable=False,
                server_default=sa.text("'confirmed'"),
            ),
        )
        op.add_column("invoices", sa.Column("notes", sa.Text(), nullable=True))
        op.add_column("suppliers", sa.Column("email", sa.String(255), nullable=True))
        op.add_column("suppliers", sa.Column("phone", sa.String(64), nullable=True))
        op.add_column("suppliers", sa.Column("address", sa.String(500), nullable=True))
        op.execute(
            sa.text(
                "UPDATE invoices SET invoice_number = 'INV-' || lpad(id::text, 8, '0') "
                "WHERE invoice_number IS NULL"
            )
        )
        op.create_unique_constraint("uq_products_sku", "products", ["sku"])
        op.create_unique_constraint(
            "uq_invoices_invoice_number",
            "invoices",
            ["invoice_number"],
        )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        op.execute(sa.text("DROP INDEX IF EXISTS uq_products_sku"))
        op.execute(sa.text("DROP INDEX IF EXISTS uq_invoices_invoice_number"))
        for table, cols in (
            ("products", ("description", "sku")),
            ("customers", ("address", "phone", "email")),
            ("invoices", ("notes", "status", "invoice_number")),
            ("suppliers", ("address", "phone", "email")),
        ):
            with op.batch_alter_table(table) as batch_op:
                for c in cols:
                    batch_op.drop_column(c)
    else:
        op.drop_constraint("uq_invoices_invoice_number", "invoices", type_="unique")
        op.drop_constraint("uq_products_sku", "products", type_="unique")
        op.drop_column("suppliers", "address")
        op.drop_column("suppliers", "phone")
        op.drop_column("suppliers", "email")
        op.drop_column("invoices", "notes")
        op.drop_column("invoices", "status")
        op.drop_column("invoices", "invoice_number")
        op.drop_column("customers", "address")
        op.drop_column("customers", "phone")
        op.drop_column("customers", "email")
        op.drop_column("products", "description")
        op.drop_column("products", "sku")

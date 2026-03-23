"""permission/role description; invoice tax and discounts

Revision ID: c9a1b2d3e4f5
Revises: b2e4f8a1c3d0
Create Date: 2026-03-23
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c9a1b2d3e4f5"
down_revision: Union[str, Sequence[str], None] = "b2e4f8a1c3d0"
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
        _sqlite_add_column("permissions", "description", "TEXT NULL")
        _sqlite_add_column("roles", "description", "TEXT NULL")
        _sqlite_add_column(
            "invoice_items",
            "discount_percent",
            "FLOAT NOT NULL DEFAULT 0",
        )
        _sqlite_add_column("invoices", "subtotal", "FLOAT NOT NULL DEFAULT 0")
        _sqlite_add_column("invoices", "discount_amount", "FLOAT NOT NULL DEFAULT 0")
        _sqlite_add_column("invoices", "tax_rate", "FLOAT NOT NULL DEFAULT 0")
        _sqlite_add_column("invoices", "tax_amount", "FLOAT NOT NULL DEFAULT 0")
        op.execute(sa.text("UPDATE invoices SET subtotal = total"))
    else:
        op.add_column("permissions", sa.Column("description", sa.Text(), nullable=True))
        op.add_column("roles", sa.Column("description", sa.Text(), nullable=True))
        op.add_column(
            "invoice_items",
            sa.Column(
                "discount_percent",
                sa.Float(),
                nullable=False,
                server_default=sa.text("0"),
            ),
        )
        op.add_column(
            "invoices",
            sa.Column(
                "subtotal",
                sa.Float(),
                nullable=False,
                server_default=sa.text("0"),
            ),
        )
        op.add_column(
            "invoices",
            sa.Column(
                "discount_amount",
                sa.Float(),
                nullable=False,
                server_default=sa.text("0"),
            ),
        )
        op.add_column(
            "invoices",
            sa.Column(
                "tax_rate",
                sa.Float(),
                nullable=False,
                server_default=sa.text("0"),
            ),
        )
        op.add_column(
            "invoices",
            sa.Column(
                "tax_amount",
                sa.Float(),
                nullable=False,
                server_default=sa.text("0"),
            ),
        )
        op.execute(sa.text("UPDATE invoices SET subtotal = total"))


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        with op.batch_alter_table("invoices") as batch_op:
            batch_op.drop_column("tax_amount")
            batch_op.drop_column("tax_rate")
            batch_op.drop_column("discount_amount")
            batch_op.drop_column("subtotal")
        with op.batch_alter_table("invoice_items") as batch_op:
            batch_op.drop_column("discount_percent")
        with op.batch_alter_table("roles") as batch_op:
            batch_op.drop_column("description")
        with op.batch_alter_table("permissions") as batch_op:
            batch_op.drop_column("description")
    else:
        op.drop_column("invoices", "tax_amount")
        op.drop_column("invoices", "tax_rate")
        op.drop_column("invoices", "discount_amount")
        op.drop_column("invoices", "subtotal")
        op.drop_column("invoice_items", "discount_percent")
        op.drop_column("roles", "description")
        op.drop_column("permissions", "description")

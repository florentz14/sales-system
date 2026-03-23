"""audit fields and soft delete mixin

Revision ID: 7cfca3b8bb0d
Revises: 6f942c6959e1
Create Date: 2026-03-23 12:36:35.268564

SQLite: plain ALTER TABLE ADD COLUMN (no defaults), backfill, then batch_alter_table
only for foreign keys. PostgreSQL: add columns + FKs in one batch per table.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "7cfca3b8bb0d"
down_revision: Union[str, Sequence[str], None] = "6f942c6959e1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_AUDIT_TABLES = (
    "customers",
    "inventory",
    "invoices",
    "invoice_items",
    "permissions",
    "products",
    "profiles",
    "roles",
    "suppliers",
    "users",
)


def _backfill_timestamps(table: str) -> None:
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        op.execute(
            sa.text(
                f"UPDATE {table} SET created_at = datetime('now'), "
                f"updated_at = datetime('now') WHERE created_at IS NULL"
            )
        )
    else:
        op.execute(
            sa.text(
                f"UPDATE {table} SET created_at = NOW(), updated_at = NOW() "
                f"WHERE created_at IS NULL"
            )
        )


def _sqlite_columns(table: str) -> set[str]:
    conn = op.get_bind()
    rows = conn.execute(sa.text(f"PRAGMA table_info({table})")).fetchall()
    return {r[1] for r in rows}


def _sqlite_add_column(table: str, name: str, ddl: str) -> None:
    if name in _sqlite_columns(table):
        return
    op.execute(sa.text(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}"))


def _upgrade_sqlite() -> None:
    for table in _AUDIT_TABLES:
        _sqlite_add_column(table, "created_at", "TIMESTAMP NULL")
        _sqlite_add_column(table, "updated_at", "TIMESTAMP NULL")
        _sqlite_add_column(table, "created_by_id", "INTEGER NULL")
        _sqlite_add_column(table, "updated_by_id", "INTEGER NULL")
        _sqlite_add_column(table, "deleted_at", "TIMESTAMP NULL")
        _sqlite_add_column(table, "deleted_by_id", "INTEGER NULL")
        _backfill_timestamps(table)
    for table in _AUDIT_TABLES:
        with op.batch_alter_table(table) as batch_op:
            batch_op.create_foreign_key(
                f"fk_{table}_audit_created_by",
                "users",
                ["created_by_id"],
                ["id"],
                ondelete="SET NULL",
            )
            batch_op.create_foreign_key(
                f"fk_{table}_audit_updated_by",
                "users",
                ["updated_by_id"],
                ["id"],
                ondelete="SET NULL",
            )
            batch_op.create_foreign_key(
                f"fk_{table}_audit_deleted_by",
                "users",
                ["deleted_by_id"],
                ["id"],
                ondelete="SET NULL",
            )


def _upgrade_postgresql() -> None:
    dt = sa.DateTime(timezone=True)
    for table in _AUDIT_TABLES:
        op.add_column(table, sa.Column("created_at", dt, nullable=True))
        op.add_column(table, sa.Column("updated_at", dt, nullable=True))
        op.add_column(table, sa.Column("created_by_id", sa.Integer(), nullable=True))
        op.add_column(table, sa.Column("updated_by_id", sa.Integer(), nullable=True))
        op.add_column(table, sa.Column("deleted_at", dt, nullable=True))
        op.add_column(table, sa.Column("deleted_by_id", sa.Integer(), nullable=True))
        op.create_foreign_key(
            f"fk_{table}_audit_created_by",
            table,
            "users",
            ["created_by_id"],
            ["id"],
            ondelete="SET NULL",
        )
        op.create_foreign_key(
            f"fk_{table}_audit_updated_by",
            table,
            "users",
            ["updated_by_id"],
            ["id"],
            ondelete="SET NULL",
        )
        op.create_foreign_key(
            f"fk_{table}_audit_deleted_by",
            table,
            "users",
            ["deleted_by_id"],
            ["id"],
            ondelete="SET NULL",
        )
        _backfill_timestamps(table)


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        _upgrade_sqlite()
    else:
        _upgrade_postgresql()


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        for table in reversed(_AUDIT_TABLES):
            with op.batch_alter_table(table) as batch_op:
                batch_op.drop_constraint(
                    f"fk_{table}_audit_deleted_by", type_="foreignkey"
                )
                batch_op.drop_constraint(
                    f"fk_{table}_audit_updated_by", type_="foreignkey"
                )
                batch_op.drop_constraint(
                    f"fk_{table}_audit_created_by", type_="foreignkey"
                )
                batch_op.drop_column("deleted_by_id")
                batch_op.drop_column("deleted_at")
                batch_op.drop_column("updated_by_id")
                batch_op.drop_column("created_by_id")
                batch_op.drop_column("updated_at")
                batch_op.drop_column("created_at")
    else:
        for table in reversed(_AUDIT_TABLES):
            op.drop_constraint(f"fk_{table}_audit_deleted_by", table, type_="foreignkey")
            op.drop_constraint(f"fk_{table}_audit_updated_by", table, type_="foreignkey")
            op.drop_constraint(f"fk_{table}_audit_created_by", table, type_="foreignkey")
            op.drop_column(table, "deleted_by_id")
            op.drop_column(table, "deleted_at")
            op.drop_column(table, "updated_by_id")
            op.drop_column(table, "created_by_id")
            op.drop_column(table, "updated_at")
            op.drop_column(table, "created_at")

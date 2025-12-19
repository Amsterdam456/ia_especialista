"""Add feedback directives and user security fields.

Revision ID: 0001_feedback_directives
Revises: None
Create Date: 2025-12-17
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect, text


revision = "0001_feedback_directives"
down_revision = None
branch_labels = None
depends_on = None


def _has_table(inspector, name: str) -> bool:
    return name in inspector.get_table_names()


def _has_column(inspector, table: str, column: str) -> bool:
    return column in {col["name"] for col in inspector.get_columns(table)}


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if not _has_table(inspector, "feedback_directives"):
        op.create_table(
            "feedback_directives",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("feedback_id", sa.Integer, sa.ForeignKey("chat_feedback.id"), nullable=False),
            sa.Column("created_by", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
            sa.Column("approved_by", sa.Integer, sa.ForeignKey("users.id"), nullable=True),
            sa.Column("status", sa.String, nullable=False, server_default=text("'pending'")),
            sa.Column("text", sa.Text, nullable=False),
            sa.Column("created_at", sa.DateTime, nullable=False),
            sa.Column("approved_at", sa.DateTime, nullable=True),
            sa.Column("applied_at", sa.DateTime, nullable=True),
        )

    if _has_table(inspector, "users"):
        if not _has_column(inspector, "users", "is_active"):
            op.add_column("users", sa.Column("is_active", sa.Boolean, nullable=False, server_default=text("1")))
        if not _has_column(inspector, "users", "failed_login_count"):
            op.add_column("users", sa.Column("failed_login_count", sa.Integer, nullable=False, server_default=text("0")))
        if not _has_column(inspector, "users", "last_failed_at"):
            op.add_column("users", sa.Column("last_failed_at", sa.DateTime, nullable=True))
        if not _has_column(inspector, "users", "locked_until"):
            op.add_column("users", sa.Column("locked_until", sa.DateTime, nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if _has_table(inspector, "users"):
        for col in ("locked_until", "last_failed_at", "failed_login_count", "is_active"):
            if _has_column(inspector, "users", col):
                op.drop_column("users", col)

    if _has_table(inspector, "feedback_directives"):
        op.drop_table("feedback_directives")

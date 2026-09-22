"""create project memberships

Revision ID: 20260922_03
Revises: 20260921_02
Create Date: 2026-09-22 00:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260922_03"
down_revision: str | None = "20260921_02"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    role = postgresql.ENUM("EDITOR", "VIEWER", name="project_membership_role", create_type=False)
    role.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "project_memberships",
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", role, nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("project_id", "user_id"),
    )
    op.create_index("ix_project_memberships_user_id", "project_memberships", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_project_memberships_user_id", table_name="project_memberships")
    op.drop_table("project_memberships")
    postgresql.ENUM(name="project_membership_role").drop(op.get_bind(), checkfirst=True)

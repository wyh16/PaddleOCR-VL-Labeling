from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision: str = "20260615_0004"
down_revision: str | None = "20260609_0005"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "password_must_change",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
            comment="是否要求下次登录后修改密码：管理员创建或重置密码后应为 true。",
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "password_must_change")

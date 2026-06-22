from __future__ import annotations

from alembic import op


revision: str = "20260619_0006"
down_revision: str | None = "20260615_0004"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.drop_constraint(
        "ck_annotation_objects_read_order",
        "annotation_objects",
        type_="check",
    )
    op.create_check_constraint(
        "ck_annotation_objects_read_order",
        "annotation_objects",
        "read_order IS NULL OR read_order >= 0",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_annotation_objects_read_order",
        "annotation_objects",
        type_="check",
    )
    op.create_check_constraint(
        "ck_annotation_objects_read_order",
        "annotation_objects",
        "read_order IS NULL OR read_order > 0",
    )

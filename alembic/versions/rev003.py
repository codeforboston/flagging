"""
empty message

Revision ID: 793fab3b5438
Revises: 39a4e575f68c
Create Date: 2023-04-17 17:42:44.755320

"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "793fab3b5438"
down_revision = "39a4e575f68c"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column("prediction", "probability", new_column_name="predicted_ecoli_cfu_100ml")


def downgrade():
    op.alter_column("prediction", "predicted_ecoli_cfu_100ml", new_column_name="probability")

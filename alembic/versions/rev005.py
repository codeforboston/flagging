"""
empty message

Revision ID: 6ab68552a4a6
Revises: e433f34dd4bd
Create Date: 2025-01-24 10:25:29.083842

"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "6ab68552a4a6"
down_revision = "e433f34dd4bd"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column("prediction", "probability", new_column_name="predicted_ecoli_cfu_100ml")


def downgrade():
    op.alter_column("prediction", "predicted_ecoli_cfu_100ml", new_column_name="probability")

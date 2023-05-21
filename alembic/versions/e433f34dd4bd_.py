"""
empty message

Revision ID: e433f34dd4bd
Revises: 793fab3b5438
Create Date: 2023-05-21 12:57:25.545426

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = 'e433f34dd4bd'
down_revision = '793fab3b5438'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('prediction', 'predicted_ecoli_cfu_100ml', new_column_name='probability')


def downgrade():
    op.alter_column('prediction', 'probability', new_column_name='predicted_ecoli_cfu_100ml')

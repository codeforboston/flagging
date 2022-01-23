"""
First migration. This is a backwards compatible migration for the 2021
website, which was not using Alembic. So we check first whether the tables
already exist before migrating.

Revision ID: 016fff145273
Revises:
Create Date: 2022-01-22 15:49:40.837695

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import schema
from sqlalchemy.engine.reflection import Inspector

from app.config import QUERIES_DIR

# revision identifiers, used by Alembic.
revision = '016fff145273'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    tables = inspector.get_table_names()

    # skip the following tables:
    # - hobolink
    # - usgs
    # - processed_data
    # - model_outputs
    # These are rewritten each time; their data doesn't need to be persisted.

    if 'boathouses' not in tables:
        op.execute(schema.CreateSequence(schema.Sequence('boathouses_id_seq')))
        op.create_table(
            'boathouses',
            sa.Column(
                'id', sa.Integer(), autoincrement=True, nullable=False,
                server_default=sa.text("nextval('boathouses_id_seq'::regclass)")
            ),
            sa.Column('boathouse', sa.String(length=255), nullable=False),
            sa.Column('reach', sa.Integer(), nullable=True),
            sa.Column('latitude', sa.Numeric(), nullable=True),
            sa.Column('longitude', sa.Numeric(), nullable=True),
            sa.Column('overridden', sa.Boolean(), nullable=True),
            sa.Column('reason', sa.String(length=255), nullable=True),
            sa.PrimaryKeyConstraint('boathouse')
        )
        with open(QUERIES_DIR + '/override_event_triggers_v1.sql', 'r') as f:
            sql = sa.text(f.read())
            conn.execute(sql)
    if 'live_website_options' not in tables:
        op.create_table(
            'live_website_options',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('flagging_message', sa.Text(), nullable=True),
            sa.Column('boating_season', sa.Boolean(), nullable=False),
            sa.PrimaryKeyConstraint('id')
        )
    if 'override_history' not in tables:
        op.create_table(
            'override_history',
            sa.Column('time', sa.TIMESTAMP(), nullable=True),
            sa.Column('boathouse', sa.TEXT(), nullable=True),
            sa.Column('overridden', sa.BOOLEAN(), nullable=True),
            sa.Column('reason', sa.TEXT(), nullable=True)
        )


def downgrade():
    op.drop_table('live_website_options')
    op.drop_table('boathouses')
    op.drop_table('override_history')

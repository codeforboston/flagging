"""
Second migration. This overhauls the 2021 website to a newer and better schema.

Revision ID: 39a4e575f68c
Revises: 016fff145273
Create Date: 2022-01-22 17:03:23.094306

"""

import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

from alembic import op
from app.config import QUERIES_DIR


# revision identifiers, used by Alembic.
revision = "39a4e575f68c"
down_revision = "016fff145273"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    tables = inspector.get_table_names()

    # Create reach association table
    op.create_table(
        "reach",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id"),
    )

    # We need to make sure that we can add the foreign key constraint to the
    # boathouse relation. If the boathouse table is already populated, this
    # necessitates running this now before adding the constraint.
    num_boathouses = conn.execute(sa.text("select * from boathouses;")).scalar()
    if num_boathouses is not None and num_boathouses > 0:
        with open(QUERIES_DIR + "/define_reach.sql", "r") as f:
            sql = sa.text(f.read())
            conn.execute(sql)

    # Migrate predictions
    # Technically speaking, the types won't match the SQLA schema because Pandas
    # overwrites the tables.
    if "model_outputs" in tables:
        op.alter_column("model_outputs", "reach", new_column_name="reach_id")
        op.drop_column("model_outputs", "log_odds")
        op.rename_table("model_outputs", "prediction")
    else:
        op.create_table(
            "prediction",
            sa.Column("reach_id", sa.Integer(), nullable=False),
            sa.Column("time", sa.DateTime(), nullable=False),
            sa.Column("probability", sa.Numeric(), nullable=True),
            sa.Column("safe", sa.Boolean(), nullable=True),
            sa.ForeignKeyConstraint(
                ["reach_id"],
                ["reach.id"],
            ),
            sa.PrimaryKeyConstraint("reach_id", "time"),
        )

    # Migrate override history.
    op.alter_column("override_history", "boathouse", new_column_name="boathouse_name")

    # Migrate website options.
    op.rename_table("live_website_options", "website_options")

    # Migrate boathouse table
    op.alter_column("boathouses", "boathouse", new_column_name="name")
    op.alter_column("boathouses", "reach", new_column_name="reach_id")
    op.alter_column("boathouses", "overridden", server_default="f")
    op.create_unique_constraint(None, "boathouses", ["name"])
    op.create_foreign_key(None, "boathouses", "reach", ["reach_id"], ["id"])
    op.rename_table("boathouses", "boathouse")
    with open(QUERIES_DIR + "/override_event_triggers_v2.sql", "r") as f:
        sql = sa.text(f.read())
        conn.execute(sql)


def downgrade():
    op.rename_table("boathouse", "boathouses")
    op.drop_constraint(None, "boathouses", type_="foreignkey")
    op.drop_constraint(None, "boathouses", type_="unique")
    op.alter_column("boathouses", "name", new_column_name="boathouse")
    op.alter_column("boathouses", "reach_id", new_column_name="reach")
    op.alter_column("boathouses", "overridden", server_default=None)

    op.drop_table("model_outputs")
    op.drop_table("prediction")
    op.drop_table("reach")

"""added column to set deadline

Revision ID: f5bd24fb168b
Revises: 0be3d73dfda1
Create Date: 2024-07-07 14:27:41.770565

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f5bd24fb168b'
down_revision = '0be3d73dfda1'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('case_report', schema=None) as batch_op:
        batch_op.add_column(sa.Column('deadline', sa.String(length=20), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('case_report', schema=None) as batch_op:
        batch_op.drop_column('deadline')

    # ### end Alembic commands ###

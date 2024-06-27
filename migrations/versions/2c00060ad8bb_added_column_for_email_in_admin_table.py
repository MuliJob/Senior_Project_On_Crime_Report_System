"""added column for email in admin table

Revision ID: 2c00060ad8bb
Revises: 87b1116534a7
Create Date: 2024-06-27 06:13:20.215257

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2c00060ad8bb'
down_revision = '87b1116534a7'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('admin', schema=None) as batch_op:
        batch_op.add_column(sa.Column('admin_email', sa.String(length=120), nullable=False))
        batch_op.create_unique_constraint(batch_op.f('uq_admin_admin_email'), ['admin_email'])

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('admin', schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f('uq_admin_admin_email'), type_='unique')
        batch_op.drop_column('admin_email')

    # ### end Alembic commands ###
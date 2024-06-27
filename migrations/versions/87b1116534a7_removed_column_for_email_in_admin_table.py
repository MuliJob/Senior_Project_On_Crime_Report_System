"""removed column for email in admin table

Revision ID: 87b1116534a7
Revises: cc4bf9882e5a
Create Date: 2024-06-27 06:10:11.137970

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '87b1116534a7'
down_revision = 'cc4bf9882e5a'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('admin', schema=None) as batch_op:
        batch_op.drop_constraint('uq_admin_admin_email', type_='unique')
        batch_op.drop_column('admin_email')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('admin', schema=None) as batch_op:
        batch_op.add_column(sa.Column('admin_email', sa.VARCHAR(length=120), nullable=False))
        batch_op.create_unique_constraint('uq_admin_admin_email', ['admin_email'])

    # ### end Alembic commands ###

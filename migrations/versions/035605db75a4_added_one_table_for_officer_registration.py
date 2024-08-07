"""added one table for officer registration

Revision ID: 035605db75a4
Revises: 4e46f1dd065d
Create Date: 2024-07-03 16:26:10.995011

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '035605db75a4'
down_revision = '4e46f1dd065d'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('_alembic_tmp_officer')
    with op.batch_alter_table('officer', schema=None) as batch_op:
        batch_op.add_column(sa.Column('reg_no', sa.Integer(), nullable=False))
        batch_op.add_column(sa.Column('username', sa.String(length=80), nullable=False))
        batch_op.add_column(sa.Column('officer_email', sa.String(length=120), nullable=False))
        batch_op.add_column(sa.Column('password', sa.String(length=128), nullable=False))
        batch_op.create_unique_constraint(batch_op.f('uq_officer_username'), ['username'])
        batch_op.drop_column('officer_id')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('officer', schema=None) as batch_op:
        batch_op.add_column(sa.Column('officer_id', sa.INTEGER(), nullable=False))
        batch_op.drop_constraint(batch_op.f('uq_officer_username'), type_='unique')
        batch_op.drop_column('password')
        batch_op.drop_column('officer_email')
        batch_op.drop_column('username')
        batch_op.drop_column('reg_no')

    op.create_table('_alembic_tmp_officer',
    sa.Column('first_name', sa.VARCHAR(length=100), nullable=False),
    sa.Column('last_name', sa.VARCHAR(length=100), nullable=True),
    sa.Column('badge', sa.VARCHAR(length=20), nullable=False),
    sa.Column('rank', sa.VARCHAR(length=10), nullable=False),
    sa.Column('station', sa.VARCHAR(length=20), nullable=False),
    sa.Column('reg_no', sa.INTEGER(), nullable=False),
    sa.Column('username', sa.VARCHAR(length=80), nullable=False),
    sa.Column('officer_email', sa.VARCHAR(length=120), nullable=False),
    sa.Column('password', sa.VARCHAR(length=128), nullable=False),
    sa.UniqueConstraint('username', name='uq_officer_username')
    )
    # ### end Alembic commands ###

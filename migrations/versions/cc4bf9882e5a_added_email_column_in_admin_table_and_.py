"""added email column in admin table and moodified crime and theft table

Revision ID: cc4bf9882e5a
Revises: 49aeb4480e90
Create Date: 2024-06-27 05:46:27.875775

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'cc4bf9882e5a'
down_revision = '49aeb4480e90'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('admin', schema=None) as batch_op:
        batch_op.add_column(sa.Column('admin_email', sa.String(length=120), nullable=False))
        batch_op.alter_column('username',
               existing_type=sa.VARCHAR(length=255),
               type_=sa.String(length=10),
               existing_nullable=False)
        batch_op.create_unique_constraint(batch_op.f('uq_admin_admin_email'), ['admin_email'])

    with op.batch_alter_table('crime', schema=None) as batch_op:
        batch_op.add_column(sa.Column('crime_status', sa.String(length=10), nullable=True))
        batch_op.add_column(sa.Column('crime_file_upload', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('crime_file_name', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('crime_mimetype', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('date_crime_received', sa.DateTime(), nullable=False))
        batch_op.drop_column('mimetype')
        batch_op.drop_column('date_received')
        batch_op.drop_column('file_upload')
        batch_op.drop_column('status')
        batch_op.drop_column('name')

    with op.batch_alter_table('theft', schema=None) as batch_op:
        batch_op.add_column(sa.Column('theft_status', sa.String(length=10), nullable=True))
        batch_op.add_column(sa.Column('theft_file_upload', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('theft_file_name', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('theft_mimetype', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('date_theft_received', sa.DateTime(), nullable=False))
        batch_op.drop_column('mimetype')
        batch_op.drop_column('date_received')
        batch_op.drop_column('file_upload')
        batch_op.drop_column('status')
        batch_op.drop_column('name')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('theft', schema=None) as batch_op:
        batch_op.add_column(sa.Column('name', sa.TEXT(), nullable=True))
        batch_op.add_column(sa.Column('status', sa.VARCHAR(length=10), nullable=True))
        batch_op.add_column(sa.Column('file_upload', sa.TEXT(), nullable=True))
        batch_op.add_column(sa.Column('date_received', sa.DATETIME(), nullable=False))
        batch_op.add_column(sa.Column('mimetype', sa.TEXT(), nullable=True))
        batch_op.drop_column('date_theft_received')
        batch_op.drop_column('theft_mimetype')
        batch_op.drop_column('theft_file_name')
        batch_op.drop_column('theft_file_upload')
        batch_op.drop_column('theft_status')

    with op.batch_alter_table('crime', schema=None) as batch_op:
        batch_op.add_column(sa.Column('name', sa.TEXT(), nullable=True))
        batch_op.add_column(sa.Column('status', sa.VARCHAR(length=10), nullable=True))
        batch_op.add_column(sa.Column('file_upload', sa.TEXT(), nullable=True))
        batch_op.add_column(sa.Column('date_received', sa.DATETIME(), nullable=False))
        batch_op.add_column(sa.Column('mimetype', sa.TEXT(), nullable=True))
        batch_op.drop_column('date_crime_received')
        batch_op.drop_column('crime_mimetype')
        batch_op.drop_column('crime_file_name')
        batch_op.drop_column('crime_file_upload')
        batch_op.drop_column('crime_status')

    with op.batch_alter_table('admin', schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f('uq_admin_admin_email'), type_='unique')
        batch_op.alter_column('username',
               existing_type=sa.String(length=10),
               type_=sa.VARCHAR(length=255),
               existing_nullable=False)
        batch_op.drop_column('admin_email')

    # ### end Alembic commands ###

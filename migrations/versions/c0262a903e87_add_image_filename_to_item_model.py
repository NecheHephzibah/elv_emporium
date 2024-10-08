"""Add image_filename to Item model

Revision ID: c0262a903e87
Revises: 01c7da8c248d
Create Date: 2024-09-20 21:13:41.949455

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c0262a903e87'
down_revision = '01c7da8c248d'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('item', schema=None) as batch_op:
        batch_op.add_column(sa.Column('image_filename', sa.String(length=100), nullable=False, server_default='ai-generated-8331478_1280.jpg'))
        batch_op.alter_column('price', existing_type=sa.INTEGER(), nullable=True)

    # Remove the server_default after setting the default value during the migration

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('item', schema=None) as batch_op:
        batch_op.alter_column('price',
               existing_type=sa.INTEGER(),
               nullable=False)
        batch_op.drop_column('image_filename')

    # ### end Alembic commands ###

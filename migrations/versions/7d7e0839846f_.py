"""empty message

Revision ID: 7d7e0839846f
Revises: 
Create Date: 2018-05-21 14:16:58.394621

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7d7e0839846f'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('topicimages', sa.Column('auth_id', sa.Integer(), nullable=True))
    op.drop_column('topicimages', 'img_title')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('topicimages', sa.Column('img_title', sa.VARCHAR(length=128), nullable=True))
    op.drop_column('topicimages', 'auth_id')
    # ### end Alembic commands ###
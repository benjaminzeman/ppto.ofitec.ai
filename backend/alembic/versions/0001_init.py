from alembic import op
import sqlalchemy as sa

revision = '0001_init'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'projects',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('currency', sa.String(), server_default='CLP')
    )
    op.create_table(
        'chapters',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('project_id', sa.Integer, sa.ForeignKey('projects.id', ondelete='CASCADE')),
        sa.Column('code', sa.String()),
        sa.Column('name', sa.String())
    )
    op.create_table(
        'items',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('chapter_id', sa.Integer, sa.ForeignKey('chapters.id', ondelete='CASCADE')),
        sa.Column('code', sa.String()),
        sa.Column('name', sa.String()),
        sa.Column('unit', sa.String(), server_default='m2'),
        sa.Column('quantity', sa.Numeric(16,3), server_default='0'),
        sa.Column('price', sa.Numeric(16,2), server_default='0')
    )
    op.create_table(
        'resources',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('type', sa.String()),
        sa.Column('code', sa.String()),
        sa.Column('name', sa.String()),
        sa.Column('unit', sa.String(), server_default='u'),
        sa.Column('unit_cost', sa.Numeric(16,4), server_default='0')
    )
    op.create_table(
        'apus',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('item_id', sa.Integer, sa.ForeignKey('items.id', ondelete='CASCADE')),
        sa.Column('resource_id', sa.Integer, sa.ForeignKey('resources.id', ondelete='RESTRICT')),
        sa.Column('coeff', sa.Numeric(16,6), server_default='0')
    )

def downgrade():
    op.drop_table('apus')
    op.drop_table('resources')
    op.drop_table('items')
    op.drop_table('chapters')
    op.drop_table('projects')

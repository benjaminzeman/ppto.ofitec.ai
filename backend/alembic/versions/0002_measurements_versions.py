from alembic import op
import sqlalchemy as sa

revision = '0002_measurements_versions'
down_revision = '0001_init'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'measurements',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('item_id', sa.Integer, sa.ForeignKey('items.id', ondelete='CASCADE')),
        sa.Column('source', sa.String(), server_default='manual'),
        sa.Column('qty', sa.Numeric(16,3), server_default='0'),
        sa.Column('note', sa.Text())
    )
    op.create_table(
        'budget_versions',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('project_id', sa.Integer, sa.ForeignKey('projects.id', ondelete='CASCADE')),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('note', sa.Text()),
        sa.Column('created_at', sa.DateTime())
    )
    op.create_table(
        'budget_version_items',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('version_id', sa.Integer, sa.ForeignKey('budget_versions.id', ondelete='CASCADE')),
        sa.Column('item_code', sa.String()),
        sa.Column('item_name', sa.String()),
        sa.Column('unit', sa.String()),
        sa.Column('qty', sa.Numeric(16,3)),
        sa.Column('unit_price', sa.Numeric(16,2))
    )

def downgrade():
    op.drop_table('budget_version_items')
    op.drop_table('budget_versions')
    op.drop_table('measurements')

from alembic import op
import sqlalchemy as sa

revision = '0005_project_baseline'
down_revision = '0004_purchases'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('projects', sa.Column('baseline_version_id', sa.Integer, sa.ForeignKey('budget_versions.id', ondelete='SET NULL')))

def downgrade():
    op.drop_column('projects', 'baseline_version_id')

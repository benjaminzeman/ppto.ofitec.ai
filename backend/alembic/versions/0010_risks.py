from alembic import op
import sqlalchemy as sa

revision = '0010_risks'
down_revision = '0009_workflows_versioning_extra'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'risks',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('project_id', sa.Integer, sa.ForeignKey('projects.id', ondelete='CASCADE'), index=True),
        sa.Column('category', sa.String),
        sa.Column('description', sa.Text),
        sa.Column('probability', sa.Integer),
        sa.Column('impact', sa.Integer),
        sa.Column('status', sa.String, server_default='open'),
        sa.Column('mitigation', sa.Text),
        sa.Column('owner', sa.String),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

def downgrade():
    op.drop_table('risks')
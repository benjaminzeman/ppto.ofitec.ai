"""jobs table

Revision ID: 0006_jobs
Revises: 0005_project_baseline
Create Date: 2025-09-20
"""
from alembic import op
import sqlalchemy as sa

revision = '0006_jobs'
down_revision = '0005_project_baseline'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'jobs',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('rq_id', sa.String(), nullable=False, unique=True, index=True),
        sa.Column('type', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False, server_default='queued'),
        sa.Column('params', sa.Text(), nullable=True),
        sa.Column('result_path', sa.String(), nullable=True),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )


def downgrade() -> None:
    op.drop_table('jobs')

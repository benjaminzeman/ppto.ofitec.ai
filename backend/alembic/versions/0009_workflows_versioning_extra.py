from alembic import op
import sqlalchemy as sa

revision = '0009_workflows_versioning_extra'
down_revision = '0008_soft_delete'
branch_labels = None
depends_on = None


def upgrade():
    # Nuevos campos en budget_versions si no existían (created_by, is_baseline, is_locked)
    with op.batch_alter_table('budget_versions') as batch_op:
        conn = op.get_bind()
        inspector = sa.inspect(conn)
        existing_cols = {c['name'] for c in inspector.get_columns('budget_versions')}
        if 'created_by' not in existing_cols:
            batch_op.add_column(sa.Column('created_by', sa.Integer, sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True))
        if 'is_baseline' not in existing_cols:
            batch_op.add_column(sa.Column('is_baseline', sa.Boolean, server_default=sa.text('false')))
        if 'is_locked' not in existing_cols:
            batch_op.add_column(sa.Column('is_locked', sa.Boolean, server_default=sa.text('false')))

    # Columnas extra para items de versión (chapter_code, chapter_name)
    with op.batch_alter_table('budget_version_items') as batch_op:
        conn = op.get_bind()
        inspector = sa.inspect(conn)
        existing_cols = {c['name'] for c in inspector.get_columns('budget_version_items')}
        cols = [
            ('chapter_code', sa.String),
            ('chapter_name', sa.String),
            ('item_code', sa.String),
            ('item_name', sa.String),
            ('unit', sa.String),
            ('qty', sa.Numeric(16,3)),
            ('unit_price', sa.Numeric(16,2))
        ]
        for name, typ in cols:
            if name not in existing_cols:
                batch_op.add_column(sa.Column(name, typ, nullable=True))

    # Tablas de workflows
    op.create_table(
        'workflows',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('project_id', sa.Integer, sa.ForeignKey('projects.id', ondelete='CASCADE'), index=True),
        sa.Column('name', sa.String, nullable=False),
        sa.Column('entity_type', sa.String, nullable=False),
        sa.Column('active', sa.Boolean, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now())
    )
    op.create_table(
        'workflow_steps',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('workflow_id', sa.Integer, sa.ForeignKey('workflows.id', ondelete='CASCADE'), index=True),
        sa.Column('position', sa.Integer, nullable=False),
        sa.Column('role_required', sa.String, nullable=False),
        sa.Column('name', sa.String, nullable=False)
    )
    op.create_table(
        'workflow_instances',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('workflow_id', sa.Integer, sa.ForeignKey('workflows.id', ondelete='CASCADE'), index=True),
        sa.Column('project_id', sa.Integer, sa.ForeignKey('projects.id', ondelete='CASCADE'), index=True),
        sa.Column('entity_type', sa.String, nullable=False),
        sa.Column('entity_id', sa.Integer, nullable=False),
        sa.Column('status', sa.String, server_default='running'),
        sa.Column('created_by', sa.Integer, sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('current_step', sa.Integer, server_default='1')
    )
    op.create_table(
        'workflow_instance_steps',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('instance_id', sa.Integer, sa.ForeignKey('workflow_instances.id', ondelete='CASCADE'), index=True),
        sa.Column('step_id', sa.Integer, sa.ForeignKey('workflow_steps.id', ondelete='CASCADE'), index=True),
        sa.Column('position', sa.Integer, nullable=False),
        sa.Column('decision', sa.String, nullable=True),
        sa.Column('decided_by', sa.Integer, sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('decided_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('comment', sa.Text, nullable=True)
    )


def downgrade():
    op.drop_table('workflow_instance_steps')
    op.drop_table('workflow_instances')
    op.drop_table('workflow_steps')
    op.drop_table('workflows')
    with op.batch_alter_table('budget_version_items') as batch_op:
        for col in ['chapter_code','chapter_name','item_code','item_name','unit','qty','unit_price']:
            try:
                batch_op.drop_column(col)
            except Exception:
                pass
    with op.batch_alter_table('budget_versions') as batch_op:
        for col in ['created_by','is_baseline','is_locked']:
            try:
                batch_op.drop_column(col)
            except Exception:
                pass
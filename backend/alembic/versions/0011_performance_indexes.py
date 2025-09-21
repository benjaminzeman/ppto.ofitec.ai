from alembic import op
import sqlalchemy as sa

revision = '0011_performance_indexes'
down_revision = '0010_risks'
branch_labels = None
depends_on = None

def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())
    # measurement_batches
    if 'measurement_batches' in existing_tables:
        op.create_index('ix_measurement_batches_project_status', 'measurement_batches', ['project_id','status'])
    # measurement_lines
    if 'measurement_lines' in existing_tables:
        op.create_index('ix_measurement_lines_batch_item', 'measurement_lines', ['batch_id','item_id'])
    # workflow_instances
    if 'workflow_instances' in existing_tables:
        op.create_index('ix_workflow_instances_proj_status_step', 'workflow_instances', ['project_id','status','current_step'])
    # workflow_instance_steps
    if 'workflow_instance_steps' in existing_tables:
        op.create_index('ix_workflow_inst_steps_instance_pos_decision', 'workflow_instance_steps', ['instance_id','position','decision'])


def downgrade():
    for name in [
        'ix_measurement_batches_project_status',
        'ix_measurement_lines_batch_item',
        'ix_workflow_instances_proj_status_step',
        'ix_workflow_inst_steps_instance_pos_decision'
    ]:
        try:
            op.drop_index(name)
        except Exception:
            pass

from alembic import op
import sqlalchemy as sa

revision = '0012_measurement_batches_lines'
down_revision = '0011_performance_indexes'
branch_labels = None
depends_on = None

def table_exists(inspector, name):
    return name in inspector.get_table_names()

def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not table_exists(inspector, 'measurement_batches'):
        op.create_table(
            'measurement_batches',
            sa.Column('id', sa.Integer, primary_key=True),
            sa.Column('project_id', sa.Integer, sa.ForeignKey('projects.id', ondelete='CASCADE'), index=True),
            sa.Column('name', sa.String),
            sa.Column('status', sa.String, server_default='open'),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now())
        )
    if not table_exists(inspector, 'measurement_lines'):
        op.create_table(
            'measurement_lines',
            sa.Column('id', sa.Integer, primary_key=True),
            sa.Column('batch_id', sa.Integer, sa.ForeignKey('measurement_batches.id', ondelete='CASCADE'), index=True),
            sa.Column('item_id', sa.Integer, sa.ForeignKey('items.id', ondelete='CASCADE'), index=True),
            sa.Column('qty', sa.Numeric(16,3), server_default='0')
        )

    # Re-crear índices de performance si la migración 0011 se saltó alguno (por ausencia de tablas en su momento)
    inspector = sa.inspect(bind)
    existing_indexes = {ix['name'] for ix in inspector.get_indexes('measurement_batches')} if table_exists(inspector, 'measurement_batches') else set()
    if table_exists(inspector, 'measurement_batches') and 'ix_measurement_batches_project_status' not in existing_indexes:
        op.create_index('ix_measurement_batches_project_status', 'measurement_batches', ['project_id','status'])

    if table_exists(inspector, 'measurement_lines'):
        existing_ml_idx = {ix['name'] for ix in inspector.get_indexes('measurement_lines')}
        if 'ix_measurement_lines_batch_item' not in existing_ml_idx:
            op.create_index('ix_measurement_lines_batch_item', 'measurement_lines', ['batch_id','item_id'])

    if table_exists(inspector, 'workflow_instances'):
        existing_wi_idx = {ix['name'] for ix in inspector.get_indexes('workflow_instances')}
        if 'ix_workflow_instances_proj_status_step' not in existing_wi_idx:
            op.create_index('ix_workflow_instances_proj_status_step', 'workflow_instances', ['project_id','status','current_step'])

    if table_exists(inspector, 'workflow_instance_steps'):
        existing_wis_idx = {ix['name'] for ix in inspector.get_indexes('workflow_instance_steps')}
        if 'ix_workflow_inst_steps_instance_pos_decision' not in existing_wis_idx:
            op.create_index('ix_workflow_inst_steps_instance_pos_decision', 'workflow_instance_steps', ['instance_id','position','decision'])

    # (Opcional) Migración de datos legacy: si existiera tabla 'measurements', se podría agrupar por item y crear un batch sintético.
    if table_exists(inspector, 'measurements') and table_exists(inspector, 'measurement_batches') and table_exists(inspector, 'measurement_lines'):
        try:
            # Verificar si ya hay datos en measurement_lines para evitar duplicar
            res = bind.execute(sa.text('SELECT COUNT(1) FROM measurement_lines')).scalar()
            if res == 0:
                # Obtener project_id a través de chapters -> items
                rows = bind.execute(sa.text('''
                    SELECT c.project_id, m.item_id, SUM(m.qty) as total_qty
                    FROM measurements m
                    JOIN items i ON i.id = m.item_id
                    JOIN chapters c ON c.id = i.chapter_id
                    GROUP BY c.project_id, m.item_id
                ''')).fetchall()
                from collections import defaultdict
                proj_map = defaultdict(list)
                for r in rows:
                    proj_map[r.project_id].append(r)
                for project_id, rlist in proj_map.items():
                    batch_id = bind.execute(sa.text('INSERT INTO measurement_batches (project_id, name, status) VALUES (:p, :n, :s) RETURNING id'),
                                             {'p': project_id, 'n': 'Legacy Import', 's': 'closed'}).scalar()
                    for r in rlist:
                        bind.execute(sa.text('INSERT INTO measurement_lines (batch_id, item_id, qty) VALUES (:b, :i, :q)'),
                                     {'b': batch_id, 'i': r.item_id, 'q': r.total_qty or 0})
        except Exception:
            # Silencioso: si la estructura legacy no coincide, se omite migración de datos sin abortar.
            pass


def downgrade():
    # Borrado simple (no se revierte migración legacy por simplicidad)
    if op.get_bind().dialect.has_table(op.get_bind(), 'measurement_lines'):
        op.drop_table('measurement_lines')
    if op.get_bind().dialect.has_table(op.get_bind(), 'measurement_batches'):
        op.drop_table('measurement_batches')

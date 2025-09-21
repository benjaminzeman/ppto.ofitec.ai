"""invoices and bank transactions

Revision ID: 0013_invoices_bank_transactions
Revises: 0012_measurement_batches_lines
Create Date: 2025-09-20
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

revision = '0013_invoices_bank_transactions'
down_revision = '0012_measurement_batches_lines'
branch_labels = None
depends_on = None


def table_exists(conn, name):
    inspector = Inspector.from_engine(conn)
    return name in inspector.get_table_names()


def upgrade():
    bind = op.get_bind()

    if not table_exists(bind, 'invoices'):
        op.create_table(
            'invoices',
            sa.Column('id', sa.Integer, primary_key=True),
            sa.Column('project_id', sa.Integer, sa.ForeignKey('projects.id', ondelete='CASCADE'), index=True),
            sa.Column('dte_number', sa.String(), index=True),
            sa.Column('status', sa.String(), server_default='pending'),
            sa.Column('amount', sa.Numeric(16,2)),
            sa.Column('currency', sa.String(), server_default='CLP'),
            sa.Column('xml_ref', sa.String()),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column('paid_at', sa.DateTime(timezone=True)),
        )

    if not table_exists(bind, 'invoice_payments'):
        op.create_table(
            'invoice_payments',
            sa.Column('id', sa.Integer, primary_key=True),
            sa.Column('invoice_id', sa.Integer, sa.ForeignKey('invoices.id', ondelete='CASCADE'), index=True),
            sa.Column('amount', sa.Numeric(16,2)),
            sa.Column('method', sa.String()),
            sa.Column('reference', sa.String()),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        )

    if not table_exists(bind, 'bank_transactions'):
        op.create_table(
            'bank_transactions',
            sa.Column('id', sa.Integer, primary_key=True),
            sa.Column('project_id', sa.Integer, sa.ForeignKey('projects.id', ondelete='CASCADE'), index=True),
            sa.Column('date', sa.Date(), index=True),
            sa.Column('description', sa.String()),
            sa.Column('amount', sa.Numeric(16,2)),
            sa.Column('balance', sa.Numeric(16,2)),
            sa.Column('source', sa.String()),
            sa.Column('raw', sa.JSON()),
            sa.Column('matched_invoice_id', sa.Integer, sa.ForeignKey('invoices.id', ondelete='SET NULL'), nullable=True, index=True),
        )

    # Índices adicionales (si no existen) para performance
    # type: ignore para analizador que espera Engine
    insp = Inspector.from_engine(bind)  # type: ignore[arg-type]
    existing_indexes = {ix['name'] for ix in insp.get_indexes('invoices')} if table_exists(bind, 'invoices') else set()
    if 'ix_invoices_project_status' not in existing_indexes and table_exists(bind, 'invoices'):
        op.create_index('ix_invoices_project_status', 'invoices', ['project_id', 'status'])
    existing_bt_indexes = {ix['name'] for ix in insp.get_indexes('bank_transactions')} if table_exists(bind, 'bank_transactions') else set()
    if 'ix_bank_txn_project_matched' not in existing_bt_indexes and table_exists(bind, 'bank_transactions'):
        op.create_index('ix_bank_txn_project_matched', 'bank_transactions', ['project_id', 'matched_invoice_id'])


def downgrade():
    bind = op.get_bind()
    inspector = Inspector.from_engine(bind)  # type: ignore[arg-type]
    tables = inspector.get_table_names()
    if 'bank_transactions' in tables:
        op.drop_table('bank_transactions')
    if 'invoice_payments' in tables:
        op.drop_table('invoice_payments')
    if 'invoices' in tables:
        op.drop_table('invoices')

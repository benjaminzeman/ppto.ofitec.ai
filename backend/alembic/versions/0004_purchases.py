from alembic import op
import sqlalchemy as sa

revision = '0004_purchases'
down_revision = '0003_users'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'suppliers',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('tax_id', sa.String()),
        sa.Column('contact_email', sa.String())
    )
    op.create_index('ix_suppliers_tax_id', 'suppliers', ['tax_id'])

    op.create_table(
        'rfqs',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('project_id', sa.Integer, sa.ForeignKey('projects.id', ondelete='CASCADE')),
        sa.Column('status', sa.String(), server_default='open'),
        sa.Column('created_at', sa.DateTime(timezone=True))
    )
    op.create_index('ix_rfqs_project_id', 'rfqs', ['project_id'])

    op.create_table(
        'rfq_items',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('rfq_id', sa.Integer, sa.ForeignKey('rfqs.id', ondelete='CASCADE')),
        sa.Column('item_id', sa.Integer, sa.ForeignKey('items.id', ondelete='CASCADE')),
        sa.Column('qty', sa.Numeric(16,3), server_default='0')
    )
    op.create_index('ix_rfq_items_rfq_id', 'rfq_items', ['rfq_id'])
    op.create_index('ix_rfq_items_item_id', 'rfq_items', ['item_id'])

    op.create_table(
        'quotes',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('rfq_id', sa.Integer, sa.ForeignKey('rfqs.id', ondelete='CASCADE')),
        sa.Column('supplier_id', sa.Integer, sa.ForeignKey('suppliers.id', ondelete='CASCADE')),
        sa.Column('created_at', sa.DateTime(timezone=True))
    )
    op.create_index('ix_quotes_rfq_id', 'quotes', ['rfq_id'])
    op.create_index('ix_quotes_supplier_id', 'quotes', ['supplier_id'])

    op.create_table(
        'quote_lines',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('quote_id', sa.Integer, sa.ForeignKey('quotes.id', ondelete='CASCADE')),
        sa.Column('rfq_item_id', sa.Integer, sa.ForeignKey('rfq_items.id', ondelete='CASCADE')),
        sa.Column('unit_price', sa.Numeric(16,4), server_default='0')
    )
    op.create_index('ix_quote_lines_quote_id', 'quote_lines', ['quote_id'])
    op.create_index('ix_quote_lines_rfq_item_id', 'quote_lines', ['rfq_item_id'])

def downgrade():
    op.drop_index('ix_quote_lines_rfq_item_id', table_name='quote_lines')
    op.drop_index('ix_quote_lines_quote_id', table_name='quote_lines')
    op.drop_table('quote_lines')
    op.drop_index('ix_quotes_supplier_id', table_name='quotes')
    op.drop_index('ix_quotes_rfq_id', table_name='quotes')
    op.drop_table('quotes')
    op.drop_index('ix_rfq_items_item_id', table_name='rfq_items')
    op.drop_index('ix_rfq_items_rfq_id', table_name='rfq_items')
    op.drop_table('rfq_items')
    op.drop_index('ix_rfqs_project_id', table_name='rfqs')
    op.drop_table('rfqs')
    op.drop_index('ix_suppliers_tax_id', table_name='suppliers')
    op.drop_table('suppliers')

from alembic import op
import sqlalchemy as sa

revision = '0008_soft_delete'
down_revision = '0007_audit_roles'
branch_labels = None
depends_on = None


def upgrade():
    # Agrega columnas deleted_at si no existen
    with op.batch_alter_table('chapters') as batch_op:
        batch_op.add_column(sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))
    with op.batch_alter_table('items') as batch_op:
        batch_op.add_column(sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))


def downgrade():
    with op.batch_alter_table('items') as batch_op:
        batch_op.drop_column('deleted_at')
    with op.batch_alter_table('chapters') as batch_op:
        batch_op.drop_column('deleted_at')

from alembic import op
import sqlalchemy as sa

revision = '0003_users'
down_revision = '0002_measurements_versions'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'users',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('username', sa.String(), nullable=False, unique=True),
        sa.Column('hashed_password', sa.String(), nullable=False),
    # Ajuste: usar boolean literal PostgreSQL 'true' en lugar de entero '1'
    sa.Column('is_active', sa.Boolean(), server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True))
    )
    op.create_index('ix_users_username', 'users', ['username'], unique=True)

def downgrade():
    op.drop_index('ix_users_username', table_name='users')
    op.drop_table('users')

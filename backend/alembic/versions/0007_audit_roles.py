from alembic import op
import sqlalchemy as sa

revision = "0007_audit_roles"
down_revision = "0006_jobs"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("project_id", sa.Integer, sa.ForeignKey("projects.id", ondelete="CASCADE")),
        sa.Column("entity", sa.String()),
        sa.Column("entity_id", sa.Integer),
        sa.Column("action", sa.String()),
        sa.Column("data", sa.JSON()),
        sa.Column("user_id", sa.Integer),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
    )
    op.create_table(
        "user_project_roles",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer),
        sa.Column("project_id", sa.Integer, sa.ForeignKey("projects.id", ondelete="CASCADE")),
        sa.Column("role", sa.String()),
    )

def downgrade():
    op.drop_table("user_project_roles")
    op.drop_table("audit_logs")

from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import os
import sys

# Asegurar path correcto para importar paquete app cuando se invoca alembic desde fuera
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app.db.base import Base  # para metadata si se agrega autogenerate

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

def get_url():
    return os.getenv("DATABASE_URL")

target_metadata = Base.metadata

def run_migrations_offline():
    url = get_url()
    context.configure(url=url, literal_binds=True, compare_type=True, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    connectable = engine_from_config({"sqlalchemy.url": get_url()}, prefix="sqlalchemy.", poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

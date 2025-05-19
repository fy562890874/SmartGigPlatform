"""Alembic environment configuration."""
import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Add project directory to sys.path for model imports
# Adjust the path depth ('..') as necessary based on your structure
project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_dir)

# Import your models here so Alembic autogenerate can detect changes
# Option 1: Import the db object from your extensions
# from app.core.extensions import db
# target_metadata = db.metadata

# Option 2: Import a base model or specific models if you don't have a central db object easily accessible
from app.models import * # Import all models from the models package
# Assuming your models inherit from a declarative base linked to your db instance's metadata
# If your db instance is created within create_app, this might be tricky.
# A common pattern is to define db = SQLAlchemy() globally (e.g., in extensions.py)
# and then initialize it with the app in create_app using db.init_app(app).
# Let's assume the db object is accessible via extensions
from app.core.extensions import db
target_metadata = db.metadata


# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.

def get_database_url():
    """Retrieve database URL from Flask app config or environment."""
    # Try to get it from environment variable first (used by manage.py)
    db_url = os.getenv('DATABASE_URL_FOR_MIGRATIONS')
    if db_url:
        return db_url

    # Fallback: Load minimal app context to get config (might be complex)
    # This is often simpler if manage.py sets the env var above.
    try:
        # This assumes your manage.py sets up an app context or passes the URL
        # As a fallback, you might hardcode the dev URL, but using env var is better.
        from app.core.config import get_config
        flask_config = get_config(os.getenv('FLASK_CONFIG', 'development'))
        return flask_config.SQLALCHEMY_DATABASE_URI
    except ImportError:
        # Fallback if app context loading fails or is too complex here
        print("Warning: Could not load Flask config for migrations. Using default dev URL.")
        return 'mysql+mysqlconnector://user:password@localhost/smartgig_dev' # Fallback


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = get_database_url() # Use the helper function
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True, # Compare column types
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # Ensure the app's database URL is used
    db_url = get_database_url()
    connectable_config = config.get_section(config.config_ini_section)
    if connectable_config is None:
        connectable_config = {}
    connectable_config['sqlalchemy.url'] = db_url # Override URL from alembic.ini

    connectable = engine_from_config(
        connectable_config, # Use modified config with correct URL
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True, # Compare column types
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()


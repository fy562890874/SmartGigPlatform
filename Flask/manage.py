#!/usr/bin/env python
"""Management script for the Flask application."""
import os
import click
from flask_migrate import Migrate, upgrade
from app import create_app
from app.core.extensions import db
# Import models so Alembic can detect them
from app import models # noqa

# Create app instance based on FLASK_CONFIG environment variable
config_name = os.getenv('FLASK_CONFIG', 'default')
app = create_app(config_name)
migrate = Migrate(app, db) # Initialize Migrate with app and db

# Set DATABASE_URL_FOR_MIGRATIONS env var for alembic env.py
# This ensures Alembic uses the same DB URL as the current app config
os.environ['DATABASE_URL_FOR_MIGRATIONS'] = app.config['SQLALCHEMY_DATABASE_URI']


@app.shell_context_processor
def make_shell_context():
    """Creates a shell context that adds the database and models."""
    context = {'db': db}
    # Dynamically add all models from app.models to the context
    for name, obj in models.__dict__.items():
        if isinstance(obj, type) and issubclass(obj, db.Model):
            context[name] = obj
    return context

@click.group(cls=click.Group)
def cli():
    """Application management commands."""
    pass

@cli.command('run')
@click.option('--host', default='127.0.0.1', help='Host to bind to.')
@click.option('--port', default=5000, help='Port to listen on.')
def run_server(host, port):
    """Runs the Flask development server."""
    app.run(host=host, port=port)

@cli.command('test')
@click.argument('test_names', nargs=-1)
def test(test_names):
    """Run the unit tests."""
    import pytest
    args = []
    if test_names:
        args = list(test_names)
    else:
        args = ['tests'] # Default to running all tests in the tests directory
    rv = pytest.main(args)
    exit(rv)

@cli.command('db_init')
def db_init():
    """Initialize the database migrations."""
    # This command should ideally be run only once.
    # It wraps 'flask db init'
    from flask_migrate import init as alembic_init
    try:
        alembic_init()
        print("Database migrations initialized.")
    except Exception as e:
        print(f"Error initializing migrations: {e}")


@cli.command('db_migrate')
@click.option('-m', '--message', default=None, help='Revision message')
def db_migrate(message):
    """Generate a new database migration."""
    # Wraps 'flask db migrate'
    from flask_migrate import migrate as alembic_migrate
    try:
        alembic_migrate(message=message)
        print("Migration script generated.")
    except Exception as e:
        print(f"Error generating migration: {e}")


@cli.command('db_upgrade')
@click.argument('revision', default='head')
def db_upgrade(revision):
    """Apply database migrations."""
    # Wraps 'flask db upgrade'
    try:
        upgrade(revision=revision)
        print(f"Database upgraded to revision: {revision}")
    except Exception as e:
        print(f"Error upgrading database: {e}")


@cli.command('db_downgrade')
@click.argument('revision', default='-1')
def db_downgrade(revision):
    """Downgrade database migrations."""
    # Wraps 'flask db downgrade'
    from flask_migrate import downgrade as alembic_downgrade
    try:
        alembic_downgrade(revision=revision)
        print(f"Database downgraded to revision: {revision}")
    except Exception as e:
        print(f"Error downgrading database: {e}")

@cli.command('db_current')
def db_current():
    """Show current database revision."""
    # Wraps 'flask db current'
    from flask_migrate import current as alembic_current
    try:
        alembic_current()
    except Exception as e:
        print(f"Error showing current revision: {e}")

@cli.command('db_history')
def db_history():
    """Show migration history."""
    # Wraps 'flask db history'
    from flask_migrate import history as alembic_history
    try:
        alembic_history()
    except Exception as e:
        print(f"Error showing migration history: {e}")


# Add other custom commands if needed
# @cli.command('seed_db')
# def seed_db():
#     """Seeds the database with initial data."""
#     # Add seeding logic here
#     print("Database seeding complete.")


if __name__ == '__main__':
    # Make the script executable
    # Ensure FLASK_APP is set or defined here if running directly
    # os.environ['FLASK_APP'] = 'manage.py' # Redundant if set in .env
    cli()

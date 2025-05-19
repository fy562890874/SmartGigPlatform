"""Pytest configuration and fixtures"""
import pytest
import os
from app import create_app
from app.core.extensions import db as _db

@pytest.fixture(scope='session')
def app():
    """Session-wide test Flask application."""
    # Set environment to 'testing'
    os.environ['FLASK_CONFIG'] = 'testing'
    app = create_app(config_name='testing')

    # Establish an application context before running the tests.
    ctx = app.app_context()
    ctx.push()

    yield app # Provide the app instance to the tests

    ctx.pop() # Clean up the context

@pytest.fixture(scope='function') # Use 'function' scope for client if needed per test
def client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture(scope='session')
def db(app):
    """Session-wide test database."""
    _db.app = app # Associate db with the app context
    with app.app_context(): # Ensure operations happen within context
        _db.create_all() # Create tables based on models

    yield _db # Provide the db instance

    # Explicitly close the connection and drop tables after session
    with app.app_context():
        _db.session.remove()
        _db.drop_all()

@pytest.fixture(scope='function')
def session(db, app):
    """Creates a new database session for a test."""
    with app.app_context(): # Ensure operations happen within context
        connection = db.engine.connect()
        transaction = connection.begin()

        # Begin a nested transaction (using SAVEPOINT)
        options = dict(bind=connection, binds={})
        session = db.create_scoped_session(options=options)

        # Establish SAVEPOINT
        session.begin_nested()

        # Session is now bound to the connection and nested transaction
        db.session = session # Use this session for the test scope

        yield session # Provide the session to the test

        # Rollback the overall transaction, effectively rolling back
        # the nested transaction and any changes made in the test
        session.remove()
        transaction.rollback()
        connection.close()

# Add other fixtures as needed, e.g., for creating test users, tokens etc.
@pytest.fixture(scope='function')
def test_user(session):
    """Fixture to create a sample user for tests."""
    from app.models.user import User
    from app.core.extensions import bcrypt
    import uuid
    # Using a phone number that can be part of the TestUser strategy,
    # but this user is created directly in DB for specific unit/integration tests.
    # For broader API tests, use shared_test_utils.get_or_create_user_token_id
    TEST_USER_FOR_FIXTURE_PHONE = '17700010010' # Example: TestUserForUnitTests
    TEST_USER_FOR_FIXTURE_PASSWORD = 'TestUser'


    hashed_password = bcrypt.generate_password_hash(TEST_USER_FOR_FIXTURE_PASSWORD).decode('utf-8')
    user = User(
        uuid=str(uuid.uuid4()),
        phone_number=TEST_USER_FOR_FIXTURE_PHONE,
        password_hash=hashed_password,
        user_type='freelancer', # Default to freelancer for this generic fixture
        # nickname='Test Fixture User', # Nickname should be in profile
        status='active'
    )
    session.add(user)
    session.commit() # Commit within the nested transaction
    
    # Create a basic profile for this user if services expect it
    from app.models.profile import FreelancerProfile
    profile = FreelancerProfile(user_id=user.id, real_name="Fixture TestUser", nickname="FixtureNickname")
    session.add(profile)
    session.commit()

    return user


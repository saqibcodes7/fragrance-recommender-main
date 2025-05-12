import pytest
import os
import tempfile
from main import create_app
from models import db, User
import bcrypt
import uuid

@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    # Create a temporary file to isolate the database for each test
    db_fd, db_path = tempfile.mkstemp()
    
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'SECRET_KEY': 'test_secret_key'
    })
    
    # Create the database and load test data
    with app.app_context():
        db.create_all()
    
    yield app
    
    # Cleanup after test
    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture
def test_client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture
def auth_user(app):
    """Create a test user."""
    with app.app_context():
        # Create test user with unique email
        unique_id = str(uuid.uuid4())[:8]
        email = f'test_{unique_id}@example.com'
        password = 'testpass123'.encode('utf-8')
        hashed_password = bcrypt.hashpw(password, bcrypt.gensalt())
        user = User(email=email, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        # Refresh the user instance to ensure it's bound to the session
        db.session.refresh(user)
        return user

@pytest.fixture
def auth_client(app, auth_user):
    """A test client with an authenticated user."""
    client = app.test_client()
    with client.session_transaction() as sess:
        sess['user_id'] = auth_user.id
        sess['_fresh'] = True  # Mark session as fresh
    return client

@pytest.fixture
def runner(app):
    """A test runner for the app's Click commands."""
    return app.test_cli_runner()

@pytest.fixture(autouse=True)
def cleanup_database(app):
    """Clean up database after each test."""
    yield
    with app.app_context():
        db.session.remove()  # Properly close any open sessions
        for table in reversed(db.metadata.sorted_tables):
            db.session.execute(table.delete())
        db.session.commit() 
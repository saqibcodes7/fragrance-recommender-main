import pytest
from flask import session
from models import User, db
import bcrypt
import json
import uuid

def test_signup_success(test_client):
    """Test successful user registration"""
    unique_id = str(uuid.uuid4())[:8]
    email = f'signup_{unique_id}@example.com'
    response = test_client.post('/api/signup', json={
        'email': email,
        'password': 'testpass123'
    })
    assert response.status_code == 201
    assert b'User registered successfully' in response.data
    
    # Verify user was created in database
    user = User.query.filter_by(email=email).first()
    assert user is not None

def test_signup_duplicate_email(test_client):
    """Test registration with existing email"""
    unique_id = str(uuid.uuid4())[:8]
    email = f'duplicate_{unique_id}@example.com'
    
    # First signup
    test_client.post('/api/signup', json={
        'email': email,
        'password': 'testpass123'
    })
    
    # Try to signup again with same email
    response = test_client.post('/api/signup', json={
        'email': email,
        'password': 'different123'
    })
    assert response.status_code == 400
    assert b'Email already registered' in response.data

def test_signup_invalid_data(test_client):
    """Test registration with invalid data"""
    # Missing email
    response = test_client.post('/api/signup', json={
        'password': 'testpass123'
    })
    assert response.status_code == 400
    
    # Missing password
    response = test_client.post('/api/signup', json={
        'email': 'test@example.com'
    })
    assert response.status_code == 400

def test_login_success(test_client):
    """Test successful login"""
    unique_id = str(uuid.uuid4())[:8]
    email = f'login_{unique_id}@example.com'
    
    # Create user first
    test_client.post('/api/signup', json={
        'email': email,
        'password': 'testpass123'
    })
    
    # Try logging in
    response = test_client.post('/api/login', json={
        'email': email,
        'password': 'testpass123'
    })
    assert response.status_code == 200
    assert b'Login successful' in response.data

def test_login_invalid_credentials(test_client):
    """Test login with invalid credentials"""
    unique_id = str(uuid.uuid4())[:8]
    email = f'invalid_{unique_id}@example.com'
    
    # Create user first
    test_client.post('/api/signup', json={
        'email': email,
        'password': 'testpass123'
    })
    
    # Wrong password
    response = test_client.post('/api/login', json={
        'email': email,
        'password': 'wrongpass'
    })
    assert response.status_code == 401
    assert b'Invalid email or password' in response.data
    
    # Non-existent email
    response = test_client.post('/api/login', json={
        'email': f'nonexistent_{unique_id}@example.com',
        'password': 'testpass123'
    })
    assert response.status_code == 401
    assert b'Invalid email or password' in response.data

def test_logout(test_client):
    """Test logout functionality"""
    unique_id = str(uuid.uuid4())[:8]
    email = f'logout_{unique_id}@example.com'
    
    # Create and login user first
    test_client.post('/api/signup', json={
        'email': email,
        'password': 'testpass123'
    })
    
    test_client.post('/api/login', json={
        'email': email,
        'password': 'testpass123'
    })
    
    # Test logout
    response = test_client.post('/api/logout')
    assert response.status_code == 200
    assert b'Logged out successfully' in response.data

def test_me_endpoint(test_client):
    """Test /me endpoint for getting current user info"""
    unique_id = str(uuid.uuid4())[:8]
    email = f'me_{unique_id}@example.com'
    
    # Create and login user first
    test_client.post('/api/signup', json={
        'email': email,
        'password': 'testpass123'
    })
    
    with test_client:  # This ensures session handling works
        test_client.post('/api/login', json={
            'email': email,
            'password': 'testpass123'
        })
        
        # Test /me endpoint
        response = test_client.get('/api/me')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['email'] == email
        
        # Test /me when not logged in
        test_client.post('/api/logout')
        response = test_client.get('/api/me')
        assert response.status_code == 401 
import pytest
import json
from models import User, Fragrance, Favorite, db

def test_get_fragrances_pagination(test_client):
    """Test fragrance listing with pagination"""
    response = test_client.get('/api/fragrances?limit=5&offset=0')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'fragrances' in data
    assert len(data['fragrances']) <= 5
    assert 'total' in data
    assert 'offset' in data
    assert 'limit' in data

def test_get_fragrances_filtering(test_client):
    """Test fragrance filtering"""
    # Test gender filter
    response = test_client.get('/api/fragrances?gender=Unisex')
    assert response.status_code == 200
    data = json.loads(response.data)
    for fragrance in data['fragrances']:
        assert fragrance['gender'] == 'Unisex'
    
    # Test minimum rating filter
    response = test_client.get('/api/fragrances?min_rating=4.0')
    assert response.status_code == 200
    data = json.loads(response.data)
    for fragrance in data['fragrances']:
        assert fragrance['rating_value'] >= 4.0
    
    # Test brand filter
    response = test_client.get('/api/fragrances?brand=Dior')
    assert response.status_code == 200
    data = json.loads(response.data)
    for fragrance in data['fragrances']:
        assert 'Dior' in fragrance['brand']

def test_get_single_fragrance(test_client):
    """Test getting a single fragrance by ID"""
    # Get first fragrance from list
    response = test_client.get('/api/fragrances?limit=1')
    data = json.loads(response.data)
    fragrance_id = data['fragrances'][0]['id']
    
    # Get specific fragrance
    response = test_client.get(f'/api/fragrances/{fragrance_id}')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['id'] == fragrance_id

def test_get_nonexistent_fragrance(test_client):
    """Test getting a nonexistent fragrance"""
    response = test_client.get('/api/fragrances/99999')
    assert response.status_code == 404

def test_add_favorite_unauthorized(test_client):
    """Test adding favorite without authentication"""
    response = test_client.post('/api/favourites', json={
        'fragrance_id': 1
    })
    assert response.status_code == 401

def test_add_favorite_success(auth_client, auth_user):
    """Test successfully adding a fragrance to favorites"""
    # Get a valid fragrance ID first
    response = auth_client.get('/api/fragrances?limit=1')
    data = json.loads(response.data)
    fragrance_id = data['fragrances'][0]['id']
    
    # Add to favorites
    response = auth_client.post('/api/favourites', json={
        'fragrance_id': fragrance_id
    })
    assert response.status_code == 201
    data = json.loads(response.data)
    assert 'favorite_id' in data
    
    # Verify it was added to database
    with auth_client.application.app_context():
        favorite = Favorite.query.filter_by(
            user_id=auth_user.id,
            fragrance_id=fragrance_id
        ).first()
        assert favorite is not None

def test_add_favorite_duplicate(auth_client, auth_user):
    """Test adding same fragrance to favorites twice"""
    # Add first time
    response = auth_client.post('/api/favourites', json={
        'fragrance_id': 1
    })
    assert response.status_code == 201
    
    # Try adding again
    response = auth_client.post('/api/favourites', json={
        'fragrance_id': 1
    })
    assert response.status_code == 200
    assert b'already in favorites' in response.data

def test_add_favorite_nonexistent(auth_client, auth_user):
    """Test adding nonexistent fragrance to favorites"""
    response = auth_client.post('/api/favourites', json={
        'fragrance_id': 99999
    })
    assert response.status_code == 404

def test_remove_favorite(auth_client, auth_user):
    """Test removing a fragrance from favorites"""
    # Add to favorites first
    response = auth_client.post('/api/favourites', json={
        'fragrance_id': 1
    })
    data = json.loads(response.data)
    favorite_id = data['favorite_id']
    
    # Remove from favorites
    response = auth_client.delete(f'/api/favourites/{favorite_id}')
    assert response.status_code == 200
    
    # Verify it was removed
    with auth_client.application.app_context():
        favorite = Favorite.query.get(favorite_id)
        assert favorite is None

def test_get_user_favorites(auth_client, auth_user):
    """Test getting user's favorite fragrances"""
    # Add some favorites first
    auth_client.post('/api/favourites', json={'fragrance_id': 1})
    auth_client.post('/api/favourites', json={'fragrance_id': 2})
    
    response = auth_client.get('/api/favourites')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data) == 2

def test_check_favorite_status(auth_client, auth_user):
    """Test checking if a fragrance is in user's favorites"""
    # Add to favorites
    auth_client.post('/api/favourites', json={'fragrance_id': 1})
    
    # Check status
    response = auth_client.get('/api/favourites/check/1')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['is_favorite'] is True
    
    # Check non-favorited fragrance
    response = auth_client.get('/api/favourites/check/2')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['is_favorite'] is False 
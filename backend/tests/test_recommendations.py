import pytest
import json
from models import User, QuizResult, Favorite, db

def test_recommendations_unauthorized(test_client):
    """Test getting recommendations without authentication"""
    response = test_client.get('/api/recommendations/personalized')
    assert response.status_code == 401

def test_recommendations_no_preferences(auth_client, auth_user):
    """Test recommendations with no quiz or favorites"""
    response = auth_client.get('/api/recommendations/personalized')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'recommendations' in data
    # Should return default top-rated fragrances
    assert len(data['recommendations']) > 0

def test_recommendations_from_quiz(auth_client, auth_user):
    """Test recommendations based on quiz preferences"""
    # Submit quiz first
    auth_client.post('/api/quiz/start', json={
        'experience_level': 'Beginner'
    })
    auth_client.post('/api/quiz/submit', json={
        'answers': {
            'vibe': 'Fresh and clean',
            'occasion': 'Daily wear',
            'season': 'Spring',
            'scent_type': 'Fresh'
        }
    })
    
    response = auth_client.get('/api/recommendations/personalized')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'recommendations' in data
    assert len(data['recommendations']) > 0
    
    # Verify recommendations have some fresh/clean characteristics
    fresh_related_terms = ['fresh', 'citrus', 'aquatic', 'clean', 'marine', 'water', 'light', 'airy', 'ozonic']
    for rec in data['recommendations']:
        assert 'Main Accords' in rec
        accords = rec['Main Accords'].lower() if isinstance(rec['Main Accords'], str) else ''
        description = rec.get('Description', '').lower()
        
        # Check if any fresh-related terms appear in either accords or description
        has_fresh_characteristic = any(term in accords or term in description for term in fresh_related_terms)
        assert has_fresh_characteristic, f"Expected fresh characteristics in recommendation: {rec['Name']}"

def test_recommendations_from_favorites(auth_client, auth_user):
    """Test recommendations based on user favorites"""
    # Add some favorites first
    with auth_client.application.app_context():
        favorite = Favorite(user_id=auth_user.id, fragrance_id=1)
        db.session.add(favorite)
        db.session.commit()
    
    response = auth_client.get('/api/recommendations/personalized')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'recommendations' in data
    assert len(data['recommendations']) > 0

def test_recommendations_hybrid(auth_client, auth_user):
    """Test hybrid recommendations combining quiz and favorites"""
    # Submit quiz
    auth_client.post('/api/quiz/start', json={
        'experience_level': 'Beginner'
    })
    auth_client.post('/api/quiz/submit', json={
        'answers': {
            'vibe': 'Warm and cosy',
            'occasion': 'Special occasions'
        }
    })
    
    # Add favorites
    with auth_client.application.app_context():
        favorite = Favorite(user_id=auth_user.id, fragrance_id=1)
        db.session.add(favorite)
        db.session.commit()
    
    response = auth_client.get('/api/recommendations/personalized')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'recommendations' in data
    assert len(data['recommendations']) > 0

def test_recommendations_pagination(auth_client, auth_user):
    """Test recommendation pagination"""
    response = auth_client.get('/api/recommendations/personalized?page=1&per_page=5')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data['recommendations']) <= 5
    
    # Test second page
    response = auth_client.get('/api/recommendations/personalized?page=2&per_page=5')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data['recommendations']) <= 5

def test_recommendations_invalid_pagination(auth_client, auth_user):
    """Test recommendations with invalid pagination parameters"""
    response = auth_client.get('/api/recommendations/personalized?page=0&per_page=0')
    assert response.status_code == 200
    data = json.loads(response.data)
    # Should use default pagination values
    assert len(data['recommendations']) > 0

def test_recommendations_fallback_no_matches(auth_client, auth_user):
    """Test fallback when no matches found for preferences"""
    # Submit quiz with very specific preferences
    auth_client.post('/api/quiz/start', json={
        'experience_level': 'Advanced'
    })
    auth_client.post('/api/quiz/submit', json={
        'answers': {
            'top_notes': 'NonexistentNote',
            'base_notes': 'AnotherNonexistentNote'
        }
    })
    
    response = auth_client.get('/api/recommendations/personalized')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'recommendations' in data
    # Should return default recommendations
    assert len(data['recommendations']) > 0

def test_recommendations_by_fragrance(auth_client, auth_user):
    """Test getting similar fragrances by title"""
    response = auth_client.get('/api/recommendations/personalized?title=Light Blue')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'recommendations' in data
    assert len(data['recommendations']) > 0 
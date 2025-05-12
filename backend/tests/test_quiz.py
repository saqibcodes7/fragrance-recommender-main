import pytest
import json
from models import User, QuizResult, db

def test_quiz_start_unauthorized(test_client):
    """Test starting quiz without authentication"""
    response = test_client.post('/api/quiz/start', json={
        'experience_level': 'Beginner'
    })
    assert response.status_code == 401

def test_quiz_start_invalid_level(auth_client, auth_user):
    """Test starting quiz with invalid experience level"""
    response = auth_client.post('/api/quiz/start', json={
        'experience_level': 'Invalid'
    })
    assert response.status_code == 400
    assert b'Valid experience level is required' in response.data

def test_quiz_start_success(auth_client, auth_user):
    """Test successful quiz start"""
    response = auth_client.post('/api/quiz/start', json={
        'experience_level': 'Beginner'
    })
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'questions' in data
    assert len(data['questions']) > 0
    
    # Verify quiz result was created
    quiz = QuizResult.query.filter_by(user_id=auth_user.id).first()
    assert quiz is not None
    prefs = json.loads(quiz.preferences)
    assert prefs['experience_level'] == 'Beginner'

def test_quiz_start_intermediate(auth_client, auth_user):
    """Test starting intermediate level quiz"""
    response = auth_client.post('/api/quiz/start', json={
        'experience_level': 'Intermediate'
    })
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'questions' in data
    # Verify intermediate-specific questions
    questions = data['questions']
    assert any('collection' in q['id'] for q in questions)
    assert any('note' in q['id'] for q in questions)

def test_quiz_start_advanced(auth_client, auth_user):
    """Test starting advanced level quiz"""
    response = auth_client.post('/api/quiz/start', json={
        'experience_level': 'Advanced'
    })
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'questions' in data
    # Verify advanced-specific questions
    questions = data['questions']
    assert any('top_notes' in q['id'] for q in questions)
    assert any('base_notes' in q['id'] for q in questions)

def test_quiz_submit_unauthorized(test_client):
    """Test submitting quiz without authentication"""
    response = test_client.post('/api/quiz/submit', json={
        'answers': {'vibe': 'Fresh and clean'}
    })
    assert response.status_code == 401

def test_quiz_submit_without_start(auth_client, auth_user):
    """Test submitting quiz without starting first"""
    response = auth_client.post('/api/quiz/submit', json={
        'answers': {'vibe': 'Fresh and clean'}
    })
    assert response.status_code == 400
    assert b'Quiz not started' in response.data

def test_quiz_submit_success(auth_client, auth_user):
    """Test successful quiz submission"""
    # Start quiz first
    auth_client.post('/api/quiz/start', json={
        'experience_level': 'Beginner'
    })
    
    # Submit answers
    answers = {
        'vibe': 'Fresh and clean',
        'occasion': 'Daily wear',
        'season': 'Spring',
        'scent_type': 'Fresh',
        'longevity': 'All day'
    }
    response = auth_client.post('/api/quiz/submit', json={
        'answers': answers
    })
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'recommendations' in data
    assert len(data['recommendations']) > 0
    
    # Verify preferences were saved
    quiz = QuizResult.query.filter_by(user_id=auth_user.id).first()
    assert quiz is not None
    prefs = json.loads(quiz.preferences)
    for key, value in answers.items():
        assert prefs[key] == value

def test_quiz_submit_invalid_data(auth_client, auth_user):
    """Test submitting quiz with invalid data"""
    # Start quiz first
    auth_client.post('/api/quiz/start', json={
        'experience_level': 'Beginner'
    })
    
    # Submit without answers
    response = auth_client.post('/api/quiz/submit', json={})
    assert response.status_code == 400
    assert b'Answers are required' in response.data

def test_quiz_overwrite_existing(auth_client, auth_user):
    """Test that new quiz submissions overwrite old ones"""
    # First quiz submission
    auth_client.post('/api/quiz/start', json={
        'experience_level': 'Beginner'
    })
    auth_client.post('/api/quiz/submit', json={
        'answers': {'vibe': 'Fresh and clean'}
    })
    
    # Second quiz submission
    auth_client.post('/api/quiz/start', json={
        'experience_level': 'Intermediate'
    })
    auth_client.post('/api/quiz/submit', json={
        'answers': {'note': 'Vanilla'}
    })
    
    # Verify only latest preferences exist
    quiz_results = QuizResult.query.filter_by(user_id=auth_user.id).all()
    assert len(quiz_results) == 1
    prefs = json.loads(quiz_results[0].preferences)
    assert prefs['experience_level'] == 'Intermediate'
    assert prefs['note'] == 'Vanilla' 
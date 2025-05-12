from flask import Blueprint, request, jsonify
import pandas as pd
import pickle
import os
import numpy as np
import json
from sklearn.metrics.pairwise import cosine_similarity
from scipy.sparse import csr_matrix
from functools import lru_cache
import gzip
from auth import login_required, get_current_user
from models import db, User, QuizResult, Favorite

recommendations_bp = Blueprint('recommendations', __name__)

# Global variables to store data
_df = None
_cosine_sim = None

def load_recommendation_data():
    """Load dataset and similarity matrix once during startup"""
    global _df, _cosine_sim
    
    if _df is None or _cosine_sim is None:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        print(f"Base directory: {base_dir}")

        # Load dataset
        df_path = os.path.join(base_dir, 'perfume_data_clean.csv')
        print(f"Looking for dataset at: {df_path}")
        if not os.path.exists(df_path):
            df_path = 'perfume_data_clean.csv'  # Try current directory
            print(f"Trying current directory instead: {df_path}")
        
        print(f"Loading dataset from: {df_path}")
        _df = pd.read_csv(df_path)
        print(f"Successfully loaded dataset with {len(_df)} rows")

        # Fill missing values
        _df['Description'] = _df['Description'].fillna('')
        _df['Main Accords'] = _df['Main Accords'].fillna('')

        # Try loading pre-computed compressed similarity matrix
        cosine_sim_path = os.path.join(base_dir, 'cosine_sim.pkl.gz')
        print(f"Looking for similarity matrix at: {cosine_sim_path}")
        if not os.path.exists(cosine_sim_path):
            cosine_sim_path = 'cosine_sim.pkl.gz'  # Try current directory
            print(f"Trying current directory instead: {cosine_sim_path}")
        
        if os.path.exists(cosine_sim_path):
            try:
                print(f"Loading compressed similarity matrix from: {cosine_sim_path}")
                with gzip.open(cosine_sim_path, 'rb') as f:
                    _cosine_sim = pickle.load(f)
                print("Successfully loaded compressed similarity matrix")
            except Exception as e:
                print(f"Error loading compressed matrix: {str(e)}")
                # Fall back to original file if compressed one fails
                cosine_sim_path = os.path.join(base_dir, 'cosine_sim.pkl')
                if os.path.exists(cosine_sim_path):
                    print(f"Falling back to uncompressed matrix: {cosine_sim_path}")
                    _cosine_sim = pickle.load(open(cosine_sim_path, 'rb'))
                else:
                    print("Creating minimal similarity matrix as fallback")
                    # If no precomputed matrix exists, create a minimal one
                    # This is a fallback and should be avoided by running optimize_cosine_sim.py
                    from sklearn.feature_extraction.text import TfidfVectorizer
                    tfidf = TfidfVectorizer(stop_words='english', max_features=1000)
                    tfidf_matrix = tfidf.fit_transform(_df['Description'] + " " + _df['Main Accords'])
                    _cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix, dense_output=False)
                    
        print(f"Recommendation data loaded: {len(_df)} fragrances")
        print(f"Sample of fragrances: {', '.join(_df['Name'].head().tolist())}")

    return _df, _cosine_sim

# Load data at import time
load_recommendation_data()

@lru_cache(maxsize=128)
def get_similar_indices(idx, top_n=5):
    """Get indices of similar fragrances with caching"""
    global _cosine_sim
    
    # For sparse matrices
    if hasattr(_cosine_sim, 'toarray'):
        row = _cosine_sim[idx].toarray().flatten()
    else:
        row = _cosine_sim[idx]
    
    # Get top similar indices (excluding self)
    sim_scores = list(enumerate(row))
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
    sim_scores = [i for i in sim_scores if i[0] != idx][:top_n]
    return [i[0] for i in sim_scores]

def hybrid_recommendations(user_id, title=None, top_n=5, page=1, per_page=5):
    """Generate recommendations with pagination"""
    global _df, _cosine_sim
    
    # Ensure valid pagination parameters
    page = max(1, page)  # Minimum page is 1
    per_page = max(1, min(20, per_page))  # Between 1 and 20
    
    # Calculate pagination offsets
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    
    user = User.query.get(user_id)
    all_recs = []

    # 1. Content-based recommendations if title provided
    if title:
        title = title.strip().lower()
        matches = _df[_df['Name'].str.lower().str.strip() == title].index
        if len(matches) > 0:
            idx = matches[0]
            perfume_indices = get_similar_indices(idx, top_n=10)
            for idx in perfume_indices:
                if idx < len(_df):
                    all_recs.append((_df.iloc[idx], 0.8))  # Weight content recs highly

    # 2. Quiz-based recommendations
    quiz_result = QuizResult.query.filter_by(user_id=user_id).first()
    if quiz_result:
        try:
            prefs = json.loads(quiz_result.preferences)
            
            # Map vibe to accords for beginners
            if prefs.get('experience_level') == 'Beginner' and prefs.get('vibe'):
                vibe_map = {
                    'Fresh and clean': ['Fresh', 'Citrus', 'Aquatic', 'Green'],
                    'Warm and cosy': ['Vanilla', 'Amber', 'Gourmand', 'Woody'],
                    'Bold and attention-grabbing': ['Spicy', 'Woody', 'Leather', 'Oriental'],
                    'Light and subtle': ['Floral', 'Citrus', 'Powdery', 'Fresh']
                }
                prefs['desired_accords'] = vibe_map.get(prefs['vibe'], [])
            
            # Apply lightweight filtering
            candidates = []
            
            if 'gender' in prefs:
                gender_matches = _df[_df['Gender'] == prefs['gender']]
                candidates.extend(list(gender_matches.index))
            
            # Only do this filtering if we have candidates or no gender filter applied
            if candidates or 'gender' not in prefs:
                # Rating filter (simple numeric comparison is fast)
                if 'min_rating' in prefs:
                    min_rating = float(prefs['min_rating'])
                    rating_matches = _df[_df['Rating Value'] >= min_rating]
                    if candidates:
                        # Intersection
                        candidates = [idx for idx in candidates if idx in rating_matches.index]
                    else:
                        candidates = list(rating_matches.index)
                
                # Accord matching
                if 'desired_accords' in prefs:
                    desired_accords = prefs['desired_accords']
                    if not candidates:
                        # If no candidates yet, check all fragrances
                        for idx in range(len(_df)):
                            accords = _df.iloc[idx]['Main Accords']
                            if isinstance(accords, str) and accords:
                                # Convert string representation to list
                                if accords.startswith('['):
                                    try:
                                        accord_list = json.loads(accords)
                                    except:
                                        accord_list = accords.strip('[]').replace("'", "").split(',')
                                else:
                                    accord_list = [a.strip() for a in accords.split(',')]
                                
                                # Count matches between desired accords and fragrance accords
                                score = sum(1 for accord in desired_accords if any(a.strip().lower() == accord.lower() for a in accord_list))
                                if score > 0:  # Only add if there's at least one match
                                    all_recs.append((_df.iloc[idx], score * 0.2 + 0.5))  # Weight by matches
                    else:
                        # Check only existing candidates
                        for idx in candidates:
                            if idx < len(_df):
                                accords = _df.iloc[idx]['Main Accords']
                                if isinstance(accords, str) and accords:
                                    # Convert string representation to list
                                    if accords.startswith('['):
                                        try:
                                            accord_list = json.loads(accords)
                                        except:
                                            accord_list = accords.strip('[]').replace("'", "").split(',')
                                    else:
                                        accord_list = [a.strip() for a in accords.split(',')]
                                    
                                    # Count matches between desired accords and fragrance accords
                                    score = sum(1 for accord in desired_accords if any(a.strip().lower() == accord.lower() for a in accord_list))
                                    if score > 0:  # Only add if there's at least one match
                                        all_recs.append((_df.iloc[idx], score * 0.2 + 0.5))  # Weight by matches
            
            # If we don't have recommendations but have a quiz result, add some default recommendations
            if not all_recs:
                top_rated = _df.sort_values('Rating Value', ascending=False).head(5)
                for _, row in top_rated.iterrows():
                    all_recs.append((row, 0.5))  # Medium weight
                    
        except Exception as e:
            print(f"Error processing quiz preferences: {str(e)}")

    # 3. Add favorites-based recommendations
    favorites = Favorite.query.filter_by(user_id=user_id).all()
    if favorites:
        fav_ids = [f.fragrance_id for f in favorites]
        for fav_id in fav_ids[:3]:  # Limit to 3 favorites to avoid too much processing
            try:
                if fav_id in _df.index:
                    similar_indices = get_similar_indices(fav_id, top_n=3)
                    for idx in similar_indices:
                        if idx < len(_df):
                            all_recs.append((_df.iloc[idx], 0.7))  # High weight for favorites-based
            except Exception as e:
                print(f"Error processing favorite {fav_id}: {str(e)}")

    # If no recommendations found, add default top-rated fragrances
    if not all_recs:
        top_rated = _df.sort_values('Rating Value', ascending=False).head(top_n)
        for _, row in top_rated.iterrows():
            all_recs.append((row, 0.3))  # Lower weight

    # Remove duplicates by keeping highest score for each fragrance
    unique_recs = {}
    for fragrance, score in all_recs:
        name = fragrance['Name']
        if name not in unique_recs or unique_recs[name][1] < score:
            unique_recs[name] = (fragrance, score)

    # Sort by score and apply pagination
    sorted_recs = sorted(unique_recs.values(), key=lambda x: x[1], reverse=True)
    paginated_recs = sorted_recs[start_idx:end_idx]
    
    # Extract just the fragrances (without scores)
    result = [rec[0] for rec in paginated_recs]
    
    return pd.DataFrame(result)

@recommendations_bp.route('/quiz', methods=['POST', 'OPTIONS'])  
def get_recommendations():
    user = get_current_user()
    title = request.args.get('title', '').strip()
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 5))
    
    try:
        recommendations = hybrid_recommendations(user.id, title if title else None, 
                                               top_n=20, page=page, per_page=per_page)
        
        if recommendations.empty:
            return jsonify({"message": "No recommendations found. Try exploring more fragrances!"}), 200
            
        return jsonify({
            "recommendations": recommendations.to_dict(orient='records'),
            "type": "hybrid",
            "count": len(recommendations),
            "page": page,
            "per_page": per_page
        }), 200
    except Exception as e:
        import traceback
        print(f"Error generating recommendations: {str(e)}")
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@recommendations_bp.route('/recommendations/personalized', methods=['GET'])
@login_required
def personalized_recommendations():
    user = get_current_user()
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 5))
    
    try:
        recommendations = hybrid_recommendations(user.id, page=page, per_page=per_page)
        if recommendations.empty:
            recommendations = _df.sort_values('Rating Value', ascending=False).head(per_page)
            
        return jsonify({
            "recommendations": recommendations.to_dict(orient='records'),
            "type": "personalized",
            "count": len(recommendations),
            "page": page,
            "per_page": per_page
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@recommendations_bp.route('/api/quiz', methods=['POST'])
@login_required
def handle_quiz_submission():
    user = get_current_user()
    data = request.get_json()
    if not data or 'preferences' not in data:
        return jsonify({
            "success": False,
            "error": "Invalid quiz data format"
        }), 400

    try:
        QuizResult.query.filter_by(user_id=user.id).delete()
        quiz_result = QuizResult(
            user_id=user.id,
            preferences=json.dumps(data['preferences'])
        )
        db.session.add(quiz_result)
        db.session.commit()

        # Get first page of recommendations
        recommendations = hybrid_recommendations(user.id, page=1, per_page=5)
        return jsonify({
            "success": True,
            "recommendations": recommendations.to_dict(orient='records')
        })

    except Exception as e:
        db.session.rollback()
        print(f"Quiz submission error: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Failed to process quiz. Please try again."
        }), 500

@recommendations_bp.route('/recommendations/similar', methods=['GET'])
def get_similar_fragrances():
    name = request.args.get('name', '').strip()
    print(f"Received request for similar fragrances to: '{name}'")
    
    try:
        # Load data if not already loaded
        global _df, _cosine_sim
        if _df is None or _cosine_sim is None:
            print("Loading recommendation data...")
            _df, _cosine_sim = load_recommendation_data()
            print("Data loaded successfully")
        
        print(f"Looking for fragrance in dataset of {len(_df)} items")
        
        # Clean up the name for comparison
        search_name = name.lower().strip()
        # Remove common suffixes that might be part of the name
        search_name = search_name.replace('for women and men', '').strip()
        search_name = search_name.replace('for men', '').strip()
        search_name = search_name.replace('for women', '').strip()
        
        print(f"Searching for cleaned name: '{search_name}'")
        
        # Try exact match first
        matches = _df[_df['Name'].str.lower().str.strip() == search_name].index
        
        # If no exact match, try partial match
        if len(matches) == 0:
            print(f"No exact match found, trying partial match")
            partial_matches = _df[_df['Name'].str.lower().str.strip().str.contains(search_name, na=False)]
            if not partial_matches.empty:
                print(f"Found {len(partial_matches)} partial matches")
                matches = [partial_matches.index[0]]
                print(f"Using first match: {partial_matches.iloc[0]['Name']}")
            else:
                print(f"No matches found for: {search_name}")
                return jsonify({"message": "Fragrance not found", "recommendations": []}), 404

        idx = matches[0]
        print(f"Found fragrance at index {idx}: {_df.iloc[idx]['Name']}")
        
        indices = get_similar_indices(idx, top_n=5)
        print(f"Found similar indices: {indices}")
        
        similar_fragrances = []
        for i in indices:
            try:
                fragrance = _df.iloc[i]
                similar_fragrances.append({
                    'id': int(i),
                    'name': str(fragrance['Name']),
                    'brand': str(fragrance.get('Brand', '')),
                    'gender': str(fragrance.get('Gender', '')),
                    'rating_value': float(fragrance.get('Rating Value', 0)),
                    'rating_count': int(fragrance.get('Rating Count', 0)),
                    'main_accords': str(fragrance.get('Main Accords', '')),
                    'description': str(fragrance.get('Description', '')),
                    'url': str(fragrance.get('url', ''))
                })
            except Exception as e:
                print(f"Error processing fragrance at index {i}: {str(e)}")
                continue

        print(f"Successfully found {len(similar_fragrances)} similar fragrances")
        return jsonify({
            "recommendations": similar_fragrances,
            "type": "similar",
            "count": len(similar_fragrances)
        }), 200

    except Exception as e:
        import traceback
        print(f"Error in get_similar_fragrances:")
        print(traceback.format_exc())
        return jsonify({"error": str(e), "recommendations": []}), 500

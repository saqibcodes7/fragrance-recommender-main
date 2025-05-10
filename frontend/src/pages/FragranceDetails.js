import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  getFragrance,
  getSimilarFragrances,
  checkFavorite,
  addToFavorites,
  removeFromFavorites,
} from '../api/requests';

const FragranceDetails = () => {
  const { id } = useParams();
  const [fragrance, setFragrance] = useState(null);
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isFavorite, setIsFavorite] = useState(false);
  const [favoriteId, setFavoriteId] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const fragranceData = await getFragrance(id);
        setFragrance(fragranceData);

        // Get similar fragrances
        if (fragranceData && fragranceData.name) {
          console.log("Fetching similar fragrances for:", fragranceData.name);
          const similarFragrances = await getSimilarFragrances(fragranceData.name);
          console.log("Similar fragrances response:", similarFragrances);
          
          // Check if we have valid recommendations
          if (Array.isArray(similarFragrances) && similarFragrances.length > 0) {
            setRecommendations(similarFragrances);
          } else {
            console.log("No similar fragrances found");
            setRecommendations([]);
          }
        }

        const favData = await checkFavorite(id);
        setIsFavorite(favData.is_favorite);
        if (favData.is_favorite) setFavoriteId(favData.favorite_id);
      } catch (err) {
        console.error('Error in fetchData:', err);
        setError('Error loading fragrance details');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [id]);

  const handleFavoriteToggle = async () => {
    try {
      if (isFavorite) {
        await removeFromFavorites(favoriteId);
        setIsFavorite(false);
        setFavoriteId(null);
      } else {
        const result = await addToFavorites(id);
        setIsFavorite(true);
        setFavoriteId(result.favorite_id);
      }
    } catch (err) {
      console.error('Favorite toggle failed:', err);
    }
  };

  if (loading) return <div className="text-center py-5">Loading...</div>;

  if (error || !fragrance) {
    return (
      <div className="container my-5">
        <div className="alert alert-danger">{error || 'Fragrance not found'}</div>
        <Link to="/" className="btn btn-primary">Back to Home</Link>
      </div>
    );
  }

  return (
    <div className="container my-5">
      <div className="row mb-5">
        <div className="col-md-4">
          <div className="card shadow-sm mb-3">
            {fragrance.url ? (
              <img
                src={`${process.env.PUBLIC_URL}/images/${fragrance.id}.jpg`}
                alt={fragrance.name}
                className="img-fluid rounded-top"
                style={{ height: '250px', objectFit: 'cover', width: '100%' }}
                onError={(e) => {
                  e.target.style.display = 'none';
                  e.target.nextElementSibling.style.display = 'flex';
                }}
              />
            ) : null}
            <div 
              className="d-none bg-light rounded-top" 
              style={{ 
                height: '250px', 
                width: '100%', 
                display: 'flex', 
                alignItems: 'center', 
                justifyContent: 'center',
                color: '#666'
              }}
            >
              <div className="text-center">
                <i className="fas fa-flask fa-3x mb-2"></i><br/>
                {fragrance.name}
              </div>
            </div>
            <div className="card-body">
              <h5>Details</h5>
              <ul className="list-group list-group-flush">
                <li className="list-group-item px-0"><strong>Gender:</strong> {fragrance.gender}</li>
                <li className="list-group-item px-0"><strong>Brand:</strong> {fragrance.brand}</li>
                <li className="list-group-item px-0">
                  <strong>Rating:</strong> 
                  <span className="text-warning ms-2">
                    {'★'.repeat(Math.round(fragrance.rating_value || 0))}
                    {'☆'.repeat(5 - Math.round(fragrance.rating_value || 0))}
                  </span>
                  ({fragrance.rating_count || 0})
                </li>
              </ul>
            </div>
          </div>
        </div>

        <div className="col-md-8">
          <div className="card shadow-sm">
            <div className="card-body">
              <h1>{fragrance.name}</h1>
              <h5 className="text-muted">{fragrance.brand}</h5>

              <div className="d-flex mb-4">
                <button className="btn btn-outline-danger me-2" onClick={handleFavoriteToggle}>
                  <i className={`fas fa-heart ${isFavorite ? 'text-danger' : ''}`}></i>
                  {isFavorite ? ' Remove Favorite' : ' Add Favorite'}
                </button>
                {fragrance.url && (
                  <a href={fragrance.url} target="_blank" rel="noopener noreferrer" className="btn btn-outline-secondary">
                    View on Fragrantica
                  </a>
                )}
              </div>

              <h5>Description</h5>
              <p>{fragrance.description || 'No description available'}</p>

              <h5 className="mt-4">Main Accords</h5>
              {fragrance.main_accords ? fragrance.main_accords.split(',').map((a, i) => (
                <span key={i} className="badge bg-secondary me-1 mb-1">{a.trim()}</span>
              )) : <p>No accords available.</p>}

              <h5 className="mt-4">Scent Notes</h5>
              {fragrance.scent_notes && fragrance.scent_notes.length > 0 ? (
                <p>{fragrance.scent_notes.join(', ')}</p>
              ) : (
                <p className="text-muted">No scent notes available.</p>
              )}
            </div>
          </div>
        </div>
      </div>

      <div className="card shadow-sm mt-5">
        <div className="card-body">
          <h3 className="mb-4">Similar Fragrances</h3>
          {recommendations.length === 0 ? (
            <p className="text-muted">No similar fragrances found.</p>
          ) : (
            <div className="row">
              {recommendations.map((rec, i) => (
                <div key={rec.id || i} className="col-md-4 mb-4">
                  <div className="card h-100 shadow-sm">
                    <div style={{ height: '200px', position: 'relative' }}>
                      {rec.url ? (
                        <img
                          src={`/images/${rec.id}.jpg`}
                          alt={rec.name}
                          className="card-img-top"
                          style={{ height: '100%', objectFit: 'cover' }}
                          onError={(e) => {
                            e.target.style.display = 'none';
                            e.target.nextElementSibling.style.display = 'flex';
                          }}
                        />
                      ) : null}
                      <div 
                        className="d-none bg-light" 
                        style={{ 
                          position: 'absolute',
                          top: 0,
                          left: 0,
                          right: 0,
                          bottom: 0,
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          color: '#666'
                        }}
                      >
                        <div className="text-center">
                          <i className="fas fa-flask fa-2x mb-2"></i><br/>
                          {rec.name}
                        </div>
                      </div>
                    </div>
                    <div className="card-body">
                      <h5 className="card-title">{rec.name}</h5>
                      <h6 className="card-subtitle mb-2 text-muted">{rec.brand}</h6>
                      <div className="mb-2">
                        <span className="text-warning">
                          {'★'.repeat(Math.round(rec.rating_value || 0))}
                          {'☆'.repeat(5 - Math.round(rec.rating_value || 0))}
                        </span>
                        <small> ({rec.rating_count || 0} reviews)</small>
                      </div>
                      <p className="card-text">{rec.description?.substring(0, 100)}...</p>
                    </div>
                    <div className="card-footer bg-white border-top-0">
                      <Link to={`/fragrance/${rec.id}`} className="btn btn-primary btn-sm w-100">
                        View Details
                      </Link>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default FragranceDetails;

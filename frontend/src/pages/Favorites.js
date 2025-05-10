import React, { useState, useEffect } from 'react';
import { Link as RouterLink } from 'react-router-dom';
import { getFavorites, removeFromFavorites } from '../api/requests';
import {
  Container,
  Typography,
  Grid,
  Card,
  CardContent,
  CardActions,
  Button,
  Chip,
  Stack,
  CircularProgress,
  Alert,
  IconButton,
  Box,
} from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';

const Favorites = () => {
  const [favorites, setFavorites] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchFavorites();
  }, []);

  const fetchFavorites = async () => {
    setLoading(true);
    try {
      const data = await getFavorites();
      console.log("Received favorites data:", data);
      // Handle both potential response formats
      const favList = data.favourites || [];
      setFavorites(favList);
      setError(null);
    } catch (err) {
      console.error("Error fetching favorites:", err);
      setError('Error loading favorites');
    } finally {
      setLoading(false);
    }
  };

  const handleRemove = async (favoriteId) => {
    try {
      await removeFromFavorites(favoriteId);
      setFavorites(favorites.filter(fav => fav.favorite_id !== favoriteId));
      // Provide user feedback
      console.log("Successfully removed from favorites");
    } catch (err) {
      console.error('Error removing from favorites:', err);
      setError('Failed to remove fragrance from favorites');
      // Clear error after 3 seconds
      setTimeout(() => setError(null), 3000);
    }
  };

  if (loading) {
    return (
      <Container sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '50vh' }}>
        <CircularProgress sx={{ color: '#FFD700' }} />
      </Container>
    );
  }

  const formatAccords = (accords) => {
    if (!accords) return [];
    if (Array.isArray(accords)) return accords;
    if (typeof accords === 'string') {
      try {
        const parsed = JSON.parse(accords);
        if (Array.isArray(parsed)) return parsed;
      } catch {
        // If parsing fails, continue with string processing
      }
      return accords.replace(/[\[\]'"]+/g, '').split(',').map(item => item.trim());
    }
    return [];
  };

  return (
    <Container sx={{ mt: 5, pb: 5 }}>
      <Typography variant="h4" gutterBottom sx={{ color: '#FFD700', mb: 3 }}>
        Your Favourite Fragrances
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {favorites.length === 0 ? (
        <Box sx={{ backgroundColor: '#2a2a2a', p: 4, borderRadius: 2 }}>
          <Typography variant="h6" sx={{ color: '#FFD700', mb: 2 }}>
            You don't have any favorite fragrances yet.
          </Typography>
          <Typography variant="body1" sx={{ color: '#ccc', mb: 3 }}>
            Add fragrances to your favorites to see them here. They'll also influence your personalized recommendations.
          </Typography>
          <Stack direction="row" spacing={2}>
            <Button 
              variant="contained" 
              component={RouterLink} 
              to="/search"
              sx={{
                backgroundColor: '#FFD700',
                color: 'black',
                '&:hover': { backgroundColor: '#e6c200' }
              }}
            >
              Search Fragrances
            </Button>
            <Button 
              variant="outlined" 
              component={RouterLink} 
              to="/quiz"
              sx={{
                borderColor: '#FFD700',
                color: '#FFD700',
                '&:hover': { backgroundColor: 'rgba(255, 215, 0, 0.1)' }
              }}
            >
              Take Our Quiz
            </Button>
          </Stack>
        </Box>
      ) : (
        <Grid container spacing={3}>
          {favorites.map((item) => {
            console.log("Processing favorite item:", item);
            const fragrance = item.fragrance || {};
            return (
              <Grid item xs={12} sm={6} md={4} key={item.favorite_id || `fav-${Math.random()}`}>
                <Card 
                  sx={{ 
                    backgroundColor: '#2a2a2a', 
                    color: 'white',
                    height: '100%',
                    display: 'flex',
                    flexDirection: 'column',
                    transition: 'transform 0.3s',
                    '&:hover': {
                      transform: 'translateY(-5px)',
                      boxShadow: '0 10px 20px rgba(0,0,0,0.3)'
                    }
                  }}
                >
                  <CardContent sx={{ flexGrow: 1 }}>
                    <Stack direction="row" justifyContent="space-between" alignItems="start">
                      <Typography variant="h6" sx={{ color: '#FFD700' }}>
                        {fragrance.name || "Unknown Fragrance"}
                      </Typography>
                      <IconButton 
                        onClick={() => handleRemove(item.favorite_id)} 
                        sx={{ 
                          color: '#ff6b6b',
                          '&:hover': { backgroundColor: 'rgba(255, 107, 107, 0.1)' }
                        }}
                      >
                        <DeleteIcon />
                      </IconButton>
                    </Stack>
                    <Typography variant="subtitle2" sx={{ color: '#aaa', mb: 1 }}>
                      {fragrance.brand || "Unknown Brand"}
                    </Typography>
                    
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                      <Typography variant="body2" sx={{ color: '#FFD700' }}>
                        {'★'.repeat(Math.round(fragrance.rating_value || 0))}
                        <span style={{ color: '#555' }}>{'☆'.repeat(5 - Math.round(fragrance.rating_value || 0))}</span>
                      </Typography>
                      <Typography variant="body2" sx={{ color: '#999', ml: 1 }}>
                        ({fragrance.rating_count || 0} reviews)
                      </Typography>
                    </Box>

                    {fragrance.main_accords && (
                      <Box sx={{ mb: 2 }}>
                        <Typography variant="body2" sx={{ color: '#aaa', mb: 1 }}>
                          <strong>Key Notes:</strong>
                        </Typography>
                        <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                          {formatAccords(fragrance.main_accords)
                            .slice(0, 3)
                            .map((accord, idx) => (
                              <Chip
                                key={idx}
                                label={accord}
                                size="small"
                                sx={{
                                  backgroundColor: '#444',
                                  color: '#FFD700',
                                  fontSize: '0.75rem',
                                  mb: 0.5
                                }}
                              />
                            ))}
                        </Stack>
                      </Box>
                    )}

                    <Typography variant="body2" sx={{ color: '#ccc', mb: 2 }}>
                      {fragrance.description?.substring(0, 100)}
                      {fragrance.description && fragrance.description.length > 100 ? '...' : ''}
                    </Typography>
                  </CardContent>
                  <CardActions>
                    <Button
                      size="small"
                      variant="contained"
                      fullWidth
                      sx={{ 
                        backgroundColor: '#FFD700', 
                        color: 'black',
                        '&:hover': { backgroundColor: '#e6c200' }
                      }}
                      component={RouterLink}
                      to={`/fragrance/${fragrance.id}`}
                    >
                      View Details
                    </Button>
                  </CardActions>
                </Card>
              </Grid>
            );
          })}
        </Grid>
      )}
    </Container>
  );
};

export default Favorites;

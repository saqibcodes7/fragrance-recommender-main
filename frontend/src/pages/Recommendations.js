import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import {
  Container,
  Typography,
  Grid,
  Card,
  CardContent,
  Button,
  Box,
  Chip,
  Stack,
  Rating,
  Alert,
  Divider,
  Pagination,
  CircularProgress
} from '@mui/material';
import { Star, StarBorder } from '@mui/icons-material';
import { getRecommendations } from '../api/requests';

const Recommendations = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { quizAnswers, recommendations: initialRecommendations, error: initialError } = location.state || {};
  
  const [recommendations, setRecommendations] = useState(initialRecommendations || []);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(initialError || '');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [displayedRecs, setDisplayedRecs] = useState([]);
  
  // Number of recommendations to display per page
  const itemsPerPage = 6;
  
  useEffect(() => {
    // If we have recommendations from quiz, paginate them client-side
    if (initialRecommendations?.length > 0) {
      const totalPgs = Math.ceil(initialRecommendations.length / itemsPerPage);
      setTotalPages(totalPgs || 1);
      
      // Initial display
      updateDisplayedRecommendations(initialRecommendations, 1);
    } else {
      // Otherwise fetch recommendations from API
      fetchRecommendations();
    }
  }, []);
  
  const updateDisplayedRecommendations = (allRecs, currentPage) => {
    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = startIndex + itemsPerPage;
    setDisplayedRecs(allRecs.slice(startIndex, endIndex));
  };
  
  const handlePageChange = async (event, newPage) => {
    setPage(newPage);
    
    if (initialRecommendations?.length > 0) {
      // Client-side pagination if we have all recommendations
      updateDisplayedRecommendations(initialRecommendations, newPage);
    } else {
      // Server-side pagination
      await fetchRecommendations(newPage);
    }
    
    // Scroll to top of recommendations
    window.scrollTo({
      top: document.getElementById('recommendations-top').offsetTop - 20,
      behavior: 'smooth'
    });
  };
  
  const fetchRecommendations = async (pageNum = 1) => {
    setLoading(true);
    try {
      const response = await getRecommendations(pageNum, itemsPerPage);
      setRecommendations(response.recommendations || []);
      setDisplayedRecs(response.recommendations || []);
      setTotalPages(Math.ceil(response.count / itemsPerPage) || 1);
      setError('');
    } catch (err) {
      console.error("Error fetching recommendations:", err);
      setError('Failed to load recommendations. Please try again later.');
    } finally {
      setLoading(false);
    }
  };

  const formatAccords = (accords) => {
    if (!accords) return [];
    if (Array.isArray(accords)) return accords;
    if (typeof accords === 'string') {
      try {
        const parsed = JSON.parse(accords);
        if (Array.isArray(parsed)) return parsed;
      } catch {
      
      }
      return accords.replace(/[\[\]'"]+/g, '').split(',').map((item) => item.trim());
    }
    return [];
  };

  const getExperienceDescription = () => {
    if (!quizAnswers?.experience_level) return '';
    const levels = {
      Beginner: 'Beginner (just starting out)',
      Intermediate: 'Intermediate (tried a few fragrances)',
      Advanced: 'Advanced (understand notes and accords)'
    };
    return levels[quizAnswers.experience_level] || '';
  };

  const renderRating = (value) => (
    <Rating
      value={value}
      precision={0.5}
      readOnly
      icon={<Star fontSize="inherit" sx={{ color: '#FFD700' }} />}
      emptyIcon={<StarBorder fontSize="inherit" sx={{ color: '#FFD700' }} />}
    />
  );

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Typography variant="h4" gutterBottom sx={{ color: '#FFD700', textAlign: 'center', mb: 4 }}>
        Your Personalised Fragrance Recommendations
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 4 }}>
          {error}
        </Alert>
      )}

      {quizAnswers && (
        <Box
          sx={{
            mb: 4,
            p: 3,
            backgroundColor: '#2a2a2a',
            borderRadius: 2,
            borderLeft: '4px solid #FFD700'
          }}
        >
          <Typography variant="h6" gutterBottom sx={{ color: '#FFD700' }}>
            Your Fragrance Profile
          </Typography>
          <Divider sx={{ my: 2, backgroundColor: '#444' }} />

          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <Typography variant="body1" sx={{ mb: 1 }}>
                <strong>Experience:</strong> {getExperienceDescription()}
              </Typography>
              {quizAnswers.longevity && (
                <Typography variant="body1" sx={{ mb: 1 }}>
                  <strong>Longevity Preference:</strong> {quizAnswers.longevity}
                </Typography>
              )}
            </Grid>
            <Grid item xs={12} md={6}>
              {quizAnswers.desired_accords?.length > 0 && (
                <Box>
                  <Typography variant="body1" sx={{ mb: 1 }}>
                    <strong>Preferred Scents:</strong>
                  </Typography>
                  <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                    {quizAnswers.desired_accords.map((accord, index) => (
                      <Chip
                        key={index}
                        label={accord}
                        sx={{
                          backgroundColor: '#FFD700',
                          color: 'black',
                          fontWeight: 'bold'
                        }}
                      />
                    ))}
                  </Stack>
                </Box>
              )}
            </Grid>
          </Grid>
        </Box>
      )}
      
      <div id="recommendations-top"></div>
      
      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', my: 5 }}>
          <CircularProgress sx={{ color: '#FFD700' }} />
        </Box>
      ) : displayedRecs?.length > 0 ? (
        <>
          <Typography variant="h5" gutterBottom sx={{ color: '#FFD700', mt: 2 }}>
            Recommended For You
          </Typography>
          <Grid container spacing={3}>
            {displayedRecs.map((fragrance, index) => (
              <Grid item xs={12} sm={6} md={4} key={index}>
                <Card
                  sx={{
                    height: '100%',
                    display: 'flex',
                    flexDirection: 'column',
                    backgroundColor: '#2a2a2a',
                    color: 'white',
                    border: '1px solid #444',
                    transition: 'transform 0.3s',
                    '&:hover': {
                      transform: 'translateY(-5px)',
                      boxShadow: '0 10px 20px rgba(0,0,0,0.3)'
                    }
                  }}
                >
                  <CardContent>
                    <Typography variant="h6" sx={{ color: '#FFD700', mb: 1 }}>
                      {fragrance.Name}
                    </Typography>
                    <Typography variant="subtitle1" sx={{ color: '#aaa', mb: 2 }}>
                      {fragrance.Brand}
                    </Typography>

                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                      {renderRating(fragrance['Rating Value'])}
                      <Typography variant="body2" sx={{ color: '#999', ml: 1 }}>
                        ({fragrance['Rating Count'] || 0} reviews)
                      </Typography>
                    </Box>

                    {fragrance['Main Accords'] && (
                      <Box sx={{ mb: 2 }}>
                        <Typography variant="body2" sx={{ color: '#aaa', mb: 1 }}>
                          <strong>Key Notes:</strong>
                        </Typography>
                        <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                          {formatAccords(fragrance['Main Accords'])
                            .slice(0, 5)
                            .map((accord, idx) => (
                              <Chip
                                key={idx}
                                label={accord}
                                size="small"
                                sx={{
                                  backgroundColor: '#444',
                                  color: '#FFD700',
                                  fontSize: '0.75rem'
                                }}
                              />
                            ))}
                        </Stack>
                      </Box>
                    )}

                    <Typography variant="body2" sx={{ color: '#ccc', mb: 2 }}>
                      {fragrance.Description?.substring(0, 150)}...
                    </Typography>

                    <Button
                      variant="contained"
                      fullWidth
                      sx={{
                        backgroundColor: '#FFD700',
                        color: 'black',
                        '&:hover': {
                          backgroundColor: '#e6c200'
                        }
                      }}
                      onClick={() => navigate(`/fragrance/${fragrance.id || index}`)}
                    >
                      View Details
                    </Button>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
          
          {/* Pagination */}
          {totalPages > 1 && (
            <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
              <Pagination 
                count={totalPages} 
                page={page} 
                onChange={handlePageChange} 
                variant="outlined" 
                shape="rounded"
                sx={{
                  '& .MuiPaginationItem-root': {
                    color: '#FFD700',
                    borderColor: '#444',
                  },
                  '& .Mui-selected': {
                    backgroundColor: 'rgba(255, 215, 0, 0.2) !important',
                  }
                }}
              />
            </Box>
          )}
        </>
      ) : (
        <Box
          sx={{
            textAlign: 'center',
            my: 10,
            p: 4,
            backgroundColor: '#2a2a2a',
            borderRadius: 2
          }}
        >
          <Typography variant="h6" sx={{ color: '#FFD700', mb: 2 }}>
            No Recommendations Found
          </Typography>
          <Typography variant="body1" sx={{ color: '#ccc', mb: 3 }}>
            We couldn't find perfect matches based on your preferences.
          </Typography>
          <Button
            variant="contained"
            onClick={() => navigate('/quiz')}
            sx={{
              backgroundColor: '#FFD700',
              color: 'black',
              '&:hover': {
                backgroundColor: '#e6c200'
              }
            }}
          >
            Retake Quiz
          </Button>
        </Box>
      )}
    </Container>
  );
};

export default Recommendations;

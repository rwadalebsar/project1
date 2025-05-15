import { Navigate, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

const ProtectedRoute = ({ children, requiredSubscription = null }) => {
  const { user, token, loading, hasSubscription } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  console.log('ProtectedRoute - Auth state:', { user, token, loading });

  // Check localStorage directly
  const storedUser = localStorage.getItem('user');
  const storedToken = localStorage.getItem('token');
  console.log('ProtectedRoute - localStorage:', {
    user: storedUser ? 'exists' : 'missing',
    token: storedToken ? 'exists' : 'missing'
  });

  // Use either context or localStorage for authentication
  let isAuthenticated = false;
  let userObj = null;

  // First check context
  if (user && token) {
    isAuthenticated = true;
    userObj = user;
  }
  // Then check localStorage
  else if (storedUser && storedToken) {
    try {
      userObj = JSON.parse(storedUser);
      if (userObj && userObj.username) {
        isAuthenticated = true;
      }
    } catch (error) {
      console.error('ProtectedRoute - Error parsing stored user:', error);
      // Clear invalid data
      localStorage.removeItem('user');
      localStorage.removeItem('token');
    }
  }

  // If we have inconsistent state, clear it
  if (!isAuthenticated) {
    localStorage.removeItem('user');
    localStorage.removeItem('token');
  }

  if (loading) {
    console.log('ProtectedRoute - Still loading auth state');
    // Show loading state while checking authentication
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
        <p>Loading...</p>
      </div>
    );
  }

  // If not authenticated, redirect to login
  if (!isAuthenticated) {
    console.log('ProtectedRoute - User not authenticated, redirecting to login');
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // If subscription tier is required, check if user has it
  if (requiredSubscription && userObj) {
    // Use hasSubscription function if available, otherwise do a simple check
    if (hasSubscription && typeof hasSubscription === 'function') {
      if (!hasSubscription(requiredSubscription)) {
        console.log('ProtectedRoute - User lacks required subscription:', requiredSubscription);
        return <Navigate to="/subscription" state={{ requiredTier: requiredSubscription }} replace />;
      }
    } else {
      // Simple subscription check
      const tierLevels = {
        'free': 0,
        'basic': 1,
        'premium': 2
      };

      const userTierLevel = tierLevels[userObj.subscription_tier] || 0;
      const requiredTierLevel = tierLevels[requiredSubscription] || 0;

      if (userTierLevel < requiredTierLevel) {
        console.log('ProtectedRoute - User lacks required subscription:', requiredSubscription);
        return <Navigate to="/subscription" state={{ requiredTier: requiredSubscription }} replace />;
      }
    }
  }

  console.log('ProtectedRoute - User authenticated, rendering protected content');
  // User is authenticated and has required subscription, render the protected component
  return children;
};

export default ProtectedRoute;

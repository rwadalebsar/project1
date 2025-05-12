import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

const ProtectedRoute = ({ children, requiredSubscription = null }) => {
  const { user, loading, hasSubscription } = useAuth();
  const location = useLocation();

  if (loading) {
    // Show loading state while checking authentication
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
        <p>Loading...</p>
      </div>
    );
  }

  // If not authenticated, redirect to login
  if (!user) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // If subscription tier is required, check if user has it
  if (requiredSubscription && !hasSubscription(requiredSubscription)) {
    return <Navigate to="/subscription" state={{ requiredTier: requiredSubscription }} replace />;
  }

  // User is authenticated and has required subscription, render the protected component
  return children;
};

export default ProtectedRoute;

import { createContext, useState, useEffect, useContext } from 'react';
import axios from 'axios';

// Create the context
const AuthContext = createContext();

// Custom hook to use the auth context
export const useAuth = () => {
  return useContext(AuthContext);
};

// Provider component
export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [loading, setLoading] = useState(true);
  const [initialized, setInitialized] = useState(false);

  // Initialize auth state from localStorage
  useEffect(() => {
    const storedToken = localStorage.getItem('token');
    const storedUser = localStorage.getItem('user');

    if (storedToken && storedUser) {
      setToken(storedToken);
      setUser(JSON.parse(storedUser));
    }

    setLoading(false);
    setInitialized(true);
  }, []);

  // Set up axios interceptor for authentication
  useEffect(() => {
    if (!initialized) return;

    // Add token to all requests
    const interceptor = axios.interceptors.request.use(
      config => {
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      error => Promise.reject(error)
    );

    // Remove interceptor on cleanup
    return () => {
      axios.interceptors.request.eject(interceptor);
    };
  }, [token, initialized]);

  // Login function
  const login = (userData, authToken) => {
    setUser(userData);
    setToken(authToken);
    localStorage.setItem('user', JSON.stringify(userData));
    localStorage.setItem('token', authToken);
  };

  // Logout function
  const logout = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem('user');
    localStorage.removeItem('token');
  };

  // Update user data
  const updateUser = (userData) => {
    setUser(userData);
    localStorage.setItem('user', JSON.stringify(userData));
  };

  // Check if user has a specific subscription tier
  const hasSubscription = (tier) => {
    if (!user) return false;
    
    const tierLevels = {
      'free': 0,
      'basic': 1,
      'premium': 2
    };
    
    const userTierLevel = tierLevels[user.subscription_tier] || 0;
    const requiredTierLevel = tierLevels[tier] || 0;
    
    return userTierLevel >= requiredTierLevel;
  };

  // Context value
  const value = {
    user,
    token,
    loading,
    login,
    logout,
    updateUser,
    hasSubscription,
    isAuthenticated: !!user
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export default AuthContext;

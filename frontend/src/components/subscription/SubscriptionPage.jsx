import { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import axios from 'axios';
import { useAuth } from '../../context/AuthContext';
import './Subscription.css';

// For debugging
console.log('SubscriptionPage module loaded');

const SubscriptionPage = () => {
  const [subscriptionTiers, setSubscriptionTiers] = useState({});
  const [currentSubscription, setCurrentSubscription] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [billingCycle, setBillingCycle] = useState('monthly');
  const { user, token, updateUser, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  // Debug auth state
  console.log('SubscriptionPage - Auth state:', {
    user,
    token: token ? 'exists' : 'missing',
    isAuthenticated
  });

  // Get the required tier from location state if available
  const requiredTier = location.state?.requiredTier;

  useEffect(() => {
    const fetchSubscriptionData = async () => {
      console.log('SubscriptionPage - fetchSubscriptionData called');
      setLoading(true);

      try {
        // Check if we have user data
        console.log('SubscriptionPage - User data check:', {
          userExists: !!user,
          userSubscriptionTier: user?.subscription_tier
        });

        // Hardcode subscription tiers as fallback
        const defaultTiers = {
          "free": {
            "name": "Free",
            "max_tanks": 1,
            "max_history_days": 7,
            "anomaly_detection": false,
            "price_monthly": 0.0,
            "price_yearly": 0.0
          },
          "basic": {
            "name": "Basic",
            "max_tanks": 5,
            "max_history_days": 30,
            "anomaly_detection": true,
            "price_monthly": 9.99,
            "price_yearly": 99.99
          },
          "premium": {
            "name": "Premium",
            "max_tanks": 100,
            "max_history_days": 365,
            "anomaly_detection": true,
            "price_monthly": 29.99,
            "price_yearly": 299.99
          }
        };

        // Try to fetch subscription tiers, but use defaults if it fails
        let tiers = defaultTiers;
        try {
          console.log('SubscriptionPage - Fetching subscription tiers');
          const tiersResponse = await axios.get(
            `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/subscription/tiers`
          );
          console.log('SubscriptionPage - Tiers response:', tiersResponse.data);
          tiers = tiersResponse.data || defaultTiers;
        } catch (tierError) {
          console.error('SubscriptionPage - Error fetching tiers:', tierError);
          // Continue with default tiers
        }

        setSubscriptionTiers(tiers);

        // If we have user data, create current subscription
        if (user && user.subscription_tier) {
          const currentSubscriptionData = {
            tier: user.subscription_tier,
            tier_details: tiers[user.subscription_tier],
            expires_at: null // We don't have this information in the user object
          };

          console.log('SubscriptionPage - Setting current subscription:', currentSubscriptionData);
          setCurrentSubscription(currentSubscriptionData);
          setError(''); // Clear any previous errors
        } else {
          // Use a default subscription if user data is not available
          console.log('SubscriptionPage - Using default free subscription');
          setCurrentSubscription({
            tier: 'free',
            tier_details: tiers.free,
            expires_at: null
          });
        }
      } catch (err) {
        console.error('SubscriptionPage - Error in fetchSubscriptionData:', err);
        setError('Failed to load subscription information. Please try again later.');
      } finally {
        setLoading(false);
      }
    };

    fetchSubscriptionData();
  }, [user]);

  const handleSubscribe = async (tier) => {
    // In a real application, this would redirect to a payment processor
    // For this demo, we'll just simulate a successful subscription
    alert(`This would redirect to a payment page for the ${tier} subscription.`);

    // For demo purposes, let's pretend the subscription was successful
    // In a real app, this would be handled by a webhook from the payment processor
    try {
      // Get the token from localStorage
      const token = localStorage.getItem('token');

      if (!token) {
        throw new Error('Authentication token not found');
      }

      // This endpoint doesn't exist in our demo, but would in a real app
      // await axios.post(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/subscription/upgrade`, {
      //   tier: tier
      // }, {
      //   headers: {
      //     'Authorization': `Bearer ${token}`
      //   }
      // });

      // Update the user object with the new subscription tier
      const updatedUser = {
        ...user,
        subscription_tier: tier
      };

      updateUser(updatedUser);

      // Redirect to dashboard
      window.location.href = '/dashboard';
    } catch (err) {
      console.error('Error upgrading subscription:', err);
      setError('Failed to upgrade subscription. Please try again later.');
    }
  };

  if (loading) {
    return (
      <div className="subscription-container">
        <div className="loading-spinner"></div>
        <p>Loading subscription information...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="subscription-container">
        <div className="error-message">{error}</div>
        <button onClick={() => window.location.href = '/dashboard'} className="back-button">
          Back to Dashboard
        </button>
      </div>
    );
  }

  return (
    <div className="subscription-container">
      <div className="subscription-header">
        <h1>Choose Your Subscription Plan</h1>
        <p>Select the plan that best fits your monitoring needs</p>

        {requiredTier && (
          <div className="upgrade-notice">
            <p>You need at least a <strong>{subscriptionTiers[requiredTier]?.name}</strong> subscription to access this feature.</p>
          </div>
        )}

        <div className="billing-toggle">
          <span className={billingCycle === 'monthly' ? 'active' : ''}>Monthly</span>
          <label className="switch">
            <input
              type="checkbox"
              checked={billingCycle === 'yearly'}
              onChange={() => setBillingCycle(billingCycle === 'monthly' ? 'yearly' : 'monthly')}
            />
            <span className="slider round"></span>
          </label>
          <span className={billingCycle === 'yearly' ? 'active' : ''}>Yearly <span className="save-badge">Save 15%</span></span>
        </div>
      </div>

      <div className="subscription-plans">
        {Object.entries(subscriptionTiers).map(([key, tier]) => (
          <div
            key={key}
            className={`plan-card ${currentSubscription?.tier === key ? 'current-plan' : ''}`}
          >
            <div className="plan-header">
              <h2>{tier.name}</h2>
              <div className="plan-price">
                <span className="currency">$</span>
                <span className="amount">
                  {billingCycle === 'monthly' ? tier.price_monthly : tier.price_yearly}
                </span>
                <span className="period">/{billingCycle === 'monthly' ? 'month' : 'year'}</span>
              </div>
            </div>

            <div className="plan-features">
              <ul>
                <li>
                  <span className="feature-check">✓</span>
                  Up to {tier.max_tanks} tanks
                </li>
                <li>
                  <span className="feature-check">✓</span>
                  {tier.max_history_days} days of history
                </li>
                <li>
                  <span className={tier.anomaly_detection ? "feature-check" : "feature-x"}>
                    {tier.anomaly_detection ? "✓" : "✗"}
                  </span>
                  Anomaly detection
                </li>
                {key === 'premium' && (
                  <>
                    <li>
                      <span className="feature-check">✓</span>
                      Priority support
                    </li>
                    <li>
                      <span className="feature-check">✓</span>
                      Custom reports
                    </li>
                  </>
                )}
              </ul>
            </div>

            <div className="plan-action">
              {currentSubscription?.tier === key ? (
                <button className="current-plan-button" disabled>Current Plan</button>
              ) : (
                <button
                  className="subscribe-button"
                  onClick={() => handleSubscribe(key)}
                >
                  {currentSubscription?.tier ? 'Upgrade' : 'Subscribe'}
                </button>
              )}
            </div>
          </div>
        ))}
      </div>

      <div className="subscription-footer">
        <button onClick={() => window.location.href = '/dashboard'} className="back-button">
          Back to Dashboard
        </button>
      </div>
    </div>
  );
};

export default SubscriptionPage;

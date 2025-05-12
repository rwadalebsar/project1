import { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import axios from 'axios';
import { useAuth } from '../../context/AuthContext';
import './Subscription.css';

const SubscriptionPage = () => {
  const [subscriptionTiers, setSubscriptionTiers] = useState({});
  const [currentSubscription, setCurrentSubscription] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [billingCycle, setBillingCycle] = useState('monthly');
  const { user, updateUser } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  
  // Get the required tier from location state if available
  const requiredTier = location.state?.requiredTier;

  useEffect(() => {
    const fetchSubscriptionData = async () => {
      setLoading(true);
      try {
        // Fetch subscription tiers
        const tiersResponse = await axios.get(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/subscription/tiers`);
        setSubscriptionTiers(tiersResponse.data);
        
        // Fetch current subscription
        const currentResponse = await axios.get(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/subscription/current`);
        setCurrentSubscription(currentResponse.data);
      } catch (err) {
        console.error('Error fetching subscription data:', err);
        setError('Failed to load subscription information. Please try again later.');
      } finally {
        setLoading(false);
      }
    };

    fetchSubscriptionData();
  }, []);

  const handleSubscribe = async (tier) => {
    // In a real application, this would redirect to a payment processor
    // For this demo, we'll just simulate a successful subscription
    alert(`This would redirect to a payment page for the ${tier} subscription.`);
    
    // For demo purposes, let's pretend the subscription was successful
    // In a real app, this would be handled by a webhook from the payment processor
    try {
      // This endpoint doesn't exist in our demo, but would in a real app
      // await axios.post(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/subscription/upgrade`, {
      //   tier: tier
      // });
      
      // Update the user object with the new subscription tier
      const updatedUser = {
        ...user,
        subscription_tier: tier
      };
      
      updateUser(updatedUser);
      
      // Redirect to dashboard
      navigate('/dashboard');
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
        <button onClick={() => navigate('/dashboard')} className="back-button">
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
        <button onClick={() => navigate('/dashboard')} className="back-button">
          Back to Dashboard
        </button>
      </div>
    </div>
  );
};

export default SubscriptionPage;

import { useState } from 'react';
import axios from 'axios';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { useTranslation } from 'react-i18next';
import LanguageSwitcher from '../common/LanguageSwitcher';
import logoSvg from '../../assets/logo.svg';
import './ModernAuth.css';

const Login = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { login } = useAuth();
  const { t } = useTranslation();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await axios.post(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/auth/login`, {
        username,
        password
      });

      // Use the login function from AuthContext
      login(response.data.user, response.data.access_token);

      // Redirect to dashboard
      navigate('/dashboard');
    } catch (err) {
      console.error('Login error:', err);
      setError(err.response?.data?.detail || t('auth.loginFailed'));
    } finally {
      setLoading(false);
    }
  };

  // Feature icons
  const FeatureIcon = ({ icon }) => (
    <div className="feature-icon">
      {icon}
    </div>
  );

  // Dashboard icon
  const DashboardIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
    </svg>
  );

  // Analytics icon
  const AnalyticsIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
    </svg>
  );

  // Anomaly icon
  const AnomalyIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
    </svg>
  );

  // Multilingual icon
  const MultilingualIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5h12M9 3v2m1.048 9.5A18.022 18.022 0 016.412 9m6.088 9h7M11 21l5-10 5 10M12.751 5C11.783 10.77 8.07 15.61 3 18.129" />
    </svg>
  );

  return (
    <div className="auth-page-wrapper">
      <div className="modern-auth-container">
        {/* Left side - Login Form */}
        <div className="auth-form-container">
          <div className="auth-language-switcher">
            <LanguageSwitcher />
          </div>

          <div className="auth-logo-container">
            <img src={logoSvg} alt="Tank Monitor Logo" className="auth-logo" />
            <div className="auth-logo-text">TankMonitor</div>
          </div>

          <div className="modern-auth-header">
            <h1>{t('auth.loginTitle')}</h1>
            <p>{t('auth.loginSubtitle')}</p>
          </div>

          {error && <div className="modern-auth-error">{error}</div>}

          <form onSubmit={handleSubmit} className="modern-auth-form">
            <div className="modern-form-group">
              <label htmlFor="username">{t('auth.username')}</label>
              <input
                type="text"
                id="username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                className="modern-form-control"
                placeholder="Enter your username"
              />
            </div>

            <div className="modern-form-group">
              <label htmlFor="password">{t('auth.password')}</label>
              <input
                type="password"
                id="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="modern-form-control"
                placeholder="Enter your password"
              />
            </div>

            <button
              type="submit"
              className="modern-auth-button"
              disabled={loading}
            >
              {loading ? t('auth.loggingIn') : t('auth.loginButton')}
            </button>
          </form>

          <div className="modern-auth-footer">
            <p>{t('auth.noAccount')} <Link to="/register">{t('auth.register')}</Link></p>
          </div>
        </div>

        {/* Right side - Features Showcase */}
        <div className="auth-features-container">
          <div className="features-content">
            <div className="features-header">
              <h2>{t('auth.featuresTitle')}</h2>
              <p>{t('auth.featuresSubtitle')}</p>
            </div>

            <div className="feature-list">
              <div className="feature-item">
                <FeatureIcon icon={<DashboardIcon />} />
                <div className="feature-text">
                  <h3>{t('auth.features.realtime.title')}</h3>
                  <p>{t('auth.features.realtime.description')}</p>
                </div>
              </div>

              <div className="feature-item">
                <FeatureIcon icon={<AnalyticsIcon />} />
                <div className="feature-text">
                  <h3>{t('auth.features.analytics.title')}</h3>
                  <p>{t('auth.features.analytics.description')}</p>
                </div>
              </div>

              <div className="feature-item">
                <FeatureIcon icon={<AnomalyIcon />} />
                <div className="feature-text">
                  <h3>{t('auth.features.anomaly.title')}</h3>
                  <p>{t('auth.features.anomaly.description')}</p>
                </div>
              </div>

              <div className="feature-item">
                <FeatureIcon icon={<MultilingualIcon />} />
                <div className="feature-text">
                  <h3>{t('auth.features.multilingual.title')}</h3>
                  <p>{t('auth.features.multilingual.description')}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;

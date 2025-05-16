import React, { useState, useEffect } from 'react';
import axios from 'axios';

const SimpleApp = () => {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [user, setUser] = useState(null);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [tankLevels, setTankLevels] = useState([]);
  const [stats, setStats] = useState(null);

  // Check if user is already logged in
  useEffect(() => {
    const token = localStorage.getItem('token');
    const storedUser = localStorage.getItem('user');
    
    if (token && storedUser) {
      try {
        const parsedUser = JSON.parse(storedUser);
        if (parsedUser && parsedUser.username) {
          setIsLoggedIn(true);
          setUser(parsedUser);
          fetchData(token);
        }
      } catch (error) {
        console.error('Error parsing stored user:', error);
        localStorage.removeItem('user');
        localStorage.removeItem('token');
      }
    }
  }, []);

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    
    try {
      const response = await axios.post('http://localhost:8000/api/auth/login', {
        username,
        password
      });
      
      const { access_token, user } = response.data;
      
      // Store authentication data
      localStorage.setItem('token', access_token);
      localStorage.setItem('user', JSON.stringify(user));
      
      setIsLoggedIn(true);
      setUser(user);
      fetchData(access_token);
    } catch (error) {
      console.error('Login error:', error);
      setError('Login failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setIsLoggedIn(false);
    setUser(null);
    setTankLevels([]);
    setStats(null);
  };

  const fetchData = async (token) => {
    try {
      setLoading(true);
      
      const headers = { Authorization: `Bearer ${token}` };
      
      // Fetch tank levels
      const levelsResponse = await axios.get(
        'http://localhost:8000/api/tank-levels?days=30&tank_id=tank1',
        { headers }
      );
      
      // Sort by timestamp (newest first)
      const sortedData = [...levelsResponse.data].sort((a, b) =>
        new Date(b.timestamp) - new Date(a.timestamp)
      );
      setTankLevels(sortedData.slice(0, 5)); // Show only the 5 most recent readings
      
      // Fetch stats
      const statsResponse = await axios.get(
        'http://localhost:8000/api/stats?days=30&tank_id=tank1',
        { headers }
      );
      setStats(statsResponse.data);
      
      setError('');
    } catch (err) {
      console.error('Error fetching data:', err);
      setError('Error fetching data. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // Login form
  if (!isLoggedIn) {
    return (
      <div style={{ maxWidth: '400px', margin: '40px auto', padding: '20px', boxShadow: '0 0 10px rgba(0,0,0,0.1)' }}>
        <h1 style={{ textAlign: 'center', marginBottom: '20px' }}>Tank Monitor Login</h1>
        
        {error && (
          <div style={{ padding: '10px', backgroundColor: '#ffebee', color: '#c62828', marginBottom: '20px', borderRadius: '4px' }}>
            {error}
          </div>
        )}
        
        <form onSubmit={handleLogin}>
          <div style={{ marginBottom: '15px' }}>
            <label style={{ display: 'block', marginBottom: '5px' }}>Username:</label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              style={{ width: '100%', padding: '8px', borderRadius: '4px', border: '1px solid #ccc' }}
              required
            />
          </div>
          
          <div style={{ marginBottom: '20px' }}>
            <label style={{ display: 'block', marginBottom: '5px' }}>Password:</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              style={{ width: '100%', padding: '8px', borderRadius: '4px', border: '1px solid #ccc' }}
              required
            />
          </div>
          
          <button
            type="submit"
            disabled={loading}
            style={{
              width: '100%',
              padding: '10px',
              backgroundColor: '#1976d2',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: loading ? 'not-allowed' : 'pointer',
              opacity: loading ? 0.7 : 1
            }}
          >
            {loading ? 'Logging in...' : 'Login'}
          </button>
        </form>
        
        <div style={{ marginTop: '20px', textAlign: 'center', fontSize: '14px', color: '#666' }}>
          <p>Default admin credentials: username: admin, password: admin123</p>
        </div>
      </div>
    );
  }

  // Dashboard
  return (
    <div style={{ maxWidth: '800px', margin: '0 auto', padding: '20px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h1>Tank Monitor Dashboard</h1>
        <div>
          <span style={{ marginRight: '10px' }}>Welcome, {user.username}!</span>
          <button
            onClick={handleLogout}
            style={{
              padding: '8px 16px',
              backgroundColor: '#f44336',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer'
            }}
          >
            Logout
          </button>
        </div>
      </div>
      
      {error && (
        <div style={{ padding: '10px', backgroundColor: '#ffebee', color: '#c62828', marginBottom: '20px', borderRadius: '4px' }}>
          {error}
        </div>
      )}
      
      {loading ? (
        <div style={{ textAlign: 'center', padding: '40px' }}>Loading data...</div>
      ) : (
        <>
          {/* Stats */}
          {stats && (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '15px', marginBottom: '30px' }}>
              <div style={{ padding: '15px', backgroundColor: '#e3f2fd', borderRadius: '8px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
                <h3 style={{ margin: '0 0 10px 0' }}>Current Level</h3>
                <div style={{ fontSize: '24px', fontWeight: 'bold' }}>{stats.current_level?.toFixed(2)} m</div>
                <div style={{ fontSize: '12px', color: '#666', marginTop: '5px' }}>
                  Updated: {new Date(stats.last_updated).toLocaleString()}
                </div>
              </div>
              
              <div style={{ padding: '15px', backgroundColor: '#e8f5e9', borderRadius: '8px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
                <h3 style={{ margin: '0 0 10px 0' }}>Min Level</h3>
                <div style={{ fontSize: '24px', fontWeight: 'bold' }}>{stats.min_level?.toFixed(2)} m</div>
                <div style={{ fontSize: '12px', color: '#666', marginTop: '5px' }}>
                  Last {stats.count} readings
                </div>
              </div>
              
              <div style={{ padding: '15px', backgroundColor: '#fff8e1', borderRadius: '8px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
                <h3 style={{ margin: '0 0 10px 0' }}>Max Level</h3>
                <div style={{ fontSize: '24px', fontWeight: 'bold' }}>{stats.max_level?.toFixed(2)} m</div>
                <div style={{ fontSize: '12px', color: '#666', marginTop: '5px' }}>
                  Last {stats.count} readings
                </div>
              </div>
              
              <div style={{ padding: '15px', backgroundColor: '#f3e5f5', borderRadius: '8px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
                <h3 style={{ margin: '0 0 10px 0' }}>Average Level</h3>
                <div style={{ fontSize: '24px', fontWeight: 'bold' }}>{stats.avg_level?.toFixed(2)} m</div>
                <div style={{ fontSize: '12px', color: '#666', marginTop: '5px' }}>
                  Std Dev: {stats.std_dev?.toFixed(2)}
                </div>
              </div>
            </div>
          )}
          
          {/* Recent Readings */}
          <div style={{ marginBottom: '30px' }}>
            <h2>Recent Tank Readings</h2>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ backgroundColor: '#f5f5f5' }}>
                  <th style={{ padding: '10px', textAlign: 'left', borderBottom: '1px solid #ddd' }}>Date</th>
                  <th style={{ padding: '10px', textAlign: 'left', borderBottom: '1px solid #ddd' }}>Time</th>
                  <th style={{ padding: '10px', textAlign: 'left', borderBottom: '1px solid #ddd' }}>Level (m)</th>
                </tr>
              </thead>
              <tbody>
                {tankLevels.map((reading, index) => (
                  <tr key={index} style={{ backgroundColor: index % 2 === 0 ? 'white' : '#f9f9f9' }}>
                    <td style={{ padding: '10px', borderBottom: '1px solid #ddd' }}>
                      {new Date(reading.timestamp).toLocaleDateString()}
                    </td>
                    <td style={{ padding: '10px', borderBottom: '1px solid #ddd' }}>
                      {new Date(reading.timestamp).toLocaleTimeString()}
                    </td>
                    <td style={{ padding: '10px', borderBottom: '1px solid #ddd' }}>
                      {reading.level.toFixed(2)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          
          <button
            onClick={() => fetchData(localStorage.getItem('token'))}
            style={{
              padding: '10px 20px',
              backgroundColor: '#1976d2',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer'
            }}
          >
            Refresh Data
          </button>
        </>
      )}
    </div>
  );
};

export default SimpleApp;

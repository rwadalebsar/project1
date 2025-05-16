import React from 'react';

const TestApp = () => {
  return (
    <div style={{ padding: '20px', maxWidth: '800px', margin: '0 auto' }}>
      <h1>Test Page</h1>
      <p>If you can see this, React is working correctly!</p>
      
      <div style={{ marginTop: '20px', padding: '20px', border: '1px solid #ccc', borderRadius: '5px' }}>
        <h2>Debug Information</h2>
        <p>Check if authentication data exists in localStorage:</p>
        <pre id="auth-data">Loading...</pre>
        
        <button 
          style={{ 
            marginTop: '10px', 
            padding: '8px 16px', 
            backgroundColor: '#1976d2', 
            color: 'white', 
            border: 'none', 
            borderRadius: '4px',
            cursor: 'pointer'
          }}
          onClick={() => {
            const token = localStorage.getItem('token');
            const user = localStorage.getItem('user');
            
            document.getElementById('auth-data').textContent = JSON.stringify({
              token: token ? 'exists' : 'missing',
              user: user ? JSON.parse(user) : 'missing'
            }, null, 2);
          }}
        >
          Check Auth Data
        </button>
        
        <button 
          style={{ 
            marginTop: '10px',
            marginLeft: '10px', 
            padding: '8px 16px', 
            backgroundColor: '#f44336', 
            color: 'white', 
            border: 'none', 
            borderRadius: '4px',
            cursor: 'pointer'
          }}
          onClick={() => {
            localStorage.removeItem('token');
            localStorage.removeItem('user');
            document.getElementById('auth-data').textContent = 'Auth data cleared';
          }}
        >
          Clear Auth Data
        </button>
        
        <button 
          style={{ 
            marginTop: '10px',
            marginLeft: '10px', 
            padding: '8px 16px', 
            backgroundColor: '#4caf50', 
            color: 'white', 
            border: 'none', 
            borderRadius: '4px',
            cursor: 'pointer'
          }}
          onClick={() => {
            window.location.href = '/standalone-login.html';
          }}
        >
          Go to Login
        </button>
      </div>
    </div>
  );
};

export default TestApp;

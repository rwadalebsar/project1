import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

const Login = () => {
  const navigate = useNavigate();

  // Redirect to standalone login page
  useEffect(() => {
    window.location.href = '/standalone-login.html';
  }, []);

  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
      <div style={{ textAlign: 'center' }}>
        <h1>Redirecting to login page...</h1>
        <p>If you are not redirected automatically, <a href="/standalone-login.html">click here</a>.</p>
      </div>
    </div>
  );
};

export default Login;

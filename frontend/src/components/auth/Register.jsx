import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

const Register = () => {
  const navigate = useNavigate();

  // Redirect to standalone registration page
  useEffect(() => {
    window.location.href = '/standalone-register.html';
  }, []);

  // Simple render function to show a loading message while redirecting

  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
      <div style={{ textAlign: 'center' }}>
        <h1>Redirecting to registration page...</h1>
        <p>If you are not redirected automatically, <a href="/standalone-register.html">click here</a>.</p>
      </div>
    </div>
  );
};

export default Register;

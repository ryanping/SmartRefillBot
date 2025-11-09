import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import LoginPageBase, { Logo, Title, Username, Password, Footer, Input} from '@react-login-page/base';
import './LoginPage.css';

function LoginPage() {
  const navigate = useNavigate();
  const [error, setError] = useState('');

  const handleLogin = async ({ email, password }) => {
    setError(''); // Clear previous errors
    try {
      const response = await fetch('http://127.0.0.1:5000/api/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
      });

      if (response.ok) {
        console.log('Login successful');
        navigate('/dashboard');
      } else {
        const errorData = await response.json();
        setError(errorData.error || 'Login failed. Please try again.');
      }
    } catch (err) {
      setError('Network error. Could not connect to the server.');
    }
  };

  return (
    <LoginPageBase onLogin={handleLogin}>
      <Logo>👨‍⚕️</Logo>
      <Title>
        Smart Refiller Login
      </Title>
      <Username name="email" placeholder="Email" />
      <Password name="password" placeholder="Password" />
      {error && <div className="login-error">{error}</div>}
      <a href="#" onClick={(event) => event.preventDefault()}>
          Forgot Password?
        </a>
    </LoginPageBase>
  );
}

export default LoginPage;

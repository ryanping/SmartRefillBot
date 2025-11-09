import React from 'react';
import { useNavigate } from 'react-router-dom';
import LoginPageBase, { Logo, Title, Username, Footer, Input} from '@react-login-page/base';
import './LoginPage.css';

function LoginPage() {
  const navigate = useNavigate();

  const handleLogin = ({ email, password }) => {
    // In a real app, you'd have authentication logic here.
    // For now, we'll just navigate to the dashboard on submit.
    console.log('Logging in with:', email, password);
    navigate('/dashboard');
  };

  return (
    <LoginPageBase onLogin={handleLogin}>
      <Logo>👨‍⚕️</Logo>
      <Title>
        Smart Refiller Login
      </Title>
      <Username name="email" placeholder="Email" />
    </LoginPageBase>
  );
}

export default LoginPage;

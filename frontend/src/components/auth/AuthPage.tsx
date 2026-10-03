import React from 'react';
import { AuthForm } from './AuthForm';
import { AuthHeroShowcase } from './AuthHeroShowcase';
import type { User } from '../../services/api';
import './auth.css';

interface AuthPageProps {
  onAuthSuccess: (user: User) => void;
}

export const AuthPage: React.FC<AuthPageProps> = ({ onAuthSuccess }) => {
  return (
    <div className="auth-viewport">
      <div className="auth-master-card">
        {/* Left: Crisp Pure-White Form */}
        <AuthForm onAuthSuccess={onAuthSuccess} />

        {/* Right: Royal Blue Gradient AI Feature Showcase */}
        <AuthHeroShowcase mode="signin" />
      </div>
    </div>
  );
};

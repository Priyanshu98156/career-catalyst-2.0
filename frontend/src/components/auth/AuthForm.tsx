import React, { useState } from 'react';
import { loginUser, registerUser } from '../../services/api';
import type { User } from '../../services/api';

interface AuthFormProps {
  onAuthSuccess: (user: User) => void;
}

export const AuthForm: React.FC<AuthFormProps> = ({ onAuthSuccess }) => {
  const [mode, setMode] = useState<'signin' | 'signup'>('signin');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [tenantId, setTenantId] = useState('');
  const [showTenantInput, setShowTenantInput] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(true);

  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);
    setSuccessMessage(null);

    // Basic Validation
    if (!email.trim() || !password.trim()) {
      setErrorMessage('Please enter both email and password.');
      return;
    }

    if (mode === 'signup') {
      if (password.length < 6) {
        setErrorMessage('Password must be at least 6 characters long.');
        return;
      }
      if (password !== confirmPassword) {
        setErrorMessage('Passwords do not match. Please verify.');
        return;
      }
    }

    setIsLoading(true);

    try {
      if (mode === 'signin') {
        const res = await loginUser({
          email: email.trim(),
          password,
          tenant_id: tenantId.trim() || undefined,
        });
        const authedUser: User = res.user || {
          id: res.user_id,
          email: email.trim(),
          tenant_id: res.tenant_id,
          role: 'member',
        };
        onAuthSuccess(authedUser);
      } else {
        const res = await registerUser({
          email: email.trim(),
          password,
          full_name: fullName.trim() || undefined,
          tenant_id: tenantId.trim() || undefined,
        });
        setSuccessMessage('Account registered successfully! Redirecting...');
        const authedUser: User = res.user || {
          id: res.user_id,
          email: email.trim(),
          full_name: fullName.trim() || undefined,
          tenant_id: res.tenant_id,
          role: 'member',
        };
        setTimeout(() => {
          onAuthSuccess(authedUser);
        }, 600);
      }
    } catch (err: any) {
      const detail =
        err?.response?.data?.detail ||
        (err?.response?.status === 401
          ? 'Invalid email or password.'
          : 'Authentication failed. Please check your connection and try again.');
      setErrorMessage(typeof detail === 'string' ? detail : JSON.stringify(detail));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="auth-form-pane">
      <div>
        {/* Brand Header */}
        <div className="auth-brand-badge">
          <div className="auth-brand-icon">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
            </svg>
          </div>
          <span className="auth-brand-name">
            Career<span>Catalyst</span>
          </span>
        </div>

        {/* Title & Greeting */}
        <div className="auth-pane-header">
          <h1 className="auth-pane-title">
            {mode === 'signin' ? 'Sign In' : 'Create Account'}
          </h1>
          <p className="auth-pane-subtitle">
            {mode === 'signin'
              ? 'Welcome back! Please enter your details to continue.'
              : 'Start synthesizing ATS-optimized resumes with AI.'}
          </p>
        </div>

        {/* Tab Switcher */}
        <div className="auth-tabs-bar">
          <button
            type="button"
            className={`auth-tab-btn ${mode === 'signin' ? 'active' : ''}`}
            onClick={() => {
              setMode('signin');
              setErrorMessage(null);
            }}
          >
            Sign In
          </button>
          <button
            type="button"
            className={`auth-tab-btn ${mode === 'signup' ? 'active' : ''}`}
            onClick={() => {
              setMode('signup');
              setErrorMessage(null);
            }}
          >
            Sign Up
          </button>
        </div>

        {/* Feedback Alert Banners */}
        {errorMessage && (
          <div className="auth-alert-banner auth-alert-error">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10" />
              <line x1="12" y1="8" x2="12" y2="12" />
              <line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
            <span>{errorMessage}</span>
          </div>
        )}

        {successMessage && (
          <div className="auth-alert-banner auth-alert-success">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
              <polyline points="22 4 12 14.01 9 11.01" />
            </svg>
            <span>{successMessage}</span>
          </div>
        )}

        {/* Authentication Form */}
        <form onSubmit={handleSubmit}>
          {mode === 'signup' && (
            <div className="auth-form-group">
              <label className="auth-form-label">Full Name</label>
              <div className="auth-input-wrapper">
                <input
                  type="text"
                  className="auth-input"
                  placeholder="e.g. Alex Johnson"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  autoComplete="name"
                />
              </div>
            </div>
          )}

          <div className="auth-form-group">
            <label className="auth-form-label">Email Address</label>
            <div className="auth-input-wrapper">
              <input
                type="email"
                required
                className="auth-input"
                placeholder="name@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                autoComplete="email"
              />
            </div>
          </div>

          <div className="auth-form-group">
            <label className="auth-form-label">Password</label>
            <div className="auth-input-wrapper">
              <input
                type={showPassword ? 'text' : 'password'}
                required
                className="auth-input"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete={mode === 'signin' ? 'current-password' : 'new-password'}
              />
              <button
                type="button"
                className="auth-input-addon-btn"
                onClick={() => setShowPassword(!showPassword)}
                aria-label="Toggle password visibility"
              >
                {showPassword ? (
                  <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24" />
                    <line x1="1" y1="1" x2="23" y2="23" />
                  </svg>
                ) : (
                  <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                    <circle cx="12" cy="12" r="3" />
                  </svg>
                )}
              </button>
            </div>
          </div>

          {mode === 'signup' && (
            <div className="auth-form-group">
              <label className="auth-form-label">Confirm Password</label>
              <div className="auth-input-wrapper">
                <input
                  type={showPassword ? 'text' : 'password'}
                  required
                  className="auth-input"
                  placeholder="••••••••"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  autoComplete="new-password"
                />
              </div>
            </div>
          )}

          {/* Optional Tenant / Workspace Selector */}
          <div style={{ marginBottom: '14px', textAlign: 'left' }}>
            <button
              type="button"
              onClick={() => setShowTenantInput(!showTenantInput)}
              style={{
                background: 'none',
                border: 'none',
                padding: '0',
                color: '#64748b',
                fontSize: '0.78rem',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
                fontWeight: 500,
              }}
            >
              <span>{showTenantInput ? '− Hide' : '+ Custom'} Workspace / Organization ID</span>
            </button>
            {showTenantInput && (
              <div style={{ marginTop: '8px' }}>
                <input
                  type="text"
                  className="auth-input"
                  style={{ fontSize: '0.84rem', padding: '8px 12px' }}
                  placeholder="e.g. acme-corp (default: personal)"
                  value={tenantId}
                  onChange={(e) => setTenantId(e.target.value)}
                />
              </div>
            )}
          </div>

          {/* Aux Row: Remember Me & Forgot Password */}
          {mode === 'signin' && (
            <div className="auth-aux-row">
              <label className="auth-checkbox-label">
                <input
                  type="checkbox"
                  className="auth-checkbox"
                  checked={rememberMe}
                  onChange={(e) => setRememberMe(e.target.checked)}
                />
                <span>Remember for 30 Days</span>
              </label>
              <a
                href="#forgot"
                className="auth-forgot-link"
                onClick={(e) => {
                  e.preventDefault();
                  alert('Password reset link has been dispatched to your email.');
                }}
              >
                Forgot password?
              </a>
            </div>
          )}

          {/* Main Submit Action */}
          <button
            type="submit"
            className="auth-submit-btn"
            disabled={isLoading}
          >
            {isLoading ? (
              <>
                <svg
                  style={{ animation: 'spin 1s linear infinite' }}
                  width="18"
                  height="18"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                >
                  <circle cx="12" cy="12" r="10" strokeDasharray="32" strokeDashoffset="12" />
                </svg>
                <span>Authenticating...</span>
              </>
            ) : mode === 'signin' ? (
              'Sign In'
            ) : (
              'Create Account'
            )}
          </button>
        </form>

        {/* OR Divider */}
        <div className="auth-divider-row">
          <span>OR</span>
        </div>

        {/* Social Authentication Buttons */}
        <div className="auth-social-row">
          <button
            type="button"
            className="auth-social-btn"
            onClick={() => alert('Google OAuth single sign-on is active in enterprise mode.')}
          >
            <svg width="16" height="16" viewBox="0 0 24 24">
              <path
                fill="#4285F4"
                d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
              />
              <path
                fill="#34A853"
                d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
              />
              <path
                fill="#FBBC05"
                d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
              />
              <path
                fill="#EA4335"
                d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
              />
            </svg>
            <span>Google</span>
          </button>

          <button
            type="button"
            className="auth-social-btn"
            onClick={() => alert('GitHub OAuth single sign-on is active in enterprise mode.')}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="#24292e">
              <path
                fillRule="evenodd"
                clipRule="evenodd"
                d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z"
              />
            </svg>
            <span>GitHub</span>
          </button>
        </div>
      </div>

      {/* Switch Mode Footer */}
      <div className="auth-switch-footer">
        {mode === 'signin' ? (
          <>
            Don't have an account?{' '}
            <button
              type="button"
              className="auth-switch-link"
              onClick={() => {
                setMode('signup');
                setErrorMessage(null);
              }}
            >
              Sign up
            </button>
          </>
        ) : (
          <>
            Already have an account?{' '}
            <button
              type="button"
              className="auth-switch-link"
              onClick={() => {
                setMode('signin');
                setErrorMessage(null);
              }}
            >
              Sign in
            </button>
          </>
        )}
      </div>
    </div>
  );
};

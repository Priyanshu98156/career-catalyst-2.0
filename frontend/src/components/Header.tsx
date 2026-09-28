import React from 'react';

interface HeaderProps {
  activeTab: 'profile' | 'studio' | 'history';
  setActiveTab: (tab: 'profile' | 'studio' | 'history') => void;
  apiHealthy: boolean;
}

export const Header: React.FC<HeaderProps> = ({ activeTab, setActiveTab, apiHealthy }) => {
  return (
    <header style={{
      borderBottom: '1px solid var(--border-subtle)',
      backgroundColor: 'rgba(7, 9, 14, 0.85)',
      backdropFilter: 'blur(16px)',
      position: 'sticky',
      top: 0,
      zIndex: 50,
      padding: '14px 28px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
    }}>
      {/* Brand & Logo */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
        <div style={{
          width: '38px',
          height: '38px',
          borderRadius: '10px',
          background: 'var(--grad-primary)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: 'var(--shadow-glow)',
        }}>
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
          </svg>
        </div>
        <div>
          <h1 style={{ fontSize: '1.25rem', fontWeight: 800, background: 'var(--grad-primary)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
            CareerCatalyst
          </h1>
          <p style={{ fontSize: '0.72rem', color: 'var(--text-muted)', letterSpacing: '0.04em', textTransform: 'uppercase' }}>
            Multi-Tenant AI Resume Studio
          </p>
        </div>
      </div>

      {/* Navigation Tabs */}
      <nav style={{ display: 'flex', gap: '6px', background: 'var(--bg-secondary)', padding: '5px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
        <button
          className={`btn ${activeTab === 'profile' ? 'btn-primary' : 'btn-secondary'}`}
          style={{ fontSize: '0.82rem', padding: '7px 14px', borderRadius: '8px' }}
          onClick={() => setActiveTab('profile')}
        >
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
          Profile & Vault
        </button>
        <button
          className={`btn ${activeTab === 'studio' ? 'btn-primary' : 'btn-secondary'}`}
          style={{ fontSize: '0.82rem', padding: '7px 14px', borderRadius: '8px' }}
          onClick={() => setActiveTab('studio')}
        >
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><path d="m10 15 5-3-5-3v6Z"/></svg>
          JD Studio & Tailoring
        </button>
        <button
          className={`btn ${activeTab === 'history' ? 'btn-primary' : 'btn-secondary'}`}
          style={{ fontSize: '0.82rem', padding: '7px 14px', borderRadius: '8px' }}
          onClick={() => setActiveTab('history')}
        >
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/><path d="M12 7v5l4 2"/></svg>
          Resume History
        </button>
      </nav>

      {/* Tenant Status Badges */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <span className="badge badge-indigo">
          Tenant: default_tenant
        </span>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
          fontSize: '0.78rem',
          color: apiHealthy ? '#10b981' : '#f43f5e',
          background: apiHealthy ? 'rgba(16, 185, 129, 0.1)' : 'rgba(244, 63, 94, 0.1)',
          padding: '4px 10px',
          borderRadius: '9999px',
          border: `1px solid ${apiHealthy ? 'rgba(16, 185, 129, 0.3)' : 'rgba(244, 63, 94, 0.3)'}`,
        }}>
          <span style={{
            width: '7px',
            height: '7px',
            borderRadius: '50%',
            backgroundColor: apiHealthy ? '#10b981' : '#f43f5e',
          }} />
          {apiHealthy ? 'API Active' : 'API Connecting'}
        </div>
      </div>
    </header>
  );
};

import { useState, useEffect, useCallback } from 'react';
import { Header } from './components/Header';
import { ProfileVaultView } from './components/ProfileVaultView';
import { JDTailoringView } from './components/JDTailoringView';
import { HistoryView } from './components/HistoryView';
import { AuthPage } from './components/auth/AuthPage';
import { apiClient, fetchCurrentUser, logoutUser, tokenStorage } from './services/api';
import type { User } from './services/api';

export function App() {
  const [activeTab, setActiveTab] = useState<'profile' | 'studio' | 'history'>('studio');
  const [apiHealthy, setApiHealthy] = useState(false);
  const [currentUser, setCurrentUser] = useState<User | null>(tokenStorage.getUser());
  const [isInitializing, setIsInitializing] = useState(true);
  const [viewKey, setViewKey] = useState(0); // Trigger view refresh when tenant/user changes

  const checkHealth = useCallback(async () => {
    try {
      const res = await apiClient.get('/api/health');
      if (res.data?.status === 'active') {
        setApiHealthy(true);
      }
    } catch {
      setApiHealthy(false);
    }
  }, []);

  const loadSession = useCallback(async () => {
    if (tokenStorage.getAccessToken()) {
      try {
        const user = await fetchCurrentUser();
        if (user) {
          setCurrentUser(user);
        } else {
          setCurrentUser(null);
        }
      } catch {
        setCurrentUser(null);
      }
    } else {
      setCurrentUser(null);
    }
    setIsInitializing(false);
  }, []);

  useEffect(() => {
    checkHealth();
    loadSession();

    const interval = setInterval(checkHealth, 15000);

    const handleLogoutEvent = () => {
      setCurrentUser(null);
      setViewKey((prev) => prev + 1);
    };

    window.addEventListener('cc_auth_logout', handleLogoutEvent);

    return () => {
      clearInterval(interval);
      window.removeEventListener('cc_auth_logout', handleLogoutEvent);
    };
  }, [checkHealth, loadSession]);

  const handleAuthSuccess = (user: User) => {
    setCurrentUser(user);
    setViewKey((prev) => prev + 1);
  };

  const handleLogout = async () => {
    await logoutUser();
    setCurrentUser(null);
    setViewKey((prev) => prev + 1);
  };

  // Initial session check spinner
  if (isInitializing && tokenStorage.getAccessToken()) {
    return (
      <div style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: '#07090e',
        color: '#94a3b8',
        fontSize: '0.9rem',
        gap: '12px',
      }}>
        <div style={{
          width: '24px',
          height: '24px',
          border: '3px solid rgba(59, 130, 246, 0.2)',
          borderTopColor: '#3b82f6',
          borderRadius: '50%',
          animation: 'spin 0.8s linear infinite',
        }} />
        <span>Restoring CareerCatalyst session...</span>
      </div>
    );
  }

  // 1. Unauthenticated Gateway: Render Dedicated Split-Screen Auth Landing Page
  if (!currentUser) {
    return <AuthPage onAuthSuccess={handleAuthSuccess} />;
  }

  // 2. Authenticated Dashboard: Render Full CareerCatalyst Studio
  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Header
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        apiHealthy={apiHealthy}
        currentUser={currentUser}
        onOpenAuth={() => {}}
        onLogout={handleLogout}
      />

      <main style={{ flex: 1, paddingBottom: '60px' }}>
        <div key={viewKey}>
          <div style={{ display: activeTab === 'profile' ? 'block' : 'none' }}>
            <ProfileVaultView />
          </div>
          <div style={{ display: activeTab === 'studio' ? 'block' : 'none' }}>
            <JDTailoringView />
          </div>
          <div style={{ display: activeTab === 'history' ? 'block' : 'none' }}>
            <HistoryView isActive={activeTab === 'history'} />
          </div>
        </div>
      </main>

      <footer
        className="no-print"
        style={{
          borderTop: '1px solid var(--border-subtle)',
          padding: '20px 28px',
          textAlign: 'center',
          fontSize: '0.8rem',
          color: 'var(--text-muted)',
          background: 'rgba(7, 9, 14, 0.9)',
        }}
      >
        CareerCatalyst v2.0 • Multi-Tenant RAG AI Resume SaaS • Powered by Google Gemini & pgvector
      </footer>
    </div>
  );
}

export default App;

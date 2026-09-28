import { useState, useEffect, useCallback } from 'react';
import { Header } from './components/Header';
import { ProfileVaultView } from './components/ProfileVaultView';
import { JDTailoringView } from './components/JDTailoringView';
import { HistoryView } from './components/HistoryView';
import { AuthModal } from './components/AuthModal';
import { apiClient, fetchCurrentUser, logoutUser, tokenStorage } from './services/api';
import type { User } from './services/api';

export function App() {
  const [activeTab, setActiveTab] = useState<'profile' | 'studio' | 'history'>('studio');
  const [apiHealthy, setApiHealthy] = useState(false);
  const [currentUser, setCurrentUser] = useState<User | null>(tokenStorage.getUser());
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const [viewKey, setViewKey] = useState(0); // Trigger view refresh when tenant changes

  const checkHealth = useCallback(async () => {
    try {
      const res = await apiClient.get('/health');
      if (res.data?.status === 'active') {
        setApiHealthy(true);
      }
    } catch {
      setApiHealthy(false);
    }
  }, []);

  const loadSession = useCallback(async () => {
    if (tokenStorage.getAccessToken()) {
      const user = await fetchCurrentUser();
      if (user) {
        setCurrentUser(user);
      } else {
        setCurrentUser(null);
      }
    }
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

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Header
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        apiHealthy={apiHealthy}
        currentUser={currentUser}
        onOpenAuth={() => setIsAuthModalOpen(true)}
        onLogout={handleLogout}
      />

      <main style={{ flex: 1, paddingBottom: '60px' }}>
        <div key={viewKey}>
          {activeTab === 'profile' && <ProfileVaultView />}
          {activeTab === 'studio' && <JDTailoringView />}
          {activeTab === 'history' && <HistoryView />}
        </div>
      </main>

      <AuthModal
        isOpen={isAuthModalOpen}
        onClose={() => setIsAuthModalOpen(false)}
        onAuthSuccess={handleAuthSuccess}
      />

      <footer className="no-print" style={{
        borderTop: '1px solid var(--border-subtle)',
        padding: '20px 28px',
        textAlign: 'center',
        fontSize: '0.8rem',
        color: 'var(--text-muted)',
        background: 'rgba(7, 9, 14, 0.9)',
      }}>
        CareerCatalyst v2.0 • Multi-Tenant RAG AI Resume SaaS • Powered by Google Gemini & pgvector
      </footer>
    </div>
  );
}

export default App;

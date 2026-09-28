import { useState, useEffect } from 'react';
import { Header } from './components/Header';
import { ProfileVaultView } from './components/ProfileVaultView';
import { JDTailoringView } from './components/JDTailoringView';
import { HistoryView } from './components/HistoryView';
import { apiClient } from './services/api';

export function App() {
  const [activeTab, setActiveTab] = useState<'profile' | 'studio' | 'history'>('studio');
  const [apiHealthy, setApiHealthy] = useState(false);

  useEffect(() => {
    checkHealth();
    const interval = setInterval(checkHealth, 15000);
    return () => clearInterval(interval);
  }, []);

  const checkHealth = async () => {
    try {
      const res = await apiClient.get('/health');
      if (res.data?.status === 'active') {
        setApiHealthy(true);
      }
    } catch {
      setApiHealthy(false);
    }
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Header
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        apiHealthy={apiHealthy}
      />

      <main style={{ flex: 1, paddingBottom: '60px' }}>
        {activeTab === 'profile' && <ProfileVaultView />}
        {activeTab === 'studio' && <JDTailoringView />}
        {activeTab === 'history' && <HistoryView />}
      </main>

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

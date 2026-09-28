import React, { useState, useEffect } from 'react';
import type { ResumeHistoryItem } from '../services/api';
import { fetchResumeHistory } from '../services/api';

export const HistoryView: React.FC = () => {
  const [history, setHistory] = useState<ResumeHistoryItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  useEffect(() => {
    loadHistory();
  }, []);

  const loadHistory = async () => {
    setIsLoading(true);
    try {
      const items = await fetchResumeHistory();
      setHistory(items);
    } catch (err) {
      console.error('Failed to load history:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCopyLatex = (id: string, latex?: string) => {
    if (!latex) return;
    navigator.clipboard.writeText(latex);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <div>
          <h2 style={{ fontSize: '1.4rem' }}>Tailored Resumes History</h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.86rem' }}>
            All resumes previously generated through the multi-tenant RAG pipeline
          </p>
        </div>
        <button className="btn btn-secondary" onClick={loadHistory} disabled={isLoading} style={{ fontSize: '0.82rem' }}>
          {isLoading ? 'Refreshing...' : '↻ Refresh History'}
        </button>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        {history.map((item) => (
          <div key={item.id} className="glass-panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '10px' }}>
              <div>
                <h3 style={{ fontSize: '1.1rem', color: '#fff' }}>{item.title}</h3>
                <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                  Created on: {new Date(item.created_at).toLocaleDateString()} at {new Date(item.created_at).toLocaleTimeString()}
                </span>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                {item.match_score && (
                  <span className="badge badge-emerald" style={{ fontSize: '0.78rem' }}>
                    ATS Match: {item.match_score}%
                  </span>
                )}
                <button
                  className="btn btn-secondary"
                  style={{ fontSize: '0.78rem', padding: '6px 12px' }}
                  onClick={() => handleCopyLatex(item.id, item.raw_latex)}
                >
                  {copiedId === item.id ? '✓ Copied LaTeX!' : 'Copy LaTeX'}
                </button>
              </div>
            </div>

            {/* Candidate & Summary excerpt */}
            {item.structured_content?.professional_summary && (
              <p style={{ fontSize: '0.86rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                {item.structured_content.professional_summary}
              </p>
            )}

            {/* Skills preview */}
            {item.structured_content?.highlighted_skills && (
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                {item.structured_content.highlighted_skills.slice(0, 8).map((skill, sIdx) => (
                  <span key={sIdx} className="badge badge-cyan" style={{ fontSize: '0.7rem' }}>
                    {skill}
                  </span>
                ))}
              </div>
            )}
          </div>
        ))}

        {history.length === 0 && !isLoading && (
          <div style={{ textAlign: 'center', padding: '64px', color: 'var(--text-muted)' }} className="glass-panel">
            <svg width="42" height="42" viewBox="0 0 24 24" fill="none" stroke="#475569" strokeWidth="1.5" style={{ marginBottom: '10px' }}>
              <circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>
            </svg>
            <p>No tailored resumes saved in history yet.</p>
            <span style={{ fontSize: '0.8rem' }}>Go to the JD Studio tab and generate your first tailored resume!</span>
          </div>
        )}
      </div>
    </div>
  );
};

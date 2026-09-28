import React, { useState, useEffect } from 'react';
import type { ParsedProfile, MasterBullet } from '../services/api';
import {
  uploadResumePdf,
  fetchProfile,
  saveProfile,
  fetchMasterBullets,
  addMasterBullets,
} from '../services/api';

export const ProfileVaultView: React.FC = () => {
  const [profile, setProfile] = useState<ParsedProfile | null>(null);
  const [bullets, setBullets] = useState<MasterBullet[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [statusMessage, setStatusMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // New bullet input state
  const [newBulletText, setNewBulletText] = useState('');
  const [newBulletCategory, setNewBulletCategory] = useState('Work Experience');
  const [newBulletSkills, setNewBulletSkills] = useState('');
  const [newBulletMetrics, setNewBulletMetrics] = useState('');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [profData, bulletsData] = await Promise.all([
        fetchProfile(),
        fetchMasterBullets(),
      ]);
      if (profData) setProfile(profData);
      if (bulletsData) setBullets(bulletsData);
    } catch (err: any) {
      console.error('Error loading profile data:', err);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.name.toLowerCase().endsWith('.pdf')) {
      setStatusMessage({ type: 'error', text: 'Please upload a PDF document.' });
      return;
    }

    setIsUploading(true);
    setStatusMessage(null);

    try {
      const parsed = await uploadResumePdf(file, true);
      setProfile(parsed);
      const updatedBullets = await fetchMasterBullets();
      setBullets(updatedBullets);
      setStatusMessage({
        type: 'success',
        text: `Successfully parsed and ingested resume for ${parsed.full_name}! Extracted ${parsed.skills.length} skills and ${parsed.experiences.length} experience roles.`,
      });
    } catch (err: any) {
      console.error('Upload failed:', err);
      setStatusMessage({
        type: 'error',
        text: err.response?.data?.detail || 'Failed to parse resume document. Please check the backend connection.',
      });
    } finally {
      setIsUploading(false);
    }
  };

  const handleAddBullet = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newBulletText.trim()) return;

    const skillsArray = newBulletSkills
      .split(',')
      .map((s) => s.trim())
      .filter(Boolean);

    const newBullet: MasterBullet = {
      bullet_text: newBulletText.trim(),
      category: newBulletCategory,
      skills_used: skillsArray,
      impact_metrics: newBulletMetrics.trim() || undefined,
    };

    try {
      const created = await addMasterBullets([newBullet]);
      setBullets((prev) => [...created, ...prev]);
      setNewBulletText('');
      setNewBulletSkills('');
      setNewBulletMetrics('');
      setStatusMessage({ type: 'success', text: 'Master bullet embedded into pgvector knowledge vault!' });
    } catch (err: any) {
      setStatusMessage({ type: 'error', text: 'Failed to add master bullet.' });
    }
  };

  const handleSaveProfile = async () => {
    if (!profile) return;
    setIsSaving(true);
    try {
      await saveProfile(profile);
      setStatusMessage({ type: 'success', text: 'Profile changes saved successfully!' });
    } catch (err) {
      setStatusMessage({ type: 'error', text: 'Failed to update profile.' });
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '24px', display: 'flex', flexDirection: 'column', gap: '28px' }}>
      {/* Status banner */}
      {statusMessage && (
        <div style={{
          padding: '12px 18px',
          borderRadius: 'var(--radius-md)',
          background: statusMessage.type === 'success' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(244, 63, 94, 0.15)',
          border: `1px solid ${statusMessage.type === 'success' ? 'rgba(16, 185, 129, 0.3)' : 'rgba(244, 63, 94, 0.3)'}`,
          color: statusMessage.type === 'success' ? '#10b981' : '#f43f5e',
          fontSize: '0.9rem',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}>
          <span>{statusMessage.text}</span>
          <button style={{ background: 'none', border: 'none', color: 'inherit', cursor: 'pointer', fontSize: '1rem' }} onClick={() => setStatusMessage(null)}>✕</button>
        </div>
      )}

      {/* Top Row: Resume Ingestion Card & Master Stats */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '24px' }}>
        {/* Upload Card */}
        <div className="glass-panel" style={{ padding: '24px', position: 'relative', overflow: 'hidden' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '14px' }}>
            <span className="badge badge-cyan">Ingestion Engine</span>
            <h3 style={{ fontSize: '1.15rem' }}>Upload Resume (PDF)</h3>
          </div>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.86rem', marginBottom: '18px' }}>
            Upload your existing PDF resume. Gemini extracts personal info, career history, education, and synchronizes achievements into the pgvector knowledge vault.
          </p>

          <label style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '28px 16px',
            border: '2px dashed var(--border-subtle)',
            borderRadius: 'var(--radius-md)',
            background: 'rgba(15, 23, 42, 0.4)',
            cursor: isUploading ? 'not-allowed' : 'pointer',
            transition: 'border-color 0.2s, background 0.2s',
          }}>
            <input
              type="file"
              accept=".pdf"
              style={{ display: 'none' }}
              onChange={handleFileUpload}
              disabled={isUploading}
            />
            {isUploading ? (
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '10px' }}>
                <div className="spinner" style={{ width: '28px', height: '28px', border: '3px solid rgba(56, 189, 248, 0.2)', borderTopColor: '#38bdf8', borderRadius: '50%' }} />
                <span style={{ fontSize: '0.85rem', color: '#38bdf8', fontWeight: 600 }}>Analyzing & Ingesting via Gemini...</span>
              </div>
            ) : (
              <>
                <svg width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="#38bdf8" strokeWidth="1.8" style={{ marginBottom: '10px' }}>
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/>
                </svg>
                <span style={{ fontWeight: 600, color: 'var(--text-primary)', fontSize: '0.92rem' }}>
                  Click or drag PDF resume here
                </span>
                <span style={{ color: 'var(--text-muted)', fontSize: '0.78rem', marginTop: '4px' }}>
                  Automated parsing + pgvector multi-tenant embedding
                </span>
              </>
            )}
          </label>
        </div>

        {/* Knowledge Vault Metrics */}
        <div className="glass-panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '14px' }}>
              <span className="badge badge-emerald">Master Vault</span>
              <h3 style={{ fontSize: '1.15rem' }}>Knowledge Vault Stats</h3>
            </div>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.86rem', marginBottom: '20px' }}>
              Granular bullet points stored with rich skill metadata for semantic RAG retrieval against target JDs.
            </p>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '14px' }}>
              <div style={{ background: 'var(--bg-secondary)', padding: '14px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)', textAlign: 'center' }}>
                <div style={{ fontSize: '1.8rem', fontWeight: 800, color: '#38bdf8' }}>{bullets.length}</div>
                <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Master Bullets</div>
              </div>
              <div style={{ background: 'var(--bg-secondary)', padding: '14px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)', textAlign: 'center' }}>
                <div style={{ fontSize: '1.8rem', fontWeight: 800, color: '#10b981' }}>{profile?.skills?.length || 0}</div>
                <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Skills Tagged</div>
              </div>
              <div style={{ background: 'var(--bg-secondary)', padding: '14px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)', textAlign: 'center' }}>
                <div style={{ fontSize: '1.8rem', fontWeight: 800, color: '#818cf8' }}>{profile?.experiences?.length || 0}</div>
                <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Past Roles</div>
              </div>
            </div>
          </div>

          <div style={{ marginTop: '18px', display: 'flex', justifyContent: 'flex-end' }}>
            <button className="btn btn-secondary" onClick={loadData} style={{ fontSize: '0.8rem' }}>
              ↻ Refresh Vault Data
            </button>
          </div>
        </div>
      </div>

      {/* Profile Details & Skills Form */}
      {profile && (
        <div className="glass-panel" style={{ padding: '28px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
            <div>
              <h3 style={{ fontSize: '1.3rem' }}>Candidate Profile Overview</h3>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>Personal details and base competencies</p>
            </div>
            <button className="btn btn-primary" onClick={handleSaveProfile} disabled={isSaving}>
              {isSaving ? 'Saving...' : 'Save Profile Changes'}
            </button>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '16px', marginBottom: '20px' }}>
            <div>
              <label style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '6px', display: 'block' }}>Full Name</label>
              <input
                className="input-field"
                value={profile.full_name || ''}
                onChange={(e) => setProfile({ ...profile, full_name: e.target.value })}
              />
            </div>
            <div>
              <label style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '6px', display: 'block' }}>Email Address</label>
              <input
                className="input-field"
                value={profile.email || ''}
                onChange={(e) => setProfile({ ...profile, email: e.target.value })}
              />
            </div>
            <div>
              <label style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '6px', display: 'block' }}>Phone Number</label>
              <input
                className="input-field"
                value={profile.phone || ''}
                onChange={(e) => setProfile({ ...profile, phone: e.target.value })}
              />
            </div>
            <div>
              <label style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '6px', display: 'block' }}>Location</label>
              <input
                className="input-field"
                value={profile.location || ''}
                onChange={(e) => setProfile({ ...profile, location: e.target.value })}
              />
            </div>
          </div>

          {/* Professional Summary */}
          <div style={{ marginBottom: '22px' }}>
            <label style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '6px', display: 'block' }}>Professional Summary</label>
            <textarea
              className="input-field"
              rows={3}
              value={profile.summary || ''}
              onChange={(e) => setProfile({ ...profile, summary: e.target.value })}
            />
          </div>

          {/* Skills Chips */}
          <div>
            <label style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '8px', display: 'block' }}>Master Skills Pool</label>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginBottom: '12px' }}>
              {profile.skills?.map((skill, idx) => (
                <span key={idx} className="badge badge-cyan" style={{ fontSize: '0.8rem', padding: '6px 12px' }}>
                  {skill}
                  <button
                    style={{ background: 'none', border: 'none', color: 'inherit', cursor: 'pointer', marginLeft: '4px' }}
                    onClick={() => {
                      const updated = profile.skills.filter((_, i) => i !== idx);
                      setProfile({ ...profile, skills: updated });
                    }}
                  >
                    ×
                  </button>
                </span>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Master Bullets Knowledge Vault Section */}
      <div className="glass-panel" style={{ padding: '28px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '18px' }}>
          <div>
            <h3 style={{ fontSize: '1.25rem' }}>Master Bullets Knowledge Vault ({bullets.length})</h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
              Individual achievement statements embedded in pgvector for RAG similarity matching
            </p>
          </div>
        </div>

        {/* Add New Bullet Form */}
        <form onSubmit={handleAddBullet} style={{ background: 'var(--bg-secondary)', padding: '18px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)', marginBottom: '24px' }}>
          <h4 style={{ fontSize: '0.95rem', marginBottom: '12px', color: '#38bdf8' }}>+ Add New Master Bullet</h4>
          <div style={{ marginBottom: '12px' }}>
            <textarea
              className="input-field"
              rows={2}
              placeholder="e.g. Architected high-throughput message consumer in Go, reducing processing latency by 35% across 20M daily events."
              value={newBulletText}
              onChange={(e) => setNewBulletText(e.target.value)}
              required
            />
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '12px', marginBottom: '14px' }}>
            <div>
              <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Category</label>
              <select
                className="input-field"
                value={newBulletCategory}
                onChange={(e) => setNewBulletCategory(e.target.value)}
              >
                <option value="Work Experience">Work Experience</option>
                <option value="Project">Project</option>
                <option value="Leadership">Leadership</option>
                <option value="Technical">Technical</option>
              </select>
            </div>
            <div>
              <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Skills Used (comma-separated)</label>
              <input
                className="input-field"
                placeholder="Go, Kafka, Docker"
                value={newBulletSkills}
                onChange={(e) => setNewBulletSkills(e.target.value)}
              />
            </div>
            <div>
              <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Impact Metric</label>
              <input
                className="input-field"
                placeholder="35% latency reduction"
                value={newBulletMetrics}
                onChange={(e) => setNewBulletMetrics(e.target.value)}
              />
            </div>
          </div>
          <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
            <button type="submit" className="btn btn-primary" style={{ fontSize: '0.85rem' }}>
              Add & Embed Bullet
            </button>
          </div>
        </form>

        {/* Existing Bullets List */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {bullets.map((b, idx) => (
            <div
              key={idx}
              style={{
                background: 'rgba(15, 23, 42, 0.5)',
                padding: '14px 18px',
                borderRadius: 'var(--radius-md)',
                border: '1px solid var(--border-subtle)',
                display: 'flex',
                flexDirection: 'column',
                gap: '8px',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span className="badge badge-indigo" style={{ fontSize: '0.7rem' }}>{b.category}</span>
                {b.impact_metrics && (
                  <span className="badge badge-emerald" style={{ fontSize: '0.7rem' }}>Metric: {b.impact_metrics}</span>
                )}
              </div>
              <p style={{ fontSize: '0.92rem', color: 'var(--text-primary)', lineHeight: 1.5 }}>
                • {b.bullet_text}
              </p>
              {b.skills_used && b.skills_used.length > 0 && (
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginTop: '2px' }}>
                  {b.skills_used.map((skill, sIdx) => (
                    <span key={sIdx} style={{ fontSize: '0.72rem', background: 'rgba(56, 189, 248, 0.1)', color: '#38bdf8', padding: '2px 8px', borderRadius: '4px' }}>
                      {skill}
                    </span>
                  ))}
                </div>
              )}
            </div>
          ))}
          {bullets.length === 0 && (
            <div style={{ textAlign: 'center', padding: '36px', color: 'var(--text-muted)' }}>
              No master bullets in knowledge vault yet. Upload a resume above or add your first bullet!
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

import React, { useState } from 'react';
import type { JDAnalysis, TailoredResumeResponse } from '../services/api';
import {
  analyzeJobDescription,
  tailorResume,
} from '../services/api';

const SAMPLE_TECH_JD = `Role: Senior Backend / Platform Engineer
Company: CloudScale Technologies
Location: Remote (US)

About the Role:
We are looking for a Senior Platform Engineer to scale our distributed event-driven data streaming platform. You will design, build, and optimize high-throughput microservices capable of processing tens of millions of events per day.

Key Responsibilities:
- Architect, build, and maintain low-latency backend microservices using Go and Python.
- Own and optimize our Apache Kafka streaming architecture and PostgreSQL database storage layers.
- Implement robust observability, telemetry (OpenTelemetry, Prometheus, Grafana), and distributed tracing.
- Optimize API endpoints to maintain strict p99 latency SLA under 15ms.
- Collaborate with infrastructure and DevOps teams on Kubernetes, Docker, and CI/CD pipelines.

Requirements & Qualifications:
- 5+ years of production experience in backend software engineering.
- Deep expertise in Go (Golang), Python, FastAPI, or similar frameworks.
- Strong proficiency with event streaming architectures (Kafka, RabbitMQ, or AWS Kinesis).
- Solid foundation in relational databases (PostgreSQL, connection pooling, indexing, schema design).
- Experience containerizing applications with Docker and deploying to Kubernetes clusters.
- Passion for low-latency systems, clean architecture, and performance benchmarking.`;

export const JDTailoringView: React.FC = () => {
  const [jobDescription, setJobDescription] = useState(SAMPLE_TECH_JD);
  const [targetJobTitle, setTargetJobTitle] = useState('Senior Backend / Platform Engineer');
  const [topKBullets] = useState(8);

  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [jdAnalysis, setJdAnalysis] = useState<JDAnalysis | null>(null);

  const [isTailoring, setIsTailoring] = useState(false);
  const [tailoredResult, setTailoredResult] = useState<TailoredResumeResponse | null>(null);

  const [activeResumeView, setActiveResumeView] = useState<'visual' | 'latex'>('visual');
  const [copiedLatex, setCopiedLatex] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleAnalyzeJD = async () => {
    if (!jobDescription.trim()) return;
    setIsAnalyzing(true);
    setErrorMessage(null);
    try {
      const analysis = await analyzeJobDescription(jobDescription, targetJobTitle);
      setJdAnalysis(analysis);
      if (analysis.job_title && !targetJobTitle) {
        setTargetJobTitle(analysis.job_title);
      }
    } catch (err: any) {
      console.error('JD Analysis error:', err);
      setErrorMessage(err.response?.data?.detail || 'Failed to analyze Job Description.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleRunTailoring = async () => {
    if (!jobDescription.trim()) {
      setErrorMessage('Please provide a target Job Description.');
      return;
    }
    setIsTailoring(true);
    setErrorMessage(null);
    try {
      const result = await tailorResume(jobDescription, targetJobTitle, topKBullets);
      setTailoredResult(result);
    } catch (err: any) {
      console.error('Tailoring error:', err);
      setErrorMessage(err.response?.data?.detail || 'Failed to synthesize tailored resume. Please verify backend connection.');
    } finally {
      setIsTailoring(false);
    }
  };

  const handleCopyLatex = () => {
    if (!tailoredResult?.latex_source) return;
    navigator.clipboard.writeText(tailoredResult.latex_source);
    setCopiedLatex(true);
    setTimeout(() => setCopiedLatex(false), 2000);
  };

  const handlePrint = () => {
    window.print();
  };

  return (
    <div style={{ maxWidth: '1440px', margin: '0 auto', padding: '24px' }}>
      {errorMessage && (
        <div style={{
          padding: '12px 18px',
          borderRadius: 'var(--radius-md)',
          background: 'rgba(244, 63, 94, 0.15)',
          border: '1px solid rgba(244, 63, 94, 0.3)',
          color: '#f43f5e',
          fontSize: '0.9rem',
          marginBottom: '20px',
          display: 'flex',
          justifyContent: 'space-between',
        }}>
          <span>{errorMessage}</span>
          <button style={{ background: 'none', border: 'none', color: 'inherit', cursor: 'pointer' }} onClick={() => setErrorMessage(null)}>✕</button>
        </div>
      )}

      {/* Split-Screen Grid Layout */}
      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(380px, 1fr) minmax(460px, 1.4fr)', gap: '28px', alignItems: 'start' }}>
        
        {/* Left Column: Target JD & Requirements Studio */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '22px' }}>
          
          <div className="glass-panel" style={{ padding: '24px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span className="badge badge-cyan">Step 1</span>
                <h3 style={{ fontSize: '1.15rem' }}>Target Job Description</h3>
              </div>
              <button
                className="btn btn-secondary"
                style={{ fontSize: '0.75rem', padding: '5px 10px' }}
                onClick={() => setJobDescription(SAMPLE_TECH_JD)}
              >
                Load Sample Tech JD
              </button>
            </div>

            <div style={{ marginBottom: '14px' }}>
              <label style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', display: 'block', marginBottom: '4px' }}>
                Target Role / Job Title (optional override)
              </label>
              <input
                className="input-field"
                placeholder="e.g. Senior Backend / Platform Engineer"
                value={targetJobTitle}
                onChange={(e) => setTargetJobTitle(e.target.value)}
              />
            </div>

            <div style={{ marginBottom: '16px' }}>
              <label style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', display: 'block', marginBottom: '4px' }}>
                Job Description Text (Paste from LinkedIn, Indeed, etc.)
              </label>
              <textarea
                className="input-field"
                style={{ height: '240px', fontSize: '0.85rem' }}
                placeholder="Paste the full job description here..."
                value={jobDescription}
                onChange={(e) => setJobDescription(e.target.value)}
              />
            </div>

            <div style={{ display: 'flex', gap: '10px' }}>
              <button
                className="btn btn-secondary"
                style={{ flex: 1 }}
                onClick={handleAnalyzeJD}
                disabled={isAnalyzing || !jobDescription.trim()}
              >
                {isAnalyzing ? (
                  <>
                    <div className="spinner" style={{ width: '16px', height: '16px', border: '2px solid rgba(255,255,255,0.2)', borderTopColor: '#fff', borderRadius: '50%' }} />
                    Analyzing Requirements...
                  </>
                ) : (
                  'Analyze Keywords & Skills'
                )}
              </button>

              <button
                className="btn btn-primary"
                style={{ flex: 1.4 }}
                onClick={handleRunTailoring}
                disabled={isTailoring || !jobDescription.trim()}
              >
                {isTailoring ? (
                  <>
                    <div className="spinner" style={{ width: '16px', height: '16px', border: '2px solid rgba(255,255,255,0.2)', borderTopColor: '#fff', borderRadius: '50%' }} />
                    Running RAG Pipeline...
                  </>
                ) : (
                  '⚡ Tailor Resume (RAG)'
                )}
              </button>
            </div>
          </div>

          {/* JD Analysis Extracted Card */}
          {jdAnalysis && (
            <div className="glass-panel" style={{ padding: '22px', borderLeft: '4px solid #38bdf8' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
                <h4 style={{ fontSize: '1rem', color: '#fff' }}>Extracted Requirements Analysis</h4>
                {jdAnalysis.seniority_level && (
                  <span className="badge badge-indigo">{jdAnalysis.seniority_level}</span>
                )}
              </div>

              <div style={{ marginBottom: '14px' }}>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', display: 'block', marginBottom: '6px' }}>
                  Target Technical Skills
                </span>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                  {jdAnalysis.primary_skills.map((skill, idx) => (
                    <span key={idx} className="badge badge-cyan" style={{ fontSize: '0.72rem' }}>
                      {skill}
                    </span>
                  ))}
                </div>
              </div>

              <div style={{ marginBottom: '14px' }}>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', display: 'block', marginBottom: '6px' }}>
                  High-Value ATS Keywords
                </span>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                  {jdAnalysis.keywords_to_target.map((kw, idx) => (
                    <span key={idx} className="badge badge-emerald" style={{ fontSize: '0.72rem' }}>
                      {kw}
                    </span>
                  ))}
                </div>
              </div>

              <div>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', display: 'block', marginBottom: '6px' }}>
                  Core Responsibilities
                </span>
                <ul style={{ paddingLeft: '18px', color: 'var(--text-secondary)', fontSize: '0.82rem', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                  {jdAnalysis.core_responsibilities.slice(0, 4).map((resp, idx) => (
                    <li key={idx}>{resp}</li>
                  ))}
                </ul>
              </div>
            </div>
          )}
        </div>

        {/* Right Column: Tailored Resume Live Preview & ATS Scorecard */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          
          {/* ATS Scorecard Banner */}
          {tailoredResult && (
            <div className="glass-panel" style={{ padding: '20px', background: 'linear-gradient(135deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.85) 100%)' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <div style={{
                      width: '54px',
                      height: '54px',
                      borderRadius: '50%',
                      background: 'conic-gradient(#10b981 0% calc(var(--score) * 1%), rgba(255,255,255,0.1) 0% 100%)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      boxShadow: '0 0 15px rgba(16, 185, 129, 0.3)',
                      ['--score' as any]: tailoredResult.match_score || 85,
                    }}>
                      <div style={{
                        width: '42px',
                        height: '42px',
                        borderRadius: '50%',
                        background: 'var(--bg-primary)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: '0.88rem',
                        fontWeight: 800,
                        color: '#10b981',
                      }}>
                        {tailoredResult.match_score || 88}%
                      </div>
                    </div>

                    <div>
                      <h4 style={{ fontSize: '1.05rem', color: '#fff' }}>ATS Optimization Score</h4>
                      <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                        Retrieved real master bullets matched with target keywords
                      </p>
                    </div>
                  </div>
                </div>

                <div style={{ display: 'flex', gap: '8px' }}>
                  <button className="btn btn-secondary" style={{ fontSize: '0.8rem', padding: '6px 12px' }} onClick={handlePrint}>
                    🖨️ Print / Export PDF
                  </button>
                  <button
                    className="btn btn-primary"
                    style={{ fontSize: '0.8rem', padding: '6px 12px' }}
                    onClick={handleCopyLatex}
                  >
                    {copiedLatex ? '✓ Copied LaTeX!' : '📋 Copy LaTeX Code'}
                  </button>
                </div>
              </div>

              {/* Keyword match breakdown */}
              <div style={{ marginTop: '16px', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div style={{ background: 'rgba(16, 185, 129, 0.08)', padding: '10px 14px', borderRadius: 'var(--radius-sm)', border: '1px solid rgba(16, 185, 129, 0.2)' }}>
                  <span style={{ fontSize: '0.72rem', color: '#10b981', fontWeight: 700, textTransform: 'uppercase' }}>
                    Matched Keywords ({tailoredResult.matched_keywords.length})
                  </span>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px', marginTop: '6px' }}>
                    {tailoredResult.matched_keywords.slice(0, 6).map((kw, idx) => (
                      <span key={idx} style={{ fontSize: '0.7rem', background: 'rgba(16, 185, 129, 0.2)', color: '#a7f3d0', padding: '2px 6px', borderRadius: '4px' }}>
                        ✓ {kw}
                      </span>
                    ))}
                  </div>
                </div>

                <div style={{ background: 'rgba(245, 158, 11, 0.08)', padding: '10px 14px', borderRadius: 'var(--radius-sm)', border: '1px solid rgba(245, 158, 11, 0.2)' }}>
                  <span style={{ fontSize: '0.72rem', color: '#f59e0b', fontWeight: 700, textTransform: 'uppercase' }}>
                    Missing Keywords ({tailoredResult.missing_keywords.length})
                  </span>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px', marginTop: '6px' }}>
                    {tailoredResult.missing_keywords.slice(0, 6).map((kw, idx) => (
                      <span key={idx} style={{ fontSize: '0.7rem', background: 'rgba(245, 158, 11, 0.2)', color: '#fde68a', padding: '2px 6px', borderRadius: '4px' }}>
                        + {kw}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Resume Viewer Tabs */}
          <div className="glass-panel" style={{ padding: '24px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '18px', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '12px' }}>
              <div style={{ display: 'flex', gap: '8px' }}>
                <button
                  className={`btn ${activeResumeView === 'visual' ? 'btn-primary' : 'btn-secondary'}`}
                  style={{ fontSize: '0.8rem', padding: '6px 14px' }}
                  onClick={() => setActiveResumeView('visual')}
                >
                  Live Visual Resume Preview
                </button>
                <button
                  className={`btn ${activeResumeView === 'latex' ? 'btn-primary' : 'btn-secondary'}`}
                  style={{ fontSize: '0.8rem', padding: '6px 14px' }}
                  onClick={() => setActiveResumeView('latex')}
                >
                  LaTeX Source View
                </button>
              </div>

              {tailoredResult && (
                <span className="badge badge-emerald">Ready for ATS Application</span>
              )}
            </div>

            {/* Content view */}
            {tailoredResult ? (
              activeResumeView === 'visual' ? (
                /* ATS Clean Printable Resume Document */
                <div
                  className="print-resume-sheet"
                  style={{
                    background: '#ffffff',
                    color: '#0f172a',
                    padding: '36px 42px',
                    borderRadius: 'var(--radius-sm)',
                    boxShadow: 'var(--shadow-lg)',
                    fontFamily: 'Georgia, Cambria, "Times New Roman", serif',
                    lineHeight: 1.5,
                  }}
                >
                  {/* Candidate Header */}
                  <div style={{ textAlign: 'center', borderBottom: '1.5px solid #0f172a', paddingBottom: '12px', marginBottom: '16px' }}>
                    <h2 style={{ fontFamily: 'Georgia, serif', color: '#0f172a', fontSize: '1.75rem', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                      {tailoredResult.structured_resume.candidate_name}
                    </h2>
                    <div style={{ fontSize: '0.85rem', color: '#334155', marginTop: '4px', display: 'flex', justifyContent: 'center', flexWrap: 'wrap', gap: '14px' }}>
                      {tailoredResult.structured_resume.contact_info.email && (
                        <span>✉ {tailoredResult.structured_resume.contact_info.email}</span>
                      )}
                      {tailoredResult.structured_resume.contact_info.phone && (
                        <span>☎ {tailoredResult.structured_resume.contact_info.phone}</span>
                      )}
                      {tailoredResult.structured_resume.contact_info.location && (
                        <span>📍 {tailoredResult.structured_resume.contact_info.location}</span>
                      )}
                      {tailoredResult.structured_resume.contact_info.linkedin && (
                        <span>🔗 LinkedIn</span>
                      )}
                    </div>
                  </div>

                  {/* Professional Summary */}
                  {tailoredResult.structured_resume.professional_summary && (
                    <div style={{ marginBottom: '18px' }}>
                      <h4 style={{ color: '#0f172a', fontSize: '0.98rem', fontWeight: 700, textTransform: 'uppercase', borderBottom: '1px solid #cbd5e1', paddingBottom: '3px', marginBottom: '6px' }}>
                        Professional Summary
                      </h4>
                      <p style={{ fontSize: '0.88rem', color: '#1e293b', textAlign: 'justify' }}>
                        {tailoredResult.structured_resume.professional_summary}
                      </p>
                    </div>
                  )}

                  {/* Highlighted Skills */}
                  {tailoredResult.structured_resume.highlighted_skills && (
                    <div style={{ marginBottom: '18px' }}>
                      <h4 style={{ color: '#0f172a', fontSize: '0.98rem', fontWeight: 700, textTransform: 'uppercase', borderBottom: '1px solid #cbd5e1', paddingBottom: '3px', marginBottom: '6px' }}>
                        Core Competencies & Technical Skills
                      </h4>
                      <p style={{ fontSize: '0.88rem', color: '#1e293b' }}>
                        <strong>Technical Skills:</strong> {tailoredResult.structured_resume.highlighted_skills.join(' • ')}
                      </p>
                    </div>
                  )}

                  {/* Tailored Experience Section */}
                  {tailoredResult.structured_resume.experiences && tailoredResult.structured_resume.experiences.length > 0 && (
                    <div style={{ marginBottom: '18px' }}>
                      <h4 style={{ color: '#0f172a', fontSize: '0.98rem', fontWeight: 700, textTransform: 'uppercase', borderBottom: '1px solid #cbd5e1', paddingBottom: '3px', marginBottom: '8px' }}>
                        Professional Experience
                      </h4>
                      {tailoredResult.structured_resume.experiences.map((exp, idx) => (
                        <div key={idx} style={{ marginBottom: '14px' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
                            <strong style={{ fontSize: '0.95rem', color: '#0f172a' }}>{exp.role}</strong>
                            <span style={{ fontSize: '0.85rem', color: '#475569', fontStyle: 'italic' }}>{exp.duration || '2021 - Present'}</span>
                          </div>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: '4px' }}>
                            <span style={{ fontSize: '0.88rem', color: '#1e293b', fontWeight: 600 }}>{exp.company}</span>
                            {exp.location && <span style={{ fontSize: '0.82rem', color: '#64748b' }}>{exp.location}</span>}
                          </div>
                          <ul style={{ paddingLeft: '20px', margin: 0 }}>
                            {exp.tailored_bullets.map((bullet, bIdx) => (
                              <li key={bIdx} style={{ fontSize: '0.87rem', color: '#1e293b', marginBottom: '3px', textAlign: 'justify' }}>
                                {bullet}
                              </li>
                            ))}
                          </ul>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ) : (
                /* LaTeX Code Viewer */
                <div>
                  <pre
                    style={{
                      background: '#090d16',
                      color: '#38bdf8',
                      fontFamily: 'var(--font-mono)',
                      fontSize: '0.8rem',
                      padding: '18px',
                      borderRadius: 'var(--radius-md)',
                      overflowX: 'auto',
                      maxHeight: '560px',
                      border: '1px solid var(--border-subtle)',
                      lineHeight: 1.5,
                    }}
                  >
                    <code>{tailoredResult.latex_source || '% No LaTeX source generated'}</code>
                  </pre>
                </div>
              )
            ) : (
              <div style={{ textAlign: 'center', padding: '64px 20px', color: 'var(--text-muted)' }}>
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#475569" strokeWidth="1.5" style={{ marginBottom: '12px' }}>
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/>
                </svg>
                <h4 style={{ color: 'var(--text-secondary)', marginBottom: '6px' }}>Ready to Tailor</h4>
                <p style={{ fontSize: '0.85rem', maxWidth: '380px', margin: '0 auto' }}>
                  Paste a target Job Description on the left and click <strong>⚡ Tailor Resume (RAG)</strong> to synthesize an ATS-optimized resume.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

import React, { useState, useEffect } from 'react';

interface AuthHeroShowcaseProps {
  mode: 'signin' | 'signup';
}

interface ShowcaseFeature {
  headline: string;
  highlight: string;
  description: string;
  roleTitle: string;
  company: string;
  atsScore: string;
  beforeBullet: string;
  aiTailoredBullet: string;
  matchedSkills: string[];
  systemMetric: string;
  systemMetricLabel: string;
}

const SHOWCASE_FEATURES: ShowcaseFeature[] = [
  {
    headline: 'Beat the ATS with Precision',
    highlight: 'AI Resume Tailoring',
    description:
      'Paste any job description. Google Gemini and pgvector RAG analyze the requirements and dynamically rewrite your achievements for a 98%+ match score.',
    roleTitle: 'Senior Platform Engineer',
    company: 'CloudScale Technologies',
    atsScore: '98.4% ATS Match',
    beforeBullet: 'Worked on backend APIs and event pipelines for data processing.',
    aiTailoredBullet: 'Architected distributed Go/Python event-driven microservices processing 25M+ events/day via Apache Kafka with 99.99% uptime.',
    matchedSkills: ['Go', 'Python', 'Kafka', 'pgvector', 'Distributed Systems'],
    systemMetric: '42ms',
    systemMetricLabel: 'Semantic RAG Latency',
  },
  {
    headline: 'Centralized Master Career',
    highlight: 'Profile & Vector Vault',
    description:
      'Upload your resume once. Your career history and bullet points are vectorized and securely isolated by tenant, ready for instant semantic retrieval.',
    roleTitle: 'Staff AI Systems Architect',
    company: 'Nexus AI Labs',
    atsScore: '99.1% ATS Match',
    beforeBullet: 'Built RAG pipelines and vector database integrations for search.',
    aiTailoredBullet: 'Engineered multi-tenant pgvector RAG architecture with Google Gemini 2.5 Flash, reducing candidate retrieval latency by 74%.',
    matchedSkills: ['Gemini 2.5', 'pgvector', 'FastAPI', 'Multi-Tenant', 'PostgreSQL'],
    systemMetric: '100%',
    systemMetricLabel: 'Tenant Data Isolation',
  },
  {
    headline: 'Recruiter-Ready Export with',
    highlight: 'Clean LaTeX Source',
    description:
      'Export production-grade, beautifully typeset LaTeX resumes that parse cleanly through enterprise HR systems (Workday, Greenhouse, Lever).',
    roleTitle: 'Principal Full Stack Lead',
    company: 'Enterprise FinTech',
    atsScore: '97.8% ATS Match',
    beforeBullet: 'Managed web frontend and cloud deployment infrastructure.',
    aiTailoredBullet: 'Spearheaded full-stack platform modernization using React, TypeScript & Docker; compiled into automated CI/CD pipelines.',
    matchedSkills: ['LaTeX Engine', 'TypeScript', 'React', 'Docker', 'AWS'],
    systemMetric: 'Top 1%',
    systemMetricLabel: 'Recruiter Pass Tier',
  },
];

export const AuthHeroShowcase: React.FC<AuthHeroShowcaseProps> = () => {
  const [activeSlide, setActiveSlide] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setActiveSlide((prev) => (prev + 1) % SHOWCASE_FEATURES.length);
    }, 7000);
    return () => clearInterval(timer);
  }, []);

  const feature = SHOWCASE_FEATURES[activeSlide];

  return (
    <div className="auth-hero-pane">
      <div className="auth-hero-content">
        {/* Dynamic Title */}
        <h2 className="auth-hero-headline">
          {feature.headline} <span>{feature.highlight}</span>
        </h2>
        <p className="auth-hero-description">
          {feature.description}
        </p>

        {/* Live Interactive AI Resume Transformation Card */}
        <div className="auth-preview-card">
          {/* Card Top: Target Role & Score Pill */}
          <div className="auth-preview-header">
            <div className="auth-target-role-box">
              <span className="auth-role-tag">Target Role</span>
              <span className="auth-role-title">{feature.roleTitle}</span>
              <span className="auth-role-company">@ {feature.company}</span>
            </div>
            <div className="auth-score-pill">
              <span className="auth-score-dot" />
              <span className="auth-score-val">{feature.atsScore}</span>
            </div>
          </div>

          {/* AI Bullet Transformation Demonstration */}
          <div className="auth-bullet-compare-box">
            {/* Original Draft */}
            <div className="bullet-row before-row">
              <div className="bullet-label-badge before">Original Bullet</div>
              <p className="bullet-text before-text">{feature.beforeBullet}</p>
            </div>

            {/* AI Tailored Version */}
            <div className="bullet-row after-row">
              <div className="bullet-label-badge after">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                  <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
                </svg>
                AI Synthesized & Quantified
              </div>
              <p className="bullet-text after-text">{feature.aiTailoredBullet}</p>
            </div>
          </div>

          {/* Matched Skill Tags */}
          <div className="auth-skills-row">
            <span className="skills-row-label">Matched Keywords:</span>
            <div className="skills-tags-wrap">
              {feature.matchedSkills.map((skill, idx) => (
                <span key={idx} className="skill-chip">
                  ✓ {skill}
                </span>
              ))}
            </div>
          </div>

          {/* Bottom Metric Status Bar */}
          <div className="auth-card-footer">
            <div className="footer-metric-item">
              <span className="metric-val">{feature.systemMetric}</span>
              <span className="metric-lbl">{feature.systemMetricLabel}</span>
            </div>
            <div className="footer-metric-item">
              <span className="metric-val">Gemini 2.5</span>
              <span className="metric-lbl">LLM Engine</span>
            </div>
            <div className="footer-metric-item">
              <span className="metric-val">pgvector</span>
              <span className="metric-lbl">Multi-Tenant Vault</span>
            </div>
          </div>
        </div>
      </div>

      {/* Feature Slider Indicators */}
      <div className="auth-carousel-dots">
        {SHOWCASE_FEATURES.map((_, idx) => (
          <button
            key={idx}
            className={`carousel-dot ${activeSlide === idx ? 'active' : ''}`}
            onClick={() => setActiveSlide(idx)}
            aria-label={`Slide ${idx + 1}`}
          />
        ))}
      </div>
    </div>
  );
};

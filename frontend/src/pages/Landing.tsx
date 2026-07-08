"""Landing page showcasing Avatar Studio features."""

import React from 'react';
import { useNavigate } from 'react-router-dom';
import './Landing.css';

const Landing: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="landing">
      {/* Navigation */}
      <nav className="navbar">
        <div className="nav-container">
          <div className="nav-logo">🎬 Avatar Studio</div>
          <div className="nav-links">
            <button onClick={() => navigate('/dashboard')} className="nav-link">Dashboard</button>
            <button onClick={() => navigate('/studio')} className="nav-link primary">Create Video</button>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="hero">
        <div className="hero-content">
          <h1 className="hero-title">Professional AI Video Creation</h1>
          <p className="hero-subtitle">Create stunning videos with AI avatars, voice cloning, and automatic lip-syncing</p>
          <button onClick={() => navigate('/studio')} className="btn btn-primary btn-large">Start Creating</button>
        </div>
        <div className="hero-visual">
          <div className="gradient-blob blob-1"></div>
          <div className="gradient-blob blob-2"></div>
          <div className="gradient-icon">🤖</div>
        </div>
      </section>

      {/* Features Grid */}
      <section className="features">
        <h2 className="section-title">Powerful Features</h2>
        <div className="features-grid">
          <div className="feature-card">
            <div className="feature-icon">🎭</div>
            <h3>AI Avatars</h3>
            <p>Create and customize digital avatars with realistic movements</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">🎤</div>
            <h3>Voice Cloning</h3>
            <p>Clone voices or use text-to-speech in multiple languages</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">👄</div>
            <h3>Lip Sync</h3>
            <p>Automatic lip-syncing with advanced AI algorithms</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">🎨</div>
            <h3>Backgrounds</h3>
            <p>Professional background removal and custom overlays</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">📝</div>
            <h3>Subtitles</h3>
            <p>Auto-generated subtitles in multiple styles</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">⚡</div>
            <h3>Batch Processing</h3>
            <p>Generate multiple videos simultaneously</p>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="cta">
        <h2>Ready to create?</h2>
        <p>Start making professional videos in minutes</p>
        <button onClick={() => navigate('/studio')} className="btn btn-primary btn-large">Create Your First Video</button>
      </section>

      {/* Footer */}
      <footer className="footer">
        <p>&copy; 2024 Avatar Studio. Made with ❤️ by Pratik Gawad</p>
      </footer>
    </div>
  );
};

export default Landing;

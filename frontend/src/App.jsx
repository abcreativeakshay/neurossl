import React, { useState, useEffect } from 'react';
import Dashboard from './components/Dashboard';
import Analytics from './components/Analytics';
import ReportGenerator from './components/ReportGenerator';
import Settings from './components/Settings';
import Disclaimer from './components/Disclaimer';
import TermsOfService from './components/TermsOfService';
import './App.css';

function App() {
  const [activeTab, setActiveTab] = useState('sandbox');
  const [scans, setScans] = useState([]);
  const [selectedScanId, setSelectedScanId] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(window.innerWidth > 768);
  
  // Global configurations sharing state with Sandbox & Settings
  const [globalSettings, setGlobalSettings] = useState({
    temperature: 1.6995,
    mcSamples: 10,
    threshold: 0.62
  });

  const selectTab = (tab) => {
    setActiveTab(tab);
    if (window.innerWidth <= 768) {
      setSidebarOpen(false);
    }
  };

  // Custom tab switching listener (triggered from quick action button in Sandbox)
  useEffect(() => {
    const handleNavEvent = (e) => {
      if (e.detail) {
        selectTab(e.detail);
      }
    };
    window.addEventListener('nav-to-tab', handleNavEvent);
    return () => window.removeEventListener('nav-to-tab', handleNavEvent);
  }, []);

  // Sync sidebar open state with viewport resizing to handle mobile/desktop threshold smoothly
  useEffect(() => {
    let lastWidth = window.innerWidth;
    const handleResize = () => {
      const currentWidth = window.innerWidth;
      if (lastWidth > 768 && currentWidth <= 768) {
        setSidebarOpen(false);
      } else if (lastWidth <= 768 && currentWidth > 768) {
        setSidebarOpen(true);
      }
      lastWidth = currentWidth;
    };
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const handleAnalysisSuccess = (result) => {
    setLastResult(result);
  };

  const renderContent = () => {
    switch (activeTab) {
      case 'sandbox':
        return (
          <Dashboard 
            globalSettings={globalSettings} 
            scans={scans}
            setScans={setScans}
            selectedScanId={selectedScanId}
            setSelectedScanId={setSelectedScanId}
          />
        );
      case 'analytics':
        return <Analytics />;
      case 'reports':
        return (
          <ReportGenerator 
            scans={scans} 
            selectedScanId={selectedScanId}
            setSelectedScanId={setSelectedScanId}
          />
        );
      case 'settings':
        return (
          <Settings 
            globalSettings={globalSettings} 
            setGlobalSettings={setGlobalSettings}
          />
        );
      case 'disclaimer':
        return <Disclaimer />;
      case 'terms':
        return <TermsOfService />;
      default:
        return (
          <Dashboard 
            globalSettings={globalSettings} 
            scans={scans}
            setScans={setScans}
            selectedScanId={selectedScanId}
            setSelectedScanId={setSelectedScanId}
          />
        );
    }
  };

  return (
    <div className={`app-container ${sidebarOpen ? 'sidebar-open' : 'sidebar-closed'}`}>
      
      {/* PREMIUM CLINICAL SIDEBAR NAVIGATION - Hidden during printing */}
      <aside className={`sidebar no-print ${sidebarOpen ? 'open' : 'closed'}`}>
        <div className="sidebar-header">
          <div className="sidebar-logo-container" style={{ fontSize: '24px' }}>
            🧠
          </div>
          <div className="sidebar-title">
            <h1>NeuroSSL</h1>
            <span>Clinical Workstation v1.0 🏥</span>
          </div>
          <button 
            className="sidebar-close-btn no-print"
            onClick={() => setSidebarOpen(false)}
            aria-label="Close sidebar"
          >
            <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>

        <div className="sidebar-section-label">Medical Suite 🩺</div>
        <nav className="sidebar-nav">
          <button 
            className={`nav-item ${activeTab === 'sandbox' ? 'active' : ''}`}
            onClick={() => selectTab('sandbox')}
          >
            <svg className="nav-svg-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="10" />
              <path d="M12 2v20" />
              <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
            </svg>
            <span className="nav-label">Diagnostic Console</span>
          </button>

          <button 
            className={`nav-item ${activeTab === 'analytics' ? 'active' : ''}`}
            onClick={() => selectTab('analytics')}
          >
            <svg className="nav-svg-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M3 3v18h18" />
              <path d="m19 9-5 5-4-4-3 3" />
            </svg>
            <span className="nav-label">Quantitative Analytics</span>
          </button>

          <button 
            className={`nav-item ${activeTab === 'reports' ? 'active' : ''}`}
            onClick={() => selectTab('reports')}
          >
            <svg className="nav-svg-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z" />
              <path d="M14 2v4a2 2 0 0 0 2 2h4" />
              <path d="M10 9H8" />
              <path d="M16 13H8" />
              <path d="M16 17H8" />
            </svg>
            <span className="nav-label">Diagnostic Report</span>
            {scans.some(s => s.result) && <span className="nav-badge">NEW</span>}
          </button>

          <button 
            className={`nav-item ${activeTab === 'settings' ? 'active' : ''}`}
            onClick={() => selectTab('settings')}
          >
            <svg className="nav-svg-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="4" x2="4" y1="21" y2="14" />
              <line x1="4" x2="4" y1="10" y2="3" />
              <line x1="12" x2="12" y1="21" y2="12" />
              <line x1="12" x2="12" y1="8" y2="3" />
              <line x1="20" x2="20" y1="21" y2="16" />
              <line x1="20" x2="20" y1="12" y2="3" />
              <line x1="2" x2="6" y1="14" y2="14" />
              <line x1="10" x2="14" y1="8" y2="8" />
              <line x1="18" x2="22" y1="16" y2="16" />
            </svg>
            <span className="nav-label">Calibration Settings ⚙️</span>
          </button>
        </nav>

        <div className="sidebar-section-label" style={{ marginTop: '1rem' }}>Legal & Info ℹ️</div>
        <nav className="sidebar-nav" style={{ flexGrow: 0 }}>
          <button 
            className={`nav-item ${activeTab === 'disclaimer' ? 'active' : ''}`}
            onClick={() => selectTab('disclaimer')}
          >
            <span className="nav-label">⚠️ Disclaimer</span>
          </button>
          <button 
            className={`nav-item ${activeTab === 'terms' ? 'active' : ''}`}
            onClick={() => selectTab('terms')}
          >
            <span className="nav-label">📜 Terms of Service</span>
          </button>
        </nav>

        <div className="sidebar-footer">
          <div className="active-config">
            <span className="config-label">CALIBRATION MATRIX</span>
            <div className="config-item-row">
              <span className="config-item-lbl">Decision Boundary:</span>
              <span className="config-item-val">t = {globalSettings.threshold.toFixed(2)}</span>
            </div>
            <div className="config-item-row">
              <span className="config-item-lbl">Scaling Temperature:</span>
              <span className="config-item-val">T = {globalSettings.temperature.toFixed(4)}</span>
            </div>
            <div className="config-item-row">
              <span className="config-item-lbl">Uncertainty Samples:</span>
              <span className="config-item-val">N = {globalSettings.mcSamples} runs</span>
            </div>
          </div>
          <div className="version-info">
            <div className="info-row">
              <span className="info-lbl">Neural Encoder:</span>
              <span className="info-val">MultiScaleViT2D</span>
            </div>
            <div className="info-row">
              <span className="info-lbl">Co-variance:</span>
              <span className="info-val">Second Order</span>
            </div>
            <div className="info-row">
              <span className="info-lbl">Acceleration:</span>
              <span className="info-val highlight-green">MPS Engine</span>
            </div>
          </div>
        </div>
      </aside>

      {/* Backdrop overlay for mobile to close sidebar when clicking outside */}
      {sidebarOpen && (
        <div 
          className="sidebar-backdrop no-print" 
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* MAIN CONTAINER AREA */}
      <main className="main-content">
        
        {/* TOP BAR - Hidden during printing */}
        <header className="topbar no-print">
          <div className="topbar-left" style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <button 
              className="btn-secondary" 
              style={{ padding: '0.5rem', borderRadius: '8px', border: 'none', background: 'transparent' }}
              onClick={() => setSidebarOpen(!sidebarOpen)}
            >
              <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="3" y1="12" x2="21" y2="12"></line>
                <line x1="3" y1="6" x2="21" y2="6"></line>
                <line x1="3" y1="18" x2="21" y2="18"></line>
              </svg>
            </button>
            <div>
              <h2>
                {activeTab === 'sandbox' && '🧠 Clinical Diagnostics Sandbox'}
              {activeTab === 'analytics' && '📊 Deep Learning Analytics'}
                {activeTab === 'reports' && '📝 Diagnostic Assessment Report'}
                {activeTab === 'settings' && '⚙️ Inference Parameter Controls'}
                {activeTab === 'disclaimer' && '⚠️ Medical Disclaimer'}
                {activeTab === 'terms' && '📜 Terms of Service'}
              </h2>
              <span className="topbar-subtitle">
              {activeTab === 'sandbox' && 'Upload brain MRI slices or test demo cohorts using Platt calibrated networks'}
              {activeTab === 'analytics' && 'Verify cross-validation results, Platt ECE metrics, and validation curves'}
              {activeTab === 'reports' && 'Preview, sign, and print printable diagnostic case files for patient history'}
                {activeTab === 'settings' && 'Optimize temperature parameters, dropout sample rate, and sensitivity boundaries'}
                {activeTab === 'disclaimer' && 'Important legal and clinical disclaimers regarding the use of NeuroSSL.'}
                {activeTab === 'terms' && 'Terms and conditions for using the NeuroSSL platform.'}
              </span>
            </div>
          </div>
          <div className="topbar-right">
            <span className="system-status-indicator">
              <span className="status-dot green" /> Inference Engine Ready
            </span>
          </div>
        </header>

        {/* Dynamic Page Rendering */}
        <div className="content-area">
          {renderContent()}
        </div>
      </main>

    </div>
  );
}

export default App;

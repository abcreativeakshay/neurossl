import React, { useState } from 'react';
import MRIViewer from './MRIViewer';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || '';

const Dashboard = ({ globalSettings, scans, setScans, selectedScanId, setSelectedScanId }) => {
  // Viewer settings
  const [opacity, setOpacity] = useState(0.5);
  const [colormap, setColormap] = useState('jet');

  // Derive current selected scan details
  const selectedScan = scans.find(s => s.id === selectedScanId) || null;
  const previewUrl = selectedScan?.previewUrl || null;
  const result = selectedScan?.result || null;
  const loading = selectedScan?.loading || false;
  const error = selectedScan?.error || null;

  const addFilesToQueue = (fileList) => {
    const newScans = fileList.map((file, idx) => ({
      id: `scan-${Date.now()}-${idx}-${Math.random().toString(36).substr(2, 5)}`,
      file,
      name: file.name,
      previewUrl: URL.createObjectURL(file),
      loading: false,
      error: null,
      result: null
    }));

    setScans(prev => {
      const updated = [...prev, ...newScans];
      return updated;
    });

    if (!selectedScanId && newScans.length > 0) {
      setSelectedScanId(newScans[0].id);
    }
  };

  const handleFileUpload = (e) => {
    const uploadedFiles = Array.from(e.target.files);
    if (uploadedFiles.length === 0) return;
    addFilesToQueue(uploadedFiles);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const uploadedFiles = Array.from(e.dataTransfer.files).filter(f => f.type.startsWith('image/'));
    if (uploadedFiles.length > 0) {
      addFilesToQueue(uploadedFiles);
    }
  };

  const runAnalysisForScan = async (scanId) => {
    const scanToAnalyze = scans.find(s => s.id === scanId);
    if (!scanToAnalyze || scanToAnalyze.loading) return;

    // Set loading state for this scan
    setScans(prev => prev.map(s => s.id === scanId ? { ...s, loading: true, error: null } : s));

    const formData = new FormData();
    formData.append('temperature', globalSettings.temperature);
    formData.append('mc_samples', globalSettings.mcSamples);
    formData.append('threshold', globalSettings.threshold);
    formData.append('file', scanToAnalyze.file);

    try {
      const response = await fetch(`${BACKEND_URL}/api/predict`, {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || "Inference server error");
      }

      const data = await response.json();
      
      // Update result state for this scan
      setScans(prev => prev.map(s => s.id === scanId ? { 
        ...s, 
        loading: false, 
        result: {
          ...data,
          imageUrl: s.previewUrl
        } 
      } : s));
    } catch (err) {
      console.error(err);
      setScans(prev => prev.map(s => s.id === scanId ? { 
        ...s, 
        loading: false, 
        error: err.message || "An unexpected error occurred during prediction." 
      } : s));
    }
  };

  const runAnalysisSelected = () => {
    if (selectedScanId) {
      runAnalysisForScan(selectedScanId);
    }
  };

  const runAnalysisAll = async () => {
    const pendingScans = scans.filter(s => !s.result && !s.loading);
    if (pendingScans.length === 0) return;
    
    // Execute all pending scans concurrently
    await Promise.all(pendingScans.map(s => runAnalysisForScan(s.id)));
  };

  const removeScan = (scanId, e) => {
    if (e) e.stopPropagation(); // Avoid selecting the item when deleting
    
    setScans(prev => {
      const filtered = prev.filter(s => s.id !== scanId);
      const removedScan = prev.find(s => s.id === scanId);
      if (removedScan) {
        URL.revokeObjectURL(removedScan.previewUrl);
      }
      return filtered;
    });

    if (selectedScanId === scanId) {
      const remaining = scans.filter(s => s.id !== scanId);
      if (remaining.length > 0) {
        setSelectedScanId(remaining[0].id);
      } else {
        setSelectedScanId(null);
      }
    }
  };

  const clearAllScans = () => {
    scans.forEach(s => URL.revokeObjectURL(s.previewUrl));
    setScans([]);
    setSelectedScanId(null);
  };

  const getStatusBadgeStyle = (scan) => {
    let bg = 'rgba(255, 255, 255, 0.04)';
    let color = 'rgba(255, 255, 255, 0.5)';
    let text = 'Pending';
    
    if (scan.loading) {
      bg = 'rgba(59, 130, 246, 0.15)';
      color = '#60a5fa';
      text = 'Analyzing...';
    } else if (scan.result) {
      text = scan.result.binary_prediction;
      if (scan.result.color_code === 'green') {
        bg = 'rgba(16, 185, 129, 0.15)';
        color = '#34d399';
      } else if (scan.result.color_code === 'red') {
        bg = 'rgba(239, 68, 68, 0.15)';
        color = '#f87171';
      } else if (scan.result.color_code === 'orange') {
        bg = 'rgba(245, 158, 11, 0.15)';
        color = '#fbbf24';
      } else {
        bg = 'rgba(251, 191, 36, 0.15)';
        color = '#fbbf24';
      }
    } else if (scan.error) {
      bg = 'rgba(239, 68, 68, 0.15)';
      color = '#f87171';
      text = 'Error';
    }
    
    return { bg, color, text };
  };

  const pendingCount = scans.filter(s => !s.result && !s.loading).length;

  return (
    <div className="dashboard-grid">
      
      {/* LEFT COLUMN: Data Input and Selection */}
      <div className="dashboard-card panel-left" style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
        <h3 className="panel-title" style={{ marginBottom: '1rem' }}>1. 📥 Patient Scan Input</h3>
        
        {/* Upload Zone */}
        <div 
          className={`upload-zone ${scans.length > 0 ? 'has-file' : ''}`}
          onDragOver={handleDragOver}
          onDrop={handleDrop}
          style={{ padding: '1.25rem', textAlign: 'center', border: '2px dashed rgba(255,255,255,0.1)', borderRadius: '10px', cursor: 'pointer', transition: 'all 0.2s ease' }}
        >
          <input 
            type="file" 
            id="mri-upload-input" 
            accept="image/*" 
            multiple
            onChange={handleFileUpload} 
            style={{ display: 'none' }}
          />
          <label htmlFor="mri-upload-input" className="upload-label" style={{ cursor: 'pointer', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.5rem' }}>
            <svg viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="currentColor" strokeWidth="2" className="upload-icon" style={{ opacity: 0.7 }}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 16.5V9.75m0 0l3 3m-3-3l-3 3M6.75 19.5a4.5 4.5 0 01-1.41-8.775 5.25 5.25 0 0110.233-2.33 3 3 0 013.758 3.848A3.752 3.752 0 0118 19.5H6.75z" />
            </svg>
            <span style={{ fontSize: '0.8rem', opacity: 0.85 }}>
              Drag & drop MRI slices or <strong className="glow-text" style={{ color: 'var(--color-primary)' }}>Browse Files</strong>
            </span>
          </label>
        </div>

        {/* Scan Queue / List */}
        {scans.length > 0 && (
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', marginTop: '1.25rem', minHeight: 0 }}>
            <div style={{ display: 'flex', justifyContent: 'between', alignItems: 'center', marginBottom: '0.5rem' }}>
              <span style={{ fontSize: '0.75rem', fontWeight: '600', color: 'var(--text-secondary)' }}>
                SCAN COLLECTION ({scans.length})
              </span>
            </div>
            
            <div className="scan-queue-list" style={{ flex: 1, overflowY: 'auto', paddingRight: '4px', minHeight: '120px' }}>
              {scans.map((scan) => {
                const isSelected = scan.id === selectedScanId;
                const { bg, color, text } = getStatusBadgeStyle(scan);

                return (
                  <div 
                    key={scan.id} 
                    className={`scan-queue-item ${isSelected ? 'selected' : ''}`}
                    onClick={() => setSelectedScanId(scan.id)}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.65rem',
                      padding: '0.6rem',
                      borderRadius: '8px',
                      cursor: 'pointer',
                      marginBottom: '0.5rem',
                      background: isSelected ? 'rgba(255,255,255,0.06)' : 'rgba(255,255,255,0.02)',
                      border: isSelected ? '1px solid rgba(255,255,255,0.12)' : '1px solid rgba(255,255,255,0.03)',
                      transition: 'all 0.2s ease',
                    }}
                  >
                    <img 
                      src={scan.previewUrl} 
                      alt="Preview" 
                      style={{ width: '38px', height: '38px', borderRadius: '4px', objectFit: 'cover', border: '1px solid rgba(255,255,255,0.08)' }}
                    />
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ fontSize: '0.78rem', fontWeight: '500', color: '#fff', textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap' }}>
                        {scan.name}
                      </div>
                      <div style={{ display: 'flex', marginTop: '0.2rem' }}>
                        <span style={{ fontSize: '0.62rem', fontWeight: '600', padding: '0.1rem 0.4rem', borderRadius: '4px', backgroundColor: bg, color: color, textTransform: 'uppercase', letterSpacing: '0.3px' }}>
                          {text}
                        </span>
                      </div>
                    </div>
                    <button 
                      onClick={(e) => removeScan(scan.id, e)}
                      style={{
                        background: 'transparent',
                        border: 'none',
                        color: 'rgba(255,255,255,0.35)',
                        cursor: 'pointer',
                        padding: '4px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        borderRadius: '4px',
                        transition: 'color 0.2s'
                      }}
                      onMouseEnter={(e) => e.target.style.color = '#f87171'}
                      onMouseLeave={(e) => e.target.style.color = 'rgba(255,255,255,0.35)'}
                      title="Remove Scan"
                    >
                      ✕
                    </button>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Predict Action Buttons */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginTop: '1.25rem' }}>
          <button 
            className={`btn-primary w-full ${loading ? 'loading' : ''}`} 
            onClick={runAnalysisSelected}
            disabled={loading || !selectedScanId || result}
            style={{ padding: '0.65rem' }}
          >
            {loading ? 'Executing Neural Inference...' : result ? 'Analysis Complete' : 'Run Diagnostics'}
          </button>
          
          {scans.length > 1 && (
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <button 
                className="btn-secondary" 
                onClick={runAnalysisAll}
                disabled={pendingCount === 0 || scans.some(s => s.loading)}
                style={{ flex: 1, padding: '0.5rem', fontSize: '0.78rem' }}
              >
                ⚡ Run All Pending ({pendingCount})
              </button>
              
              <button 
                className="btn-secondary" 
                onClick={clearAllScans}
                style={{ padding: '0.5rem', fontSize: '0.78rem', color: '#f87171', borderColor: 'rgba(239, 68, 68, 0.2)' }}
              >
                🗑️ Clear All
              </button>
            </div>
          )}
        </div>

        {error && <div className="error-alert" style={{ marginTop: '1rem' }}>{error}</div>}
      </div>

      {/* CENTER COLUMN: Interactive Visualizer */}
      <div className="dashboard-card panel-center">
        <h3 className="panel-title">2. 🧠 Neural Attention Mapping</h3>
        
        {previewUrl ? (
          <MRIViewer 
            imageUrl={previewUrl}
            attentionMap={result?.attention_map}
            opacity={opacity}
            colormap={colormap}
          />
        ) : (
          <div style={{ display: 'flex', flex: 1, flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '300px', border: '1px dashed rgba(255,255,255,0.08)', borderRadius: '12px', color: 'var(--text-muted)' }}>
            <span style={{ fontSize: '2.5rem', marginBottom: '0.75rem' }}>🧠</span>
            <p style={{ fontSize: '0.85rem' }}>No patient scan selected for visualization</p>
          </div>
        )}

        {/* Overlay Adjustments */}
        {result && (
          <div className="visualization-controls">
            <div className="control-group">
              <label>Attention Map Opacity: {Math.round(opacity * 100)}%</label>
              <input 
                type="range" 
                min="0" 
                max="1" 
                step="0.05" 
                value={opacity} 
                onChange={(e) => setOpacity(parseFloat(e.target.value))}
                className="slider-primary"
              />
            </div>
            
            <div className="control-group">
              <label>Visual Colormap Style</label>
              <div className="colormap-selector">
                {['jet', 'hot', 'viridis', 'plasma'].map(cmap => (
                  <button 
                    key={cmap}
                    className={`cmap-btn ${colormap === cmap ? 'active' : ''} cmap-${cmap}`}
                    onClick={() => setColormap(cmap)}
                  >
                    {cmap.toUpperCase()}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* RIGHT COLUMN: Diagnostic Results */}
      <div className="dashboard-card panel-right results-panel">
        <h3 className="panel-title">3. 📝 Diagnostic Assessment</h3>

        {loading && (
          <div className="skeleton-container">
            <div className="skeleton-pulse skeleton-title" />
            <div className="skeleton-pulse skeleton-box" />
            <div className="skeleton-pulse skeleton-bar" />
            <div className="skeleton-pulse skeleton-bar" />
          </div>
        )}

        {!loading && !result && (
          <div className="results-placeholder">
            <svg viewBox="0 0 24 24" width="48" height="48" fill="none" stroke="currentColor" strokeWidth="1.2">
              <path strokeLinecap="round" strokeLinejoin="round" d="M9.75 3.104v1.244c0 .89-.56 1.6-1.39 1.6H6.25c-.83 0-1.39-.71-1.39-1.6V3.104m5.27 0a9.002 9.002 0 00-5.27 0m5.27 0c1.352.09 2.533.624 3.56 1.458m-8.83 0A9.001 9.001 0 003 12c0 3.18 1.662 6 4.18 7.544m0 0v-1.29c0-.89.56-1.6 1.39-1.6h1.96c.83 0 1.39.71 1.39 1.6v1.29m-4.74 0c1.352.09 2.533.624 3.56 1.458m0-1.458a9.003 9.003 0 005.27 0m-5.27 0v1.244c0 .89.56 1.6 1.39 1.6h1.96c.83 0 1.39-.71 1.39-1.6V19.54m-5.27 0A9.002 9.002 0 0019.5 12c0-3.18-1.662-6-4.18-7.544m0 0v1.29c0 .89-.56 1.6-1.39 1.6h-1.96c-.83 0-1.39-.71-1.39-1.6v-1.29" />
            </svg>
            {selectedScanId ? (
              <p>Awaiting diagnostics execution for <strong>{selectedScan?.name}</strong>...</p>
            ) : (
              <p>Awaiting scan upload and neural diagnostics execution...</p>
            )}
          </div>
        )}

        {!loading && result && (
          <div className="results-content fade-in">
            
            {/* Status Alert Banner */}
            <div className={`status-banner banner-${result.color_code}`}>
              <div className="status-marker" />
              <div className="status-banner-text">
                <div className="status-label">CLASSIFICATION RESULT</div>
                <div className="status-val">{result.binary_prediction}</div>
              </div>
            </div>

            {/* Clinical Message Card */}
            <div className={`clinical-card card-${result.color_code}`}>
              <div className="card-header-icon">🛡️ Clinical Recommendation</div>
              <p className="clinical-text">{result.clinical_message}</p>
            </div>

            {/* Metric Metrics Grid */}
            <div className="metrics-summary-grid">
              
              {/* Probability Card */}
              <div className="metric-box">
                <span className="metric-title">Calibrated Probability</span>
                <div className="metric-value">
                  {Math.round(result.calibrated_probability * 1000) / 10}%
                </div>
                <div className="metric-progress-bg">
                  <div 
                    className="metric-progress-fill fill-prob" 
                    style={{ width: `${result.calibrated_probability * 100}%` }} 
                  />
                </div>
                <span className="metric-sub">Raw Output: {Math.round(result.raw_probability * 1000) / 10}%</span>
              </div>

              {/* Uncertainty Card */}
              <div className="metric-box">
                <span className="metric-title">Model Uncertainty (σ)</span>
                <div className="metric-value">
                  {result.uncertainty.toFixed(3)}
                </div>
                <div className="metric-progress-bg">
                  <div 
                    className={`metric-progress-fill fill-uncert ${result.uncertainty > 0.15 ? 'warn' : ''}`} 
                    style={{ width: `${Math.min(result.uncertainty * 400, 100)}%` }} 
                  />
                </div>
                <span className="metric-sub">Confidence level: <strong>{result.confidence_level}</strong></span>
              </div>
              
            </div>

            {/* Quick Action */}
            <div className="quick-actions">
              <span className="quick-action-text">Create patient record from this assessment:</span>
              <button 
                className="btn-secondary w-full"
                onClick={() => {
                  window.dispatchEvent(new CustomEvent('nav-to-tab', { detail: 'reports' }));
                }}
              >
                📝 Transfer to Diagnostic Report
              </button>
            </div>

          </div>
        )}
      </div>

    </div>
  );
};

export default Dashboard;

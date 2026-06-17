import React, { useState, useEffect } from 'react';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || '';

const Analytics = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeLightbox, setActiveLightbox] = useState(null);

  useEffect(() => {
    fetch(`${BACKEND_URL}/api/analytics`)
      .then(res => {
        if (!res.ok) throw new Error("Could not fetch analytics data");
        return res.json();
      })
      .then(json => {
        setData(json);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setError("Error connecting to server. Please verify the backend is active.");
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <div className="analytics-loading">
        <div className="spinner" />
        <p>Retrieving model training parameters and reports...</p>
      </div>
    );
  }

  if (error) {
    return <div className="error-alert max-w-xl mx-auto mt-8">{error}</div>;
  }

  const metrics = data?.metrics?.cross_validation?.metrics || {};
  const calibration = data?.metrics?.calibration || {};
  const datasets = data?.metrics?.datasets || {};
  const bestFold = data?.metrics?.best_fold ?? 0;
  const figures = data?.figures || [];

  return (
    <div className="analytics-container fade-in">
      
      {/* Overview Cards */}
      <div className="section-header">
        <h2>📊 Model Metrics & Cross-Validation</h2>
        <span className="badge-fold">Optimal Performance (Fold {bestFold}) ⭐</span>
      </div>

      <div className="metrics-grid">
        <div className="metric-card glow-blue">
          <span className="card-label">Test ROC-AUC</span>
          <div className="card-val">{(metrics.test_auc?.mean * 100).toFixed(2)}%</div>
          <span className="card-desc">Discriminative power of prediction model</span>
        </div>
        <div className="metric-card">
          <span className="card-label">Sensitivity (Recall)</span>
          <div className="card-val text-green">{(metrics.test_sensitivity?.mean * 100).toFixed(2)}%</div>
          <span className="card-desc">True positive rate (identifying dementia cases)</span>
        </div>
        <div className="metric-card">
          <span className="card-label">Specificity</span>
          <div className="card-val text-yellow">{(metrics.test_specificity?.mean * 100).toFixed(2)}%</div>
          <span className="card-desc">True negative rate (identifying healthy controls)</span>
        </div>
        <div className="metric-card">
          <span className="card-label">F1 Diagnostic Score</span>
          <div className="card-val">{(metrics.test_f1?.mean * 100).toFixed(2)}%</div>
          <span className="card-desc">Harmonic mean of precision and sensitivity</span>
        </div>
      </div>

      <div className="analytics-details-grid">
        
        {/* Dataset Stats */}
        <div className="analytics-detail-card">
          <h4>🗂️ Dataset Scale & Composition</h4>
          <div className="dataset-stats-list">
            <div className="dataset-row">
              <span className="dataset-label">Total Slices Pool</span>
              <span className="dataset-val">{(datasets.oasis_slices + datasets.ixi_slices || 0).toLocaleString()} Slices</span>
            </div>
            <div className="dataset-row-sub">
              <span>• OASIS Neuroimaging Dataset</span>
              <span>{datasets.oasis_slices?.toLocaleString()} slices</span>
            </div>
            <div className="dataset-row-sub">
              <span>• IXI Normal Brain Dataset</span>
              <span>{datasets.ixi_slices?.toLocaleString()} slices</span>
            </div>
            <div className="dataset-row" style={{ marginTop: '1.5rem' }}>
              <span className="dataset-label">Matthews Correlation (MCC)</span>
              <span className="dataset-val">{metrics.test_mcc?.mean.toFixed(4)}</span>
            </div>
            <div className="dataset-row">
              <span className="dataset-label">Cohen's Kappa (Agreement)</span>
              <span className="dataset-val">{metrics.test_kappa?.mean.toFixed(4)}</span>
            </div>
            <div className="dataset-row">
              <span className="dataset-label">Brier Calibration Score</span>
              <span className="dataset-val">{metrics.test_brier?.mean.toFixed(4)}</span>
            </div>
          </div>
        </div>

        {/* Calibration Stats */}
        <div className="analytics-detail-card">
          <h4>🌡️ Probability Temperature Calibration</h4>
          <p className="description-text">
            Neural networks are often overconfident. Platt scaling adjusts model outputs 
            using validation-set temperature mapping to align prediction percentages with actual diagnosis rates.
          </p>
          <div className="calibration-stats">
            <div className="calib-metric">
              <span className="calib-label">Optimal Scaling Temp (T)</span>
              <span className="calib-val">{calibration.temperature?.toFixed(4)}</span>
            </div>
            <div className="calib-row-container">
              <div className="calib-bar-group">
                <div className="calib-bar-label">
                  <span>ECE Before Calibration</span>
                  <span>{(calibration.ece_before * 100).toFixed(2)}%</span>
                </div>
                <div className="calib-bar-bg">
                  <div className="calib-bar-fill before" style={{ width: `${calibration.ece_before * 100}%` }} />
                </div>
              </div>
              <div className="calib-bar-group">
                <div className="calib-bar-label">
                  <span>ECE After Calibration</span>
                  <span>{(calibration.ece_after * 100).toFixed(2)}%</span>
                </div>
                <div className="calib-bar-bg">
                  <div className="calib-bar-fill after" style={{ width: `${calibration.ece_after * 100}%` }} />
                </div>
              </div>
            </div>
            <div className="calib-improvement-box">
              <span>📈 expected calibration error (ECE) reduced by <strong>{((calibration.ece_before - calibration.ece_after)*100).toFixed(2)}%</strong></span>
            </div>
          </div>
        </div>

      </div>

      {/* Validation Figures Gallery */}
      <div className="section-header mt-8">
        <h2>📈 Diagnostic Validation Curves & Embeddings</h2>
        <span className="header-subtitle">Click any image to expand and view high-resolution analysis curves</span>
      </div>

      <div className="figures-gallery-grid">
        {figures.map(fig => {
          // Create human readable labels
          const title = fig
            .replace('.png', '')
            .replace(/_/g, ' ')
            .toUpperCase();
          return (
            <div 
              key={fig} 
              className="figure-card"
              onClick={() => setActiveLightbox(`${BACKEND_URL}/api/figures/${fig}`)}
            >
              <div className="figure-img-wrapper">
                <img 
                  src={`${BACKEND_URL}/api/figures/${fig}`} 
                  alt={title} 
                  loading="lazy"
                />
              </div>
              <div className="figure-label">
                <h5>{title}</h5>
                <span className="figure-zoom-text">🔎 Click to Expand</span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Lightbox Modal */}
      {activeLightbox && (
        <div className="lightbox-modal" onClick={() => setActiveLightbox(null)}>
          <div className="lightbox-content" onClick={(e) => e.stopPropagation()}>
            <button className="lightbox-close" onClick={() => setActiveLightbox(null)}>×</button>
            <img src={activeLightbox} alt="Expanded diagnostic chart" />
          </div>
        </div>
      )}

    </div>
  );
};

export default Analytics;

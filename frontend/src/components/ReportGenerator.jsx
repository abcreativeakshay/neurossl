import React, { useState, useEffect } from 'react';
import MRIViewer from './MRIViewer';

const ReportGenerator = ({ scans, selectedScanId, setSelectedScanId }) => {
  const [patientInfo, setPatientInfo] = useState({
    name: '',
    age: '',
    gender: 'Male',
    id: '',
    physician: 'Dr. Akshay Biradar',
    notes: '',
    scanDate: new Date().toISOString().split('T')[0]
  });

  const analyzedScans = scans.filter(s => s.result !== null);

  // Keep track of report scan selection
  const [reportScanId, setReportScanId] = useState('');

  // Sync selection when scans change or active tab switches
  useEffect(() => {
    const defaultScan = scans.find(s => s.id === selectedScanId && s.result);
    if (defaultScan) {
      setReportScanId(defaultScan.id);
    } else if (analyzedScans.length > 0 && !analyzedScans.some(s => s.id === reportScanId)) {
      setReportScanId(analyzedScans[0].id);
    }
  }, [scans, selectedScanId]);

  const reportScan = scans.find(s => s.id === reportScanId) || null;
  const activeResult = reportScan ? reportScan.result : null;

  // Pre-fill if a result exists
  useEffect(() => {
    if (activeResult) {
      setPatientInfo(prev => ({
        ...prev,
        id: prev.id || `PAT-${Math.floor(100000 + Math.random() * 900000)}`
      }));
    }
  }, [activeResult]);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setPatientInfo(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="report-container fade-in">
      
      {/* FORM CONTROL PANEL - Hidden during print */}
      <div className="report-form-panel no-print">
        <h3 className="panel-title">📋 Diagnostic Report Metadata</h3>
        <div className="form-grid">
          
          {analyzedScans.length > 0 && (
            <div className="form-group">
              <label>Select Patient Scan for Report</label>
              <select 
                value={reportScanId} 
                onChange={(e) => setReportScanId(e.target.value)}
                style={{
                  width: '100%',
                  padding: '0.6rem',
                  borderRadius: '6px',
                  background: 'rgba(255,255,255,0.04)',
                  border: '1px solid rgba(255,255,255,0.1)',
                  color: '#fff',
                  fontFamily: 'inherit',
                  outline: 'none',
                  fontSize: '0.82rem',
                }}
              >
                {analyzedScans.map(s => (
                  <option key={s.id} value={s.id} style={{ background: '#111827' }}>
                    {s.name} ({s.result.binary_prediction})
                  </option>
                ))}
              </select>
            </div>
          )}

          <div className="form-group">
            <label>Patient Full Name</label>
            <input 
              type="text" 
              name="name" 
              value={patientInfo.name} 
              onChange={handleInputChange} 
              placeholder="e.g. John Doe"
            />
          </div>

          <div className="form-group-row" style={{ display: 'flex', gap: '0.5rem' }}>
            <div className="form-group" style={{ flex: 1 }}>
              <label>Age</label>
              <input 
                type="number" 
                name="age" 
                value={patientInfo.age} 
                onChange={handleInputChange} 
                placeholder="e.g. 72"
              />
            </div>
            <div className="form-group" style={{ flex: 1 }}>
              <label>Gender</label>
              <select name="gender" value={patientInfo.gender} onChange={handleInputChange}>
                <option value="Male">Male</option>
                <option value="Female">Female</option>
                <option value="Other">Other</option>
              </select>
            </div>
          </div>

          <div className="form-group">
            <label>Patient ID / Case Code</label>
            <input 
              type="text" 
              name="id" 
              value={patientInfo.id} 
              onChange={handleInputChange} 
              placeholder="e.g. PAT-849301"
            />
          </div>

          <div className="form-group">
            <label>Attending Radiologist / Physician</label>
            <input 
              type="text" 
              name="physician" 
              value={patientInfo.physician} 
              onChange={handleInputChange}
            />
          </div>

          <div className="form-group">
            <label>Physician Clinical Findings / Diagnosis Notes</label>
            <textarea 
              name="notes" 
              rows="4" 
              value={patientInfo.notes} 
              onChange={handleInputChange} 
              placeholder="Enter patient diagnosis, comments, and treatment suggestions..."
            />
          </div>
        </div>

        <button 
          className="btn-primary w-full btn-lg mt-4" 
          onClick={handlePrint}
          disabled={!activeResult}
        >
          Export Diagnostic Report (Print / PDF)
        </button>
        {analyzedScans.length === 0 && (
          <div className="form-warning" style={{ marginTop: '1rem', padding: '0.75rem', borderRadius: '8px', background: 'rgba(245, 158, 11, 0.1)', border: '1px solid rgba(245, 158, 11, 0.2)', color: '#fbbf24', fontSize: '0.8rem' }}>
            ⚠️ Run diagnostics on a scan in the <strong>Diagnostic Console</strong> first to attach MRI scans to the report.
          </div>
        )}
      </div>

      {/* REPORT SHEET FOR PRINTING */}
      <div className="report-sheet-wrapper">
        <div className="report-sheet">
          
          {/* Diagnostic Header */}
          <div className="report-header">
            <div className="hospital-logo">
              <span className="logo-icon">🧠</span>
              <div className="logo-text">
                <h2>NEURO-SSL CLINICAL PORTAL</h2>
                <span>Self-Supervised Deep Learning Imaging Laboratory</span>
              </div>
            </div>
            <div className="report-meta-box">
              <div><strong>Doc ID:</strong> {patientInfo.id || 'N/A'}</div>
              <div><strong>Date:</strong> {patientInfo.scanDate}</div>
            </div>
          </div>

          <hr className="report-divider" />

          {/* Patient Details Grid */}
          <h3 className="section-subtitle">👤 Patient Demographics</h3>
          <div className="demographics-grid">
            <div className="demo-item"><strong>Patient Name:</strong> <span>{patientInfo.name || 'Unspecified'}</span></div>
            <div className="demo-item"><strong>Patient ID:</strong> <span>{patientInfo.id || 'N/A'}</span></div>
            <div className="demo-item"><strong>Age / Gender:</strong> <span>{patientInfo.age || 'N/A'} yrs / {patientInfo.gender}</span></div>
            <div className="demo-item"><strong>Referring Doctor:</strong> <span>{patientInfo.physician}</span></div>
          </div>

          <hr className="report-divider" />

          {/* Scan Visualizations */}
          <h3 className="section-subtitle">🔍 Deep Learning MRI Assessment</h3>
          <div className="scans-report-grid">
            
            {/* Visualizer Frame */}
            <div className="report-viewer-card">
              <div className="viewer-title">Original Slice vs. ViT Attention Overlay</div>
              {activeResult ? (
                <div className="report-viewer-holder">
                  <MRIViewer 
                    imageUrl={activeResult.imageUrl}
                    attentionMap={activeResult.attention_map}
                    opacity={0.65}
                    colormap="jet"
                  />
                </div>
              ) : (
                <div className="report-scan-placeholder">
                  No scan analysis attached to this report.
                </div>
              )}
            </div>

            {/* Neural Evaluation Details */}
            <div className="report-findings-card">
              <div className="findings-title">AI Diagnostics Summary</div>
              {activeResult ? (
                <div className="findings-list">
                  <div className="findings-row">
                    <span>Classification Output</span>
                    <strong className={`badge-report text-${activeResult.color_code}`}>
                      {activeResult.binary_prediction}
                    </strong>
                  </div>
                  <div className="findings-row">
                    <span>Calibrated Confidence</span>
                    <strong>{Math.round(activeResult.calibrated_probability * 1000) / 10}%</strong>
                  </div>
                  <div className="findings-row">
                    <span>Uncertainty Factor (σ)</span>
                    <strong>{activeResult.uncertainty.toFixed(4)}</strong>
                  </div>
                  <div className="findings-row">
                    <span>Model Confidence Band</span>
                    <strong>{activeResult.confidence_level}</strong>
                  </div>

                  <div className={`report-clinical-alert border-${activeResult.color_code}`}>
                    <strong>Assessment Flag:</strong>
                    <p>{activeResult.clinical_message}</p>
                  </div>
                </div>
              ) : (
                <div className="report-scan-placeholder">
                  Awaiting inference data attachment...
                </div>
              )}
            </div>

          </div>

          <hr className="report-divider" />

          {/* Physician Notes */}
          <div className="report-notes-section">
            <h3 className="section-subtitle">✍️ Clinical Findings & Comments</h3>
            <div className="notes-box">
              {patientInfo.notes ? (
                <p className="clinical-notes-preview">{patientInfo.notes}</p>
              ) : (
                <div className="blank-notes-lines">
                  <div className="note-line" />
                  <div className="note-line" />
                  <div className="note-line" />
                </div>
              )}
            </div>
          </div>

          {/* Signature Footer */}
          <div className="report-footer-signatures">
            <div className="sig-block">
              <div className="sig-line" />
              <span>Assessing Clinician / Signature</span>
            </div>
            <div className="sig-block">
              <div className="sig-line" />
              <span>Date of Verification</span>
            </div>
          </div>

          <div className="report-disclaimer">
            Disclaimer: This diagnostic report is generated by a deep learning Vision Transformer neural network. 
            Results are uncertainty-aware and calibrated, but should be used in conjunction with full patient histories 
            and verified by a board-certified neuroradiologist.
          </div>
        </div>
      </div>

    </div>
  );
};

export default ReportGenerator;

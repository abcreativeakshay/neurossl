import React from 'react';

const TermsOfService = () => {
  return (
    <div className="analytics-container fade-in">
      <div className="section-header">
        <h2>📜 Terms of Service</h2>
      </div>
      <div className="settings-card">
        <p className="description-text" style={{ fontSize: '1rem', lineHeight: '1.6' }}>
          Welcome to NeuroSSL. By using our platform, you agree to these terms.
        </p>
        <h4 style={{ marginTop: '1rem', marginBottom: '0.5rem' }}>1. 🤝 Acceptance of Terms</h4>
        <p className="description-text">By accessing and using this tool, you accept and agree to be bound by the terms and provision of this agreement.</p>
        
        <h4 style={{ marginTop: '1rem', marginBottom: '0.5rem' }}>2. 🩺 Use of the Service</h4>
        <p className="description-text">This service is designed for medical image analysis research. You agree not to use the service for any illegal or unauthorized purpose.</p>
        
        <h4 style={{ marginTop: '1rem', marginBottom: '0.5rem' }}>3. 🔒 Privacy and Data Security</h4>
        <p className="description-text">Uploaded images are processed ephemerally or subject to the privacy policies of the hosting environment. Do not upload images containing Personally Identifiable Information (PII) or Protected Health Information (PHI) unless authorized.</p>
        
        <h4 style={{ marginTop: '1rem', marginBottom: '0.5rem' }}>4. 🛑 Limitation of Liability</h4>
        <p className="description-text">In no event shall the creators or maintainers of NeuroSSL be liable for any direct, indirect, incidental, special, or consequential damages resulting from the use or the inability to use the service.</p>
      </div>
    </div>
  );
};

export default TermsOfService;

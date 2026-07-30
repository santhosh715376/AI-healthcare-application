import React, { useState } from 'react';
import DoctorPortal from './DoctorPortal.jsx';
import PatientPortal from './PatientPortal.jsx';

export default function CapturePage() {
  const [userRole, setUserRole] = useState('doctor'); // 'doctor' | 'patient'

  return (
    <div className="app-container">
      {/* Global Header & Role Selection Router */}
      <header className="app-header">
        <div className="brand">
          <span>🩺 Personalized Healthcare Platform</span>
          <span className="brand-badge">Phase 1 Live Architecture</span>
        </div>
        
        {/* Portal Role Switcher */}
        <div className="tab-selector" style={{ backgroundColor: '#111827', padding: '4px', borderRadius: '8px' }}>
          <button
            className={`tab-btn ${userRole === 'doctor' ? 'active' : ''}`}
            onClick={() => setUserRole('doctor')}
            style={{
              backgroundColor: userRole === 'doctor' ? '#2563eb' : 'transparent',
              color: '#fff',
              fontWeight: 600
            }}
          >
            👨‍⚕️ Doctor Portal (STT & Clinical RAG)
          </button>
          <button
            className={`tab-btn ${userRole === 'patient' ? 'active' : ''}`}
            onClick={() => setUserRole('patient')}
            style={{
              backgroundColor: userRole === 'patient' ? '#10b981' : 'transparent',
              color: '#fff',
              fontWeight: 600
            }}
          >
            👤 Patient Portal (OCR & Timeline)
          </button>
        </div>
      </header>

      {/* Render Active Domain Portal */}
      {userRole === 'doctor' ? <DoctorPortal /> : <PatientPortal />}
    </div>
  );
}

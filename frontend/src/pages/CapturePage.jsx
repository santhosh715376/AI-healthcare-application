import React from 'react';
import DoctorPortal from './DoctorPortal.jsx';
import PatientPortal from './PatientPortal.jsx';

export default function CapturePage({ currentUser, onLogout }) {
  const userRole = currentUser?.role ? currentUser.role.toLowerCase() : 'doctor';

  return (
    <div className="app-container">
      {/* Global Header & Role Isolation Router */}
      <header className="app-header">
        <div className="brand">
          <span>🩺 Personalized Healthcare Platform</span>
          <span className="brand-badge">SQLite & Auth Active</span>
        </div>
        
        {/* Strict Role Isolation & Logout Header */}
        {currentUser ? (
          <div style={{ display: 'flex', alignItems: 'center', gap: '14px', fontSize: '0.85rem' }}>
            {/* Authenticated Role Badge */}
            <span style={{
              backgroundColor: currentUser.role === 'DOCTOR' ? '#1e3a8a' : '#065f46',
              border: `1px solid ${currentUser.role === 'DOCTOR' ? '#3b82f6' : '#10b981'}`,
              padding: '6px 14px',
              borderRadius: '20px',
              color: '#ffffff',
              fontWeight: 700,
              display: 'flex',
              alignItems: 'center',
              gap: '6px'
            }}>
              {currentUser.role === 'DOCTOR' 
                ? `👨‍⚕️ Dr. ${currentUser.name} (${currentUser.doc_license || 'NMC Verified'})` 
                : `👤 ${currentUser.name}`}
            </span>

            {/* Logout Button */}
            <button
              onClick={onLogout}
              style={{
                backgroundColor: '#dc2626',
                color: '#fff',
                border: 'none',
                padding: '6px 14px',
                borderRadius: '6px',
                fontWeight: 'bold',
                cursor: 'pointer',
                fontSize: '0.82rem',
                boxShadow: '0 2px 4px rgba(220, 38, 38, 0.4)'
              }}
            >
              🚪 Logout
            </button>
          </div>
        ) : (
          <div style={{ color: '#9ca3af', fontSize: '0.85rem' }}>
            Guest Session
          </div>
        )}
      </header>

      {/* Strict Role-Based Portal Workspace Rendering */}
      <main className="app-main">
        {userRole === 'doctor' ? (
          <DoctorPortal currentUser={currentUser} />
        ) : (
          <PatientPortal currentUser={currentUser} />
        )}
      </main>
    </div>
  );
}

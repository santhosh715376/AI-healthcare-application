import React from 'react';
import DoctorPortal from './DoctorPortal.jsx';
import PatientPortal from './PatientPortal.jsx';

export default function CapturePage({ currentUser, onLogout }) {
  const userRole = currentUser?.role ? currentUser.role.toLowerCase() : 'doctor';

  return (
    <div className="app-container" style={{ display: 'flex', flexDirection: 'column', height: '100vh', backgroundColor: '#0b0f17' }}>
      {/* Permanent Fixed Header with User Profile Badge & Logout Button */}
      <header className="app-header" style={{
        height: '60px',
        backgroundColor: '#111827',
        borderBottom: '1px solid #1f2937',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 24px',
        zIndex: 100
      }}>
        {/* Brand Title */}
        <div className="brand" style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span style={{ fontSize: '1.25rem', fontWeight: 700, color: '#ffffff' }}>🩺 Personalized Healthcare Platform</span>
          <span className="brand-badge" style={{
            backgroundColor: '#059669',
            color: '#ecfdf5',
            padding: '2px 8px',
            borderRadius: '4px',
            fontSize: '0.75rem',
            fontWeight: 600
          }}>
            SQLite Auth Active
          </span>
        </div>
        
        {/* Active Auth Session & Prominent Logout Button */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          {currentUser ? (
            <>
              {/* Role & Name Badge */}
              <div style={{
                backgroundColor: currentUser.role === 'DOCTOR' ? '#1e3a8a' : '#064e3b',
                border: `1px solid ${currentUser.role === 'DOCTOR' ? '#3b82f6' : '#10b981'}`,
                padding: '6px 14px',
                borderRadius: '20px',
                color: '#ffffff',
                fontWeight: 700,
                fontSize: '0.88rem',
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
              }}>
                {currentUser.role === 'DOCTOR' 
                  ? `👨‍⚕️ Dr. ${currentUser.name} (License: ${currentUser.doc_license || 'NMC Verified'})` 
                  : `👤 ${currentUser.name} (Phone: ${currentUser.phone || '9876543210'})`}
              </div>

              {/* Prominent Red Logout Button */}
              <button
                onClick={onLogout}
                style={{
                  backgroundColor: '#ef4444',
                  color: '#ffffff',
                  border: 'none',
                  padding: '8px 18px',
                  borderRadius: '8px',
                  fontWeight: 'bold',
                  cursor: 'pointer',
                  fontSize: '0.88rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  boxShadow: '0 4px 12px rgba(239, 68, 68, 0.4)',
                  transition: 'transform 0.1s ease-in-out'
                }}
              >
                🚪 Logout
              </button>
            </>
          ) : (
            <div style={{ color: '#9ca3af', fontSize: '0.85rem' }}>
              Guest Session
            </div>
          )}
        </div>
      </header>

      {/* Strict Role-Based Portal Workspace Rendering */}
      <main className="app-main" style={{ flex: 1, overflow: 'hidden' }}>
        {userRole === 'doctor' ? (
          <DoctorPortal currentUser={currentUser} />
        ) : (
          <PatientPortal currentUser={currentUser} />
        )}
      </main>
    </div>
  );
}

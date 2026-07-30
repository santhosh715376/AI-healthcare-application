import React, { useState } from 'react';

export default function AuthPage({ onLoginSuccess }) {
  const [roleTab, setRoleTab] = useState('DOCTOR'); // 'DOCTOR' | 'PATIENT'
  const [isSignup, setIsSignup] = useState(true);

  // Form State
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('9943953454');
  const [password, setPassword] = useState('');
  const [docLicense, setDocLicense] = useState('');
  const [hospitalName, setHospitalName] = useState('');

  // Login identifier (Email, Phone, or License)
  const [identifier, setIdentifier] = useState('');

  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMsg('');
    setLoading(true);

    const endpoint = isSignup ? '/api/auth/signup' : '/api/auth/login';
    const payload = isSignup
      ? {
          role: roleTab,
          name,
          email,
          phone,
          password,
          doc_license: roleTab === 'DOCTOR' ? docLicense : null,
          hospital_name: roleTab === 'DOCTOR' ? hospitalName : null,
        }
      : {
          identifier,
          password,
        };

    try {
      const res = await fetch(`http://localhost:8000${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Authentication failed');
      }

      // Save token and user object
      localStorage.setItem('access_token', data.access_token);
      localStorage.setItem('user_profile', JSON.stringify(data.user));

      if (onLoginSuccess) {
        onLoginSuccess(data.user);
      }
    } catch (err) {
      setErrorMsg(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      backgroundColor: '#0b0f17',
      color: '#f3f4f6',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '16px'
    }}>
      <div style={{
        width: '100%',
        maxWidth: '460px',
        maxHeight: '92vh',
        overflowY: 'auto',
        backgroundColor: '#111827',
        border: '1px solid #1f2937',
        borderRadius: '16px',
        padding: '24px 28px',
        boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.5)'
      }}>
        {/* Brand Header */}
        <div style={{ textAlign: 'center', marginBottom: '16px' }}>
          <div style={{ fontSize: '2rem', marginBottom: '4px' }}>🩺</div>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 'bold', color: '#fff' }}>
            Personalized Healthcare Platform
          </h2>
          <p style={{ fontSize: '0.8rem', color: '#9ca3af', marginTop: '2px' }}>
            {isSignup ? 'Create your medical account' : 'Sign in to access your portal'}
          </p>
        </div>

        {/* Role Selector Tabs */}
        <div style={{
          display: 'flex',
          backgroundColor: '#1f2937',
          padding: '4px',
          borderRadius: '10px',
          marginBottom: '16px'
        }}>
          <button
            type="button"
            onClick={() => { setRoleTab('DOCTOR'); setErrorMsg(''); }}
            style={{
              flex: 1,
              padding: '8px 12px',
              border: 'none',
              borderRadius: '8px',
              backgroundColor: roleTab === 'DOCTOR' ? '#2563eb' : 'transparent',
              color: '#fff',
              fontWeight: 600,
              fontSize: '0.85rem',
              cursor: 'pointer',
              transition: 'all 0.2s'
            }}
          >
            👨‍⚕️ Doctor Portal
          </button>
          <button
            type="button"
            onClick={() => { setRoleTab('PATIENT'); setErrorMsg(''); }}
            style={{
              flex: 1,
              padding: '8px 12px',
              border: 'none',
              borderRadius: '8px',
              backgroundColor: roleTab === 'PATIENT' ? '#10b981' : 'transparent',
              color: '#fff',
              fontWeight: 600,
              fontSize: '0.85rem',
              cursor: 'pointer',
              transition: 'all 0.2s'
            }}
          >
            👤 Patient Portal
          </button>
        </div>

        {errorMsg && (
          <div style={{
            backgroundColor: 'rgba(239, 68, 68, 0.15)',
            border: '1px solid #ef4444',
            color: '#fca5a5',
            padding: '8px 12px',
            borderRadius: '8px',
            fontSize: '0.82rem',
            marginBottom: '12px'
          }}>
            ⚠️ {errorMsg}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          {isSignup ? (
            <>
              {/* Full Name */}
              <div style={{ marginBottom: '12px' }}>
                <label style={{ display: 'block', fontSize: '0.78rem', color: '#9ca3af', marginBottom: '4px' }}>
                  {roleTab === 'DOCTOR' ? 'Doctor Full Name (e.g. Dr. Nithin)' : 'Patient Full Name'}
                </label>
                <input
                  type="text"
                  required
                  className="transcript-area"
                  style={{ height: '38px', fontSize: '0.88rem' }}
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder={roleTab === 'DOCTOR' ? 'Dr. Nithin Narayanan' : 'Santhosh Kumar'}
                />
              </div>

              {/* Email */}
              <div style={{ marginBottom: '12px' }}>
                <label style={{ display: 'block', fontSize: '0.78rem', color: '#9ca3af', marginBottom: '4px' }}>
                  Email Address
                </label>
                <input
                  type="email"
                  required
                  className="transcript-area"
                  style={{ height: '38px', fontSize: '0.88rem' }}
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@example.com"
                />
              </div>

              {/* Phone */}
              <div style={{ marginBottom: '12px' }}>
                <label style={{ display: 'block', fontSize: '0.78rem', color: '#9ca3af', marginBottom: '4px' }}>
                  Mobile Number (10 Digits)
                </label>
                <input
                  type="text"
                  required
                  className="transcript-area"
                  style={{ height: '38px', fontSize: '0.88rem' }}
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  placeholder="9943953454"
                />
              </div>

              {/* Doctor Specific Fields */}
              {roleTab === 'DOCTOR' && (
                <>
                  <div style={{ marginBottom: '12px' }}>
                    <label style={{ display: 'block', fontSize: '0.78rem', color: '#9ca3af', marginBottom: '4px' }}>
                      NMC Medical License ID
                    </label>
                    <input
                      type="text"
                      required
                      className="transcript-area"
                      style={{ height: '38px', fontSize: '0.88rem' }}
                      value={docLicense}
                      onChange={(e) => setDocLicense(e.target.value)}
                      placeholder="NMC-TN-88492"
                    />
                  </div>

                  <div style={{ marginBottom: '12px' }}>
                    <label style={{ display: 'block', fontSize: '0.78rem', color: '#9ca3af', marginBottom: '4px' }}>
                      Hospital / Clinic Name
                    </label>
                    <input
                      type="text"
                      required
                      className="transcript-area"
                      style={{ height: '38px', fontSize: '0.88rem' }}
                      value={hospitalName}
                      onChange={(e) => setHospitalName(e.target.value)}
                      placeholder="Coimbatore Health Centre"
                    />
                  </div>
                </>
              )}

              {/* Password */}
              <div style={{ marginBottom: '16px' }}>
                <label style={{ display: 'block', fontSize: '0.78rem', color: '#9ca3af', marginBottom: '4px' }}>
                  Password
                </label>
                <input
                  type="password"
                  required
                  className="transcript-area"
                  style={{ height: '38px', fontSize: '0.88rem' }}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                />
              </div>
            </>
          ) : (
            <>
              {/* Login Identifier */}
              <div style={{ marginBottom: '12px' }}>
                <label style={{ display: 'block', fontSize: '0.78rem', color: '#9ca3af', marginBottom: '4px' }}>
                  {roleTab === 'DOCTOR' ? 'Email, 10-digit Phone, or License ID' : 'Email or 10-digit Phone'}
                </label>
                <input
                  type="text"
                  required
                  className="transcript-area"
                  style={{ height: '38px', fontSize: '0.88rem' }}
                  value={identifier}
                  onChange={(e) => setIdentifier(e.target.value)}
                  placeholder={roleTab === 'DOCTOR' ? '9943953454 or NMC-TN-88492' : '9943953454 or email'}
                />
              </div>

              {/* Password */}
              <div style={{ marginBottom: '16px' }}>
                <label style={{ display: 'block', fontSize: '0.78rem', color: '#9ca3af', marginBottom: '4px' }}>
                  Password
                </label>
                <input
                  type="password"
                  required
                  className="transcript-area"
                  style={{ height: '38px', fontSize: '0.88rem' }}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                />
              </div>
            </>
          )}

          {/* Confirm Submit Button */}
          <button
            type="submit"
            disabled={loading}
            className="action-btn"
            style={{
              width: '100%',
              backgroundColor: roleTab === 'DOCTOR' ? '#2563eb' : '#10b981',
              color: '#ffffff',
              padding: '12px',
              borderRadius: '8px',
              fontSize: '0.92rem',
              fontWeight: 'bold',
              justifyContent: 'center',
              cursor: 'pointer',
              boxShadow: '0 4px 12px rgba(37, 99, 235, 0.3)',
              marginTop: '4px'
            }}
          >
            {loading ? 'Authenticating...' : isSignup ? `✅ Confirm Registration (${roleTab === 'DOCTOR' ? 'Doctor' : 'Patient'})` : `🔑 Sign In (${roleTab === 'DOCTOR' ? 'Doctor' : 'Patient'})`}
          </button>
        </form>

        {/* Toggle Signup / Login */}
        <div style={{ textAlign: 'center', marginTop: '16px', fontSize: '0.82rem', color: '#9ca3af' }}>
          {isSignup ? 'Already have an account?' : "Don't have an account yet?"}{' '}
          <button
            type="button"
            onClick={() => { setIsSignup(!isSignup); setErrorMsg(''); }}
            style={{
              background: 'none',
              border: 'none',
              color: roleTab === 'DOCTOR' ? '#60a5fa' : '#34d399',
              fontWeight: 'bold',
              cursor: 'pointer',
              textDecoration: 'underline'
            }}
          >
            {isSignup ? 'Sign In' : 'Register Now'}
          </button>
        </div>
      </div>
    </div>
  );
}

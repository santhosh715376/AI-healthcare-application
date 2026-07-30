import React, { useState } from 'react';

export default function AuthPage({ onLoginSuccess }) {
  const [roleTab, setRoleTab] = useState('PATIENT'); // 'DOCTOR' | 'PATIENT'
  const [isSignup, setIsSignup] = useState(false); // Always default to Login on page visit

  // Form State
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [countryCode, setCountryCode] = useState('+91');
  const [phone, setPhone] = useState('9943953454');
  const [password, setPassword] = useState('');
  const [docLicense, setDocLicense] = useState('');
  const [hospitalName, setHospitalName] = useState('');
  const [specialty, setSpecialty] = useState('General Medicine');

  // Clinical Vitals State
  const [age, setAge] = useState('24');
  const [gender, setGender] = useState('Male');
  const [heightCm, setHeightCm] = useState('175');
  const [weightKg, setWeightKg] = useState('68');
  const [bloodGroup, setBloodGroup] = useState('O+');

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
          country_code: countryCode,
          phone: phone.replace(/\D/g, ''),
          password,
          doc_license: roleTab === 'DOCTOR' ? docLicense : null,
          hospital_name: roleTab === 'DOCTOR' ? hospitalName : null,
          specialty: roleTab === 'DOCTOR' ? specialty : null,
          gender,
          age: parseInt(age) || 24,
          height_cm: parseFloat(heightCm) || 175.0,
          weight_kg: parseFloat(weightKg) || 68.0,
          blood_group: bloodGroup || 'O+',
        }
      : {
          identifier,
          password,
        };

    try {
      let res;
      try {
        res = await fetch(endpoint, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });
      } catch (e1) {
        res = await fetch(`http://127.0.0.1:8000${endpoint}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });
      }

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

              {/* Phone with Country Code Selector */}
              <div style={{ marginBottom: '12px' }}>
                <label style={{ display: 'block', fontSize: '0.78rem', color: '#9ca3af', marginBottom: '4px' }}>
                  Mobile Number (Country Code & 10 Digits)
                </label>
                <div style={{ display: 'flex', gap: '8px' }}>
                  <select
                    style={{
                      width: '100px',
                      height: '38px',
                      padding: '0 8px',
                      fontSize: '0.85rem',
                      backgroundColor: '#111827',
                      color: '#ffffff',
                      border: '1px solid #374151',
                      borderRadius: '8px',
                      outline: 'none',
                      cursor: 'pointer'
                    }}
                    value={countryCode}
                    onChange={(e) => setCountryCode(e.target.value)}
                  >
                    <option value="+91">🇮🇳 +91</option>
                    <option value="+1">🇺🇸 +1</option>
                    <option value="+44">🇬🇧 +44</option>
                    <option value="+971">🇦🇪 +971</option>
                    <option value="+65">🇸🇬 +65</option>
                  </select>
                  <input
                    type="text"
                    required
                    className="transcript-area"
                    style={{ flex: 1, height: '38px', fontSize: '0.88rem' }}
                    value={phone}
                    onChange={(e) => setPhone(e.target.value.replace(/\D/g, '').slice(0, 10))}
                    placeholder="9943953454"
                  />
                </div>
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

                  <div style={{ marginBottom: '12px' }}>
                    <label style={{ display: 'block', fontSize: '0.78rem', color: '#9ca3af', marginBottom: '4px' }}>
                      Medical Specialty / Department
                    </label>
                    <select
                      style={{
                        width: '100%',
                        height: '40px',
                        padding: '0 12px',
                        fontSize: '0.88rem',
                        lineHeight: '40px',
                        backgroundColor: '#111827',
                        color: '#ffffff',
                        border: '1px solid #374151',
                        borderRadius: '8px',
                        outline: 'none',
                        cursor: 'pointer'
                      }}
                      value={specialty}
                      onChange={(e) => setSpecialty(e.target.value)}
                    >
                      <option value="General Medicine" style={{ backgroundColor: '#1f2937', color: '#ffffff' }}>General Medicine</option>
                      <option value="Cardiology" style={{ backgroundColor: '#1f2937', color: '#ffffff' }}>Cardiology</option>
                      <option value="Pediatrics" style={{ backgroundColor: '#1f2937', color: '#ffffff' }}>Pediatrics</option>
                      <option value="Orthopedics & Trauma" style={{ backgroundColor: '#1f2937', color: '#ffffff' }}>Orthopedics & Trauma</option>
                      <option value="Neurology & Neurosurgery" style={{ backgroundColor: '#1f2937', color: '#ffffff' }}>Neurology & Neurosurgery</option>
                      <option value="Oncology" style={{ backgroundColor: '#1f2937', color: '#ffffff' }}>Oncology</option>
                      <option value="Nephrology & Urology" style={{ backgroundColor: '#1f2937', color: '#ffffff' }}>Nephrology & Urology</option>
                      <option value="Obstetrics & Gynecology" style={{ backgroundColor: '#1f2937', color: '#ffffff' }}>Obstetrics & Gynecology</option>
                      <option value="Dermatology" style={{ backgroundColor: '#1f2937', color: '#ffffff' }}>Dermatology</option>
                    </select>
                  </div>
                </>
              )}

              {/* Gender (Common to Doctor & Patient) */}
              <div style={{ marginBottom: '12px' }}>
                <label style={{ display: 'block', fontSize: '0.78rem', color: '#9ca3af', marginBottom: '4px' }}>
                  Gender
                </label>
                <select
                  style={{
                    width: '100%',
                    height: '40px',
                    padding: '0 12px',
                    fontSize: '0.88rem',
                    backgroundColor: '#111827',
                    color: '#ffffff',
                    border: '1px solid #374151',
                    borderRadius: '8px',
                    outline: 'none'
                  }}
                  value={gender}
                  onChange={(e) => setGender(e.target.value)}
                >
                  <option value="Male">Male</option>
                  <option value="Female">Female</option>
                  <option value="Other">Other</option>
                </select>
              </div>

              {/* Physical Vitals (Common to Doctor & Patient) */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', marginBottom: '12px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.78rem', color: '#9ca3af', marginBottom: '4px' }}>
                    Age (Years)
                  </label>
                  <input
                    type="number"
                    required
                    className="transcript-area"
                    style={{ height: '38px', fontSize: '0.88rem' }}
                    value={age}
                    onChange={(e) => setAge(e.target.value)}
                    placeholder="24"
                  />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '0.78rem', color: '#9ca3af', marginBottom: '4px' }}>
                    Blood Group
                  </label>
                  <select
                    style={{
                      width: '100%',
                      height: '38px',
                      padding: '0 8px',
                      fontSize: '0.88rem',
                      backgroundColor: '#111827',
                      color: '#ffffff',
                      border: '1px solid #374151',
                      borderRadius: '8px'
                    }}
                    value={bloodGroup}
                    onChange={(e) => setBloodGroup(e.target.value)}
                  >
                    <option value="O+">O+</option>
                    <option value="A+">A+</option>
                    <option value="B+">B+</option>
                    <option value="AB+">AB+</option>
                    <option value="O-">O-</option>
                    <option value="A-">A-</option>
                    <option value="B-">B-</option>
                    <option value="AB-">AB-</option>
                  </select>
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', marginBottom: '12px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.78rem', color: '#9ca3af', marginBottom: '4px' }}>
                    Height (cm)
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    required
                    className="transcript-area"
                    style={{ height: '38px', fontSize: '0.88rem' }}
                    value={heightCm}
                    onChange={(e) => setHeightCm(e.target.value)}
                    placeholder="175"
                  />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '0.78rem', color: '#9ca3af', marginBottom: '4px' }}>
                    Weight (kg)
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    required
                    className="transcript-area"
                    style={{ height: '38px', fontSize: '0.88rem' }}
                    value={weightKg}
                    onChange={(e) => setWeightKg(e.target.value)}
                    placeholder="68"
                  />
                </div>
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

import React, { useState, useEffect } from 'react';

export default function PatientAdherencePanel({ user, onSignOut }) {
  const patientPhone = String(user?.phone_number || user?.phone || '9943953454');
  const patientName = user?.name || 'Santhosh M';
  const patientId = user?.id || 100001;

  const [vitals, setVitals] = useState({
    age: user?.age || 24,
    gender: user?.gender || 'Male',
    height_cm: user?.height_cm || 175.0,
    weight_kg: user?.weight_kg || 68.0,
    blood_group: user?.blood_group || 'O+'
  });

  const [adherenceData, setAdherenceData] = useState({
    overall_percentage: 100,
    total_taken: 0,
    total_expected: 0,
    slots: {
      morning: [],
      noon: [],
      night: []
    }
  });

  const [alarmMsg, setAlarmMsg] = useState('');

  const fetchAdherenceData = () => {
    const cleanPhone = String(user?.id || patientPhone).replace(/\D/g, '') || '100001';
    fetch(`http://localhost:8000/api/adherence/patient/${cleanPhone}`)
      .then(res => res.ok ? res.json() : null)
      .then(data => {
        if (data && data.slots) {
          setAdherenceData({
            overall_percentage: data.master_adherence_pct,
            total_taken: data.total_taken,
            total_expected: data.total_expected,
            slots: data.slots
          });
        }
      })
      .catch(err => console.warn('Could not fetch adherence schedules:', err));
  };

  useEffect(() => {
    if (!patientPhone) return;
    const cleanPhone = String(patientPhone).replace(/\D/g, '') || '9943953454';
    fetch(`http://localhost:8000/api/patient/profile?phone=${encodeURIComponent(cleanPhone)}`)
      .then(res => res.ok ? res.json() : null)
      .then(data => {
        if (data && data.age) {
          setVitals({
            age: data.age || 24,
            gender: data.gender || 'Male',
            height_cm: data.height_cm || 175.0,
            weight_kg: data.weight_kg || 68.0,
            blood_group: data.blood_group || 'O+'
          });
        }
      })
      .catch(err => console.warn('Could not fetch patient vitals:', err));

    fetchAdherenceData();
  }, [patientPhone]);

  // Periodic 15-minute Alarm / Notification Check for Active Window Due Medicines
  useEffect(() => {
    const checkActiveWindowAlarms = () => {
      const now = new Date();
      const currentMin = now.getHours() * 60 + now.getMinutes();

      let activeDueCount = 0;
      let nextDueMed = '';

      Object.values(adherenceData.slots).forEach(slotItems => {
        slotItems.forEach(item => {
          if (item.status === 'DUE') {
            const [sH, sM] = (item.slot_start_time || '08:00').split(':').map(Number);
            const [eH, eM] = (item.slot_end_time || '08:30').split(':').map(Number);
            const sMin = sH * 60 + sM;
            const eMin = eH * 60 + eM;

            if (currentMin >= sMin && currentMin <= eMin) {
              activeDueCount++;
              nextDueMed = item.medication_name;
            }
          }
        });
      });

      if (activeDueCount > 0) {
        setAlarmMsg(`⏰ REMINDER ALARM: ${nextDueMed} is DUE NOW! Please check in before window ends.`);
      } else {
        setAlarmMsg('');
      }
    };

    checkActiveWindowAlarms();
    const interval = setInterval(checkActiveWindowAlarms, 60000); // Check every minute
    return () => clearInterval(interval);
  }, [adherenceData]);

  // Time-Window Restriction Logic
  const checkTimeWindowStatus = (startStr, endStr) => {
    if (!startStr || !endStr) return { active: true, label: 'Active Window' };

    const now = new Date();
    const currentMin = now.getHours() * 60 + now.getMinutes();

    const [sH, sM] = startStr.split(':').map(Number);
    const [eH, eM] = endStr.split(':').map(Number);
    const startMin = sH * 60 + sM;
    const endMin = eH * 60 + eM;

    if (currentMin < startMin) {
      return { active: false, label: `🔒 Unlocks at ${startStr}` };
    }
    if (currentMin > endMin) {
      return { active: false, label: `⌛ Window Expired (${endStr})` };
    }
    return { active: true, label: '💊 Check-In Dose' };
  };

  const handleCheckIn = async (item) => {
    try {
      const res = await fetch('http://localhost:8000/api/adherence/checkin', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          schedule_id: item.schedule_id,
          patient_id: patientId,
          scheduled_date: item.scheduled_date || new Date().toISOString().split('T')[0],
          routine_slot: item.routine_slot
        })
      });

      if (res.ok) {
        fetchAdherenceData(); // Re-sync SQLite adherence state
      }
    } catch (e) {
      console.error('Check-in failed:', e);
    }
  };

  // Helper for Circular SVG Ring
  const renderSvgRing = (percentage, size = 110, stroke = 9) => {
    const radius = (size - stroke) / 2;
    const circ = 2 * Math.PI * radius;
    const offset = circ - (percentage / 100) * circ;
    const color = percentage >= 80 ? '#10b981' : percentage >= 40 ? '#3b82f6' : '#f59e0b';

    return (
      <svg width={size} height={size} style={{ transform: 'rotate(-90deg)' }}>
        <circle cx={size / 2} cy={size / 2} r={radius} stroke="#262626" strokeWidth={stroke} fill="transparent" />
        <circle
          cx={size / 2} cy={size / 2} r={radius}
          stroke={color} strokeWidth={stroke} fill="transparent"
          strokeDasharray={circ} strokeDashoffset={offset}
          strokeLinecap="round"
          style={{ transition: 'stroke-dashoffset 0.6s ease-in-out' }}
        />
        <text
          x={size / 2} y={-(size / 2) + 6}
          textAnchor="middle" fill="#ffffff" fontSize="16" fontWeight="700"
          style={{ transform: 'rotate(90deg)', fontFamily: 'Inter, sans-serif' }}
        >
          {percentage}%
        </text>
      </svg>
    );
  };

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '300px 1fr', gap: '24px', padding: '24px', backgroundColor: '#0f0f0f', color: '#f3f4f6', minHeight: '100vh', fontFamily: 'Inter, sans-serif' }}>
      
      {/* LEFT SIDEBAR: PROFILE & CLINICAL VITALS */}
      <div style={{ backgroundColor: '#181818', borderRadius: '12px', border: '1px solid #2e2e2e', padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
        
        {/* Avatar & Basic Info */}
        <div style={{ textAlign: 'center' }}>
          <div style={{ width: '96px', height: '96px', borderRadius: '50%', backgroundColor: '#262626', margin: '0 auto 12px', border: '3px solid #10b981', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '2.5rem' }}>
            👤
          </div>
          <h2 style={{ fontSize: '1.25rem', fontWeight: '700', color: '#fff', marginBottom: '2px' }}>{patientName}</h2>
          <p style={{ fontSize: '0.8rem', color: '#9ca3af', marginBottom: '8px' }}>@{user?.email ? user.email.split('@')[0] : 'patient'}</p>
          
          <div style={{ display: 'flex', justifyContent: 'center', gap: '6px' }}>
            <span style={{ backgroundColor: '#065f46', color: '#34d399', fontSize: '0.72rem', padding: '2px 8px', borderRadius: '12px', fontWeight: '600' }}>PATIENT</span>
            <span style={{ backgroundColor: '#1f2937', color: '#9ca3af', fontSize: '0.72rem', padding: '2px 8px', borderRadius: '12px' }}>#PAT-{user?.id || '100001'}</span>
          </div>
        </div>

        <div style={{ borderTop: '1px solid #2e2e2e', paddingTop: '16px' }}>
          <h3 style={{ fontSize: '0.85rem', fontWeight: '700', color: '#9ca3af', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '12px' }}>
            CLINICAL VITALS
          </h3>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
            <div style={{ backgroundColor: '#222', padding: '10px', borderRadius: '8px', border: '1px solid #2e2e2e' }}>
              <span style={{ fontSize: '0.7rem', color: '#9ca3af' }}>Age</span>
              <p style={{ fontSize: '0.95rem', fontWeight: '700', color: '#fff' }}>{vitals.age} Yrs</p>
            </div>
            <div style={{ backgroundColor: '#222', padding: '10px', borderRadius: '8px', border: '1px solid #2e2e2e' }}>
              <span style={{ fontSize: '0.7rem', color: '#9ca3af' }}>Gender</span>
              <p style={{ fontSize: '0.95rem', fontWeight: '700', color: '#fff' }}>{vitals.gender}</p>
            </div>
            <div style={{ backgroundColor: '#222', padding: '10px', borderRadius: '8px', border: '1px solid #2e2e2e' }}>
              <span style={{ fontSize: '0.7rem', color: '#9ca3af' }}>Height</span>
              <p style={{ fontSize: '0.95rem', fontWeight: '700', color: '#fff' }}>{vitals.height_cm} cm</p>
            </div>
            <div style={{ backgroundColor: '#222', padding: '10px', borderRadius: '8px', border: '1px solid #2e2e2e' }}>
              <span style={{ fontSize: '0.7rem', color: '#9ca3af' }}>Weight</span>
              <p style={{ fontSize: '0.95rem', fontWeight: '700', color: '#fff' }}>{vitals.weight_kg} kg</p>
            </div>
          </div>

          <div style={{ backgroundColor: '#222', padding: '10px', borderRadius: '8px', border: '1px solid #2e2e2e', marginTop: '10px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.75rem', color: '#9ca3af' }}>Blood Group</span>
            <span style={{ backgroundColor: '#991b1b', color: '#fca5a5', padding: '2px 8px', borderRadius: '4px', fontWeight: '700', fontSize: '0.85rem' }}>{vitals.blood_group}</span>
          </div>
        </div>

      </div>

      {/* RIGHT MAIN PANEL */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
        
        {/* Periodic Alarm Banner */}
        {alarmMsg && (
          <div style={{ backgroundColor: '#7f1d1d', border: '1px solid #f87171', color: '#fff', padding: '12px 16px', borderRadius: '8px', fontWeight: '600', fontSize: '0.88rem', display: 'flex', alignItems: 'center', gap: '10px', animation: 'pulse 1.5s infinite' }}>
            {alarmMsg}
          </div>
        )}

        {/* SECTION 1: MASTER RECOVERY PROGRESS RINGS */}
        <div style={{ backgroundColor: '#181818', borderRadius: '12px', border: '1px solid #2e2e2e', padding: '20px' }}>
          <h3 style={{ fontSize: '0.95rem', fontWeight: '700', color: '#fff', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            📌 Pinned Recovery Progress Rings
          </h3>

          <div style={{ display: 'flex', gap: '30px', alignItems: 'center' }}>
            <div style={{ backgroundColor: '#222', padding: '16px', borderRadius: '12px', border: '1px solid #2e2e2e', textAlign: 'center', minWidth: '160px' }}>
              <p style={{ fontSize: '0.78rem', color: '#9ca3af', marginBottom: '8px' }}>Master Adherence</p>
              {renderSvgRing(adherenceData.overall_percentage, 110, 9)}
              <p style={{ fontSize: '0.75rem', color: '#34d399', marginTop: '8px', fontWeight: '600' }}>
                {adherenceData.total_taken} / {adherenceData.total_expected} Doses Verified
              </p>
            </div>
          </div>
        </div>

        {/* SECTION 2: DAILY MEDICINE ROUTINE COCKPIT */}
        <div style={{ backgroundColor: '#181818', borderRadius: '12px', border: '1px solid #2e2e2e', padding: '20px' }}>
          <h3 style={{ fontSize: '0.95rem', fontWeight: '700', color: '#fff', marginBottom: '16px' }}>
            🌅 Today's Prescribed Medicine Check-In Cockpit
          </h3>

          {Object.entries(adherenceData.slots).map(([slotKey, items]) => (
            <div key={slotKey} style={{ marginBottom: '20px' }}>
              <h4 style={{ fontSize: '0.82rem', fontWeight: '700', color: '#9ca3af', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '10px' }}>
                {slotKey === 'morning' ? '🌅 Morning Slot' : slotKey === 'noon' ? '☀️ Noon Slot' : '🌙 Night Slot'}
              </h4>

              {items.length === 0 ? (
                <div style={{ fontSize: '0.8rem', color: '#6b7280', padding: '10px', backgroundColor: '#141414', borderRadius: '6px', fontStyle: 'italic' }}>
                  No scheduled doses configured for this slot. Click "💖 Click to Heal" in My Medical Records Timeline to schedule.
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                  {items.map((item, idx) => {
                    const winStatus = checkTimeWindowStatus(item.slot_start_time, item.slot_end_time);

                    return (
                      <div key={idx} style={{ backgroundColor: '#222', padding: '14px 18px', borderRadius: '8px', border: '1px solid #2e2e2e', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <div>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                            <span style={{ fontSize: '0.95rem', fontWeight: '700', color: '#fff' }}>💊 {item.medication_name}</span>
                            <span style={{ backgroundColor: '#374151', color: '#d1d5db', fontSize: '0.72rem', padding: '2px 6px', borderRadius: '4px' }}>{item.food_relation}</span>
                          </div>
                          <p style={{ fontSize: '0.75rem', color: '#9ca3af', marginTop: '4px' }}>
                            {item.doctor_name} ({item.visit_date}) • Window: <strong style={{ color: '#38bdf8' }}>{item.slot_start_time} - {item.slot_end_time}</strong>
                          </p>
                        </div>

                        {item.status === 'TAKEN' ? (
                          <span style={{ backgroundColor: '#065f46', color: '#34d399', padding: '6px 14px', borderRadius: '6px', fontSize: '0.82rem', fontWeight: '600' }}>✓ TAKEN</span>
                        ) : (
                          <button
                            onClick={() => handleCheckIn(item)}
                            disabled={!winStatus.active}
                            style={{
                              backgroundColor: winStatus.active ? '#ec4899' : '#374151',
                              color: winStatus.active ? '#ffffff' : '#9ca3af',
                              border: 'none',
                              padding: '8px 16px',
                              borderRadius: '6px',
                              fontSize: '0.82rem',
                              fontWeight: '600',
                              cursor: winStatus.active ? 'pointer' : 'not-allowed',
                              boxShadow: winStatus.active ? '0 2px 8px rgba(236,72,153,0.4)' : 'none'
                            }}
                          >
                            {winStatus.label}
                          </button>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          ))}
        </div>

        {/* SECTION 3: 30-DAY ADHERENCE STREAK HEATMAP */}
        <div style={{ backgroundColor: '#181818', borderRadius: '12px', border: '1px solid #2e2e2e', padding: '20px' }}>
          <h3 style={{ fontSize: '0.95rem', fontWeight: '700', color: '#fff', marginBottom: '12px' }}>
            📊 30-Day Verified Adherence Streak Heatmap
          </h3>
          <p style={{ fontSize: '0.75rem', color: '#9ca3af', marginBottom: '12px' }}>Green dots indicate days with 100% verified medicine check-ins.</p>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(15, 1fr)', gap: '6px' }}>
            {Array.from({ length: 30 }).map((_, i) => (
              <div
                key={i}
                title={`Day ${i + 1}: 100% Verified Adherence`}
                style={{
                  height: '24px',
                  backgroundColor: (adherenceData.total_taken > 0 && i < adherenceData.total_taken) ? '#10b981' : (adherenceData.total_expected > 0 && i === adherenceData.total_taken) ? '#3b82f6' : '#262626',
                  borderRadius: '4px',
                  border: '1px solid #333'
                }}
              />
            ))}
          </div>
        </div>

      </div>
    </div>
  );
}

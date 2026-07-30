import React, { useState } from 'react';

export default function PrescriptionTimelineCard({ prescription, patientId, onScheduleSaved }) {
  const { id: rxId, date, time, index, visitSummary, header, body, tail, source } = prescription;

  const doctorName = header?.doctorName || 'Dr. Prescribing Doctor';
  const hospitalName = header?.hospitalName || 'Coimbatore Health Centre';
  const opdContact = header?.opdContact || '';
  const medications = body?.medications || [];

  // Modal State
  const [selectedMed, setSelectedMed] = useState(null);
  const [foodRelation, setFoodRelation] = useState('After Food');
  const [durationDays, setDurationDays] = useState(5);
  const [morningSlot, setMorningSlot] = useState({ enabled: true, start: '08:00', end: '08:30' });
  const [noonSlot, setNoonSlot] = useState({ enabled: false, start: '13:30', end: '14:00' });
  const [nightSlot, setNightSlot] = useState({ enabled: false, start: '20:30', end: '21:00' });
  const [submitting, setSubmitting] = useState(false);
  const [msg, setMsg] = useState('');

  const openClickToHealModal = (med) => {
    setSelectedMed(med);
    setMsg('');
    const rel = med.foodRelation || 'After Food';
    setFoodRelation(rel);
    
    // Auto-detect slots based on frequency
    const freq = (med.frequency || '').toUpperCase();
    if (freq.includes('TDS') || freq.includes('Q8H') || freq.includes('3')) {
      setMorningSlot({ enabled: true, start: rel === 'Before Food' ? '07:30' : '08:00', end: rel === 'Before Food' ? '08:00' : '08:30' });
      setNoonSlot({ enabled: true, start: rel === 'Before Food' ? '13:00' : '13:30', end: rel === 'Before Food' ? '13:30' : '14:00' });
      setNightSlot({ enabled: true, start: rel === 'Before Food' ? '20:00' : '20:30', end: rel === 'Before Food' ? '20:30' : '21:00' });
    } else if (freq.includes('BD') || freq.includes('Q12H') || freq.includes('2')) {
      setMorningSlot({ enabled: true, start: rel === 'Before Food' ? '07:30' : '08:00', end: rel === 'Before Food' ? '08:00' : '08:30' });
      setNoonSlot({ enabled: false, start: '13:30', end: '14:00' });
      setNightSlot({ enabled: true, start: rel === 'Before Food' ? '20:00' : '20:30', end: rel === 'Before Food' ? '20:30' : '21:00' });
    } else {
      setMorningSlot({ enabled: true, start: rel === 'Before Food' ? '07:30' : '08:00', end: rel === 'Before Food' ? '08:00' : '08:30' });
      setNoonSlot({ enabled: false, start: '13:30', end: '14:00' });
      setNightSlot({ enabled: false, start: '20:30', end: '21:00' });
    }
  };

  const getDayCycleBadge = (freq) => {
    const f = (freq || '').toUpperCase();
    if (f.includes('TDS') || f.includes('3')) return '🌅 Morn | ☀️ Noon | 🌙 Night';
    if (f.includes('BD') || f.includes('2')) return '🌅 Morn | 🌙 Night';
    return '🌅 Morning';
  };

  const handleSaveSchedule = async () => {
    if (!selectedMed) return;
    setSubmitting(true);
    setMsg('');

    const activeSlots = [];
    if (morningSlot.enabled) activeSlots.push({ routine_slot: 'morning', slot_start_time: morningSlot.start, slot_end_time: morningSlot.end });
    if (noonSlot.enabled) activeSlots.push({ routine_slot: 'noon', slot_start_time: noonSlot.start, slot_end_time: noonSlot.end });
    if (nightSlot.enabled) activeSlots.push({ routine_slot: 'night', slot_start_time: nightSlot.start, slot_end_time: nightSlot.end });

    if (activeSlots.length === 0) {
      setMsg('Please select at least one day cycle routine slot (Morning, Noon, or Night).');
      setSubmitting(false);
      return;
    }

    try {
      const savedUser = JSON.parse(localStorage.getItem('healthcare_user') || '{}');
      const activePatId = patientId || savedUser?.id || savedUser?.phone || '901514';
      const patIdClean = parseInt(String(activePatId).replace(/\D/g, '')) || 901514;
      const payloadBody = JSON.stringify({
        prescription_id: rxId || `rx-${index}`,
        patient_id: patIdClean,
        medication_name: selectedMed.name,
        dosage: selectedMed.dosage,
        food_relation: foodRelation,
        duration_days: durationDays,
        slots: activeSlots
      });

      let res;
      try {
        res = await fetch('/api/adherence/schedule', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: payloadBody
        });
      } catch (e1) {
        res = await fetch('http://127.0.0.1:8000/api/adherence/schedule', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: payloadBody
        });
      }

      const data = await res.json();
      if (res.ok) {
        setMsg('✅ Schedule saved & alarms set successfully!');
        setTimeout(() => {
          setSelectedMed(null);
          if (onScheduleSaved) onScheduleSaved();
        }, 1200);
      } else {
        setMsg(`❌ ${data.detail || 'Failed to save schedule.'}`);
      }
    } catch (e) {
      setMsg(`❌ Error: ${e.message}`);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="timeline-card-dark" id={`rx-card-${index}`} style={{ backgroundColor: '#14171f', borderRadius: '12px', border: '1px solid #232936', padding: '20px', marginBottom: '20px' }}>
      {/* Top Header */}
      <div className="timeline-card-top-row" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <div className="timeline-card-title" style={{ color: '#38bdf8', fontWeight: '700', fontSize: '1rem' }}>
            {time} – {date} – Entry #{String(index).padStart(2, '0')}
          </div>
          <div className="timeline-card-meta" style={{ color: '#9ca3af', fontSize: '0.82rem', marginTop: '4px', display: 'flex', gap: '16px' }}>
            <span>🏥 {hospitalName} {opdContact && `(${opdContact})`}</span>
            <span>👨‍⚕️ {doctorName}</span>
          </div>
        </div>
        <span className="timeline-badge-tag" style={{ backgroundColor: '#1e293b', color: '#38bdf8', border: '1px solid #334155', padding: '4px 10px', borderRadius: '6px', fontSize: '0.75rem', fontWeight: '600' }}>
          {source || 'PATIENT_OCR'}
        </span>
      </div>

      <div style={{ borderTop: '1px solid #232936', margin: '14px 0' }} />

      {/* Visit Summary */}
      <div className="timeline-visit-quote" style={{ backgroundColor: '#1a2234', borderLeft: '4px solid #10b981', padding: '10px 14px', borderRadius: '0 8px 8px 0', color: '#e2e8f0', fontSize: '0.88rem', marginBottom: '16px' }}>
        📝 <strong>Visit Summary:</strong> {visitSummary}
      </div>

      {/* Medication Table with DAY CYCLE and CLICK TO HEAL Column */}
      {medications.length > 0 && (
        <table className="timeline-table-dark" style={{ width: '100%', borderCollapse: 'collapse', color: '#e2e8f0', fontSize: '0.85rem' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid #232936', color: '#9ca3af', textAlign: 'left' }}>
              <th style={{ padding: '8px' }}>Medicine</th>
              <th style={{ padding: '8px' }}>Dosage</th>
              <th style={{ padding: '8px' }}>Frequency</th>
              <th style={{ padding: '8px' }}>Day Cycle</th>
              <th style={{ padding: '8px' }}>Duration</th>
              <th style={{ padding: '8px' }}>Relation</th>
              <th style={{ padding: '8px', textAlign: 'center' }}>Action</th>
            </tr>
          </thead>
          <tbody>
            {medications.map((med, mIdx) => (
              <tr key={mIdx} style={{ borderBottom: '1px solid #1e2430' }}>
                <td style={{ padding: '10px 8px', fontWeight: '600', color: '#fff' }}>{med.name}</td>
                <td style={{ padding: '10px 8px' }}>{med.dosage}</td>
                <td style={{ padding: '10px 8px' }}>
                  <span style={{ backgroundColor: '#1e293b', color: '#60a5fa', padding: '2px 6px', borderRadius: '4px', fontSize: '0.75rem', fontWeight: '600' }}>{med.frequency}</span>
                </td>
                <td style={{ padding: '10px 8px', color: '#fbbf24', fontSize: '0.78rem' }}>
                  {getDayCycleBadge(med.frequency)}
                </td>
                <td style={{ padding: '10px 8px' }}>{med.duration || '5d'}</td>
                <td style={{ padding: '10px 8px' }}>{med.foodRelation || 'After Food'}</td>
                <td style={{ padding: '10px 8px', textAlign: 'center' }}>
                  <button
                    onClick={() => openClickToHealModal(med)}
                    style={{ backgroundColor: '#ec4899', color: '#fff', border: 'none', padding: '5px 12px', borderRadius: '20px', fontWeight: '600', fontSize: '0.76rem', cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: '4px', boxShadow: '0 2px 8px rgba(236,72,153,0.3)' }}
                  >
                    💖 Click to Heal
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {/* Tail Advice */}
      {tail?.advice && (
        <div style={{ marginTop: '14px', fontSize: '0.85rem', color: '#9ca3af' }}>
          💡 <strong>Advice:</strong> {tail.advice} {tail.followUpDate && `(Follow up: ${tail.followUpDate})`}
        </div>
      )}

      {/* CLICK TO HEAL INTERACTIVE TIMING SELECTION MODAL */}
      {selectedMed && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, backgroundColor: 'rgba(0,0,0,0.75)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 9999 }}>
          <div style={{ backgroundColor: '#18181b', border: '1px solid #27272a', borderRadius: '16px', padding: '24px', width: '480px', maxWidth: '90%', color: '#fff', boxShadow: '0 20px 25px -5px rgba(0,0,0,0.5)' }}>
            
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <h3 style={{ fontSize: '1.1rem', fontWeight: '700', color: '#ec4899', margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
                💖 Click to Heal: Schedule Reminders
              </h3>
              <button onClick={() => setSelectedMed(null)} style={{ backgroundColor: 'transparent', border: 'none', color: '#9ca3af', fontSize: '1.2rem', cursor: 'pointer' }}>✕</button>
            </div>

            <div style={{ backgroundColor: '#27272a', padding: '12px', borderRadius: '8px', marginBottom: '16px', fontSize: '0.85rem' }}>
              <div><strong>Medicine:</strong> <span style={{ color: '#60a5fa' }}>{selectedMed.name}</span> ({selectedMed.dosage})</div>
              <div><strong>Prescribed Frequency:</strong> {selectedMed.frequency} | {selectedMed.foodRelation || 'After Food'}</div>
            </div>

            {/* Food Relation Selection */}
            <div style={{ marginBottom: '14px' }}>
              <label style={{ fontSize: '0.8rem', color: '#9ca3af', display: 'block', marginBottom: '6px' }}>FOOD RELATION</label>
              <select
                value={foodRelation}
                onChange={(e) => setFoodRelation(e.target.value)}
                style={{ width: '100%', backgroundColor: '#09090b', border: '1px solid #3f3f46', color: '#fff', padding: '8px', borderRadius: '6px', fontSize: '0.85rem' }}
              >
                <option value="After Food">After Food (e.g. Breakfast, Lunch, Dinner)</option>
                <option value="Before Food">Before Food (30 mins prior to meals)</option>
                <option value="With Food">With Food / During Meal</option>
              </select>
            </div>

            {/* Routine Day Slots Selection */}
            <div style={{ marginBottom: '16px' }}>
              <label style={{ fontSize: '0.8rem', color: '#9ca3af', display: 'block', marginBottom: '8px' }}>DAY CYCLE TIMING WINDOWS (AM / PM)</label>
              
              {/* MORNING */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', backgroundColor: '#09090b', padding: '8px 12px', borderRadius: '6px', marginBottom: '8px' }}>
                <input
                  type="checkbox"
                  checked={morningSlot.enabled}
                  onChange={(e) => setMorningSlot({ ...morningSlot, enabled: e.target.checked })}
                />
                <span style={{ fontSize: '0.82rem', width: '90px', color: '#f59e0b' }}>🌅 Morning</span>
                <input
                  type="time"
                  value={morningSlot.start}
                  onChange={(e) => setMorningSlot({ ...morningSlot, start: e.target.value })}
                  style={{ backgroundColor: '#18181b', border: '1px solid #3f3f46', color: '#fff', padding: '4px', borderRadius: '4px', fontSize: '0.8rem' }}
                />
                <span style={{ fontSize: '0.78rem', color: '#71717a' }}>to</span>
                <input
                  type="time"
                  value={morningSlot.end}
                  onChange={(e) => setMorningSlot({ ...morningSlot, end: e.target.value })}
                  style={{ backgroundColor: '#18181b', border: '1px solid #3f3f46', color: '#fff', padding: '4px', borderRadius: '4px', fontSize: '0.8rem' }}
                />
              </div>

              {/* NOON */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', backgroundColor: '#09090b', padding: '8px 12px', borderRadius: '6px', marginBottom: '8px' }}>
                <input
                  type="checkbox"
                  checked={noonSlot.enabled}
                  onChange={(e) => setNoonSlot({ ...noonSlot, enabled: e.target.checked })}
                />
                <span style={{ fontSize: '0.82rem', width: '90px', color: '#38bdf8' }}>☀️ Noon</span>
                <input
                  type="time"
                  value={noonSlot.start}
                  onChange={(e) => setNoonSlot({ ...noonSlot, start: e.target.value })}
                  style={{ backgroundColor: '#18181b', border: '1px solid #3f3f46', color: '#fff', padding: '4px', borderRadius: '4px', fontSize: '0.8rem' }}
                />
                <span style={{ fontSize: '0.78rem', color: '#71717a' }}>to</span>
                <input
                  type="time"
                  value={noonSlot.end}
                  onChange={(e) => setNoonSlot({ ...noonSlot, end: e.target.value })}
                  style={{ backgroundColor: '#18181b', border: '1px solid #3f3f46', color: '#fff', padding: '4px', borderRadius: '4px', fontSize: '0.8rem' }}
                />
              </div>

              {/* NIGHT */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', backgroundColor: '#09090b', padding: '8px 12px', borderRadius: '6px' }}>
                <input
                  type="checkbox"
                  checked={nightSlot.enabled}
                  onChange={(e) => setNightSlot({ ...nightSlot, enabled: e.target.checked })}
                />
                <span style={{ fontSize: '0.82rem', width: '90px', color: '#a78bfa' }}>🌙 Night</span>
                <input
                  type="time"
                  value={nightSlot.start}
                  onChange={(e) => setNightSlot({ ...nightSlot, start: e.target.value })}
                  style={{ backgroundColor: '#18181b', border: '1px solid #3f3f46', color: '#fff', padding: '4px', borderRadius: '4px', fontSize: '0.8rem' }}
                />
                <span style={{ fontSize: '0.78rem', color: '#71717a' }}>to</span>
                <input
                  type="time"
                  value={nightSlot.end}
                  onChange={(e) => setNightSlot({ ...nightSlot, end: e.target.value })}
                  style={{ backgroundColor: '#18181b', border: '1px solid #3f3f46', color: '#fff', padding: '4px', borderRadius: '4px', fontSize: '0.8rem' }}
                />
              </div>
            </div>

            {msg && (
              <div style={{ padding: '8px 12px', borderRadius: '6px', fontSize: '0.8rem', marginBottom: '14px', backgroundColor: msg.includes('✅') ? '#064e3b' : '#7f1d1d', color: msg.includes('✅') ? '#34d399' : '#f87171' }}>
                {msg}
              </div>
            )}

            {/* Action Buttons */}
            <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
              <button
                onClick={() => setSelectedMed(null)}
                style={{ backgroundColor: '#27272a', color: '#9ca3af', border: 'none', padding: '8px 16px', borderRadius: '8px', cursor: 'pointer', fontSize: '0.85rem' }}
              >
                Cancel
              </button>
              <button
                onClick={handleSaveSchedule}
                disabled={submitting}
                style={{ backgroundColor: '#ec4899', color: '#fff', border: 'none', padding: '8px 20px', borderRadius: '8px', fontWeight: '600', cursor: 'pointer', fontSize: '0.85rem' }}
              >
                {submitting ? 'Saving...' : '💾 Save & Activate Alarms'}
              </button>
            </div>

          </div>
        </div>
      )}

    </div>
  );
}

import React, { useState, useEffect } from 'react';

export default function PrescriptionCard({ data, onUpdate }) {
  if (!data) return null;

  const [isEditing, setIsEditing] = useState(false);
  const [editableData, setEditableData] = useState(data);

  // Sync state when new parsed data arrives
  useEffect(() => {
    setEditableData(data);
    setIsEditing(false);
  }, [data]);

  const handleFieldChange = (section, key, value) => {
    setEditableData((prev) => ({
      ...prev,
      [section]: {
        ...prev[section],
        [key]: value,
      },
    }));
  };

  const handleMedChange = (index, key, value) => {
    setEditableData((prev) => {
      const newMeds = [...(prev.body?.medications || [])];
      newMeds[index] = { ...newMeds[index], [key]: value };
      return {
        ...prev,
        body: {
          ...prev.body,
          medications: newMeds,
        },
      };
    });
  };

  const handleConfirmUpdate = () => {
    setIsEditing(false);
    if (onUpdate) {
      onUpdate(editableData);
    }
  };

  const handleCancelEdit = () => {
    setEditableData(data); // Revert to original AI parsed data
    setIsEditing(false);
  };

  const header = editableData.header || {};
  const body = editableData.body || {};
  const tail = editableData.tail || {};
  const medications = body.medications || [];

  return (
    <div className="rx-card" style={{ border: isEditing ? '1px solid #3b82f6' : '1px solid #2d2d2d' }}>
      {/* Header Bar with Edit / Confirm / Cancel Controls */}
      <div className="rx-header-block">
        <div>
          {isEditing ? (
            <input
              type="text"
              className="transcript-area"
              style={{ height: '36px', fontSize: '1rem', fontWeight: 'bold', marginBottom: '4px' }}
              value={header.doctorName || ''}
              onChange={(e) => handleFieldChange('header', 'doctorName', e.target.value)}
              placeholder="Doctor Name"
            />
          ) : (
            <div className="rx-doctor">{header.doctorName || 'Dr. Prescribing Doctor'}</div>
          )}

          {isEditing ? (
            <input
              type="text"
              className="transcript-area"
              style={{ height: '30px', fontSize: '0.85rem' }}
              value={header.hospitalName || ''}
              onChange={(e) => handleFieldChange('header', 'hospitalName', e.target.value)}
              placeholder="Hospital / Clinic Name"
            />
          ) : (
            <div className="rx-clinic">{header.hospitalName || 'Coimbatore Health Centre'}</div>
          )}
        </div>

        <div style={{ textAlign: 'right', display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '6px' }}>
          <div>
            <span className="rx-provenance">{editableData.source || 'doctor_voice'}</span>
          </div>

          {/* Edit / Save / Cancel Action Buttons */}
          {isEditing ? (
            <div style={{ display: 'flex', gap: '6px' }}>
              <button
                onClick={handleConfirmUpdate}
                style={{
                  backgroundColor: '#10b981',
                  color: '#fff',
                  border: 'none',
                  padding: '4px 10px',
                  borderRadius: '4px',
                  fontSize: '0.8rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                }}
              >
                💾 Confirm Update
              </button>
              <button
                onClick={handleCancelEdit}
                style={{
                  backgroundColor: '#ef4444',
                  color: '#fff',
                  border: 'none',
                  padding: '4px 10px',
                  borderRadius: '4px',
                  fontSize: '0.8rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                }}
              >
                ❌ Cancel
              </button>
            </div>
          ) : (
            <button
              onClick={() => setIsEditing(true)}
              style={{
                backgroundColor: '#3b82f6',
                color: '#fff',
                border: 'none',
                padding: '4px 12px',
                borderRadius: '4px',
                fontSize: '0.8rem',
                fontWeight: 600,
                cursor: 'pointer',
              }}
            >
              ✏️ Edit Card
            </button>
          )}
        </div>
      </div>

      {/* Recorded Diagnosis Section */}
      <div className="rx-diagnosis-box">
        <div className="rx-diagnosis-title">RECORDED DIAGNOSIS (DOCTOR STATED ONLY)</div>
        {isEditing ? (
          <input
            type="text"
            className="transcript-area"
            style={{ height: '36px', marginTop: '4px', fontSize: '0.9rem' }}
            value={body.recordedDiagnosis || ''}
            onChange={(e) => handleFieldChange('body', 'recordedDiagnosis', e.target.value)}
            placeholder="Type recorded diagnosis..."
          />
        ) : (
          <div className="rx-diagnosis-val">
            {body.recordedDiagnosis ? body.recordedDiagnosis : <em style={{ color: '#9ca3af' }}>None Stated</em>}
          </div>
        )}
      </div>

      {/* Prescribed Medications Table */}
      <div style={{ marginBottom: '8px', fontWeight: 600, fontSize: '0.9rem', color: '#e5e7eb' }}>
        PRESCRIBED MEDICATIONS ({medications.length})
      </div>

      {medications.length === 0 ? (
        <div style={{ color: '#9ca3af', fontSize: '0.85rem', fontStyle: 'italic', marginBottom: '16px' }}>
          No medications extracted yet.
        </div>
      ) : (
        <table className="meds-table">
          <thead>
            <tr>
              <th>Medicine</th>
              <th>Dosage</th>
              <th>Frequency</th>
              <th>Relation</th>
            </tr>
          </thead>
          <tbody>
            {medications.map((med, i) => (
              <tr key={i}>
                <td>
                  {isEditing ? (
                    <input
                      type="text"
                      className="transcript-area"
                      style={{ height: '30px', fontSize: '0.85rem', padding: '4px' }}
                      value={med.name || ''}
                      onChange={(e) => handleMedChange(i, 'name', e.target.value)}
                    />
                  ) : (
                    <span style={{ fontWeight: 600, color: '#fff' }}>{med.name}</span>
                  )}
                </td>
                <td>
                  {isEditing ? (
                    <input
                      type="text"
                      className="transcript-area"
                      style={{ height: '30px', fontSize: '0.85rem', padding: '4px' }}
                      value={med.dosage || ''}
                      onChange={(e) => handleMedChange(i, 'dosage', e.target.value)}
                    />
                  ) : (
                    med.dosage
                  )}
                </td>
                <td>
                  {isEditing ? (
                    <input
                      type="text"
                      className="transcript-area"
                      style={{ height: '30px', fontSize: '0.85rem', padding: '4px' }}
                      value={med.frequency || ''}
                      onChange={(e) => handleMedChange(i, 'frequency', e.target.value)}
                    />
                  ) : (
                    <span className="freq-badge">{med.frequency || '1-0-1'}</span>
                  )}
                </td>
                <td>
                  {isEditing ? (
                    <input
                      type="text"
                      className="transcript-area"
                      style={{ height: '30px', fontSize: '0.85rem', padding: '4px' }}
                      value={med.foodRelation || ''}
                      onChange={(e) => handleMedChange(i, 'foodRelation', e.target.value)}
                    />
                  ) : (
                    <span style={{ color: '#10b981' }}>{med.foodRelation || 'After Food'}</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {/* Dietary & Lifestyle Advice Section */}
      {editableData.dietaryAdvice && (
        <div style={{ marginTop: '16px', borderTop: '1px dashed #374151', paddingTop: '12px' }}>
          <div style={{ fontWeight: 600, fontSize: '0.85rem', color: '#10b981', marginBottom: '8px' }}>
            🍎 DIETARY, LIFESTYLE & HOME REMEDIES
          </div>
          
          {/* Recommended Foods */}
          {editableData.dietaryAdvice.recommendedFoods?.length > 0 && (
            <div style={{ marginBottom: '8px' }}>
              <span style={{ fontSize: '0.75rem', color: '#9ca3af', display: 'block', marginBottom: '4px' }}>Recommended Foods & Hydration:</span>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                {editableData.dietaryAdvice.recommendedFoods.map((item, idx) => (
                  <span key={idx} style={{ backgroundColor: 'rgba(16, 185, 129, 0.15)', color: '#34d399', border: '1px solid #059669', padding: '2px 8px', borderRadius: '12px', fontSize: '0.8rem' }}>
                    🥗 {item}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Foods to Avoid */}
          {editableData.dietaryAdvice.foodsToAvoid?.length > 0 && (
            <div style={{ marginBottom: '8px' }}>
              <span style={{ fontSize: '0.75rem', color: '#9ca3af', display: 'block', marginBottom: '4px' }}>Foods & Items to Avoid:</span>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                {editableData.dietaryAdvice.foodsToAvoid.map((item, idx) => (
                  <span key={idx} style={{ backgroundColor: 'rgba(239, 68, 68, 0.15)', color: '#fca5a5', border: '1px solid #dc2626', padding: '2px 8px', borderRadius: '12px', fontSize: '0.8rem' }}>
                    🚫 {item}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Traditional Remedies */}
          {editableData.dietaryAdvice.traditionalRemedies?.length > 0 && (
            <div style={{ marginBottom: '8px' }}>
              <span style={{ fontSize: '0.75rem', color: '#9ca3af', display: 'block', marginBottom: '4px' }}>Traditional & Home Remedies:</span>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                {editableData.dietaryAdvice.traditionalRemedies.map((item, idx) => (
                  <span key={idx} style={{ backgroundColor: 'rgba(245, 158, 11, 0.15)', color: '#fcd34d', border: '1px solid #d97706', padding: '2px 8px', borderRadius: '12px', fontSize: '0.8rem' }}>
                    🌿 {item}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {(tail.advice || tail.followUpDate || isEditing) && (
        <div style={{ borderTop: '1px solid #2d2d2d', paddingTop: '12px', marginTop: '12px', fontSize: '0.85rem', color: '#9ca3af' }}>
          {isEditing ? (
            <input
              type="text"
              className="transcript-area"
              style={{ height: '34px', fontSize: '0.85rem' }}
              value={tail.advice || ''}
              onChange={(e) => handleFieldChange('tail', 'advice', e.target.value)}
              placeholder="Doctor Advice / Instructions"
            />
          ) : (
            tail.advice && <div><strong>Advice:</strong> {tail.advice}</div>
          )}
        </div>
      )}
    </div>
  );
}

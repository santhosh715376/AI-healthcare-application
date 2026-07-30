import React from 'react';

export default function PrescriptionTimelineCard({ prescription }) {
  const { date, time, index, visitSummary, header, body, tail, source } = prescription;

  const doctorName = header?.doctorName || 'Dr. Unspecified';
  const hospitalName = header?.hospitalName || 'General Clinic';
  const opdContact = header?.opdContact || '';
  const medications = body?.medications || [];

  return (
    <div className="timeline-card-dark" id={`rx-card-${index}`}>
      {/* Top Title & Metadata Row */}
      <div className="timeline-card-top-row">
        <div>
          <div className="timeline-card-title">
            {time} – {date} – Entry #{String(index).padStart(2, '0')}
          </div>
          <div className="timeline-card-meta">
            <span>🏥 {hospitalName} {opdContact && `(${opdContact})`}</span>
            <span>👨‍⚕️ {doctorName}</span>
          </div>
        </div>
        <span className="timeline-badge-tag">{source || 'PATIENT_OCR'}</span>
      </div>

      <div className="timeline-card-divider" />

      {/* Narrative Visit Summary Sentence */}
      <div className="timeline-visit-quote">
        📝 <strong>Visit Summary:</strong> {visitSummary}
      </div>

      {/* Real-World Prescription Medication Table */}
      {medications.length > 0 && (
        <table className="timeline-table-dark">
          <thead>
            <tr>
              <th>Medicine</th>
              <th>Dosage</th>
              <th>Frequency</th>
              <th>Duration</th>
              <th>Relation</th>
            </tr>
          </thead>
          <tbody>
            {medications.map((med, mIdx) => (
              <tr key={mIdx}>
                <td className="med-name-bold">{med.name}</td>
                <td>{med.dosage}</td>
                <td>
                  <span className="freq-badge">{med.frequency}</span>
                </td>
                <td>{med.duration || '—'}</td>
                <td>{med.foodRelation || 'After Food'}</td>
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
    </div>
  );
}

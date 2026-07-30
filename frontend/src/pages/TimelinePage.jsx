import React, { useState, useEffect, useRef } from 'react';
import PrescriptionTimelineCard from '../components/PrescriptionTimelineCard.jsx';
import TickRail from '../components/TickRail.jsx';

export default function TimelinePage({ patientId = '9876543210', doctorId = null }) {
  const [prescriptions, setPrescriptions] = useState([]);
  const [activeIndex, setActiveIndex] = useState(1);
  const [loading, setLoading] = useState(true);

  const leftPanelRef = useRef(null);

  const fetchTimeline = async () => {
    setLoading(true);
    try {
      const url = `http://localhost:8000/api/timeline/${patientId}${doctorId ? `?doctor_id=${doctorId}` : ''}`;
      const res = await fetch(url);
      const data = await res.json();
      setPrescriptions(data.prescriptions || []);
      if (data.prescriptions?.length > 0) {
        setActiveIndex(data.prescriptions[0].index);
      }
    } catch (err) {
      console.error('Error fetching timeline:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTimeline();
  }, [patientId, doctorId]);

  // IntersectionObserver to auto-sync active tick line as user scrolls left panel
  useEffect(() => {
    if (!prescriptions.length) return;

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            const id = entry.target.id;
            const idx = parseInt(id.replace('rx-card-', ''), 10);
            if (!isNaN(idx)) {
              setActiveIndex(idx);
            }
          }
        });
      },
      { root: leftPanelRef.current, threshold: 0.4 }
    );

    prescriptions.forEach((rx) => {
      const el = document.getElementById(`rx-card-${rx.index}`);
      if (el) observer.observe(el);
    });

    return () => observer.disconnect();
  }, [prescriptions]);

  const handleTickClick = (index) => {
    setActiveIndex(index);
    const el = document.getElementById(`rx-card-${index}`);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  };

  return (
    <div className="timeline-container">
      {/* Clean Header Bar */}
      <div className="timeline-header-bar">
        <div className="timeline-title-group">
          <span className="timeline-main-title">📋 Patient Prescription Timeline</span>
          <span className="timeline-patient-badge">Patient Lookup: {patientId}</span>
        </div>
        <button className="action-btn" onClick={fetchTimeline} style={{ padding: '6px 14px', fontSize: '0.82rem' }}>
          🔄 Refresh Record
        </button>
      </div>

      {/* Split Area: Left Cards Panel + Right Tick Rail */}
      <div className="timeline-body-split">
        {/* Left Scrollable Panel */}
        <div className="timeline-left-panel" ref={leftPanelRef}>
          {loading ? (
            <div style={{ color: '#9ca3af', fontStyle: 'italic', marginTop: '60px' }}>Loading timeline record...</div>
          ) : prescriptions.length === 0 ? (
            <div style={{ textAlign: 'center', marginTop: '60px', color: '#9ca3af' }}>
              <div style={{ fontSize: '3rem', marginBottom: '12px' }}>📂</div>
              <h3 style={{ color: '#fff', fontSize: '1.2rem' }}>No Prescriptions Saved Yet</h3>
              <p style={{ marginTop: '8px', fontSize: '0.9rem' }}>
                Go to 🎙️ Voice Capture or 📷 OCR Upload tab, complete a parse, and click <br />
                <strong style={{ color: '#10b981' }}>"🏥 Confirm & Save to Patient Timeline Record"</strong> to populate this timeline!
              </p>
            </div>
          ) : (
            <div className="timeline-cards-list">
              {prescriptions.map((rx, idx) => (
                <React.Fragment key={rx.id || rx.index}>
                  <PrescriptionTimelineCard prescription={rx} />
                  {idx < prescriptions.length - 1 && <div className="timeline-connector-line" />}
                </React.Fragment>
              ))}
            </div>
          )}
        </div>

        {/* Right Rail: Jump-Index Rectangle Ticks (1:1 with prescription entries) */}
        {prescriptions.length > 0 && (
          <TickRail
            items={prescriptions}
            activeIndex={activeIndex}
            onTickClick={handleTickClick}
          />
        )}
      </div>
    </div>
  );
}

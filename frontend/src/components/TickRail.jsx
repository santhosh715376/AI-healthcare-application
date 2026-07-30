import React, { useState } from 'react';

export default function TickRail({ items, activeIndex, onTickClick }) {
  const [hoveredItem, setHoveredItem] = useState(null);
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 });

  const handleMouseMove = (e, item) => {
    setHoveredItem(item);
    setMousePos({ x: e.clientX - 330, y: Math.max(10, e.clientY - 60) });
  };

  const handleMouseLeave = () => {
    setHoveredItem(null);
  };

  return (
    <div className="tick-rail-container">
      <div className="tick-rail-track">
        {items.map((item) => {
          const isActive = item.index === activeIndex;

          return (
            <div
              key={item.id || item.index}
              className={`tick-line-rect ${isActive ? 'active' : ''}`}
              onClick={() => onTickClick(item.index)}
              onMouseMove={(e) => handleMouseMove(e, item)}
              onMouseLeave={handleMouseLeave}
              title={`Entry #${item.index} - ${item.date}`}
            />
          );
        })}
      </div>

      {/* Floating Hover Index Popup Matching Reference Screenshot */}
      {hoveredItem && (
        <div
          className="tick-popup-dark"
          style={{ top: `${mousePos.y}px`, left: `${mousePos.x}px` }}
        >
          <div className="tick-popup-header">
            {hoveredItem.time} – {hoveredItem.date} – Entry #{String(hoveredItem.index).padStart(2, '0')}
          </div>
          <div className="tick-popup-body">
            <div>🏥 {hoveredItem.header?.hospitalName || 'General Clinic'}</div>
            <div>👨‍⚕️ {hoveredItem.header?.doctorName || 'Dr. Unspecified'}</div>
            <div className="tick-popup-diag">
              Diagnosis: {hoveredItem.body?.recordedDiagnosis || 'URTI'}
            </div>
            <div style={{ marginTop: '4px', color: '#e5e7eb' }}>
              💊 {hoveredItem.body?.medications?.length || 0} Prescribed Medications
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

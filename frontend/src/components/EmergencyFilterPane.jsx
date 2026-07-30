import React from 'react';

export default function EmergencyFilterPane({
  searchQuery,
  onSearchChange,
  radiusKm,
  onRadiusChange,
  selectedCategory,
  onCategoryChange,
  hospitals = [],
  selectedHospitalId,
  onSelectHospital,
  locationEnabled,
  onRequestLocation,
  cardRefs
}) {
  const categories = ['All', '24/7 ER', 'Multispecialty', 'Pediatrics', 'Cardiology', 'Trauma'];

  return (
    <div style={{
      width: '420px',
      height: '100%',
      backgroundColor: '#111827',
      borderRight: '1px solid #1f2937',
      display: 'flex',
      flexDirection: 'column',
      overflow: 'hidden'
    }}>
      {/* Top Search Header */}
      <div style={{ padding: '16px', borderBottom: '1px solid #1f2937', backgroundColor: '#1f2937' }}>
        <div style={{ position: 'relative', marginBottom: '12px' }}>
          <input
            type="text"
            className="transcript-area"
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            placeholder="Search hospital name or area..."
            style={{
              width: '100%',
              height: '42px',
              paddingLeft: '36px',
              paddingRight: '36px',
              fontSize: '0.9rem',
              backgroundColor: '#111827',
              borderColor: '#374151'
            }}
          />
          <span style={{ position: 'absolute', left: '12px', top: '10px', fontSize: '1rem', color: '#9ca3af' }}>🔍</span>
          {searchQuery && (
            <button
              onClick={() => onSearchChange('')}
              style={{
                position: 'absolute',
                right: '10px',
                top: '10px',
                background: 'none',
                border: 'none',
                color: '#9ca3af',
                cursor: 'pointer',
                fontSize: '1rem'
              }}
            >
              ✕
            </button>
          )}
        </div>

        {/* GPS Location Banner */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: '12px',
          padding: '8px 12px',
          backgroundColor: locationEnabled ? 'rgba(16, 185, 129, 0.15)' : 'rgba(245, 158, 11, 0.15)',
          border: `1px solid ${locationEnabled ? '#10b981' : '#f59e0b'}`,
          borderRadius: '8px'
        }}>
          <span style={{ fontSize: '0.8rem', fontWeight: 600, color: locationEnabled ? '#34d399' : '#fbbf24' }}>
            {locationEnabled ? '🔵 Real-Time GPS Active' : '📍 Enable GPS for live distance'}
          </span>
          <button
            onClick={onRequestLocation}
            style={{
              backgroundColor: locationEnabled ? '#10b981' : '#f59e0b',
              color: '#111827',
              border: 'none',
              padding: '4px 10px',
              borderRadius: '6px',
              fontSize: '0.78rem',
              fontWeight: 700,
              cursor: 'pointer'
            }}
          >
            {locationEnabled ? '🎯 Refresh GPS' : 'Turn On Location'}
          </button>
        </div>

        {/* Radius Resizing Slider */}
        <div style={{ marginBottom: '10px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.82rem', marginBottom: '4px', color: '#d1d5db' }}>
            <span>Search Radius Slider</span>
            <span style={{ color: '#60a5fa', fontWeight: 700 }}>{radiusKm} km</span>
          </div>
          <input
            type="range"
            min="1"
            max="50"
            value={radiusKm}
            onChange={(e) => onRadiusChange(Number(e.target.value))}
            style={{ width: '100%', accentColor: '#3b82f6', cursor: 'pointer' }}
          />
        </div>

        {/* Category Chips */}
        <div style={{ display: 'flex', gap: '6px', overflowX: 'auto', paddingBottom: '4px' }}>
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => onCategoryChange(cat)}
              style={{
                backgroundColor: selectedCategory === cat ? '#2563eb' : '#374151',
                color: '#ffffff',
                border: 'none',
                padding: '4px 12px',
                borderRadius: '16px',
                fontSize: '0.78rem',
                fontWeight: 600,
                cursor: 'pointer',
                whiteSpace: 'nowrap'
              }}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      {/* Scrollable Results List */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '12px' }}>
        {hospitals.length === 0 ? (
          <div style={{ textAlign: 'center', color: '#9ca3af', marginTop: '40px', fontSize: '0.9rem' }}>
            No hospitals found matching criteria. Adjust radius or search query.
          </div>
        ) : (
          hospitals.map((item, idx) => {
            const isSelected = item.id === selectedHospitalId;
            return (
              <div
                key={item.id}
                ref={(el) => (cardRefs.current[item.id] = el)}
                onClick={() => onSelectHospital(item.id)}
                style={{
                  backgroundColor: isSelected ? '#1e293b' : '#1f2937',
                  border: `1.5px solid ${isSelected ? '#3b82f6' : '#374151'}`,
                  borderRadius: '12px',
                  padding: '14px',
                  marginBottom: '12px',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                  boxShadow: isSelected ? '0 0 12px rgba(59, 130, 246, 0.4)' : 'none'
                }}
              >
                {/* Hospital Header */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '6px' }}>
                  <div style={{ flex: 1, paddingRight: '8px' }}>
                    <span style={{ fontSize: '0.95rem', fontWeight: 700, color: '#ffffff' }}>
                      #{item.rank || idx + 1}. {item.name}
                    </span>
                    {item.distanceRange && (
                      <div style={{ fontSize: '0.72rem', color: '#60a5fa', fontWeight: 600, marginTop: '2px' }}>
                        📍 {item.distanceRange}
                      </div>
                    )}
                  </div>
                  <span style={{
                    backgroundColor: '#064e3b',
                    color: '#34d399',
                    fontSize: '0.75rem',
                    fontWeight: 700,
                    padding: '3px 8px',
                    borderRadius: '12px',
                    whiteSpace: 'nowrap'
                  }}>
                    {item.distanceKm} km away
                  </span>
                </div>

                {/* Rating & Status */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.82rem', marginBottom: '8px' }}>
                  <span style={{ color: '#fbbf24', fontWeight: 700 }}>★ {item.rating}</span>
                  <span style={{ color: '#9ca3af' }}>({item.reviewCount.toLocaleString()})</span>
                  <span style={{ color: '#10b981', fontWeight: 600 }}>• {item.open24x7 ? 'Open 24 Hours' : 'Open'}</span>
                </div>

                {/* Enriched Clinical Badges */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', marginBottom: '10px' }}>
                  <div style={{ fontSize: '0.78rem', color: '#60a5fa', fontWeight: 600 }}>
                    🏥 {item.beds} Beds | {item.category}
                  </div>
                  <div style={{ fontSize: '0.78rem', color: '#f472b6', fontWeight: 600 }}>
                    ⚡ {item.emergencySpecialty24x7}
                  </div>
                  <div style={{ fontSize: '0.78rem', color: '#fbbf24', fontWeight: 600 }}>
                    🏆 {item.bestSector}
                  </div>
                </div>

                {/* Phone & Address */}
                <div style={{ fontSize: '0.8rem', color: '#9ca3af', marginBottom: '10px' }}>
                  📞 {item.phone} | 📍 {item.address}
                </div>

                {/* Direct Google Maps Directions Button */}
                <a
                  href={item.googleMapsUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  onClick={(e) => e.stopPropagation()}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '6px',
                    backgroundColor: '#2563eb',
                    color: '#ffffff',
                    padding: '8px 14px',
                    borderRadius: '8px',
                    fontWeight: 700,
                    fontSize: '0.82rem',
                    textDecoration: 'none',
                    boxShadow: '0 2px 6px rgba(37, 99, 235, 0.4)'
                  }}
                >
                  ↪️ Direct Google Maps Navigation
                </a>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}

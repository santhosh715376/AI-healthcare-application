import React, { useEffect, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

export default function HospitalMap({
  hospitals = [],
  center = { lat: 11.0168, lng: 76.9558 },
  radiusKm = 15,
  userLocation = null,
  selectedHospitalId = null,
  onSelectHospital = () => {}
}) {
  const mapContainerRef = useRef(null);
  const mapRef = useRef(null);
  const markersLayerRef = useRef(null);
  const circleRef = useRef(null);
  const userMarkerRef = useRef(null);

  // Initialize Leaflet Map once
  useEffect(() => {
    if (!mapContainerRef.current || mapRef.current) return;

    const map = L.map(mapContainerRef.current, {
      center: [center.lat, center.lng],
      zoom: 10,
      zoomControl: true,
      attributionControl: false
    });

    // Tile Layer: Esri World Imagery (Satellite)
    L.tileLayer(
      'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
      { maxZoom: 19 }
    ).addTo(map);

    // Labels Overlay (Transportation & Places)
    L.tileLayer(
      'https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}',
      { maxZoom: 19, opacity: 0.85 }
    ).addTo(map);

    // Load Full Coimbatore Revenue District GeoJSON Boundary & Mask
    fetch('/data/coimbatore_boundary.geojson')
      .then((res) => res.json())
      .then((geoJson) => {
        if (!mapRef.current) return;

        // Neon district boundary stroke
        const districtLayer = L.geoJSON(geoJson, {
          style: {
            color: '#39ff14',
            weight: 3,
            opacity: 0.9,
            fillOpacity: 0
          }
        }).addTo(mapRef.current);

        // Fit map canvas camera to cover entire Coimbatore Revenue District
        if (!userLocation) {
          mapRef.current.fitBounds(districtLayer.getBounds(), { padding: [15, 15] });
        }

        // Inverted polygon dimming mask outside district boundary
        try {
          const outerRing = [
            [-90, -360],
            [90, -360],
            [90, 360],
            [-90, 360],
            [-90, -360]
          ];
          const coords = geoJson.features[0].geometry.coordinates[0];
          const innerRing = coords.map((c) => [c[1], c[0]]);

          L.polygon([outerRing, innerRing], {
            color: 'transparent',
            fillColor: '#000000',
            fillOpacity: 0.65,
            interactive: false
          }).addTo(mapRef.current);
        } catch (e) {
          console.warn('District GeoJSON boundary mask creation warning:', e);
        }
      })
      .catch((err) => console.warn('Could not load coimbatore_boundary.geojson:', err));

    markersLayerRef.current = L.layerGroup().addTo(map);
    mapRef.current = map;

    return () => {
      if (mapRef.current) {
        mapRef.current.remove();
        mapRef.current = null;
      }
    };
  }, []);

  // Update User Pulsing GPS Location Marker & Radius Circle
  useEffect(() => {
    if (!mapRef.current) return;

    const currentCenter = userLocation
      ? [userLocation.lat, userLocation.lng]
      : [center.lat, center.lng];

    if (userLocation) {
      mapRef.current.setView(currentCenter, Math.max(mapRef.current.getZoom(), 11));
    }

    // Update or create dashed radius circle
    if (circleRef.current) {
      circleRef.current.setLatLng(currentCenter);
      circleRef.current.setRadius(radiusKm * 1000);
    } else {
      circleRef.current = L.circle(currentCenter, {
        radius: radiusKm * 1000,
        color: '#3b82f6',
        weight: 2,
        dashArray: '6, 8',
        fillColor: '#3b82f6',
        fillOpacity: 0.08
      }).addTo(mapRef.current);
    }

    // Highlighting User Location Blue Dot SVG Marker
    if (userLocation) {
      if (userMarkerRef.current) {
        userMarkerRef.current.setLatLng([userLocation.lat, userLocation.lng]);
      } else {
        const userIcon = L.divIcon({
          className: '',
          html: `<div style="
            width: 24px;
            height: 24px;
            background-color: #3b82f6;
            border: 3.5px solid #ffffff;
            border-radius: 50%;
            box-shadow: 0 0 16px rgba(59, 130, 246, 1);
            animation: pulseUser 1.5s infinite;
          "></div>`,
          iconSize: [24, 24],
          iconAnchor: [12, 12]
        });
        userMarkerRef.current = L.marker([userLocation.lat, userLocation.lng], { icon: userIcon })
          .addTo(mapRef.current)
          .bindTooltip('🔵 You (Active GPS Location)', { permanent: false, direction: 'top' });
      }
    }
  }, [userLocation, center, radiusKm]);

  // Render Clean Circular Pin Markers with Rich Hover Popup Cards
  useEffect(() => {
    if (!markersLayerRef.current) return;
    markersLayerRef.current.clearLayers();

    hospitals.forEach((item, index) => {
      const isSelected = item.id === selectedHospitalId;
      const rankNum = index + 1;

      // Color coding: Top 3 Orange/Amber, Top 5 Blue, Others Grey-Blue
      let bgGrad = 'linear-gradient(135deg, #4b5563, #374151)';
      let borderColor = '#9ca3af';
      if (rankNum === 1) {
        bgGrad = 'linear-gradient(135deg, #f97316, #ea580c)';
        borderColor = '#fdba74';
      } else if (rankNum <= 3) {
        bgGrad = 'linear-gradient(135deg, #f59e0b, #d97706)';
        borderColor = '#fde68a';
      } else if (rankNum <= 5) {
        bgGrad = 'linear-gradient(135deg, #2563eb, #1d4ed8)';
        borderColor = '#93c5fd';
      }

      if (isSelected) {
        bgGrad = 'linear-gradient(135deg, #dc2626, #b91c1c)';
        borderColor = '#fca5a5';
      }

      const pinSize = isSelected ? 34 : (rankNum <= 3 ? 30 : 26);

      const markerHtml = `
        <div style="
          width: ${pinSize}px;
          height: ${pinSize}px;
          background: ${bgGrad};
          border: 2px solid ${borderColor};
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          color: #ffffff;
          font-size: ${pinSize * 0.42}px;
          font-weight: 800;
          font-family: system-ui, sans-serif;
          box-shadow: 0 4px 12px rgba(0,0,0,0.6);
          cursor: pointer;
          transform: ${isSelected ? 'scale(1.2)' : 'scale(1)'};
          transition: transform 0.2s ease;
        ">
          ${rankNum}
        </div>
      `;

      const customIcon = L.divIcon({
        className: '',
        html: markerHtml,
        iconSize: [pinSize, pinSize],
        iconAnchor: [pinSize / 2, pinSize / 2],
        popupAnchor: [0, -pinSize / 2]
      });

      const popupContent = `
        <div style="padding: 6px; min-width: 230px; font-family: system-ui, sans-serif;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
            <strong style="font-size: 0.95rem; color: #111827; flex: 1;">${item.name}</strong>
            <span style="background-color: #f59e0b; color: #ffffff; font-size: 0.75rem; padding: 2px 6px; border-radius: 10px; font-weight: bold; margin-left: 6px;">#${rankNum}</span>
          </div>
          <div style="font-size: 0.8rem; color: #4b5563; margin-bottom: 6px;">
            📍 ${item.distanceKm} km away • <span style="color: #10b981; font-weight: 600;">${item.emergency24x7 ? '24/7 ER' : 'Open'}</span>
          </div>
          <div style="font-size: 0.78rem; color: #1e40af; font-weight: 600; margin-bottom: 4px;">
            🏥 ${item.beds} beds • ${item.category}
          </div>
          <div style="font-size: 0.75rem; color: #92400e; font-weight: 600; margin-bottom: 10px;">
            ⚡ ${item.emergencySpecialty24x7 || item.bestSector}
          </div>
          <a href="${item.googleMapsUrl}" target="_blank" rel="noopener noreferrer" style="
            display: block;
            text-align: center;
            background-color: #2563eb;
            color: #ffffff;
            padding: 8px 12px;
            border-radius: 6px;
            text-decoration: none;
            font-size: 0.82rem;
            font-weight: bold;
            box-shadow: 0 2px 6px rgba(37, 99, 235, 0.4);
          ">
            🧭 Get Directions
          </a>
        </div>
      `;

      const marker = L.marker([item.latitude, item.longitude], { icon: customIcon })
        .bindPopup(popupContent, { closeButton: true });

      marker.on('click', () => {
        onSelectHospital(item.id);
      });

      marker.addTo(markersLayerRef.current);
    });
  }, [hospitals, selectedHospitalId, onSelectHospital]);

  return (
    <div style={{ width: '100%', height: '100%', position: 'relative' }}>
      <div ref={mapContainerRef} style={{ width: '100%', height: '100%' }} />

      {/* Result Count Badge */}
      <div style={{
        position: 'absolute',
        top: '16px',
        right: '16px',
        zIndex: 1000,
        backgroundColor: 'rgba(17, 24, 39, 0.85)',
        border: '1px solid #374151',
        padding: '6px 14px',
        borderRadius: '20px',
        color: '#10b981',
        fontSize: '0.82rem',
        fontWeight: 700,
        boxShadow: '0 4px 12px rgba(0,0,0,0.5)',
        backdropFilter: 'blur(6px)'
      }}>
        🟢 {hospitals.length} Hospitals in District Range ({radiusKm} km)
      </div>

      {/* Map Legend */}
      <div style={{
        position: 'absolute',
        bottom: '24px',
        left: '16px',
        zIndex: 1000,
        backgroundColor: 'rgba(17, 24, 39, 0.88)',
        border: '1px solid #374151',
        padding: '10px 14px',
        borderRadius: '10px',
        fontSize: '0.78rem',
        color: '#e5e7eb',
        boxShadow: '0 4px 14px rgba(0,0,0,0.6)',
        backdropFilter: 'blur(6px)'
      }}>
        <div style={{ fontWeight: 800, color: '#9ca3af', marginBottom: '6px', fontSize: '0.72rem', letterSpacing: '0.05em' }}>COIMBATORE DISTRICT LEGEND</div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
          <span style={{ width: '10px', height: '10px', borderRadius: '50%', backgroundColor: '#f97316' }}></span> #1 Ranked
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
          <span style={{ width: '10px', height: '10px', borderRadius: '50%', backgroundColor: '#f59e0b' }}></span> #2-3 Ranked
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
          <span style={{ width: '10px', height: '10px', borderRadius: '50%', backgroundColor: '#2563eb' }}></span> Top 5
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
          <span style={{ width: '10px', height: '10px', borderRadius: '50%', backgroundColor: '#4b5563' }}></span> Others
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ width: '10px', height: '10px', borderRadius: '50%', backgroundColor: '#3b82f6', border: '1.5px solid #fff' }}></span> You (GPS Active)
        </div>
      </div>
    </div>
  );
}

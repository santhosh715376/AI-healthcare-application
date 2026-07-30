'use client';

import React, { useEffect, useRef, useMemo } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { Hospital } from './HospitalCard';

const containerStyle: React.CSSProperties = {
  width: '100%',
  height: '100%',
  minHeight: '600px',
};

interface HospitalMapProps {
  hospitals: { hospital: Hospital; reason?: string; rank?: number }[];
  center?: { lat: number; lng: number };
  radiusKm?: number;
}

// SVG marker builder for crisp, scalable markers
function buildMarkerSvg(
  fillColor: string,
  strokeColor: string,
  size: number,
  label?: string
): string {
  const half = size / 2;
  if (label) {
    return `<svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size}" viewBox="0 0 ${size} ${size}">
      <circle cx="${half}" cy="${half}" r="${half - 2}" fill="${fillColor}" stroke="${strokeColor}" stroke-width="2.5"/>
      <text x="${half}" y="${half}" text-anchor="middle" dominant-baseline="central" font-size="${Math.round(size * 0.4)}px" font-weight="bold" fill="#fff" font-family="system-ui, sans-serif">${label}</text>
    </svg>`;
  }
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size}" viewBox="0 0 ${size} ${size}">
    <circle cx="${half}" cy="${half}" r="${half - 2}" fill="${fillColor}" stroke="${strokeColor}" stroke-width="2"/>
  </svg>`;
}

function createIcon(fillColor: string, strokeColor: string, size: number, label?: string): L.DivIcon {
  return L.divIcon({
    html: buildMarkerSvg(fillColor, strokeColor, size, label),
    className: '',
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
    popupAnchor: [0, -size / 2],
  });
}

export default function HospitalMap({
  hospitals,
  center = { lat: 11.0168, lng: 76.9558 },
  radiusKm = 15,
}: HospitalMapProps) {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<L.Map | null>(null);
  const markersLayerRef = useRef<L.LayerGroup | null>(null);
  const circleRef = useRef<L.Circle | null>(null);

  // Determine if hospitals are ranked
  const hasRanking = useMemo(() => hospitals.some(h => h.rank !== undefined), [hospitals]);

  // Init map once
  useEffect(() => {
    if (!mapContainerRef.current || mapRef.current) return;

    const map = L.map(mapContainerRef.current, {
      center: [center.lat, center.lng],
      zoom: 12,
      zoomControl: true,
      attributionControl: true,
    });

    // --- Satellite tile layer (Esri World Imagery – free, no API key) ---
    L.tileLayer(
      'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
      {
        attribution: 'Tiles &copy; Esri',
        maxZoom: 19,
      }
    ).addTo(map);

    // --- Labels overlay so you can read place names on satellite ---
    L.tileLayer(
      'https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Transportation/MapServer/tile/{z}/{y}/{x}',
      { maxZoom: 19, opacity: 0.7 }
    ).addTo(map);

    L.tileLayer(
      'https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}',
      { maxZoom: 19, opacity: 0.85 }
    ).addTo(map);

    // --- Isolate Coimbatore District ---
    fetch('/data/coimbatore_boundary.geojson')
      .then(res => res.json())
      .then(geoJson => {
        if (!mapRef.current) return;
        
        // 1. Render bright neon boundary stroke
        L.geoJSON(geoJson, {
          style: {
            color: '#39ff14',
            weight: 3,
            fillOpacity: 0,
            opacity: 0.9,
          }
        }).addTo(map);

        // 2. Inverted polygon mask to dim the outside world
        try {
          // World boundaries (outer ring)
          const outerRing: [number, number][] = [
            [-90, -360],
            [90, -360],
            [90, 360],
            [-90, 360],
            [-90, -360]
          ];

          // Extract inner ring from GeoJSON (handle both Feature and raw Geometry)
          let coordinates = [];
          if (geoJson.type === 'FeatureCollection' && geoJson.features.length > 0) {
            coordinates = geoJson.features[0].geometry.coordinates;
          } else if (geoJson.type === 'Feature') {
            coordinates = geoJson.geometry.coordinates;
          } else if (geoJson.type === 'Polygon' || geoJson.type === 'MultiPolygon') {
            coordinates = geoJson.coordinates;
          }

          if (coordinates && coordinates.length > 0) {
            // Flatten to get the first polygon ring (assuming simple polygon for mask)
            // Leaflet expects [lat, lng], GeoJSON is [lng, lat]
            const innerRingRaw = Array.isArray(coordinates[0][0][0]) 
              ? coordinates[0][0] // MultiPolygon 
              : coordinates[0];   // Polygon

            const innerRing: [number, number][] = innerRingRaw.map((coord: [number, number]) => [coord[1], coord[0]]);

            // Create a polygon with a hole
            L.polygon([outerRing, innerRing], {
              color: 'transparent',
              fillColor: '#000000',
              fillOpacity: 0.65, // Dim the outside by 65%
            }).addTo(map);
          }
        } catch (e) {
          console.error('Failed to create isolation mask:', e);
        }
      })
      .catch(console.error);

    // Markers layer group
    markersLayerRef.current = L.layerGroup().addTo(map);

    mapRef.current = map;

    return () => {
      map.remove();
      mapRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Update center & radius circle
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    // Remove old circle
    if (circleRef.current) {
      circleRef.current.remove();
    }

    // User location marker (blue pulsing dot)
    // We'll re-add via circle + a tiny marker
    const userIcon = L.divIcon({
      html: `<div style="
        width: 18px; height: 18px;
        background: #2563eb;
        border: 3px solid #fff;
        border-radius: 50%;
        box-shadow: 0 0 0 4px rgba(37,99,235,0.3), 0 0 12px rgba(37,99,235,0.5);
        animation: pulse-blue 2s ease-in-out infinite;
      "></div>
      <style>
        @keyframes pulse-blue {
          0%, 100% { box-shadow: 0 0 0 4px rgba(37,99,235,0.3), 0 0 12px rgba(37,99,235,0.5); }
          50% { box-shadow: 0 0 0 8px rgba(37,99,235,0.15), 0 0 20px rgba(37,99,235,0.3); }
        }
      </style>`,
      className: '',
      iconSize: [18, 18],
      iconAnchor: [9, 9],
    });

    // Remove previous user marker if any (stored on map)
    if ((map as unknown as { _userMarker?: L.Marker })._userMarker) {
      (map as unknown as { _userMarker?: L.Marker })._userMarker!.remove();
    }
    const userMarker = L.marker([center.lat, center.lng], { icon: userIcon, zIndexOffset: 1000 })
      .addTo(map)
      .bindPopup('<div style="font-weight:600;font-size:13px;color:#1e40af;">📍 Your Location</div>');
    (map as unknown as { _userMarker: L.Marker })._userMarker = userMarker;

    // Radius circle
    const radiusCircle = L.circle([center.lat, center.lng], {
      radius: radiusKm * 1000, // convert km to meters
      color: '#3b82f6',
      weight: 2.5,
      opacity: 0.7,
      fillColor: '#3b82f6',
      fillOpacity: 0.08,
      dashArray: '8, 6',
    }).addTo(map);
    circleRef.current = radiusCircle;

    // Fit map to the radius circle bounds
    map.fitBounds(radiusCircle.getBounds(), { padding: [30, 30] });
  }, [center, radiusKm]);

  // Update markers when hospitals change
  useEffect(() => {
    const map = mapRef.current;
    const markersLayer = markersLayerRef.current;
    if (!map || !markersLayer) return;

    markersLayer.clearLayers();

    hospitals.forEach(({ hospital, reason, rank }) => {
      const isTopRanked = rank !== undefined && rank <= 3;
      const isEmergency = hospital.emergencyServices;

      let fillColor = '#22c55e'; // green default
      let strokeColor = '#ffffff';
      let markerSize = 22;
      let label: string | undefined;

      if (hasRanking && rank !== undefined) {
        // Ranked mode: gradient from gold → silver → bronze → blue
        if (rank === 1) { fillColor = '#f59e0b'; markerSize = 34; strokeColor = '#fff'; }
        else if (rank === 2) { fillColor = '#94a3b8'; markerSize = 30; strokeColor = '#fff'; }
        else if (rank === 3) { fillColor = '#d97706'; markerSize = 28; strokeColor = '#fff'; }
        else if (rank <= 5) { fillColor = '#3b82f6'; markerSize = 24; }
        else { fillColor = '#6366f1'; markerSize = 20; }
        label = `${rank}`;
      } else {
        // Unranked mode
        if (isEmergency) { fillColor = '#ef4444'; markerSize = 24; }
        else { fillColor = '#22c55e'; markerSize = 20; }
      }

      const icon = createIcon(fillColor, strokeColor, markerSize, label);

      const popupContent = `
        <div style="font-family:system-ui,sans-serif;min-width:200px;max-width:260px;padding:4px;">
          <div style="display:flex;align-items:start;justify-content:space-between;gap:8px;">
            <h3 style="margin:0;font-size:14px;font-weight:700;line-height:1.3;color:#1a1a2e;">${hospital.name}</h3>
            ${rank ? `<span style="display:flex;align-items:center;justify-content:center;width:24px;height:24px;border-radius:50%;background:${fillColor};color:#fff;font-size:11px;font-weight:700;flex-shrink:0;">#${rank}</span>` : ''}
          </div>

          <div style="display:flex;flex-wrap:wrap;gap:4px;margin-top:8px;">
            ${hospital.specialties.slice(0, 3).map(s => `<span style="font-size:10px;padding:2px 6px;border-radius:4px;background:#e8f5e9;color:#2e7d32;border:1px solid #c8e6c9;">${s}</span>`).join('')}
            ${hospital.specialties.length > 3 ? `<span style="font-size:10px;padding:2px 6px;border-radius:4px;background:#f5f5f5;color:#666;">+${hospital.specialties.length - 3}</span>` : ''}
          </div>

          <div style="display:flex;gap:12px;margin-top:8px;font-size:11px;color:#666;">
            ${hospital.distanceKm !== undefined ? `<span>📍 ${hospital.distanceKm.toFixed(1)} km</span>` : ''}
            ${isEmergency ? `<span style="color:#ef4444;">🚨 ER 24×7</span>` : ''}
            ${hospital.open24x7 ? `<span style="color:#22c55e;">🕐 24/7</span>` : ''}
          </div>

          <div style="margin-top:6px;font-size:10px;color:#888;">
            🏥 ${hospital.beds} beds · ${hospital.accreditation} · Est. ${hospital.yearEstablished}
          </div>

          ${reason ? `<div style="margin-top:8px;padding:8px;background:linear-gradient(135deg,#eff6ff,#f0f7ff);border:1px solid #bfdbfe;border-radius:8px;font-size:11px;line-height:1.5;color:#1e40af;">
            <strong style="display:block;margin-bottom:2px;">🤖 AI Match Reason:</strong>${reason}
          </div>` : ''}

          <div style="margin-top:10px;">
            <a href="https://www.google.com/maps/dir/?api=1&destination=${hospital.location.lat},${hospital.location.lng}"
              target="_blank" rel="noopener noreferrer"
              style="display:block;text-align:center;padding:8px;background:#2563eb;color:#fff;border-radius:8px;font-size:12px;font-weight:600;text-decoration:none;">
              🧭 Get Directions
            </a>
          </div>
        </div>
      `;

      L.marker([hospital.location.lat, hospital.location.lng], { icon, zIndexOffset: isTopRanked ? 500 : 0 })
        .addTo(markersLayer)
        .bindPopup(popupContent, { maxWidth: 280, className: 'hospital-popup' });
    });
  }, [hospitals, hasRanking]);

  return (
    <div className="relative w-full h-full min-h-[600px] rounded-2xl overflow-hidden glass-card border border-glass-border shadow-2xl z-0">
      <div ref={mapContainerRef} style={containerStyle} />

      {/* Hospital count badge */}
      <div className="absolute top-4 right-4 z-[1000] bg-black/70 backdrop-blur-md text-white px-4 py-2 rounded-full text-sm font-semibold shadow-lg border border-white/10 flex items-center gap-2">
        <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
        {hospitals.length} hospital{hospitals.length !== 1 ? 's' : ''} found
      </div>

      {/* Legend */}
      <div className="absolute bottom-6 left-4 z-[1000] bg-black/60 backdrop-blur-md text-white p-3 rounded-xl text-xs shadow-lg border border-white/10 flex flex-col gap-1.5">
        <div className="font-semibold text-[11px] uppercase tracking-wide opacity-70 mb-1">Legend</div>
        {hasRanking ? (
          <>
            <div className="flex items-center gap-2"><span className="w-3 h-3 rounded-full" style={{ background: '#f59e0b' }} /> #1 Ranked</div>
            <div className="flex items-center gap-2"><span className="w-3 h-3 rounded-full" style={{ background: '#94a3b8' }} /> #2 Ranked</div>
            <div className="flex items-center gap-2"><span className="w-3 h-3 rounded-full" style={{ background: '#d97706' }} /> #3 Ranked</div>
            <div className="flex items-center gap-2"><span className="w-3 h-3 rounded-full" style={{ background: '#3b82f6' }} /> Top 5</div>
            <div className="flex items-center gap-2"><span className="w-3 h-3 rounded-full" style={{ background: '#6366f1' }} /> Others</div>
          </>
        ) : (
          <>
            <div className="flex items-center gap-2"><span className="w-3 h-3 rounded-full" style={{ background: '#22c55e' }} /> Hospital</div>
            <div className="flex items-center gap-2"><span className="w-3 h-3 rounded-full" style={{ background: '#ef4444' }} /> Emergency</div>
          </>
        )}
        <div className="flex items-center gap-2"><span className="w-3 h-3 rounded-full" style={{ background: '#2563eb', border: '2px solid #fff' }} /> You</div>
      </div>

      <style jsx global>{`
        .hospital-popup .leaflet-popup-content-wrapper {
          border-radius: 14px;
          box-shadow: 0 8px 32px rgba(0,0,0,0.25);
          border: 1px solid rgba(0,0,0,0.08);
        }
        .hospital-popup .leaflet-popup-tip {
          box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }
      `}</style>
    </div>
  );
}

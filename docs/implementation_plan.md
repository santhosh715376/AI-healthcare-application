# Implementation Plan: Emergency Hospital Mapping Engine ("Mapping")

## Executive Summary & Data Enrichment

This feature embeds a **Google Maps-Style Emergency Hospital Mapping Engine** into the **Patient Health Portal** under the sub-tab **🗺️ Mapping**.

Per your feedback, the backend dataset stored in SQLite (`healthcare.db`) is enriched with realistic synthetic clinical data for Coimbatore hospitals, including exact latitude/longitude, total bed counts, 24/7 emergency specialties, and sector rankings. On the map canvas, data points render as **clean, simple labelled SVG pin markers**.

---

## 🗄️ 1. Enriched SQLite Dataset Architecture

### `hospitals` SQLite Database Schema (`agents/healthcare.db`)
```sql
CREATE TABLE IF NOT EXISTS hospitals (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    beds INTEGER DEFAULT 150,
    emergency_specialty_24x7 TEXT DEFAULT '24/7 Emergency & General Medicine',
    best_sector TEXT DEFAULT 'General Multispecialty',
    rating REAL DEFAULT 4.5,
    review_count INTEGER DEFAULT 150,
    category TEXT DEFAULT 'Multispecialty Hospital',
    specialties TEXT DEFAULT 'General Medicine, Emergency Care',
    emergency_24x7 BOOLEAN DEFAULT 1,
    phone TEXT,
    address TEXT,
    review_snippet TEXT
);
```

### Sample Enriched Hospital Records in SQLite

```json
[
  {
    "id": "hosp_1001",
    "name": "Kovai Medical Center and Hospital (KMCH)",
    "latitude": 11.0424,
    "longitude": 77.0378,
    "beds": 750,
    "emergency_specialty_24x7": "24/7 Cardiology, Trauma & Organ Transplant ICU",
    "best_sector": "Best Sector: Cardiac Surgery & Interventional Cardiology",
    "rating": 4.7,
    "review_count": 5120,
    "category": "Super Specialty Hospital",
    "specialties": "Cardiology, Trauma, Neurology, Oncology",
    "phone": "+91 422 4323800",
    "address": "Avinashi Road, Peelamedu, Coimbatore",
    "review_snippet": "Outstanding 24/7 cardiac ICU emergency response and doctors."
  },
  {
    "id": "hosp_1002",
    "name": "Sri Ramakrishna Hospital",
    "latitude": 11.0168,
    "longitude": 76.9558,
    "beds": 550,
    "emergency_specialty_24x7": "24/7 Pediatric ICU & Neonatal Care",
    "best_sector": "Best Sector: Pediatrics & Oncology",
    "rating": 4.6,
    "review_count": 4234,
    "category": "Multispecialty Hospital",
    "specialties": "Pediatrics, Oncology, Nephrology, Surgery",
    "phone": "+91 422 4500000",
    "address": "395, Sarojini Naidu Rd, Sidhapudur, Coimbatore",
    "review_snippet": "Immediate emergency admission and excellent pediatric doctors."
  },
  {
    "id": "hosp_1003",
    "name": "PSG Hospitals",
    "latitude": 11.0289,
    "longitude": 77.0031,
    "beds": 900,
    "emergency_specialty_24x7": "24/7 Polytrauma & Neurosurgery ICU",
    "best_sector": "Best Sector: Polytrauma & Neurological Sciences",
    "rating": 4.8,
    "review_count": 6890,
    "category": "Teaching & Super Specialty Hospital",
    "specialties": "Neurosurgery, Orthopedics, Gastroenterology",
    "phone": "+91 422 2570170",
    "address": "Peelamedu, Avinashi Rd, Coimbatore",
    "review_snippet": "Top tier trauma care equipment and skilled specialists."
  }
]
```

---

## 🎨 2. Clean Labelled SVG Data Point Markers

On the Leaflet map canvas, markers render as **simple, clean SVG data points** with crisp text labels:

```typescript
function createSimpleLabelledMarkerSvg(labelNumber: number, hospitalName: string): string {
  return `
    <div style="display: flex; align-items: center; gap: 6px; background-color: #1f2937; border: 1.5px solid #ef4444; border-radius: 20px; padding: 2px 8px; box-shadow: 0 4px 10px rgba(0,0,0,0.6); white-space: nowrap;">
      <svg width="18" height="18" viewBox="0 0 18 18">
        <circle cx="9" cy="9" r="7" fill="#ef4444" stroke="#ffffff" stroke-width="1.5"/>
        <text x="9" y="9" text-anchor="middle" dominant-baseline="central" fill="#ffffff" font-size="10px" font-weight="bold">${labelNumber}</text>
      </svg>
      <span style="color: #ffffff; font-size: 11px; font-weight: 700; font-family: system-ui;">${hospitalName}</span>
    </div>
  `;
}
```

---

## 📂 Proposed File Changes (Pending Review)

### Database Layer

#### [MODIFY] [agents/database.py](file:///d:/health_care/agents/database.py)
- Create `hospitals` table in SQLite (`healthcare.db`) storing `beds`, `emergency_specialty_24x7`, and `best_sector`.
- Seed 275+ enriched Coimbatore spatial hospital records.

#### [MODIFY] [agents/server.py](file:///d:/health_care/agents/server.py)
- Implement `GET /api/hospitals` API querying SQLite with GPS parameters (`lat`, `lng`, `radiusKm`, `query`, `specialty`).

---

### Dependencies

#### [MODIFY] [frontend/package.json](file:///d:/health_care/frontend/package.json)
- Add `leaflet` (`^1.9.4`) and `@types/leaflet`.

---

### Data Asset Layer

#### [NEW] [frontend/public/data/coimbatore_boundary.geojson](file:///d:/health_care/frontend/public/data/coimbatore_boundary.geojson)
- Copy municipal boundary polygon for Leaflet canvas mask rendering.

---

### Frontend Component Layer

#### [NEW] [frontend/src/components/HospitalMap.jsx](file:///d:/health_care/frontend/src/components/HospitalMap.jsx)
- Full-bleed Leaflet map with satellite/street layer toggle, neon boundary stroke, 65% dark terrain isolation mask, clean labelled SVG data point pins, GPS location blue dot (`🔵 You`), and pin click callback to locate left cards.

#### [NEW] [frontend/src/components/EmergencyFilterPane.jsx](file:///d:/health_care/frontend/src/components/EmergencyFilterPane.jsx)
- Left drawer panel containing hospital name search input, radius slider (1–50 km), category filter chips, GPS prompt banner, and scrollable hospital cards displaying **Beds**, **24/7 Specialty**, **Best Sector**, and direct Google Maps navigation buttons.

#### [MODIFY] [frontend/src/pages/PatientPortal.jsx](file:///d:/health_care/frontend/src/pages/PatientPortal.jsx)
- Add sub-tab label **🗺️ Mapping** embedding `EmergencyFilterPane` & `HospitalMap`.

---

## 🧪 Verification Plan

### Automated Verification
1. Run `npm install leaflet` in `frontend/`.
2. Run `python scratch/verify_auth_db.py` to verify SQLite `hospitals` table creation and test `GET /api/hospitals` endpoint responses with GPS parameters.

### Manual UI Verification
1. Open Patient Health Portal at `http://localhost:5173/`.
2. Click sub-tab **🗺️ Mapping**.
3. Allow browser location access and verify pulsing blue dot (`🔵 You`).
4. Inspect left drawer hospital cards for **Beds**, **24/7 Emergency Specialty**, and **Best Sector** badges.
5. Click a hospital card in the left pane to confirm instant redirect to Google Maps navigation in a new browser tab.
6. Click a map data point pin to confirm it locates and highlights the card in the left pane.

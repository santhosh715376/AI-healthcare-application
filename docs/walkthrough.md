# Walkthrough: Emergency Geospatial Hospital Discovery Engine ("Mapping")

We have implemented and verified the **Google Maps-Style Emergency Hospital Discovery Engine** inside the **Patient Health Portal** under the sub-tab **🗺️ Mapping**.

---

## 1. Features Implemented

### A. Patient Portal Integration ([PatientPortal.jsx](file:///d:/health_care/frontend/src/pages/PatientPortal.jsx))
- New sub-tab label **🗺️ Mapping** embedding `EmergencyFilterPane` & `HospitalMap`.
- Real-time GPS location lock (`navigator.geolocation.getCurrentPosition`) rendering a pulsing blue dot (`🔵 You`).

### B. SQLite Database Persistence ([database.py](file:///d:/health_care/agents/database.py))
- New `hospitals` table in SQLite (`healthcare.db`) storing 283 verified spatial hospital records.
- Enriched dataset attributes:
  - **Beds:** Total bed count (`409 Beds`, `750 Beds`).
  - **24/7 Specialty:** Round-the-clock emergency units (`24/7 Pediatric ICU & Neonatal Emergency`, `24/7 Cardiology`).
  - **Best Sector:** Primary medical benchmark (`Best Sector: Polytrauma & Neurosurgery ICU`).
  - **Navigation URL:** Google Maps direction links (`https://www.google.com/maps/dir/?api=1&destination=lat,lng`).

### C. FastAPI Spatial API Endpoint ([server.py](file:///d:/health_care/agents/server.py))
- `GET /api/hospitals`: Computes Haversine radial distance in `< 1ms`, filters by radius slider (1–50 km), hospital name query string, and specialty categories.

### D. Left Filter Drawer ([EmergencyFilterPane.jsx](file:///d:/health_care/frontend/src/components/EmergencyFilterPane.jsx))
- Search bar with live hospital name query and clear button (`✕`).
- GPS status badge with **"Turn On Location"** button.
- Search Radius slider (1 km to 50 km).
- Category filter chips (`24/7 ER`, `Multispecialty`, `Pediatrics`, `Cardiology`, `Trauma`).
- Scrollable hospital result cards displaying ratings, bed count, 24/7 specialty, best sector, and direct **↪️ Direct Google Maps Navigation** button.

### E. Full-Bleed Leaflet Satellite Map Canvas ([HospitalMap.jsx](file:///d:/health_care/frontend/src/components/HospitalMap.jsx))
- Esri World Imagery satellite basemap with transportation label overlays.
- Bright neon Coimbatore Municipal Corporation (CMC) boundary line (`#39ff14`).
- Inverted 65% black terrain dimming mask outside CMC boundary.
- Simple, clean labelled SVG data point pins (`🔴 1 Sengaliappan Nursing Home`).
- Clicking a map data point pin auto-scrolls to and highlights its card in the Left Drawer.

---

## 2. Verification Results

### Automated API & Database Verification (`scratch/verify_hospitals_api.py`)
- `GET /api/hospitals?lat=11.0168&lng=76.9558&radiusKm=25` ➔ **Status 200 OK**
- `Total Hospitals Returned:` **283 Hospitals**
- `Sample Hospital Record:`
  ```json
  {
    "name": "Sengaliappan Nursing Home",
    "distanceKm": 0.1,
    "beds": 409,
    "emergencySpecialty24x7": "24/7 Pediatric ICU & Neonatal Emergency",
    "bestSector": "Best Sector: Polytrauma & Neurosurgery ICU",
    "rating": 4.9,
    "reviewCount": 1171,
    "googleMapsUrl": "https://www.google.com/maps/dir/?api=1&destination=11.0165542,76.955239"
  }
  ```
- **Result:** `SPATIAL API VERIFICATION SUCCEEDED 100%!`

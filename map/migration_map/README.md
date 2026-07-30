# 🗺️ Migration Package: Hospital Geospatial Mapping Component

This self-contained directory (`migration_map`) contains everything required to drop the **Coimbatore Hospital Geospatial Mapping Engine** into any Next.js (or React/Fullstack) application with **zero friction**.

---

## 📁 Package Directory Structure

```
migration_map/
├── data/
│   ├── coimbatore_boundary.geojson      # Official CMC spatial polygon boundary (EPSG:4326)
│   └── coimbatore_hospitals_osm.json    # Strict point-in-polygon clipped hospital dataset
├── components/
│   └── HospitalMap.tsx                  # Leaflet map with satellite tiles, neon boundary & dimming mask
├── scripts/
│   └── agent_0_coimbatore_hospital_pipeline.py  # LangGraph / Python data ingestion & spatial filter pipeline
├── api/
│   └── hospitals/
│       └── route.ts                      # Ready-to-use Next.js App Router API endpoint (/api/hospitals)
└── README.md                            # This integration guide
```

---

## 🚀 3-Step Quick Integration Guide for New Workspaces

When you copy `migration_map` into a new project, follow these 3 quick steps:

### Step 1: Copy Assets into Target App Folders
From your target project root, copy the files:

```bash
# 1. Copy public spatial data assets
cp -r migration_map/data/ public/data/

# 2. Copy the map component into components
cp migration_map/components/HospitalMap.tsx src/components/features/

# 3. Copy API route handler into app router
cp -r migration_map/api/hospitals/ src/app/api/
```

### Step 2: Ensure Leaflet Dependencies are Installed
Make sure your target `package.json` includes Leaflet & Framer Motion:

```bash
npm install leaflet framer-motion lucide-react
npm install -D @types/leaflet
```

### Step 3: Render the Map Component
In any Next.js page (e.g. `src/app/hospitals/page.tsx`), render the dynamic Leaflet map:

```tsx
import dynamic from 'next/dynamic';

const HospitalMap = dynamic(() => import('@/components/features/HospitalMap'), { 
  ssr: false,
  loading: () => <div className="h-[600px] flex items-center justify-center bg-gray-900 text-white font-medium">Loading Map...</div>
});

export default function Page() {
  return (
    <div className="w-full h-[700px]">
      <HospitalMap 
        hospitals={hospitalList} 
        center={{ lat: 11.0168, lng: 76.9558 }} 
        radiusKm={15} 
      />
    </div>
  );
}
```

---

## ⚙️ Key Technical Features Included
- **Strict Boundary Isolation**: Inverted polygon hole mask dims all land outside Coimbatore Municipal Corporation by 65%.
- **Satellite Hybrid Basemap**: Esri World Imagery tiles with transportation/places label overlays.
- **Dynamic Radius Circle**: Rendered in dashed blue meters relative to user position.
- **Interactive Popup**: Google Maps direction links, ER availability tags, bed counts, and AI ranking badges.

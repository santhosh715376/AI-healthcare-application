# Implementation Plan: Coimbatore District Boundary Topology & Spatial Mapping Specification

## 1. Boundary Layer Selection & Performance Optimization

[Certain] Attempting to load all 295 revenue villages or 227 village panchayats into a Leaflet React web canvas will freeze the DOM thread due to rendering over 50,000 polygon vertex vectors simultaneously.

To achieve smooth 60 FPS map interaction while maintaining exact spatial administrative coverage across Coimbatore District, we specify **two optimal boundary sections**:

---

### Layer A (District-Wide Tier): The 11 Taluk Boundaries
**Coverage:** 
1. Coimbatore North
2. Coimbatore South
3. Pollachi
4. Kinathukadavu
5. Mettupalayam
6. Sulur
7. Annur
8. Perur
9. Madukkarai
10. Anaimalai
11. Valparai

**Why 11 Taluks:**
- Gives complete administrative coverage of the entire Coimbatore District from Mettupalayam (North) to Valparai (South) and Sulur (East).
- Allows spatial point-in-polygon queries (e.g., `"Which Taluk is patient in?"` -> `"Mettupalayam Taluk"` -> Filter 24/7 mountain highway trauma centers).
- Lightweight rendering (~150 KB GeoJSON vs. 15 MB for 295 villages).

---

### Layer B (Urban Core Tier): The 100 Wards of CCMC (Coimbatore City Municipal Corporation)
**Coverage:** 
- Wards 1 to 100 covering North, South, East, West, and Central zones of Coimbatore City proper.

**Why 100 CCMC Wards:**
- Handles high-density urban hospital cluster navigation inside Coimbatore city (KMCH, PSG, Sri Ramakrishna, Ganga Hospital).

---

## 2. High-Level Architecture (HLD)

```text
 ┌──────────────────────────────────────────────────────────────────────────────────────────┐
 │                      COIMBATORE DISTRICT DUAL-TIER BOUNDARY SYSTEM                       │
 └─────────────────────────────────────────────┬────────────────────────────────────────────┘
                                               │
               ┌───────────────────────────────┴───────────────────────────────┐
               ▼                                                               ▼
 ┌───────────────────────────┐                                   ┌───────────────────────────┐
 │   TIER A: 11 TALUK GeoJSON│                                   │ TIER B: 100 CCMC WARD     │
 │   (District-Wide Filter)  │                                   │ GeoJSON (Urban City Core) │
 └─────────────┬─────────────┘                                   └─────────────┬─────────────┘
               │                                                               │
               │ Points-in-Polygon (Taluk Level)                               │ Points-in-Polygon (City Level)
               ▼                                                               ▼
 ┌───────────────────────────────────────────────────────────────────────────────────────────┐
 │                      `HospitalDB` Spatial Query (283 Hydrated Nodes)                      │
 └───────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Verification & File Specifications

Target local files:
- **`frontend/public/data/coimbatore_taluks.geojson`:** Contains the 11 Taluk polygon features.
- **`frontend/public/data/coimbatore_wards.geojson`:** Contains the 100 CCMC Ward polygon features.

Review this boundary specification artifact and confirm so we can load the 11 Taluk topology file into the mapping service.

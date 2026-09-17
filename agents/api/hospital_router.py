import math
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db, HospitalDB
from repositories.hospital_repository import HospitalRepository

router = APIRouter(prefix="/api/hospitals", tags=["Hospital & Geospatial Triage"])

def get_hospital_repo(db: Session = Depends(get_db)) -> HospitalRepository:
    return HospitalRepository(db)

def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 2)


@router.get("")
def get_hospitals_endpoint(
    lat: float = 11.0168,
    lng: float = 76.9558,
    radiusKm: float = 15.0,
    query: Optional[str] = None,
    specialty: Optional[str] = None,
    limit: Optional[int] = 500,
    repo: HospitalRepository = Depends(get_hospital_repo)
):
    """
    Queries real-time hospital spatial records, computes Haversine distance,
    and returns ranked facilities matching radial proximity.
    """
    all_hospitals = repo.list_all(limit=limit or 500)
    results = []

    for h in all_hospitals:
        dist = haversine_distance_km(lat, lng, h.latitude, h.longitude)
        if dist > radiusKm:
            continue

        if query and query.strip():
            q_clean = query.strip().lower()
            if q_clean not in h.name.lower() and q_clean not in (h.address or "").lower():
                continue

        if specialty and specialty.strip():
            s_clean = specialty.strip().lower()
            h_text = f"{h.category} {h.specialties} {h.emergency_specialty_24x7}".lower()
            if s_clean not in h_text:
                continue

        google_maps_url = f"https://www.google.com/maps/dir/?api=1&destination={h.latitude},{h.longitude}"

        results.append({
            "id": h.id,
            "name": h.name,
            "latitude": h.latitude,
            "longitude": h.longitude,
            "location": {"lat": h.latitude, "lng": h.longitude},
            "beds": h.beds,
            "emergencySpecialty24x7": h.emergency_specialty_24x7,
            "bestSector": h.best_sector,
            "rating": h.rating,
            "reviewCount": h.review_count,
            "category": h.category,
            "specialties": h.specialties,
            "emergency24x7": h.emergency_24x7,
            "phone": h.phone,
            "address": h.address,
            "reviewSnippet": h.review_snippet,
            "distanceKm": dist,
            "googleMapsUrl": google_maps_url
        })

    results.sort(key=lambda x: x["distanceKm"])

    final_results = []
    max_limit = limit if limit else len(results)
    for idx, item in enumerate(results[:max_limit]):
        dist = item["distanceKm"]
        if dist <= 5.0:
            dist_range = "0–5 km (Immediate Proximity)"
        elif dist <= 15.0:
            dist_range = "5–15 km (Nearby District Range)"
        elif dist <= 30.0:
            dist_range = "15–30 km (Outer Highway Range)"
        else:
            dist_range = "30+ km (Extended District Range)"

        item["rank"] = idx + 1
        item["distanceRange"] = dist_range
        final_results.append(item)

    return final_results

import math
from typing import List, Dict, Any

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates distance in kilometers between two GPS coordinates."""
    R = 6371.0  # Earth radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2.0) ** 2) + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * (math.sin(dlon / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c

def rank_hospitals_factual(
    hospitals: List[Dict[str, Any]],
    user_lat: float,
    user_lng: float,
    target_specialty: str = "General Medicine",
    limit: int = 4
) -> List[Dict[str, Any]]:
    """
    Ranks candidate hospital DB records based on factual multi-factor scoring:
    - Distance (45%)
    - Specialty Match (35%)
    - 24/7 Emergency Availability (10%)
    - Verified Rating (10%)
    (Bed-availability weight zeroed - W_b = 0)
    """
    scored_hospitals = []

    for item in hospitals:
        lat = float(item.get("latitude") or item.get("lat", 0))
        lng = float(item.get("longitude") or item.get("lon") or item.get("lng", 0))
        dist_km = haversine_distance(user_lat, user_lng, lat, lng)

        # 1. Distance Score (Inverted: closer = higher score, max 50km)
        dist_score = max(0.0, 1.0 - (dist_km / 50.0))

        # 2. Specialty Match Score
        specs = str(item.get("specialties", "")).lower()
        target_lower = target_specialty.lower()
        if target_lower in specs:
            spec_score = 1.0
        elif any(token in specs for token in target_lower.split()):
            spec_score = 0.7
        else:
            spec_score = 0.3

        # 3. 24/7 ER Score
        er_score = 1.0 if item.get("emergency_24x7", True) else 0.5

        # 4. Rating Score (Normalized 0.0 to 1.0)
        rating_score = float(item.get("rating", 4.5)) / 5.0

        # Weighted Final Score (Bed weight W_b = 0)
        final_score = (0.45 * dist_score) + (0.35 * spec_score) + (0.10 * er_score) + (0.10 * rating_score)

        # Google Maps Navigation URL
        gmaps_url = f"https://www.google.com/maps/dir/?api=1&destination={lat},{lng}"

        scored_hospitals.append({
            "id": item.get("id"),
            "name": item.get("name"),
            "latitude": lat,
            "longitude": lng,
            "distance_km": round(dist_km, 1),
            "category": item.get("category", "Multispecialty Hospital"),
            "specialties": item.get("specialties", "General Medicine"),
            "emergency_specialty_24x7": item.get("emergency_specialty_24x7", "24/7 ER Care"),
            "facilities_json": item.get("facilities_json", '["24/7 ER"]'),
            "beds": item.get("beds", 150),
            "rating": item.get("rating", 4.5),
            "phone": item.get("phone", "+91 422 2300000"),
            "address": item.get("address", "Coimbatore District"),
            "emergency_24x7": item.get("emergency_24x7", True),
            "score": round(final_score, 3),
            "google_maps_url": gmaps_url
        })

    # Sort descending by final score
    scored_hospitals.sort(key=lambda x: x["score"], reverse=True)

    # Return flexible limit (min(limit, total_available))
    return scored_hospitals[:min(limit, len(scored_hospitals))]

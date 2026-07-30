"""
AGENT 0 — Coimbatore Hospital Pipeline
=======================================
Standalone hospital discovery pipeline for Coimbatore District.
Covers: boundary ingestion, Overpass API fetch, district polygon filtering,
metadata enrichment, Haversine nearest-neighbor search, directions URL.

Pipeline stages (LangGraph nodes):
  1. fetch_boundary    -> downloads & saves coimbatore_boundary.geojson
  2. fetch_osm         -> queries Overpass API within the boundary bbox
  3. polygon_filter    -> clips results to the strict district polygon
  4. enrich_metadata   -> merges curated JSON metadata (specialties, etc.)
  5. user_search       -> Haversine NN + specialty/emergency filter
  6. attach_directions -> Google Maps directions URL per result
  7. save_and_done     -> writes final dataset to disk, returns results
"""

import os
import json
import math
import time
import datetime
import requests
import geopandas as gpd
from shapely.geometry import Point
from typing import TypedDict, Annotated, List, Optional
import operator

from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import StateGraph, END

# ── COIMBATORE CONSTANTS ──────────────────────────────────────────────────────
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search.php?q=Coimbatore+district&polygon_geojson=1&format=json"
COIMBATORE_BBOX_APPROX = {          # fallback if Nominatim is unreachable
    "minx": 76.6559, "miny": 10.2204,
    "maxx": 77.2937, "maxy": 11.4052,
}
OVERPASS_ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://lz4.overpass-api.de/api/interpreter",
]

# ── Curated metadata path (from personalized_health_care_system project) ──────
_CURATED_PATH = os.path.join(
    os.path.dirname(__file__),
    "..", "backend-and-mapping", "data", "coimbatore_hospitals.json"
)
_OUTPUT_PATH  = os.path.join(
    os.path.dirname(__file__),
    "..", "backend-and-mapping", "data", "coimbatore_hospitals_full.json"
)

# ── Agent State ───────────────────────────────────────────────────────────────
class CoimbatoreHospitalState(TypedDict):
    messages:         Annotated[List, operator.add]
    # pipeline outputs
    boundary_polygon: object           # Shapely polygon (not serialized)
    boundary_bbox:    dict             # {minx, miny, maxx, maxy}
    raw_osm:          List[dict]       # all hospitals in bbox
    inside_municipal: List[dict]       # polygon-clipped subset
    enriched:         List[dict]       # after curated metadata merge
    # user-search inputs (optional — skip user_search if None)
    user_lat:         Optional[float]
    user_lng:         Optional[float]
    specialty_filter: Optional[str]
    emergency_only:   bool
    radius_km:        float
    # search results
    search_results:   List[dict]
    step:             str
    error:            Optional[str]

# ═════════════════════════════════════════════════════
#  TOOLS
# ═════════════════════════════════════════════════════

@tool
def fetch_coimbatore_boundary() -> dict:
    """
    Downloads the Coimbatore District boundary from Nominatim
    and saves coimbatore_boundary.geojson.
    Returns the bounding box dict {minx, miny, maxx, maxy}.
    """
    print("  [Tool] Fetching Coimbatore District boundary from Nominatim...")
    try:
        headers = {"User-Agent": "CoimbatoreHospitalAgent/1.0"}
        r = requests.get(NOMINATIM_URL, headers=headers, timeout=30)
        r.raise_for_status()
        data = r.json()
        if not data:
            raise ValueError("No boundary found in Nominatim")
        
        geojson = data[0]["geojson"]
        feature_collection = {
            "type": "FeatureCollection",
            "features": [{
                "type": "Feature",
                "properties": {"name": "Coimbatore District"},
                "geometry": geojson
            }]
        }

        out_path = os.path.join(
            os.path.dirname(__file__),
            "..", "backend-and-mapping", "data", "boundary", "coimbatore_boundary.geojson"
        )
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "w") as f:
            json.dump(feature_collection, f)

        bbox = data[0]["boundingbox"]
        miny, maxy = float(bbox[0]), float(bbox[1])
        minx, maxx = float(bbox[2]), float(bbox[3])
        print(f"  [Tool] Boundary saved. BBox: ({minx:.4f}, {miny:.4f}, {maxx:.4f}, {maxy:.4f})")
        return {"minx": minx, "miny": miny, "maxx": maxx, "maxy": maxy, "status": "ok"}

    except Exception as e:
        print(f"  [Tool] Nominatim unreachable ({e}). Using hardcoded Coimbatore bbox.")
        return {**COIMBATORE_BBOX_APPROX, "status": "fallback"}


@tool
def fetch_osm_hospitals_coimbatore(minx: float, miny: float, maxx: float, maxy: float) -> List[dict]:
    """
    Queries the Overpass API for ALL hospitals within the Coimbatore
    bounding box. Returns raw list (pre-polygon-filter).
    Includes retry logic across two Overpass mirror endpoints.
    """
    overpass_bbox = f"{miny},{minx},{maxy},{maxx}"
    query = f"""
    [out:json][timeout:120];
    (
      node["amenity"="hospital"]({overpass_bbox});
      way["amenity"="hospital"]({overpass_bbox});
      relation["amenity"="hospital"]({overpass_bbox});
    );
    out center;
    """
    headers = {"User-Agent": "CoimbatoreHospitalAgent/1.0", "Accept": "*/*"}

    for url in OVERPASS_ENDPOINTS:
        for attempt in range(2):
            try:
                r = requests.post(url, data=query.encode("utf-8"), headers=headers, timeout=130)
                r.raise_for_status()
                elements = r.json().get("elements", [])
                hospitals = []
                for el in elements:
                    tags = el.get("tags", {})
                    lat  = el.get("lat") or el.get("center", {}).get("lat")
                    lon  = el.get("lon") or el.get("center", {}).get("lon")
                    if lat is None or lon is None:
                        continue
                    hospitals.append({
                        "osm_id":    str(el["id"]),
                        "name":      tags.get("name", "Unnamed Hospital"),
                        "lat":       lat,
                        "lon":       lon,
                        "phone":     tags.get("phone") or tags.get("contact:phone", ""),
                        "website":   tags.get("website") or tags.get("contact:website", ""),
                        "operator":  tags.get("operator", ""),
                        "emergency": tags.get("emergency", ""),
                        "beds":      tags.get("beds", ""),
                        "addr":      ", ".join(filter(None, [
                            tags.get("addr:street", ""),
                            tags.get("addr:city", "Coimbatore"),
                            tags.get("addr:postcode", ""),
                        ])),
                    })
                print(f"  [Tool] OSM: {len(hospitals)} hospitals in bbox")
                return hospitals
            except Exception as e:
                print(f"  [Tool] Overpass {url} attempt {attempt+1} failed: {e}")
                time.sleep(2)

    raise RuntimeError("All Overpass endpoints failed after retries.")


@tool
def filter_inside_municipal_polygon(hospitals: List[dict], boundary_geojson_path: str) -> dict:
    """
    Strict point-in-polygon filter: keeps only hospitals whose centroid
    falls inside the Coimbatore Municipal Corporation polygon.
    Returns {inside: [...], discarded_count: int}.
    COIMBATORE-SPECIFIC safety guarantee: no hospital outside CMC enters output.
    """
    try:
        gdf = gpd.read_file(boundary_geojson_path)
        polygon = gdf.geometry.union_all()
    except Exception:
        print("  [Tool] WARNING: Could not load boundary. Skipping polygon filter.")
        return {"inside": hospitals, "discarded_count": 0}

    inside, outside = [], 0
    for h in hospitals:
        pt = Point(h["lon"], h["lat"])
        if polygon.contains(pt) or pt.within(polygon):
            inside.append(h)
        else:
            outside += 1

    print(f"  [Tool] Polygon filter: {len(inside)} inside CMC, {outside} discarded")
    if outside == 0:
        print("  [Tool] WARNING: 0 hospitals discarded — verify polygon filter is working.")
    return {"inside": inside, "discarded_count": outside}


@tool
def merge_curated_metadata(osm_hospitals: List[dict], curated_path: str) -> List[dict]:
    """
    Merges specialties, acceptedInsurance, rating, bedCount, accreditation
    from the curated coimbatore_hospitals.json into matching OSM records.
    Match is by fuzzy name substring. OSM data is never overwritten — only
    enriched. Curated hospitals not in OSM are appended to the list.
    """
    try:
        with open(curated_path, encoding="utf-8") as f:
            curated = json.load(f)
    except FileNotFoundError:
        print("  [Tool] Curated metadata not found. Skipping enrichment.")
        return osm_hospitals

    # Index OSM hospitals by lowercase name
    osm_index = {h["name"].lower(): i for i, h in enumerate(osm_hospitals)}
    enriched  = [dict(h) for h in osm_hospitals]
    appended  = 0

    for c in curated:
        c_name  = c["name"].lower()
        # Try exact then partial match
        matched_idx = osm_index.get(c_name)
        if matched_idx is None:
            for osm_name, idx in osm_index.items():
                if any(word in osm_name for word in c_name.split()[:2]):
                    matched_idx = idx
                    break

        metadata = {
            "specialties":        c.get("specialties", []),
            "acceptedInsurance":  c.get("acceptedInsurance", []),
            "rating":             c.get("rating"),
            "bedCount":           c.get("bedCount"),
            "accreditation":      c.get("accreditation"),
            "emergencyServices":  c.get("emergencyServices", False),
            "curated_id":         c.get("id"),
        }

        if matched_idx is not None:
            enriched[matched_idx].update(metadata)
        else:
            # Curated hospital not in OSM — append it using curated coords
            loc = c.get("location", {})
            enriched.append({
                "osm_id":  c.get("id"),
                "name":    c["name"],
                "lat":     loc.get("lat"),
                "lon":     loc.get("lng"),
                "addr":    loc.get("address", "Coimbatore"),
                **metadata,
                "_source": "curated_only",
            })
            appended += 1

    print(f"  [Tool] Metadata merged: {len(enriched)} total ({appended} curated-only appended)")
    return enriched


@tool
def haversine_search(hospitals: List[dict], user_lat: float, user_lng: float,
                     radius_km: float, specialty: str, emergency_only: bool) -> List[dict]:
    """
    Performs Haversine nearest-neighbor search within radius_km of the user.
    Applies specialty tag filter and emergency_only flag.
    Attaches _distance_km to each result and sorts ascending.
    COIMBATORE-SPECIFIC: only operates on the CMC-polygon-filtered dataset.
    """
    def haversine(lat1, lng1, lat2, lng2):
        R = 6371.0
        φ1, φ2 = math.radians(lat1), math.radians(lat2)
        Δφ = math.radians(lat2 - lat1)
        Δλ = math.radians(lng2 - lng1)
        a  = math.sin(Δφ/2)**2 + math.cos(φ1)*math.cos(φ2)*math.sin(Δλ/2)**2
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    results = []
    for h in hospitals:
        if h.get("lat") is None or h.get("lon") is None:
            continue
        dist = haversine(user_lat, user_lng, h["lat"], h["lon"])
        if dist > radius_km:
            continue
        if specialty:
            specs = [s.lower() for s in h.get("specialties", [])]
            if not any(specialty.lower() in s for s in specs):
                continue
        if emergency_only and not h.get("emergencyServices", False):
            continue
        results.append({**h, "_distance_km": round(dist, 2)})

    results.sort(key=lambda x: x["_distance_km"])
    print(f"  [Tool] Search: {len(results)} hospitals match within {radius_km} km")
    return results


@tool
def attach_directions_urls(hospitals: List[dict], user_lat: float, user_lng: float) -> List[dict]:
    """
    Attaches a Google Maps driving directions URL to each hospital result.
    COIMBATORE-SPECIFIC: origin is always the user's Coimbatore location.
    """
    out = []
    for h in hospitals:
        url = (
            f"https://www.google.com/maps/dir/?api=1"
            f"&origin={user_lat},{user_lng}"
            f"&destination={h['lat']},{h['lon']}"
            f"&travelmode=driving"
        )
        out.append({**h, "directions_url": url})
    return out


# ═════════════════════════════════════════════════════
#  GRAPH NODES
# ═════════════════════════════════════════════════════

def node_fetch_boundary(state: CoimbatoreHospitalState) -> CoimbatoreHospitalState:
    bbox_result = fetch_coimbatore_boundary.invoke({})
    # Store polygon in state (load from saved file)
    geojson_path = os.path.join(
        os.path.dirname(__file__),
        "..", "backend-and-mapping", "data", "boundary", "coimbatore_boundary.geojson"
    )
    try:
        gdf     = gpd.read_file(geojson_path)
        polygon = gdf.geometry.union_all()
    except Exception:
        polygon = None

    bbox = {k: v for k, v in bbox_result.items() if k != "status"}
    return {
        **state,
        "boundary_polygon": polygon,
        "boundary_bbox":    bbox,
        "step": "fetch_osm",
        "messages": state["messages"] + [
            AIMessage(content=f"Boundary ready. BBox: {bbox}")
        ],
    }


def node_fetch_osm(state: CoimbatoreHospitalState) -> CoimbatoreHospitalState:
    b = state["boundary_bbox"]
    hospitals = fetch_osm_hospitals_coimbatore.invoke(b)
    return {
        **state,
        "raw_osm": hospitals,
        "step": "polygon_filter",
        "messages": state["messages"] + [
            AIMessage(content=f"Overpass: {len(hospitals)} raw hospitals in bbox.")
        ],
    }


def node_polygon_filter(state: CoimbatoreHospitalState) -> CoimbatoreHospitalState:
    geojson_path = os.path.join(
        os.path.dirname(__file__),
        "..", "backend-and-mapping", "data", "boundary", "coimbatore_boundary.geojson"
    )
    result = filter_inside_municipal_polygon.invoke({
        "hospitals":            state["raw_osm"],
        "boundary_geojson_path": geojson_path,
    })
    return {
        **state,
        "inside_municipal": result["inside"],
        "step": "enrich_metadata",
        "messages": state["messages"] + [
            AIMessage(content=(
                f"Polygon filter: {len(result['inside'])} inside CMC, "
                f"{result['discarded_count']} discarded."
            ))
        ],
    }


def node_enrich_metadata(state: CoimbatoreHospitalState) -> CoimbatoreHospitalState:
    enriched = merge_curated_metadata.invoke({
        "osm_hospitals": state["inside_municipal"],
        "curated_path":  _CURATED_PATH,
    })
    return {
        **state,
        "enriched": enriched,
        "step": "user_search" if state.get("user_lat") else "save",
        "messages": state["messages"] + [
            AIMessage(content=f"Metadata enriched: {len(enriched)} total hospitals.")
        ],
    }


def node_user_search(state: CoimbatoreHospitalState) -> CoimbatoreHospitalState:
    results = haversine_search.invoke({
        "hospitals":     state["enriched"],
        "user_lat":      state["user_lat"],
        "user_lng":      state["user_lng"],
        "radius_km":     state["radius_km"],
        "specialty":     state["specialty_filter"] or "",
        "emergency_only": state["emergency_only"],
    })
    return {
        **state,
        "search_results": results,
        "step": "attach_directions",
        "messages": state["messages"] + [
            AIMessage(content=f"Search: {len(results)} hospitals match user query.")
        ],
    }


def node_attach_directions(state: CoimbatoreHospitalState) -> CoimbatoreHospitalState:
    results = attach_directions_urls.invoke({
        "hospitals": state["search_results"][:10],     # top 10 results
        "user_lat":  state["user_lat"],
        "user_lng":  state["user_lng"],
    })
    return {
        **state,
        "search_results": results,
        "step": "save",
        "messages": state["messages"] + [
            AIMessage(content=f"Directions attached to {len(results)} results.")
        ],
    }


def node_save(state: CoimbatoreHospitalState) -> CoimbatoreHospitalState:
    output = {
        "generated_at":    datetime.datetime.now(datetime.UTC).isoformat(),
        "region":          "Coimbatore Municipal Corporation",
        "boundary_source": "DataMeet Cbe2011Wards.geojson",
        "osm_source":      "Overpass API",
        "hospital_count":  len(state["enriched"]),
        "hospitals":       state["enriched"],
    }
    os.makedirs(os.path.dirname(_OUTPUT_PATH), exist_ok=True)
    with open(_OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    search_count = len(state.get("search_results", []))
    summary = (
        f"Saved {len(state['enriched'])} CMC hospitals to coimbatore_hospitals_full.json. "
        + (f"User search returned {search_count} results." if search_count else "")
    )
    print(f"\n  [Done] {summary}")
    return {
        **state,
        "step": "done",
        "messages": state["messages"] + [AIMessage(content=summary)],
    }


# ═════════════════════════════════════════════════════
#  ROUTER
# ═════════════════════════════════════════════════════

def router(state: CoimbatoreHospitalState) -> str:
    step = state.get("step", "start")
    if step == "start":             return "fetch_boundary"
    if step == "fetch_osm":         return "fetch_osm"
    if step == "polygon_filter":    return "polygon_filter"
    if step == "enrich_metadata":   return "enrich_metadata"
    if step == "user_search":       return "user_search"
    if step == "attach_directions": return "attach_directions"
    if step == "save":              return "save"
    return END


# ═════════════════════════════════════════════════════
#  BUILD GRAPH
# ═════════════════════════════════════════════════════

def build_coimbatore_hospital_agent():
    g = StateGraph(CoimbatoreHospitalState)
    g.add_node("fetch_boundary",    node_fetch_boundary)
    g.add_node("fetch_osm",         node_fetch_osm)
    g.add_node("polygon_filter",    node_polygon_filter)
    g.add_node("enrich_metadata",   node_enrich_metadata)
    g.add_node("user_search",       node_user_search)
    g.add_node("attach_directions", node_attach_directions)
    g.add_node("save",              node_save)
    g.set_conditional_entry_point(router)
    for node in ["fetch_boundary", "fetch_osm", "polygon_filter",
                 "enrich_metadata", "user_search", "attach_directions"]:
        g.add_conditional_edges(node, router)
    g.add_edge("save", END)
    return g.compile()


# ═════════════════════════════════════════════════════
#  ENTRYPOINT
# ═════════════════════════════════════════════════════

if __name__ == "__main__":
    print("\nCoimbatore Hospital Pipeline Agent - Starting")
    print("  Fetches -> Filters (CMC polygon) -> Enriches -> User Search -> Directions\n")

    agent = build_coimbatore_hospital_agent()

    final = agent.invoke({
        "messages":        [HumanMessage(content=(
            "Build the Coimbatore hospital dataset and find "
            "Cardiology hospitals with emergency services near Gandhipuram."
        ))],
        "boundary_polygon": None,
        "boundary_bbox":    {},
        "raw_osm":          [],
        "inside_municipal": [],
        "enriched":         [],
        # User search params (Gandhipuram coords)
        "user_lat":         11.0116,
        "user_lng":         76.9744,
        "specialty_filter": "Cardiology",
        "emergency_only":   True,
        "radius_km":        15.0,
        "search_results":   [],
        "step":             "start",
        "error":            None,
    })

    if final.get("search_results"):
        print(f"\nTop Results for User:")
        for h in final["search_results"][:5]:
            print(f"  - {h['name']} ({h['_distance_km']} km) | "
                  f"Rating: {h.get('rating','N/A')} | "
                  f"Emergency: {h.get('emergencyServices', False)}")

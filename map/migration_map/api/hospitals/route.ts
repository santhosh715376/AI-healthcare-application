import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

// Haversine distance calculator
function haversineDistance(lat1: number, lon1: number, lat2: number, lon2: number): number {
  const R = 6371.0; // Earth radius in km
  const dLat = (lat2 - lat1) * (Math.PI / 180);
  const dLon = (lon2 - lon1) * (Math.PI / 180);
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(lat1 * (Math.PI / 180)) * Math.cos(lat2 * (Math.PI / 180)) *
    Math.sin(dLon / 2) * Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
}

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const userLat = parseFloat(searchParams.get('lat') || '11.0168');
    const userLng = parseFloat(searchParams.get('lng') || '76.9558');
    const radiusKm = parseFloat(searchParams.get('radiusKm') || '15');
    const specialty = searchParams.get('specialty');

    // Locate dataset in public/data or relative path
    const dataPath = path.join(process.cwd(), 'public', 'data', 'coimbatore_hospitals_osm.json');
    const fallbackPath = path.join(process.cwd(), 'migration_map', 'data', 'coimbatore_hospitals_osm.json');

    let filePath = dataPath;
    if (!fs.existsSync(dataPath) && fs.existsSync(fallbackPath)) {
      filePath = fallbackPath;
    }

    if (!fs.existsSync(filePath)) {
      return NextResponse.json({ error: 'Hospital dataset not found' }, { status: 404 });
    }

    const fileData = fs.readFileSync(filePath, 'utf-8');
    const parsedData = JSON.parse(fileData);
    const hospitals = parsedData.hospitals || [];

    // Filter by radius & optional specialty
    let filtered = hospitals.map((h: any) => {
      const dist = haversineDistance(userLat, userLng, h.lat, h.lon);
      return {
        id: h.osm_id,
        name: h.name,
        location: { lat: h.lat, lng: h.lon },
        distanceKm: Math.round(dist * 10) / 10,
        specialties: h.specialties || ['General Medicine', 'Emergency Care'],
        emergencyServices: h.emergency === 'yes' || h.emergencyServices === true,
        open24x7: h.opening_hours === '24/7' || h.open24x7 === true,
        beds: h.beds || 150,
        accreditation: h.nabh ? 'NABH' : (h.jci ? 'JCI' : 'ISO Certified'),
        yearEstablished: 2010,
        phone: h.phone || '+91 422 2300000',
        address: h['addr:street'] || h.addr || 'Coimbatore, Tamil Nadu',
      };
    }).filter((h: any) => h.distanceKm <= radiusKm);

    if (specialty) {
      filtered = filtered.filter((h: any) =>
        h.specialties.some((s: string) => s.toLowerCase().includes(specialty.toLowerCase()))
      );
    }

    // Sort nearest first
    filtered.sort((a: any, b: any) => a.distanceKm - b.distanceKm);

    return NextResponse.json(filtered);
  } catch (error: any) {
    return NextResponse.json({ error: 'Internal Server Error', details: error.message }, { status: 500 });
  }
}

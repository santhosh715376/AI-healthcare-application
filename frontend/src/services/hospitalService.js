import { apiRequest, DEFAULT_LAT, DEFAULT_LNG } from './api';

export async function fetchHospitals({
  lat = DEFAULT_LAT,
  lng = DEFAULT_LNG,
  radiusKm = 15.0,
  query = '',
  specialty = '',
  limit = 500
} = {}) {
  const params = new URLSearchParams();
  params.set('lat', lat);
  params.set('lng', lng);
  params.set('radiusKm', radiusKm);
  if (query) params.set('query', query);
  if (specialty) params.set('specialty', specialty);
  if (limit) params.set('limit', limit);

  return apiRequest(`/api/hospitals?${params.toString()}`);
}

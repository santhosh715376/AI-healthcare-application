export const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
export const DEFAULT_LAT = parseFloat(import.meta.env.VITE_DEFAULT_LAT || '11.0168');
export const DEFAULT_LNG = parseFloat(import.meta.env.VITE_DEFAULT_LNG || '76.9558');

/**
 * Universal API client wrapping fetch with automatic JWT authentication header,
 * robust error parsing, and graceful session invalidation.
 */
export async function apiRequest(path, options = {}) {
  const token = localStorage.getItem('access_token');
  const headers = {
    'Content-Type': 'application/json',
    ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
    ...options.headers,
  };

  if (options.body instanceof FormData) {
    delete headers['Content-Type'];
  }

  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  if (res.status === 401) {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user_profile');
  }

  if (!res.ok) {
    let errorDetail = `Request failed (${res.status})`;
    try {
      const errJson = await res.json();
      errorDetail = errJson.detail || errJson.message || errorDetail;
    } catch (_) {
      try {
        const errText = await res.text();
        if (errText) errorDetail = errText;
      } catch (_) {}
    }
    const err = new Error(errorDetail);
    err.status = res.status;
    throw err;
  }

  return res.json();
}

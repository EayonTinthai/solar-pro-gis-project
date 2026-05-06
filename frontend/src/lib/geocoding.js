/**
 * Geocoding utility using Nominatim (OpenStreetMap) as default.
 * Falls back gracefully if Google Maps API key is available.
 */

const GOOGLE_API_KEY = typeof import.meta !== 'undefined'
  ? (import.meta.env?.VITE_GOOGLE_API_KEY || '')
  : '';

const NOMINATIM_BASE = 'https://nominatim.openstreetmap.org';

// Rate limiting for Nominatim (max 1 request/second per their policy)
let lastNominatimRequest = 0;

async function throttleNominatim() {
  const now = Date.now();
  const elapsed = now - lastNominatimRequest;
  if (elapsed < 1100) {
    await new Promise((resolve) => setTimeout(resolve, 1100 - elapsed));
  }
  lastNominatimRequest = Date.now();
}

/**
 * Search for a place by query string.
 * Uses Google Maps Geocoding API if key is available, otherwise Nominatim.
 *
 * @param {string} query - Search query (address, place name, etc.)
 * @param {object} [options]
 * @param {string} [options.bounded] - Restrict to Bangkok area
 * @returns {Promise<Array<{lat: number, lon: number, displayName: string}>>}
 */
export async function searchPlace(query, options = {}) {
  if (!query || !query.trim()) return [];

  // Try Google first if key is available
  if (GOOGLE_API_KEY) {
    try {
      return await searchPlaceGoogle(query);
    } catch {
      // Fall through to Nominatim
    }
  }

  return searchPlaceNominatim(query, options);
}

/**
 * Reverse geocode coordinates to an address.
 *
 * @param {number} lat - Latitude
 * @param {number} lon - Longitude
 * @returns {Promise<{lat: number, lon: number, displayName: string} | null>}
 */
export async function reverseGeocode(lat, lon) {
  if (!Number.isFinite(lat) || !Number.isFinite(lon)) return null;

  // Try Google first if key is available
  if (GOOGLE_API_KEY) {
    try {
      return await reverseGeocodeGoogle(lat, lon);
    } catch {
      // Fall through to Nominatim
    }
  }

  return reverseGeocodeNominatim(lat, lon);
}

// --- Nominatim Implementation ---

async function searchPlaceNominatim(query, options = {}) {
  await throttleNominatim();

  const params = new URLSearchParams({
    q: query,
    format: 'json',
    limit: '5',
    addressdetails: '1',
  });

  // Bias results toward Bangkok area
  if (options.bounded !== false) {
    params.set('viewbox', '100.3,13.5,100.9,14.0');
    params.set('bounded', '0'); // Prefer but don't restrict
  }

  const response = await fetch(`${NOMINATIM_BASE}/search?${params}`, {
    headers: {
      'User-Agent': 'SolarPotentialApp/1.0',
      'Accept-Language': 'en,th',
    },
  });

  if (!response.ok) {
    throw new Error(`Nominatim search failed: ${response.status}`);
  }

  const results = await response.json();

  return results.map((r) => ({
    lat: parseFloat(r.lat),
    lon: parseFloat(r.lon),
    displayName: r.display_name,
    type: r.type,
    category: r.category,
    boundingBox: r.boundingbox
      ? {
          south: parseFloat(r.boundingbox[0]),
          north: parseFloat(r.boundingbox[1]),
          west: parseFloat(r.boundingbox[2]),
          east: parseFloat(r.boundingbox[3]),
        }
      : null,
  }));
}

async function reverseGeocodeNominatim(lat, lon) {
  await throttleNominatim();

  const params = new URLSearchParams({
    lat: String(lat),
    lon: String(lon),
    format: 'json',
    addressdetails: '1',
    zoom: '18',
  });

  const response = await fetch(`${NOMINATIM_BASE}/reverse?${params}`, {
    headers: {
      'User-Agent': 'SolarPotentialApp/1.0',
      'Accept-Language': 'en,th',
    },
  });

  if (!response.ok) {
    throw new Error(`Nominatim reverse geocode failed: ${response.status}`);
  }

  const result = await response.json();

  if (result.error) return null;

  return {
    lat: parseFloat(result.lat),
    lon: parseFloat(result.lon),
    displayName: result.display_name,
    address: result.address || null,
  };
}

// --- Google Maps Implementation ---

async function searchPlaceGoogle(query) {
  const params = new URLSearchParams({
    address: query,
    key: GOOGLE_API_KEY,
    // Bias toward Bangkok
    bounds: '13.5,100.3|14.0,100.9',
  });

  const response = await fetch(
    `https://maps.googleapis.com/maps/api/geocode/json?${params}`
  );

  if (!response.ok) {
    throw new Error(`Google geocoding failed: ${response.status}`);
  }

  const data = await response.json();

  if (data.status !== 'OK' || !Array.isArray(data.results)) {
    return [];
  }

  return data.results.map((r) => ({
    lat: r.geometry.location.lat,
    lon: r.geometry.location.lng,
    displayName: r.formatted_address,
    placeId: r.place_id,
  }));
}

async function reverseGeocodeGoogle(lat, lon) {
  const params = new URLSearchParams({
    latlng: `${lat},${lon}`,
    key: GOOGLE_API_KEY,
  });

  const response = await fetch(
    `https://maps.googleapis.com/maps/api/geocode/json?${params}`
  );

  if (!response.ok) {
    throw new Error(`Google reverse geocode failed: ${response.status}`);
  }

  const data = await response.json();

  if (data.status !== 'OK' || !data.results?.length) {
    return null;
  }

  const top = data.results[0];
  return {
    lat,
    lon,
    displayName: top.formatted_address,
    placeId: top.place_id,
  };
}

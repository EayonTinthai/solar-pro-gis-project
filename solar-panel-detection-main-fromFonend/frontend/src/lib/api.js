/**
 * Central Buildings + Solar API client (Vite: import.meta.env.VITE_BUILDINGS_API_URL).
 */

export function getBaseUrl() {
  return import.meta.env.VITE_BUILDINGS_API_URL || 'http://localhost:8001';
}

/** @type {null | (() => Promise<string | null | undefined>)} */
let clerkGetToken = null;

/**
 * Wire Clerk session tokens into API calls (guest sign-in wall: pass null).
 * @param {null | (() => Promise<string | null | undefined>)} getToken
 */
export function configureApiAuth(getToken) {
  clerkGetToken = getToken;
}

/**
 * @param {string} path
 * @param {RequestInit} [options]
 * @returns {Promise<Response>}
 */
export async function rawFetch(path, options = {}) {
  const url = `${getBaseUrl()}${path.startsWith('/') ? path : `/${path}`}`;
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  };
  if (!headers.Authorization && clerkGetToken) {
    try {
      const token = await clerkGetToken();
      if (token) headers.Authorization = `Bearer ${token}`;
    } catch {
      // ignore — unauthenticated or Clerk still loading
    }
  }
  return fetch(url, {
    ...options,
    headers,
    mode: 'cors',
  });
}

/**
 * @param {string} path
 * @param {RequestInit} [options]
 */
export async function apiFetchJson(path, options = {}) {
  const res = await rawFetch(path, options);
  if (!res.ok) {
    const text = await res.text();
    const err = new Error(text || res.statusText || 'Request failed');
    err.status = res.status;
    err.path = path;
    throw err;
  }
  const ct = res.headers.get('content-type');
  if (ct && ct.includes('application/json')) {
    return res.json();
  }
  return null;
}

function parseGeometry(building) {
  if (!building.geometry) return { ...building, geometry: null };
  try {
    const g =
      typeof building.geometry === 'string'
        ? JSON.parse(building.geometry)
        : building.geometry;
    return { ...building, geometry: g };
  } catch {
    return { ...building, geometry: null };
  }
}

/**
 * @param {{ minLat: number, maxLat: number, minLon: number, maxLon: number }} bbox
 * @param {{ limit?: number, minConfidence?: number }} [options]
 */
export async function fetchBuildingsBbox(bbox, options = {}) {
  const {
    limit = 1000,
    minConfidence = 0.7,
  } = options;
  const params = new URLSearchParams({
    min_lat: String(bbox.minLat),
    max_lat: String(bbox.maxLat),
    min_lon: String(bbox.minLon),
    max_lon: String(bbox.maxLon),
    limit: String(limit),
    min_confidence: String(minConfidence),
  });
  const data = await apiFetchJson(`/buildings/bbox?${params}`);
  if (data.buildings) {
    data.buildings = data.buildings.map(parseGeometry);
  }
  return data;
}

/**
 * @param {number} lat
 * @param {number} lon
 * @param {{ radiusM?: number, limit?: number, minConfidence?: number }} [options]
 */
export async function fetchBuildingsNearby(lat, lon, options = {}) {
  const {
    radiusM = 500,
    limit = 100,
    minConfidence = 0.7,
  } = options;
  const params = new URLSearchParams({
    lat: String(lat),
    lon: String(lon),
    radius_m: String(radiusM),
    limit: String(limit),
    min_confidence: String(minConfidence),
  });
  const data = await apiFetchJson(`/buildings/nearby?${params}`);
  if (data.buildings) {
    data.buildings = data.buildings.map(parseGeometry);
  }
  return data;
}

/**
 * @param {number} buildingId
 */
export async function fetchBuildingById(buildingId) {
  const b = await apiFetchJson(`/buildings/${buildingId}`);
  return parseGeometry(b);
}

/** @returns {Promise<Record<string, unknown>>} */
export async function fetchStats() {
  return apiFetchJson('/stats');
}

/**
 * POST /solar/calculate
 * @param {{
 *   latitude: number,
 *   longitude: number,
 *   area_m2: number,
 *   confidence: number,
 *   tilt?: number|null,
 *   azimuth?: number|null,
 * }} body
 */
export async function fetchSolarCalculate(body) {
  return apiFetchJson('/solar/calculate', {
    method: 'POST',
    body: JSON.stringify(body),
  });
}

/**
 * POST /payments/create-checkout
 * @param {string} clerkUserId
 * @returns {Promise<{url: string}>}
 */
export async function createCheckoutSession(clerkUserId) {
  return apiFetchJson('/payments/create-checkout', {
    method: 'POST',
    body: JSON.stringify({ clerk_user_id: clerkUserId }),
  });
}

/**
 * POST /payments/portal
 * @param {string} clerkUserId
 * @returns {Promise<{url: string}>}
 */
export async function createPortalSession(clerkUserId) {
  return apiFetchJson('/payments/portal', {
    method: 'POST',
    body: JSON.stringify({ clerk_user_id: clerkUserId }),
  });
}

/**
 * GET /weather/forecast
 * @param {number} lat
 * @param {number} lon
 * @param {string} timezone
 * @returns {Promise<Object>}
 */
export async function fetchWeatherForecast(lat, lon, timezone = 'Asia/Bangkok') {
  const params = new URLSearchParams({
    lat: String(lat),
    lon: String(lon),
    timezone,
  });
  return apiFetchJson(`/weather/forecast?${params}`);
}

/**
 * GET /solar/forecast
 * @param {number} lat
 * @param {number} lon
 * @param {number} systemKwp
 * @param {string} timezone
 * @returns {Promise<Object>}
 */
export async function fetchSolarForecast(lat, lon, systemKwp, timezone = 'Asia/Bangkok') {
  const params = new URLSearchParams({
    lat: String(lat),
    lon: String(lon),
    system_kwp: String(systemKwp),
    timezone,
  });
  return apiFetchJson(`/solar/forecast?${params}`);
}

/**
 * @param {Array<Record<string, unknown>>} buildings
 */
export function buildingsToGeoJSON(buildings) {
  return {
    type: 'FeatureCollection',
    features: buildings.map((building) => ({
      type: 'Feature',
      id: building.id,
      geometry: building.geometry,
      properties: {
        id: building.id,
        open_buildings_id: building.open_buildings_id,
        area_m2: building.area_m2,
        confidence: building.confidence,
        latitude: building.latitude,
        longitude: building.longitude,
        distance_m: building.distance_m,
      },
    })),
  };
}

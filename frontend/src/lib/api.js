/**
 * Central Buildings + Solar API client (Vite: import.meta.env.VITE_BUILDINGS_API_URL).
 */

export function getBuildingsBaseUrl() {
    return import.meta.env.VITE_BUILDINGS_API_URL || 'http://localhost:8001';
}

export function getSolarWeatherBaseUrl() {
    return (
        import.meta.env.VITE_SOLAR_WEATHER_API_URL ||
        import.meta.env.VITE_BUILDINGS_API_URL ||
        'http://localhost:8001'
    );
}

// Backward compatible alias used by existing callers.
export function getBaseUrl() {
    return getBuildingsBaseUrl();
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

async function buildRequestHeaders(options = {}) {
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers,
    };
    if (!headers.Authorization && clerkGetToken) {
        try {
            const token = await clerkGetToken();
            if (token) headers.Authorization = `Bearer ${token}`;
        } catch {
            // ignore - unauthenticated or Clerk still loading
        }
    }
    return headers;
}

async function rawFetchWithBase(baseUrl, path, options = {}) {
    const url = `${baseUrl}${path.startsWith('/') ? path : `/${path}`}`;
    const headers = await buildRequestHeaders(options);
    return fetch(url, {
        ...options,
        headers,
        mode: 'cors',
    });
}

/**
 * @param {string} path
 * @param {RequestInit} [options]
 * @returns {Promise<Response>}
 */
export async function rawFetch(path, options = {}) {
    return rawFetchWithBase(getBuildingsBaseUrl(), path, options);
}

/**
 * @param {string} path
 * @param {RequestInit} [options]
 * @returns {Promise<Response>}
 */
export async function rawSolarWeatherFetch(path, options = {}) {
    return rawFetchWithBase(getSolarWeatherBaseUrl(), path, options);
}

async function buildApiError(res, path) {
    const contentType = res.headers.get('content-type') || '';
    let message = res.statusText || 'Request failed';
    let payload = null;

    try {
        if (contentType.includes('application/json')) {
            payload = await res.json();
            const detail = payload?.detail;
            if (typeof detail === 'string') {
                message = detail;
            } else if (Array.isArray(detail) && detail.length) {
                message = detail.map((item) => item?.msg || String(item)).join('; ');
            } else if (payload?.message) {
                message = String(payload.message);
            }
        } else {
            const text = await res.text();
            if (text) message = text;
        }
    } catch {
        // keep statusText fallback
    }

    const err = new Error(message || 'Request failed');
    err.status = res.status;
    err.path = path;
    err.payload = payload;
    return err;
}

/**
 * @param {string} path
 * @param {RequestInit} [options]
 */
export async function apiFetchJson(path, options = {}) {
    const res = await rawFetch(path, options);
    if (!res.ok) {
        throw await buildApiError(res, path);
    }
    const ct = res.headers.get('content-type');
    if (ct && ct.includes('application/json')) {
        return res.json();
    }
    return null;
}

function isSolarWeatherPath(path) {
    return path.startsWith('/solar/') || path.startsWith('/weather/');
}

function isValidForecastPayload(payload) {
    if (!payload || typeof payload !== 'object') return false;

    // Solar forecast payload shape used by the live service.
    const hasSolarForecast =
        payload.location &&
        typeof payload.location === 'object' &&
        Array.isArray(payload.hourly_forecast) &&
        Array.isArray(payload.weekly_outlook) &&
        (typeof payload.next_24h_generation_kwh === 'number' ||
            typeof payload.system_kwp === 'number');

    // Weather forecast fallback shape (keeps this logic reusable for /weather/*).
    const hasWeatherForecast =
        Array.isArray(payload.hourly) ||
        Array.isArray(payload.daily) ||
        typeof payload.current === 'object';

    return Boolean(hasSolarForecast || hasWeatherForecast);
}

/**
 * @param {string} path
 * @param {RequestInit} [options]
 */
export async function solarWeatherApiFetchJson(path, options = {}) {
    const res = await rawSolarWeatherFetch(path, options);

    let payload = null;
    const ct = res.headers.get('content-type');
    if (ct && ct.includes('application/json')) {
        try {
            payload = await res.json();
        } catch {
            payload = null;
        }
    }

    // Backend occasionally returns non-2xx with usable forecast JSON.
    if (isSolarWeatherPath(path) && isValidForecastPayload(payload)) {
        return payload;
    }

    if (!res.ok) {
        throw await buildApiError(res, path);
    }

    return payload;
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

/** @returns {Promise<Record<string, unknown>>} */
export async function fetchStatsDistribution() {
    return apiFetchJson('/stats/distribution');
}

function toFiniteNumber(value) {
    const n = Number(value);
    return Number.isFinite(n) ? n : null;
}

function parseRangeLabel(label) {
    const m = String(label).trim().match(/^(-?\d*\.?\d+)\s*-\s*(-?\d*\.?\d+)$/);
    if (!m) return null;
    const start = toFiniteNumber(m[1]);
    const end = toFiniteNumber(m[2]);
    if (start == null || end == null) return null;
    return { start, end };
}

function normalizeConfidenceBuckets(rawBuckets) {
    if (!rawBuckets || typeof rawBuckets !== 'object') return [];

    return Object.entries(rawBuckets)
        .map(([label, count]) => {
            const range = parseRangeLabel(label);
            const normalizedCount = toFiniteNumber(count) ?? 0;
            return {
                label: String(label),
                count: normalizedCount,
                start: range?.start ?? Number.POSITIVE_INFINITY,
                end: range?.end ?? Number.POSITIVE_INFINITY,
            };
        })
        .sort((a, b) => (a.start - b.start) || (a.end - b.end))
        .map(({ label, count }) => ({ label, count }));
}

function normalizeCumulativeByThreshold(rawCumulative) {
    if (!rawCumulative || typeof rawCumulative !== 'object') return [];

    return Object.entries(rawCumulative)
        .map(([threshold, count]) => {
            const t = toFiniteNumber(threshold);
            const c = toFiniteNumber(count);
            if (t == null || c == null) return null;
            return { threshold: t, count: c };
        })
        .filter(Boolean)
        .sort((a, b) => a.threshold - b.threshold);
}

function deriveConfidenceSplitFromBuckets(confidenceBuckets) {
    let high = 0;
    let medium = 0;
    let low = 0;

    for (const bucket of confidenceBuckets) {
        const range = parseRangeLabel(bucket.label);
        const count = toFiniteNumber(bucket.count) ?? 0;
        if (!range) continue;

        if (range.start >= 0.8) high += count;
        else if (range.start >= 0.7) medium += count;
        else low += count;
    }

    return { high, medium, low };
}

/**
 * Merge `/stats` and `/stats/distribution` into the legacy stats panel shape.
 * If distribution fetch fails, we still return core `/stats` payload.
 * @returns {Promise<Record<string, unknown>>}
 */
export async function fetchStatsWithDistribution() {
    const stats = await fetchStats();

    try {
        const distribution = await fetchStatsDistribution();
        const confidenceBuckets = normalizeConfidenceBuckets(distribution?.confidence_buckets);
        const cumulativeByThreshold = normalizeCumulativeByThreshold(
            distribution?.cumulative_by_threshold
        );

        return {
            ...stats,
            ...(confidenceBuckets.length ? { confidence_buckets: confidenceBuckets } : {}),
            ...(cumulativeByThreshold.length
                ? { cumulative_by_threshold: cumulativeByThreshold }
                : {}),
            ...(!stats?.confidence_split && confidenceBuckets.length
                ? { confidence_split: deriveConfidenceSplitFromBuckets(confidenceBuckets) }
                : {}),
        };
    } catch {
        return stats;
    }
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
    return solarWeatherApiFetchJson('/solar/calculate', {
        method: 'POST',
        body: JSON.stringify(body),
    });
}

/**
 * GET /weather/forecast
 * @param {{
 *   lat: number,
 *   lon: number,
 *   timezone?: string,
 * }} params
 */
export async function fetchWeatherForecast(params) {
    const query = new URLSearchParams({
        lat: String(params.lat),
        lon: String(params.lon),
        timezone: params.timezone || 'Asia/Bangkok',
    });
    return solarWeatherApiFetchJson(`/weather/forecast?${query}`);
}

/**
 * GET /solar/forecast
 * @param {{
 *   lat: number,
 *   lon: number,
 *   system_kwp: number,
 *   timezone?: string,
 * }} params
 */
export async function fetchSolarForecast(params) {
    const query = new URLSearchParams({
        lat: String(params.lat),
        lon: String(params.lon),
        system_kwp: String(params.system_kwp),
        timezone: params.timezone || 'Asia/Bangkok',
    });
    return solarWeatherApiFetchJson(`/solar/forecast?${query}`);
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

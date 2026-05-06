import { useEffect, useMemo, useRef } from 'react';
import { GeoJSON } from 'react-leaflet';
import { buildingsToGeoJSON } from '@/lib/api';
import {
  areaBucketColor,
  confidenceColor,
  flatPolygonColor,
  paybackColor,
} from '@/lib/utils';
import { calculateSolarPotential } from '@/lib/solar-calc';
import { isDrawModeActive } from '@/components/map/AoiSelector';

const GOOGLE_API_KEY = import.meta.env.VITE_GOOGLE_API_KEY || import.meta.env.GOOGLE_API_KEY || '';
const googleDetailsCache = new Map();

function formatArea(area) {
  const n = Number(area);
  return Number.isFinite(n) ? `${n.toFixed(1)} m²` : 'Unknown area';
}

function escapeHtml(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;');
}

function getGoogleMapsLink(lat, lng) {
  return `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(`${lat},${lng}`)}`;
}

function getGoogleStaticMapThumbnailUrl(lat, lng) {
  if (!GOOGLE_API_KEY) return null;
  const center = encodeURIComponent(`${lat},${lng}`);
  const marker = encodeURIComponent(`color:red|${lat},${lng}`);
  return `https://maps.googleapis.com/maps/api/staticmap?center=${center}&zoom=20&size=320x160&scale=2&maptype=satellite&markers=${marker}&key=${encodeURIComponent(GOOGLE_API_KEY)}`;
}

function getLayerLatLng(layer, event) {
  const center = layer?.getBounds?.()?.getCenter?.();
  const point = center ?? event?.latlng;
  const lat = Number(point?.lat);
  const lng = Number(point?.lng);
  if (!Number.isFinite(lat) || !Number.isFinite(lng)) return null;
  return { lat, lng };
}

function getCacheKey(props, lat, lng) {
  if (props?.id != null) return `id:${String(props.id)}`;
  return `coords:${lat.toFixed(6)},${lng.toFixed(6)}`;
}

async function fetchGoogleDetails(lat, lng) {
  if (!GOOGLE_API_KEY) return { status: 'unavailable' };

  const url =
    `https://maps.googleapis.com/maps/api/geocode/json?latlng=${encodeURIComponent(`${lat},${lng}`)}` +
    `&key=${encodeURIComponent(GOOGLE_API_KEY)}`;

  try {
    const res = await fetch(url);
    if (!res.ok) return { status: 'unavailable' };

    const data = await res.json();
    if (data?.status !== 'OK' || !Array.isArray(data?.results) || data.results.length === 0) {
      return { status: 'unavailable' };
    }

    const top = data.results[0] ?? {};
    return {
      status: 'ok',
      formattedAddress: top.formatted_address ?? null,
      placeId: top.place_id ?? null,
    };
  } catch {
    return { status: 'unavailable' };
  }
}

function fetchGoogleDetailsCached(props, lat, lng) {
  const key = getCacheKey(props, lat, lng);
  if (googleDetailsCache.has(key)) return googleDetailsCache.get(key);
  const request = fetchGoogleDetails(lat, lng);
  googleDetailsCache.set(key, request);
  return request;
}

function popupContent(props, details, latlng) {
  const id = escapeHtml(props?.id ?? '—');
  const area = escapeHtml(formatArea(props?.area_m2));
  const thumbUrl = latlng ? getGoogleStaticMapThumbnailUrl(latlng.lat, latlng.lng) : null;
  const addressHtml =
    details?.status === 'ok' && details?.formattedAddress
      ? `<p class="building-popup-meta">Address: ${escapeHtml(details.formattedAddress)}</p>`
      : '';
  const placeIdHtml =
    details?.status === 'ok' && details?.placeId
      ? `<p class="building-popup-meta">Place ID: ${escapeHtml(details.placeId)}</p>`
      : '';
  const statusHtml =
    details?.status === 'loading'
      ? '<p class="building-popup-meta">Loading Google details...</p>'
      : '';
  const thumbnailHtml = thumbUrl
    ? `<img class="building-popup-thumb" src="${escapeHtml(thumbUrl)}" alt="Building map thumbnail" loading="lazy" onerror="this.style.display='none'" />`
    : '';
  const mapsHtml = latlng
    ? `<p class="building-popup-meta"><a href="${escapeHtml(getGoogleMapsLink(latlng.lat, latlng.lng))}" target="_blank" rel="noopener noreferrer">Open in Google Maps</a></p>`
    : '';

  return `
    <div class="building-popup-content">
      <p class="building-popup-kicker">Building</p>
      <p class="building-popup-title">ID ${id}</p>
      <p class="building-popup-meta">Area: ${area}</p>
      ${thumbnailHtml}
      ${addressHtml}
      ${placeIdHtml}
      ${statusHtml}
      ${mapsHtml}
    </div>
  `;
}

/**
 * @param {'confidence' | 'area' | 'flat' | 'payback'} mode
 * @param {GeoJSON.Feature} feature
 * @param {number} minArea
 * @param {number} maxArea
 */
function leafletStyle(mode, feature, minArea, maxArea) {
  const p = feature.properties;
  const conf = p.confidence;
  const area = p.area_m2;
  if (mode === 'flat') {
    const { fill, stroke } = flatPolygonColor();
    return { fillColor: fill, color: stroke, fillOpacity: 0.35, weight: 1, opacity: 0.85 };
  }
  if (mode === 'area') {
    const { fill, stroke } = areaBucketColor(area, minArea, maxArea);
    return { fillColor: fill, color: stroke, fillOpacity: 0.35, weight: 1, opacity: 0.85 };
  }
  if (mode === 'payback') {
    const lat = p.latitude || 13.75;
    const lon = p.longitude || 100.52;
    const calc = calculateSolarPotential(area || 100, conf || 0.8, lat, lon);
    const { fill, stroke } = paybackColor(calc.paybackYears.expected);
    return { fillColor: fill, color: stroke, fillOpacity: 0.45, weight: 1, opacity: 0.85 };
  }
  const { fill, stroke } = confidenceColor(conf);
  return { fillColor: fill, color: stroke, fillOpacity: 0.4, weight: 1, opacity: 0.85 };
}

/**
 * @param {{
 *   buildings: Array<Record<string, unknown>>,
 *   colorMode: 'confidence' | 'area' | 'flat',
 *   onBuildingClick: (props: Record<string, unknown>) => void,
 *   highlightId?: number | null,
 * }} props
 */
export function BuildingLayer({ buildings, colorMode, onBuildingClick, highlightId }) {
  const layersByIdRef = useRef(new Map());
  const areas = useMemo(() => {
    const vals = buildings.map((b) => b.area_m2).filter((v) => v != null);
    return {
      min: vals.length ? Math.min(...vals) : 0,
      max: vals.length ? Math.max(...vals) : 1,
    };
  }, [buildings]);

  const geojson = useMemo(() => buildingsToGeoJSON(buildings), [buildings]);

  const styleFn = (feature) => {
    const base = leafletStyle(colorMode, feature, areas.min, areas.max);
    const id = feature.properties?.id;
    if (highlightId != null && id === highlightId) {
      return { ...base, weight: 3, opacity: 1 };
    }
    return base;
  };

  const onEach = (feature, layer) => {
    const featureId = feature.properties?.id;
    if (featureId != null) {
      layersByIdRef.current.set(featureId, { layer, props: feature.properties });
    }

    layer.bindPopup(popupContent(feature.properties, { status: 'loading' }, null), {
      closeButton: false,
      autoPan: false,
      className: 'building-info-popup',
      offset: [0, -2],
    });

    const updatePopup = (details, event = null, forcedLatLng = null) => {
      const latlng = forcedLatLng || getLayerLatLng(layer, event);
      layer.setPopupContent(popupContent(feature.properties, details, latlng));
      if (latlng) layer.openPopup([latlng.lat, latlng.lng]);
    };

    const loadGoogleDetails = async (event = null, forcedLatLng = null) => {
      const latlng = forcedLatLng || getLayerLatLng(layer, event);
      if (!latlng) {
        updatePopup({ status: 'unavailable' }, event, forcedLatLng);
        return;
      }

      updatePopup({ status: 'loading' }, event, latlng);
      const details = await fetchGoogleDetailsCached(feature.properties, latlng.lat, latlng.lng);
      updatePopup(details, event, latlng);
    };

    layer.on({
      mouseover: (event) => {
        if (isDrawModeActive()) return;
        loadGoogleDetails(event);
      },
      mouseout: () => {
        layer.closePopup();
      },
      click: (event) => {
        if (isDrawModeActive()) {
          // In draw mode, manually fire map click for AOI point collection
          layer._map?.fire('click', event);
          return;
        }
        loadGoogleDetails(event, event?.latlng ?? null);
        onBuildingClick(feature.properties);
      },
    });

    layer.on('remove', () => {
      if (featureId != null) {
        layersByIdRef.current.delete(featureId);
      }
    });
  };

  useEffect(() => {
    if (highlightId == null) return;
    const entry = layersByIdRef.current.get(highlightId);
    if (!entry?.layer || !entry?.props) return;

    const center = entry.layer.getBounds?.()?.getCenter?.();
    const lat = Number(center?.lat ?? entry.props?.latitude);
    const lng = Number(center?.lng ?? entry.props?.longitude);
    const latlng = Number.isFinite(lat) && Number.isFinite(lng) ? { lat, lng } : null;

    entry.layer.setPopupContent(popupContent(entry.props, { status: 'loading' }, latlng));
    if (latlng) {
      entry.layer.openPopup([latlng.lat, latlng.lng]);
      void fetchGoogleDetailsCached(entry.props, latlng.lat, latlng.lng).then((details) => {
        entry.layer.setPopupContent(popupContent(entry.props, details, latlng));
        entry.layer.openPopup([latlng.lat, latlng.lng]);
      });
    }
  }, [highlightId]);

  if (!buildings?.length) return null;

  return (
    <GeoJSON
      key={`${buildings.length}-${colorMode}-${highlightId}`}
      data={geojson}
      style={styleFn}
      onEachFeature={onEach}
    />
  );
}

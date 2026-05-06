import { useCallback, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { MapContainer, TileLayer, useMap, useMapEvents } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import { BuildingLayer } from '@/components/map/BuildingLayer';
import { BASEMAPS } from '@/lib/mapBasemaps';
import { useMapSettings } from '@/contexts/MapSettingsContext';

/**
 * @param {{
 *   buildings: Array<Record<string, unknown>>,
 *   onBuildingClick: (p: Record<string, unknown>) => void,
 * }} props
 */
export function MapView({ buildings, onBuildingClick }) {
  const {
    basemap,
    polygonColorMode,
    mapCenter,
    setMapCenter,
    mapZoom,
    setMapZoom,
    setBounds,
    highlightBuildingId,
    flyToTarget,
    setFlyToTarget,
  } = useMapSettings();

  const bm = BASEMAPS[basemap] || BASEMAPS.esri;

  const onBounds = useCallback(
    (b) => {
      setBounds({
        minLat: b.minLat,
        maxLat: b.maxLat,
        minLon: b.minLon,
        maxLon: b.maxLon,
      });
    },
    [setBounds]
  );

  const mapRoot = typeof document !== 'undefined' ? document.getElementById('map-root') : null;
  if (!mapRoot) return null;

  return createPortal(
    <MapContainer
      center={mapCenter}
      zoom={mapZoom}
      style={{ width: '100%', height: '100%' }}
      scrollWheelZoom
      zoomControl={false}
    >
      <TileLayer attribution={bm.attribution} url={bm.url} />
      <BoundsSync onBounds={onBounds} setMapCenter={setMapCenter} setMapZoom={setMapZoom} />
      <FlyToEffect target={flyToTarget} onDone={() => setFlyToTarget(null)} />
      <BuildingLayer
        buildings={buildings}
        colorMode={polygonColorMode}
        onBuildingClick={onBuildingClick}
        highlightId={highlightBuildingId}
      />
    </MapContainer>,
    mapRoot
  );
}

/**
 * @param {{ onBounds: (b: { minLat: number, maxLat: number, minLon: number, maxLon: number }) => void, setMapCenter: function, setMapZoom: function }} props
 */
function BoundsSync({ onBounds, setMapCenter, setMapZoom }) {
  const map = useMap();

  useMapEvents({
    moveend: () => {
      const b = map.getBounds();
      onBounds({
        minLat: b.getSouth(),
        maxLat: b.getNorth(),
        minLon: b.getWest(),
        maxLon: b.getEast(),
      });
      const c = map.getCenter();
      setMapCenter([c.lat, c.lng]);
      setMapZoom(map.getZoom());
    },
  });

  useEffect(() => {
    const b = map.getBounds();
    onBounds({
      minLat: b.getSouth(),
      maxLat: b.getNorth(),
      minLon: b.getWest(),
      maxLon: b.getEast(),
    });
  }, [map, onBounds]);

  return null;
}

/**
 * @param {{ target: { lat: number, lon: number, zoom?: number } | null, onDone: () => void }} props
 */
function FlyToEffect({ target, onDone }) {
  const map = useMap();

  useEffect(() => {
    if (!target) return;
    map.setView([target.lat, target.lon], target.zoom ?? map.getZoom());
    const t = window.setTimeout(onDone, 400);
    return () => clearTimeout(t);
  }, [target, map, onDone]);

  return null;
}

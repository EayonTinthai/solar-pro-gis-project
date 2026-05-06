import { useCallback, useEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { MapContainer, TileLayer, useMap, useMapEvents } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import { BuildingLayer } from '@/components/map/BuildingLayer';
import { AoiMapLayer } from '@/components/map/AoiSelector';
import { BASEMAPS } from '@/lib/mapBasemaps';
import { useMapSettings } from '@/contexts/MapSettingsContext';

/**
 * @param {{
 *   buildings: Array<Record<string, unknown>>,
 *   onBuildingClick: (p: Record<string, unknown>) => void,
 *   navigationLocked?: boolean,
 *   onNavigationAttempt?: () => void,
 * }} props
 */
export function MapView({
  buildings,
  onBuildingClick,
  navigationLocked = false,
  onNavigationAttempt = () => {},
}) {
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

  const [tilesReady, setTilesReady] = useState(false);
  const [mapRoot, setMapRoot] = useState(null);
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

  useEffect(() => {
    if (typeof document === 'undefined') return;

    const syncRoot = () => {
      const root = document.getElementById('map-root');
      if (root) setMapRoot(root);
    };

    syncRoot();
    if (document.getElementById('map-root')) return;

    const observer = new MutationObserver(syncRoot);
    observer.observe(document.body, { childList: true, subtree: true });
    return () => observer.disconnect();
  }, []);

  if (!mapRoot) return null;

  const tileHandlers = {
    loading: () => setTilesReady(false),
    load: () => setTilesReady(true),
    tileerror: () => setTilesReady(true),
  };

  return createPortal(
    <div className="relative h-full w-full">
      <MapContainer
        center={mapCenter}
        zoom={mapZoom}
        style={{ width: '100%', height: '100%' }}
        scrollWheelZoom={true}
        dragging={true}
        touchZoom={true}
        doubleClickZoom={true}
        keyboard={true}
        zoomControl={false}
      >
        <TileLayer attribution={bm.attribution} url={bm.url} eventHandlers={tileHandlers} />
        <BoundsSync
          onBounds={onBounds}
          setMapCenter={setMapCenter}
          setMapZoom={setMapZoom}
          navigationLocked={navigationLocked}
          onNavigationAttempt={onNavigationAttempt}
        />
        <FlyToEffect
          target={flyToTarget}
          onDone={() => setFlyToTarget(null)}
        />
        <BuildingLayer
          buildings={buildings}
          colorMode={polygonColorMode}
          onBuildingClick={onBuildingClick}
          highlightId={highlightBuildingId}
        />
        <AoiMapLayer />
      </MapContainer>

      {!tilesReady ? (
        <div className="pointer-events-none absolute inset-0 z-[1] flex items-center justify-center bg-background/35 backdrop-blur-[1px]">
          <span className="rounded-md bg-background/80 px-3 py-1 text-xs text-muted-foreground shadow-sm">
            Loading map tiles...
          </span>
        </div>
      ) : null}
    </div>,
    mapRoot
  );
}

/**
 * @param {{ onBounds: (b: { minLat: number, maxLat: number, minLon: number, maxLon: number }) => void, setMapCenter: function, setMapZoom: function }} props
 */
function BoundsSync({ onBounds, setMapCenter, setMapZoom, navigationLocked, onNavigationAttempt }) {
  const map = useMap();

  // Dynamically enable/disable map interactions based on navigationLocked
  useEffect(() => {
    if (navigationLocked) {
      map.scrollWheelZoom.disable();
      map.dragging.disable();
      map.touchZoom.disable();
      map.doubleClickZoom.disable();
      map.keyboard.disable();
    } else {
      map.scrollWheelZoom.enable();
      map.dragging.enable();
      map.touchZoom.enable();
      map.doubleClickZoom.enable();
      map.keyboard.enable();
    }
  }, [map, navigationLocked]);

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
    wheel: () => {
      if (navigationLocked) onNavigationAttempt();
    },
    dblclick: () => {
      if (navigationLocked) onNavigationAttempt();
    },
  });

  useEffect(() => {
    if (!navigationLocked) return undefined;
    const container = map.getContainer();
    if (!container) return undefined;

    let pointerDownPoint = null;

    const onPointerDown = (event) => {
      pointerDownPoint = { x: event.clientX, y: event.clientY };
    };

    const onPointerMove = (event) => {
      if (!pointerDownPoint) return;
      const dx = Math.abs(event.clientX - pointerDownPoint.x);
      const dy = Math.abs(event.clientY - pointerDownPoint.y);
      if (dx > 6 || dy > 6) {
        onNavigationAttempt();
        pointerDownPoint = null;
      }
    };

    const onPointerUp = () => {
      pointerDownPoint = null;
    };

    const onKeyDown = (event) => {
      const blocked = new Set([
        'ArrowUp',
        'ArrowDown',
        'ArrowLeft',
        'ArrowRight',
        '+',
        '=',
        '-',
        '_',
        'PageUp',
        'PageDown',
      ]);
      if (!blocked.has(event.key)) return;
      onNavigationAttempt();
    };

    const onTouchMove = () => {
      onNavigationAttempt();
    };

    container.addEventListener('pointerdown', onPointerDown);
    container.addEventListener('pointermove', onPointerMove);
    container.addEventListener('pointerup', onPointerUp);
    container.addEventListener('pointercancel', onPointerUp);
    container.addEventListener('keydown', onKeyDown);
    container.addEventListener('touchmove', onTouchMove, { passive: true });

    return () => {
      container.removeEventListener('pointerdown', onPointerDown);
      container.removeEventListener('pointermove', onPointerMove);
      container.removeEventListener('pointerup', onPointerUp);
      container.removeEventListener('pointercancel', onPointerUp);
      container.removeEventListener('keydown', onKeyDown);
      container.removeEventListener('touchmove', onTouchMove);
    };
  }, [map, navigationLocked, onNavigationAttempt]);

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
  const lastTargetRef = useRef(null);

  useEffect(() => {
    if (!target) {
      lastTargetRef.current = null;
      return;
    }
    // Only fly if target actually changed
    const key = `${target.lat},${target.lon},${target.zoom}`;
    if (lastTargetRef.current === key) return;
    lastTargetRef.current = key;

    map.setView([target.lat, target.lon], target.zoom ?? map.getZoom());
    // Clear target immediately so it doesn't re-trigger
    onDone();
  }, [target, map, onDone]);

  return null;
}

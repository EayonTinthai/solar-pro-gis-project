import React, {
  createContext,
  useContext,
  useMemo,
  useState,
} from 'react';

/** @typedef {'esri' | 'osm' | 'carto'} BasemapId */
/** @typedef {'confidence' | 'area' | 'flat'} PolygonColorMode */

const MapSettingsContext = createContext(null);

const BANGKOK = [13.7563, 100.5018];

export function MapSettingsProvider({ children }) {
  const [basemap, setBasemap] = useState(/** @type {BasemapId} */ ('esri'));
  const [polygonColorMode, setPolygonColorMode] = useState(
    /** @type {PolygonColorMode} */ ('confidence')
  );
  const [defaultConfidence, setDefaultConfidence] = useState(0.7);
  const [defaultLimit, setDefaultLimit] = useState(1000);
  const [mapCenter, setMapCenter] = useState(BANGKOK);
  const [mapZoom, setMapZoom] = useState(12);
  const [bounds, setBounds] = useState(
    /** @type {{ minLat: number, maxLat: number, minLon: number, maxLon: number } | null} */ (
      null
    )
  );
  const [highlightBuildingId, setHighlightBuildingId] = useState(
    /** @type {number | null} */ (null)
  );
  const [flyToTarget, setFlyToTarget] = useState(
    /** @type {{ lat: number, lon: number, zoom?: number } | null} */ (null)
  );

  const value = useMemo(
    () => ({
      basemap,
      setBasemap,
      polygonColorMode,
      setPolygonColorMode,
      defaultConfidence,
      setDefaultConfidence,
      defaultLimit,
      setDefaultLimit,
      mapCenter,
      setMapCenter,
      mapZoom,
      setMapZoom,
      bounds,
      setBounds,
      highlightBuildingId,
      setHighlightBuildingId,
      flyToTarget,
      setFlyToTarget,
    }),
    [
      basemap,
      polygonColorMode,
      defaultConfidence,
      defaultLimit,
      mapCenter,
      mapZoom,
      bounds,
      highlightBuildingId,
      flyToTarget,
    ]
  );

  return (
    <MapSettingsContext.Provider value={value}>
      {children}
    </MapSettingsContext.Provider>
  );
}

export function useMapSettings() {
  const ctx = useContext(MapSettingsContext);
  if (!ctx) {
    throw new Error('useMapSettings must be used within MapSettingsProvider');
  }
  return ctx;
}

export const DEFAULT_MAP_CENTER = BANGKOK;

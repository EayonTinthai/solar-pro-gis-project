import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { GeoJSON, useMap, useMapEvents } from 'react-leaflet';
import PropTypes from 'prop-types';

/**
 * AOI (Area of Interest) Selector component.
 * SPLIT ARCHITECTURE:
 * - AoiControls: UI controls (dropdown, buttons) - render in LeftPanel
 * - AoiMapLayer: Map layers (GeoJSON boundaries) - render inside MapContainer
 */

// --- Shared state via a simple event bus ---
let _aoiState = { selectedFeature: null, customPolygon: null, drawMode: false, customPoints: [], addPoint: null };
const _listeners = new Set();
function notifyAoi() { _listeners.forEach(fn => fn({ ..._aoiState })); }

/**
 * Returns whether draw mode is currently active.
 * Can be imported by other components (e.g. BuildingLayer) to suppress clicks.
 */
export function isDrawModeActive() {
  return _aoiState.drawMode;
}

/**
 * UI Controls for AOI selection (render in LeftPanel, outside MapContainer)
 */
export function AoiSelector({ buildings, onFilteredBuildings, onDistrictSelect, onAoiBboxChange, onCustomAoiActive }) {
  const [districts, setDistricts] = useState(null);
  const [selectedDistrict, setSelectedDistrict] = useState('');
  const [drawMode, setDrawMode] = useState(false);
  const [customPolygon, setCustomPolygon] = useState(null);
  const [customPoints, setCustomPoints] = useState([]);
  const [loading, setLoading] = useState(true);

  // Load districts GeoJSON
  useEffect(() => {
    fetch('/bangkok-districts.geojson')
      .then((res) => {
        if (!res.ok) throw new Error('Failed to load districts');
        return res.json();
      })
      .then((data) => {
        setDistricts(data);
        setLoading(false);
      })
      .catch((err) => {
        console.warn('Could not load bangkok-districts.geojson:', err.message);
        setLoading(false);
      });
  }, []);

  // Get sorted district names
  const districtNames = useMemo(() => {
    if (!districts?.features) return [];
    return districts.features
      .map((f) => ({
        name: f.properties.NAME_2 || f.properties.name || f.properties.NAME || '',
        nameLocal: f.properties.NL_NAME_2 || f.properties.name_th || '',
      }))
      .filter((d) => d.name)
      .sort((a, b) => a.name.localeCompare(b.name));
  }, [districts]);

  // Get selected district feature
  const selectedFeature = useMemo(() => {
    if (!selectedDistrict || !districts?.features) return null;
    return districts.features.find(
      (f) => (f.properties.NAME_2 || f.properties.name || f.properties.NAME) === selectedDistrict
    );
  }, [selectedDistrict, districts]);

  // Callback for map layer to add points during draw mode
  const addPoint = useCallback((latlng) => {
    setCustomPoints((prev) => [...prev, [latlng.lng, latlng.lat]]);
  }, []);

  // Update shared state for map layer
  useEffect(() => {
    _aoiState = { selectedFeature, customPolygon, drawMode, customPoints, addPoint };
    notifyAoi();
  }, [selectedFeature, customPolygon, drawMode, customPoints, addPoint]);

  // Compute and report AOI bounding box when selectedFeature changes (Issue 5)
  useEffect(() => {
    if (!onAoiBboxChange) return;
    if (!selectedFeature) {
      onAoiBboxChange(null);
      return;
    }
    const bbox = computeFeatureBbox(selectedFeature);
    onAoiBboxChange(bbox);
  }, [selectedFeature, onAoiBboxChange]);

  // Filter buildings within selected AOI
  useEffect(() => {
    if (!buildings?.length) {
      onFilteredBuildings?.([]);
      return;
    }

    if (customPolygon) {
      const filtered = buildings.filter((b) =>
        pointInPolygon([b.longitude, b.latitude], customPolygon)
      );
      onFilteredBuildings?.(filtered);
      return;
    }

    if (!selectedFeature) {
      onFilteredBuildings?.(buildings);
      return;
    }

    const filtered = buildings.filter((b) => {
      if (!b.latitude || !b.longitude) return false;
      return isPointInFeature([b.longitude, b.latitude], selectedFeature);
    });
    onFilteredBuildings?.(filtered);
    onDistrictSelect?.(selectedDistrict);
  }, [selectedFeature, customPolygon, buildings, onFilteredBuildings, onDistrictSelect, selectedDistrict]);

  const handleDistrictChange = useCallback((e) => {
    setSelectedDistrict(e.target.value);
    setCustomPolygon(null);
    setCustomPoints([]);
    setDrawMode(false);
  }, []);

  const handleDrawToggle = useCallback(() => {
    if (drawMode) {
      if (customPoints.length >= 3) {
        setCustomPolygon([...customPoints, customPoints[0]]);
        onCustomAoiActive?.(true);
      }
      setDrawMode(false);
    } else {
      setSelectedDistrict('');
      setCustomPolygon(null);
      setCustomPoints([]);
      setDrawMode(true);
      onCustomAoiActive?.(false);
    }
  }, [drawMode, customPoints]);

  const handleClearAoi = useCallback(() => {
    setSelectedDistrict('');
    setCustomPolygon(null);
    setCustomPoints([]);
    setDrawMode(false);
    onDistrictSelect?.('');
    onAoiBboxChange?.(null);
    onCustomAoiActive?.(false);
  }, [onDistrictSelect, onAoiBboxChange, onCustomAoiActive]);

  return (
    <div className="rounded-lg border bg-card p-3 shadow-sm">
      <h3 className="mb-2 text-sm font-medium text-foreground">Area of Interest</h3>

      <div className="mb-2">
        <select
          value={selectedDistrict}
          onChange={handleDistrictChange}
          disabled={loading || !districts}
          className="w-full rounded-md border border-input bg-background px-2 py-1.5 text-sm text-foreground focus:outline-none focus:ring-1 focus:ring-ring"
        >
          <option value="">
            {loading ? 'Loading districts...' : 'Select a district (เขต)'}
          </option>
          {districtNames.map((d) => (
            <option key={d.name} value={d.name}>
              {d.name} {d.nameLocal ? `(${d.nameLocal})` : ''}
            </option>
          ))}
        </select>
      </div>

      <div className="flex gap-2">
        <button
          onClick={handleDrawToggle}
          className={`flex-1 rounded-md px-2 py-1.5 text-xs font-medium transition-colors ${
            drawMode
              ? 'bg-red-500 text-white hover:bg-red-600'
              : 'bg-secondary text-secondary-foreground hover:bg-secondary/80'
          }`}
        >
          {drawMode ? `Finish (${customPoints.length} pts)` : 'Draw custom AOI'}
        </button>
        {(selectedDistrict || customPolygon) && (
          <button
            onClick={handleClearAoi}
            className="rounded-md bg-muted px-2 py-1.5 text-xs text-muted-foreground hover:bg-muted/80"
          >
            Clear
          </button>
        )}
      </div>

      {drawMode && (
        <p className="mt-1.5 text-xs text-muted-foreground">
          Click on the map to add points. Click &quot;Finish&quot; when done (min 3 points).
        </p>
      )}

      {selectedDistrict && (
        <p className="mt-1.5 text-xs text-muted-foreground">
          Showing buildings in: <strong>{selectedDistrict}</strong>
        </p>
      )}

      {/* Issue 3: Show "Custom AOI" indicator when a drawn polygon is active */}
      {!selectedDistrict && customPolygon && (
        <p className="mt-1.5 text-xs font-medium text-blue-600 dark:text-blue-400">
          Active: Custom drawn area
        </p>
      )}
    </div>
  );
}

AoiSelector.propTypes = {
  buildings: PropTypes.array,
  onFilteredBuildings: PropTypes.func,
  onDistrictSelect: PropTypes.func,
  onAoiBboxChange: PropTypes.func,
  onCustomAoiActive: PropTypes.func,
};

/**
 * Map layer component for AOI boundaries.
 * MUST be rendered inside <MapContainer>.
 */
export function AoiMapLayer() {
  const [state, setState] = useState(_aoiState);
  const map = useMap();

  useEffect(() => {
    const handler = (s) => setState(s);
    _listeners.add(handler);
    return () => _listeners.delete(handler);
  }, []);

  // Issue 2: Change cursor when draw mode is active
  useEffect(() => {
    const container = map.getContainer();
    if (state.drawMode) {
      container.style.cursor = 'crosshair';
    } else {
      container.style.cursor = '';
    }
  }, [state.drawMode, map]);

  // Fly to district when selected
  useEffect(() => {
    if (!state.selectedFeature) return;
    try {
      const L = window.L || map.options?.L;
      if (!L) return;
      const layer = L.geoJSON(state.selectedFeature);
      const bounds = layer.getBounds();
      if (bounds.isValid()) {
        map.fitBounds(bounds, { padding: [20, 20] });
      }
    } catch {
      // ignore
    }
  }, [state.selectedFeature, map]);

  // Draw mode click handler
  useMapEvents({
    click: (e) => {
      if (!state.drawMode) return;
      if (state.addPoint) {
        state.addPoint(e.latlng);
      }
    },
  });

  const districtStyle = {
    color: '#2563eb',
    weight: 2.5,
    fillColor: '#3b82f6',
    fillOpacity: 0.08,
    dashArray: '5,5',
  };

  const customStyle = {
    color: '#dc2626',
    weight: 2,
    fillColor: '#ef4444',
    fillOpacity: 0.1,
    dashArray: '4,4',
  };

  return (
    <>
      {/* Issue 4: Use district name in key to force re-render on district change */}
      {state.selectedFeature && (
        <GeoJSON
          key={`district-${state.selectedFeature?.properties?.NAME_2 || state.selectedFeature?.properties?.name || 'none'}`}
          data={state.selectedFeature}
          style={districtStyle}
        />
      )}
      {state.customPolygon && (
        <GeoJSON
          key={`custom-${state.customPolygon.length}`}
          data={{
            type: 'Feature',
            geometry: { type: 'Polygon', coordinates: [state.customPolygon] },
            properties: {},
          }}
          style={customStyle}
        />
      )}
    </>
  );
}

// --- Geometry Helpers ---

function pointInPolygon(point, polygon) {
  const [x, y] = point;
  let inside = false;
  for (let i = 0, j = polygon.length - 1; i < polygon.length; j = i++) {
    const [xi, yi] = polygon[i];
    const [xj, yj] = polygon[j];
    const intersect = yi > y !== yj > y && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi;
    if (intersect) inside = !inside;
  }
  return inside;
}

function isPointInFeature(point, feature) {
  const geom = feature.geometry;
  if (!geom) return false;
  if (geom.type === 'Polygon') return pointInPolygon(point, geom.coordinates[0]);
  if (geom.type === 'MultiPolygon') return geom.coordinates.some((poly) => pointInPolygon(point, poly[0]));
  return false;
}

/**
 * Compute bounding box {minLat, maxLat, minLon, maxLon} from a GeoJSON feature.
 */
function computeFeatureBbox(feature) {
  const coords = [];
  const geom = feature.geometry;
  if (!geom) return null;

  function collectCoords(c) {
    if (typeof c[0] === 'number') {
      coords.push(c);
    } else {
      c.forEach(collectCoords);
    }
  }
  collectCoords(geom.coordinates);

  if (coords.length === 0) return null;

  let minLon = Infinity, maxLon = -Infinity, minLat = Infinity, maxLat = -Infinity;
  for (const [lon, lat] of coords) {
    if (lon < minLon) minLon = lon;
    if (lon > maxLon) maxLon = lon;
    if (lat < minLat) minLat = lat;
    if (lat > maxLat) maxLat = lat;
  }
  return { minLat, maxLat, minLon, maxLon };
}

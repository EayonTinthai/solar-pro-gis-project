import { useMemo } from 'react';
import { GeoJSON } from 'react-leaflet';
import { buildingsToGeoJSON } from '@/lib/api';
import {
  areaBucketColor,
  confidenceColor,
  flatPolygonColor,
} from '@/lib/utils';

/**
 * @param {'confidence' | 'area' | 'flat'} mode
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
    layer.on({
      click: () => onBuildingClick(feature.properties),
    });
  };

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

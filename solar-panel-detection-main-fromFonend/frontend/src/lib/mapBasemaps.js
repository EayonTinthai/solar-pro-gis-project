/** @typedef {{ url: string, attribution: string }} BasemapTile */

/** @type {Record<'esri' | 'osm' | 'carto', BasemapTile>} */
export const BASEMAPS = {
  esri: {
    url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    attribution:
      'Tiles &copy; Esri &mdash; Source: Esri, Maxar, Earthstar Geographics, and the GIS User Community',
  },
  osm: {
    url: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
    attribution: '&copy; OpenStreetMap contributors',
  },
  carto: {
    url: 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
    attribution: '&copy; OpenStreetMap &copy; CARTO',
  },
};

export const FALLBACK_BBOX = {
  minLat: 13.65,
  maxLat: 13.85,
  minLon: 100.4,
  maxLon: 100.65,
};

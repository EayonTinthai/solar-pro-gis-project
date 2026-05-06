import { useCallback, useEffect, useState } from 'react';

const DEFAULT_HASH = '#/map';

function normalizeHash() {
  const h = window.location.hash || DEFAULT_HASH;
  if (!h || h === '#') return DEFAULT_HASH;
  return h.startsWith('#') ? h : `#${h}`;
}

/**
 * @returns {['#/map' | '#/stats' | '#/data' | '#/solar', (route: string) => void]}
 */
export function useHashRoute() {
  const [route, setRouteState] = useState(normalizeHash);

  useEffect(() => {
    if (!window.location.hash || window.location.hash === '#') {
      window.location.replace('#/map');
    }
  }, []);

  useEffect(() => {
    const onHash = () => setRouteState(normalizeHash());
    window.addEventListener('hashchange', onHash);
    return () => window.removeEventListener('hashchange', onHash);
  }, []);

  const setRoute = useCallback((next) => {
    const r = next.startsWith('#') ? next : `#${next}`;
    if (window.location.hash !== r) {
      window.location.hash = r;
    } else {
      setRouteState(r);
    }
  }, []);

  return [route, setRoute];
}

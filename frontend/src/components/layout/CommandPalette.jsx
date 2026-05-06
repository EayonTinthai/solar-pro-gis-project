import { useEffect, useMemo, useRef, useState } from 'react';
import {
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandSeparator,
} from '@/components/ui/command';
import { BarChart3, Map, Sun, Table2 } from 'lucide-react';
import { useMapUI } from '@/contexts/MapUIContext';
import { useMapSettings } from '@/contexts/MapSettingsContext';

const PAGES = [
  { id: 'map', label: 'Map', tab: null, icon: Map },
  { id: 'stats', label: 'Statistics', tab: 'stats', icon: BarChart3 },
  { id: 'data', label: 'Buildings data', tab: 'data', icon: Table2 },
  { id: 'solar', label: 'Solar calculator', tab: 'solar', icon: Sun },
];

function shortLabel(displayName) {
  if (!displayName) return '';
  const parts = String(displayName).split(',').map((p) => p.trim()).filter(Boolean);
  return parts.slice(0, 2).join(', ');
}

/**
 * @param {{ open: boolean, onOpenChange: (v: boolean) => void }} props
 */
export function CommandPalette({ open, onOpenChange }) {
  const { setLeftPanelOpen, setLeftPanelTab } = useMapUI();
  const { setFlyToTarget } = useMapSettings();
  const [query, setQuery] = useState('');
  const [locResults, setLocResults] = useState([]);
  const [locLoading, setLocLoading] = useState(false);
  const [locError, setLocError] = useState(null);
  const abortRef = useRef(/** @type {AbortController | null} */ (null));

  useEffect(() => {
    const down = (e) => {
      if (e.key === 'k' && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        onOpenChange(true);
      }
    };
    window.addEventListener('keydown', down);
    return () => window.removeEventListener('keydown', down);
  }, [onOpenChange]);

  useEffect(() => {
    if (!open) return;
    // When reopening, keep query but refresh results if needed.
    // Also cancel any in-flight request.
    abortRef.current?.abort?.();
    abortRef.current = null;
  }, [open]);

  const debouncedQuery = useDebouncedValue(query, 300);

  useEffect(() => {
    if (!open) return;
    const q = debouncedQuery.trim();
    if (q.length < 2) {
      setLocResults([]);
      setLocLoading(false);
      setLocError(null);
      abortRef.current?.abort?.();
      abortRef.current = null;
      return;
    }

    const ctrl = new AbortController();
    abortRef.current?.abort?.();
    abortRef.current = ctrl;
    setLocLoading(true);
    setLocError(null);

    const url = new URL('https://nominatim.openstreetmap.org/search');
    url.searchParams.set('format', 'json');
    url.searchParams.set('addressdetails', '1');
    url.searchParams.set('limit', '5');
    url.searchParams.set('q', q);

    fetch(url.toString(), {
      method: 'GET',
      signal: ctrl.signal,
      headers: {
        Accept: 'application/json',
      },
    })
      .then((r) => {
        if (!r.ok) throw new Error(`Geocoding failed (${r.status})`);
        return r.json();
      })
      .then((data) => {
        const list = Array.isArray(data) ? data : [];
        setLocResults(
          list
            .map((it) => ({
              id: String(it.place_id ?? `${it.lat},${it.lon}`),
              display_name: String(it.display_name ?? ''),
              lat: Number(it.lat),
              lon: Number(it.lon),
            }))
            .filter((it) => Number.isFinite(it.lat) && Number.isFinite(it.lon) && it.display_name)
        );
        setLocLoading(false);
      })
      .catch((e) => {
        if (e?.name === 'AbortError') return;
        setLocLoading(false);
        setLocError(e?.message || 'Geocoding failed');
      });

    return () => ctrl.abort();
  }, [debouncedQuery, open]);

  const showLocations = useMemo(() => {
    const q = query.trim();
    return open && q.length >= 2;
  }, [open, query]);

  const flyToLocation = (loc) => {
    setFlyToTarget({
      lat: loc.lat,
      lon: loc.lon,
      zoom: 16,
    });
    onOpenChange(false);
  };

  const go = (id, tab) => {
    if (tab) {
      setLeftPanelOpen(true);
      setLeftPanelTab(tab);
    }

    onOpenChange(false);
  };

  return (
    <CommandDialog open={open} onOpenChange={onOpenChange}>
      <CommandInput
        placeholder="Search pages or locations…"
        value={query}
        onValueChange={setQuery}
        onKeyDown={(e) => {
          if (e.key !== 'Enter') return;
          if (!showLocations) return;
          if (!locResults.length) return;
          e.preventDefault();
          flyToLocation(locResults[0]);
        }}
      />
      <CommandList>
        <CommandEmpty>No results.</CommandEmpty>

        {showLocations ? (
          <CommandGroup heading="Locations">
            {locLoading ? (
              <CommandItem disabled value="locations-loading">
                Searching…
              </CommandItem>
            ) : locError ? (
              <CommandItem disabled value="locations-error">
                {locError}
              </CommandItem>
            ) : locResults.length ? (
              locResults.map((loc) => (
                <CommandItem
                  key={loc.id}
                  value={`loc ${loc.display_name}`}
                  onSelect={() => flyToLocation(loc)}
                  className="min-h-10"
                >
                  <div className="min-w-0">
                    <div className="truncate">{shortLabel(loc.display_name) || loc.display_name}</div>
                    <div className="truncate text-xs text-muted-foreground">{loc.display_name}</div>
                  </div>
                </CommandItem>
              ))
            ) : (
              <CommandItem disabled value="locations-empty">
                No locations found.
              </CommandItem>
            )}
          </CommandGroup>
        ) : null}

        <CommandGroup heading="Navigate">
          {PAGES.map(({ id, label, tab, icon: Icon }) => (
            <CommandItem
              key={id}
              value={`${label} ${id}`}
              onSelect={() => go(id, tab)}
              className="min-h-10"
            >
              <Icon className="mr-2 h-4 w-4" />
              {label}
            </CommandItem>
          ))}
        </CommandGroup>
        <CommandSeparator />
        <CommandGroup heading="Tips">
          <CommandItem disabled value="tip">
            Use map filters to refine building detections
          </CommandItem>
        </CommandGroup>
      </CommandList>
    </CommandDialog>
  );
}

/**
 * @param {string} value
 * @param {number} delayMs
 */
function useDebouncedValue(value, delayMs) {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const t = window.setTimeout(() => setDebounced(value), delayMs);
    return () => window.clearTimeout(t);
  }, [value, delayMs]);
  return debounced;
}

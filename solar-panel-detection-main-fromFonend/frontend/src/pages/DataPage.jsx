import { useMapSettings } from '@/contexts/MapSettingsContext';
import { BuildingsTable } from '@/components/data/BuildingsTable';
import { useBuildings } from '@/hooks/useBuildings';
import { FALLBACK_BBOX } from '@/lib/mapBasemaps';

/**
 * @param {{
 *   onSelectBuilding: (b: Record<string, unknown>) => void,
 *   onLoadInMap: (b: Record<string, unknown>) => void,
 * }} props
 */
export function DataPage({ onSelectBuilding, onLoadInMap }) {
  const { bounds } = useMapSettings();
  const bbox = bounds ?? FALLBACK_BBOX;

  const q = useBuildings(bbox, {
    limit: 5000,
    minConfidence: 0.5,
    enabled: true,
  });

  return (
    <div className="space-y-4 p-4 md:p-6">
      <div>
        <h2 className="text-balance text-xl font-semibold">Buildings data</h2>
        <p className="text-sm text-muted-foreground">
          Dataset for the current map view (or Bangkok fallback if the map has not reported bounds yet).
        </p>
      </div>
      {q.isError ? (
        <p className="text-sm text-destructive">Failed to load buildings.</p>
      ) : null}
      <BuildingsTable
        buildings={q.data?.buildings ?? []}
        loading={q.isLoading}
        onRowOpen={(b) => {
          const lat = Number(b?.latitude);
          const lon = Number(b?.longitude);
          const canFly = Number.isFinite(lat) && Number.isFinite(lon);
          if (canFly) onLoadInMap(b);
          else onSelectBuilding(b);
        }}
        onLoadInMap={onLoadInMap}
      />
    </div>
  );
}

import { useEffect, useMemo, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { AuthGate } from '@/components/auth/AuthGate';
import { MapView } from '@/components/map/MapView';
import { BuildingsTable } from '@/components/data/BuildingsTable';
import { useBuildings } from '@/hooks/useBuildings';
import { useMapSettings } from '@/contexts/MapSettingsContext';
import { estimatePortfolioCo2KgYear } from '@/lib/utils';
import { FALLBACK_BBOX } from '@/lib/mapBasemaps';
import { LeftPanel } from '@/components/layout/LeftPanel';
import { BottomBar } from '@/components/layout/BottomBar';
import { MapControls } from '@/components/map/MapControls';
import { MapLegendFloating } from '@/components/map/MapLegendFloating';
import { StatsPanelV2 } from '@/components/stats/StatsPanelV2';
import { FiltersPanel } from '@/components/map/FiltersPanel';
import { SolarPage } from '@/pages/SolarPage';
import { useMapUI } from '@/contexts/MapUIContext';
import { useAuth } from '@/hooks/useAuth';
import { WeatherPanel } from '@/components/weather/WeatherPanel';
import { WeatherToggle } from '@/components/weather/WeatherToggle';

/**
 * @param {{
 *   onSelectBuilding: (b: Record<string, unknown>) => void,
 *   onLoadInMap?: (b: Record<string, unknown>) => void,
 * }} props
 */
export function MapPage({ onSelectBuilding, onLoadInMap }) {
  const queryClient = useQueryClient();
  const { isSignedIn } = useAuth();
  const {
    bounds,
    defaultConfidence,
    defaultLimit,
    setHighlightBuildingId,
    mapCenter,
  } = useMapSettings();
  const { setActiveFilterCount, leftPanelOpen } = useMapUI();

  const [commitConf, setCommitConf] = useState(defaultConfidence);
  const [commitLimit, setCommitLimit] = useState(defaultLimit);
  const [draftConf, setDraftConf] = useState(defaultConfidence);
  const [draftLimit, setDraftLimit] = useState(defaultLimit);
  const [minAreaIn, setMinAreaIn] = useState('');
  const [maxAreaIn, setMaxAreaIn] = useState('');
  const [weatherPanelOpen, setWeatherPanelOpen] = useState(false);

  const bbox = bounds ?? FALLBACK_BBOX;

  const q = useBuildings(bbox, {
    minConfidence: commitConf,
    limit: commitLimit,
    enabled: true, // Always load buildings (no auth required)
  });

  const minA = minAreaIn === '' ? null : Number(minAreaIn);
  const maxA = maxAreaIn === '' ? null : Number(maxAreaIn);

  const displayed = useMemo(() => {
    let list = q.data?.buildings ?? [];
    if (minA != null && !Number.isNaN(minA)) {
      list = list.filter((b) => b.area_m2 >= minA);
    }
    if (maxA != null && !Number.isNaN(maxA)) {
      list = list.filter((b) => b.area_m2 <= maxA);
    }
    return list;
  }, [q.data?.buildings, minA, maxA]);

  const kpis = useMemo(() => {
    const n = displayed.length;
    if (!n) {
      return { n: 0, avgC: '—', area: '—', co2: '—' };
    }
    const avgC =
      displayed.reduce((s, b) => s + Number(b.confidence), 0) / n;
    const area = displayed.reduce((s, b) => s + Number(b.area_m2), 0);
    const co2 = estimatePortfolioCo2KgYear({
      total_buildings: n,
      area_m2: { average: area / n },
      confidence: { average: avgC },
    });
    return {
      n,
      avgC: `${(avgC * 100).toFixed(1)}%`,
      area: `${Math.round(area).toLocaleString()} m²`,
      co2: `${co2.toLocaleString()} kg/yr`,
    };
  }, [displayed]);

  const activeFilterCount = useMemo(() => {
    let c = 0;
    if (commitConf !== defaultConfidence) c += 1;
    if (commitLimit !== defaultLimit) c += 1;
    if (minAreaIn !== '') c += 1;
    if (maxAreaIn !== '') c += 1;
    return c;
  }, [commitConf, commitLimit, defaultConfidence, defaultLimit, minAreaIn, maxAreaIn]);

  const handleApply = () => {
    setCommitConf(draftConf);
    setCommitLimit(draftLimit);
    queryClient.invalidateQueries({ queryKey: ['buildings'] });
  };

  const clearDraft = () => {
    setDraftConf(defaultConfidence);
    setDraftLimit(defaultLimit);
    setMinAreaIn('');
    setMaxAreaIn('');
  };

  const openBuilding = (b) => {
    setHighlightBuildingId(b.id);
    onSelectBuilding(b);
  };

  const openBuildingInMap = (b) => {
    const lat = Number(b?.latitude);
    const lon = Number(b?.longitude);
    const canFly =
      onLoadInMap &&
      Number.isFinite(lat) &&
      Number.isFinite(lon);

    if (canFly) {
      onLoadInMap(b);
      return;
    }

    openBuilding(b);
  };

  useEffect(() => {
    setActiveFilterCount(activeFilterCount);
  }, [activeFilterCount, setActiveFilterCount]);

  const bottomKpis = useMemo(
    () => ({
      buildings: kpis.n,
      avgConf: kpis.avgC,
      totalArea: kpis.area,
      co2Saved: kpis.co2,
    }),
    [kpis]
  );

  return (
    <>
      <MapView buildings={displayed} onBuildingClick={(p) => openBuilding(p)} />

      {/* Weather Panel */}
      <WeatherPanel
        location={{ lat: mapCenter[0], lon: mapCenter[1] }}
        systemKwp={5} // Default system size
        open={weatherPanelOpen}
        onOpenChange={setWeatherPanelOpen}
      />

      {/* Weather Toggle Button */}
      <div
        className="pointer-events-auto"
        style={{
          position: 'absolute',
          right: '12px',
          top: '12px',
          zIndex: 15,
        }}
      >
        <WeatherToggle
          active={weatherPanelOpen}
          onClick={() => setWeatherPanelOpen(!weatherPanelOpen)}
        />
      </div>

      <LeftPanel
        stats={
          <AuthGate
            title="Statistics require Pro"
            subtitle="View portfolio KPIs and database-wide stats with a Pro subscription."
          >
            <StatsPanelV2 />
          </AuthGate>
        }
        filters={
          <AuthGate
            title="Filters require Pro"
            subtitle="Adjust confidence, area, and result limits with Pro."
            className="min-h-[200px]"
          >
            <div className="space-y-3">
              <FiltersPanel
                minConfidence={draftConf}
                onMinConfidenceChange={setDraftConf}
                minArea={minAreaIn}
                maxArea={maxAreaIn}
                onMinAreaChange={setMinAreaIn}
                onMaxAreaChange={setMaxAreaIn}
                limit={draftLimit}
                onLimitChange={setDraftLimit}
                onApply={handleApply}
                activeFilterCount={activeFilterCount}
                defaultConfidence={defaultConfidence}
                defaultLimit={defaultLimit}
                onClearDraft={clearDraft}
              />
              {q.isFetching ? <span className="text-xs text-muted-foreground">Updating…</span> : null}
              {q.isError ? (
                <p className="text-sm text-destructive">Could not load buildings for this view.</p>
              ) : null}
            </div>
          </AuthGate>
        }
        data={
          <AuthGate
            title="Building data requires Pro"
            subtitle="Browse, sort, and export building rows with Pro."
            className="min-h-[240px]"
          >
            <BuildingsTable
              buildings={displayed}
              loading={q.isLoading}
              compact
              onRowOpen={openBuildingInMap}
              onLoadInMap={onLoadInMap}
            />
          </AuthGate>
        }
        solar={
          <AuthGate
            title="Solar calculator requires Pro"
            subtitle="Run solar potential estimates and history with Pro."
            className="min-h-[280px]"
          >
            <SolarPage />
          </AuthGate>
        }
      />

      {/* <div
        className="pointer-events-auto"
        style={{
          position: 'absolute',
          bottom: '12px',
          left: '12px',
          right: '12px',
          zIndex: 15,
        }}
      >
        <AuthGate
          title="KPI bar requires Pro"
          subtitle="See live portfolio metrics at a glance with Pro."
          className="flex min-h-[160px] flex-col justify-end"
        >
          <BottomBar embedded kpis={bottomKpis} activeFilterCount={activeFilterCount} />
        </AuthGate>
      </div> */}

      {/* <div
        className="pointer-events-auto"
        style={{
          position: 'absolute',
          right: '12px',
          bottom: '68px',
          zIndex: 15,
        }}
      >
        <AuthGate
          title="Map controls require Pro"
          subtitle="Zoom and recenter the map with Pro."
          className="flex min-h-[200px] w-[42px] flex-col justify-end"
        >
          <MapControls embedded />
        </AuthGate>
      </div> */}

      {/* <div
        className="pointer-events-auto"
        style={{
          position: 'absolute',
          left: leftPanelOpen ? '344px' : '12px',
          bottom: '68px',
          zIndex: 15,
          transition: 'left 280ms cubic-bezier(0.16, 1, 0.3, 1)',
        }}
      >
        <AuthGate
          title="Legend requires Pro"
          subtitle="Show the confidence color key with Pro."
          className="min-h-[120px]"
        >
          <MapLegendFloating embedded />
        </AuthGate>
      </div> */}
    </>
  );
}

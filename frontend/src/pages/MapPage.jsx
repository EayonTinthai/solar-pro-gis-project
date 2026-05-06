import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { AuthGate } from '@/components/auth/AuthGate';
import { MapView } from '@/components/map/MapView';
import { BuildingsTable } from '@/components/data/BuildingsTable';
import { useBuildings } from '@/hooks/useBuildings';
import {
  DEFAULT_MAP_CENTER,
  DEFAULT_NON_PRO_MAP_ZOOM,
  useMapSettings,
} from '@/contexts/MapSettingsContext';
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
import { useUpgrade } from '@/contexts/UpgradeContext';
import { AoiSelector } from '@/components/map/AoiSelector';
import { RankingPanel } from '@/components/map/RankingPanel';

/**
 * @param {{
 *   onSelectBuilding: (b: Record<string, unknown>) => void,
 *   onLoadInMap?: (b: Record<string, unknown>) => void,
 * }} props
 */
export function MapPage({ onSelectBuilding, onLoadInMap }) {
  const queryClient = useQueryClient();
  const { isSignedIn, hasFeatureAccess } = useAuth();
  const { openUpgrade } = useUpgrade();
  const {
    bounds,
    defaultConfidence,
    defaultLimit,
    setMapCenter,
    setMapZoom,
    setFlyToTarget,
    setHighlightBuildingId,
  } = useMapSettings();
  const { setActiveFilterCount, leftPanelOpen, selectedBuilding } = useMapUI();
  const lastNonProNoticeAtRef = useRef(0);

  const [commitConf, setCommitConf] = useState(defaultConfidence);
  const [commitLimit, setCommitLimit] = useState(defaultLimit);
  const [draftConf, setDraftConf] = useState(defaultConfidence);
  const [draftLimit, setDraftLimit] = useState(defaultLimit);
  const [minAreaIn, setMinAreaIn] = useState('');
  const [maxAreaIn, setMaxAreaIn] = useState('');
  const [aoiFilteredBuildings, setAoiFilteredBuildings] = useState(null);
  const [selectedDistrictName, setSelectedDistrictName] = useState('');
  const [aoiBbox, setAoiBbox] = useState(null);
  const [hasCustomAoi, setHasCustomAoi] = useState(false);

  // Issue 5: Use AOI bbox when available, with higher limit
  const queryBbox = aoiBbox || bounds || FALLBACK_BBOX;
  const queryLimit = aoiBbox ? 5000 : commitLimit;
  const nonProNavigationLocked = false; // Always unlocked in local dev

  const q = useBuildings(queryBbox, {
    minConfidence: commitConf,
    limit: queryLimit,
    enabled: isSignedIn,
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

  const displayedForMap = useMemo(() => {
    if (!selectedBuilding?.id) return displayed;
    const selectedId = String(selectedBuilding.id);
    const exists = displayed.some((b) => String(b?.id) === selectedId);
    if (exists) return displayed;
    return [selectedBuilding, ...displayed];
  }, [displayed, selectedBuilding]);

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

  useEffect(() => {
    if (!nonProNavigationLocked) return;
    setMapCenter(DEFAULT_MAP_CENTER);
    setMapZoom(DEFAULT_NON_PRO_MAP_ZOOM);
    setFlyToTarget(null);
  }, [nonProNavigationLocked, setFlyToTarget, setMapCenter, setMapZoom]);

  const handleNonProNavigationAttempt = useCallback(() => {
    if (!nonProNavigationLocked) return;
    const now = Date.now();
    if (now - lastNonProNoticeAtRef.current < 10000) return;
    lastNonProNoticeAtRef.current = now;
    toast.info(
      'Non-Pro access is limited to this fixed Bangkok map view. Please sign up for a Pro account to use the full version.'
    );
    openUpgrade();
  }, [nonProNavigationLocked, openUpgrade]);

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
      <MapView
        buildings={displayedForMap}
        onBuildingClick={(p) => openBuilding(p)}
        navigationLocked={nonProNavigationLocked}
        onNavigationAttempt={handleNonProNavigationAttempt}
      />

      {nonProNavigationLocked ? (
        <div
          className="pointer-events-none"
          style={{
            position: 'absolute',
            bottom: '12px',
            left: '50%',
            transform: 'translateX(-50%)',
            zIndex: 20,
          }}
        >
          <div className="rounded-full border border-border/60 bg-background/90 px-4 py-2 text-xs font-medium text-foreground shadow-md backdrop-blur-sm">
            Map is locked and limited to Pro users only.
          </div>
        </div>
      ) : null}

      <LeftPanel
        stats={
          <AuthGate
            title="Statistics require Pro"
            subtitle="View portfolio KPIs and database-wide stats with a Pro subscription."
          >
            <div className="space-y-3">
              <AoiSelector
                buildings={displayed}
                onFilteredBuildings={setAoiFilteredBuildings}
                onDistrictSelect={(name) => {
                  setSelectedDistrictName(name);
                  setHasCustomAoi(false);
                }}
                onAoiBboxChange={setAoiBbox}
                onCustomAoiActive={setHasCustomAoi}
              />
              <RankingPanel
                buildings={aoiFilteredBuildings || displayed}
                onFlyTo={(target) => {
                  setFlyToTarget(target);
                }}
              />
              <StatsPanelV2
                localBuildings={(selectedDistrictName || hasCustomAoi) ? (aoiFilteredBuildings || []) : null}
                aoiLabel={selectedDistrictName || (hasCustomAoi ? 'Custom AOI' : null)}
              />
            </div>
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
                buildings={q.data?.buildings}
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
    </>
  );
}

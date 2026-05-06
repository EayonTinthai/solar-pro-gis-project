import { useEffect, useMemo, useState } from 'react';
import { ArrowLeft, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { cn, estimatePortfolioCo2KgYear } from '@/lib/utils';
import { useStats } from '@/hooks/useStats';
import { useSolarForecast, useWeatherForecast } from '@/hooks/useSolarCalc';
import { useMapSettings } from '@/contexts/MapSettingsContext';
import { ConfidenceBarChart } from '@/components/stats/ConfidenceBarChart';
import { CumulativeAreaChart } from '@/components/stats/CumulativeAreaChart';
import { ConfidenceDonut } from '@/components/stats/ConfidenceDonut';

function formatRelative(ms) {
  if (ms == null) return '—';
  const s = Math.floor(ms / 1000);
  if (s < 60) return `${s}s ago`;
  const m = Math.floor(s / 60);
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;
  const d = Math.floor(h / 24);
  return `${d}d ago`;
}

function KpiTile({ label, value, active, onClick, sub }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        'rounded-lg border border-border/40 shadow-none bg-background/60 px-3 py-2 text-left',
        'transition-[transform,box-shadow,border-color] active:scale-[0.99]',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring',
        active ? 'ring-1 ring-ring/50 border-border/60' : 'hover:shadow-sm'
      )}
    >
      <div className="flex items-start justify-between gap-2">
        <span className="text-[11px] text-muted-foreground leading-none">{label}</span>
        {sub ? (
          <Badge variant="secondary" className="text-[10px] tabular-nums">
            {sub}
          </Badge>
        ) : null}
      </div>
      <div className="mt-1 text-[14px] font-semibold tabular-nums leading-none">{value}</div>
    </button>
  );
}

function InsightCard({ title, value, detail, onClick }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        'w-full rounded-lg border border-border/40 shadow-none bg-background/60 p-3 text-left',
        'transition-[transform,box-shadow] active:scale-[0.99] hover:shadow-sm',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring'
      )}
    >
      <div className="flex items-center justify-between gap-3">
        <div className="min-w-0">
          <div className="text-xs font-medium text-foreground/90">{title}</div>
          <div className="text-[11px] text-muted-foreground">{detail}</div>
        </div>
        <div className="text-sm font-semibold tabular-nums">{value}</div>
      </div>
    </button>
  );
}

/**
 * World-class narrative stats panel (left panel).
 * @param {{ localBuildings?: Array | null, aoiLabel?: string | null }} props
 */
export function StatsPanelV2({ localBuildings = null, aoiLabel = null }) {
  const q = useStats();
  const { mapCenter } = useMapSettings();
  const [tick, setTick] = useState(0);

  const [activeView, setActiveView] = useState(/** @type {'buckets'|'split'|'cumulative'} */ ('buckets'));
  const [drill, setDrill] = useState(/** @type {null | { type: 'bucket', label: string } | { type: 'segment', id: string } | { type: 'threshold', index: number }} */ (null));

  useEffect(() => {
    const id = window.setInterval(() => setTick((t) => t + 1), 10000);
    return () => clearInterval(id);
  }, []);

  const s = q.data;

  const age = useMemo(
    () => (q.dataUpdatedAt ? formatRelative(Date.now() - q.dataUpdatedAt) : '—'),
    [tick, q.dataUpdatedAt]
  );

  // Determine if we're showing local (AOI) data or global stats
  const isLocalMode = Array.isArray(localBuildings) && localBuildings.length > 0;

  const localKpis = useMemo(() => {
    if (!isLocalMode) return null;
    const n = localBuildings.length;
    const totalArea = localBuildings.reduce((sum, b) => sum + Number(b.area_m2 || 0), 0);
    const avgC = localBuildings.reduce((sum, b) => sum + Number(b.confidence || 0), 0) / n;
    const co2 = estimatePortfolioCo2KgYear({
      total_buildings: n,
      area_m2: { average: totalArea / n },
      confidence: { average: avgC },
    });
    return { buildings: n, avgConf: avgC, roofArea: Math.round(totalArea), co2Est: co2 };
  }, [isLocalMode, localBuildings]);

  const buildings = isLocalMode ? localKpis.buildings : (s?.total_buildings ?? null);
  const avgConf = isLocalMode ? localKpis.avgConf : (s?.confidence?.average ?? null);
  const roofArea = isLocalMode
    ? localKpis.roofArea
    : (s?.total_buildings && s?.area_m2?.average ? Math.round(s.total_buildings * s.area_m2.average) : null);
  const co2Est = isLocalMode ? localKpis.co2Est : estimatePortfolioCo2KgYear(s);

  const refSystemKwp = 10;
  const mapLat = Number(mapCenter[0]);
  const mapLon = Number(mapCenter[1]);
  const hasMapCenter = Number.isFinite(mapLat) && Number.isFinite(mapLon);

  const weather = useWeatherForecast(
    hasMapCenter
      ? {
          lat: mapLat,
          lon: mapLon,
          timezone: 'Asia/Bangkok',
        }
      : null
  );
  const solarForecast = useSolarForecast(
    hasMapCenter
      ? {
          lat: mapLat,
          lon: mapLon,
          timezone: 'Asia/Bangkok',
          systemKwp: refSystemKwp,
        }
      : null
  );

  const toNumber = (v) => {
    const n = Number(v);
    return Number.isFinite(n) ? n : null;
  };

  const rainProb = (() => {
    const direct = toNumber(
      weather.data?.summary?.precipitation_probability_max ??
        weather.data?.precipitation_probability_max ??
        weather.data?.daily?.precipitation_probability_max?.[0]
    );
    if (direct != null) return direct;

    // New API shape fallback: convert rainy hours in the next 24h into a percent-like value.
    const rainyHours = toNumber(weather.data?.impact_summary?.rainy_hours);
    if (rainyHours == null) return null;
    return Math.max(0, Math.min(100, (rainyHours / 24) * 100));
  })();
  const cloudPct = (() => {
    const direct = toNumber(
      weather.data?.summary?.cloud_cover_pct ??
        weather.data?.cloud_cover_pct ??
        weather.data?.daily?.cloud_cover_mean?.[0]
    );
    if (direct != null) return direct;

    // New API shape fallback: infer cloudiness from average vs peak radiation.
    const avgRadiation = toNumber(weather.data?.impact_summary?.avg_solar_radiation);
    const peakRadiation = toNumber(weather.data?.impact_summary?.peak_solar_radiation);
    if (avgRadiation == null || peakRadiation == null || peakRadiation <= 0) return null;
    const estimate = (1 - (avgRadiation / peakRadiation)) * 100;
    return Math.max(0, Math.min(100, estimate));
  })();
  const next24h = toNumber(
    solarForecast.data?.summary?.next_24h_kwh ??
      solarForecast.data?.next_24h_kwh ??
      solarForecast.data?.next_24h_generation_kwh ??
      solarForecast.data?.daily?.energy_kwh?.[0]
  );

  const barData =
    s?.confidence_buckets?.map((b) => ({
      label: b.label,
      count: b.count,
    })) ?? [];

  const donutData = s?.confidence_split
    ? [
        { id: 'high', name: 'High (≥0.8)', value: s.confidence_split.high },
        { id: 'medium', name: 'Medium (0.7–0.8)', value: s.confidence_split.medium },
        { id: 'low', name: 'Low (<0.7)', value: s.confidence_split.low },
      ]
    : [];

  const donutTotal = donutData.reduce((sum, d) => sum + Number(d.value || 0), 0);
  const highShare =
    donutTotal > 0 ? (Number(donutData.find((d) => d.id === 'high')?.value ?? 0) / donutTotal) : null;

  const cumData = s?.cumulative_by_threshold ?? [];

  const headerStatus = q.isFetching ? 'Updating…' : `Updated ${age}`;

  const backLabel =
    drill?.type === 'bucket'
      ? `Bucket ${drill.label}`
      : drill?.type === 'segment'
        ? `Split ${drill.id}`
        : drill?.type === 'threshold'
          ? `Threshold`
          : null;

  return (
    <div className="space-y-3">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <h2 className="truncate text-sm font-semibold leading-tight">
              {isLocalMode ? (aoiLabel || 'AOI Summary') : 'Overview'}
            </h2>
            {drill ? (
              <Badge variant="secondary" className="text-[10px] tabular-nums">
                Drilldown
              </Badge>
            ) : null}
          </div>
          <p className="truncate text-xs text-muted-foreground leading-tight">{headerStatus}</p>
        </div>
        <Button
          type="button"
          variant="ghost"
          size="icon"
          className="h-8 w-8 shrink-0"
          onClick={() => q.refetch()}
          disabled={q.isFetching}
          aria-label="Refresh stats"
        >
          <RefreshCw className={cn('h-4 w-4', q.isFetching ? 'animate-spin' : '')} />
        </Button>
      </div>

      <div className="grid grid-cols-2 gap-2">
        <KpiTile
          label="Buildings"
          value={buildings != null ? Number(buildings).toLocaleString() : '—'}
          active={activeView === 'buckets'}
          onClick={() => {
            setActiveView('buckets');
            setDrill(null);
          }}
        />
        <KpiTile
          label="Avg confidence"
          value={avgConf != null ? `${(Number(avgConf) * 100).toFixed(1)}%` : '—'}
          sub={avgConf != null ? (Number(avgConf) >= 0.8 ? 'High' : Number(avgConf) >= 0.7 ? 'Med' : 'Low') : null}
          active={activeView === 'split'}
          onClick={() => {
            setActiveView('split');
            setDrill(null);
          }}
        />
        <KpiTile
          label="Roof area"
          value={roofArea != null ? `${Number(roofArea).toLocaleString()} m²` : '—'}
          active={activeView === 'cumulative'}
          onClick={() => {
            setActiveView('cumulative');
            setDrill(null);
          }}
        />
        <KpiTile
          label="CO₂ potential"
          value={co2Est != null ? `${Number(co2Est).toLocaleString()} kg/yr` : '—'}
          active={activeView === 'cumulative'}
          onClick={() => {
            setActiveView('cumulative');
            setDrill(null);
          }}
        />
      </div>

      <div className="space-y-2">
        <InsightCard
          title="High-confidence share"
          detail="How much of the dataset is ≥ 0.8"
          value={highShare != null ? `${(highShare * 100).toFixed(0)}%` : '—'}
          onClick={() => {
            setActiveView('split');
            setDrill({ type: 'segment', id: 'high' });
          }}
        />
        <InsightCard
          title="Dataset scale"
          detail="Buildings × average area"
          value={roofArea != null ? `${Number(roofArea).toLocaleString()} m²` : '—'}
          onClick={() => {
            setActiveView('cumulative');
            setDrill(null);
          }}
        />
      </div>

      {/* Hide forecast and charts when showing local AOI data */}
      {!isLocalMode && (<>
      <div className="rounded-lg border border-border/40 shadow-none bg-background/60 p-3 space-y-2">
        <div className="flex items-center justify-between gap-2">
          <div className="text-xs font-medium text-foreground/90">Forecast snapshot</div>
          <Badge variant="outline" className="text-[10px] tabular-nums">
            {mapCenter[0].toFixed(3)}, {mapCenter[1].toFixed(3)}
          </Badge>
        </div>
        <p className="text-[11px] text-muted-foreground">
          Context for the current map center. Solar estimate uses a {refSystemKwp} kWp reference system.
        </p>
        <div className="grid grid-cols-3 gap-2 text-xs tabular-nums">
          <div className="rounded-md border border-border/40 bg-background/60 p-2">
            <p className="text-muted-foreground">Rain chance</p>
            <p className="mt-1 font-semibold">
              {weather.isLoading ? '...' : weather.isError ? 'Err' : rainProb != null ? `${rainProb.toFixed(0)}%` : '—'}
            </p>
          </div>
          <div className="rounded-md border border-border/40 bg-background/60 p-2">
            <p className="text-muted-foreground">Cloud cover</p>
            <p className="mt-1 font-semibold">
              {weather.isLoading ? '...' : weather.isError ? 'Err' : cloudPct != null ? `${cloudPct.toFixed(0)}%` : '—'}
            </p>
          </div>
          <div className="rounded-md border border-border/40 bg-background/60 p-2">
            <p className="text-muted-foreground">Solar next 24h</p>
            <p className="mt-1 font-semibold">
              {solarForecast.isLoading
                ? '...'
                : solarForecast.isError
                  ? 'Err'
                  : next24h != null
                    ? `${next24h.toFixed(1)} kWh`
                    : '—'}
            </p>
          </div>
        </div>
      </div>

      <div className="rounded-lg border border-border/40 shadow-none bg-background/60 p-2 space-y-2">
        <div className="flex items-center justify-between gap-2">
          <div className="min-w-0">
            <div className="text-xs font-medium text-foreground/90">
              {activeView === 'buckets'
                ? 'Confidence buckets'
                : activeView === 'split'
                  ? 'High / medium / low split'
                  : 'Cumulative by threshold'}
            </div>
            <div className="text-[11px] text-muted-foreground truncate">
              {drill ? `Focused: ${backLabel}` : 'Tap a segment/bar to drill in'}
            </div>
          </div>
          {drill ? (
            <Button
              type="button"
              variant="ghost"
              size="sm"
              className="h-8 px-2 text-xs"
              onClick={() => setDrill(null)}
            >
              <ArrowLeft className="h-4 w-4" />
              Back
            </Button>
          ) : null}
        </div>

        {activeView === 'buckets' ? (
          <ConfidenceBarChart
            data={barData}
            loading={q.isLoading}
            heightClassName="h-52"
            activeLabel={drill?.type === 'bucket' ? drill.label : null}
            onSelectLabel={(label) => setDrill({ type: 'bucket', label })}
          />
        ) : activeView === 'split' ? (
          <ConfidenceDonut
            data={donutData}
            loading={q.isLoading}
            heightClassName="h-52"
            focusKey={drill?.type === 'segment' ? drill.id : null}
            onSelectId={(id) => setDrill({ type: 'segment', id })}
          />
        ) : (
          <CumulativeAreaChart
            data={cumData}
            loading={q.isLoading}
            heightClassName="h-52"
            activeIndex={drill?.type === 'threshold' ? drill.index : null}
            onSelectIndex={(index) => setDrill({ type: 'threshold', index })}
          />
        )}

        {drill?.type === 'bucket' ? (
          <div className="rounded-md border border-border/40 bg-background/60 px-3 py-2 text-xs">
            <div className="font-medium text-foreground/90">What this means</div>
            <div className="text-muted-foreground">
              This bucket represents buildings whose model confidence falls within <span className="tabular-nums">{drill.label}</span>.
            </div>
          </div>
        ) : drill?.type === 'segment' ? (
          <div className="rounded-md border border-border/40 bg-background/60 px-3 py-2 text-xs">
            <div className="font-medium text-foreground/90">Focused segment</div>
            <div className="text-muted-foreground">
              Segment <span className="font-medium text-foreground/90">{drill.id}</span> is emphasized in the split.
            </div>
          </div>
        ) : drill?.type === 'threshold' ? (
          <div className="rounded-md border border-border/40 bg-background/60 px-3 py-2 text-xs">
            <div className="font-medium text-foreground/90">Focused threshold</div>
            <div className="text-muted-foreground">
              Point <span className="tabular-nums">#{drill.index + 1}</span> selected.
            </div>
          </div>
        ) : null}
      </div>
      </>)}
    </div>
  );
}

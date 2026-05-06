import { useEffect, useMemo, useState } from 'react';
import { RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn, estimatePortfolioCo2KgYear } from '@/lib/utils';
import { useStats } from '@/hooks/useStats';
import { KpiCard } from '@/components/stats/KpiCard';
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

const CHARTS = [
  { id: 'bar', label: 'Buckets' },
  { id: 'cum', label: 'Cumulative' },
  { id: 'donut', label: 'Split' },
];

const KPI_TO_CHART = {
  buildings: 'bar',
  avgConfidence: 'donut',
  area: 'cum',
  co2: 'cum',
};

function ToggleButton({ active, children, onClick }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        'h-7 rounded-md px-2 text-[11px] font-medium transition-colors',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring',
        active ? 'bg-accent text-accent-foreground' : 'text-muted-foreground hover:bg-muted/60 hover:text-foreground'
      )}
    >
      {children}
    </button>
  );
}

export function StatsPanel() {
  const q = useStats();
  const [tick, setTick] = useState(0);
  const [chart, setChart] = useState('bar');
  const [focusKey, setFocusKey] = useState(/** @type {string | null} */ (null));
  const [chartPhase, setChartPhase] = useState('in');

  useEffect(() => {
    const id = window.setInterval(() => setTick((t) => t + 1), 10000);
    return () => clearInterval(id);
  }, []);

  const s = q.data;

  const age = useMemo(
    () => (q.dataUpdatedAt ? formatRelative(Date.now() - q.dataUpdatedAt) : '—'),
    [tick, q.dataUpdatedAt]
  );

  const barData =
    s?.confidence_buckets?.map((b) => ({
      label: b.label,
      count: b.count,
    })) ?? [];

  const cumData = s?.cumulative_by_threshold ?? [];

  const donutData = s?.confidence_split
    ? [
        { id: 'high', name: 'High (≥0.8)', value: s.confidence_split.high },
        { id: 'medium', name: 'Medium (0.7–0.8)', value: s.confidence_split.medium },
        { id: 'low', name: 'Low (<0.7)', value: s.confidence_split.low },
      ]
    : [];

  const co2Est = estimatePortfolioCo2KgYear(s);

  const onKpi = (k) => {
    if (q.isFetching) return;
    const next = KPI_TO_CHART[k] ?? 'bar';
    setChartPhase('out');
    window.setTimeout(() => {
      setChart(next);
      if (next === 'donut') setFocusKey('high');
      else setFocusKey(null);
      setChartPhase('in');
    }, 90);
  };

  return (
    <div className="space-y-3">
      <div className="space-y-1">
        <div className="flex items-center justify-between gap-3">
          <div className="min-w-0">
            <h2 className="truncate text-sm font-semibold leading-tight">Overview</h2>
            <p className="truncate text-xs text-muted-foreground leading-tight">
              Database-wide · updated {age}
            </p>
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
      </div>

      <div className="grid grid-cols-2 gap-2">
        <button
          type="button"
          onClick={() => onKpi('buildings')}
          disabled={q.isFetching}
          className={cn(
            'text-left rounded-lg focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring transition-[transform,box-shadow] active:scale-[0.99]',
            !q.isFetching && 'hover:shadow-sm'
          )}
          aria-label="Show confidence buckets chart"
        >
          <KpiCard
            title="Total buildings"
            value={s?.total_buildings?.toLocaleString() ?? '—'}
            loading={q.isLoading}
            className={cn(
              'border border-border/40 shadow-none bg-background/60',
              chart === 'bar' ? 'ring-1 ring-ring/50' : ''
            )}
          />
        </button>

        <button
          type="button"
          onClick={() => onKpi('avgConfidence')}
          disabled={q.isFetching}
          className={cn(
            'text-left rounded-lg focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring transition-[transform,box-shadow] active:scale-[0.99]',
            !q.isFetching && 'hover:shadow-sm'
          )}
          aria-label="Show confidence split chart"
        >
          <KpiCard
            title="Avg confidence"
            value={s?.confidence?.average != null ? `${(s.confidence.average * 100).toFixed(1)}%` : '—'}
            loading={q.isLoading}
            className={cn(
              'border border-border/40 shadow-none bg-background/60',
              chart === 'donut' ? 'ring-1 ring-ring/50' : ''
            )}
          />
        </button>

        <button
          type="button"
          onClick={() => onKpi('area')}
          disabled={q.isFetching}
          className={cn(
            'text-left rounded-lg focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring transition-[transform,box-shadow] active:scale-[0.99]',
            !q.isFetching && 'hover:shadow-sm'
          )}
          aria-label="Show cumulative threshold chart"
        >
          <KpiCard
            title="Total roof area"
            value={
              s?.total_buildings && s?.area_m2?.average
                ? `${Math.round(s.total_buildings * s.area_m2.average).toLocaleString()} m²`
                : '—'
            }
            loading={q.isLoading}
            className={cn(
              'border border-border/40 shadow-none bg-background/60',
              chart === 'cum' ? 'ring-1 ring-ring/50' : ''
            )}
          />
        </button>

        <button
          type="button"
          onClick={() => onKpi('co2')}
          disabled={q.isFetching}
          className={cn(
            'text-left rounded-lg focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring transition-[transform,box-shadow] active:scale-[0.99]',
            !q.isFetching && 'hover:shadow-sm'
          )}
          aria-label="Show cumulative threshold chart"
        >
          <KpiCard
            title="Est. CO₂ potential"
            value={co2Est ? `${co2Est.toLocaleString()} kg/yr` : '—'}
            loading={q.isLoading}
            className={cn(
              'border border-border/40 shadow-none bg-background/60',
              chart === 'cum' ? 'ring-1 ring-ring/50' : ''
            )}
          />
        </button>
      </div>

      <div className="flex items-center gap-1">
        {CHARTS.map((c) => (
          <ToggleButton key={c.id} active={chart === c.id} onClick={() => setChart(c.id)}>
            {c.label}
          </ToggleButton>
        ))}
      </div>

      <div
        className={cn(
          'rounded-lg border border-border/40 shadow-none bg-background/60 p-2 transition-[opacity,transform] duration-150 ease-out',
          chartPhase === 'out' ? 'opacity-0 translate-y-0.5' : 'opacity-100 translate-y-0'
        )}
      >
        {chart === 'bar' ? (
          <ConfidenceBarChart data={barData} loading={q.isLoading} />
        ) : chart === 'cum' ? (
          <CumulativeAreaChart data={cumData} loading={q.isLoading} />
        ) : (
          <ConfidenceDonut data={donutData} loading={q.isLoading} focusKey={focusKey} />
        )}
      </div>
    </div>
  );
}


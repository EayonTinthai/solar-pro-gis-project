import { Badge } from '@/components/ui/badge';

function Divider() {
  return <div className="mx-1 h-6 w-px bg-border/60" aria-hidden />;
}

function KpiChip({ label, value, className }) {
  return (
    <div className={`flex flex-col items-start px-3 ${className ?? ''}`}>
      <span className="text-xs text-muted-foreground leading-none mb-0.5">{label}</span>
      <span className="text-sm font-semibold tabular-nums leading-none">{value ?? '—'}</span>
    </div>
  );
}

/**
 * @param {{
 *   kpis?: { buildings?: any, avgConf?: any, totalArea?: any, co2Saved?: any },
 *   activeFilterCount?: number,
 *   embedded?: boolean,
 * }} props
 */
export function BottomBar({ kpis, activeFilterCount = 0, embedded = false }) {
  const positionStyle = embedded
    ? {
        position: 'relative',
        width: '100%',
        height: '44px',
        display: 'flex',
        alignItems: 'center',
        padding: '0 8px',
        gap: '4px',
        overflowX: 'auto',
      }
    : {
        position: 'absolute',
        bottom: '12px',
        left: '12px',
        right: '12px',
        height: '44px',
        display: 'flex',
        alignItems: 'center',
        padding: '0 8px',
        gap: '4px',
        overflowX: 'auto',
        zIndex: 15,
      };

  return (
    <footer className="glass-panel pointer-events-auto" style={positionStyle}>
      <KpiChip label="Buildings" value={kpis?.buildings} />
      <Divider />
      <KpiChip label="Avg Conf" value={kpis?.avgConf} />
      <Divider />
      <KpiChip label="Total Area" value={kpis?.totalArea} className="hidden sm:flex" />
      <Divider />
      <KpiChip label="CO₂ Saved" value={kpis?.co2Saved} className="hidden sm:flex" />

      <div className="ml-auto flex items-center gap-2 pr-2">
        {activeFilterCount > 0 ? (
          <Badge variant="secondary" className="text-xs tabular-nums">
            {activeFilterCount} filter{activeFilterCount > 1 ? 's' : ''} active
          </Badge>
        ) : null}
      </div>
    </footer>
  );
}


export const nf0 = new Intl.NumberFormat(undefined, { maximumFractionDigits: 0 });

export function formatCount(v) {
  if (v == null) return '—';
  const n = Number(v);
  return Number.isFinite(n) ? nf0.format(n) : String(v);
}

export function formatPct01(v) {
  if (v == null) return '—';
  const n = Number(v);
  if (!Number.isFinite(n)) return String(v);
  return `${(n * 100).toFixed(1)}%`;
}

export function GlassTooltip({ active, label, payload, valueFormatter, labelFormatter }) {
  if (!active || !payload?.length) return null;
  const l = labelFormatter ? labelFormatter(label) : label;
  return (
    <div className="glass-panel pointer-events-none px-3 py-2 text-xs">
      {l != null ? <div className="mb-1 font-medium text-foreground/90">{l}</div> : null}
      <div className="space-y-0.5">
        {payload.map((p) => {
          const v = valueFormatter ? valueFormatter(p.value, p) : p.value;
          return (
            <div key={p.dataKey ?? p.name} className="flex items-center justify-between gap-3">
              <div className="flex items-center gap-2 min-w-0">
                <span
                  className="h-2.5 w-2.5 shrink-0 rounded-sm"
                  style={{ background: p.color ?? p.fill ?? 'hsl(var(--foreground))' }}
                />
                <span className="truncate text-muted-foreground">{p.name ?? p.dataKey}</span>
              </div>
              <span className="tabular-nums text-foreground">{v}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}


import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { formatCount, GlassTooltip } from '@/components/stats/chartUtils.jsx';

/**
 * @param {{ data: Array<{ threshold: number, count: number }>, loading?: boolean, heightClassName?: string, activeIndex?: number | null, onSelectIndex?: (index: number) => void }} props
 */
export function CumulativeAreaChart({
  data,
  loading,
  heightClassName = 'h-56',
  activeIndex = null,
  onSelectIndex,
}) {
  if (loading) {
    return <div className={`${heightClassName} animate-pulse rounded-lg bg-muted`} />;
  }

  const chartData = (data || []).map((d) => ({
    name: `≥ ${d.threshold}`,
    count: d.count,
  }));

  return (
    <div className={`${heightClassName} w-full`}>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={chartData} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border) / 0.55)" />
          <XAxis
            dataKey="name"
            tick={{ fontSize: 11, fill: 'hsl(var(--foreground) / 0.7)' }}
            axisLine={{ stroke: 'hsl(var(--border) / 0.55)' }}
            tickLine={{ stroke: 'hsl(var(--border) / 0.55)' }}
          />
          <YAxis
            tick={{ fontSize: 11, fill: 'hsl(var(--foreground) / 0.7)' }}
            axisLine={{ stroke: 'hsl(var(--border) / 0.55)' }}
            tickLine={{ stroke: 'hsl(var(--border) / 0.55)' }}
            allowDecimals={false}
            tickFormatter={formatCount}
          />
          <Tooltip
            cursor={{ stroke: 'hsl(var(--foreground) / 0.25)' }}
            content={<GlassTooltip valueFormatter={(v) => formatCount(v)} />}
          />
          <Area
            type="monotone"
            dataKey="count"
            name="Buildings"
            stroke="hsl(var(--primary))"
            fill="hsl(var(--primary))"
            fillOpacity={0.22}
            strokeWidth={2}
            dot={(props) => {
              const { cx, cy, index } = props;
              if (cx == null || cy == null) return null;
              const isActive = activeIndex != null && index === activeIndex;
              return (
                <circle
                  cx={cx}
                  cy={cy}
                  r={isActive ? 4 : 2.5}
                  fill="hsl(var(--primary))"
                  fillOpacity={isActive ? 1 : 0.75}
                  stroke="hsl(var(--background))"
                  strokeWidth={isActive ? 2 : 1.5}
                  style={{ cursor: onSelectIndex ? 'pointer' : 'default' }}
                  onClick={() => (onSelectIndex ? onSelectIndex(index) : null)}
                />
              );
            }}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

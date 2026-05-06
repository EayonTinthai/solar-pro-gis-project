import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { CHART_COLORS } from '@/lib/utils';
import { formatCount, GlassTooltip } from '@/components/stats/chartUtils.jsx';

/**
 * @param {{ data: Array<{ label: string, count: number }>, loading?: boolean, heightClassName?: string, activeLabel?: string | null, onSelectLabel?: (label: string) => void }} props
 */
export function ConfidenceBarChart({
  data,
  loading,
  heightClassName = 'h-56',
  activeLabel = null,
  onSelectLabel,
}) {
  if (loading) {
    return <div className={`${heightClassName} animate-pulse rounded-lg bg-muted`} />;
  }

  const chartData = data || [];

  return (
    <div className={`${heightClassName} w-full`}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={chartData} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border) / 0.55)" />
          <XAxis
            dataKey="label"
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
            cursor={{ fill: 'hsl(var(--muted) / 0.35)' }}
            content={<GlassTooltip valueFormatter={(v) => formatCount(v)} />}
          />
          <Bar
            dataKey="count"
            name="Buildings"
            radius={[6, 6, 0, 0]}
            onClick={(p) => {
              const label = p?.label;
              if (label && onSelectLabel) onSelectLabel(label);
            }}
          >
            {chartData.map((d, i) => (
              <Cell
                key={d.label ?? i}
                fill={CHART_COLORS[i % CHART_COLORS.length]}
                opacity={activeLabel && d.label !== activeLabel ? 0.45 : 1}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

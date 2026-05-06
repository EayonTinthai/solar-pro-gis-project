import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts';
import { CHART_COLORS } from '@/lib/utils';
import { formatCount, GlassTooltip } from '@/components/stats/chartUtils.jsx';

/**
 * @param {{ data: Array<{ id?: string, name: string, value: number }>, loading?: boolean, focusKey?: string | null, heightClassName?: string, onSelectId?: (id: string) => void }} props
 */
export function ConfidenceDonut({
  data,
  loading,
  focusKey = null,
  heightClassName = 'h-56',
  onSelectId,
}) {
  if (loading) {
    return <div className={`${heightClassName} animate-pulse rounded-lg bg-muted`} />;
  }

  const chartData = data || [];

  return (
    <div className={`${heightClassName} w-full`}>
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={chartData}
            dataKey="value"
            nameKey="name"
            innerRadius={54}
            outerRadius={86}
            paddingAngle={2}
            onClick={(d) => {
              const id = d?.id;
              if (id && onSelectId) onSelectId(id);
            }}
          >
            {chartData.map((d, i) => (
              <Cell
                key={d.id ?? i}
                fill={CHART_COLORS[i % CHART_COLORS.length]}
                opacity={focusKey && d.id && d.id !== focusKey ? 0.55 : 1}
              />
            ))}
          </Pie>
          <Tooltip content={<GlassTooltip valueFormatter={(v) => formatCount(v)} />} />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}

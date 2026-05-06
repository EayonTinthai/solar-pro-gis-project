import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { formatKwh, formatTHB } from '@/lib/utils';

/**
 * @param {{ items: Array<Record<string, unknown>> }} props
 */
export function SolarHistory({ items }) {
  if (!items?.length) return null;

  const hasWeather = items.some((item) => item?.weather_forecast);

  const weatherBrief = (row) => {
    const w = row?.weather_forecast;
    if (!w) return '—';
    const rain = Number(
      w?.summary?.precipitation_probability_max ??
        w?.precipitation_probability_max ??
        w?.daily?.precipitation_probability_max?.[0]
    );
    if (Number.isFinite(rain)) return `Rain ${rain.toFixed(0)}%`;
    return 'Forecast';
  };

  return (
    <div className="mt-6 space-y-2">
      <h3 className="text-sm font-medium text-muted-foreground">Recent calculations</h3>
      <div className="overflow-x-auto rounded-lg border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>kWp</TableHead>
              <TableHead>kWh/yr</TableHead>
              <TableHead>Savings</TableHead>
              <TableHead>Payback (yr)</TableHead>
              {hasWeather ? <TableHead>Weather</TableHead> : null}
            </TableRow>
          </TableHeader>
          <TableBody>
            {items.map((r, i) => (
              <TableRow key={i}>
                <TableCell className="tabular-nums">{r.system_size_kwp}</TableCell>
                <TableCell className="tabular-nums">{formatKwh(r.annual_production_kwh)}</TableCell>
                <TableCell className="tabular-nums">{formatTHB(r.annual_savings_thb)}</TableCell>
                <TableCell className="tabular-nums">
                  {r.payback_period_years != null ? Number(r.payback_period_years).toFixed(1) : '—'}
                </TableCell>
                {hasWeather ? <TableCell className="tabular-nums">{weatherBrief(r)}</TableCell> : null}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}

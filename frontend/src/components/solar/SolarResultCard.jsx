import { ChevronDown } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';
import { Progress } from '@/components/ui/progress';
import { formatKwh, formatTHB } from '@/lib/utils';

const PAYBACK_REF = 25;

/**
 * @param {{
 *   result: Record<string, unknown> | undefined,
 *   weatherForecast?: Record<string, unknown>,
 *   weatherLoading?: boolean,
 *   weatherError?: boolean,
 *   solarForecast?: Record<string, unknown>,
 *   solarForecastLoading?: boolean,
 *   solarForecastError?: boolean,
 * }} props
 */
export function SolarResultCard({
  result,
  weatherForecast,
  weatherLoading,
  weatherError,
  solarForecast,
  solarForecastLoading,
  solarForecastError,
}) {
  if (!result) return null;

  const toNumber = (v) => {
    const n = Number(v);
    return Number.isFinite(n) ? n : null;
  };

  const weather = weatherForecast || result.weather_forecast || null;
  const weatherTempMax = toNumber(
    weather?.summary?.temp_max_c ??
      weather?.temperature_max_c ??
      weather?.daily?.temperature_2m_max?.[0]
  );
  const weatherRainProb = toNumber(
    weather?.summary?.precipitation_probability_max ??
      weather?.precipitation_probability_max ??
      weather?.daily?.precipitation_probability_max?.[0]
  );
  const weatherCloud = toNumber(
    weather?.summary?.cloud_cover_pct ??
      weather?.cloud_cover_pct ??
      weather?.daily?.cloud_cover_mean?.[0]
  );

  const solarNext24 = toNumber(
    solarForecast?.summary?.next_24h_kwh ??
      solarForecast?.next_24h_kwh ??
      solarForecast?.daily?.energy_kwh?.[0] ??
      solarForecast?.daily?.generation_kwh?.[0]
  );
  const solarNext7 = toNumber(
    solarForecast?.summary?.next_7d_kwh ??
      solarForecast?.next_7d_kwh ??
      solarForecast?.weekly_generation_kwh
  );

  const payback = result.payback_period_years;
  const paybackPct =
    payback != null ? Math.min(100, (Number(payback) / PAYBACK_REF) * 100) : 0;

  const assumptions = result.assumptions || {};

  return (
    <Card className="mt-4">
      <CardHeader>
        <CardTitle className="text-base">Results</CardTitle>
        <CardDescription>pvlib / simplified backend output</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid gap-3 sm:grid-cols-2">
          <div>
            <p className="text-xs font-medium text-muted-foreground">System size</p>
            <p className="text-xl font-bold tabular-nums">{result.system_size_kwp} kWp</p>
          </div>
          <div>
            <p className="text-xs font-medium text-muted-foreground">Annual production</p>
            <p className="text-xl font-bold tabular-nums">{formatKwh(result.annual_production_kwh)}</p>
          </div>
          <div>
            <p className="text-xs font-medium text-muted-foreground">Installation cost</p>
            <p className="text-xl font-bold tabular-nums">{formatTHB(result.installation_cost_thb)}</p>
          </div>
          <div>
            <p className="text-xs font-medium text-muted-foreground">Annual savings</p>
            <p className="text-xl font-bold tabular-nums">{formatTHB(result.annual_savings_thb)}</p>
          </div>
        </div>
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">Payback</span>
            <span className="tabular-nums">
              {payback != null ? `${Number(payback).toFixed(1)}` : '—'} of {PAYBACK_REF} yrs (ref.)
            </span>
          </div>
          <Progress value={paybackPct} className="h-2" />
        </div>
        <div className="flex flex-wrap gap-2">
          <Badge variant="secondary">{result.irradiance_source}</Badge>
          <Badge variant="outline" className="tabular-nums">
            {result.irradiance_kwh_m2_day} kWh/m²/day
          </Badge>
        </div>

        <div className="grid gap-3 sm:grid-cols-2">
          <div className="rounded-lg border border-border/40 bg-background/60 p-3">
            <p className="text-xs font-medium text-muted-foreground">Weather forecast</p>
            {weatherLoading ? (
              <p className="mt-1 text-sm text-muted-foreground">Loading weather...</p>
            ) : weatherError ? (
              <p className="mt-1 text-sm text-destructive">Weather forecast unavailable</p>
            ) : weather ? (
              <div className="mt-2 space-y-1 text-sm tabular-nums">
                <p>Max temp: {weatherTempMax != null ? `${weatherTempMax.toFixed(1)}°C` : '—'}</p>
                <p>Rain chance: {weatherRainProb != null ? `${weatherRainProb.toFixed(0)}%` : '—'}</p>
                <p>Cloud cover: {weatherCloud != null ? `${weatherCloud.toFixed(0)}%` : '—'}</p>
              </div>
            ) : (
              <p className="mt-1 text-sm text-muted-foreground">No weather data</p>
            )}
          </div>

          <div className="rounded-lg border border-border/40 bg-background/60 p-3">
            <p className="text-xs font-medium text-muted-foreground">Solar forecast</p>
            {solarForecastLoading ? (
              <p className="mt-1 text-sm text-muted-foreground">Loading solar forecast...</p>
            ) : solarForecastError ? (
              <p className="mt-1 text-sm text-destructive">Solar forecast unavailable</p>
            ) : solarForecast ? (
              <div className="mt-2 space-y-1 text-sm tabular-nums">
                <p>Next 24h: {solarNext24 != null ? formatKwh(solarNext24) : '—'}</p>
                <p>Next 7d: {solarNext7 != null ? formatKwh(solarNext7) : '—'}</p>
              </div>
            ) : (
              <p className="mt-1 text-sm text-muted-foreground">No solar forecast data</p>
            )}
          </div>
        </div>

        <Collapsible>
          <CollapsibleTrigger className="flex w-full items-center justify-between rounded-lg border px-3 py-2 text-sm font-medium hover:bg-muted">
            Assumptions
            <ChevronDown className="h-4 w-4" />
          </CollapsibleTrigger>
          <CollapsibleContent className="mt-2 space-y-1 rounded-lg bg-muted/50 p-3 text-xs font-mono">
            <p>panel_efficiency: {String(assumptions.panel_efficiency)}</p>
            <p>usable_roof_ratio: {String(assumptions.usable_roof_ratio)}</p>
            <p>cost_per_wp: {String(assumptions.cost_per_wp)}</p>
            <p>electricity_rate: {String(assumptions.electricity_rate)}</p>
            <p>co2_factor: {String(assumptions.co2_factor)}</p>
            <p>calculation_method: {String(assumptions.calculation_method)}</p>
          </CollapsibleContent>
        </Collapsible>
      </CardContent>
    </Card>
  );
}

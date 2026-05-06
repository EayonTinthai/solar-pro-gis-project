import { useEffect, useMemo, useState } from 'react';
import { Leaf, Loader2, X } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Separator } from '@/components/ui/separator';
import { Skeleton } from '@/components/ui/skeleton';
import { calculateSolarPotential } from '@/lib/solar-calc';
import {
  useSolarCalc,
  useSolarForecast,
  useWeatherForecast,
} from '@/hooks/useSolarCalc';
import { useCountUp } from '@/hooks/useCountUp';
import {
  cn,
  confidenceBadgeClassName,
  formatKwh,
  formatTHB,
} from '@/lib/utils';
import { AuthGate } from '@/components/auth/AuthGate';

const PAYBACK_MAX_YEARS = 25;

function formatArea(area) {
  const n = Number(area);
  return Number.isFinite(n) ? `${n.toFixed(1)} m²` : 'Unknown area';
}

/**
 * @param {{
 *   building: Record<string, unknown> | null,
 *   open: boolean,
 *   onOpenChange: (v: boolean) => void,
 * }} props
 */
export function BuildingSheet({ building, open, onOpenChange }) {
  const solar = useSolarCalc();
  const [isMobile, setIsMobile] = useState(false);

  const weather = useWeatherForecast(
    building
      ? {
          lat: Number(building.latitude),
          lon: Number(building.longitude),
          timezone: 'Asia/Bangkok',
        }
      : null,
    { enabled: Boolean(building && open) }
  );

  const solarForecast = useSolarForecast(
    building
      ? {
          lat: Number(building.latitude),
          lon: Number(building.longitude),
          timezone: 'Asia/Bangkok',
          systemKwp: Number(solar.data?.system_size_kwp || 0),
        }
      : null,
    { enabled: Boolean(building && open && Number(solar.data?.system_size_kwp) > 0) }
  );

  useEffect(() => {
    const mq = window.matchMedia?.('(max-width: 768px)');
    if (!mq) return;
    const onChange = () => setIsMobile(mq.matches);
    onChange();
    mq.addEventListener?.('change', onChange);
    return () => mq.removeEventListener?.('change', onChange);
  }, []);

  useEffect(() => {
    solar.reset();
  }, [building?.id]);

  const handleCalc = () => {
    if (!building) return;
    solar.mutate({
      latitude: building.latitude,
      longitude: building.longitude,
      area_m2: building.area_m2,
      confidence: building.confidence,
      tilt: null,
      azimuth: 180,
    });
  };

  const data = solar.data;
  
  // Recalculate with size-dependent costs for differentiated payback
  const localCalc = useMemo(() => {
    if (!building) return null;
    return calculateSolarPotential(
      building.area_m2,
      building.confidence || 0.8,
      Number(building.latitude),
      Number(building.longitude)
    );
  }, [building]);

  // Use backend data for production (pvlib is more accurate) but local calc for cost/payback
  const kwp = useCountUp(data?.system_size_kwp ?? 0, 500);
  const kwh = useCountUp(data?.annual_production_kwh ?? 0, 500);
  const save = useCountUp(localCalc?.annualSavingsTHB?.expected ?? data?.annual_savings_thb ?? 0, 500);
  const cost = useCountUp(localCalc?.totalCostTHB?.expected ?? data?.installation_cost_thb ?? 0, 500);
  const co2 = useCountUp(data?.co2_reduction_kg ?? 0, 500);

  const payback = localCalc?.paybackYears?.expected ?? data?.payback_period_years;
  const paybackMin = localCalc?.paybackYears?.min;
  const paybackMax = localCalc?.paybackYears?.max;
  const paybackPct =
    payback != null ? Math.min(100, (payback / PAYBACK_MAX_YEARS) * 100) : 0;

  const toNumber = (v) => {
    const n = Number(v);
    return Number.isFinite(n) ? n : null;
  };

  const weatherData = weather.data;
  const weatherRain = toNumber(
    weatherData?.summary?.precipitation_probability_max ??
      weatherData?.precipitation_probability_max ??
      weatherData?.daily?.precipitation_probability_max?.[0]
  );
  const weatherCloud = toNumber(
    weatherData?.summary?.cloud_cover_pct ??
      weatherData?.cloud_cover_pct ??
      weatherData?.daily?.cloud_cover_mean?.[0]
  );
  const next24h = toNumber(
    solarForecast.data?.summary?.next_24h_kwh ??
      solarForecast.data?.next_24h_kwh ??
      solarForecast.data?.daily?.energy_kwh?.[0]
  );

  return (
    <aside
      className="glass-panel-lg building-sheet pointer-events-auto overflow-hidden flex flex-col"
      style={{
        position: 'absolute',
        right: isMobile ? '0' : '12px',
        left: isMobile ? '0' : undefined,
        top: isMobile ? undefined : '72px',
        bottom: isMobile ? '52px' : '64px',
        width: isMobile ? '100%' : '360px',
        height: isMobile ? '70vh' : undefined,
        borderRadius: isMobile ? 'var(--radius) var(--radius) 0 0' : undefined,
        transform: isMobile
          ? open && building
            ? 'translateY(0)'
            : 'translateY(100%)'
          : open && building
            ? 'translateX(0)'
            : 'translateX(calc(100% + 24px))',
        transition: 'transform 280ms cubic-bezier(0.16, 1, 0.3, 1)',
        zIndex: 15,
      }}
      aria-hidden={!open}
    >
      <div className="flex items-center justify-between px-4 py-3 border-b border-border/60 flex-shrink-0">
        {isMobile ? <div className="panel-handle" /> : null}
        <div className="min-w-0">
          <h2 className="truncate text-sm font-semibold">
            {building ? `Building #${building.id}` : 'Building'}
          </h2>
          <p className="truncate text-xs text-muted-foreground">
            {building
              ? `${formatArea(building.area_m2)} · confidence ${(Number(building.confidence) * 100).toFixed(1)}%`
              : null}
          </p>
        </div>
        <button
          type="button"
          onClick={() => onOpenChange(false)}
          className="text-muted-foreground hover:text-foreground transition-colors"
          aria-label="Close"
        >
          <X size={16} />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {!building ? (
          <p className="text-sm text-muted-foreground">Select a building on the map.</p>
        ) : (
          <div className="space-y-4">
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant="outline" className="tabular-nums">
                ID {building.id}
              </Badge>
              <Badge variant="outline" className="tabular-nums">
                {formatArea(building.area_m2)}
              </Badge>
            </div>
            <AuthGate
              title="Advanced solar insights require Pro"
              subtitle="Upgrade to run solar estimates and unlock forecast, payback, and savings details."
              className="min-h-[200px]"
            >
              <div className="space-y-4">
                <div className="flex flex-wrap items-center gap-2">
                  <Badge className={cn(confidenceBadgeClassName(Number(building.confidence)))}>
                    Detection confidence: {(Number(building.confidence) * 100).toFixed(1)}%
                  </Badge>
                </div>
                <Button
                  type="button"
                  className="w-full"
                  onClick={handleCalc}
                  disabled={solar.isPending}
                >
                  {solar.isPending ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Calculating…
                    </>
                  ) : (
                    'Calculate solar potential'
                  )}
                </Button>

                {solar.isPending ? (
                  <div className="space-y-3">
                    <Skeleton className="h-24 w-full rounded-lg" />
                    <Skeleton className="h-24 w-full rounded-lg" />
                  </div>
                ) : null}

                {solar.isError ? (
                  <p className="text-sm text-destructive">Could not calculate solar potential.</p>
                ) : null}

                {data && !solar.isPending ? (
                  <div className="space-y-4">
                    <div className="grid grid-cols-2 gap-3">
                      <div className="rounded-lg border border-border/40 shadow-none bg-background/60 p-3">
                        <p className="text-xs font-medium text-muted-foreground">System size</p>
                        <p className="text-xl font-bold tabular-nums">{kwp.toFixed(1)} kWp</p>
                      </div>
                      <div className="rounded-lg border border-border/40 shadow-none bg-background/60 p-3">
                        <p className="text-xs font-medium text-muted-foreground">Annual production</p>
                        <p className="text-xl font-bold tabular-nums">{formatKwh(Math.round(kwh))}</p>
                      </div>
                      <div className="rounded-lg border border-border/40 shadow-none bg-background/60 p-3">
                        <p className="text-xs font-medium text-muted-foreground">Savings / yr</p>
                        <p className="text-xl font-bold tabular-nums">{formatTHB(save)}</p>
                      </div>
                      <div className="rounded-lg border border-border/40 shadow-none bg-background/60 p-3">
                        <p className="text-xs font-medium text-muted-foreground">Install cost</p>
                        <p className="text-xl font-bold tabular-nums">{formatTHB(cost)}</p>
                      </div>
                    </div>
                    <div className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span className="text-muted-foreground">Payback</span>
                        <span className="tabular-nums font-medium">
                          {payback != null ? `${payback.toFixed(1)} yrs` : '—'}
                          {paybackMin != null && paybackMax != null ? ` (${paybackMin.toFixed(1)}–${paybackMax.toFixed(1)})` : ''}
                        </span>
                      </div>
                      <Progress value={paybackPct} className="h-2" />
                    </div>
                    <div className="flex items-center gap-2 rounded-lg border border-border/40 shadow-none bg-background/60 px-3 py-2 text-sm">
                      <Leaf className="h-4 w-4 text-primary" aria-hidden />
                      <span className="tabular-nums font-medium">{Math.round(co2)} kg CO₂ / yr avoided</span>
                    </div>
                    <Separator />
                    <div className="flex flex-wrap gap-2">
                      <Badge variant="secondary">{data.irradiance_source}</Badge>
                      <Badge variant="outline" className="tabular-nums">
                        {data.irradiance_kwh_m2_day} kWh/m²/day
                      </Badge>
                    </div>

                    <div className="grid grid-cols-2 gap-3">
                      <div className="rounded-lg border border-border/40 shadow-none bg-background/60 p-3">
                        <p className="text-xs font-medium text-muted-foreground">Weather</p>
                        {weather.isPending ? (
                          <p className="mt-1 text-sm text-muted-foreground">Loading...</p>
                        ) : weather.isError ? (
                          <p className="mt-1 text-sm text-destructive">Unavailable</p>
                        ) : (
                          <div className="mt-1 text-sm tabular-nums">
                            <p>Rain: {weatherRain != null ? `${weatherRain.toFixed(0)}%` : '—'}</p>
                            <p>Cloud: {weatherCloud != null ? `${weatherCloud.toFixed(0)}%` : '—'}</p>
                          </div>
                        )}
                      </div>
                      <div className="rounded-lg border border-border/40 shadow-none bg-background/60 p-3">
                        <p className="text-xs font-medium text-muted-foreground">Solar forecast</p>
                        {solarForecast.isPending ? (
                          <p className="mt-1 text-sm text-muted-foreground">Loading...</p>
                        ) : solarForecast.isError ? (
                          <p className="mt-1 text-sm text-destructive">Unavailable</p>
                        ) : (
                          <div className="mt-1 text-sm tabular-nums">
                            <p>Next 24h: {next24h != null ? formatKwh(next24h) : '—'}</p>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ) : null}
              </div>
            </AuthGate>
          </div>
        )}
      </div>
    </aside>
  );
}

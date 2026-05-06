import { useEffect, useState } from 'react';
import { Leaf, Loader2, X, Cloud } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Separator } from '@/components/ui/separator';
import { Skeleton } from '@/components/ui/skeleton';
import { useSolarCalc } from '@/hooks/useSolarCalc';
import { useCountUp } from '@/hooks/useCountUp';
import { getWeatherForecast, getSolarForecast, formatWeatherData, formatSolarForecastData } from '@/lib/weatherAPI';
import {
  cn,
  confidenceBadgeClassName,
  formatKwh,
  formatTHB,
} from '@/lib/utils';
import { AuthGate } from '@/components/auth/AuthGate';

const PAYBACK_MAX_YEARS = 25;

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
  const [weatherData, setWeatherData] = useState(null);
  const [weatherLoading, setWeatherLoading] = useState(false);

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
    setWeatherData(null);
  }, [building?.id]);

  const loadWeatherData = async () => {
    if (!building) return;
    
    setWeatherLoading(true);
    try {
      const weather = await getWeatherForecast(building.latitude, building.longitude);
      setWeatherData(formatWeatherData(weather));
    } catch (error) {
      console.error('Weather loading error:', error);
    } finally {
      setWeatherLoading(false);
    }
  };

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
  const kwp = useCountUp(data?.system_size_kwp ?? 0, 500);
  const kwh = useCountUp(data?.annual_production_kwh ?? 0, 500);
  const save = useCountUp(data?.annual_savings_thb ?? 0, 500);
  const cost = useCountUp(data?.installation_cost_thb ?? 0, 500);
  const co2 = useCountUp(data?.co2_reduction_kg ?? 0, 500);

  const payback = data?.payback_period_years;
  const paybackPct =
    payback != null ? Math.min(100, (payback / PAYBACK_MAX_YEARS) * 100) : 0;

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
              ? `${Number(building.area_m2).toFixed(1)} m² · confidence ${(Number(building.confidence) * 100).toFixed(1)}%`
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
          <AuthGate
            title="Building details require Pro"
            subtitle="Inspect footprint data and run solar estimates from the sheet with Pro."
            className="min-h-[200px]"
          >
          <div className="space-y-4">
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant="outline" className="tabular-nums">
                ID {building.id}
              </Badge>
              <Badge className={cn(confidenceBadgeClassName(Number(building.confidence)))}>
                {(Number(building.confidence) * 100).toFixed(1)}%
              </Badge>
            </div>

            {/* Weather Info Button */}
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={loadWeatherData}
              disabled={weatherLoading}
              className="w-full mb-2"
            >
              {weatherLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Loading weather...
                </>
              ) : (
                <>
                  <Cloud className="mr-2 h-4 w-4" />
                  Load weather forecast
                </>
              )}
            </Button>

            {/* Weather Summary */}
            {weatherData && (
              <div 
                className="rounded-lg border p-3 mb-3"
                style={{ 
                  borderLeftColor: weatherData.impactColor,
                  borderLeftWidth: '3px',
                  backgroundColor: `${weatherData.impactColor}08`
                }}
              >
                <div className="flex items-center gap-2 mb-1">
                  <div 
                    className="w-2 h-2 rounded-full"
                    style={{ backgroundColor: weatherData.impactColor }}
                  />
                  <span className="font-medium text-sm">
                    {weatherData.impactLabel} Weather
                  </span>
                </div>
                <div className="grid grid-cols-2 gap-2 text-xs mt-2">
                  <div>
                    <span className="text-muted-foreground">Temp: </span>
                    <span className="font-medium">{weatherData.avgTemp}°C</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Solar: </span>
                    <span className="font-medium">{weatherData.avgSolarRadiation}W/m²</span>
                  </div>
                </div>
              </div>
            )}

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
                      {payback != null ? `${payback.toFixed(1)} yrs` : '—'} of {PAYBACK_MAX_YEARS} yrs ref.
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
              </div>
            ) : null}
          </div>
          </AuthGate>
        )}
      </div>
    </aside>
  );
}

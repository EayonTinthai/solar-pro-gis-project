import { useState } from 'react';
import { SolarForm } from '@/components/solar/SolarForm';
import { SolarResultCard } from '@/components/solar/SolarResultCard';
import { SolarHistory } from '@/components/solar/SolarHistory';
import { useSolarCalc, useSolarForecast, useWeatherForecast } from '@/hooks/useSolarCalc';
import { toast } from 'sonner';

export function SolarPage() {
  const solar = useSolarCalc();
  const [history, setHistory] = useState(/** @type {Array<Record<string, unknown>>} */ ([]));
  const [forecastInput, setForecastInput] = useState(
    /** @type {{ lat: number, lon: number, timezone: string, systemKwp: number } | null} */ (null)
  );

  const weather = useWeatherForecast(forecastInput);
  const solarForecast = useSolarForecast(forecastInput);

  const handleSubmit = async (payload) => {
    try {
      const res = await solar.mutateAsync(payload);
      const systemKwp = Number(res?.system_size_kwp || 0);
      setForecastInput({
        lat: Number(payload.latitude),
        lon: Number(payload.longitude),
        timezone: 'Asia/Bangkok',
        systemKwp,
      });
      setHistory((h) => [res, ...h].slice(0, 5));
    } catch {
      toast.error('Solar calculation failed', {
        action: { label: 'Retry', onClick: () => solar.mutate(payload) },
      });
    }
  };

  return (
    <div className="space-y-4 p-4 md:p-6">
      <div>
        <h2 className="text-balance text-xl font-semibold">Solar calculator</h2>
        <p className="text-sm text-muted-foreground">
          Manual inputs; map center is shared with the map view.
        </p>
      </div>
      <SolarForm onSubmit={handleSubmit} loading={solar.isPending} />
      {solar.isPending ? (
        <div className="h-40 animate-pulse rounded-xl bg-muted" />
      ) : null}
      <SolarResultCard
        result={solar.data}
        weatherForecast={weather.data}
        weatherLoading={weather.isPending}
        weatherError={weather.isError}
        solarForecast={solarForecast.data}
        solarForecastLoading={solarForecast.isPending}
        solarForecastError={solarForecast.isError}
      />
      <SolarHistory items={history} />
    </div>
  );
}

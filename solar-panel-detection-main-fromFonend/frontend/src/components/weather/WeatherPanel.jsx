/**
 * Weather Panel Component - Modern version for new frontend
 * Displays weather forecast and solar impact analysis
 */

import { useState, useEffect } from 'react';
import { X, Cloud, Sun, CloudRain, Snowflake, Loader2, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Separator } from '@/components/ui/separator';
import { getWeatherForecast, getSolarForecast, formatWeatherData, formatSolarForecastData } from '@/lib/weatherAPI';
import { cn } from '@/lib/utils';

const WeatherIcon = ({ weather, size = 16 }) => {
  const iconMap = {
    sunny: Sun,
    cloudy: Cloud,
    rain: CloudRain,
    snow: Snowflake,
  };
  
  const IconComponent = iconMap[weather] || Cloud;
  return <IconComponent size={size} />;
};

/**
 * @param {{
 *   location: { lat: number, lon: number },
 *   systemKwp?: number,
 *   open: boolean,
 *   onOpenChange: (open: boolean) => void,
 * }} props
 */
export function WeatherPanel({ location, systemKwp, open, onOpenChange }) {
  const [weatherData, setWeatherData] = useState(null);
  const [solarForecast, setSolarForecast] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const loadWeatherData = async () => {
    if (!location) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const [weather, solar] = await Promise.all([
        getWeatherForecast(location.lat, location.lon),
        systemKwp ? getSolarForecast(location.lat, location.lon, systemKwp) : null
      ]);
      
      setWeatherData(formatWeatherData(weather));
      setSolarForecast(formatSolarForecastData(solar));
    } catch (err) {
      setError(err.message);
      console.error('Weather data loading error:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (open && location) {
      loadWeatherData();
    }
  }, [open, location, systemKwp]);

  if (!open) return null;

  return (
    <div className="glass-panel-lg pointer-events-auto absolute left-4 top-20 z-20 w-80 max-h-[calc(100vh-120px)] overflow-y-auto">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-border/60 px-4 py-3">
        <div>
          <h3 className="font-semibold text-sm">Weather Forecast</h3>
          <p className="text-xs text-muted-foreground">
            {location.lat.toFixed(4)}, {location.lon.toFixed(4)}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={loadWeatherData}
            disabled={loading}
            className="h-8 w-8 p-0"
          >
            <RefreshCw className={cn("h-4 w-4", loading && "animate-spin")} />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => onOpenChange(false)}
            className="h-8 w-8 p-0"
          >
            <X className="h-4 w-4" />
          </Button>
        </div>
      </div>

      <div className="p-4 space-y-4">
        {loading && (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" />
            Loading weather data...
          </div>
        )}

        {error && (
          <div className="rounded-lg border border-destructive/20 bg-destructive/10 p-3">
            <p className="text-sm text-destructive font-medium">Weather Error</p>
            <p className="text-xs text-destructive/80 mt-1">{error}</p>
            <Button 
              variant="outline" 
              size="sm" 
              onClick={loadWeatherData}
              className="mt-2 h-7 text-xs"
            >
              Retry
            </Button>
          </div>
        )}

        {/* Weather Impact Summary */}
        {weatherData && (
          <div className="space-y-3">
            <div 
              className="rounded-lg border p-3"
              style={{ 
                borderLeftColor: weatherData.impactColor,
                borderLeftWidth: '4px',
                backgroundColor: `${weatherData.impactColor}10`
              }}
            >
              <div className="flex items-center gap-2 mb-2">
                <div 
                  className="w-2 h-2 rounded-full"
                  style={{ backgroundColor: weatherData.impactColor }}
                />
                <span className="font-medium text-sm">
                  {weatherData.impactLabel} Conditions
                </span>
              </div>
              <p className="text-xs text-muted-foreground">
                {weatherData.summary}
              </p>
            </div>

            {/* Current Conditions Grid */}
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="rounded-lg bg-muted/50 p-2">
                <p className="text-muted-foreground">Temperature</p>
                <p className="font-semibold">{weatherData.avgTemp}°C</p>
              </div>
              <div className="rounded-lg bg-muted/50 p-2">
                <p className="text-muted-foreground">Solar Radiation</p>
                <p className="font-semibold">{weatherData.avgSolarRadiation} W/m²</p>
              </div>
              <div className="rounded-lg bg-muted/50 p-2">
                <p className="text-muted-foreground">Rain (24h)</p>
                <p className="font-semibold">{weatherData.totalRain24h} mm</p>
              </div>
              <div className="rounded-lg bg-muted/50 p-2">
                <p className="text-muted-foreground">Rainy Hours</p>
                <p className="font-semibold">{weatherData.rainyHours}/24</p>
              </div>
            </div>
          </div>
        )}

        {/* Solar Forecast Summary */}
        {solarForecast && (
          <>
            <Separator />
            <div className="space-y-3">
              <h4 className="font-medium text-sm">Solar Generation Forecast</h4>
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div className="rounded-lg bg-muted/50 p-2">
                  <p className="text-muted-foreground">Next 24h</p>
                  <p className="font-semibold text-green-600">
                    {solarForecast.next24hGeneration} kWh
                  </p>
                </div>
                <div className="rounded-lg bg-muted/50 p-2">
                  <p className="text-muted-foreground">Weather Score</p>
                  <p className="font-semibold">
                    {solarForecast.weatherQualityScore}/100
                  </p>
                </div>
              </div>
            </div>
          </>
        )}

        {/* Hourly Preview */}
        {weatherData?.hourlyPreview && weatherData.hourlyPreview.length > 0 && (
          <>
            <Separator />
            <div className="space-y-3">
              <h4 className="font-medium text-sm">Next 8 Hours</h4>
              <div className="grid grid-cols-4 gap-2">
                {weatherData.hourlyPreview.slice(0, 8).map((hour, index) => (
                  <div key={index} className="text-center rounded-lg bg-muted/30 p-2">
                    <div className="text-xs text-muted-foreground mb-1">
                      {new Date(hour.time).getHours()}:00
                    </div>
                    <div className="flex justify-center mb-1">
                      <WeatherIcon weather={hour.weather} size={14} />
                    </div>
                    <div className="text-xs font-medium">
                      {hour.temp}°C
                    </div>
                    <div className="text-xs text-muted-foreground">
                      {hour.solar_radiation}W
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </>
        )}

        {/* Weekly Outlook */}
        {solarForecast?.dailyChart && solarForecast.dailyChart.length > 0 && (
          <>
            <Separator />
            <div className="space-y-3">
              <h4 className="font-medium text-sm">7-Day Solar Outlook</h4>
              <div className="space-y-2">
                {solarForecast.dailyChart.slice(0, 5).map((day, index) => (
                  <div key={index} className="flex items-center justify-between text-xs py-1">
                    <div className="flex-1 font-medium">
                      {new Date(day.date).toLocaleDateString('en-US', { 
                        weekday: 'short', 
                        month: 'short', 
                        day: 'numeric' 
                      })}
                    </div>
                    <div className="flex-1 text-center">
                      {day.maxTemp}°C
                    </div>
                    <div className="flex-1 text-center font-medium text-green-600">
                      {day.generation} kWh
                    </div>
                    <div className="flex-1 text-right text-muted-foreground">
                      {day.rainProbability}%
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </>
        )}

        {/* Footer */}
        <Separator />
        <div className="text-center text-xs text-muted-foreground">
          Powered by WxTech 5km Weather API
        </div>
      </div>
    </div>
  );
}
import { useState } from 'react';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Switch } from '@/components/ui/switch';
import { useMapSettings } from '@/contexts/MapSettingsContext';

/**
 * @param {{
 *   onSubmit: (payload: {
 *     latitude: number,
 *     longitude: number,
 *     area_m2: number,
 *     confidence: number,
 *     tilt: number | null,
 *     azimuth: number | null,
 *   }) => void,
 *   loading?: boolean,
 * }} props
 */
export function SolarForm({ onSubmit, loading }) {
  const { mapCenter } = useMapSettings();
  const [lat, setLat] = useState(String(mapCenter[0]));
  const [lon, setLon] = useState(String(mapCenter[1]));
  const [area, setArea] = useState('120');
  const [conf, setConf] = useState('0.85');
  const [tilt, setTilt] = useState('');
  const [azimuth, setAzimuth] = useState('180');
  const [includeWeather, setIncludeWeather] = useState(true);

  const useMapCenter = () => {
    setLat(String(mapCenter[0]));
    setLon(String(mapCenter[1]));
  };

  const submit = (e) => {
    e.preventDefault();
    onSubmit({
      latitude: Number(lat),
      longitude: Number(lon),
      area_m2: Number(area),
      confidence: Number(conf),
      tilt: tilt === '' ? null : Number(tilt),
      azimuth: azimuth === '' ? 180 : Number(azimuth),
      include_weather: includeWeather,
    });
  };

  return (
    <form onSubmit={submit} className="space-y-4 rounded-xl border bg-card p-4 shadow-sm">
      <div className="flex flex-wrap items-end gap-2">
        <Button type="button" variant="secondary" size="sm" onClick={useMapCenter}>
          Use map center
        </Button>
      </div>
      <div className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-2">
          <Label htmlFor="lat">Latitude</Label>
          <Input id="lat" value={lat} onChange={(e) => setLat(e.target.value)} required />
        </div>
        <div className="space-y-2">
          <Label htmlFor="lon">Longitude</Label>
          <Input id="lon" value={lon} onChange={(e) => setLon(e.target.value)} required />
        </div>
        <div className="space-y-2">
          <Label htmlFor="area">Area (m²)</Label>
          <Input id="area" type="number" min={1} step={0.1} value={area} onChange={(e) => setArea(e.target.value)} required />
        </div>
        <div className="space-y-2">
          <Label htmlFor="conf">Confidence (0–1)</Label>
          <Input id="conf" type="number" min={0} max={1} step={0.01} value={conf} onChange={(e) => setConf(e.target.value)} required />
        </div>
        <div className="space-y-2">
          <Label htmlFor="tilt">Tilt (optional)</Label>
          <Input id="tilt" type="number" placeholder="Optimal if empty" value={tilt} onChange={(e) => setTilt(e.target.value)} />
        </div>
        <div className="space-y-2">
          <Label htmlFor="az">Azimuth (°)</Label>
          <Input id="az" type="number" placeholder="180 = south" value={azimuth} onChange={(e) => setAzimuth(e.target.value)} />
        </div>
      </div>
      
      {/* Weather Enhancement Toggle */}
      <div className="flex items-center space-x-2 rounded-lg border p-3">
        <Switch
          id="weather"
          checked={includeWeather}
          onCheckedChange={setIncludeWeather}
        />
        <div className="space-y-1">
          <Label htmlFor="weather" className="text-sm font-medium">
            Include weather forecast
          </Label>
          <p className="text-xs text-muted-foreground">
            Enhance calculations with real-time weather data and 7-day solar forecast
          </p>
        </div>
      </div>
      
      <Button type="submit" className="w-full sm:w-auto" disabled={loading}>
        {loading ? 'Calculating…' : includeWeather ? 'Calculate with weather' : 'Calculate'}
      </Button>
    </form>
  );
}

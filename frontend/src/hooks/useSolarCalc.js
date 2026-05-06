import { useMutation, useQuery } from '@tanstack/react-query';
import {
  fetchSolarCalculate,
  fetchSolarForecast,
  fetchWeatherForecast,
} from '@/lib/api';

/**
 * @typedef {Object} SolarCalcInput
 * @property {number} latitude
 * @property {number} longitude
 * @property {number} area_m2
 * @property {number} confidence
 * @property {number|null} [tilt]
 * @property {number|null} [azimuth]
 */

export function useSolarCalc() {
  return useMutation({
    mutationFn: /** @param {SolarCalcInput} body */ (body) =>
      fetchSolarCalculate({
        latitude: body.latitude,
        longitude: body.longitude,
        area_m2: body.area_m2,
        confidence: body.confidence,
        tilt: body.tilt ?? null,
        azimuth: body.azimuth ?? 180,
      }),
  });
}

/**
 * @param {{ lat?: number, lon?: number, timezone?: string } | null} params
 * @param {{ enabled?: boolean }} [options]
 */
export function useWeatherForecast(params, options = {}) {
  const lat = Number(params?.lat);
  const lon = Number(params?.lon);
  const timezone = params?.timezone || 'Asia/Bangkok';
  const hasCoords = Number.isFinite(lat) && Number.isFinite(lon);
  const enabled = options.enabled ?? hasCoords;

  return useQuery({
    queryKey: ['weather-forecast', lat, lon, timezone],
    queryFn: () =>
      fetchWeatherForecast({
        lat,
        lon,
        timezone,
      }),
    enabled,
    staleTime: 5 * 60 * 1000,
  });
}

/**
 * @param {{ lat?: number, lon?: number, systemKwp?: number, timezone?: string } | null} params
 * @param {{ enabled?: boolean }} [options]
 */
export function useSolarForecast(params, options = {}) {
  const lat = Number(params?.lat);
  const lon = Number(params?.lon);
  const systemKwp = Number(params?.systemKwp);
  const timezone = params?.timezone || 'Asia/Bangkok';
  const hasInputs =
    Number.isFinite(lat) && Number.isFinite(lon) && Number.isFinite(systemKwp) && systemKwp > 0;
  const enabled = options.enabled ?? hasInputs;

  return useQuery({
    queryKey: ['solar-forecast', lat, lon, systemKwp, timezone],
    queryFn: () =>
      fetchSolarForecast({
        lat,
        lon,
        system_kwp: systemKwp,
        timezone,
      }),
    enabled,
    staleTime: 5 * 60 * 1000,
  });
}

import { useMutation } from '@tanstack/react-query';
import { fetchSolarCalculate } from '@/lib/api';

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

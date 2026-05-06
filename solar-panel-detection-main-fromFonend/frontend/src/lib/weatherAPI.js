/**
 * Weather API Service for WxTech Integration
 * Provides weather forecast and solar impact analysis
 */

import { fetchWeatherForecast, fetchSolarForecast } from './api';

/**
 * Weather impact levels with colors and descriptions
 */
export const WEATHER_IMPACT_LEVELS = {
  excellent: {
    color: '#10b981',
    label: 'Excellent',
    description: 'Perfect conditions for solar generation'
  },
  good: {
    color: '#3b82f6',
    label: 'Good',
    description: 'Good conditions with minor weather impact'
  },
  moderate: {
    color: '#f59e0b',
    label: 'Moderate',
    description: 'Some weather impact on generation'
  },
  poor: {
    color: '#ef4444',
    label: 'Poor',
    description: 'Significant weather impact expected'
  }
};

/**
 * Get weather forecast for location
 * @param {number} lat 
 * @param {number} lon 
 * @param {string} timezone 
 * @returns {Promise<Object>}
 */
export async function getWeatherForecast(lat, lon, timezone = 'Asia/Bangkok') {
  return fetchWeatherForecast(lat, lon, timezone);
}

/**
 * Get solar generation forecast with weather data
 * @param {number} lat 
 * @param {number} lon 
 * @param {number} systemKwp 
 * @param {string} timezone 
 * @returns {Promise<Object>}
 */
export async function getSolarForecast(lat, lon, systemKwp, timezone = 'Asia/Bangkok') {
  return fetchSolarForecast(lat, lon, systemKwp, timezone);
}

/**
 * Format weather data for display components
 * @param {Object} weatherData 
 * @returns {Object|null}
 */
export function formatWeatherData(weatherData) {
  if (!weatherData) return null;
  
  const { impact_summary, next_24h_preview } = weatherData;
  
  return {
    impactLevel: impact_summary.impact_level,
    impactColor: WEATHER_IMPACT_LEVELS[impact_summary.impact_level]?.color || '#6b7280',
    impactLabel: WEATHER_IMPACT_LEVELS[impact_summary.impact_level]?.label || 'Unknown',
    summary: impact_summary.summary,
    totalRain24h: impact_summary.total_rain_24h,
    rainyHours: impact_summary.rainy_hours,
    maxTemp: impact_summary.max_temperature,
    avgTemp: impact_summary.avg_temperature,
    peakSolarRadiation: impact_summary.peak_solar_radiation,
    avgSolarRadiation: impact_summary.avg_solar_radiation,
    hourlyPreview: next_24h_preview?.slice(0, 12) || []
  };
}

/**
 * Format solar forecast data for charts and display
 * @param {Object} forecastData 
 * @returns {Object|null}
 */
export function formatSolarForecastData(forecastData) {
  if (!forecastData) return null;
  
  const { hourly_forecast, weekly_outlook } = forecastData;
  
  // Hourly chart data (next 24h)
  const hourlyChartData = hourly_forecast?.map(hour => ({
    time: new Date(hour.time).getHours(),
    generation: hour.generation_kwh,
    solarRadiation: hour.solar_radiation,
    temperature: hour.temperature,
    weather: hour.weather
  })) || [];
  
  // Daily chart data (next 7 days)
  const dailyChartData = weekly_outlook?.map(day => ({
    date: day.date,
    generation: day.estimated_generation,
    solarRadiation: day.solar_radiation,
    maxTemp: day.max_temp,
    rainProbability: day.rain_probability
  })) || [];
  
  return {
    next24hGeneration: forecastData.next_24h_generation_kwh,
    weatherQualityScore: forecastData.weather_quality_score,
    hourlyChart: hourlyChartData,
    dailyChart: dailyChartData,
    analysisTime: forecastData.analysis_time
  };
}
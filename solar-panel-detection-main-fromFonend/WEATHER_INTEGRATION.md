# Weather Integration for Solar Panel Detection System

This document describes the weather integration features added to the solar panel detection system, providing real-time weather forecasts and solar generation predictions.

## Overview

The weather integration enhances the solar panel detection system with:

- **Real-time weather forecasts** using WxTech 5km Global Weather API
- **Solar generation predictions** with weather-enhanced calculations
- **Weather impact analysis** for solar potential assessment
- **7-day solar outlook** with daily generation estimates
- **Interactive weather panel** with detailed forecasts

## Architecture

### Backend Components

1. **Weather Service** (`backend/weather_service.py`)
   - WxTech API client with async HTTP requests
   - Weather data parsing and formatting
   - Solar impact analysis algorithms
   - Forecast data caching and optimization

2. **Weather API Endpoints** (`backend/api_weather_only.py`)
   - `/weather/forecast` - Get weather forecast for location
   - `/solar/forecast` - Get solar generation forecast with weather data
   - `/health` - API health check

3. **Enhanced Solar Calculations** (`backend/api_bigquery.py`)
   - Integration with pvlib-python for physics-based modeling
   - Weather-enhanced solar potential calculations
   - Real-time weather data incorporation

### Frontend Components

1. **Weather Panel** (`frontend/src/components/weather/WeatherPanel.jsx`)
   - Interactive weather forecast display
   - Solar generation predictions
   - Weather impact visualization
   - Hourly and daily forecast charts

2. **Weather Toggle** (`frontend/src/components/weather/WeatherToggle.jsx`)
   - Floating button to toggle weather panel
   - Visual indicator for weather panel state

3. **Weather API Service** (`frontend/src/lib/weatherAPI.js`)
   - API client for weather endpoints
   - Data formatting and processing utilities
   - Error handling and retry logic

4. **Enhanced Building Sheet** (`frontend/src/components/map/BuildingSheet.jsx`)
   - Weather information for selected buildings
   - Weather-enhanced solar calculations
   - Real-time weather impact display

## Features

### Weather Forecast Panel

- **Current Conditions**: Temperature, solar radiation, precipitation
- **Hourly Forecast**: Next 8-12 hours with weather icons
- **Daily Outlook**: 7-day forecast with generation estimates
- **Weather Impact**: Color-coded impact levels (Excellent/Good/Moderate/Poor)

### Solar Generation Predictions

- **24-hour Generation**: Estimated kWh production for next 24 hours
- **Weather Quality Score**: 0-100 score based on solar conditions
- **Generation Factors**: Real-time efficiency calculations
- **Weekly Outlook**: Daily generation estimates for planning

### Building Analysis Enhancement

- **Weather-Enhanced Calculations**: Real-time weather data integration
- **Impact Assessment**: Weather impact on solar potential
- **Forecast Integration**: Future generation predictions
- **Visual Indicators**: Color-coded weather impact levels

## API Integration

### WxTech Weather API

- **Endpoint**: `https://wxtech.weathernews.com/api/v2/global/wx`
- **Coverage**: Global 5km resolution weather data
- **Forecast**: 72-hour hourly + 14-day daily forecasts
- **Data**: Temperature, precipitation, solar radiation, wind, humidity

### Weather Data Structure

```javascript
{
  "location": [lat, lon],
  "timezone": "Asia/Bangkok",
  "hourly": [
    {
      "forecast_time": "2024-03-30T12:00:00Z",
      "weather_code": 100,
      "temperature_c": 32,
      "solar_radiation_wm2": 850,
      "precip_mm_per_hr": 0.0,
      "weather_main": "sunny"
    }
  ],
  "daily": [
    {
      "forecast_date": "2024-03-30",
      "max_temp_c": 35,
      "min_temp_c": 26,
      "daily_solar_radiation": 25.5,
      "precip_probability_pct": 10
    }
  ]
}
```

### Solar Forecast Response

```javascript
{
  "next_24h_generation_kwh": 45.2,
  "weather_quality_score": 85,
  "hourly_forecast": [
    {
      "time": "2024-03-30T12:00:00Z",
      "generation_kwh": 3.2,
      "solar_radiation": 850,
      "temperature": 32,
      "weather": "sunny"
    }
  ],
  "weekly_outlook": [
    {
      "date": "2024-03-30",
      "estimated_generation": 42.5,
      "solar_radiation": 25.5,
      "max_temp": 35,
      "rain_probability": 10
    }
  ]
}
```

## Deployment

### Backend Deployment

The weather-enhanced backend is deployed to Google Cloud Run:

```bash
# Deploy weather API
./deploy-weather-api.ps1
```

**Service URL**: `https://solar-weather-api-715107904640.asia-southeast1.run.app`

### Frontend Deployment

The frontend with weather integration is deployed to Firebase:

```bash
# Deploy frontend with weather features
./deploy-frontend-weather.ps1
```

### Complete System Deployment

Deploy both backend and frontend together:

```bash
# Deploy complete weather-enhanced system
./deploy-weather-system.ps1
```

## Environment Configuration

### Backend Environment Variables

```bash
# WxTech API Configuration
WXTECH_API_KEY=pEfaXCQdGHdWpuSbGM0k2CoxnCWToODm26xfs890

# Google Cloud Configuration
GOOGLE_CLOUD_PROJECT=solar-panel-detection-440806
```

### Frontend Environment Variables

```bash
# API Endpoints
VITE_BUILDINGS_API_URL=https://solar-weather-api-715107904640.asia-southeast1.run.app

# Clerk Authentication
VITE_CLERK_PUBLISHABLE_KEY=pk_test_REPLACE_ME
```

## Usage

### Weather Panel

1. **Open Weather Panel**: Click the cloud icon in the top-right corner
2. **View Forecast**: See current conditions and hourly/daily forecasts
3. **Solar Predictions**: View generation estimates and weather impact
4. **Location-Based**: Weather data updates based on map center

### Building Analysis

1. **Select Building**: Click on any building on the map
2. **Load Weather**: Click "Load weather forecast" in the building sheet
3. **Enhanced Calculations**: Use weather data for more accurate solar estimates
4. **Impact Assessment**: See weather impact on solar potential

### Solar Calculator

1. **Weather Toggle**: Enable "Include weather forecast" option
2. **Enhanced Results**: Get weather-enhanced solar calculations
3. **Forecast Integration**: See future generation predictions
4. **Real-time Data**: Use current weather conditions for accuracy

## Performance

### API Response Times

- Weather forecast: < 500ms
- Solar forecast: < 600ms
- Building analysis: < 400ms

### Caching Strategy

- Weather data cached for 15 minutes
- Solar forecasts cached for 30 minutes
- Building weather data cached per session

### Error Handling

- Graceful degradation when weather API unavailable
- Retry logic with exponential backoff
- Fallback to basic solar calculations

## Monitoring

### Health Checks

- `/health` endpoint for API monitoring
- Weather API connectivity checks
- Database connection monitoring

### Logging

- Weather API request/response logging
- Error tracking and alerting
- Performance metrics collection

## Future Enhancements

### Planned Features

1. **Historical Weather Data**: Integration with historical weather patterns
2. **Weather Alerts**: Notifications for severe weather affecting solar generation
3. **Seasonal Analysis**: Long-term weather pattern analysis
4. **Advanced Forecasting**: Machine learning-enhanced predictions
5. **Weather Maps**: Visual weather overlay on the map interface

### API Improvements

1. **Caching Optimization**: Redis-based caching for better performance
2. **Batch Processing**: Multiple location weather requests
3. **WebSocket Updates**: Real-time weather data streaming
4. **Offline Support**: Cached weather data for offline usage

## Support

For technical support or questions about the weather integration:

- **Documentation**: This file and inline code comments
- **API Testing**: Use the provided test scripts
- **Deployment Issues**: Check the deployment logs and error messages
- **Weather Data**: Verify WxTech API key and connectivity

## License

This weather integration uses the WxTech Weather API under commercial license. Ensure proper API key management and usage compliance.
# Solar Panel Detection System with Weather Integration

A comprehensive solar panel detection and analysis system enhanced with real-time weather forecasting and solar generation predictions.

## 🌟 Features

### Core Functionality
- **Building Detection**: AI-powered solar panel detection on building rooftops
- **Solar Potential Analysis**: Physics-based solar generation calculations using pvlib-python
- **Interactive Map**: Leaflet-based map interface with building visualization
- **Authentication**: Secure user authentication with Clerk
- **Pro Features**: Advanced analytics and unlimited access

### Weather Integration ⭐ NEW
- **Real-time Weather Forecasts**: WxTech 5km Global Weather API integration
- **Solar Generation Predictions**: Weather-enhanced 24-hour and 7-day forecasts
- **Weather Impact Analysis**: Color-coded impact levels for solar potential
- **Interactive Weather Panel**: Detailed weather information with hourly/daily forecasts
- **Enhanced Calculations**: Weather-aware solar potential assessments

## 🏗️ Architecture

### Backend Services
- **Buildings API**: Core building detection and solar calculations
- **Weather API**: Real-time weather data and solar forecasting
- **Database**: PostgreSQL with PostGIS for geospatial data
- **Authentication**: Clerk integration for user management

### Frontend Application
- **Modern React**: Vite + React 18 with TypeScript support
- **UI Components**: Radix UI with Tailwind CSS styling
- **State Management**: TanStack Query for server state
- **Map Integration**: React Leaflet for interactive mapping
- **Weather Interface**: Custom weather panel and forecast components

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ and npm
- Python 3.9+ with pip
- Google Cloud SDK
- Firebase CLI
- PostgreSQL with PostGIS

### Backend Setup

1. **Clone and setup**:
   ```bash
   git clone <repository>
   cd solar-panel-detection-main
   ```

2. **Install Python dependencies**:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and database credentials
   ```

4. **Start backend services**:
   ```bash
   # Weather-enhanced API
   python api_weather_only.py
   
   # Or full BigQuery integration
   python api_bigquery.py
   ```

### Frontend Setup

1. **Install dependencies**:
   ```bash
   cd frontend
   npm install
   ```

2. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your API URLs and Clerk keys
   ```

3. **Start development server**:
   ```bash
   npm run dev
   ```

### Weather Integration Setup

1. **Get WxTech API Key**: Contact WxTech for API access
2. **Configure Backend**: Add `WXTECH_API_KEY` to backend `.env`
3. **Update Frontend**: Set `VITE_BUILDINGS_API_URL` to weather API endpoint
4. **Deploy**: Use provided deployment scripts

## 📡 API Endpoints

### Weather API
- `GET /weather/forecast` - Get weather forecast for location
- `GET /solar/forecast` - Get solar generation forecast with weather data
- `GET /health` - API health check

### Buildings API
- `GET /buildings/bbox` - Get buildings in bounding box
- `GET /buildings/nearby` - Get buildings near location
- `POST /solar/calculate` - Calculate solar potential (weather-enhanced)
- `GET /stats` - Get system statistics

## 🌤️ Weather Features

### Weather Panel
- Current weather conditions
- 8-hour hourly forecast
- 7-day daily outlook
- Solar radiation data
- Weather impact assessment

### Solar Forecasting
- 24-hour generation predictions
- Weather quality scoring (0-100)
- Generation efficiency factors
- Weekly solar outlook

### Building Analysis
- Weather-enhanced solar calculations
- Real-time weather impact display
- Location-specific forecasts
- Visual weather indicators

## 🚀 Deployment

### Complete System Deployment
```bash
# Deploy weather-enhanced system
./deploy-weather-system.ps1
```

### Individual Component Deployment
```bash
# Backend weather API
./deploy-weather-api.ps1

# Frontend with weather integration
./deploy-frontend-weather.ps1
```

### Production URLs
- **Frontend**: https://solar-panel-detection-440806.web.app
- **Weather API**: https://solar-weather-api-715107904640.asia-southeast1.run.app
- **Buildings API**: https://buildings-api-715107904640.asia-southeast1.run.app

## 🧪 Testing

### Weather Integration Tests
```bash
# Test all weather features
./test-weather-integration.ps1

# Test specific endpoints
./test-weather-endpoints.ps1
```

### API Testing
```bash
# Test production deployment
./test-production.ps1

# Test all features
./test-features.ps1
```

## 📊 Technology Stack

### Backend
- **Python 3.9+**: Core backend language
- **FastAPI**: Modern web framework
- **pvlib-python**: Solar modeling and calculations
- **aiohttp**: Async HTTP client for weather API
- **PostgreSQL + PostGIS**: Geospatial database
- **Google Cloud Run**: Serverless deployment

### Frontend
- **React 18**: Modern React with hooks
- **Vite**: Fast build tool and dev server
- **TypeScript**: Type-safe JavaScript
- **Tailwind CSS**: Utility-first CSS framework
- **Radix UI**: Accessible component library
- **TanStack Query**: Server state management
- **React Leaflet**: Interactive maps
- **Firebase Hosting**: Static site hosting

### Weather Integration
- **WxTech API**: 5km global weather data
- **Real-time Forecasting**: Hourly and daily predictions
- **Solar Radiation Data**: Direct and diffuse irradiance
- **Weather Impact Analysis**: Automated assessment algorithms

## 🔧 Configuration

### Environment Variables

#### Backend
```bash
# Weather API
WXTECH_API_KEY=your_wxtech_api_key

# Database
DATABASE_URL=postgresql://user:pass@host:port/db

# Google Cloud
GOOGLE_CLOUD_PROJECT=your_project_id
```

#### Frontend
```bash
# API Endpoints
VITE_BUILDINGS_API_URL=https://your-weather-api.run.app

# Authentication
VITE_CLERK_PUBLISHABLE_KEY=pk_test_your_key

# Payments
VITE_STRIPE_PAYMENT_LINK_URL=https://buy.stripe.com/your_link
```

## 📈 Performance

### API Response Times
- Weather forecast: < 500ms
- Solar forecast: < 600ms
- Building queries: < 400ms
- Map data loading: < 300ms

### Caching Strategy
- Weather data: 15-minute cache
- Solar forecasts: 30-minute cache
- Building data: Session-based cache
- Map tiles: Browser cache

## 🔒 Security

- **API Authentication**: Clerk JWT tokens
- **CORS Configuration**: Restricted origins
- **Rate Limiting**: API endpoint protection
- **Environment Variables**: Secure credential storage
- **HTTPS Only**: All production traffic encrypted

## 📚 Documentation

- **Weather Integration**: See `WEATHER_INTEGRATION.md`
- **API Documentation**: Available at `/docs` endpoint
- **Deployment Guide**: See deployment scripts
- **Testing Guide**: See test scripts

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new features
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License. Weather data provided by WxTech under commercial license.

## 🆘 Support

For technical support:
- Check the documentation files
- Review the test scripts for examples
- Verify environment configuration
- Check deployment logs for errors

---

**Weather-Enhanced Solar Panel Detection System** - Combining AI-powered building detection with real-time weather forecasting for accurate solar potential analysis.
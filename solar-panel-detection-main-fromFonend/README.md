# Solar Buildings Map

A geospatial web application for analyzing rooftop solar photovoltaic potential on building footprints using custom segmentation models and physics-based solar modeling.

## Overview

This application provides accurate solar energy potential assessments for buildings in Thailand by combining:

- **Custom Building Segmentation**: Deep learning-based building footprint detection with confidence scores
- **Google Open Buildings Dataset**: Supplementary reference data for validation and coverage
- **pvlib-python**: Industry-standard photovoltaic system modeling library
- **NASA POWER API**: Satellite-derived solar irradiance data
- **Interactive Mapping**: Real-time visualization on satellite imagery

The system calculates technical and financial feasibility metrics including system sizing, energy production, installation costs, payback periods, and carbon emission reductions.

## Technical Architecture

### Frontend

- **Framework**: React 18
- **Mapping**: Leaflet with Esri World Imagery basemap
- **Visualization**: GeoJSON rendering with confidence-based color coding
- **API Integration**: RESTful communication with FastAPI backend

### Backend

- **Framework**: FastAPI (Python 3.9+)
- **Database**: PostgreSQL 14+ with PostGIS spatial extension
- **Solar Modeling**: pvlib-python 0.10.3+
- **Data Source**: NASA POWER API for location-specific irradiance

### Database

- **Engine**: PostgreSQL with PostGIS
- **Schema**: Spatial indexes on building geometries
- **Data Volume**: Supports millions of building records
- **Deployment**: Docker containerized for portability

## Solar Calculation Methodology

### Calculation Engine

The application employs a two-tier calculation approach:

1. **Primary Method**: pvlib-python physics-based modeling
2. **Fallback Method**: Simplified empirical calculation

### pvlib-python Implementation

The primary calculation method uses pvlib-python, a community-supported library developed by Sandia National Laboratories and maintained by the pvlib community. This approach provides research-grade accuracy through:

**Solar Position Calculation**

- Astronomical algorithms for sun position (azimuth, zenith)
- Accounts for atmospheric refraction and equation of time
- Hourly resolution over full calendar year

**Irradiance Modeling**

- Clear sky irradiance model (Ineichen-Perez)
- Decomposition of Global Horizontal Irradiance (GHI) into Direct Normal Irradiance (DNI) and Diffuse Horizontal Irradiance (DHI)
- Transposition to tilted plane-of-array (POA) irradiance
- Accounts for ground reflection (albedo)

**Temperature Effects**

- Sandia Array Performance Model (SAPM) for cell temperature
- Accounts for ambient temperature, wind speed, and mounting configuration
- Temperature coefficient applied to power output (-0.4%/°C typical for monocrystalline silicon)

**System Performance**

- PVWatts DC model for module power output
- Inverter efficiency modeling (96% nominal)
- System losses including soiling, wiring, and mismatch

### Calculation Parameters

All parameters are referenced to published sources and Thailand-specific data:

#### Solar Irradiance

- **Default Value**: 5.06 kWh/m²/day
- **Source**: World Bank Global Solar Atlas via RatedPower (2022)
- **Regional Variation**: Bangkok/Central region 4.8-5.3 kWh/m²/day
- **Seasonal Peak**: April-May 5.6-6.7 kWh/m²/day
- **Dynamic Source**: NASA POWER API ALLSKY_SFC_SW_DWN parameter when available
- **Reference**: https://ratedpower.com/blog/solar-energy-thailand/

#### Panel Efficiency

- **Value**: 20% (0.20)
- **Technology**: Standard commercial monocrystalline silicon
- **Industry Range**: 18-22% (IRENA, IEA PVPS Thailand 2021)
- **Justification**: Representative of current market-available modules

#### System Efficiency (Performance Ratio)

- **Value**: 80% (0.80)
- **Standard**: IEC 61724
- **Thailand Studies**: 75-82% observed in rooftop installations
- **Loss Factors**:
  - Inverter losses: 2-5%
  - Wiring losses: 2%
  - Soiling/dust: 3%
  - Temperature derating: 5-8% (Thailand climate)
  - Mismatch losses: 2%
- **Reference**: IEA PVPS National Survey Report Thailand 2021
  - https://iea-pvps.org/wp-content/uploads/2022/09/NSR-of-PV-Power-Applications-in-Thailand-2021.pdf

#### Usable Roof Area

- **Value**: 50% (0.50)
- **Justification**: Conservative estimate for Thailand urban buildings
- **Exclusions**:
  - HVAC equipment and water tanks
  - Roof edge setbacks (safety and wind loading)
  - Shading from parapet walls and adjacent structures
  - Access pathways and maintenance clearances
- **Academic Basis**: GIS-based rooftop PV potential studies use 40-60% depending on building type
- **Building Type Variation**:
  - Residential: 55-60%
  - Commercial/Industrial: 40-50%
- **Reference**: "Evaluating rooftop solar PV potential in Thailand" (DEDE data 2022)
  - https://www.researchgate.net/figure/Breakdown-of-the-costs-of-a-100-kWp-solar-rooftop-PV-system

#### Installation Cost

- **Value**: 25 THB/Wp
- **Segment**: Commercial and Industrial (C&I) rooftop systems
- **Trend**: Decreased from 27.5 THB/Wp (2020) to 25 THB/Wp (2024)
- **Residential Systems**: Higher at approximately 39 THB/Wp due to smaller scale
- **Academic Benchmark**: 25.14 THB/Wp for 100 kWp hospital system in Southern Thailand
- **References**:
  - Krungsri Research "Rooftop Solar Business Models Thailand" 2025
    - https://www.krungsri.com/en/research/research-intelligence/solar-rooftop-2-2025
  - ResearchGate breakdown study (DEDE data)

#### Electricity Rate

- **Value**: 4.18 THB/kWh
- **Basis**: 2024 actual average rate
- **Context**: Government capped rate at 3.99 THB/kWh through end of 2025
- **Historical Average**: 4.26 THB/kWh (2024-2025 period)
- **Rate Authority**: Energy Regulatory Commission (ERC), Metropolitan Electricity Authority (MEA), Provincial Electricity Authority (PEA)
- **References**:
  - https://www.globalpetrolprices.com/Thailand/electricity_prices/
  - https://www.nationthailand.com/business/economy/40049646
  - Krungsri Research citing ERC data

#### CO₂ Emission Factor

- **Value**: 0.40 kgCO₂/kWh
- **Exact Value**: 0.399 kgCO₂/kWh (2024)
- **Trend**: Decreased from 0.438 kgCO₂/kWh (2023)
- **Source**: Energy Policy and Planning Office (EPPO), Ministry of Energy Thailand
- **Data Provider**: CEIC
- **Reference**: https://www.ceicdata.com/en/thailand/carbon-dioxide-emissions-statistics

### Calculation Formulas

The following formulas are applied in sequence:

**1. Usable Roof Area**

```
usable_roof_area = building_area × usable_roof_ratio × confidence_adjustment
```

where `confidence_adjustment = max(building_confidence, 0.7)` to account for Google Open Buildings detection uncertainty.

**2. System Size**

```
system_size_kWp = usable_roof_area × panel_efficiency
```

Based on Standard Test Conditions (STC): 1 m² of panel at 20% efficiency under 1 kW/m² irradiance = 0.20 kWp.

**3. Annual Energy Production**

_pvlib method (primary):_

```
For each hour in year:
  solar_position = calculate_sun_position(latitude, longitude, timestamp)
  clearsky_irradiance = ineichen_clearsky_model(solar_position)
  poa_irradiance = transpose_to_plane(clearsky_irradiance, tilt, azimuth)
  cell_temperature = sapm_temperature_model(poa_irradiance, ambient_temp, wind_speed)
  dc_power = pvwatts_dc_model(poa_irradiance, cell_temperature, system_size_kWp)
  ac_power = dc_power × inverter_efficiency

annual_production_kWh = sum(ac_power) / 1000
```

_Simplified method (fallback):_

```
annual_production_kWh = system_size_kWp × avg_irradiance × 365 × system_efficiency
```

**4. Financial Metrics**

```
installation_cost_THB = system_size_kWp × 1000 × cost_per_Wp
annual_savings_THB = annual_production_kWh × electricity_rate
payback_period_years = installation_cost_THB / annual_savings_THB
```

**5. Environmental Impact**

```
co2_reduction_kg_per_year = annual_production_kWh × co2_emission_factor
co2_reduction_tonnes_per_year = co2_reduction_kg_per_year / 1000
```

### Data Sources

**Building Footprints**

- **Primary Source**: Custom segmentation model trained for building detection
- **Model Architecture**: Deep learning-based semantic segmentation
- **Supplementary Data**: Google Open Buildings dataset for validation and coverage extension
- **Coverage**: Thailand nationwide with focus on Bangkok Metropolitan Region
- **Records**: 1.88M+ buildings
- **Attributes**: Geometry (polygon), area, confidence score, centroid coordinates
- **Output Format**: GeoJSON/PostGIS-compatible geometries

**Segmentation Model Details**

- **Input**: High-resolution satellite imagery
- **Output**: Building footprint polygons with confidence scores
- **Confidence Score**: Model prediction certainty (0.0-1.0)
- **Post-processing**: Polygon simplification, area filtering, geometry validation

**Google Open Buildings (Reference)**

- **Usage**: Validation, gap filling, and coverage extension
- **License**: Open Data Commons Open Database License (ODbL)
- **Access**: https://sites.research.google/open-buildings/

**Solar Irradiance**

- **Primary Source**: NASA POWER (Prediction Of Worldwide Energy Resources)
- **Parameter**: ALLSKY_SFC_SW_DWN (All-Sky Surface Shortwave Downward Irradiance)
- **Temporal Resolution**: Monthly climatology (long-term average)
- **Spatial Resolution**: 0.5° × 0.625° (approximately 50 km)
- **Data Period**: 1984-present (GEWEX SRB + CERES SYN1deg)
- **API**: https://power.larc.nasa.gov/api/temporal/monthly/point
- **Documentation**: https://power.larc.nasa.gov/docs/

## System Requirements

### Minimum Requirements

- **Operating System**: Windows 10/11, macOS 10.15+, Linux (Ubuntu 20.04+)
- **RAM**: 4 GB
- **Disk Space**: 2 GB free space
- **Software**:
  - Node.js 16.0.0 or higher
  - Python 3.9.0 or higher
  - Docker Desktop 20.10.0 or higher (for database)

### Recommended Requirements

- **RAM**: 8 GB or higher
- **Disk Space**: 10 GB or higher (for full dataset)
- **Network**: Broadband internet connection for NASA POWER API access

## Installation

### 1. Clone Repository

```bash
git clone https://github.com/Teera235/shushi.git
cd shushi
```

### 2. Backend Setup

```bash
cd backend
pip install -r requirements.txt
```

Required Python packages:

- fastapi==0.104.1
- uvicorn[standard]==0.24.0
- psycopg2-binary==2.9.9
- python-dotenv==1.0.0
- pydantic==2.5.0
- pvlib==0.10.3
- pandas==2.1.4
- numpy==1.26.2
- requests==2.31.0

### 3. Frontend Setup

```bash
cd ../frontend
npm install
```

### 4. Database Setup

#### Using Docker (Recommended)

```bash
cd ..
docker-compose up -d
```

This creates:

- PostgreSQL 15 with PostGIS 3.3 extension
- Container name: `solar-pro-db`
- Port: 5432
- Database: `solar_pro`
- User: `postgres`
- Password: `solar_pro_2024`

#### Manual PostgreSQL Installation

If not using Docker:

1. Install PostgreSQL 14 or higher
2. Install PostGIS extension
3. Create database:

```sql
CREATE DATABASE solar_pro;
\c solar_pro
CREATE EXTENSION postgis;
```

4. Run initialization script:

```bash
psql -U postgres -d solar_pro -f database/init.sql
```

### 5. Environment Configuration

#### Backend Configuration

Create `backend/.env`:

```env
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=solar_pro_2024
DB_NAME=solar_pro
```

For production deployment with connection string:

```env
DATABASE_URL=postgresql://user:password@host:port/database
```

#### Frontend Configuration

Create `frontend/.env`:

```env
REACT_APP_BUILDINGS_API_URL=http://localhost:8001
```

For production:

```env
REACT_APP_BUILDINGS_API_URL=https://your-api-domain.com
```

### 6. Data Import

The application requires building footprint data in the PostgreSQL database.

#### Sample Data (100 buildings)

For testing and demonstration:

```bash
cd database
python import_sample_data.py
```

#### Custom Segmentation Model Output

If you have building footprints from the custom segmentation model:

```bash
python import_custom_data.py --file path/to/segmentation_output.geojson
```

Expected format:

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Polygon",
        "coordinates": [[[lng, lat], ...]]
      },
      "properties": {
        "area_m2": 250.5,
        "confidence": 0.95
      }
    }
  ]
}
```

#### Google Open Buildings Dataset (Supplementary)

For additional coverage or validation:

1. Download from Google Open Buildings:
   - Visit: https://sites.research.google/open-buildings/
   - Select: Thailand → Bangkok Metropolitan Region
   - Format: Parquet or CSV
   - Size: Approximately 275 MB compressed

2. Import using provided script:

```bash
python import_google_buildings.py --file path/to/downloaded/file.parquet
```

## Running the Application

### Development Mode

#### Terminal 1: Start Backend API

```bash
cd backend
python api.py
```

Backend will run at: http://localhost:8001

API documentation available at: http://localhost:8001/docs

#### Terminal 2: Start Frontend

```bash
cd frontend
npm start
```

Frontend will run at: http://localhost:3000

### Production Mode

#### Backend

```bash
cd backend
uvicorn api:app --host 0.0.0.0 --port 8001 --workers 4
```

#### Frontend

```bash
cd frontend
npm run build
# Serve build directory with nginx, Apache, or static hosting service
```

## API Endpoints

### Buildings Data

**GET /stats**

- Description: Database statistics and extent
- Response: Total buildings, confidence statistics, area statistics, geographic extent

**GET /buildings/bbox**

- Description: Retrieve buildings within bounding box
- Parameters:
  - `min_lat` (float, required): Minimum latitude
  - `max_lat` (float, required): Maximum latitude
  - `min_lon` (float, required): Minimum longitude
  - `max_lon` (float, required): Maximum longitude
  - `limit` (int, optional): Maximum results (default: 1000, max: 5000)
  - `min_confidence` (float, optional): Minimum confidence threshold (default: 0.7)
- Response: Array of building objects with geometries

**GET /buildings/nearby**

- Description: Retrieve buildings near a point
- Parameters:
  - `lat` (float, required): Latitude
  - `lon` (float, required): Longitude
  - `radius_m` (float, optional): Search radius in meters (default: 500)
  - `limit` (int, optional): Maximum results (default: 100, max: 1000)
  - `min_confidence` (float, optional): Minimum confidence threshold (default: 0.7)
- Response: Array of building objects with distance

**GET /buildings/{id}**

- Description: Retrieve detailed building information
- Parameters:
  - `id` (int, required): Building ID
- Response: Building object with full geometry and metadata

### Solar Calculations

**POST /solar/calculate**

- Description: Calculate solar potential using pvlib-python
- Request Body:

```json
{
  "latitude": 13.7563,
  "longitude": 100.5018,
  "area_m2": 250.0,
  "confidence": 0.95,
  "tilt": null,
  "azimuth": 180
}
```

- Response:

```json
{
  "usable_roof_area": 119,
  "system_size_kwp": 23.8,
  "annual_production_kwh": 34560,
  "installation_cost_thb": 595000,
  "annual_savings_thb": 144461,
  "payback_period_years": 4.1,
  "co2_reduction_kg": 13824,
  "co2_reduction_ton": 13.8,
  "irradiance_source": "pvlib (Clear Sky Model)",
  "irradiance_kwh_m2_day": 5.12,
  "assumptions": {
    "panel_efficiency": 0.2,
    "usable_roof_ratio": 0.5,
    "cost_per_wp": 25,
    "electricity_rate": 4.18,
    "co2_factor": 0.4,
    "calculation_method": "pvlib"
  }
}
```

## User Interface

### Map View

- **Basemap**: Esri World Imagery (satellite)
- **Overlay**: Esri World Boundaries and Places (labels)
- **Building Rendering**: GeoJSON polygons with confidence-based coloring
  - Green (≥90%): High confidence
  - Blue (80-90%): Good confidence
  - Orange (70-80%): Moderate confidence
  - Red (<70%): Low confidence

### Information Panels

**Buildings Data Panel** (Top Right)

- Displayed buildings count
- Total buildings in current view
- Truncation notice if limit exceeded

**Solar Potential Panel** (Bottom Left)
Appears when building is selected:

- Building area and usable roof area
- System size (kWp)
- Confidence score
- Annual energy production (kWh)
- Annual savings (THB)
- Installation cost (THB)
- Payback period (years)
- CO₂ reduction (kg/year)
- Solar irradiance value and data source

**Confidence Legend** (Bottom Right)

- Color-coded confidence level reference

## Database Schema

### buildings Table

```sql
CREATE TABLE buildings (
    id SERIAL PRIMARY KEY,
    open_buildings_id VARCHAR(255) UNIQUE NOT NULL,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    area_m2 DOUBLE PRECISION NOT NULL,
    confidence DOUBLE PRECISION NOT NULL,
    geometry GEOMETRY(Polygon, 4326) NOT NULL,
    centroid GEOMETRY(Point, 4326) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_buildings_geom ON buildings USING GIST (geometry);
CREATE INDEX idx_buildings_centroid ON buildings USING GIST (centroid);
CREATE INDEX idx_buildings_confidence ON buildings (confidence);
CREATE INDEX idx_buildings_area ON buildings (area_m2);
```

## Performance Considerations

### Frontend

- Building rendering limited to 1000 features per view to maintain responsiveness
- GeoJSON features cached by React state
- Map bounds change debounced to reduce API calls

### Backend

- Spatial indexes on geometry columns for fast bounding box queries
- Connection pooling for database efficiency
- CORS configured for cross-origin requests

### Database

- PostGIS spatial indexes (GIST) for geometry queries
- Confidence and area indexes for filtering
- Query optimization for large datasets

## Deployment

### Docker Deployment

```bash
docker-compose up -d
```

### Cloud Deployment Options

**Google Cloud Platform**

- Cloud Run for backend API
- Cloud Storage + Cloud CDN for frontend
- Cloud SQL for PostgreSQL database

**Amazon Web Services**

- Elastic Container Service (ECS) for backend
- S3 + CloudFront for frontend
- RDS for PostgreSQL database

**Microsoft Azure**

- App Service for backend
- Static Web Apps for frontend
- Database for PostgreSQL

## Limitations and Assumptions

### Data Limitations

- Building footprints from segmentation model represent 2D roof area; actual 3D geometry not available
- Confidence scores reflect model prediction certainty, not roof condition or structural suitability
- Segmentation accuracy depends on satellite imagery resolution and quality
- No information on roof material, age, or load-bearing capacity
- Shading from trees, adjacent buildings, or terrain not modeled
- Model may have varying accuracy across different building types and urban densities

### Calculation Assumptions

- Assumes flat or optimally-tilted roof surface
- Does not account for roof orientation variations within single building
- Temperature modeling uses regional averages, not microclimate data
- Soiling losses based on typical urban environment
- No consideration of local regulations, grid connection requirements, or permitting

### Operational Assumptions

- System maintenance performed according to manufacturer specifications
- No major component failures during payback period
- Electricity rates remain constant (actual rates may vary)
- Net metering or feed-in tariff policies not modeled

## Troubleshooting

### Database Connection Errors

- Verify PostgreSQL is running: `docker ps` or `systemctl status postgresql`
- Check credentials in `backend/.env`
- Ensure PostGIS extension is installed: `SELECT PostGIS_version();`
- Verify network connectivity to database host

### Frontend Not Displaying Buildings

- Check backend API is running: `curl http://localhost:8001/stats`
- Verify database contains data: `SELECT COUNT(*) FROM buildings;`
- Open browser console for JavaScript errors
- Check CORS configuration in backend API

### pvlib Calculation Errors

- Verify pvlib installation: `pip show pvlib`
- Check Python version compatibility (3.9+)
- Review backend logs for detailed error messages
- Fallback to simplified calculation if pvlib unavailable

### Performance Issues

- Reduce `limit` parameter in API calls
- Add additional database indexes for frequently queried columns
- Use sample data instead of full dataset for development
- Consider database query optimization or read replicas for production

## License

This project is licensed under the MIT License. See LICENSE file for details.

### Third-Party Licenses

- **Custom Segmentation Model**: Proprietary (contact repository owner for licensing)
- **Google Open Buildings**: Open Data Commons Open Database License (ODbL) - used as supplementary reference data
- **pvlib-python**: BSD 3-Clause License
- **NASA POWER Data**: Public domain (U.S. Government work)
- **Leaflet**: BSD 2-Clause License
- **React**: MIT License
- **FastAPI**: MIT License

## References

### Academic and Technical Publications

1. IEA PVPS (2021). "National Survey Report of PV Power Applications in Thailand 2021"
   - International Energy Agency Photovoltaic Power Systems Programme
   - https://iea-pvps.org/wp-content/uploads/2022/09/NSR-of-PV-Power-Applications-in-Thailand-2021.pdf

2. Krungsri Research (2025). "Rooftop Solar Business Models Thailand"
   - Bank of Ayudhya PCL Research Department
   - https://www.krungsri.com/en/research/research-intelligence/solar-rooftop-2-2025

3. RatedPower (2022). "Solar Energy in Thailand: Market Overview and Potential"
   - https://ratedpower.com/blog/solar-energy-thailand/

4. CEIC Data. "Thailand Carbon Dioxide Emissions Statistics"
   - Energy Policy and Planning Office (EPPO) data
   - https://www.ceicdata.com/en/thailand/carbon-dioxide-emissions-statistics

5. Global Petrol Prices (2024). "Thailand Electricity Prices"
   - https://www.globalpetrolprices.com/Thailand/electricity_prices/

### Data Sources

6. Google Research (2024). "Open Buildings Dataset"
   - https://sites.research.google/open-buildings/

7. NASA POWER Project. "Prediction Of Worldwide Energy Resources"
   - https://power.larc.nasa.gov/

### Software Documentation

8. pvlib-python Documentation
   - https://pvlib-python.readthedocs.io/

9. PostGIS Documentation
   - https://postgis.net/documentation/

10. FastAPI Documentation
    - https://fastapi.tiangolo.com/

## Contact and Support

For technical issues, feature requests, or questions:

- GitHub Issues: https://github.com/Teera235/shushi/issues
- Repository: https://github.com/Teera235/shushi

## Acknowledgments

This project utilizes data and tools from:

- Custom building segmentation model development team
- Google Research Open Buildings team (supplementary reference data)
- NASA Langley Research Center POWER Project
- pvlib-python development community
- Sandia National Laboratories (pvlib original development)
- Thailand Department of Alternative Energy Development and Efficiency (DEDE)
- Energy Regulatory Commission of Thailand (ERC)

---

**Version**: 1.0.0  
**Last Updated**: March 2026  
**Tested On**: Windows 11, Node.js 18, Python 3.11, PostgreSQL 15

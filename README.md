# Solar Pro — GIS-Based Rooftop Solar PV Potential Assessment

A web-based GIS platform for assessing rooftop solar photovoltaic potential across Thailand, with Bangkok Metropolitan Region as the pilot area. Built for the GIS Computing course.

## What It Does

- **Building-level solar potential estimation** using pvlib-python (physics-based PV modeling)
- **Interactive map** with 107M+ building footprints color-coded by payback period
- **Area of Interest (AOI) selection** — choose Bangkok districts or draw custom polygons
- **Multi-criteria ranking** — find top buildings by production, payback, or capacity within an AOI
- **Size-dependent financial model** — realistic payback differentiation (3–6 years depending on building size)
- **Uncertainty quantification** — min/max ranges for all estimates (±15% irradiance, ±10% cost)

## Architecture

```
Frontend (React + Vite + Leaflet)
    ↕ REST API
Backend (FastAPI + pvlib-python)
    ↕ BigQuery SQL
Google BigQuery (107M+ buildings from Google Open Buildings v3)
```

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Frontend | React 18, Leaflet, Tailwind CSS | Interactive map, AOI selection, ranking |
| Backend | FastAPI, pvlib-python 0.10.3 | Solar calculation, spatial queries |
| Database | Google BigQuery | 107M+ building footprints (Thailand) |
| Irradiance | NASA POWER API + pvlib clear sky | Location-specific solar resource data |
| Boundaries | GADM 4.1 | Bangkok 50 districts (เขต) |

## Quick Start (Local Development)

```bash
# Frontend
cd frontend
npm install
npx vite
# → http://localhost:3000
```

No API keys required for local development — Clerk auth is mocked automatically, and the frontend connects to the production API on Cloud Run.

### Optional: Backend locally

```bash
cd backend
pip install -r requirements.txt
# Set GCP_PROJECT and GOOGLE_APPLICATION_CREDENTIALS in .env
uvicorn api_bigquery:app --port 8080
```

## Solar Calculation Methodology

The platform uses a **two-tier calculation approach**:

1. **Primary**: pvlib-python hourly simulation (Ineichen-Perez clear sky → POA transposition → SAPM temperature → PVWatts DC)
2. **Fallback**: Simplified model using Thailand average irradiance (5.06 kWh/m²/day)

### Key Parameters

| Parameter | Value | Source |
|-----------|-------|--------|
| Panel efficiency | 20% | Industry standard (monocrystalline) |
| Performance ratio | 80% | IEA PVPS Thailand 2021 |
| Usable roof ratio | 50% | GIS-based rooftop studies |
| Installation cost | 20–35 THB/Wp (size-dependent) | Krungsri Research 2025 |
| Electricity rate | 4.18 THB/kWh | ERC Thailand 2024 |
| CO₂ factor | 0.40 kgCO₂/kWh | EPPO Thailand 2024 |

### Size-Dependent Cost Model

| Building Category | System Size | Cost/Wp | Typical Payback |
|-------------------|-------------|---------|-----------------|
| Residential | <10 kWp | 35 THB/Wp | 5.5 years |
| Small Commercial | 10–50 kWp | 28 THB/Wp | 4.5 years |
| Medium Commercial | 50–100 kWp | 25 THB/Wp | 4.0 years |
| Large C&I | >100 kWp | 20 THB/Wp | 3.2 years |

## GIS Features

- **Payback-based thematic mapping** — green (≤3.5 yr), blue (3.5–4.5), yellow (4.5–5.5), red (>5.5)
- **Bangkok district boundaries** — 50 districts from GADM 4.1 (real polygons)
- **Custom AOI drawing** — freeform polygon with point-in-polygon filtering
- **Spatial queries** — bounding box, proximity, polygon containment
- **Geocoding** — search by place name (Nominatim/Google Maps)

## Documentation

| Document | Description |
|----------|-------------|
| [Technical Report](docs/TECHNICAL_REPORT.md) | Full academic report (Introduction → Results → Discussion) |
| [Literature Review](docs/LITERATURE_REVIEW.md) | Referenced review of methods and data sources |
| [Methodology](docs/METHODOLOGY.md) | Every formula with step-by-step derivation and sources |
| [Results](docs/RESULTS.md) | Platform outputs, validation, and key findings |

## Data Sources

- **Building footprints**: Google Open Buildings v3 (Sirko et al., 2023) — 107M+ buildings in Thailand
- **Solar irradiance**: NASA POWER (ALLSKY_SFC_SW_DWN) + pvlib Ineichen-Perez clear sky model
- **Admin boundaries**: GADM 4.1 (Bangkok level 2 districts)
- **Market data**: Krungsri Research 2025, IEA PVPS Thailand 2021, ERC, EPPO

## References

1. Holmgren, W.F. et al. (2018). "pvlib python: a python package for modeling solar energy systems." *JOSS*, 3(29), 884.
2. Sirko, W. et al. (2023). "Continental-Scale Building Detection from High Resolution Satellite Imagery." *arXiv:2107.12283v3*.
3. IEA PVPS (2021). "National Survey Report of PV Power Applications in Thailand."
4. Krungsri Research (2025). "Rooftop Solar Business Models Thailand."
5. NASA POWER Project. https://power.larc.nasa.gov/

## License

MIT

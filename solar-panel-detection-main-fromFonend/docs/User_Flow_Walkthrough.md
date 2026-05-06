# Solar Buildings Map — User Flow Walkthrough (Stakeholder Demo)

This document is a **presentation-ready walkthrough** of the Solar Buildings Map platform: what it does, how users move through the UI, and how the Free vs Pro experience works.

---

### Executive summary (what this platform does)

- **What it is**: A web map that visualizes **building footprints** (polygons) and estimates **rooftop solar potential** for selected buildings.
- **What users get**:
  - Explore a region and see building polygons color-coded by **detection confidence**
  - Review **dataset statistics**a and apply **filters**
  - Open a **data table**, fly-to a building on the map, and **export CSV**
  - (Pro) Run a **solar potential calculation** with annual production, cost, savings, payback, and CO₂ impact

---

### 60-second demo script (talk track)

1. **Start on the map** and pan/zoom around Bangkok; call out that every polygon is a detected building footprint.
2. Point to the **legend** (“Confidence”) and explain the color meaning (higher confidence = greener).
3. Open the **left panel** and quickly click through **Stats → Filters → Data** to show the analysis workflow.
4. In **Data**, pick a row and click **Map** to “fly-to” that building, then click the building to open the **Building sheet**.
5. Click **Calculate solar potential** (mention: **Pro feature**) and show the results (kWh/yr, THB/yr, payback, CO₂).
6. Close with: “Free users can explore and export; Pro unlocks physics-based solar potential modeling and ROI metrics.”

---

## Product tour (mental model)

### The 4 core surfaces

- **Map (full screen)**: The primary canvas for exploration; polygons are clickable.
- **Left panel (Stats / Filters / Data / Solar)**: The analysis “workspace” for stats, filtering, table browsing, and the manual Solar calculator.
- **Building sheet (right side)**: Appears after selecting a building; contains building details and the one-click solar calculation path.
- **Top & bottom UI**:
  - **Top bar**: Search/command palette, settings, sign-in, upgrade.
  - **Bottom bar**: KPI chips (buildings count, avg confidence, total area, CO₂ potential) and “filters active”.

### Navigation shortcuts

- **Command palette**: Press **⌘K** (Mac) or **Ctrl+K** (Windows/Linux) to open “Search pages or locations…”.
  - Type a location (geocoding) to fly there, or choose a page (Map / Statistics / Buildings data / Solar calculator).
- **Left panel tabs**: **Stats**, **Filters**, **Data**, **Solar**.
- **Map controls (bottom-right)**: **Zoom in**, **Zoom out**, **My location** (geolocation).
- **Settings** (top-right): Theme, basemap, default confidence threshold, default result limit, polygon color mode, subscription section.

---

## Flow A — Anonymous map exploration (no sign-in)

### A1. Open the app

What you’ll see immediately:

- A satellite basemap (default) with **building polygons**.
- **Legend** on the lower-left (“Confidence”) explaining polygon colors.
- **Map controls** on the lower-right (zoom and my-location).
- **Left panel** (collapsed by default) you can open with the chevron button.

### A2. Interpret building polygons

- Each polygon is a building footprint.
- Polygon color represents **confidence**:
  - **Green**: ≥ 90%
  - **Blue**: 80–90%
  - **Orange**: 70–80%
  - **Red**: < 70%

### A3. Explore a place fast

- Press **⌘K / Ctrl+K**, start typing a place name, and choose a result under **Locations**.
- The map flies to that location and you can continue exploring.

### A4. Open a building

- Click any polygon.
- The **Building sheet** slides in and shows:
  - Building ID
  - Area (m²)
  - Confidence (%)
  - A **Calculate solar potential** button (may be Pro-gated depending on account status)

---

## Flow B — Sign up / sign in (Clerk) and feature gates

### B1. Where sign-in appears

You’ll see sign-in entry points in two common places:

- **Top bar**: “Sign in” and “Get started”
- **Feature gates**: If a feature requires access, the UI shows an overlay card prompting:
  - **Sign in** (Free features)
  - **Upgrade to Pro** (Pro-only features)

### B2. What becomes available after sign-in (Free plan)

After sign-in, the following experiences are intended to be available for free accounts:

- **Filters** (left panel “Filters” tab)
- **Buildings data table** (left panel “Data” tab)
- **Export CSV** from the data table

### B3. What remains Pro-only

- **Solar calculator** features are Pro-gated:
  - Manual solar calculator (Solar tab)
  - One-click solar calculation from the Building sheet

---

## Flow C — Buildings data table, “load in map”, and CSV export

This is the “from exploration to reporting” workflow.

### C1. Open the Data tab

- Open the left panel and click **Data**.
- If you are signed out, you’ll see a **Sign in to view buildings** gate.

### C2. Filter/sort the table (table-level refinement)

In the Data table you can:

- **Sort** by ID, Area, Confidence, Lat, Lon.
- **Filter**:
  - Confidence range slider (0.50–1.00)
  - Min/Max area inputs
  - Per-column text filters (ID, area, confidence, lat, lon)
- Paginate and change **rows per page**.

### C3. Open details from the table

- Click a row to open the **Building sheet**.
- This is the fastest way to move from “list” → “detail”.

### C4. Fly to a row on the map (“Map” button)

- Click the **Map** button (pin icon) on a row.
- The map flies to the building and highlights it.
- This is helpful when you’ve found the right building in the table and want to visually confirm it.

### C5. Export CSV

- Click **Export CSV**.
- Exported columns:
  - `id`, `area_m2`, `confidence`, `latitude`, `longitude`
- Important: Export is gated behind **sign-in**. If signed out, you’ll be prompted to sign in.

---

## Flow D — Upgrade to Pro and use the Solar calculator

### D1. Upgrade entry points

Users can reach upgrade from:

- **Top bar**: “Upgrade to Pro”
- **Settings → Subscription**: “Upgrade to Pro →”
- Pro-gated overlays (e.g., Solar calculator) with a primary “Upgrade to Pro” action

### D2. Checkout behavior (Stripe Payment Link)

- Clicking upgrade takes the user to a **Stripe Payment Link** checkout.
- After checkout, the app recognizes the return state via the URL query parameter:
  - `?payment=success` shows a “Welcome to Pro…” message
  - `?payment=cancelled` shows “Checkout cancelled.”

### D3. How Pro status is displayed

- Signed-in users may see a **Pro badge** (or Pro indicator) instead of the upgrade prompt.

### D4. Solar calculation path 1: from a building (recommended demo)

1. Click a building polygon on the map (or choose a row from Data).
2. In the **Building sheet**, click **Calculate solar potential**.
3. Results appear in the sheet, including:
   - System size (kWp)
   - Annual production (kWh/yr)
   - Savings per year (THB/yr)
   - Installation cost (THB)
   - Payback period (years)
   - CO₂ avoided (kg/yr)
   - Irradiance source + kWh/m²/day used

### D5. Solar calculation path 2: manual Solar tab (inputs + map center)

1. Open the left panel and click **Solar**.
2. Use **Use map center** to populate latitude/longitude.
3. Fill in area (m²), confidence (0–1), optional tilt, and azimuth (default 180 = south).
4. Click **Calculate** and review the result card and recent history.

---

## Interpreting results (what the numbers mean)

### Solar metrics

- **System size (kWp)**: Estimated PV system capacity based on usable roof area and panel efficiency.
- **Annual production (kWh/yr)**: Estimated yearly energy output.
- **Savings / yr (THB/yr)**: \(annual_production \times electricity_rate\).
- **Installation cost (THB)**: \(kWp \times 1000 \times cost_per_Wp\).
- **Payback (years)**: \(installation_cost / annual_savings\).
- **CO₂ avoided (kg/yr)**: \(annual_production \times co2_factor\).

### Key assumptions (demo-safe summary)

The calculations are intended to be a **feasibility estimate**, not a construction-ready design. The default assumptions are Thailand-oriented and include:

- Panel efficiency (representative commercial module)
- Usable roof ratio (accounts for setbacks and obstacles)
- Confidence adjustment (very low confidence is clamped upward in calculations)
- Electricity rate (THB/kWh)
- Installation cost per Wp
- CO₂ grid factor

### What the solar engine does (high level)

When you click **Calculate**, the backend estimates usable roof area and runs one of two approaches:

- **Primary**: pvlib-based, physics-style modeling (clear-sky irradiance + temperature + inverter efficiency).
- **Fallback**: Simplified model using **NASA POWER** irradiance when available; otherwise a Thailand-average irradiance default.

The API response includes an `irradiance_source` field so you can see what was used for a given calculation.

### Limitations (important to say out loud in a stakeholder demo)

- Building polygons represent **2D roof footprint area**; no 3D roof geometry is used.
- No explicit modeling of **shading** (trees, nearby buildings), roof condition, structural capacity, or local permitting constraints.
- Payback and savings assume a **constant electricity rate** and do not model net metering or feed-in tariffs.
- Confidence is a **model certainty signal**, not a guarantee of installability.

---

## FAQ / common issues (demo-friendly)

### “No buildings are showing”

- Likely causes:
  - Buildings API is unreachable
  - Wrong `VITE_BUILDINGS_API_URL` configuration
- What to do:
  - Use the in-app retry (if shown)
  - Confirm the backend/API is up and the frontend environment is set

### “I can’t open Filters / Data / Export”

- These are **sign-in gated** features.
- Sign in from the **Top bar** or the gate overlay.

### “Solar calculator is locked”

- Solar is **Pro-only**.
- Upgrade from the gate overlay, Top bar, or Settings → Subscription.

### “I upgraded but I’m still not Pro”

- Pro access is determined from your account metadata; it may take a moment to propagate after checkout.
- Refresh after checkout success, then confirm you see a Pro indicator (badge / plan = Pro in settings).

### “My location doesn’t work”

- Browser geolocation requires permission. If denied, the map can’t center on you.

---

## Appendix — Demo setup checklist (optional)

### Minimal configuration (frontend)

To run a realistic stakeholder demo, ensure these env vars are set for the frontend build:

- `VITE_CLERK_PUBLISHABLE_KEY` (auth UI)
- `VITE_BUILDINGS_API_URL` (buildings + solar API base)
- `VITE_STRIPE_PAYMENT_LINK_URL` and `VITE_STRIPE_PRO_PRICE_DISPLAY` (upgrade modal)

### Backend capabilities (what the UI calls)

- Buildings:
  - `GET /stats`
  - `GET /buildings/bbox`
  - `GET /buildings/{id}`
- Solar:
  - `POST /solar/calculate`

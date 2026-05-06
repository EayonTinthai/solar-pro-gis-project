/**
 * Solar potential calculation with size-dependent costs and location-specific irradiance.
 * Differentiates payback periods based on building size and location.
 */

/**
 * Size-dependent installation cost (THB/Wp)
 * Source: Krungsri Research 2025, DEDE data
 * - Residential (<10 kWp): 35 THB/Wp
 * - Small commercial (10-50 kWp): 28 THB/Wp
 * - Medium commercial (50-100 kWp): 25 THB/Wp
 * - Large C&I (>100 kWp): 20 THB/Wp
 *
 * Uses linear interpolation within each tier for smooth transitions.
 */
export function getCostPerWp(systemSizeKwp) {
  if (systemSizeKwp <= 0) return 35;

  // Tier breakpoints: [sizeKwp, costPerWp]
  const tiers = [
    [0, 35],
    [10, 35],
    [10.01, 28],
    [50, 28],
    [50.01, 25],
    [100, 25],
    [100.01, 20],
    [500, 20],
  ];

  // Smooth interpolation using a continuous curve
  // This avoids discontinuities at tier boundaries
  if (systemSizeKwp <= 10) return 35;
  if (systemSizeKwp <= 50) {
    // Linear interpolation from 35 to 28 between 10-50 kWp
    const t = (systemSizeKwp - 10) / 40;
    return 35 - t * 7;
  }
  if (systemSizeKwp <= 100) {
    // Linear interpolation from 28 to 25 between 50-100 kWp
    const t = (systemSizeKwp - 50) / 50;
    return 28 - t * 3;
  }
  if (systemSizeKwp <= 500) {
    // Linear interpolation from 25 to 20 between 100-500 kWp
    const t = (systemSizeKwp - 100) / 400;
    return 25 - t * 5;
  }
  return 20;
}

/**
 * Location-adjusted irradiance for Bangkok districts.
 * Bangkok ranges from 4.8-5.3 kWh/m²/day depending on urban heat island and local conditions.
 *
 * Model: Base irradiance adjusted by distance from urban core and latitude gradient.
 * - Central Bangkok (dense urban): lower due to pollution/UHI → ~4.8 kWh/m²/day
 * - Outer Bangkok (suburban): higher due to less pollution → ~5.3 kWh/m²/day
 *
 * @param {number} lat - Latitude
 * @param {number} lon - Longitude
 * @returns {number} Daily irradiance in kWh/m²/day
 */
export function getLocalIrradiance(lat, lon) {
  // Bangkok center approximately at 13.75°N, 100.52°E
  const centerLat = 13.75;
  const centerLon = 100.52;

  // Distance from center in degrees (rough proxy for urban density)
  const dLat = lat - centerLat;
  const dLon = lon - centerLon;
  const distFromCenter = Math.sqrt(dLat * dLat + dLon * dLon);

  // Base irradiance for Bangkok region
  const baseIrradiance = 4.8;
  // Max bonus for being far from urban core (up to 0.5 kWh/m²/day)
  const urbanBonus = Math.min(distFromCenter / 0.3, 1.0) * 0.5;

  // Slight latitude gradient (higher latitude in Bangkok = slightly less irradiance)
  const latAdjustment = (lat - 13.5) * -0.1;

  const irradiance = baseIrradiance + urbanBonus + latAdjustment;

  // Clamp to realistic Bangkok range
  return Math.max(4.8, Math.min(5.3, irradiance));
}

/**
 * Estimate system size from rooftop area.
 * Assumes ~60% usable roof area and 200 Wp/m² panel density (modern panels).
 *
 * @param {number} area_m2 - Total rooftop area in m²
 * @param {object} options
 * @param {number} [options.usableRatio=0.6] - Fraction of roof usable for panels
 * @param {number} [options.panelDensityWpPerM2=200] - Panel power density
 * @returns {number} System size in kWp
 */
export function estimateSystemSize(area_m2, options = {}) {
  const { usableRatio = 0.6, panelDensityWpPerM2 = 200 } = options;
  const usableArea = area_m2 * usableRatio;
  const systemWp = usableArea * panelDensityWpPerM2;
  return systemWp / 1000; // Convert to kWp
}

/**
 * Full solar potential calculation with uncertainty range.
 * Returns { expected, min, max } for each metric.
 *
 * Key differentiators:
 * - Size-dependent cost curve → larger buildings get cheaper per-Wp → shorter payback
 * - Location-specific irradiance → different areas get different production
 * - Uncertainty ranges for all outputs
 *
 * @param {number} area_m2 - Building rooftop area in m²
 * @param {number} confidence - Detection confidence (0-1)
 * @param {number} lat - Latitude
 * @param {number} lon - Longitude
 * @param {object} options
 * @param {number} [options.usableRatio=0.6] - Fraction of roof usable for panels
 * @param {number} [options.panelDensityWpPerM2=200] - Panel power density (Wp/m²)
 * @param {number} [options.performanceRatio=0.8] - System performance ratio (losses)
 * @param {number} [options.degradationRate=0.005] - Annual panel degradation
 * @param {number} [options.electricityRate=4.5] - Electricity rate (THB/kWh)
 * @param {number} [options.irradianceUncertainty=0.15] - ±15% cloud cover variability
 * @param {number} [options.costUncertainty=0.10] - ±10% cost variability
 * @returns {object} Calculation results with expected, min, max ranges
 */
export function calculateSolarPotential(area_m2, confidence, lat, lon, options = {}) {
  const {
    usableRatio = 0.6,
    panelDensityWpPerM2 = 200,
    performanceRatio = 0.8,
    degradationRate = 0.005,
    electricityRate = 4.5,
    irradianceUncertainty = 0.15,
    costUncertainty = 0.10,
  } = options;

  // Adjust usable area by confidence (lower confidence = less certain about area)
  const confidenceAdjustedRatio = usableRatio * (0.7 + 0.3 * confidence);

  // System sizing
  const systemSizeKwp = estimateSystemSize(area_m2, {
    usableRatio: confidenceAdjustedRatio,
    panelDensityWpPerM2,
  });

  // Location-specific irradiance
  const dailyIrradiance = getLocalIrradiance(lat, lon);

  // Annual production (kWh/year)
  // Formula: SystemSize(kWp) × Irradiance(kWh/m²/day) × 365 × PerformanceRatio
  const annualProductionKwh = systemSizeKwp * dailyIrradiance * 365 * performanceRatio;

  // Size-dependent cost
  const costPerWp = getCostPerWp(systemSizeKwp);
  const totalCostTHB = systemSizeKwp * 1000 * costPerWp;

  // Annual savings
  const annualSavingsTHB = annualProductionKwh * electricityRate;

  // Simple payback (years)
  const paybackYears = annualSavingsTHB > 0 ? totalCostTHB / annualSavingsTHB : Infinity;

  // 25-year lifetime savings (accounting for degradation)
  const lifetimeSavingsTHB = calculateLifetimeSavings(
    annualSavingsTHB,
    25,
    degradationRate,
    0.03 // electricity price inflation
  );

  // ROI
  const roi25Year = totalCostTHB > 0 ? ((lifetimeSavingsTHB - totalCostTHB) / totalCostTHB) * 100 : 0;

  // CO2 offset (Thailand grid emission factor: ~0.5 kgCO2/kWh)
  const annualCO2OffsetKg = annualProductionKwh * 0.5;

  // Calculate uncertainty ranges
  const irradianceMin = dailyIrradiance * (1 - irradianceUncertainty);
  const irradianceMax = dailyIrradiance * (1 + irradianceUncertainty);
  const costMin = costPerWp * (1 - costUncertainty);
  const costMax = costPerWp * (1 + costUncertainty);

  const productionMin = systemSizeKwp * irradianceMin * 365 * performanceRatio;
  const productionMax = systemSizeKwp * irradianceMax * 365 * performanceRatio;

  const totalCostMin = systemSizeKwp * 1000 * costMin;
  const totalCostMax = systemSizeKwp * 1000 * costMax;

  const savingsMin = productionMin * electricityRate;
  const savingsMax = productionMax * electricityRate;

  // Worst case payback: highest cost / lowest savings
  const paybackMax = savingsMin > 0 ? totalCostMax / savingsMin : Infinity;
  // Best case payback: lowest cost / highest savings
  const paybackMin = savingsMax > 0 ? totalCostMin / savingsMax : Infinity;

  return {
    systemSizeKwp: {
      expected: round2(systemSizeKwp),
      min: round2(systemSizeKwp), // Size doesn't have uncertainty
      max: round2(systemSizeKwp),
    },
    dailyIrradiance: {
      expected: round2(dailyIrradiance),
      min: round2(irradianceMin),
      max: round2(irradianceMax),
    },
    annualProductionKwh: {
      expected: round0(annualProductionKwh),
      min: round0(productionMin),
      max: round0(productionMax),
    },
    costPerWp: {
      expected: round1(costPerWp),
      min: round1(costMin),
      max: round1(costMax),
    },
    totalCostTHB: {
      expected: round0(totalCostTHB),
      min: round0(totalCostMin),
      max: round0(totalCostMax),
    },
    annualSavingsTHB: {
      expected: round0(annualSavingsTHB),
      min: round0(savingsMin),
      max: round0(savingsMax),
    },
    paybackYears: {
      expected: round2(paybackYears),
      min: round2(paybackMin),
      max: round2(paybackMax),
    },
    lifetimeSavingsTHB: {
      expected: round0(lifetimeSavingsTHB),
      min: round0(lifetimeSavingsTHB * (1 - irradianceUncertainty)),
      max: round0(lifetimeSavingsTHB * (1 + irradianceUncertainty)),
    },
    roi25Year: {
      expected: round1(roi25Year),
      min: round1(roi25Year * (1 - irradianceUncertainty - costUncertainty)),
      max: round1(roi25Year * (1 + irradianceUncertainty + costUncertainty)),
    },
    annualCO2OffsetKg: {
      expected: round0(annualCO2OffsetKg),
      min: round0(annualCO2OffsetKg * (1 - irradianceUncertainty)),
      max: round0(annualCO2OffsetKg * (1 + irradianceUncertainty)),
    },
    // Metadata
    _meta: {
      area_m2,
      confidence,
      lat,
      lon,
      usableRatio: confidenceAdjustedRatio,
      buildingCategory: getBuildingCategory(systemSizeKwp),
    },
  };
}

/**
 * Calculate lifetime savings with degradation and electricity price inflation.
 */
function calculateLifetimeSavings(annualSavingsYear1, years, degradationRate, inflationRate) {
  let total = 0;
  for (let y = 0; y < years; y++) {
    const degradedProduction = 1 - degradationRate * y;
    const inflatedPrice = Math.pow(1 + inflationRate, y);
    total += annualSavingsYear1 * degradedProduction * inflatedPrice;
  }
  return total;
}

/**
 * Get building category based on system size.
 */
export function getBuildingCategory(systemSizeKwp) {
  if (systemSizeKwp < 10) return 'residential';
  if (systemSizeKwp < 50) return 'small_commercial';
  if (systemSizeKwp < 100) return 'medium_commercial';
  return 'large_ci';
}

/**
 * Get human-readable category label.
 */
export function getBuildingCategoryLabel(systemSizeKwp) {
  const cat = getBuildingCategory(systemSizeKwp);
  const labels = {
    residential: 'Residential (<10 kWp)',
    small_commercial: 'Small Commercial (10-50 kWp)',
    medium_commercial: 'Medium Commercial (50-100 kWp)',
    large_ci: 'Large C&I (>100 kWp)',
  };
  return labels[cat] || 'Unknown';
}

// Rounding helpers
function round0(n) { return Math.round(n); }
function round1(n) { return Math.round(n * 10) / 10; }
function round2(n) { return Math.round(n * 100) / 100; }

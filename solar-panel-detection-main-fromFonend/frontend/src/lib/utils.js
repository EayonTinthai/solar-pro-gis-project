import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

/**
 * Merge Tailwind classes with conflict resolution.
 * @param {...import('clsx').ClassValue} inputs
 */
export function cn(...inputs) {
  return twMerge(clsx(inputs));
}

/** Fixed palette for Recharts (also exported for any chart config). */
export const CHART_COLORS = ['#14b8a6', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6'];

/**
 * Polygon / map fill for confidence-based styling (single source of truth for hex).
 * @param {number} confidence 0–1
 * @returns {{ fill: string, stroke: string }}
 */
export function confidenceColor(confidence) {
  const c = Number(confidence);
  if (c >= 0.9) return { fill: '#22c55e', stroke: '#16a34a' };
  if (c >= 0.8) return { fill: '#3b82f6', stroke: '#2563eb' };
  if (c >= 0.7) return { fill: '#f59e0b', stroke: '#d97706' };
  return { fill: '#ef4444', stroke: '#dc2626' };
}

/**
 * Area-based gradient for map (uses CHART_COLORS endpoints).
 * @param {number} areaM2
 * @param {number} minArea
 * @param {number} maxArea
 */
export function areaBucketColor(areaM2, minArea, maxArea) {
  const span = Math.max(maxArea - minArea, 1);
  const t = (areaM2 - minArea) / span;
  const i = Math.min(4, Math.floor(Math.max(0, t) * 5));
  const hex = CHART_COLORS[i];
  return { fill: hex, stroke: hex };
}

/** Neutral slate for flat polygon mode. */
export function flatPolygonColor() {
  return { fill: '#64748b', stroke: '#475569' };
}

/**
 * @param {number} thb
 */
export function formatTHB(thb) {
  return new Intl.NumberFormat('th-TH', {
    style: 'currency',
    currency: 'THB',
    maximumFractionDigits: 0,
  }).format(thb);
}

/**
 * @param {number} kwh
 */
export function formatKwh(kwh) {
  return `${new Intl.NumberFormat('en-US', { maximumFractionDigits: 0 }).format(kwh)} kWh`;
}

/**
 * Badge variant for confidence (shadcn Badge class names).
 * @param {number} confidence 0–1
 */
export function confidenceBadgeVariant(confidence) {
  const c = Number(confidence);
  if (c >= 0.9) return 'default';
  if (c >= 0.8) return 'secondary';
  if (c >= 0.7) return 'outline';
  return 'destructive';
}

/**
 * Tailwind classes for confidence badge (centralized colors).
 * @param {number} confidence
 */
export function confidenceBadgeClassName(confidence) {
  const c = Number(confidence);
  if (c >= 0.9) return 'border-transparent bg-emerald-600 text-white hover:bg-emerald-600';
  if (c >= 0.8) return 'border-transparent bg-blue-600 text-white hover:bg-blue-600';
  if (c >= 0.7) return 'border-transparent bg-amber-500 text-black hover:bg-amber-500';
  return 'border-transparent bg-red-600 text-white hover:bg-red-600';
}

/**
 * Rough portfolio CO₂ avoidance (kg/yr) from DB-wide means — for KPI display only.
 * @param {{ total_buildings?: number, area_m2?: { average?: number }, confidence?: { average?: number } }} stats
 */
export function estimatePortfolioCo2KgYear(stats) {
  const n = stats?.total_buildings;
  const avgArea = stats?.area_m2?.average;
  const avgConf = stats?.confidence?.average;
  if (!n || avgArea == null || avgConf == null) return 0;
  const usableRoofRatio = 0.5;
  const panelEff = 0.2;
  const avgIrr = 5.06;
  const sysEff = 0.8;
  const co2Factor = 0.4;
  const confAdj = Math.max(Number(avgConf), 0.7);
  const perBuildingAnnualKwh =
    avgArea * usableRoofRatio * confAdj * panelEff * avgIrr * 365 * sysEff;
  return Math.round(n * perBuildingAnnualKwh * co2Factor);
}

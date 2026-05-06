import { useMemo, useState } from 'react';
import PropTypes from 'prop-types';
import { calculateSolarPotential, getBuildingCategoryLabel } from '@/lib/solar-calc';

/**
 * Ranking Panel - Shows top-10 buildings within the selected AOI.
 * Ranked by: production (default), payback (shortest), capacity (largest).
 */
export function RankingPanel({ buildings, onFlyTo }) {
  const [sortBy, setSortBy] = useState('production');
  const [showCount, setShowCount] = useState(10);

  // Calculate solar potential for each building and rank
  const rankedBuildings = useMemo(() => {
    if (!buildings?.length) return [];

    const withCalc = buildings
      .filter((b) => b.area_m2 > 0 && b.latitude && b.longitude)
      .map((b) => {
        const calc = calculateSolarPotential(
          b.area_m2,
          b.confidence || 0.8,
          b.latitude,
          b.longitude
        );
        return { ...b, calc };
      });

    // Sort based on selected criteria
    switch (sortBy) {
      case 'payback':
        // Shortest payback first
        return withCalc.sort(
          (a, b) => a.calc.paybackYears.expected - b.calc.paybackYears.expected
        );
      case 'capacity':
        // Largest system size first
        return withCalc.sort(
          (a, b) => b.calc.systemSizeKwp.expected - a.calc.systemSizeKwp.expected
        );
      case 'production':
      default:
        // Highest production first
        return withCalc.sort(
          (a, b) => b.calc.annualProductionKwh.expected - a.calc.annualProductionKwh.expected
        );
    }
  }, [buildings, sortBy]);

  const displayBuildings = rankedBuildings.slice(0, showCount);

  if (!buildings?.length) {
    return (
      <div className="rounded-lg border bg-card p-3 shadow-sm">
        <h3 className="mb-2 text-sm font-medium text-foreground">Building Rankings</h3>
        <p className="text-xs text-muted-foreground">
          Select an area of interest to see ranked buildings.
        </p>
      </div>
    );
  }

  return (
    <div className="rounded-lg border bg-card p-3 shadow-sm">
      <div className="mb-2 flex items-center justify-between">
        <h3 className="text-sm font-medium text-foreground">
          Top Buildings ({Math.min(showCount, rankedBuildings.length)} of {rankedBuildings.length})
        </h3>
      </div>

      {/* Sort controls */}
      <div className="mb-3 flex gap-1">
        {[
          { key: 'production', label: 'Production' },
          { key: 'payback', label: 'Payback' },
          { key: 'capacity', label: 'Capacity' },
        ].map(({ key, label }) => (
          <button
            key={key}
            onClick={() => setSortBy(key)}
            className={`rounded px-2 py-1 text-xs font-medium transition-colors ${
              sortBy === key
                ? 'bg-primary text-primary-foreground'
                : 'bg-muted text-muted-foreground hover:bg-muted/80'
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {/* Building list */}
      <div className="space-y-2 max-h-[400px] overflow-y-auto pr-1">
        {displayBuildings.map((b, idx) => (
          <RankingItem
            key={b.id || idx}
            rank={idx + 1}
            building={b}
            sortBy={sortBy}
            onFlyTo={onFlyTo}
          />
        ))}
      </div>

      {/* Show more */}
      {rankedBuildings.length > showCount && (
        <button
          onClick={() => setShowCount((c) => c + 10)}
          className="mt-2 w-full rounded bg-muted py-1 text-xs text-muted-foreground hover:bg-muted/80"
        >
          Show more...
        </button>
      )}
    </div>
  );
}

RankingPanel.propTypes = {
  buildings: PropTypes.array,
  onFlyTo: PropTypes.func,
};

function RankingItem({ rank, building, sortBy, onFlyTo }) {
  const { calc } = building;
  const category = getBuildingCategoryLabel(calc.systemSizeKwp.expected);

  return (
    <div className="rounded-md border bg-background p-2 text-xs">
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-1.5">
          <span className="flex h-5 w-5 items-center justify-center rounded-full bg-primary/10 text-[10px] font-bold text-primary">
            {rank}
          </span>
          <div>
            <p className="font-medium text-foreground">
              {building.area_m2.toFixed(0)} m² roof
            </p>
            <p className="text-muted-foreground">{category}</p>
          </div>
        </div>
        <button
          onClick={() =>
            onFlyTo?.({ lat: building.latitude, lon: building.longitude, zoom: 19 })
          }
          className="rounded bg-secondary px-1.5 py-0.5 text-[10px] font-medium text-secondary-foreground hover:bg-secondary/80"
          title="Fly to building"
        >
          Fly to
        </button>
      </div>

      {/* Metrics */}
      <div className="mt-1.5 grid grid-cols-2 gap-x-3 gap-y-0.5">
        <MetricRow
          label="System"
          value={`${calc.systemSizeKwp.expected} kWp`}
          highlight={sortBy === 'capacity'}
        />
        <MetricRow
          label="Production"
          value={`${formatNumber(calc.annualProductionKwh.expected)} kWh/yr`}
          highlight={sortBy === 'production'}
        />
        <MetricRow
          label="Payback"
          value={`${calc.paybackYears.expected} yrs`}
          subValue={`(${calc.paybackYears.min}–${calc.paybackYears.max})`}
          highlight={sortBy === 'payback'}
        />
        <MetricRow
          label="Cost/Wp"
          value={`฿${calc.costPerWp.expected}`}
        />
      </div>
    </div>
  );
}

RankingItem.propTypes = {
  rank: PropTypes.number.isRequired,
  building: PropTypes.object.isRequired,
  sortBy: PropTypes.string.isRequired,
  onFlyTo: PropTypes.func,
};

function MetricRow({ label, value, subValue, highlight }) {
  return (
    <div className={`flex justify-between ${highlight ? 'font-medium text-primary' : 'text-muted-foreground'}`}>
      <span>{label}:</span>
      <span className="text-foreground">
        {value}
        {subValue && <span className="ml-0.5 text-muted-foreground">{subValue}</span>}
      </span>
    </div>
  );
}

MetricRow.propTypes = {
  label: PropTypes.string.isRequired,
  value: PropTypes.string.isRequired,
  subValue: PropTypes.string,
  highlight: PropTypes.bool,
};

function formatNumber(n) {
  if (n >= 1000000) return `${(n / 1000000).toFixed(1)}M`;
  if (n >= 1000) return `${(n / 1000).toFixed(1)}k`;
  return String(Math.round(n));
}

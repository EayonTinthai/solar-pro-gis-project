import { useMemo } from 'react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Slider } from '@/components/ui/slider';
import { cn } from '@/lib/utils';

function Chip({ children }) {
  return (
    <Badge variant="secondary" className="text-[11px] tabular-nums">
      {children}
    </Badge>
  );
}

function Section({ title, children, right }) {
  return (
    <section className="space-y-2">
      <div className="flex items-end justify-between gap-3">
        <h3 className="text-xs font-medium text-foreground/80">{title}</h3>
        {right}
      </div>
      {children}
    </section>
  );
}

function confidenceTier(v) {
  if (v >= 0.9) return 'High';
  if (v >= 0.8) return 'Med';
  return 'Low';
}

/**
 * Panel-native filters UI (no popover).
 * Keeps existing draft/apply semantics; no data logic changes.
 *
 * @param {{
 *   minConfidence: number,
 *   onMinConfidenceChange: (v: number) => void,
 *   minArea: string,
 *   maxArea: string,
 *   onMinAreaChange: (v: string) => void,
 *   onMaxAreaChange: (v: string) => void,
 *   limit: number,
 *   onLimitChange: (v: number) => void,
 *   onApply: () => void,
 *   activeFilterCount: number,
 *   defaultConfidence: number,
 *   defaultLimit: number,
 *   onClearDraft: () => void,
 *   buildings?: Array<Record<string, unknown>>,
 * }} props
 */
export function FiltersPanel({
  minConfidence,
  onMinConfidenceChange,
  minArea,
  maxArea,
  onMinAreaChange,
  onMaxAreaChange,
  limit,
  onLimitChange,
  onApply,
  activeFilterCount,
  defaultConfidence,
  defaultLimit,
  onClearDraft,
  buildings,
}) {
  const minA = minArea === '' ? null : Number(minArea);
  const maxA = maxArea === '' ? null : Number(maxArea);
  const areaInvalid =
    minA != null &&
    maxA != null &&
    !Number.isNaN(minA) &&
    !Number.isNaN(maxA) &&
    minA > maxA;

  const areaRange = useMemo(() => {
    if (!buildings?.length) return null;
    const areas = buildings.map((b) => Number(b.area_m2)).filter((a) => Number.isFinite(a) && a > 0);
    if (!areas.length) return null;
    const min = Math.min(...areas);
    const max = Math.max(...areas);
    return { min: Math.round(min), max: Math.round(max) };
  }, [buildings]);

  const chips = useMemo(() => {
    const out = [];
    if (minConfidence !== defaultConfidence) out.push(`MinConf ≥ ${minConfidence.toFixed(2)}`);
    if (limit !== defaultLimit) out.push(`Limit ${limit}`);
    if (minArea !== '' || maxArea !== '') {
      const a = `${minArea === '' ? '—' : minArea}–${maxArea === '' ? '—' : maxArea} m²`;
      out.push(`Area ${a}`);
    }
    return out;
  }, [defaultConfidence, defaultLimit, limit, maxArea, minArea, minConfidence]);

  return (
    <div className="space-y-3">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <h2 className="text-sm font-semibold leading-tight">Filters</h2>
          <p className="text-xs text-muted-foreground leading-tight">
            {activeFilterCount > 0 ? `${activeFilterCount} active` : 'No active filters'}
          </p>
        </div>
        <Button
          type="button"
          variant="ghost"
          size="sm"
          className="h-8 px-2 text-xs"
          onClick={onClearDraft}
          disabled={activeFilterCount === 0 && minArea === '' && maxArea === '' && minConfidence === defaultConfidence && limit === defaultLimit}
        >
          Clear
        </Button>
      </div>

      {chips.length ? (
        <div className="flex flex-wrap gap-1.5">
          {chips.map((c) => (
            <Chip key={c}>{c}</Chip>
          ))}
        </div>
      ) : null}

      <div className="rounded-lg border border-border/40 shadow-none bg-background/60 p-3 space-y-4">
        <Section
          title="Confidence"
          right={
            <div className="flex items-center gap-2">
              <Chip>{confidenceTier(minConfidence)}</Chip>
              <span className="tabular-nums text-xs text-muted-foreground">{minConfidence.toFixed(2)}</span>
            </div>
          }
        >
          <Slider
            value={[minConfidence]}
            min={0.5}
            max={1}
            step={0.01}
            onValueChange={(v) => onMinConfidenceChange(v[0])}
          />
        </Section>

        <Section title="Area (m²)">
          <div className="grid grid-cols-2 gap-2">
            <div className="space-y-1">
              <Label className="text-[11px] text-muted-foreground">Min</Label>
              <Input
                type="number"
                min={0}
                placeholder="Any"
                value={minArea}
                onChange={(e) => onMinAreaChange(e.target.value)}
                className={cn(areaInvalid && 'border-destructive/50 focus-visible:ring-destructive/30')}
              />
            </div>
            <div className="space-y-1">
              <Label className="text-[11px] text-muted-foreground">Max</Label>
              <Input
                type="number"
                min={0}
                placeholder="Any"
                value={maxArea}
                onChange={(e) => onMaxAreaChange(e.target.value)}
                className={cn(areaInvalid && 'border-destructive/50 focus-visible:ring-destructive/30')}
              />
            </div>
          </div>
          {areaInvalid ? (
            <p className="text-xs text-destructive">Min area must be ≤ max area.</p>
          ) : null}
          {areaRange ? (
            <p className="text-[11px] text-muted-foreground">
              Loaded buildings range: {areaRange.min.toLocaleString()}–{areaRange.max.toLocaleString()} m²
            </p>
          ) : null}
        </Section>

        <Section title="Result limit">
          <Select value={String(limit)} onValueChange={(v) => onLimitChange(Number(v))}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="100">100</SelectItem>
              <SelectItem value="500">500</SelectItem>
              <SelectItem value="1000">1000</SelectItem>
              <SelectItem value="5000">5000</SelectItem>
            </SelectContent>
          </Select>
        </Section>
      </div>

      <div className="sticky bottom-0 pt-1">
        <div className="grid grid-cols-2 gap-2">
          <Button type="button" variant="outline" className="w-full" onClick={onClearDraft}>
            Reset
          </Button>
          <Button type="button" className="w-full" onClick={onApply} disabled={areaInvalid}>
            Apply
          </Button>
        </div>
      </div>
    </div>
  );
}


import { ChevronDown } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';
import { Progress } from '@/components/ui/progress';
import { formatKwh, formatTHB } from '@/lib/utils';

const PAYBACK_REF = 25;

/**
 * @param {{ result: Record<string, unknown> | undefined }} props
 */
export function SolarResultCard({ result }) {
  if (!result) return null;

  const payback = result.payback_period_years;
  const paybackPct =
    payback != null ? Math.min(100, (Number(payback) / PAYBACK_REF) * 100) : 0;

  const assumptions = result.assumptions || {};

  return (
    <Card className="mt-4">
      <CardHeader>
        <CardTitle className="text-base">Results</CardTitle>
        <CardDescription>pvlib / simplified backend output</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid gap-3 sm:grid-cols-2">
          <div>
            <p className="text-xs font-medium text-muted-foreground">System size</p>
            <p className="text-xl font-bold tabular-nums">{result.system_size_kwp} kWp</p>
          </div>
          <div>
            <p className="text-xs font-medium text-muted-foreground">Annual production</p>
            <p className="text-xl font-bold tabular-nums">{formatKwh(result.annual_production_kwh)}</p>
          </div>
          <div>
            <p className="text-xs font-medium text-muted-foreground">Installation cost</p>
            <p className="text-xl font-bold tabular-nums">{formatTHB(result.installation_cost_thb)}</p>
          </div>
          <div>
            <p className="text-xs font-medium text-muted-foreground">Annual savings</p>
            <p className="text-xl font-bold tabular-nums">{formatTHB(result.annual_savings_thb)}</p>
          </div>
        </div>
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">Payback</span>
            <span className="tabular-nums">
              {payback != null ? `${Number(payback).toFixed(1)}` : '—'} of {PAYBACK_REF} yrs (ref.)
            </span>
          </div>
          <Progress value={paybackPct} className="h-2" />
        </div>
        <div className="flex flex-wrap gap-2">
          <Badge variant="secondary">{result.irradiance_source}</Badge>
          <Badge variant="outline" className="tabular-nums">
            {result.irradiance_kwh_m2_day} kWh/m²/day
          </Badge>
        </div>
        <Collapsible>
          <CollapsibleTrigger className="flex w-full items-center justify-between rounded-lg border px-3 py-2 text-sm font-medium hover:bg-muted">
            Assumptions
            <ChevronDown className="h-4 w-4" />
          </CollapsibleTrigger>
          <CollapsibleContent className="mt-2 space-y-1 rounded-lg bg-muted/50 p-3 text-xs font-mono">
            <p>panel_efficiency: {String(assumptions.panel_efficiency)}</p>
            <p>usable_roof_ratio: {String(assumptions.usable_roof_ratio)}</p>
            <p>cost_per_wp: {String(assumptions.cost_per_wp)}</p>
            <p>electricity_rate: {String(assumptions.electricity_rate)}</p>
            <p>co2_factor: {String(assumptions.co2_factor)}</p>
            <p>calculation_method: {String(assumptions.calculation_method)}</p>
          </CollapsibleContent>
        </Collapsible>
      </CardContent>
    </Card>
  );
}

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { confidenceColor } from '@/lib/utils';

const STEPS = [
  { label: '≥ 0.90', min: 0.9 },
  { label: '0.80 – 0.90', min: 0.8 },
  { label: '0.70 – 0.80', min: 0.7 },
  { label: '< 0.70', min: 0 },
];

export function MapLegend() {
  return (
    <Card className="pointer-events-none w-44 border bg-background/95 shadow-md backdrop-blur-sm">
      <CardHeader className="p-3 pb-1">
        <CardTitle className="text-xs font-medium text-muted-foreground">Confidence</CardTitle>
      </CardHeader>
      <CardContent className="space-y-1.5 p-3 pt-0">
        {STEPS.map(({ label, min }) => {
          const { fill } = confidenceColor(min === 0 ? 0.65 : min + 0.01);
          return (
            <div key={label} className="flex items-center gap-2 text-xs">
              <span
                className="h-3 w-3 shrink-0 rounded-sm border border-white/20"
                style={{ backgroundColor: fill }}
              />
              <span className="text-muted-foreground">{label}</span>
            </div>
          );
        })}
      </CardContent>
    </Card>
  );
}

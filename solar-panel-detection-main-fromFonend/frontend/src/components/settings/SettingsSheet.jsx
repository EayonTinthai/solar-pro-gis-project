import { useTheme } from 'next-themes';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import { Slider } from '@/components/ui/slider';
import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Separator } from '@/components/ui/separator';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from '@/components/ui/sheet';
import { useMapSettings } from '@/contexts/MapSettingsContext';
import { useAuth } from '@/hooks/useAuth';
import { useUpgrade } from '@/contexts/UpgradeContext';

/**
 * @param {{ open: boolean, onOpenChange: (v: boolean) => void }} props
 */
export function SettingsSheet({ open, onOpenChange }) {
  const { theme, setTheme } = useTheme();
  const { isPro } = useAuth();
  const { openUpgrade } = useUpgrade();
  const {
    basemap,
    setBasemap,
    polygonColorMode,
    setPolygonColorMode,
    defaultConfidence,
    setDefaultConfidence,
    defaultLimit,
    setDefaultLimit,
  } = useMapSettings();

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="flex w-full flex-col p-0 sm:max-w-md">
        <SheetHeader className="border-b px-6 py-4 text-left">
          <SheetTitle>Customization</SheetTitle>
          <SheetDescription>Theme, map defaults, and polygon styling.</SheetDescription>
        </SheetHeader>
        <ScrollArea className="flex-1 px-6 py-4">
          <div className="space-y-6">
            <section className="space-y-3">
              <h3 className="text-sm font-medium text-muted-foreground">Theme</h3>
              <div className="flex flex-wrap gap-2">
                <Button
                  type="button"
                  variant={theme === 'light' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setTheme('light')}
                >
                  Light
                </Button>
                <Button
                  type="button"
                  variant={theme === 'dark' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setTheme('dark')}
                >
                  Dark
                </Button>
                <Button
                  type="button"
                  variant={theme === 'system' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setTheme('system')}
                >
                  System
                </Button>
              </div>
            </section>

            <Separator />

            <section className="space-y-3">
              <Label className="text-sm font-medium text-muted-foreground">Map basemap</Label>
              <Select value={basemap} onValueChange={setBasemap}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="esri">Esri World Imagery</SelectItem>
                  <SelectItem value="osm">OpenStreetMap</SelectItem>
                  <SelectItem value="carto">CartoDB Dark</SelectItem>
                </SelectContent>
              </Select>
            </section>

            <section className="space-y-3">
              <div className="flex items-center justify-between gap-4">
                <Label className="text-sm font-medium text-muted-foreground">
                  Default confidence threshold
                </Label>
                <span className="tabular-nums text-sm text-muted-foreground">
                  {defaultConfidence.toFixed(2)}
                </span>
              </div>
              <Slider
                value={[defaultConfidence]}
                min={0.5}
                max={1}
                step={0.01}
                onValueChange={(v) => setDefaultConfidence(v[0])}
              />
            </section>

            <section className="space-y-3">
              <Label className="text-sm font-medium text-muted-foreground">Default result limit</Label>
              <Select
                value={String(defaultLimit)}
                onValueChange={(v) => setDefaultLimit(Number(v))}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="100">100</SelectItem>
                  <SelectItem value="500">500</SelectItem>
                  <SelectItem value="1000">1000</SelectItem>
                </SelectContent>
              </Select>
            </section>

            <section className="space-y-3">
              <Label className="text-sm font-medium text-muted-foreground">Units</Label>
              <div className="flex items-center justify-between rounded-lg border px-3 py-2">
                <span className="text-sm">Metric (m², kWh, kg)</span>
                <Switch checked disabled aria-readonly />
              </div>
              <p className="text-xs text-muted-foreground">Imperial units may be added later.</p>
            </section>

            <Separator />

            <section className="space-y-3">
              <Label className="text-sm font-medium text-muted-foreground">Polygon colors</Label>
              <Select value={polygonColorMode} onValueChange={setPolygonColorMode}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="confidence">Confidence-based</SelectItem>
                  <SelectItem value="area">Area-based</SelectItem>
                  <SelectItem value="flat">Flat color</SelectItem>
                </SelectContent>
              </Select>
            </section>

            <Separator />

            <section className="space-y-3">
              <h3 className="text-sm font-medium text-muted-foreground">Subscription</h3>
              <div className="flex items-center justify-between rounded-lg border px-3 py-2">
                <div className="space-y-0.5">
                  <p className="text-sm">Plan</p>
                  <p className="text-xs text-muted-foreground">{isPro ? 'Pro' : 'Free'}</p>
                </div>
                {isPro ? (
                  <Badge variant="secondary" className="text-xs">
                    Pro ✓
                  </Badge>
                ) : null}
              </div>

              {isPro ? (
                <div className="space-y-2">
                  <Button type="button" variant="outline" size="sm" disabled>
                    Manage billing →
                  </Button>
                  <p className="text-xs text-muted-foreground">
                    Billing management requires a customer portal session. Check your Stripe email receipt for a “Manage subscription” link.
                  </p>
                </div>
              ) : (
                <Button type="button" size="sm" onClick={openUpgrade}>
                  Upgrade to Pro →
                </Button>
              )}
            </section>
          </div>
        </ScrollArea>
      </SheetContent>
    </Sheet>
  );
}

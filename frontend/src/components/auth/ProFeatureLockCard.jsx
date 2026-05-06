import { Lock } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { cn } from '@/lib/utils';

/**
 * Upgrade CTA used inside AuthGate overlays.
 *
 * @param {{
 *   title: string,
 *   subtitle: string,
 *   onUpgrade: (e?: import('react').MouseEvent) => void,
 *   onRequestDemo?: (e?: import('react').MouseEvent) => void,
 *   className?: string,
 * }} props
 */
export function ProFeatureLockCard({ title, subtitle, onUpgrade, onRequestDemo, className }) {
  return (
    <Card className={cn('w-[min(420px,calc(100%-2rem))] shadow-md', className)}>
      <CardHeader className="space-y-1">
        <div className="flex items-center gap-2">
          <Lock className="h-6 w-6 text-muted-foreground" aria-hidden />
          <CardTitle className="text-base">{title}</CardTitle>
        </div>
        <CardDescription>{subtitle}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="grid gap-2 sm:grid-rows-2">
          <Button
            type="button"
            className="w-full"
            onClick={(e) => {
              e.stopPropagation();
              onUpgrade(e);
            }}
          >
            Upgrade to Pro
          </Button>
          {onRequestDemo ? (
            <Button
              type="button"
              variant="outline"
              className="w-full"
              onClick={(e) => {
                e.stopPropagation();
                onRequestDemo(e);
              }}
            >
              Request Demo
            </Button>
          ) : null}
        </div>
      </CardContent>
    </Card>
  );
}

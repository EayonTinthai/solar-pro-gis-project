import { useState } from 'react';
import { Loader2 } from 'lucide-react';
import { toast } from 'sonner';
import { useAuth } from '@/hooks/useAuth';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';

/**
 * @param {{ open: boolean, onOpenChange: (v: boolean) => void }} props
 */
export function UpgradeModal({ open, onOpenChange }) {
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);
  const priceDisplay = import.meta.env.VITE_STRIPE_PRO_PRICE_DISPLAY || 'Pro subscription';
  const paymentLinkUrl = import.meta.env.VITE_STRIPE_PAYMENT_LINK_URL;

  const onUpgrade = async () => {
    if (!user?.id) return;
    if (!paymentLinkUrl) {
      toast.error('Missing Stripe Payment Link URL.');
      return;
    }
    try {
      setLoading(true);
      window.location.href = paymentLinkUrl;
    } catch {
      toast.error("Couldn't open Stripe checkout. Try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <span><svg class="w-auto h-10" xmlns="http://www.w3.org/2000/svg" version="1.0" width="308.000000pt" height="218.000000pt" viewBox="0 0 308.000000 218.000000" preserveAspectRatio="xMidYMid meet"><g transform="translate(0.000000,218.000000) scale(0.100000,-0.100000)" fill="currentColor" stroke="none"><path d="M1793 2035 c21 -52 19 -64 -7 -71 -27 -6 -30 -12 -21 -36 4 -9 17 -13 39 -10 31 4 35 1 41 -27 6 -29 21 -48 31 -39 2 3 -2 21 -10 40 -16 38 -13 48 16 48 13 0 18 7 18 25 0 24 -3 25 -33 20 -31 -6 -34 -4 -43 26 -5 18 -16 35 -23 37 -10 3 -12 0 -8 -13z"></path><path d="M1450 1851 c-299 -98 -577 -340 -646 -564 l-18 -58 55 -55 54 -54 54 54 c34 34 51 59 47 68 -4 7 -13 24 -21 38 -19 33 -19 111 0 157 60 143 299 328 540 419 85 32 37 29 -65 -5z"></path><path d="M240 845 l0 -245 50 0 50 0 0 95 0 95 73 0 c46 0 80 -5 92 -14 11 -7 45 -50 75 -95 l55 -81 53 0 c45 0 53 3 48 16 -11 29 -97 143 -126 168 l-30 25 33 10 c83 28 122 128 77 199 -37 60 -81 72 -277 72 l-173 0 0 -245z m345 140 c14 -13 25 -33 25 -45 0 -11 -11 -32 -25 -45 -23 -24 -31 -25 -135 -25 l-110 0 0 70 0 70 110 0 c104 0 112 -1 135 -25z"></path><path d="M842 848 l3 -243 50 0 50 0 3 243 2 242 -55 0 -55 0 2 -242z"></path><path d="M1092 848 l3 -243 50 0 50 0 3 103 3 102 140 0 140 0 -3 38 -3 37 -137 3 -138 3 0 59 0 60 145 0 145 0 0 40 0 40 -200 0 -200 0 2 -242z"></path><path d="M1592 848 l3 -243 48 -3 47 -3 1 90 c1 50 2 97 3 104 1 9 37 13 139 15 l137 3 0 39 0 39 -137 3 -138 3 0 55 0 55 148 3 147 3 0 39 0 40 -200 0 -200 0 2 -242z"></path><path d="M2163 850 c-73 -131 -133 -242 -133 -245 0 -3 22 -5 49 -5 49 0 49 0 80 55 l31 55 154 0 154 0 28 -55 c29 -55 29 -55 77 -55 26 0 47 5 47 11 0 9 -215 406 -248 457 -11 18 -24 22 -61 22 l-46 0 -132 -240z m236 45 c28 -53 51 -98 51 -100 0 -3 -50 -5 -110 -5 l-110 0 52 100 c29 55 56 100 60 100 3 0 29 -43 57 -95z"></path><path d="M2742 848 l3 -243 50 0 50 0 3 243 2 242 -55 0 -55 0 2 -242z"></path></g></svg> Solar Panel Detection Pro</span>
            <Badge variant="secondary" className="text-xs">
              Pro
            </Badge>
          </DialogTitle>
          <DialogDescription>Everything in Free, plus:</DialogDescription>
        </DialogHeader>

        <div className="space-y-3">
          <ul className="space-y-2 text-sm">
            <li>✓ Solar potential calculator</li>
            <li>✓ pvlib-powered irradiance data</li>
            <li>✓ ROI, payback period &amp; CO₂ metrics</li>
            <li>✓ Export unlimited reports</li>
          </ul>

          <div className="rounded-lg border bg-card p-3 text-sm">
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">Price</span>
              <span className="font-medium">{priceDisplay}</span>
            </div>
          </div>
        </div>

        <DialogFooter className="gap-2 sm:gap-0">
          <Button
            type="button"
            variant="outline"
            onClick={() => onOpenChange(false)}
            disabled={loading}
          >
            Maybe later
          </Button>
          <Button type="button" onClick={onUpgrade} disabled={loading}>
            {loading ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Starting checkout…
              </>
            ) : (
              'Upgrade Now →'
            )}
          </Button>
        </DialogFooter>

        <div className="space-y-1 text-center text-xs text-muted-foreground sm:text-left">
          <p>Secure payment via Stripe</p>
          <p>Cancel anytime from your account</p>
        </div>
      </DialogContent>
    </Dialog>
  );
}


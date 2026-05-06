import { useEffect, useState } from 'react';
import { Loader2, Mail } from 'lucide-react';
import { toast } from 'sonner';
import { useAuth } from '@/hooks/useAuth';
import { useDemoLifecycle } from '@/contexts/DemoLifecycleContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';

function formatDate(iso) {
  if (!iso) return null;
  const parsed = Date.parse(iso);
  if (!Number.isFinite(parsed)) return null;
  return new Date(parsed).toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

/**
 * @param {{ open: boolean, onOpenChange: (v: boolean) => void, source?: string }} props
 */
export function DemoRequestModal({ open, onOpenChange, source = 'Locked Pro feature' }) {
  const { isSignedIn, user } = useAuth();
  const { requestDemoAccess } = useDemoLifecycle();
  const [loading, setLoading] = useState(false);
  const [company, setCompany] = useState('');
  const [note, setNote] = useState('');

  const userEmail = user?.primaryEmailAddress?.emailAddress?.trim() || 'Not available';

  useEffect(() => {
    if (!open) return;
    setCompany('');
    setNote('');
  }, [open]);

  const onSubmit = async () => {
    const trimmedCompany = company.trim();
    if (isSignedIn && !trimmedCompany) {
      toast.error('Company is required to request demo access.');
      return;
    }

    try {
      setLoading(true);
      const result = await requestDemoAccess({
        source,
        company: trimmedCompany,
        note,
      });

      if (result.code === 'signin_required') {
        toast.message('Sign in to request demo access.');
        onOpenChange(false);
        return;
      }
      if (!result.ok) {
        toast.error('Could not submit your demo request. Please try again.');
        return;
      }

      if (result.code === 'already_pending') {
        toast.message('Your demo request is already pending review.');
        onOpenChange(false);
        return;
      }

      if (result.code === 'already_granted') {
        const label = formatDate(result.expiresAt);
        if (label) {
          toast.success(`Demo access is already active until ${label}.`);
        } else {
          toast.success('Demo access is already active.');
        }
        onOpenChange(false);
        return;
      }

      toast.success('Demo request submitted. Your account is now marked as pending.');
      if (Array.isArray(result.webhookFailures) && result.webhookFailures.length) {
        toast.message('Request saved, but some email notifications are delayed and will retry.');
      }
      onOpenChange(false);
    } catch {
      toast.error('Could not submit your demo request. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Mail className="h-5 w-5 text-muted-foreground" aria-hidden />
            Request Demo Access
          </DialogTitle>
          <DialogDescription>
            Tell us where you are evaluating the product and we will follow up with demo access support.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-3">
          <div className="space-y-1.5">
            <Label htmlFor="demo-account-email">Account email</Label>
            <Input id="demo-account-email" type="text" value={userEmail} disabled />
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="demo-company">Company</Label>
            <Input
              id="demo-company"
              type="text"
              autoComplete="organization"
              placeholder="Your company"
              value={company}
              onChange={(e) => setCompany(e.target.value)}
            />
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="demo-note">What are you trying to evaluate? (optional)</Label>
            <textarea
              id="demo-note"
              className="flex min-h-[96px] w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
              placeholder="Example: rooftop suitability and export reporting for our pilot area"
              value={note}
              onChange={(e) => setNote(e.target.value)}
            />
          </div>

          <p className="text-xs text-muted-foreground">
            {isSignedIn
              ? 'Request status is tied to your signed-in account and updates automatically.'
              : 'Sign in first so we can attach this request to your account.'}
          </p>
        </div>

        <DialogFooter className="gap-2 sm:gap-0">
          <Button type="button" variant="outline" onClick={() => onOpenChange(false)} disabled={loading}>
            Cancel
          </Button>
          <Button type="button" onClick={onSubmit} disabled={loading || (isSignedIn && !company.trim())}>
            {loading ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Submitting...
              </>
            ) : (
              isSignedIn ? 'Request Demo' : 'Sign In to Request'
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

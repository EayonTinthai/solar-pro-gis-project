import { X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { useDemoLifecycle } from '@/contexts/DemoLifecycleContext';

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

export function LifecycleNoticeBanner() {
  const { activeNotice, dismissNotice } = useDemoLifecycle();

  if (!activeNotice) return null;

  const isGranted = activeNotice.type === 'granted';
  const grantedLabel = formatDate(activeNotice.expiresAt);
  const expiredLabel = formatDate(activeNotice.expiredAt);

  return (
    <div
      className={cn(
        'pointer-events-auto rounded-lg border px-3 py-2 shadow-sm',
        isGranted
          ? 'border-emerald-300/70 bg-emerald-100/85 text-emerald-950 dark:border-emerald-700/70 dark:bg-emerald-950/40 dark:text-emerald-100'
          : 'border-amber-300/70 bg-amber-100/85 text-amber-950 dark:border-amber-700/70 dark:bg-amber-950/40 dark:text-amber-100'
      )}
      role="status"
      aria-live="polite"
    >
      <div className="flex items-start gap-2">
        <p className="flex-1 text-sm">
          {isGranted
            ? grantedLabel
              ? `Demo access granted. Pro features are active until ${grantedLabel}.`
              : 'Demo access granted. Pro features are now active.'
            : expiredLabel
              ? `Demo access expired on ${expiredLabel}. You are now back on the Free plan.`
              : 'Demo access expired. You are now back on the Free plan.'}
        </p>
        <Button
          type="button"
          size="icon"
          variant="ghost"
          className="h-7 w-7"
          onClick={() => dismissNotice(activeNotice.type)}
          aria-label="Dismiss notice"
        >
          <X className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}

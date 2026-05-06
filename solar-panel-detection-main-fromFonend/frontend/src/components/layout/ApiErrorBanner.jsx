import { AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';

/**
 * Inline banner when API is unreachable.
 * @param {{ message?: string, onRetry?: () => void }} props
 */
export function ApiErrorBanner({ message = 'Unable to reach the buildings API.', onRetry }) {
  return (
    <div
      role="alert"
      className="flex items-center justify-between gap-3 border-b border-destructive/40 bg-destructive/10 px-4 py-2 text-sm text-destructive"
    >
      <div className="flex items-center gap-2">
        <AlertCircle className="h-4 w-4 shrink-0" aria-hidden />
        <span>{message}</span>
      </div>
      {onRetry ? (
        <Button type="button" variant="outline" size="sm" onClick={onRetry} className="shrink-0">
          Retry
        </Button>
      ) : null}
    </div>
  );
}

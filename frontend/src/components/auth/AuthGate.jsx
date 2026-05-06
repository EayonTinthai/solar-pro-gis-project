import { ProFeatureLockCard } from '@/components/auth/ProFeatureLockCard';
import { cn } from '@/lib/utils';
import { useAuth } from '@/hooks/useAuth';
import { useUpgrade } from '@/contexts/UpgradeContext';
import { useDemoRequest } from '@/contexts/DemoRequestContext';

const DEFAULT_TITLE = 'This feature requires Pro';
const DEFAULT_SUBTITLE = 'Upgrade to unlock full access to buildings, analytics, and solar tools.';

/**
 * Pro-only gate (sign-in is enforced at the app root).
 *
 * @param {{
 *   children: import('react').ReactNode,
 *   title?: string,
 *   subtitle?: string,
 *   className?: string,
 *   fallback?: import('react').ReactNode,
 *   onRequestUpgrade?: () => void,
 *   onRequestDemo?: () => void,
 * }} props
 */
export function AuthGate({
  children,
  title = DEFAULT_TITLE,
  subtitle = DEFAULT_SUBTITLE,
  className,
  fallback,
  onRequestUpgrade,
  onRequestDemo,
}) {
  const { isLoaded, hasFeatureAccess } = useAuth();
  const { openUpgrade } = useUpgrade();
  const { openDemoRequest } = useDemoRequest();

  const locked = isLoaded ? !hasFeatureAccess : true;

  if (!locked) return children;

  if (fallback) {
    return (
      <div className={cn('relative', className)}>
        <div className="pointer-events-none select-none opacity-50">{children}</div>
        {fallback}
      </div>
    );
  }

  const primaryAction = () => {
    (onRequestUpgrade || openUpgrade)?.();
  };

  const secondaryAction = () => {
    if (onRequestDemo) {
      onRequestDemo();
      return;
    }
    openDemoRequest({ source: title });
  };

  return (
    <div className={cn('relative', className)}>
      <div className="pointer-events-none select-none opacity-50">{children}</div>

      <div className="absolute inset-0 z-[1]">
        <button
          type="button"
          className="absolute inset-0 z-0 cursor-pointer backdrop-blur-[2px]"
          aria-label="Upgrade to Pro to use this feature"
          onClick={primaryAction}
        />
        <div className="relative z-10 flex h-full w-full items-center justify-center p-2">
          <div className="flex justify-center items-center max-w-full cursor-pointer" onClick={primaryAction}>
            <ProFeatureLockCard
              title={title}
              subtitle={subtitle}
              onUpgrade={primaryAction}
              onRequestDemo={secondaryAction}
            />
          </div>
        </div>
      </div>
    </div>
  );
}

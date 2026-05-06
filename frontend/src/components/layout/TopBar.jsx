import { useEffect, useMemo, useState } from 'react';
import { Search, Settings, Sun, Moon, Laptop } from 'lucide-react';
import { useTheme } from 'next-themes';
import { Show, SignInButton, UserButton } from '@clerk/react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { useAuth } from '@/hooks/useAuth';
import { useUpgrade } from '@/contexts/UpgradeContext';
/**
 * @param {{
 *   title: string,
 *   onOpenCommand: () => void,
 *   onOpenSettings: () => void,
 * }} props
 */
export function TopBar({ title, onOpenCommand, onOpenSettings }) {
  const { setTheme } = useTheme();
  const { isPro, accountType, isFrontendTrialActive, demoAccessStatus, trialExpiresAt } = useAuth();
  const { openUpgrade } = useUpgrade();
  const [nowMs, setNowMs] = useState(() => Date.now());

  useEffect(() => {
    if (!isFrontendTrialActive) return;
    setNowMs(Date.now());
    const id = window.setInterval(() => setNowMs(Date.now()), 60 * 1000);
    return () => window.clearInterval(id);
  }, [isFrontendTrialActive]);

  const trialDaysLeft = useMemo(() => {
    if (!isFrontendTrialActive || !trialExpiresAt) return null;
    const expiresMs = Date.parse(trialExpiresAt);
    if (!Number.isFinite(expiresMs)) return null;
    const remainingMs = Math.max(0, expiresMs - nowMs);
    return Math.ceil(remainingMs / (24 * 60 * 60 * 1000));
  }, [isFrontendTrialActive, nowMs, trialExpiresAt]);

  return (
    <header
      className="glass-panel pointer-events-auto relative"
      style={{
        position: 'absolute',
        top: '12px',
        left: '12px',
        right: '12px',
        height: '48px',
        display: 'flex',
        alignItems: 'center',
        padding: '0 12px',
        gap: '8px',
        zIndex: 20,
      }}
    >
      <div className="flex min-w-0 items-center gap-2">
      {/* <div className="pointer-events-none absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2"> */}
        <span className="h-8 flex items-center text-foreground font-bold text-lg tracking-tight">
          Solar Pro
        </span>
      </div>

      <div className="flex min-w-0 items-center gap-2">
        {/* title placeholder */}
      </div>
      <div className="flex-1" />

      <Button
        type="button"
        variant="outline"
        size="sm"
        className="hidden h-8 gap-2 text-muted-foreground md:inline-flex"
        data-tour="search-trigger"
        onClick={onOpenCommand}
      >
        <Search className="h-4 w-4" />
        <span className="text-xs">Search</span>
        <kbd className="pointer-events-none hidden rounded border bg-muted px-1.5 py-0.5 font-mono text-[10px] font-medium sm:inline-block">
          ⌘K
        </kbd>
      </Button>
      <Button
        type="button"
        variant="ghost"
        size="icon"
        className="h-8 w-8 md:hidden"
        data-tour="search-trigger"
        onClick={onOpenCommand}
        aria-label="Open command palette"
      >
        <Search className="h-4 w-4" />
      </Button>

      <div className="flex-1" />

      <div className="flex shrink-0 items-center gap-1">
        <Button
          type="button"
          variant="ghost"
          size="icon"
          className="h-8 w-8"
          onClick={onOpenSettings}
          aria-label="Settings"
        >
          <Settings className="h-4 w-4" />
        </Button>

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              type="button"
              variant="ghost"
              size="icon"
              className="relative h-8 w-8"
              aria-label="Theme menu"
            >
              <Sun className="h-4 w-4 dark:hidden" />
              <Moon className="hidden h-4 w-4 dark:inline" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem onClick={() => setTheme('light')}>
              <Sun className="mr-2 h-4 w-4" />
              Light
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => setTheme('dark')}>
              <Moon className="mr-2 h-4 w-4" />
              Dark
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => setTheme('system')}>
              <Laptop className="mr-2 h-4 w-4" />
              System
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>

        <div className="mx-1 hidden h-5 w-px bg-border/60 sm:block" />

        <div className="flex items-center gap-2">
          <Show when="signed-out">
            <SignInButton mode="modal">
              <Button type="button" variant="outline" size="sm" className="h-8">
                Sign in
              </Button>
            </SignInButton>
          </Show>
          <Show when="signed-in">
            <div className="flex items-center gap-2">
              {accountType === 'free' ? (
                <Button
                  variant="outline"
                  size="sm"
                  className="hidden h-8 sm:inline-flex"
                  onClick={openUpgrade}
                >
                  Upgrade to Pro
                </Button>
              ) : null}
              {isFrontendTrialActive ? (
                <Button
                  variant="outline"
                  size="sm"
                  className="hidden h-8 sm:inline-flex"
                  onClick={openUpgrade}
                >
                  Upgrade Before Trial Ends
                </Button>
              ) : null}
              {isPro ? (
                <Badge variant="secondary" className="hidden text-xs sm:inline-flex">
                  Pro
                </Badge>
              ) : null}
              {accountType === 'demo' ? (
                <Badge variant="outline" className="hidden text-xs sm:inline-flex">
                  Demo
                </Badge>
              ) : null}
              {isFrontendTrialActive ? (
                <Badge variant="outline" className="hidden text-xs sm:inline-flex">
                  {trialDaysLeft != null ? `Trial ${trialDaysLeft}d left` : 'Trial'}
                </Badge>
              ) : null}
              {demoAccessStatus === 'pending' ? (
                <Badge variant="outline" className="text-xs">
                  Pending
                </Badge>
              ) : null}
              <UserButton afterSignOutUrl={window.location.href} />
            </div>
          </Show>
        </div>
      </div>
    </header>
  );
}

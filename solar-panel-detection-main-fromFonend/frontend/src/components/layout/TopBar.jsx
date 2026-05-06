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

// Check if Clerk is available
const hasClerk = Boolean(import.meta.env.VITE_CLERK_PUBLISHABLE_KEY);

/**
 * @param {{
 *   title: string,
 *   onOpenCommand: () => void,
 *   onOpenSettings: () => void,
 * }} props
 */
export function TopBar({ title, onOpenCommand, onOpenSettings }) {
  const { setTheme } = useTheme();
  const { isPro, isSignedIn } = useAuth();
  const { openUpgrade } = useUpgrade();

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
        <svg
          className="h-8 w-auto text-foreground"
          xmlns="http://www.w3.org/2000/svg"
          version="1.0"
          width="308.000000pt"
          height="218.000000pt"
          viewBox="0 0 308.000000 218.000000"
          preserveAspectRatio="xMidYMid meet"
        >
          <g
            transform="translate(0.000000,218.000000) scale(0.100000,-0.100000)"
            fill="currentColor"
            stroke="none"
          >
            <path d="M1793 2035 c21 -52 19 -64 -7 -71 -27 -6 -30 -12 -21 -36 4 -9 17 -13 39 -10 31 4 35 1 41 -27 6 -29 21 -48 31 -39 2 3 -2 21 -10 40 -16 38 -13 48 16 48 13 0 18 7 18 25 0 24 -3 25 -33 20 -31 -6 -34 -4 -43 26 -5 18 -16 35 -23 37 -10 3 -12 0 -8 -13z"></path>
            <path d="M1450 1851 c-299 -98 -577 -340 -646 -564 l-18 -58 55 -55 54 -54 54 54 c34 34 51 59 47 68 -4 7 -13 24 -21 38 -19 33 -19 111 0 157 60 143 299 328 540 419 85 32 37 29 -65 -5z"></path>
            <path d="M240 845 l0 -245 50 0 50 0 0 95 0 95 73 0 c46 0 80 -5 92 -14 11 -7 45 -50 75 -95 l55 -81 53 0 c45 0 53 3 48 16 -11 29 -97 143 -126 168 l-30 25 33 10 c83 28 122 128 77 199 -37 60 -81 72 -277 72 l-173 0 0 -245z m345 140 c14 -13 25 -33 25 -45 0 -11 -11 -32 -25 -45 -23 -24 -31 -25 -135 -25 l-110 0 0 70 0 70 110 0 c104 0 112 -1 135 -25z"></path>
            <path d="M842 848 l3 -243 50 0 50 0 3 243 2 242 -55 0 -55 0 2 -242z"></path>
            <path d="M1092 848 l3 -243 50 0 50 0 3 103 3 102 140 0 140 0 -3 38 -3 37 -137 3 -138 3 0 59 0 60 145 0 145 0 0 40 0 40 -200 0 -200 0 2 -242z"></path>
            <path d="M1592 848 l3 -243 48 -3 47 -3 1 90 c1 50 2 97 3 104 1 9 37 13 139 15 l137 3 0 39 0 39 -137 3 -138 3 0 55 0 55 148 3 147 3 0 39 0 40 -200 0 -200 0 2 -242z"></path>
            <path d="M2163 850 c-73 -131 -133 -242 -133 -245 0 -3 22 -5 49 -5 49 0 49 0 80 55 l31 55 154 0 154 0 28 -55 c29 -55 29 -55 77 -55 26 0 47 5 47 11 0 9 -215 406 -248 457 -11 18 -24 22 -61 22 l-46 0 -132 -240z m236 45 c28 -53 51 -98 51 -100 0 -3 -50 -5 -110 -5 l-110 0 52 100 c29 55 56 100 60 100 3 0 29 -43 57 -95z"></path>
            <path d="M2742 848 l3 -243 50 0 50 0 3 243 2 242 -55 0 -55 0 2 -242z"></path>
          </g>
        </svg>
      </div>

      <div className="flex min-w-0 items-center gap-2">
        {/* <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-primary text-primary-foreground text-[11px] font-bold">
        <svg class="w-auto h-10" xmlns="http://www.w3.org/2000/svg" version="1.0" width="308.000000pt" height="218.000000pt" viewBox="0 0 308.000000 218.000000" preserveAspectRatio="xMidYMid meet"><g transform="translate(0.000000,218.000000) scale(0.100000,-0.100000)" fill="#FFF" stroke="none"><path d="M1793 2035 c21 -52 19 -64 -7 -71 -27 -6 -30 -12 -21 -36 4 -9 17 -13 39 -10 31 4 35 1 41 -27 6 -29 21 -48 31 -39 2 3 -2 21 -10 40 -16 38 -13 48 16 48 13 0 18 7 18 25 0 24 -3 25 -33 20 -31 -6 -34 -4 -43 26 -5 18 -16 35 -23 37 -10 3 -12 0 -8 -13z"></path><path d="M1450 1851 c-299 -98 -577 -340 -646 -564 l-18 -58 55 -55 54 -54 54 54 c34 34 51 59 47 68 -4 7 -13 24 -21 38 -19 33 -19 111 0 157 60 143 299 328 540 419 85 32 37 29 -65 -5z"></path><path d="M240 845 l0 -245 50 0 50 0 0 95 0 95 73 0 c46 0 80 -5 92 -14 11 -7 45 -50 75 -95 l55 -81 53 0 c45 0 53 3 48 16 -11 29 -97 143 -126 168 l-30 25 33 10 c83 28 122 128 77 199 -37 60 -81 72 -277 72 l-173 0 0 -245z m345 140 c14 -13 25 -33 25 -45 0 -11 -11 -32 -25 -45 -23 -24 -31 -25 -135 -25 l-110 0 0 70 0 70 110 0 c104 0 112 -1 135 -25z"></path><path d="M842 848 l3 -243 50 0 50 0 3 243 2 242 -55 0 -55 0 2 -242z"></path><path d="M1092 848 l3 -243 50 0 50 0 3 103 3 102 140 0 140 0 -3 38 -3 37 -137 3 -138 3 0 59 0 60 145 0 145 0 0 40 0 40 -200 0 -200 0 2 -242z"></path><path d="M1592 848 l3 -243 48 -3 47 -3 1 90 c1 50 2 97 3 104 1 9 37 13 139 15 l137 3 0 39 0 39 -137 3 -138 3 0 55 0 55 148 3 147 3 0 39 0 40 -200 0 -200 0 2 -242z"></path><path d="M2163 850 c-73 -131 -133 -242 -133 -245 0 -3 22 -5 49 -5 49 0 49 0 80 55 l31 55 154 0 154 0 28 -55 c29 -55 29 -55 77 -55 26 0 47 5 47 11 0 9 -215 406 -248 457 -11 18 -24 22 -61 22 l-46 0 -132 -240z m236 45 c28 -53 51 -98 51 -100 0 -3 -50 -5 -110 -5 l-110 0 52 100 c29 55 56 100 60 100 3 0 29 -43 57 -95z"></path><path d="M2742 848 l3 -243 50 0 50 0 3 243 2 242 -55 0 -55 0 2 -242z"></path></g></svg>
        </div> */}
        {/* <h1 className="hidden truncate text-sm font-semibold tracking-tight sm:block">{title}</h1> */}
      </div>
      <div className="flex-1" />

      <Button
        type="button"
        variant="outline"
        size="sm"
        className="hidden h-8 gap-2 text-muted-foreground md:inline-flex"
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
          {hasClerk ? (
            <>
              <Show when="signed-out">
                <SignInButton mode="modal">
                  <Button type="button" variant="outline" size="sm" className="h-8">
                    Sign in
                  </Button>
                </SignInButton>
              </Show>
              <Show when="signed-in">
                <div className="flex items-center gap-2">
                  {!isPro ? (
                    <Button
                      variant="outline"
                      size="sm"
                      className="hidden h-8 sm:inline-flex"
                      onClick={openUpgrade}
                    >
                      Upgrade to Pro
                    </Button>
                  ) : (
                    <Badge variant="secondary" className="hidden text-xs sm:inline-flex">
                      Pro
                    </Badge>
                  )}
                  <UserButton afterSignOutUrl={window.location.href} />
                </div>
              </Show>
            </>
          ) : (
            <Badge variant="outline" className="text-xs">
              Guest Mode
            </Badge>
          )}
        </div>
      </div>
    </header>
  );
}

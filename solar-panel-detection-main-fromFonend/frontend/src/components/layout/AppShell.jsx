import { useState } from 'react';
import { ApiErrorBanner } from '@/components/layout/ApiErrorBanner';
import { CommandPalette } from '@/components/layout/CommandPalette';
import { SettingsSheet } from '@/components/settings/SettingsSheet';
import { TopBar } from '@/components/layout/TopBar';

/**
 * @param {{
 *   children: import('react').ReactNode,
 *   route: string,
 *   title: string,
 *   apiError?: boolean,
 *   onApiRetry?: () => void,
 * }} props
 */
export function AppShell({ children, route, title, apiError, onApiRetry }) {
  const [commandOpen, setCommandOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);

  return (
    <div className="relative h-dvh w-screen overflow-hidden">
      {/* Layer 0: Map — always full screen */}
      <div id="map-root" className="fixed inset-0" style={{ zIndex: 0 }} />

      {/* Layer 1: Floating UI — all panels, bars, controls */}
      <div className="fixed inset-0 pointer-events-none" style={{ zIndex: 10 }}>
        <TopBar
          title={title}
          onOpenCommand={() => setCommandOpen(true)}
          onOpenSettings={() => setSettingsOpen(true)}
        />

        {apiError ? (
          <div
            className="pointer-events-auto"
            style={{ position: 'absolute', top: '64px', left: '12px', right: '12px', zIndex: 30 }}
          >
            <ApiErrorBanner
              message="Unable to reach the buildings API. Check the server or VITE_BUILDINGS_API_URL."
              onRetry={onApiRetry}
            />
          </div>
        ) : null}

        {children}

        <CommandPalette open={commandOpen} onOpenChange={setCommandOpen} />
        <SettingsSheet open={settingsOpen} onOpenChange={setSettingsOpen} />
      </div>
    </div>
  );
}

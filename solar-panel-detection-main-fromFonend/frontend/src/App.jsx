import { useEffect } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { ClerkLoaded, ClerkLoading, useAuth as useClerkAuth } from '@clerk/react';
import { AppShell } from '@/components/layout/AppShell';
import { BuildingSheet } from '@/components/map/BuildingSheet';
import { useHashRoute } from '@/hooks/useHashRoute';
import { useStats } from '@/hooks/useStats';
import { configureApiAuth } from '@/lib/api';
import { MapPage } from '@/pages/MapPage';
import { useMapSettings } from '@/contexts/MapSettingsContext';
import { useMapUI } from '@/contexts/MapUIContext';
import { Loader2 } from 'lucide-react';

const TITLES = {
  '#/map': 'Map',
  '#/stats': 'Statistics',
  '#/data': 'Buildings data',
  '#/solar': 'Solar calculator',
};

// Check if Clerk is available
const hasClerk = Boolean(import.meta.env.VITE_CLERK_PUBLISHABLE_KEY);

/**
 * Same map shell as the original flat App: AppShell + MapPage + BuildingSheet.
 * `getTokenForApi` is null for guests, or Clerk getToken when signed in.
 *
 * @param {{ getTokenForApi: null | (() => Promise<string | null | undefined>) }} props
 */
function MainMapApp({ getTokenForApi, isSignedIn = false }) {
  const queryClient = useQueryClient();
  const [route] = useHashRoute();
  const statsQ = useStats();
  const { setFlyToTarget, setHighlightBuildingId } = useMapSettings();

  const { selectedBuilding, setSelectedBuilding } = useMapUI();

  useEffect(() => {
    if (!isSignedIn) {
      queryClient.removeQueries({ queryKey: ['stats'] });
      queryClient.removeQueries({ queryKey: ['buildings'] });
    }
  }, [isSignedIn, queryClient]);

  useEffect(() => {
    configureApiAuth(getTokenForApi);
    return () => configureApiAuth(null);
  }, [getTokenForApi]);

  useEffect(() => {
    const url = new URL(window.location.href);
    const payment = url.searchParams.get('payment');
    if (payment === 'success') {
      toast.success('Welcome to Pro! If your account is not unlocked yet, refresh in a moment.', {
        id: 'payment-success',
      });
      url.searchParams.delete('payment');
      window.history.replaceState({}, '', url.toString());
    }
    if (payment === 'cancelled') {
      toast.message('Checkout cancelled.', { id: 'payment-cancelled' });
      url.searchParams.delete('payment');
      window.history.replaceState({}, '', url.toString());
    }
  }, []);

  useEffect(() => {
    if (isSignedIn && statsQ.isError) {
      toast.error('Buildings API unreachable', {
        id: 'api-down',
        action: { label: 'Retry', onClick: () => statsQ.refetch() },
      });
    }
  }, [isSignedIn, statsQ.isError, statsQ.refetch]);

  const title = TITLES[route] || TITLES['#/map'];

  const onSelectBuilding = (b) => {
    setSelectedBuilding(b);
  };

  const onLoadInMap = (b) => {
    setFlyToTarget({
      lat: Number(b.latitude),
      lon: Number(b.longitude),
      zoom: 17,
    });
    setHighlightBuildingId(b.id);
    setSelectedBuilding(b);
  };

  return (
    <AppShell
      route={route}
      title={title}
      apiError={Boolean(isSignedIn && statsQ.isError)}
      onApiRetry={() => statsQ.refetch()}
    >
      <>
        <MapPage onSelectBuilding={onSelectBuilding} onLoadInMap={onLoadInMap} />
        <BuildingSheet
          building={selectedBuilding}
          open={Boolean(selectedBuilding)}
          onOpenChange={(open) => {
            if (!open) {
              setSelectedBuilding(null);
              setHighlightBuildingId(null);
            }
          }}
        />
      </>
    </AppShell>
  );
}

function AppWithAuth() {
  const { isSignedIn, getToken } = useClerkAuth();
  return <MainMapApp getTokenForApi={isSignedIn ? getToken : null} isSignedIn={isSignedIn} />;
}

function AppWithoutAuth() {
  return <MainMapApp getTokenForApi={null} isSignedIn={false} />;
}

function App() {
  // If no Clerk key, run without authentication
  if (!hasClerk) {
    return <AppWithoutAuth />;
  }

  // With Clerk authentication
  return (
    <>
      <ClerkLoading>
        <div className="flex min-h-dvh w-screen flex-col items-center justify-center gap-3 bg-background text-muted-foreground">
          <Loader2 className="h-8 w-8 animate-spin" aria-hidden />
          <span className="text-sm">Loading…</span>
        </div>
      </ClerkLoading>
      <ClerkLoaded>
        <AppWithAuth />
      </ClerkLoaded>
    </>
  );
}

export default App;

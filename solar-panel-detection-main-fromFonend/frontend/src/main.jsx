import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { ClerkProvider } from '@clerk/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider } from 'next-themes';
import { TooltipProvider } from '@/components/ui/tooltip';
import { Toaster } from '@/components/ui/sonner';
import { MapSettingsProvider } from '@/contexts/MapSettingsContext';
import { MapUIProvider } from '@/contexts/MapUIContext';
import { UpgradeProvider } from '@/contexts/UpgradeContext';
import './index.css';
import App from './App';

const clerkKey = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY;

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

const AppContent = () => (
  <QueryClientProvider client={queryClient}>
    <ThemeProvider attribute="class" defaultTheme="system" enableSystem disableTransitionOnChange>
      <TooltipProvider delayDuration={200}>
        <MapSettingsProvider>
          <MapUIProvider>
            <UpgradeProvider>
              <App />
              <Toaster richColors position="top-center" />
            </UpgradeProvider>
          </MapUIProvider>
        </MapSettingsProvider>
      </TooltipProvider>
    </ThemeProvider>
  </QueryClientProvider>
);

createRoot(document.getElementById('root')).render(
  <StrictMode>
    {clerkKey ? (
      <ClerkProvider
        publishableKey={clerkKey}
        afterSignOutUrl="/"
        appearance={{
          variables: {
            colorPrimary: 'hsl(173 58% 39%)',
            colorBackground: 'hsl(var(--background))',
            colorInputBackground: 'hsl(var(--card))',
            colorText: 'hsl(var(--foreground))',
            borderRadius: '0.5rem',
            fontFamily: 'inherit',
          },
          elements: {
            card: 'shadow-md border border-border',
            formButtonPrimary: 'bg-primary text-primary-foreground hover:bg-primary/90',
          },
        }}
      >
        <AppContent />
      </ClerkProvider>
    ) : (
      <AppContent />
    )}
  </StrictMode>
);

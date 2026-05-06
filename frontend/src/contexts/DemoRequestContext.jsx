import { createContext, useCallback, useContext, useMemo, useState } from 'react';
import { DemoRequestModal } from '@/components/payments/DemoRequestModal';

const DemoRequestContext = createContext(
  /** @type {null | { openDemoRequest: (opts?: { source?: string }) => void, closeDemoRequest: () => void }} */ (null)
);

/**
 * Provides a global Demo Request modal trigger for locked Pro surfaces.
 * @param {{ children: import('react').ReactNode }} props
 */
export function DemoRequestProvider({ children }) {
  const [open, setOpen] = useState(false);
  const [source, setSource] = useState('Locked Pro feature');

  const openDemoRequest = useCallback((opts) => {
    setSource(opts?.source || 'Locked Pro feature');
    setOpen(true);
  }, []);

  const closeDemoRequest = useCallback(() => setOpen(false), []);

  const value = useMemo(() => ({ openDemoRequest, closeDemoRequest }), [openDemoRequest, closeDemoRequest]);

  return (
    <DemoRequestContext.Provider value={value}>
      {children}
      <DemoRequestModal open={open} onOpenChange={setOpen} source={source} />
    </DemoRequestContext.Provider>
  );
}

export function useDemoRequest() {
  const ctx = useContext(DemoRequestContext);
  if (!ctx) {
    return { openDemoRequest: () => {}, closeDemoRequest: () => {} };
  }
  return ctx;
}

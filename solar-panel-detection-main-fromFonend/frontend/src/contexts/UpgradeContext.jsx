import { createContext, useCallback, useContext, useMemo, useState } from 'react';
import { UpgradeModal } from '@/components/payments/UpgradeModal';

const UpgradeContext = createContext(
  /** @type {null | { openUpgrade: () => void, closeUpgrade: () => void }} */ (null)
);

/**
 * Provides a global Upgrade modal trigger for TopBar/Pro gate/Settings.
 * @param {{ children: import('react').ReactNode }} props
 */
export function UpgradeProvider({ children }) {
  const [open, setOpen] = useState(false);

  const openUpgrade = useCallback(() => setOpen(true), []);
  const closeUpgrade = useCallback(() => setOpen(false), []);

  const value = useMemo(() => ({ openUpgrade, closeUpgrade }), [openUpgrade, closeUpgrade]);

  return (
    <UpgradeContext.Provider value={value}>
      {children}
      <UpgradeModal open={open} onOpenChange={setOpen} />
    </UpgradeContext.Provider>
  );
}

export function useUpgrade() {
  const ctx = useContext(UpgradeContext);
  if (!ctx) {
    return { openUpgrade: () => {}, closeUpgrade: () => {} };
  }
  return ctx;
}


import { createContext, useContext, useMemo, useState } from 'react';

const MapUIContext = createContext(null);

export function MapUIProvider({ children }) {
  const [leftPanelOpen, setLeftPanelOpen] = useState(false);
  const [leftPanelTab, setLeftPanelTab] = useState('stats'); // 'stats' | 'filters' | 'data' | 'solar'
  const [selectedBuilding, setSelectedBuilding] = useState(null);
  const [legendOpen, setLegendOpen] = useState(true);
  const [activeFilterCount, setActiveFilterCount] = useState(0);

  const value = useMemo(
    () => ({
      leftPanelOpen,
      setLeftPanelOpen,
      leftPanelTab,
      setLeftPanelTab,
      selectedBuilding,
      setSelectedBuilding,
      legendOpen,
      setLegendOpen,
      activeFilterCount,
      setActiveFilterCount,
    }),
    [
      leftPanelOpen,
      leftPanelTab,
      selectedBuilding,
      legendOpen,
      activeFilterCount,
    ]
  );

  return <MapUIContext.Provider value={value}>{children}</MapUIContext.Provider>;
}

export function useMapUI() {
  const ctx = useContext(MapUIContext);
  if (!ctx) throw new Error('useMapUI must be used within a MapUIProvider');
  return ctx;
}


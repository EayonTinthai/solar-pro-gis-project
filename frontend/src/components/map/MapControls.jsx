import { Crosshair, Minus, Plus } from 'lucide-react';
import { toast } from 'sonner';
import { useMapSettings } from '@/contexts/MapSettingsContext';

function MapIconButton({ children, onClick, ...props }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="h-10 w-10 flex items-center justify-center text-muted-foreground hover:text-foreground transition-colors"
      {...props}
    >
      {children}
    </button>
  );
}

/**
 * @param {{ embedded?: boolean, navigationLocked?: boolean, onNavigationAttempt?: () => void }} props
 */
export function MapControls({
  embedded = false,
  navigationLocked = false,
  onNavigationAttempt = () => {},
}) {
  const { mapCenter, mapZoom, setMapCenter, setFlyToTarget } = useMapSettings();

  const zoomTo = (nextZoom) => {
    if (navigationLocked) {
      onNavigationAttempt();
      return;
    }
    const [lat, lon] = mapCenter;
    setFlyToTarget({ lat: Number(lat), lon: Number(lon), zoom: nextZoom });
  };

  const locateUser = () => {
    if (navigationLocked) {
      onNavigationAttempt();
      return;
    }
    if (!navigator.geolocation) {
      toast.error('Geolocation is not supported');
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const lat = pos.coords.latitude;
        const lon = pos.coords.longitude;
        setMapCenter([lat, lon]);
        setFlyToTarget({ lat, lon, zoom: Math.max(mapZoom, 15) });
        toast.success('Centered on your location');
      },
      () => toast.error('Could not get your location'),
      { enableHighAccuracy: true, timeout: 10000 }
    );
  };

  const positionStyle = embedded
    ? {
        position: 'relative',
        display: 'flex',
        flexDirection: 'column',
        gap: '1px',
        overflow: 'hidden',
      }
    : {
        position: 'absolute',
        right: '12px',
        bottom: '68px',
        display: 'flex',
        flexDirection: 'column',
        gap: '1px',
        overflow: 'hidden',
        zIndex: 15,
      };

  return (
    <div className="glass-panel pointer-events-auto map-controls" style={positionStyle}>
      <MapIconButton aria-label="Zoom in" onClick={() => zoomTo(mapZoom + 1)}>
        <Plus size={16} />
      </MapIconButton>
      <div className="h-px bg-border/60" />
      <MapIconButton aria-label="Zoom out" onClick={() => zoomTo(mapZoom - 1)}>
        <Minus size={16} />
      </MapIconButton>
      <div className="h-px bg-border/60" />
      <MapIconButton aria-label="My location" onClick={locateUser}>
        <Crosshair size={16} />
      </MapIconButton>
    </div>
  );
}


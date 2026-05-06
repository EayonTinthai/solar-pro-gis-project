import { ChevronDown, Layers } from 'lucide-react';
import { useMapUI } from '@/contexts/MapUIContext';

const ITEMS = [
  { color: '#22c55e', label: '≥ 90%' },
  { color: '#3b82f6', label: '80–90%' },
  { color: '#f59e0b', label: '70–80%' },
  { color: '#ef4444', label: '< 70%' },
];

/**
 * @param {{ embedded?: boolean }} props
 */
export function MapLegendFloating({ embedded = false }) {
  const { leftPanelOpen, legendOpen, setLegendOpen } = useMapUI();

  const positionStyle = embedded
    ? {
        position: 'relative',
        padding: '8px 12px',
      }
    : {
        position: 'absolute',
        left: leftPanelOpen ? '344px' : '12px',
        bottom: '68px',
        transition: 'left 280ms cubic-bezier(0.16, 1, 0.3, 1)',
        padding: '8px 12px',
        zIndex: 15,
      };

  return (
    <div className="glass-panel pointer-events-auto" style={positionStyle}>
      {legendOpen ? (
        <div>
          <div className="flex items-center justify-between mb-2 gap-3">
            <span className="text-xs font-medium">Confidence</span>
            <button
              type="button"
              onClick={() => setLegendOpen(false)}
              className="text-muted-foreground hover:text-foreground transition-colors"
              aria-label="Collapse legend"
            >
              <ChevronDown size={12} />
            </button>
          </div>
          {ITEMS.map(({ color, label }) => (
            <div key={label} className="flex items-center gap-2 py-0.5">
              <div className="w-2.5 h-2.5 rounded-sm flex-shrink-0" style={{ background: color }} />
              <span className="text-xs text-muted-foreground">{label}</span>
            </div>
          ))}
        </div>
      ) : (
        <button
          type="button"
          onClick={() => setLegendOpen(true)}
          className="flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors"
        >
          <Layers size={12} />
          <span>Legend</span>
        </button>
      )}
    </div>
  );
}


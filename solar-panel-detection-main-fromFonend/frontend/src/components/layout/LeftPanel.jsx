import { useEffect, useState } from 'react';
import { ChevronLeft } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useMapUI } from '@/contexts/MapUIContext';

function TabButton({ active, children, onClick }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        'h-8 rounded-md px-2.5 text-xs font-medium transition-colors',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring',
        active ? 'bg-accent text-accent-foreground' : 'text-muted-foreground hover:bg-muted/60 hover:text-foreground'
      )}
    >
      {children}
    </button>
  );
}

/**
 * @param {{
 *   stats?: import('react').ReactNode,
 *   filters?: import('react').ReactNode,
 *   data?: import('react').ReactNode,
 *   solar?: import('react').ReactNode,
 * }} props
 */
export function LeftPanel({ stats, filters, data, solar }) {
  const { leftPanelOpen, setLeftPanelOpen, leftPanelTab, setLeftPanelTab } = useMapUI();
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    const mq = window.matchMedia?.('(max-width: 768px)');
    if (!mq) return;
    const onChange = () => setIsMobile(mq.matches);
    onChange();
    mq.addEventListener?.('change', onChange);
    return () => mq.removeEventListener?.('change', onChange);
  }, []);

  return (
    <>
      <aside
        className="glass-panel-lg left-panel pointer-events-auto overflow-hidden flex flex-col"
        style={{
          position: 'absolute',
          left: isMobile ? '0' : '12px',
          right: isMobile ? '0' : undefined,
          top: isMobile ? undefined : '72px',
          bottom: isMobile ? '52px' : '64px',
          width: isMobile ? '100%' : '320px',
          height: isMobile ? '60vh' : undefined,
          borderRadius: isMobile ? 'var(--radius) var(--radius) 0 0' : undefined,
          transform: isMobile
            ? leftPanelOpen
              ? 'translateY(0)'
              : 'translateY(100%)'
            : leftPanelOpen
              ? 'translateX(0)'
              : 'translateX(calc(-100% - 24px))',
          transition: 'transform 280ms cubic-bezier(0.16, 1, 0.3, 1)',
          zIndex: 15,
        }}
      >
        <div className="flex border-b border-border/60 px-3 pt-2 gap-1 flex-shrink-0">
          <TabButton active={leftPanelTab === 'stats'} onClick={() => setLeftPanelTab('stats')}>
            Stats
          </TabButton>
          <TabButton active={leftPanelTab === 'filters'} onClick={() => setLeftPanelTab('filters')}>
            Filters
          </TabButton>
          <TabButton active={leftPanelTab === 'data'} onClick={() => setLeftPanelTab('data')}>
            Data
          </TabButton>
          {solar ? (
            <TabButton active={leftPanelTab === 'solar'} onClick={() => setLeftPanelTab('solar')}>
              Solar
            </TabButton>
          ) : null}
        </div>

        <div className="flex-1 overflow-y-auto p-3 space-y-3">
          {leftPanelTab === 'stats' ? stats : null}
          {leftPanelTab === 'filters' ? filters : null}
          {leftPanelTab === 'data' ? data : null}
          {leftPanelTab === 'solar' ? solar : null}
        </div>
      </aside>

      <button
        type="button"
        className="glass-panel pointer-events-auto"
        style={{
          position: 'absolute',
          left: isMobile ? '12px' : leftPanelOpen ? '344px' : '12px',
          top: isMobile ? undefined : '72px',
          bottom: isMobile ? '64px' : undefined,
          width: '32px',
          height: '32px',
          transition: isMobile
            ? 'bottom 280ms cubic-bezier(0.16, 1, 0.3, 1)'
            : 'left 280ms cubic-bezier(0.16, 1, 0.3, 1)',
          zIndex: 16,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
        onClick={() => setLeftPanelOpen((p) => !p)}
        aria-label={leftPanelOpen ? 'Close panel' : 'Open panel'}
      >
        <ChevronLeft
          size={16}
          style={{
            transform: leftPanelOpen ? 'rotate(0deg)' : 'rotate(180deg)',
            transition: 'transform 280ms',
          }}
        />
      </button>
    </>
  );
}


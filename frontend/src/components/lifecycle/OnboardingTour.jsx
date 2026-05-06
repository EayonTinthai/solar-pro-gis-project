import { useEffect, useMemo, useState } from 'react';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { useMapUI } from '@/contexts/MapUIContext';
import { useDemoLifecycle } from '@/contexts/DemoLifecycleContext';

const TOUR_STEPS = [
  {
    id: 'search',
    selector: '[data-tour="search-trigger"]',
    title: 'Search Places Fast',
    description: 'Use Search to jump to locations, commands, and panels from anywhere in the app.',
  },
  {
    id: 'panel-toggle',
    selector: '[data-tour="panel-toggle"]',
    title: 'Open the Side Panel',
    description: 'Toggle the left panel to view statistics, filters, data, and solar tools.',
  },
  {
    id: 'panel-tabs',
    selector: '[data-tour="panel-tabs"]',
    title: 'Switch Between Tabs',
    description: 'Use these tabs to move between Stats, Filters, Data, and Solar workflows.',
  },
  {
    id: 'map-area',
    selector: '[data-tour="map-area"]',
    title: 'Interact With the Map',
    description: 'Pan, zoom, and click buildings to inspect rooftop metrics and potential.',
  },
];

function readStorage(key) {
  if (typeof window === 'undefined') return null;
  try {
    return window.localStorage.getItem(key);
  } catch {
    return null;
  }
}

function writeStorage(key, value) {
  if (typeof window === 'undefined') return;
  try {
    window.localStorage.setItem(key, value);
  } catch {
    // ignore storage failures
  }
}

function findVisibleTarget(selector) {
  if (typeof document === 'undefined') return null;
  const nodes = Array.from(document.querySelectorAll(selector));
  return (
    nodes.find((node) => {
      const rect = node.getBoundingClientRect();
      if (rect.width <= 0 || rect.height <= 0) return false;
      const style = window.getComputedStyle(node);
      return style.display !== 'none' && style.visibility !== 'hidden' && style.opacity !== '0';
    }) || null
  );
}

function clamp(value, min, max) {
  return Math.min(Math.max(value, min), max);
}

function getCardPosition(targetRect) {
  if (!targetRect || typeof window === 'undefined') {
    return {
      top: '50%',
      left: '50%',
      transform: 'translate(-50%, -50%)',
    };
  }

  const cardWidth = Math.min(340, window.innerWidth - 24);
  const preferredLeft = targetRect.left;
  const left = clamp(preferredLeft, 12, Math.max(12, window.innerWidth - cardWidth - 12));

  const preferredBelow = targetRect.bottom + 14;
  const cardHeightEstimate = 220;
  const useBelow = preferredBelow + cardHeightEstimate <= window.innerHeight - 12;
  const top = useBelow
    ? preferredBelow
    : clamp(targetRect.top - cardHeightEstimate - 14, 12, Math.max(12, window.innerHeight - cardHeightEstimate - 12));

  return {
    top: `${top}px`,
    left: `${left}px`,
    transform: 'none',
  };
}

export function OnboardingTour() {
  const { setLeftPanelOpen } = useMapUI();
  const { isSignedIn, userId, tourCompletedAt, completeTour } = useDemoLifecycle();
  const [open, setOpen] = useState(false);
  const [stepIndex, setStepIndex] = useState(0);
  const [targetRect, setTargetRect] = useState(null);
  const [saving, setSaving] = useState(false);

  const localCompletionKey = userId ? `demo-lifecycle:${userId}:tour-local-complete` : null;
  const localCompleted = localCompletionKey ? Boolean(readStorage(localCompletionKey)) : false;

  useEffect(() => {
    if (!isSignedIn || !userId || tourCompletedAt || localCompleted) {
      setOpen(false);
      return;
    }
    setOpen(true);
    setStepIndex(0);
  }, [isSignedIn, localCompleted, tourCompletedAt, userId]);

  useEffect(() => {
    if (!open) return;
    const step = TOUR_STEPS[stepIndex];
    if (step?.id === 'panel-tabs') {
      setLeftPanelOpen(true);
    }

    const refreshRect = () => {
      const target = step ? findVisibleTarget(step.selector) : null;
      if (!target) {
        setTargetRect(null);
        return;
      }
      const rect = target.getBoundingClientRect();
      setTargetRect({
        top: Math.max(8, rect.top - 6),
        left: Math.max(8, rect.left - 6),
        width: rect.width + 12,
        height: rect.height + 12,
      });
    };

    refreshRect();
    window.addEventListener('resize', refreshRect);
    window.addEventListener('scroll', refreshRect, true);
    const interval = window.setInterval(refreshRect, 300);

    return () => {
      window.removeEventListener('resize', refreshRect);
      window.removeEventListener('scroll', refreshRect, true);
      window.clearInterval(interval);
    };
  }, [open, setLeftPanelOpen, stepIndex]);

  useEffect(() => {
    if (!open) return;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = previousOverflow;
    };
  }, [open]);

  const step = TOUR_STEPS[stepIndex];
  const cardStyle = useMemo(() => getCardPosition(targetRect), [targetRect]);

  const markTourComplete = async () => {
    if (!localCompletionKey) return;
    writeStorage(localCompletionKey, new Date().toISOString());
    setSaving(true);
    const result = await completeTour();
    if (!result.ok) {
      toast.error('Tour was closed locally but could not sync completion yet.');
    }
    setSaving(false);
    setOpen(false);
  };

  const onNext = async () => {
    if (stepIndex === TOUR_STEPS.length - 1) {
      await markTourComplete();
      return;
    }
    setStepIndex((idx) => Math.min(idx + 1, TOUR_STEPS.length - 1));
  };

  const onBack = () => {
    setStepIndex((idx) => Math.max(idx - 1, 0));
  };

  if (!open || !step) return null;

  return (
    <div className="fixed inset-0 z-[80]">
      <div className="absolute inset-0 bg-black/45" />

      {targetRect ? (
        <div
          className="pointer-events-none absolute rounded-xl border-2 border-primary/80 transition-all duration-200"
          style={{
            top: `${targetRect.top}px`,
            left: `${targetRect.left}px`,
            width: `${targetRect.width}px`,
            height: `${targetRect.height}px`,
            boxShadow: '0 0 0 9999px rgba(0, 0, 0, 0.45)',
          }}
        />
      ) : null}

      <div
        className="glass-panel-lg absolute w-[min(340px,calc(100vw-24px))] pointer-events-auto p-4"
        style={cardStyle}
      >
        <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
          Step {stepIndex + 1} of {TOUR_STEPS.length}
        </p>
        <h3 className="mt-1 text-base font-semibold">{step.title}</h3>
        <p className="mt-2 text-sm text-muted-foreground">{step.description}</p>

        <div className="mt-4 flex items-center justify-between gap-2">
          <Button type="button" variant="ghost" size="sm" onClick={markTourComplete} disabled={saving}>
            Skip tour
          </Button>
          <div className="flex items-center gap-2">
            <Button type="button" variant="outline" size="sm" onClick={onBack} disabled={stepIndex === 0 || saving}>
              Back
            </Button>
            <Button type="button" size="sm" onClick={onNext} disabled={saving}>
              {stepIndex === TOUR_STEPS.length - 1 ? 'Finish' : 'Next'}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}

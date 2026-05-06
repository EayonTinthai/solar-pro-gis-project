/**
 * Weather Toggle Button Component
 * Floating button to toggle weather panel
 */

import { Cloud } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

/**
 * @param {{
 *   active: boolean,
 *   onClick: () => void,
 *   className?: string,
 * }} props
 */
export function WeatherToggle({ active, onClick, className }) {
  return (
    <Button
      variant={active ? "default" : "secondary"}
      size="sm"
      onClick={onClick}
      className={cn(
        "h-9 w-9 p-0 shadow-lg transition-all duration-200",
        active && "bg-blue-600 hover:bg-blue-700",
        className
      )}
      title="Toggle weather forecast"
    >
      <Cloud className="h-4 w-4" />
    </Button>
  );
}
import { LayoutGrid, Map, Sun, Table2, BarChart3 } from 'lucide-react';
import { cn } from '@/lib/utils';

const NAV = [
  { href: '#/map', label: 'Map', icon: Map },
  { href: '#/stats', label: 'Stats', icon: BarChart3 },
  { href: '#/data', label: 'Data', icon: Table2 },
  { href: '#/solar', label: 'Solar', icon: Sun },
];

/**
 * @param {{ route: string, onNavigate?: () => void }} props
 */
export function Sidebar({ route, onNavigate }) {
  const r = route || '#/map';

  return (
    <nav className="flex flex-col gap-1 p-3" aria-label="Main">
      <div className="mb-2 flex items-center gap-2 px-2 text-muted-foreground">
        <LayoutGrid className="h-4 w-4" aria-hidden />
        <span className="text-xs font-medium uppercase tracking-wide">Views</span>
      </div>
      {NAV.map(({ href, label, icon: Icon }) => {
        const isActive = r === href;

        return (
          <a
            key={href}
            href={href}
            onClick={() => onNavigate?.()}
            className={cn(
              'flex min-h-10 items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring',
              isActive
                ? 'bg-accent text-accent-foreground'
                : 'text-muted-foreground hover:bg-muted hover:text-foreground'
            )}
          >
            <Icon className="h-4 w-4 shrink-0" aria-hidden />
            {label}
          </a>
        );
      })}
    </nav>
  );
}

import { StatsPanelV2 } from '@/components/stats/StatsPanelV2';

export function StatsPage() {
  return (
    <div className="space-y-6 p-4 md:p-6">
      <div className="mx-auto w-full max-w-4xl">
        <StatsPanelV2 />
      </div>
    </div>
  );
}

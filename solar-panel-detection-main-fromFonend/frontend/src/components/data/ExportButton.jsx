import { Download } from 'lucide-react';
import { Button } from '@/components/ui/button';

/**
 * @param {{ rows: Array<Record<string, unknown>>, filename?: string }} props
 */
export function ExportButton({ rows, filename = 'buildings.csv' }) {
  const download = () => {
    if (!rows?.length) return;
    const headers = ['id', 'area_m2', 'confidence', 'latitude', 'longitude'];
    const lines = [
      headers.join(','),
      ...rows.map((r) =>
        headers
          .map((h) => {
            const v = r[h];
            if (v == null) return '';
            const s = String(v);
            return s.includes(',') ? `"${s.replace(/"/g, '""')}"` : s;
          })
          .join(',')
      ),
    ];
    const blob = new Blob([lines.join('\n')], { type: 'text/csv;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <Button type="button" variant="outline" size="sm" className="gap-2" onClick={download}>
      <Download className="h-4 w-4" />
      Export CSV
    </Button>
  );
}

import { useMemo, useState } from 'react';
import { ArrowUpDown, MapPin } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Slider } from '@/components/ui/slider';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { ExportButton } from '@/components/data/ExportButton';
import { cn, confidenceBadgeClassName } from '@/lib/utils';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
/**
 * @param {{
 *   buildings: Array<Record<string, unknown>>,
 *   loading?: boolean,
 *   compact?: boolean,
 *   onRowOpen: (b: Record<string, unknown>) => void,
 *   onLoadInMap?: (b: Record<string, unknown>) => void,
 * }} props
 */
export function BuildingsTable({
  buildings,
  loading,
  compact,
  onRowOpen,
  onLoadInMap,
}) {
  const [sortKey, setSortKey] = useState(/** @type {'id'|'area_m2'|'confidence'|'latitude'|'longitude'} */ ('area_m2'));
  const [sortDir, setSortDir] = useState(/** @type {'asc'|'desc'} */ ('desc'));
  const [qId, setQId] = useState('');
  const [qArea, setQArea] = useState('');
  const [qConf, setQConf] = useState('');
  const [qLat, setQLat] = useState('');
  const [qLon, setQLon] = useState('');
  const [confRange, setConfRange] = useState([0.5, 1]);
  const [minArea, setMinArea] = useState('');
  const [maxArea, setMaxArea] = useState('');
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(25);

  const filtered = useMemo(() => {
    let rows = buildings || [];
    const match = (row, field, q) => {
      if (!q.trim()) return true;
      const v = row[field];
      return String(v ?? '').toLowerCase().includes(q.toLowerCase());
    };
    rows = rows.filter(
      (r) =>
        match(r, 'id', qId) &&
        match(r, 'area_m2', qArea) &&
        match(r, 'confidence', qConf) &&
        match(r, 'latitude', qLat) &&
        match(r, 'longitude', qLon)
    );
    rows = rows.filter(
      (r) =>
        r.confidence >= confRange[0] &&
        r.confidence <= confRange[1]
    );
    const minA = minArea === '' ? null : Number(minArea);
    const maxA = maxArea === '' ? null : Number(maxArea);
    if (minA != null && !Number.isNaN(minA)) {
      rows = rows.filter((r) => r.area_m2 >= minA);
    }
    if (maxA != null && !Number.isNaN(maxA)) {
      rows = rows.filter((r) => r.area_m2 <= maxA);
    }
    return rows;
  }, [buildings, qId, qArea, qConf, qLat, qLon, confRange, minArea, maxArea]);

  const sorted = useMemo(() => {
    const rows = [...filtered];
    rows.sort((a, b) => {
      const av = a[sortKey];
      const bv = b[sortKey];
      const mul = sortDir === 'asc' ? 1 : -1;
      if (av == null) return 1;
      if (bv == null) return -1;
      if (typeof av === 'number' && typeof bv === 'number') {
        return (av - bv) * mul;
      }
      return String(av).localeCompare(String(bv)) * mul;
    });
    return rows;
  }, [filtered, sortKey, sortDir]);

  const pageCount = Math.max(1, Math.ceil(sorted.length / pageSize));
  const pageRows = useMemo(() => {
    if (compact) return sorted.slice(0, 10);
    const start = page * pageSize;
    return sorted.slice(start, start + pageSize);
  }, [sorted, page, pageSize, compact]);

  const toggleSort = (key) => {
    if (sortKey === key) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortKey(key);
      setSortDir('desc');
    }
  };

  const defaultConfRange = [0.5, 1];
  const defaultArea = ['', ''];
  const activeFilters =
    (confRange[0] !== defaultConfRange[0] || confRange[1] !== defaultConfRange[1] ? 1 : 0) +
    (minArea !== '' || maxArea !== '' ? 1 : 0) +
    (qId || qArea || qConf || qLat || qLon ? 1 : 0);

  if (loading) {
    return (
      <div className="space-y-2 rounded-xl border p-4">
        <div className="h-8 w-full animate-pulse rounded bg-muted" />
        <div className="h-40 w-full animate-pulse rounded bg-muted" />
      </div>
    );
  }

  return (
    <div className={cn('space-y-3 rounded-xl border bg-card p-4 shadow-sm', compact && 'p-3')}>
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-sm font-medium text-muted-foreground">Buildings</span>
            {activeFilters > 0 ? (
              <Badge variant="secondary" className="tabular-nums">
                {activeFilters} active
              </Badge>
            ) : null}
          </div>
          <div className="flex flex-wrap gap-2">
            <ExportButton rows={sorted} />
          </div>
        </div>

        {!compact ? (
          <div className="flex flex-col gap-4 md:flex-row md:items-end">
            <div className="space-y-2">
              <p className="text-xs font-medium text-muted-foreground">Confidence range</p>
              <Slider
                value={confRange}
                min={0.5}
                max={1}
                step={0.01}
                onValueChange={setConfRange}
                className="w-48"
              />
              <p className="tabular-nums text-xs text-muted-foreground">
                {confRange[0].toFixed(2)} – {confRange[1].toFixed(2)}
              </p>
            </div>
            <div className="flex gap-2">
              <div>
                <p className="text-xs text-muted-foreground">Min area</p>
                <Input
                  type="number"
                  className="w-28"
                  value={minArea}
                  onChange={(e) => setMinArea(e.target.value)}
                  placeholder="m²"
                />
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Max area</p>
                <Input
                  type="number"
                  className="w-28"
                  value={maxArea}
                  onChange={(e) => setMaxArea(e.target.value)}
                  placeholder="m²"
                />
              </div>
            </div>
          </div>
        ) : null}

        <div className="overflow-x-auto rounded-lg border">
          <Table>
            <TableHeader>
              <TableRow>
                {[
                  { key: 'id', label: 'ID' },
                  { key: 'area_m2', label: 'Area (m²)' },
                  { key: 'confidence', label: 'Conf.' },
                  { key: 'latitude', label: 'Lat' },
                  { key: 'longitude', label: 'Lon' },
                ].map((col) => (
                  <TableHead key={col.key}>
                    <button
                      type="button"
                      className="flex items-center gap-1 font-medium hover:text-foreground"
                      onClick={() => toggleSort(col.key)}
                    >
                      {col.label}
                      <ArrowUpDown className="h-3 w-3 opacity-50" />
                    </button>
                    {!compact ? (
                      <Input
                        className="mt-1 h-8 text-xs"
                        placeholder="Filter…"
                        value={
                          col.key === 'id'
                            ? qId
                            : col.key === 'area_m2'
                              ? qArea
                              : col.key === 'confidence'
                                ? qConf
                                : col.key === 'latitude'
                                  ? qLat
                                  : qLon
                        }
                        onChange={(e) => {
                          const v = e.target.value;
                          if (col.key === 'id') setQId(v);
                          if (col.key === 'area_m2') setQArea(v);
                          if (col.key === 'confidence') setQConf(v);
                          if (col.key === 'latitude') setQLat(v);
                          if (col.key === 'longitude') setQLon(v);
                        }}
                      />
                    ) : null}
                  </TableHead>
                ))}
                {!compact ? <TableHead className="w-[120px]">Map</TableHead> : null}
              </TableRow>
            </TableHeader>
            <TableBody>
              {pageRows.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={compact ? 5 : 6} className="h-24 text-center text-muted-foreground">
                    No buildings match the current filters.
                  </TableCell>
                </TableRow>
              ) : (
                pageRows.map((b) => (
                  <TableRow
                    key={b.id}
                    className="cursor-pointer"
                    onClick={() => onRowOpen(b)}
                  >
                    <TableCell className="tabular-nums font-medium">{b.id}</TableCell>
                    <TableCell className="tabular-nums">{Number(b.area_m2).toFixed(1)}</TableCell>
                    <TableCell>
                      <Badge className={cn(confidenceBadgeClassName(Number(b.confidence)), 'tabular-nums')}>
                        {(Number(b.confidence) * 100).toFixed(1)}%
                      </Badge>
                    </TableCell>
                    <TableCell className="tabular-nums text-xs">{Number(b.latitude).toFixed(5)}</TableCell>
                    <TableCell className="tabular-nums text-xs">{Number(b.longitude).toFixed(5)}</TableCell>
                    {!compact ? (
                      <TableCell>
                        {onLoadInMap ? (
                          <Button
                            type="button"
                            variant="outline"
                            size="sm"
                            className="gap-1"
                            onClick={(e) => {
                              e.stopPropagation();
                              onLoadInMap(b);
                            }}
                          >
                            <MapPin className="h-3 w-3" />
                            Map
                          </Button>
                        ) : null}
                      </TableCell>
                    ) : null}
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>

        {!compact ? (
          <div className="flex flex-wrap items-center justify-between gap-2 text-sm">
            <div className="flex items-center gap-2">
              <span className="text-muted-foreground">Rows per page</span>
              <Select
                value={String(pageSize)}
                onValueChange={(v) => {
                  setPageSize(Number(v));
                  setPage(0);
                }}
              >
                <SelectTrigger className="w-24">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="25">25</SelectItem>
                  <SelectItem value="50">50</SelectItem>
                  <SelectItem value="100">100</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="flex items-center gap-2">
              <Button
                type="button"
                variant="outline"
                size="sm"
                disabled={page <= 0}
                onClick={() => setPage((p) => Math.max(0, p - 1))}
              >
                Prev
              </Button>
              <span className="tabular-nums text-muted-foreground">
                {page + 1} / {pageCount}
              </span>
              <Button
                type="button"
                variant="outline"
                size="sm"
                disabled={page >= pageCount - 1}
                onClick={() => setPage((p) => Math.min(pageCount - 1, p + 1))}
              >
                Next
              </Button>
            </div>
          </div>
        ) : null}
      </div>
  );
}

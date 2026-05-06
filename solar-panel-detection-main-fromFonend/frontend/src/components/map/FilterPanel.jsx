import { Filter } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Slider } from '@/components/ui/slider';

/**
 * @param {{
 *   minConfidence: number,
 *   onMinConfidenceChange: (v: number) => void,
 *   minArea: string,
 *   maxArea: string,
 *   onMinAreaChange: (v: string) => void,
 *   onMaxAreaChange: (v: string) => void,
 *   limit: number,
 *   onLimitChange: (v: number) => void,
 *   onApply: () => void,
 *   activeFilterCount: number,
 * }} props
 */
export function FilterPanel({
  minConfidence,
  onMinConfidenceChange,
  minArea,
  maxArea,
  onMinAreaChange,
  onMaxAreaChange,
  limit,
  onLimitChange,
  onApply,
  activeFilterCount,
}) {
  return (
    <Popover>
      <PopoverTrigger asChild>
        <Button
          type="button"
          variant="outline"
          size="sm"
          className="gap-2"
        >
          <Filter className="h-4 w-4" />
          Filters
          {activeFilterCount > 0 ? (
            <Badge variant="secondary" className="tabular-nums">
              {activeFilterCount}
            </Badge>
          ) : null}
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-80 space-y-4" align="start">
        <div className="space-y-2">
          <div className="flex justify-between gap-2">
            <Label className="text-sm font-medium text-muted-foreground">
              Min confidence
            </Label>
            <span className="tabular-nums text-sm text-muted-foreground">
              {minConfidence.toFixed(2)}
            </span>
          </div>
          <Slider
            value={[minConfidence]}
            min={0.5}
            max={1}
            step={0.01}
            onValueChange={(v) => onMinConfidenceChange(v[0])}
          />
        </div>
        <div className="grid grid-cols-2 gap-2">
          <div className="space-y-1">
            <Label className="text-xs text-muted-foreground">Min area (m²)</Label>
            <Input
              type="number"
              min={0}
              placeholder="Any"
              value={minArea}
              onChange={(e) => onMinAreaChange(e.target.value)}
            />
          </div>
          <div className="space-y-1">
            <Label className="text-xs text-muted-foreground">Max area (m²)</Label>
            <Input
              type="number"
              min={0}
              placeholder="Any"
              value={maxArea}
              onChange={(e) => onMaxAreaChange(e.target.value)}
            />
          </div>
        </div>
        <div className="space-y-2">
          <Label className="text-sm font-medium text-muted-foreground">Result limit</Label>
          <Select value={String(limit)} onValueChange={(v) => onLimitChange(Number(v))}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="100">100</SelectItem>
              <SelectItem value="500">500</SelectItem>
              <SelectItem value="1000">1000</SelectItem>
              <SelectItem value="5000">5000</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <Button type="button" className="w-full" onClick={onApply}>
          Apply filters
        </Button>
      </PopoverContent>
    </Popover>
  );
}

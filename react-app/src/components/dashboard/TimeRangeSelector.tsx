import { useState } from "react";
import { Calendar, Clock } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { TIME_RANGES } from "@/hooks/useStats";
import type { TimeRange, StatsQuery } from "@/types/stats";

interface TimeRangeSelectorProps {
  value: StatsQuery;
  onChange: (query: StatsQuery) => void;
  className?: string;
}

export function TimeRangeSelector({
  value,
  onChange,
  className,
}: TimeRangeSelectorProps) {
  const [showCustomDialog, setShowCustomDialog] = useState(false);
  const [customStart, setCustomStart] = useState("");
  const [customEnd, setCustomEnd] = useState("");

  const currentTimeRange = value.time_range || "24h";
  const isCustomRange = currentTimeRange === "custom";

  const handleTimeRangeChange = (newRange: TimeRange) => {
    if (newRange === "custom") {
      setShowCustomDialog(true);
    } else {
      onChange({
        ...value,
        time_range: newRange,
        start_date: undefined,
        end_date: undefined,
      });
    }
  };

  const handleCustomRangeSubmit = () => {
    if (customStart && customEnd) {
      onChange({
        ...value,
        time_range: "custom",
        start_date: customStart,
        end_date: customEnd,
      });
      setShowCustomDialog(false);
    }
  };

  const getCurrentRangeLabel = () => {
    if (isCustomRange && value.start_date && value.end_date) {
      const startDate = new Date(value.start_date).toLocaleDateString();
      const endDate = new Date(value.end_date).toLocaleDateString();
      return `${startDate} - ${endDate}`;
    }

    const range = TIME_RANGES.find((r) => r.value === currentTimeRange);
    return range?.label || "Last 24 Hours";
  };

  const getDataFreshness = () => {
    const now = new Date();
    const lastUpdate = new Date(now.getTime() - 30000); // Mock 30 seconds ago
    const secondsAgo = Math.floor(
      (now.getTime() - lastUpdate.getTime()) / 1000,
    );

    if (secondsAgo < 60) {
      return `${secondsAgo}s ago`;
    } else if (secondsAgo < 3600) {
      return `${Math.floor(secondsAgo / 60)}m ago`;
    } else {
      return `${Math.floor(secondsAgo / 3600)}h ago`;
    }
  };

  return (
    <>
      <div
        className={`flex items-center space-x-3 ${className}`}
        data-oid="shg97dm"
      >
        {/* Time Range Selector */}
        <div className="flex items-center space-x-2" data-oid="fwwyqgj">
          <Clock className="h-4 w-4 text-muted-foreground" data-oid="e30442t" />
          <Select
            value={currentTimeRange}
            onValueChange={handleTimeRangeChange}
            data-oid="1m3jxce"
          >
            <SelectTrigger className="w-40" data-oid="avcvekt">
              <SelectValue data-oid="iaecz74" />
            </SelectTrigger>
            <SelectContent data-oid="pvlkkfh">
              {TIME_RANGES.map((range) => (
                <SelectItem
                  key={range.value}
                  value={range.value}
                  data-oid="77d:7z:"
                >
                  {range.label}
                </SelectItem>
              ))}
              <SelectItem value="custom" data-oid="urj8qn2">
                Custom Range
              </SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Current Range Display */}
        <div className="flex items-center space-x-2" data-oid="lk62d9m">
          <Badge variant="outline" className="text-xs" data-oid="i99l-o6">
            {getCurrentRangeLabel()}
          </Badge>

          {isCustomRange && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowCustomDialog(true)}
              data-oid="n_5sj0w"
            >
              <Calendar className="h-4 w-4" data-oid="0em_kgs" />
            </Button>
          )}
        </div>

        {/* Data Freshness Indicator */}
        <div className="text-xs text-muted-foreground" data-oid="xw28_0s">
          Updated {getDataFreshness()}
        </div>
      </div>

      {/* Custom Range Dialog */}
      <Dialog
        open={showCustomDialog}
        onOpenChange={setShowCustomDialog}
        data-oid="_1.6_yi"
      >
        <DialogContent className="max-w-md" data-oid="t:z.wv8">
          <DialogHeader data-oid="73_th1o">
            <DialogTitle data-oid="sdy813m">Custom Date Range</DialogTitle>
          </DialogHeader>

          <div className="space-y-4" data-oid="9wewg7o">
            <div className="grid grid-cols-2 gap-4" data-oid="mwtsx6.">
              <div className="space-y-2" data-oid="n0:m-.-">
                <Label htmlFor="start-date" data-oid="2yfv6p5">
                  Start Date
                </Label>
                <Input
                  id="start-date"
                  type="datetime-local"
                  value={customStart}
                  onChange={(e) => setCustomStart(e.target.value)}
                  data-oid="sb75jp7"
                />
              </div>

              <div className="space-y-2" data-oid="1yk052e">
                <Label htmlFor="end-date" data-oid="u7epb1q">
                  End Date
                </Label>
                <Input
                  id="end-date"
                  type="datetime-local"
                  value={customEnd}
                  onChange={(e) => setCustomEnd(e.target.value)}
                  data-oid="fsbqnvm"
                />
              </div>
            </div>

            {/* Quick Presets */}
            <div className="space-y-2" data-oid="688:n5c">
              <Label className="text-sm" data-oid="30vy-jh">
                Quick Presets
              </Label>
              <div className="flex flex-wrap gap-2" data-oid="vv1.8id">
                {[
                  { label: "Today", hours: 24 },
                  { label: "Yesterday", hours: 24, offset: 1 },
                  { label: "This Week", hours: 168 },
                  { label: "Last Week", hours: 168, offset: 1 },
                ].map((preset) => (
                  <Button
                    key={preset.label}
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      const end = new Date();
                      if (preset.offset) {
                        end.setDate(
                          end.getDate() - preset.offset * (preset.hours / 24),
                        );
                      }

                      const start = new Date(end);
                      start.setHours(start.getHours() - preset.hours);

                      setCustomStart(start.toISOString().slice(0, 16));
                      setCustomEnd(end.toISOString().slice(0, 16));
                    }}
                    data-oid="2ryjz8h"
                  >
                    {preset.label}
                  </Button>
                ))}
              </div>
            </div>
          </div>

          <DialogFooter data-oid="roea23r">
            <Button
              variant="outline"
              onClick={() => setShowCustomDialog(false)}
              data-oid="u56:bmt"
            >
              Cancel
            </Button>
            <Button
              onClick={handleCustomRangeSubmit}
              disabled={!customStart || !customEnd}
              data-oid="r:r6ks2"
            >
              Apply Range
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}

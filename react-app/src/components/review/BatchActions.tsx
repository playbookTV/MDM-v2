import { useState } from "react";
import {
  CheckCircle,
  XCircle,
  AlertTriangle,
  Loader2,
  MessageSquare,
  Users,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { useSubmitBatchReviews } from "@/hooks/useReviews";
import type { Scene, ReviewStatus } from "@/types/dataset";

interface BatchActionsProps {
  selectedScenes: Scene[];
  onClearSelection: () => void;
  className?: string;
}

export function BatchActions({
  selectedScenes,
  onClearSelection,
  className,
}: BatchActionsProps) {
  const [showDialog, setShowDialog] = useState(false);
  const [actionType, setActionType] = useState<ReviewStatus | null>(null);
  const [notes, setNotes] = useState("");

  const batchReviewMutation = useSubmitBatchReviews();

  const handleBatchAction = (status: ReviewStatus) => {
    setActionType(status);
    setShowDialog(true);
  };

  const confirmBatchAction = async () => {
    if (!actionType) return;

    try {
      await batchReviewMutation.mutateAsync({
        scene_reviews: selectedScenes.map((scene) => ({
          scene_id: scene.id,
          status: actionType,
          notes: notes || undefined,
        })),
      });

      setShowDialog(false);
      setNotes("");
      setActionType(null);
      onClearSelection();
    } catch (error) {
      // Error handled by mutation
    }
  };

  const getActionLabel = (status: ReviewStatus) => {
    switch (status) {
      case "approved":
        return "Approve";
      case "rejected":
        return "Reject";
      case "corrected":
        return "Mark as Corrected";
      default:
        return "Update";
    }
  };

  const getActionDescription = (status: ReviewStatus) => {
    switch (status) {
      case "approved":
        return "Mark all selected scenes as approved. This indicates the AI predictions are correct.";
      case "rejected":
        return "Mark all selected scenes as rejected. This indicates the AI predictions need significant correction.";
      case "corrected":
        return "Mark all selected scenes as corrected. This indicates manual corrections have been applied.";
      default:
        return "Update the review status of all selected scenes.";
    }
  };

  if (selectedScenes.length === 0) {
    return null;
  }

  return (
    <>
      <div
        className={`bg-card border rounded-lg p-4 ${className}`}
        data-oid="wqrsde9"
      >
        <div className="flex items-center justify-between" data-oid="cs9euvm">
          <div className="flex items-center space-x-3" data-oid="8:uzwfz">
            <Users className="h-5 w-5 text-primary" data-oid="7p2tz92" />
            <div data-oid="jy8ny_g">
              <div className="font-medium" data-oid="877xxsz">
                {selectedScenes.length} scene
                {selectedScenes.length !== 1 ? "s" : ""} selected
              </div>
              <div className="text-xs text-muted-foreground" data-oid="9.zm-h.">
                Perform bulk review actions
              </div>
            </div>
          </div>

          <div className="flex items-center space-x-2" data-oid="sbo-a31">
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleBatchAction("approved")}
              disabled={batchReviewMutation.isPending}
              data-oid="jzy_.dk"
            >
              <CheckCircle
                className="h-4 w-4 mr-1 text-green-600"
                data-oid="me0n8c5"
              />
              Approve All
            </Button>

            <Button
              variant="outline"
              size="sm"
              onClick={() => handleBatchAction("rejected")}
              disabled={batchReviewMutation.isPending}
              data-oid="1c2y28u"
            >
              <XCircle
                className="h-4 w-4 mr-1 text-red-600"
                data-oid="r-epmhh"
              />
              Reject All
            </Button>

            <Button
              variant="outline"
              size="sm"
              onClick={() => handleBatchAction("corrected")}
              disabled={batchReviewMutation.isPending}
              data-oid=":0hebkg"
            >
              <AlertTriangle
                className="h-4 w-4 mr-1 text-yellow-600"
                data-oid="wbw8a.z"
              />
              Mark Corrected
            </Button>

            <Button
              variant="ghost"
              size="sm"
              onClick={onClearSelection}
              disabled={batchReviewMutation.isPending}
              data-oid="sj.1ytx"
            >
              Clear Selection
            </Button>
          </div>
        </div>

        {/* Selection Summary */}
        <div className="mt-3 flex flex-wrap gap-2" data-oid="cj-ykd6">
          {getSelectionSummary(selectedScenes).map(({ status, count }) => (
            <Badge
              key={status}
              variant="outline"
              className="text-xs"
              data-oid="4keja1n"
            >
              {count} {status.replace("_", " ")}
            </Badge>
          ))}
        </div>

        {/* Progress Indicator */}
        {batchReviewMutation.isPending && (
          <div
            className="mt-3 flex items-center space-x-2 text-sm text-muted-foreground"
            data-oid="5aw85re"
          >
            <Loader2 className="h-4 w-4 animate-spin" data-oid="u.wbqar" />
            <span data-oid="z.-xw-9">Processing batch review...</span>
          </div>
        )}
      </div>

      {/* Confirmation Dialog */}
      <Dialog open={showDialog} onOpenChange={setShowDialog} data-oid="pr9l4ow">
        <DialogContent className="max-w-md" data-oid="hjc6vgo">
          <DialogHeader data-oid="e_xg3vv">
            <DialogTitle data-oid="05rc-4b">
              {actionType && getActionLabel(actionType)} {selectedScenes.length}{" "}
              Scene{selectedScenes.length !== 1 ? "s" : ""}
            </DialogTitle>
            <DialogDescription data-oid="y_1r9xd">
              {actionType && getActionDescription(actionType)}
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4" data-oid="v5ifo20">
            {/* Scene List Preview */}
            <div
              className="max-h-32 overflow-y-auto border rounded p-2"
              data-oid="_njo35z"
            >
              <div
                className="text-xs text-muted-foreground mb-2"
                data-oid="tu7u332"
              >
                Selected scenes:
              </div>
              {selectedScenes.slice(0, 5).map((scene) => (
                <div
                  key={scene.id}
                  className="text-xs py-1 truncate"
                  data-oid="c5j117x"
                >
                  {scene.source}
                </div>
              ))}
              {selectedScenes.length > 5 && (
                <div
                  className="text-xs text-muted-foreground"
                  data-oid="e_-2j1s"
                >
                  and {selectedScenes.length - 5} more...
                </div>
              )}
            </div>

            {/* Notes Input */}
            <div className="space-y-2" data-oid="b_te_v2">
              <Label htmlFor="batch-notes" data-oid="lunegij">
                Notes (optional)
              </Label>
              <Input
                id="batch-notes"
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Add notes for this batch review..."
                disabled={batchReviewMutation.isPending}
                data-oid="9_6_:s6"
              />
            </div>

            {/* Warning for Mixed Status */}
            {hasMixedStatuses(selectedScenes) && (
              <div
                className="bg-yellow-50 border border-yellow-200 rounded p-3"
                data-oid="07.gg1d"
              >
                <div className="flex items-center space-x-2" data-oid="58f_8c7">
                  <AlertTriangle
                    className="h-4 w-4 text-yellow-600"
                    data-oid="3p233e9"
                  />
                  <span className="text-sm text-yellow-800" data-oid="dfmts6g">
                    Selected scenes have different review statuses. This action
                    will override all existing reviews.
                  </span>
                </div>
              </div>
            )}
          </div>

          <DialogFooter data-oid="y1wayt-">
            <Button
              variant="outline"
              onClick={() => setShowDialog(false)}
              disabled={batchReviewMutation.isPending}
              data-oid="gnjy:g3"
            >
              Cancel
            </Button>
            <Button
              onClick={confirmBatchAction}
              disabled={batchReviewMutation.isPending}
              data-oid="xkup.aw"
            >
              {batchReviewMutation.isPending ? (
                <>
                  <Loader2
                    className="h-4 w-4 mr-2 animate-spin"
                    data-oid="2py3he2"
                  />
                  Processing...
                </>
              ) : (
                <>
                  {actionType && getActionLabel(actionType)}{" "}
                  {selectedScenes.length} Scene
                  {selectedScenes.length !== 1 ? "s" : ""}
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}

// Utility functions
function getSelectionSummary(scenes: Scene[]) {
  const statusCounts: Record<string, number> = {};

  scenes.forEach((scene) => {
    const status = scene.review_status || "pending";
    statusCounts[status] = (statusCounts[status] || 0) + 1;
  });

  return Object.entries(statusCounts).map(([status, count]) => ({
    status,
    count,
  }));
}

function hasMixedStatuses(scenes: Scene[]): boolean {
  const statuses = new Set(
    scenes.map((scene) => scene.review_status || "pending"),
  );
  return statuses.size > 1;
}

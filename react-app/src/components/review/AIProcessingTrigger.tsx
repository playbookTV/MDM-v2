import { useState } from "react";
import {
  Activity,
  Play,
  Clock,
  CheckCircle,
  AlertCircle,
  RefreshCw,
  Zap,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { useToast } from "@/components/ui/use-toast";
import type { Scene } from "@/types/dataset";

interface AIProcessingTriggerProps {
  scene: Scene;
  onProcessingComplete?: (sceneId: string) => void;
  className?: string;
}

type ProcessingStatus = "idle" | "processing" | "completed" | "error";

export function AIProcessingTrigger({
  scene,
  onProcessingComplete,
  className,
}: AIProcessingTriggerProps) {
  const [status, setStatus] = useState<ProcessingStatus>("idle");
  const [progress, setProgress] = useState(0);
  const [processingTime, setProcessingTime] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  const { toast } = useToast();

  // Check if scene needs AI processing
  const needsProcessing =
    !scene.scene_type ||
    !scene.objects ||
    scene.objects.length === 0 ||
    !scene.styles ||
    scene.styles.length === 0;

  const triggerAIProcessing = async () => {
    setStatus("processing");
    setProgress(0);
    setError(null);
    const startTime = Date.now();

    try {
      // Start the processing job
      const processResponse = await fetch(
        `/api/v1/scenes/${scene.id}/process`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            force_reprocess: true,
          }),
        },
      );

      if (!processResponse.ok) {
        throw new Error(`Processing failed: ${processResponse.statusText}`);
      }

      const processResult = await processResponse.json();
      const jobId = processResult.job_id;

      if (!jobId) {
        throw new Error("No job ID returned from processing request");
      }

      // Poll for progress updates
      const pollProgress = async (): Promise<void> => {
        const statusResponse = await fetch(
          `/api/v1/scenes/${scene.id}/process-status`,
        );

        if (!statusResponse.ok) {
          throw new Error("Failed to get processing status");
        }

        const statusData = await statusResponse.json();

        // Update progress from real job status
        setProgress(statusData.progress || 0);

        if (statusData.status === "succeeded") {
          // Verify that processed data is actually available before showing success
          try {
            const verifyResponse = await fetch(`/api/v1/scenes/${scene.id}`);
            if (!verifyResponse.ok) {
              throw new Error("Failed to verify processed data");
            }
            
            const updatedScene = await verifyResponse.json();
            
            // Check that processing actually completed by verifying we have the expected data
            const hasProcessedData = updatedScene.scene_type && 
              updatedScene.objects && updatedScene.objects.length > 0;
            
            if (!hasProcessedData) {
              // Data not yet available, continue polling
              setTimeout(pollProgress, 1000);
              return;
            }
          } catch (err) {
            // If verification fails, continue polling
            setTimeout(pollProgress, 1000);
            return;
          }

          setProgress(100);
          const endTime = Date.now();
          setProcessingTime((endTime - startTime) / 1000);
          setStatus("completed");

          // Show success toast
          toast({
            title: "AI Processing Complete!",
            description: `Scene analyzed in ${((endTime - startTime) / 1000).toFixed(1)}s`,
            duration: 5000,
          });

          // Notify parent component with the updated scene data
          onProcessingComplete?.(scene.id);

          // Auto-reset after 3 seconds
          setTimeout(() => {
            setStatus("idle");
            setProgress(0);
            setProcessingTime(null);
          }, 3000);
        } else if (statusData.status === "failed") {
          throw new Error(statusData.error || "Processing failed");
        } else if (
          statusData.status === "running" ||
          statusData.status === "pending"
        ) {
          // Continue polling
          setTimeout(pollProgress, 1000);
        }
      };

      // Start polling for progress
      setTimeout(pollProgress, 1000);
    } catch (err) {
      setStatus("error");
      setError(err instanceof Error ? err.message : "Processing failed");

      toast({
        title: "Processing Failed",
        description: "Failed to process scene with AI models",
        variant: "destructive",
        duration: 5000,
      });
    }
  };

  const getStatusIcon = () => {
    switch (status) {
      case "processing":
        return (
          <RefreshCw className="h-4 w-4 animate-spin" data-oid="yp4:nfg" />
        );

      case "completed":
        return (
          <CheckCircle className="h-4 w-4 text-green-600" data-oid="vg_qjv-" />
        );

      case "error":
        return (
          <AlertCircle className="h-4 w-4 text-red-600" data-oid="ee3n6tr" />
        );

      default:
        return <Activity className="h-4 w-4" data-oid="dxhr9lh" />;
    }
  };

  const getStatusBadge = () => {
    switch (status) {
      case "processing":
        return (
          <Badge variant="default" className="animate-pulse" data-oid="2h65j2z">
            Processing
          </Badge>
        );

      case "completed":
        return (
          <Badge variant="secondary" data-oid="krzkczz">
            Completed
          </Badge>
        );

      case "error":
        return (
          <Badge variant="destructive" data-oid="gyb98l2">
            Failed
          </Badge>
        );

      default:
        return needsProcessing ? (
          <Badge variant="outline" data-oid="4bx5e2o">
            Needs Processing
          </Badge>
        ) : (
          <Badge variant="secondary" data-oid="r77nv3.">
            Processed
          </Badge>
        );
    }
  };

  return (
    <Card className={className} data-oid="rfo81v6">
      <CardHeader className="pb-3" data-oid="dvryyn4">
        <CardTitle
          className="flex items-center justify-between text-base"
          data-oid="e9s7u6c"
        >
          <div className="flex items-center space-x-2" data-oid="k9p17qh">
            {getStatusIcon()}
            <span data-oid="l_a-8:j">AI Processing</span>
          </div>
          {getStatusBadge()}
        </CardTitle>
      </CardHeader>

      <CardContent className="space-y-4" data-oid="e25gxrp">
        {status === "idle" && (
          <>
            {needsProcessing ? (
              <div className="space-y-3" data-oid="rka1cmw">
                <Alert data-oid="xs:0g_x">
                  <Zap className="h-4 w-4" data-oid="ub50wkm" />
                  <AlertDescription data-oid="-vejpnr">
                    This scene needs AI analysis to extract comprehensive
                    metadata.
                  </AlertDescription>
                </Alert>

                <Button
                  onClick={triggerAIProcessing}
                  className="w-full"
                  size="sm"
                  data-oid="yuwtaah"
                >
                  <Play className="h-4 w-4 mr-2" data-oid="hvl-hng" />
                  Run AI Analysis
                </Button>

                <div
                  className="text-xs text-muted-foreground"
                  data-oid="mn54cjk"
                >
                  <p data-oid="dvohcb7">Will analyze:</p>
                  <ul
                    className="mt-1 space-y-1 list-disc list-inside"
                    data-oid="udtsc5f"
                  >
                    <li data-oid="e6ilren">Scene type classification</li>
                    <li data-oid="66w6hfs">Object detection & segmentation</li>
                    <li data-oid="v8uif2b">Interior design style analysis</li>
                    <li data-oid="zi965fl">Material identification</li>
                    <li data-oid="5ly41bf">Color palette extraction</li>
                    <li data-oid="06bfb7s">Depth map generation</li>
                  </ul>
                </div>
              </div>
            ) : (
              <div className="text-center py-4" data-oid="lx1v99s">
                <CheckCircle
                  className="h-8 w-8 mx-auto mb-2 text-green-600"
                  data-oid="dujz_ko"
                />

                <p className="text-sm font-medium" data-oid="jen_wub">
                  Scene Already Processed
                </p>
                <p
                  className="text-xs text-muted-foreground mt-1"
                  data-oid="hi-.vjj"
                >
                  All AI analysis completed
                </p>

                <Button
                  variant="outline"
                  size="sm"
                  onClick={triggerAIProcessing}
                  className="mt-2"
                  data-oid="msymh_m"
                >
                  <RefreshCw className="h-4 w-4 mr-2" data-oid=".vao13g" />
                  Reprocess
                </Button>
              </div>
            )}
          </>
        )}

        {status === "processing" && (
          <div className="space-y-3" data-oid="21a6rj8">
            <div className="text-center" data-oid="x7o2eit">
              <div
                className="w-12 h-12 mx-auto mb-3 relative"
                data-oid="l:2vn9h"
              >
                <Activity
                  className="h-12 w-12 text-primary animate-pulse"
                  data-oid="deuxksr"
                />
              </div>
              <p className="text-sm font-medium" data-oid="0x6ppxc">
                Processing Scene...
              </p>
              <p className="text-xs text-muted-foreground" data-oid="qcx:sfc">
                Running AI models on RunPod GPU
              </p>
            </div>

            <div className="space-y-2" data-oid="1n:puio">
              <div className="flex justify-between text-xs" data-oid="g7ae1z9">
                <span data-oid="k6y7q-.">Progress</span>
                <span data-oid="p4mkofe">{Math.round(progress)}%</span>
              </div>
              <Progress
                value={progress}
                className="w-full"
                data-oid="uadog2t"
              />
            </div>

            <div
              className="text-xs text-muted-foreground text-center"
              data-oid="5aonzwg"
            >
              Expected time: ~2-3 seconds
            </div>
          </div>
        )}

        {status === "completed" && processingTime && (
          <div className="text-center space-y-2" data-oid="v8:g_za">
            <CheckCircle
              className="h-8 w-8 mx-auto text-green-600"
              data-oid="odfmc81"
            />

            <div data-oid="-m-0mc:">
              <p
                className="text-sm font-medium text-green-600"
                data-oid="y4p3wa_"
              >
                Processing Complete!
              </p>
              <p className="text-xs text-muted-foreground" data-oid="m_i7172">
                Completed in {processingTime.toFixed(1)}s
              </p>
            </div>
            <Badge variant="secondary" className="text-xs" data-oid="zv7:rs0">
              <Clock className="h-3 w-3 mr-1" data-oid="07qb7mw" />
              Fast Processing
            </Badge>
          </div>
        )}

        {status === "error" && error && (
          <Alert variant="destructive" data-oid="sc40qof">
            <AlertCircle className="h-4 w-4" data-oid=".o.v1v1" />
            <AlertDescription className="text-sm" data-oid="a.k6i06">
              {error}
            </AlertDescription>
          </Alert>
        )}
      </CardContent>
    </Card>
  );
}

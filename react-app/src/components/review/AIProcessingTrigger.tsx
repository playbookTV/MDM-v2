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

          // Notify parent component
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
          <RefreshCw className="h-4 w-4 animate-spin" data-oid="0x5kc18" />
        );
      case "completed":
        return (
          <CheckCircle className="h-4 w-4 text-green-600" data-oid="lwenrem" />
        );
      case "error":
        return (
          <AlertCircle className="h-4 w-4 text-red-600" data-oid="am.8hqy" />
        );
      default:
        return <Activity className="h-4 w-4" data-oid="zbg.kv7" />;
    }
  };

  const getStatusBadge = () => {
    switch (status) {
      case "processing":
        return (
          <Badge variant="default" className="animate-pulse" data-oid="td5sbvh">
            Processing
          </Badge>
        );
      case "completed":
        return (
          <Badge variant="secondary" data-oid=".h2fw_3">
            Completed
          </Badge>
        );
      case "error":
        return (
          <Badge variant="destructive" data-oid="q0uvk5d">
            Failed
          </Badge>
        );
      default:
        return needsProcessing ? (
          <Badge variant="outline" data-oid="y1w_6d1">
            Needs Processing
          </Badge>
        ) : (
          <Badge variant="secondary" data-oid="q1c.vvd">
            Processed
          </Badge>
        );
    }
  };

  return (
    <Card className={className} data-oid="rde8d9g">
      <CardHeader className="pb-3" data-oid="otwwnol">
        <CardTitle
          className="flex items-center justify-between text-base"
          data-oid="6co82au"
        >
          <div className="flex items-center space-x-2" data-oid="jtxwizu">
            {getStatusIcon()}
            <span data-oid="s9vink9">AI Processing</span>
          </div>
          {getStatusBadge()}
        </CardTitle>
      </CardHeader>

      <CardContent className="space-y-4" data-oid="zfo46fl">
        {status === "idle" && (
          <>
            {needsProcessing ? (
              <div className="space-y-3" data-oid=":6u:cxt">
                <Alert data-oid="9.yo2nx">
                  <Zap className="h-4 w-4" data-oid="x238s.s" />
                  <AlertDescription data-oid="wfl9:qv">
                    This scene needs AI analysis to extract comprehensive
                    metadata.
                  </AlertDescription>
                </Alert>

                <Button
                  onClick={triggerAIProcessing}
                  className="w-full"
                  size="sm"
                  data-oid="vm:enhg"
                >
                  <Play className="h-4 w-4 mr-2" data-oid="v6o6rhs" />
                  Run AI Analysis
                </Button>

                <div
                  className="text-xs text-muted-foreground"
                  data-oid="aejibuw"
                >
                  <p data-oid="cl6gd_x">Will analyze:</p>
                  <ul
                    className="mt-1 space-y-1 list-disc list-inside"
                    data-oid="v9-ed49"
                  >
                    <li data-oid="0mlqoe.">Scene type classification</li>
                    <li data-oid="t300hw4">Object detection & segmentation</li>
                    <li data-oid="mq4_gd6">Interior design style analysis</li>
                    <li data-oid="7l.fzui">Material identification</li>
                    <li data-oid="5zg3.8-">Color palette extraction</li>
                    <li data-oid="f8ij0-5">Depth map generation</li>
                  </ul>
                </div>
              </div>
            ) : (
              <div className="text-center py-4" data-oid="j.u:lua">
                <CheckCircle
                  className="h-8 w-8 mx-auto mb-2 text-green-600"
                  data-oid="hwnh8x6"
                />
                <p className="text-sm font-medium" data-oid="km0e5s3">
                  Scene Already Processed
                </p>
                <p
                  className="text-xs text-muted-foreground mt-1"
                  data-oid="ht0kzgd"
                >
                  All AI analysis completed
                </p>

                <Button
                  variant="outline"
                  size="sm"
                  onClick={triggerAIProcessing}
                  className="mt-2"
                  data-oid="hon9z3k"
                >
                  <RefreshCw className="h-4 w-4 mr-2" data-oid="pqiaj2s" />
                  Reprocess
                </Button>
              </div>
            )}
          </>
        )}

        {status === "processing" && (
          <div className="space-y-3" data-oid="bt79bk7">
            <div className="text-center" data-oid="8wn_ype">
              <div
                className="w-12 h-12 mx-auto mb-3 relative"
                data-oid="vm:39bd"
              >
                <Activity
                  className="h-12 w-12 text-primary animate-pulse"
                  data-oid="3c770uv"
                />
              </div>
              <p className="text-sm font-medium" data-oid="c0lsp2g">
                Processing Scene...
              </p>
              <p className="text-xs text-muted-foreground" data-oid="gng5ptw">
                Running AI models on RunPod GPU
              </p>
            </div>

            <div className="space-y-2" data-oid="lhxd.5u">
              <div className="flex justify-between text-xs" data-oid="b284xy8">
                <span data-oid="bfgq4a.">Progress</span>
                <span data-oid="ft:ukdv">{Math.round(progress)}%</span>
              </div>
              <Progress
                value={progress}
                className="w-full"
                data-oid="tlpiivs"
              />
            </div>

            <div
              className="text-xs text-muted-foreground text-center"
              data-oid="0q9dtx9"
            >
              Expected time: ~2-3 seconds
            </div>
          </div>
        )}

        {status === "completed" && processingTime && (
          <div className="text-center space-y-2" data-oid="bv--g6k">
            <CheckCircle
              className="h-8 w-8 mx-auto text-green-600"
              data-oid="t:38u1u"
            />
            <div data-oid="xs6c4ph">
              <p
                className="text-sm font-medium text-green-600"
                data-oid="etck7-7"
              >
                Processing Complete!
              </p>
              <p className="text-xs text-muted-foreground" data-oid="k8yhw-n">
                Completed in {processingTime.toFixed(1)}s
              </p>
            </div>
            <Badge variant="secondary" className="text-xs" data-oid="68h4bi:">
              <Clock className="h-3 w-3 mr-1" data-oid="n2k05ml" />
              Fast Processing
            </Badge>
          </div>
        )}

        {status === "error" && error && (
          <Alert variant="destructive" data-oid="h45x3p6">
            <AlertCircle className="h-4 w-4" data-oid="ltjx8li" />
            <AlertDescription className="text-sm" data-oid="w-r8xpr">
              {error}
            </AlertDescription>
          </Alert>
        )}
      </CardContent>
    </Card>
  );
}

import { useState } from "react";
import { ExternalLink, AlertCircle, CheckCircle, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useCreateDataset } from "@/hooks/useDatasets";
import type { DatasetCreate } from "@/types/dataset";

interface HFImportModalProps {
  open: boolean;
  onClose: () => void;
}

const HF_URL_PATTERN =
  /^https:\/\/huggingface\.co\/datasets\/[\w-]+\/[\w-]+(?:\/.*)?$/;

export function HFImportModal({ open, onClose }: HFImportModalProps) {
  const [formData, setFormData] = useState<
    DatasetCreate & { source_url: string }
  >({
    name: "",
    version: "v1.0",
    source_url: "",
    license: "",
    notes: "",
  });
  const [urlError, setUrlError] = useState<string | null>(null);
  const [isValidating, setIsValidating] = useState(false);

  const createMutation = useCreateDataset();

  const validateHuggingFaceUrl = async (url: string) => {
    if (!url) {
      setUrlError(null);
      return false;
    }

    if (!HF_URL_PATTERN.test(url)) {
      setUrlError("Please enter a valid HuggingFace dataset URL");
      return false;
    }

    setIsValidating(true);
    setUrlError(null);

    try {
      // Extract dataset name from URL for pre-filling form
      const urlMatch = url.match(/datasets\/([\w-]+)\/([\w-]+)/);
      if (urlMatch) {
        const [, org, datasetName] = urlMatch;
        setFormData((prev) => ({
          ...prev,
          name: prev.name || `${org}/${datasetName}`,
        }));
      }

      // In a real implementation, you might want to validate the URL
      // by checking if it exists or fetching metadata
      // For now, we'll just validate the URL format
      setIsValidating(false);
      return true;
    } catch (error) {
      setUrlError("Failed to validate dataset URL");
      setIsValidating(false);
      return false;
    }
  };

  const handleUrlChange = (url: string) => {
    setFormData((prev) => ({ ...prev, source_url: url }));

    // Debounce URL validation
    const timeoutId = setTimeout(() => {
      validateHuggingFaceUrl(url);
    }, 500);

    return () => clearTimeout(timeoutId);
  };

  const handleSubmit = async () => {
    if (!formData.name.trim() || !formData.source_url.trim()) return;

    const isValidUrl = await validateHuggingFaceUrl(formData.source_url);
    if (!isValidUrl) return;

    try {
      await createMutation.mutateAsync({
        name: formData.name,
        version: formData.version,
        source_url: formData.source_url,
        license: formData.license || undefined,
        notes: formData.notes || undefined,
      });

      onClose();
      resetForm();
    } catch (error) {
      // Error is handled by the mutation
    }
  };

  const resetForm = () => {
    setFormData({
      name: "",
      version: "v1.0",
      source_url: "",
      license: "",
      notes: "",
    });
    setUrlError(null);
    setIsValidating(false);
  };

  const handleClose = () => {
    if (createMutation.isPending) return;
    onClose();
    resetForm();
  };

  const canSubmit =
    formData.name.trim() &&
    formData.source_url.trim() &&
    !urlError &&
    !isValidating &&
    !createMutation.isPending;

  return (
    <Dialog open={open} onOpenChange={handleClose} data-oid="1dwdrc9">
      <DialogContent className="max-w-lg" data-oid="j4170a4">
        <div data-oid="31c008f">
          <DialogHeader data-oid="_udp_vx">
            <DialogTitle data-oid="ri.9-6k">
              Import from HuggingFace
            </DialogTitle>
            <DialogDescription data-oid="eyq3p7-">
              Import a dataset directly from HuggingFace Hub.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4" data-oid="hrh9jlv">
            {/* HuggingFace URL */}
            <div className="space-y-2" data-oid="xv2k-u4">
              <Label htmlFor="hf-url" data-oid="3l0x8e5">
                HuggingFace Dataset URL *
              </Label>
              <div className="relative" data-oid="qd5ktgq">
                <Input
                  id="hf-url"
                  value={formData.source_url}
                  onChange={(e) => handleUrlChange(e.target.value)}
                  placeholder="https://huggingface.co/datasets/username/dataset-name"
                  disabled={createMutation.isPending}
                  className={urlError ? "border-destructive" : ""}
                  data-oid="ric5omq"
                />

                <div
                  className="absolute right-3 top-1/2 -translate-y-1/2"
                  data-oid="l9bifpi"
                >
                  {isValidating && (
                    <Loader2
                      className="h-4 w-4 animate-spin"
                      data-oid="pez4kki"
                    />
                  )}
                  {!isValidating && formData.source_url && !urlError && (
                    <CheckCircle
                      className="h-4 w-4 text-green-500"
                      data-oid="mv-4y_x"
                    />
                  )}
                </div>
              </div>
              {urlError && (
                <div
                  className="flex items-center space-x-1 text-sm text-destructive"
                  data-oid="u4bsp37"
                >
                  <AlertCircle className="h-3 w-3" data-oid="n9fafl3" />
                  <span data-oid="whm2aja">{urlError}</span>
                </div>
              )}
              <p
                className="text-xs text-muted-foreground flex items-center space-x-1"
                data-oid="cjp0yj8"
              >
                <ExternalLink className="h-3 w-3" data-oid="zci7jaw" />
                <span data-oid="xnfw.q-">
                  Browse datasets at huggingface.co/datasets
                </span>
              </p>
            </div>

            {/* Dataset Metadata */}
            <div className="grid grid-cols-2 gap-4" data-oid="_9-fl98">
              <div className="space-y-2" data-oid="ucszgsp">
                <Label htmlFor="name" data-oid="ctqc1gl">
                  Dataset Name *
                </Label>
                <Input
                  id="name"
                  value={formData.name}
                  onChange={(e) =>
                    setFormData((prev) => ({ ...prev, name: e.target.value }))
                  }
                  placeholder="living-rooms-hf"
                  disabled={createMutation.isPending}
                  data-oid="cwbvp1l"
                />
              </div>
              <div className="space-y-2" data-oid="lb:mjoh">
                <Label htmlFor="version" data-oid="36.81_t">
                  Version
                </Label>
                <Input
                  id="version"
                  value={formData.version}
                  onChange={(e) =>
                    setFormData((prev) => ({
                      ...prev,
                      version: e.target.value,
                    }))
                  }
                  placeholder="v1.0"
                  disabled={createMutation.isPending}
                  data-oid="fwr_jc5"
                />
              </div>
            </div>

            <div className="space-y-2" data-oid="am4dr_:">
              <Label htmlFor="license" data-oid="mn3r0_2">
                License (optional)
              </Label>
              <Input
                id="license"
                value={formData.license}
                onChange={(e) =>
                  setFormData((prev) => ({ ...prev, license: e.target.value }))
                }
                placeholder="Will be auto-detected from HuggingFace"
                disabled={createMutation.isPending}
                data-oid="jv_m.p0"
              />
            </div>

            <div className="space-y-2" data-oid="1wzo7-a">
              <Label htmlFor="notes" data-oid="9a646f0">
                Notes (optional)
              </Label>
              <Input
                id="notes"
                value={formData.notes}
                onChange={(e) =>
                  setFormData((prev) => ({ ...prev, notes: e.target.value }))
                }
                placeholder="Imported from HuggingFace"
                disabled={createMutation.isPending}
                data-oid="hja3rc6"
              />
            </div>

            {/* Info Box */}
            <div className="bg-muted p-3 rounded-md" data-oid="vbol__d">
              <p className="text-sm text-muted-foreground" data-oid="66dl-z-">
                <strong data-oid="r-io4s3">Note:</strong> After importing,
                you'll need to run a processing job to download and analyze the
                images from HuggingFace.
              </p>
            </div>

            {/* Error Display */}
            {createMutation.error && (
              <div
                className="bg-destructive/10 border border-destructive/20 rounded-md p-3"
                data-oid="q3d.o4l"
              >
                <div className="flex items-center space-x-2" data-oid="s63qak:">
                  <AlertCircle
                    className="h-4 w-4 text-destructive"
                    data-oid="gcgilpd"
                  />

                  <span className="text-sm text-destructive" data-oid="x8fejje">
                    {(createMutation.error as Error)?.message ||
                      "An error occurred during import"}
                  </span>
                </div>
              </div>
            )}
          </div>

          <DialogFooter data-oid="k2itaj5">
            <Button
              variant="outline"
              onClick={handleClose}
              disabled={createMutation.isPending}
              data-oid="lztc:f_"
            >
              Cancel
            </Button>
            <Button
              onClick={handleSubmit}
              disabled={!canSubmit}
              data-oid="x-_1_-j"
            >
              {createMutation.isPending ? (
                <>
                  <Loader2
                    className="h-4 w-4 mr-2 animate-spin"
                    data-oid="42nr-a:"
                  />
                  Importing...
                </>
              ) : (
                "Import Dataset"
              )}
            </Button>
          </DialogFooter>
        </div>
      </DialogContent>
    </Dialog>
  );
}

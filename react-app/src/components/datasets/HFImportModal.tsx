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
    <Dialog open={open} onOpenChange={handleClose} data-oid="2jqb:uw">
      <DialogContent className="max-w-lg" data-oid="8hlm-d1">
        <div data-oid="4z0gusk">
          <DialogHeader data-oid="2dtaf0p">
            <DialogTitle data-oid=":8zk1:t">
              Import from HuggingFace
            </DialogTitle>
            <DialogDescription data-oid="dzmyi-d">
              Import a dataset directly from HuggingFace Hub.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4" data-oid="mhykkab">
            {/* HuggingFace URL */}
            <div className="space-y-2" data-oid="37z9kqj">
              <Label htmlFor="hf-url" data-oid="4w28037">
                HuggingFace Dataset URL *
              </Label>
              <div className="relative" data-oid="r79u0dd">
                <Input
                  id="hf-url"
                  value={formData.source_url}
                  onChange={(e) => handleUrlChange(e.target.value)}
                  placeholder="https://huggingface.co/datasets/username/dataset-name"
                  disabled={createMutation.isPending}
                  className={urlError ? "border-destructive" : ""}
                  data-oid="jc6b99x"
                />

                <div
                  className="absolute right-3 top-1/2 -translate-y-1/2"
                  data-oid="vv8g10r"
                >
                  {isValidating && (
                    <Loader2
                      className="h-4 w-4 animate-spin"
                      data-oid="jey-f-5"
                    />
                  )}
                  {!isValidating && formData.source_url && !urlError && (
                    <CheckCircle
                      className="h-4 w-4 text-green-500"
                      data-oid="fklzg.u"
                    />
                  )}
                </div>
              </div>
              {urlError && (
                <div
                  className="flex items-center space-x-1 text-sm text-destructive"
                  data-oid="ahfzzd5"
                >
                  <AlertCircle className="h-3 w-3" data-oid="ae5zv.m" />
                  <span data-oid="9ab12b_">{urlError}</span>
                </div>
              )}
              <p
                className="text-xs text-muted-foreground flex items-center space-x-1"
                data-oid=".92sjo7"
              >
                <ExternalLink className="h-3 w-3" data-oid="w2abcbw" />
                <span data-oid=".79pb8o">
                  Browse datasets at huggingface.co/datasets
                </span>
              </p>
            </div>

            {/* Dataset Metadata */}
            <div className="grid grid-cols-2 gap-4" data-oid=":zn9f6y">
              <div className="space-y-2" data-oid="0xmgipv">
                <Label htmlFor="name" data-oid="8a3o3jd">
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
                  data-oid="fiahaja"
                />
              </div>
              <div className="space-y-2" data-oid="1gnl.g.">
                <Label htmlFor="version" data-oid="71cst92">
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
                  data-oid="j0-a8or"
                />
              </div>
            </div>

            <div className="space-y-2" data-oid="vi_.2m8">
              <Label htmlFor="license" data-oid="8ysw6y1">
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
                data-oid="eau7o21"
              />
            </div>

            <div className="space-y-2" data-oid="iqcj:r3">
              <Label htmlFor="notes" data-oid="hjwhcty">
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
                data-oid="w_n1cn-"
              />
            </div>

            {/* Info Box */}
            <div className="bg-muted p-3 rounded-md" data-oid="_ohajz0">
              <p className="text-sm text-muted-foreground" data-oid="jqc--w3">
                <strong data-oid="7pjr3k-">Note:</strong> After importing,
                you'll need to run a processing job to download and analyze the
                images from HuggingFace.
              </p>
            </div>

            {/* Error Display */}
            {createMutation.error && (
              <div
                className="bg-destructive/10 border border-destructive/20 rounded-md p-3"
                data-oid="43vt4ko"
              >
                <div className="flex items-center space-x-2" data-oid=".phkiga">
                  <AlertCircle
                    className="h-4 w-4 text-destructive"
                    data-oid="5qjaos5"
                  />
                  <span className="text-sm text-destructive" data-oid="kj:y6g5">
                    {(createMutation.error as Error)?.message ||
                      "An error occurred during import"}
                  </span>
                </div>
              </div>
            )}
          </div>

          <DialogFooter data-oid="lu6p:x-">
            <Button
              variant="outline"
              onClick={handleClose}
              disabled={createMutation.isPending}
              data-oid="aba5-.j"
            >
              Cancel
            </Button>
            <Button
              onClick={handleSubmit}
              disabled={!canSubmit}
              data-oid="byq9ay9"
            >
              {createMutation.isPending ? (
                <>
                  <Loader2
                    className="h-4 w-4 mr-2 animate-spin"
                    data-oid="qhwh7lb"
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

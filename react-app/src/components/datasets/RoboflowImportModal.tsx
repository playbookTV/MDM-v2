import { useState } from "react";
import { ExternalLink, AlertCircle, CheckCircle, Loader2, Eye, EyeOff } from "lucide-react";
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
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useCreateDataset } from "@/hooks/useDatasets";
import type { DatasetCreate } from "@/types/dataset";

interface RoboflowImportModalProps {
  open: boolean;
  onClose: () => void;
}

const ROBOFLOW_URL_PATTERN =
  /^https:\/\/universe\.roboflow\.com\/([\w-]+)\/([\w-]+)(?:\/model\/(\d+))?(?:\/.*)?$/;

const EXPORT_FORMATS = [
  { value: "coco", label: "COCO JSON", description: "Standard object detection format" },
  { value: "yolov8", label: "YOLOv8", description: "YOLO training format" },
  { value: "yolov5pytorch", label: "YOLOv5 PyTorch", description: "YOLO PyTorch format" },
];

export function RoboflowImportModal({ open, onClose }: RoboflowImportModalProps) {
  const [formData, setFormData] = useState<
    DatasetCreate & { 
      source_url: string;
      api_key: string;
      export_format: string;
      max_images?: number;
    }
  >({
    name: "",
    version: "v1.0",
    source_url: "",
    api_key: "",
    export_format: "coco",
    max_images: undefined,
    license: "",
    notes: "",
  });
  
  const [urlError, setUrlError] = useState<string | null>(null);
  const [isValidating, setIsValidating] = useState(false);
  const [showApiKey, setShowApiKey] = useState(false);

  const createMutation = useCreateDataset();

  const validateRoboflowUrl = async (url: string) => {
    if (!url) {
      setUrlError(null);
      return false;
    }

    if (!ROBOFLOW_URL_PATTERN.test(url)) {
      setUrlError("Please enter a valid Roboflow Universe URL");
      return false;
    }

    setIsValidating(true);
    setUrlError(null);

    try {
      // Extract dataset name from URL for pre-filling form
      const urlMatch = url.match(ROBOFLOW_URL_PATTERN);
      if (urlMatch) {
        const [, workspace, project, version] = urlMatch;
        setFormData((prev) => ({
          ...prev,
          name: prev.name || `${workspace}/${project}`,
          version: prev.version === "v1.0" ? `v${version || "1"}` : prev.version,
        }));
      }

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
      validateRoboflowUrl(url);
    }, 500);

    return () => clearTimeout(timeoutId);
  };

  const handleSubmit = async () => {
    if (!formData.name.trim() || !formData.source_url.trim() || !formData.api_key.trim()) return;

    const isValidUrl = await validateRoboflowUrl(formData.source_url);
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
      api_key: "",
      export_format: "coco",
      max_images: undefined,
      license: "",
      notes: "",
    });
    setUrlError(null);
    setIsValidating(false);
    setShowApiKey(false);
  };

  const handleClose = () => {
    if (createMutation.isPending) return;
    onClose();
    resetForm();
  };

  const canSubmit =
    formData.name.trim() &&
    formData.source_url.trim() &&
    formData.api_key.trim() &&
    !urlError &&
    !isValidating &&
    !createMutation.isPending;

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>Import from Roboflow Universe</DialogTitle>
          <DialogDescription>
            Import a dataset directly from Roboflow Universe with rich annotations.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {/* Roboflow URL */}
          <div className="space-y-2">
            <Label htmlFor="roboflow-url">Roboflow Universe URL *</Label>
            <div className="relative">
              <Input
                id="roboflow-url"
                value={formData.source_url}
                onChange={(e) => handleUrlChange(e.target.value)}
                placeholder="https://universe.roboflow.com/workspace/project/model/version"
                disabled={createMutation.isPending}
                className={urlError ? "border-destructive" : ""}
              />

              <div className="absolute right-3 top-1/2 -translate-y-1/2">
                {isValidating && (
                  <Loader2 className="h-4 w-4 animate-spin" />
                )}
                {!isValidating && formData.source_url && !urlError && (
                  <CheckCircle className="h-4 w-4 text-green-500" />
                )}
              </div>
            </div>
            {urlError && (
              <div className="flex items-center space-x-1 text-sm text-destructive">
                <AlertCircle className="h-3 w-3" />
                <span>{urlError}</span>
              </div>
            )}
            <p className="text-xs text-muted-foreground flex items-center space-x-1">
              <ExternalLink className="h-3 w-3" />
              <span>Browse datasets at universe.roboflow.com</span>
            </p>
          </div>

          {/* API Key */}
          <div className="space-y-2">
            <Label htmlFor="api-key">Roboflow API Key *</Label>
            <div className="relative">
              <Input
                id="api-key"
                type={showApiKey ? "text" : "password"}
                value={formData.api_key}
                onChange={(e) =>
                  setFormData((prev) => ({ ...prev, api_key: e.target.value }))
                }
                placeholder="Your Roboflow API key"
                disabled={createMutation.isPending}
              />
              <Button
                type="button"
                variant="ghost"
                size="sm"
                className="absolute right-1 top-1/2 -translate-y-1/2 h-8 w-8 p-0"
                onClick={() => setShowApiKey(!showApiKey)}
              >
                {showApiKey ? (
                  <EyeOff className="h-4 w-4" />
                ) : (
                  <Eye className="h-4 w-4" />
                )}
              </Button>
            </div>
            <p className="text-xs text-muted-foreground">
              Get your API key from your Roboflow Account settings
            </p>
          </div>

          {/* Dataset Metadata */}
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="name">Dataset Name *</Label>
              <Input
                id="name"
                value={formData.name}
                onChange={(e) =>
                  setFormData((prev) => ({ ...prev, name: e.target.value }))
                }
                placeholder="furniture-roboflow"
                disabled={createMutation.isPending}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="version">Version</Label>
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
              />
            </div>
          </div>

          {/* Export Format */}
          <div className="space-y-2">
            <Label htmlFor="export-format">Export Format</Label>
            <Select
              value={formData.export_format}
              onValueChange={(value) =>
                setFormData((prev) => ({ ...prev, export_format: value }))
              }
              disabled={createMutation.isPending}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {EXPORT_FORMATS.map((format) => (
                  <SelectItem key={format.value} value={format.value}>
                    <div>
                      <div className="font-medium">{format.label}</div>
                      <div className="text-xs text-muted-foreground">{format.description}</div>
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Max Images */}
          <div className="space-y-2">
            <Label htmlFor="max-images">Max Images (optional)</Label>
            <Input
              id="max-images"
              type="number"
              value={formData.max_images || ""}
              onChange={(e) =>
                setFormData((prev) => ({
                  ...prev,
                  max_images: e.target.value ? parseInt(e.target.value) : undefined,
                }))
              }
              placeholder="Leave empty to import all images"
              disabled={createMutation.isPending}
              min="1"
              max="10000"
            />
            <p className="text-xs text-muted-foreground">
              Limit for testing or large datasets (recommended: 100-500 for first import)
            </p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="license">License (optional)</Label>
            <Input
              id="license"
              value={formData.license}
              onChange={(e) =>
                setFormData((prev) => ({ ...prev, license: e.target.value }))
              }
              placeholder="Will be auto-detected from Roboflow"
              disabled={createMutation.isPending}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="notes">Notes (optional)</Label>
            <Input
              id="notes"
              value={formData.notes}
              onChange={(e) =>
                setFormData((prev) => ({ ...prev, notes: e.target.value }))
              }
              placeholder="Imported from Roboflow Universe"
              disabled={createMutation.isPending}
            />
          </div>

          {/* Info Box */}
          <div className="bg-muted p-3 rounded-md">
            <p className="text-sm text-muted-foreground">
              <strong>Note:</strong> After importing, you'll need to run a processing job to download 
              and analyze the images from Roboflow. Existing annotations will be preserved and used to 
              skip redundant AI processing.
            </p>
          </div>

          {/* Error Display */}
          {createMutation.error && (
            <div className="bg-destructive/10 border border-destructive/20 rounded-md p-3">
              <div className="flex items-center space-x-2">
                <AlertCircle className="h-4 w-4 text-destructive" />
                <span className="text-sm text-destructive">
                  {(createMutation.error as Error)?.message ||
                    "An error occurred during import"}
                </span>
              </div>
            </div>
          )}
        </div>

        <DialogFooter>
          <Button
            variant="outline"
            onClick={handleClose}
            disabled={createMutation.isPending}
          >
            Cancel
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={!canSubmit}
          >
            {createMutation.isPending ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Importing...
              </>
            ) : (
              "Import Dataset"
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
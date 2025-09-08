import { useState, useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { Upload, X, FileImage, AlertCircle, CheckCircle } from "lucide-react";
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
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { useUploadDataset } from "@/hooks/useDatasets";
import type { DatasetCreate } from "@/types/dataset";

interface DatasetUploadModalProps {
  open: boolean;
  onClose: () => void;
}

interface FileWithStatus extends File {
  id: string;
  status: "pending" | "uploading" | "success" | "error";
  error?: string;
}

export function DatasetUploadModal({ open, onClose }: DatasetUploadModalProps) {
  const [files, setFiles] = useState<FileWithStatus[]>([]);
  const [formData, setFormData] = useState<DatasetCreate>({
    name: "",
    version: "v1.0",
    license: "CC BY 4.0",
    notes: "",
  });

  const uploadMutation = useUploadDataset();

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const newFiles: FileWithStatus[] = acceptedFiles.map((file) => ({
      ...file,
      id: `${file.name}-${Date.now()}-${Math.random()}`,
      status: "pending" as const,
    }));

    setFiles((prev) => [...prev, ...newFiles]);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "image/*": [".jpg", ".jpeg", ".png", ".webp"],
    },
    multiple: true,
  });

  const removeFile = (fileId: string) => {
    setFiles((prev) => prev.filter((f) => f.id !== fileId));
  };

  const handleSubmit = async () => {
    if (!formData.name.trim() || files.length === 0) return;

    try {
      // Update file statuses to uploading
      setFiles((prev) =>
        prev.map((f) => ({ ...f, status: "uploading" as const })),
      );

      const actualFiles = files.map((f) => {
        // Create a new File object without the extra properties
        return new File([f], f.name, {
          type: f.type,
          lastModified: f.lastModified,
        });
      });

      await uploadMutation.mutateAsync({
        dataset: formData,
        files: actualFiles,
      });

      // Update file statuses to success
      setFiles((prev) =>
        prev.map((f) => ({ ...f, status: "success" as const })),
      );

      // Close modal after short delay to show success
      setTimeout(() => {
        onClose();
        resetForm();
      }, 1000);
    } catch (error) {
      // Update file statuses to error
      setFiles((prev) =>
        prev.map((f) => ({
          ...f,
          status: "error" as const,
          error: error instanceof Error ? error.message : "Upload failed",
        })),
      );
    }
  };

  const resetForm = () => {
    setFiles([]);
    setFormData({
      name: "",
      version: "v1.0",
      license: "CC BY 4.0",
      notes: "",
    });
  };

  const handleClose = () => {
    if (uploadMutation.isPending) return; // Prevent closing during upload
    onClose();
    resetForm();
  };

  const isUploading = uploadMutation.isPending;
  const canSubmit = formData.name.trim() && files.length > 0 && !isUploading;

  return (
    <Dialog open={open} onOpenChange={handleClose} data-oid="1ku2amn">
      <DialogContent
        className="max-w-2xl max-h-[80vh] overflow-y-auto"
        data-oid="jewjr0k"
      >
        <div data-oid="fz6moi4">
          <DialogHeader data-oid="neellik">
            <DialogTitle data-oid="bp0y3at">Upload Dataset</DialogTitle>
            <DialogDescription data-oid="xjd0x7s">
              Upload images from your local machine to create a new dataset.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-6" data-oid="-g_f725">
            {/* Dataset Metadata Form */}
            <div className="grid grid-cols-2 gap-4" data-oid="p18viuk">
              <div className="space-y-2" data-oid="g:ct_cj">
                <Label htmlFor="name" data-oid="s2f5aap">
                  Dataset Name *
                </Label>
                <Input
                  id="name"
                  value={formData.name}
                  onChange={(e) =>
                    setFormData((prev) => ({ ...prev, name: e.target.value }))
                  }
                  placeholder="Living Rooms v2"
                  disabled={isUploading}
                  data-oid="334o-sa"
                />
              </div>
              <div className="space-y-2" data-oid="ii_x6pw">
                <Label htmlFor="version" data-oid="mwnvwka">
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
                  disabled={isUploading}
                  data-oid="vnho7jj"
                />
              </div>
              <div className="space-y-2" data-oid="koby.hf">
                <Label htmlFor="license" data-oid="mohuuc0">
                  License
                </Label>
                <Input
                  id="license"
                  value={formData.license}
                  onChange={(e) =>
                    setFormData((prev) => ({
                      ...prev,
                      license: e.target.value,
                    }))
                  }
                  placeholder="CC BY 4.0"
                  disabled={isUploading}
                  data-oid="-m4ximb"
                />
              </div>
              <div className="space-y-2" data-oid="5rg.am4">
                <Label htmlFor="notes" data-oid="fhx9wif">
                  Notes (optional)
                </Label>
                <Input
                  id="notes"
                  value={formData.notes}
                  onChange={(e) =>
                    setFormData((prev) => ({ ...prev, notes: e.target.value }))
                  }
                  placeholder="Internal test dataset"
                  disabled={isUploading}
                  data-oid="fhttqal"
                />
              </div>
            </div>

            {/* File Upload Area */}
            <div className="space-y-4" data-oid="fg7b2im">
              <div
                {...getRootProps()}
                className={`
                border-2 border-dashed rounded-lg p-8 text-center cursor-pointer
                transition-colors hover:bg-muted/50
                ${isDragActive ? "border-primary bg-primary/10" : "border-muted-foreground/25"}
                ${isUploading ? "pointer-events-none opacity-50" : ""}
              `}
                data-oid="aqszatn"
              >
                <input {...getInputProps()} data-oid="5-_r6zp" />
                <Upload
                  className="mx-auto h-12 w-12 text-muted-foreground mb-4"
                  data-oid="9axtnet"
                />
                {isDragActive ? (
                  <p className="text-lg font-medium" data-oid="h6-ev0u">
                    Drop the images here...
                  </p>
                ) : (
                  <>
                    <p className="text-lg font-medium mb-2" data-oid=":kcadim">
                      Drag & drop images here, or click to select
                    </p>
                    <p
                      className="text-sm text-muted-foreground"
                      data-oid="wi-0mix"
                    >
                      Supports JPG, PNG, WebP formats
                    </p>
                  </>
                )}
              </div>

              {/* File List */}
              {files.length > 0 && (
                <div
                  className="space-y-2 max-h-48 overflow-y-auto"
                  data-oid="2qdu5ok"
                >
                  <div
                    className="flex items-center justify-between"
                    data-oid="lxsi45a"
                  >
                    <span className="text-sm font-medium" data-oid="81j9zau">
                      {files.length} file{files.length !== 1 ? "s" : ""}{" "}
                      selected
                    </span>
                    {isUploading && (
                      <Progress
                        value={75} // Mock progress - in production, track actual progress
                        className="w-24"
                        data-oid="g7gkpid"
                      />
                    )}
                  </div>

                  {files.map((file) => (
                    <div
                      key={file.id}
                      className="flex items-center space-x-3 p-2 bg-muted rounded-md"
                      data-oid="vpmkqe9"
                    >
                      <FileImage
                        className="h-4 w-4 text-muted-foreground"
                        data-oid=":kav-fn"
                      />
                      <div className="flex-1 min-w-0" data-oid="03i9htj">
                        <p
                          className="text-sm font-medium truncate"
                          data-oid="d:p6vlc"
                        >
                          {file.name}
                        </p>
                        <p
                          className="text-xs text-muted-foreground"
                          data-oid="wg7byhr"
                        >
                          {(file.size / 1024 / 1024).toFixed(1)} MB
                        </p>
                      </div>

                      <div
                        className="flex items-center space-x-2"
                        data-oid="p:wwspt"
                      >
                        {file.status === "pending" && (
                          <Badge variant="outline" data-oid="msyvehe">
                            Ready
                          </Badge>
                        )}
                        {file.status === "uploading" && (
                          <Badge variant="default" data-oid="n-zoex6">
                            Uploading...
                          </Badge>
                        )}
                        {file.status === "success" && (
                          <CheckCircle
                            className="h-4 w-4 text-green-500"
                            data-oid="aokd80z"
                          />
                        )}
                        {file.status === "error" && (
                          <AlertCircle
                            className="h-4 w-4 text-red-500"
                            data-oid="4v:8ya_"
                          />
                        )}

                        {!isUploading && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => removeFile(file.id)}
                            data-oid="7qzwmea"
                          >
                            <X className="h-3 w-3" data-oid="o3zvu:z" />
                          </Button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Error Display */}
            {uploadMutation.error && (
              <div
                className="bg-destructive/10 border border-destructive/20 rounded-md p-3"
                data-oid="fw6xuhx"
              >
                <div className="flex items-center space-x-2" data-oid="r:sp4iv">
                  <AlertCircle
                    className="h-4 w-4 text-destructive"
                    data-oid="_pr-5te"
                  />
                  <span className="text-sm text-destructive" data-oid="uta87s2">
                    {(uploadMutation.error as Error)?.message ||
                      "An error occurred during upload"}
                  </span>
                </div>
              </div>
            )}
          </div>

          <DialogFooter data-oid="15kg4jd">
            <Button
              variant="outline"
              onClick={handleClose}
              disabled={isUploading}
              data-oid="uqalzdz"
            >
              Cancel
            </Button>
            <Button
              onClick={handleSubmit}
              disabled={!canSubmit}
              data-oid="f3jdsf."
            >
              {isUploading
                ? "Uploading..."
                : `Upload ${files.length} file${files.length !== 1 ? "s" : ""}`}
            </Button>
          </DialogFooter>
        </div>
      </DialogContent>
    </Dialog>
  );
}

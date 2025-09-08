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
    <Dialog open={open} onOpenChange={handleClose} data-oid="h-6ia6u">
      <DialogContent
        className="max-w-2xl max-h-[80vh] overflow-y-auto"
        data-oid="b-px664"
      >
        <div data-oid="64khfx.">
          <DialogHeader data-oid="d12ddbg">
            <DialogTitle data-oid="eg4nrhy">Upload Dataset</DialogTitle>
            <DialogDescription data-oid="2lf6zhx">
              Upload images from your local machine to create a new dataset.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-6" data-oid="8grfvkg">
            {/* Dataset Metadata Form */}
            <div className="grid grid-cols-2 gap-4" data-oid="obk23:8">
              <div className="space-y-2" data-oid="05k44gx">
                <Label htmlFor="name" data-oid="k65zxcz">
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
                  data-oid="ap:pwry"
                />
              </div>
              <div className="space-y-2" data-oid="zuzmu5d">
                <Label htmlFor="version" data-oid="1u7_9d5">
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
                  data-oid="drt7xdc"
                />
              </div>
              <div className="space-y-2" data-oid="9kgdgxs">
                <Label htmlFor="license" data-oid="pbqfm5n">
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
                  data-oid="k18myhb"
                />
              </div>
              <div className="space-y-2" data-oid="rgvxbl0">
                <Label htmlFor="notes" data-oid="r_59x0g">
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
                  data-oid="yc86dk1"
                />
              </div>
            </div>

            {/* File Upload Area */}
            <div className="space-y-4" data-oid="-3hiej3">
              <div
                {...getRootProps()}
                className={`
                border-2 border-dashed rounded-lg p-8 text-center cursor-pointer
                transition-colors hover:bg-muted/50
                ${isDragActive ? "border-primary bg-primary/10" : "border-muted-foreground/25"}
                ${isUploading ? "pointer-events-none opacity-50" : ""}
              `}
                data-oid="4z6fy.o"
              >
                <input {...getInputProps()} data-oid="y:ju9ne" />
                <Upload
                  className="mx-auto h-12 w-12 text-muted-foreground mb-4"
                  data-oid="4w:j0dt"
                />

                {isDragActive ? (
                  <p className="text-lg font-medium" data-oid="gd4m7u2">
                    Drop the images here...
                  </p>
                ) : (
                  <>
                    <p className="text-lg font-medium mb-2" data-oid="e6nl-r_">
                      Drag & drop images here, or click to select
                    </p>
                    <p
                      className="text-sm text-muted-foreground"
                      data-oid="zmh5znq"
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
                  data-oid="ojnlnt_"
                >
                  <div
                    className="flex items-center justify-between"
                    data-oid="7xpd8cj"
                  >
                    <span className="text-sm font-medium" data-oid="4fdh520">
                      {files.length} file{files.length !== 1 ? "s" : ""}{" "}
                      selected
                    </span>
                    {isUploading && (
                      <Progress
                        value={75} // Mock progress - in production, track actual progress
                        className="w-24"
                        data-oid="zgtb7fc"
                      />
                    )}
                  </div>

                  {files.map((file) => (
                    <div
                      key={file.id}
                      className="flex items-center space-x-3 p-2 bg-muted rounded-md"
                      data-oid="jvrd4aa"
                    >
                      <FileImage
                        className="h-4 w-4 text-muted-foreground"
                        data-oid="cx947rn"
                      />

                      <div className="flex-1 min-w-0" data-oid="lch71m3">
                        <p
                          className="text-sm font-medium truncate"
                          data-oid="gwca8rg"
                        >
                          {file.name}
                        </p>
                        <p
                          className="text-xs text-muted-foreground"
                          data-oid="270d-0x"
                        >
                          {(file.size / 1024 / 1024).toFixed(1)} MB
                        </p>
                      </div>

                      <div
                        className="flex items-center space-x-2"
                        data-oid="0r_xue9"
                      >
                        {file.status === "pending" && (
                          <Badge variant="outline" data-oid="p1c86_m">
                            Ready
                          </Badge>
                        )}
                        {file.status === "uploading" && (
                          <Badge variant="default" data-oid="5rx2dd2">
                            Uploading...
                          </Badge>
                        )}
                        {file.status === "success" && (
                          <CheckCircle
                            className="h-4 w-4 text-green-500"
                            data-oid="ff:4o3o"
                          />
                        )}
                        {file.status === "error" && (
                          <AlertCircle
                            className="h-4 w-4 text-red-500"
                            data-oid="hgr8ndv"
                          />
                        )}

                        {!isUploading && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => removeFile(file.id)}
                            data-oid="01.o:a5"
                          >
                            <X className="h-3 w-3" data-oid="jb277b:" />
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
                data-oid="nwvnbkr"
              >
                <div className="flex items-center space-x-2" data-oid="jp4w6-r">
                  <AlertCircle
                    className="h-4 w-4 text-destructive"
                    data-oid="gpu:6en"
                  />

                  <span className="text-sm text-destructive" data-oid=".y_scr3">
                    {(uploadMutation.error as Error)?.message ||
                      "An error occurred during upload"}
                  </span>
                </div>
              </div>
            )}
          </div>

          <DialogFooter data-oid="hwmt2aq">
            <Button
              variant="outline"
              onClick={handleClose}
              disabled={isUploading}
              data-oid="vi3a03n"
            >
              Cancel
            </Button>
            <Button
              onClick={handleSubmit}
              disabled={!canSubmit}
              data-oid="kcg4ac7"
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

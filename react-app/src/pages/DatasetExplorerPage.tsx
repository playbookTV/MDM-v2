import { useState, useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Plus, Download, Search, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { DatasetTable } from "@/components/datasets/DatasetTable";
import { DatasetUploadModal } from "@/components/datasets/DatasetUploadModal";
import { HFImportModal } from "@/components/datasets/HFImportModal";
import { RoboflowImportModal } from "@/components/datasets/RoboflowImportModal";
import { useDatasets, useProcessHuggingFaceDataset, useProcessRoboflowDataset } from "@/hooks/useDatasets";
import { useToast } from "@/components/ui/use-toast";
import type { Dataset } from "@/types/dataset";

export function DatasetExplorerPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [currentPage, setCurrentPage] = useState(1);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [showImportModal, setShowImportModal] = useState(false);
  const [showRoboflowModal, setShowRoboflowModal] = useState(false);
  const [highlightDatasetId, setHighlightDatasetId] = useState<string | null>(
    null,
  );

  const [searchParams, setSearchParams] = useSearchParams();

  const { data, isLoading, error } = useDatasets({
    q: searchQuery || undefined,
    page: currentPage,
    limit: 50,
  });

  const processHuggingFace = useProcessHuggingFaceDataset();
  // const processRoboflow = useProcessRoboflowDataset(); // TODO: Use for advanced Roboflow processing
  const navigate = useNavigate();
  const { toast } = useToast();

  const datasets = data?.items || [];
  const totalPages = data ? Math.ceil(data.total / data.limit) : 0;

  // Handle dataset highlighting from URL parameters
  useEffect(() => {
    const datasetId = searchParams.get("dataset");
    if (datasetId) {
      setHighlightDatasetId(datasetId);
      // Clear the URL parameter after highlighting
      const newSearchParams = new URLSearchParams(searchParams);
      newSearchParams.delete("dataset");
      setSearchParams(newSearchParams, { replace: true });

      // Clear highlight after 3 seconds
      const timer = setTimeout(() => {
        setHighlightDatasetId(null);
      }, 3000);

      return () => clearTimeout(timer);
    }
  }, [searchParams, setSearchParams]);

  const handleSelectDataset = (dataset: Dataset) => {
    console.log("Selected dataset:", dataset);
    // TODO: Navigate to dataset detail view or show dataset info
  };

  const handleViewScenes = (dataset: Dataset) => {
    console.log("View scenes for dataset:", dataset);
    // Navigate to review page with dataset filter
    navigate(`/review?dataset=${dataset.id}`);
  };

  const handleProcessDataset = async (dataset: Dataset) => {
    console.log("Process dataset:", dataset);

    if (!dataset.source_url) {
      toast({
        title: "Processing Failed",
        description: "Dataset has no source URL to process",
        variant: "destructive",
      });
      return;
    }

    try {
      // Determine dataset source type and process accordingly
      const isRoboflow = dataset.source_url.includes("universe.roboflow.com");
      const isHuggingFace = dataset.source_url.includes("huggingface.co");

      if (isRoboflow) {
        // For Roboflow datasets, we need API key - show a prompt or use a stored key
        // For now, we'll prompt user to process via the import flow
        toast({
          title: "Roboflow Processing",
          description: "For Roboflow datasets, please use the 'Import from Roboflow' option with your API key",
          variant: "default",
        });
        return;
      } else if (isHuggingFace) {
        const result = await processHuggingFace.mutateAsync({
          datasetId: dataset.id,
          hfUrl: dataset.source_url,
          options: {
            split: "train",
            image_column: "image",
            max_images: 100, // Optional limit for testing
          },
        });

        console.log(`HuggingFace processing started successfully. Job ID: ${result.job_id}`);

        toast({
          title: "Processing Started",
          description: `Dataset processing job ${result.job_id} started successfully`,
          variant: "default",
        });

        // Navigate to job monitoring page
        navigate("/jobs");
      } else {
        toast({
          title: "Processing Failed",
          description: "Unknown dataset source type",
          variant: "destructive",
        });
      }
    } catch (error) {
      console.error("Failed to start dataset processing:", error);

      toast({
        title: "Processing Failed",
        description:
          error instanceof Error
            ? error.message
            : "Failed to start dataset processing",
        variant: "destructive",
      });
    }
  };

  const handleSearch = (query: string) => {
    setSearchQuery(query);
    setCurrentPage(1); // Reset to first page on new search
  };

  if (error) {
    return (
      <div
        className="flex items-center justify-center min-h-[400px]"
        data-oid="3q3bt2k"
      >
        {error && (
          <div className="text-center py-8" data-oid=".23rtrv">
            <AlertCircle
              className="h-12 w-12 text-destructive mx-auto mb-4"
              data-oid="fnqe-ff"
            />

            <p
              className="text-lg font-medium text-destructive mb-2"
              data-oid="i01rwld"
            >
              Failed to load datasets
            </p>
            <p className="text-muted-foreground" data-oid="jb6s.di">
              {error?.message || "An error occurred while loading datasets"}
            </p>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8 pl-0 pr-0" data-oid="f3dzi2o">
      {/* Header */}
      <div
        className="flex justify-between mb-8 gap-[24px] flex-row items-end"
        data-oid="8lbjuyj"
      >
        <div data-oid="ypbbsqz">
          <h1 className="text-3xl font-bold tracking-tight" data-oid="9cd1i9o">
            Dataset Explorer
          </h1>
          <p className="text-muted-foreground mt-1" data-oid="fghp2zu">
            Manage and process your interior scene datasets
          </p>
        </div>

        <div
          className="flex items-center space-x-2 flex-row w-[fit-content]"
          data-oid="sfwq0v4"
        >
          <Button
            variant="outline"
            onClick={() => setShowImportModal(true)}
            data-oid="s5mfu.l"
          >
            <Download className="h-4 w-4 mr-2" data-oid="avjxlpj" />
            Import from HF
          </Button>
          <Button
            variant="outline"
            onClick={() => setShowRoboflowModal(true)}
            data-oid="roboflow-import"
          >
            <Download className="h-4 w-4 mr-2" />
            Import from Roboflow
          </Button>
          <Button onClick={() => setShowUploadModal(true)} data-oid="83v-rll">
            <Plus className="h-4 w-4 mr-2" data-oid="_1swiby" />
            Upload Dataset
          </Button>
        </div>
      </div>

      {/* Search and Filters */}
      <div
        className="flex items-center space-x-4 mb-6 flex-col"
        data-oid="z97eut7"
      >
        <div className="relative flex-1 max-w-sm" data-oid="4cj1ci:">
          <Search
            className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground"
            data-oid="_lhmnn9"
          />

          <Input
            placeholder="Search datasets..."
            value={searchQuery}
            onChange={(e) => handleSearch(e.target.value)}
            className="pl-9"
            data-oid="ha26-po"
          />
        </div>

        {data && (
          <div className="text-sm text-muted-foreground" data-oid="1o-x.av">
            Showing {data.items.length} of {data.total} dataset
            {data.total !== 1 ? "s" : ""}
          </div>
        )}
      </div>

      {/* Dataset Table */}
      <DatasetTable
        datasets={datasets}
        loading={isLoading}
        highlightId={highlightDatasetId}
        onSelectDataset={handleSelectDataset}
        onViewScenes={handleViewScenes}
        onProcessDataset={handleProcessDataset}
        data-oid="xln3pew"
      />

      {/* Pagination */}
      {totalPages > 1 && (
        <div
          className="flex items-center justify-between mt-6"
          data-oid="a-2h3z0"
        >
          <div className="text-sm text-muted-foreground" data-oid="k59_tj3">
            Page {currentPage} of {totalPages}
          </div>

          <div className="flex items-center space-x-2" data-oid="gns_f4z">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
              disabled={currentPage <= 1 || isLoading}
              data-oid="eibxt.1"
            >
              Previous
            </Button>

            <Button
              variant="outline"
              size="sm"
              onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
              disabled={currentPage >= totalPages || isLoading}
              data-oid="zxwkkvn"
            >
              Next
            </Button>
          </div>
        </div>
      )}

      {/* Modals */}
      <DatasetUploadModal
        open={showUploadModal}
        onClose={() => setShowUploadModal(false)}
        data-oid="9d:nvn8"
      />

      <HFImportModal
        open={showImportModal}
        onClose={() => setShowImportModal(false)}
        data-oid="9un19th"
      />

      <RoboflowImportModal
        open={showRoboflowModal}
        onClose={() => setShowRoboflowModal(false)}
      />
    </div>
  );
}

import { Routes, Route, Navigate } from "react-router-dom";
import { DatasetExplorerPage } from "@/pages/DatasetExplorerPage";
import { JobsPage } from "@/pages/JobsPage";
import { StatsDashboardPage } from "@/pages/StatsDashboardPage";
import { SceneReviewPage } from "@/pages/SceneReviewPage";
import { Navigation } from "@/components/layout/Navigation";
import ErrorBoundary from "@/components/ui/error-boundary";

function App() {
  return (
    <ErrorBoundary data-oid="_3src4z">
      <div className="min-h-screen bg-background" data-oid="sq0xkee">
        <Navigation data-oid="6a5wku6" />
        <main className="container mx-auto px-4 py-6" data-oid="fsfe9i7">
          <Routes data-oid="mn5grb:">
            <Route
              path="/"
              element={<Navigate to="/datasets" replace data-oid="6itf:.b" />}
              data-oid="a7t1.hs"
            />

            <Route
              path="/datasets"
              element={<DatasetExplorerPage data-oid="_5q00ks" />}
              data-oid="6icihg-"
            />

            <Route
              path="/jobs"
              element={<JobsPage data-oid="yoyojot" />}
              data-oid="3nxsyu3"
            />

            <Route
              path="/dashboard"
              element={<StatsDashboardPage data-oid="3rx4-rn" />}
              data-oid="gqc8.0:"
            />

            <Route
              path="/review"
              element={<SceneReviewPage data-oid="_tuv7z3" />}
              data-oid="phtg5hf"
            />
          </Routes>
        </main>
      </div>
    </ErrorBoundary>
  );
}

export default App;

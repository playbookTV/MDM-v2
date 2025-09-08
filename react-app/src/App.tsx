import { Routes, Route, Navigate } from "react-router-dom";
import { DatasetExplorerPage } from "@/pages/DatasetExplorerPage";
import { JobsPage } from "@/pages/JobsPage";
import { StatsDashboardPage } from "@/pages/StatsDashboardPage";
import { SceneReviewPage } from "@/pages/SceneReviewPage";
import { Navigation } from "@/components/layout/Navigation";
import ErrorBoundary from "@/components/ui/error-boundary";

function App() {
  return (
    <ErrorBoundary data-oid="vzr1c5b">
      <div className="min-h-screen bg-background" data-oid="5-5i_mu">
        <Navigation data-oid="-6:.2aa" />
        <main className="container mx-auto px-4 py-6" data-oid="9-.fc-n">
          <Routes data-oid="2.lepe-">
            <Route
              path="/"
              element={<Navigate to="/datasets" replace data-oid="v3-un8x" />}
              data-oid="7sz9.35"
            />
            <Route
              path="/datasets"
              element={<DatasetExplorerPage data-oid="emrpcj0" />}
              data-oid="2v78cit"
            />
            <Route
              path="/jobs"
              element={<JobsPage data-oid="dypek92" />}
              data-oid="0m23taa"
            />
            <Route
              path="/dashboard"
              element={<StatsDashboardPage data-oid="j7kwyb9" />}
              data-oid="iarywta"
            />
            <Route
              path="/review"
              element={<SceneReviewPage data-oid="r.4:s1g" />}
              data-oid="m.gfu5s"
            />
          </Routes>
        </main>
      </div>
    </ErrorBoundary>
  );
}

export default App;

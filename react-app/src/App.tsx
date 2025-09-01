import { Routes, Route, Navigate } from 'react-router-dom'
import { DatasetExplorerPage } from '@/pages/DatasetExplorerPage'
import { JobsPage } from '@/pages/JobsPage'
import { StatsDashboardPage } from '@/pages/StatsDashboardPage'
import { SceneReviewPage } from '@/pages/SceneReviewPage'
import { Navigation } from '@/components/layout/Navigation'
import ErrorBoundary from '@/components/ui/error-boundary'

function App() {
  return (
    <ErrorBoundary>
      <div className="min-h-screen bg-background">
        <Navigation />
        <main className="container mx-auto px-4 py-6">
          <Routes>
            <Route path="/" element={<Navigate to="/datasets" replace />} />
            <Route path="/datasets" element={<DatasetExplorerPage />} />
            <Route path="/jobs" element={<JobsPage />} />
            <Route path="/dashboard" element={<StatsDashboardPage />} />
            <Route path="/review" element={<SceneReviewPage />} />
          </Routes>
        </main>
      </div>
    </ErrorBoundary>
  )
}

export default App
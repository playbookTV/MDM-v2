import { Routes, Route, Navigate } from 'react-router-dom'
import { DatasetExplorerPage } from '@/pages/DatasetExplorerPage'
import { JobsPage } from '@/pages/JobsPage'
import { StatsDashboardPage } from '@/pages/StatsDashboardPage'
import { SceneReviewPage } from '@/pages/SceneReviewPage'

function App() {
  return (
    <div className="min-h-screen bg-background">
      <Routes>
        <Route path="/" element={<Navigate to="/datasets" replace />} />
        <Route path="/datasets" element={<DatasetExplorerPage />} />
        <Route path="/jobs" element={<JobsPage />} />
        <Route path="/dashboard" element={<StatsDashboardPage />} />
        <Route path="/review" element={<SceneReviewPage />} />
      </Routes>
    </div>
  )
}

export default App
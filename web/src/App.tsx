import { AlertTriangle, BrainCircuit, RotateCcw, Settings } from 'lucide-react'
import { lazy, Suspense } from 'react'
import { Navigate, Route, Routes, useLocation } from 'react-router-dom'
import { AppShell } from './components/AppShell'
import { useWorkspace } from './components/workspace-context'
import { Button } from './components/ui'
import { OnboardingPage } from './pages/OnboardingPage'
import { PlaceholderPage } from './pages/PlaceholderPage'

const SearchPage = lazy(() =>
  import('./pages/SearchPage').then((module) => ({ default: module.SearchPage })),
)
const CreatePage = lazy(() =>
  import('./pages/CreatePage').then((module) => ({ default: module.CreatePage })),
)
const SourcesPage = lazy(() =>
  import('./pages/SourcesPage').then((module) => ({ default: module.SourcesPage })),
)
const BacklogPage = lazy(() =>
  import('./pages/BacklogPage').then((module) => ({ default: module.BacklogPage })),
)
const RetentionPage = lazy(() =>
  import('./pages/RetentionPage').then((module) => ({ default: module.RetentionPage })),
)
const MasteryPage = lazy(() =>
  import('./pages/MasteryPage').then((module) => ({ default: module.MasteryPage })),
)
const ProfilePage = lazy(() =>
  import('./pages/ProfilePage').then((module) => ({ default: module.ProfilePage })),
)

function App() {
  const { health, loading, error, refresh } = useWorkspace()

  if (loading) {
    return (
      <div className="boot-screen">
        <div className="boot-screen__mark">
          <BrainCircuit size={26} />
        </div>
        <strong>Opening Studium</strong>
        <span className="boot-screen__line" />
      </div>
    )
  }

  if (error) {
    return (
      <main className="fatal-state">
        <div className="fatal-state__icon">
          <AlertTriangle size={24} />
        </div>
        <p className="eyebrow">Connection problem</p>
        <h1>Studium could not reach its local service.</h1>
        <p>{error.message}</p>
        <Button variant="primary" onClick={() => void refresh()}>
          <RotateCcw size={16} /> Try again
        </Button>
      </main>
    )
  }

  if (!health?.workspace_open) return <OnboardingPage />

  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route index element={<Navigate to="/search" replace />} />
        <Route
          path="/search"
          element={<SearchRoute />}
        />
        <Route
          path="/create/*"
          element={
            <Suspense fallback={<div className="page"><div className="boot-screen__line" /></div>}>
              <CreatePage />
            </Suspense>
          }
        />
        <Route
          path="/sources/*"
          element={
            <Suspense fallback={<div className="page"><div className="boot-screen__line" /></div>}>
              <SourcesPage />
            </Suspense>
          }
        />
        <Route
          path="/backlog"
          element={
            <Suspense fallback={<div className="page"><div className="boot-screen__line" /></div>}>
              <BacklogPage />
            </Suspense>
          }
        />
        <Route
          path="/retention"
          element={
            <Suspense fallback={<div className="page"><div className="boot-screen__line" /></div>}>
              <RetentionPage />
            </Suspense>
          }
        />
        <Route
          path="/mastery"
          element={
            <Suspense fallback={<div className="page"><div className="boot-screen__line" /></div>}>
              <MasteryPage />
            </Suspense>
          }
        />
        <Route
          path="/profile"
          element={
            <Suspense fallback={<div className="page"><div className="boot-screen__line" /></div>}>
              <ProfilePage />
            </Suspense>
          }
        />
        <Route
          path="/settings"
          element={
            <PlaceholderPage
              eyebrow="Local control"
              title="Know where your data lives and which models see it."
              description="Configure vault, providers, privacy, exports, and recovery."
            >
              <Settings size={26} />
            </PlaceholderPage>
          }
        />
        <Route path="*" element={<Navigate to="/search" replace />} />
      </Route>
    </Routes>
  )
}

function SearchRoute() {
  const location = useLocation()
  const query = new URLSearchParams(location.search).get('q') ?? ''
  return (
    <Suspense fallback={<div className="page"><div className="boot-screen__line" /></div>}>
      <SearchPage key={query} />
    </Suspense>
  )
}

export default App

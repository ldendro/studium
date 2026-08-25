import { AlertTriangle, BrainCircuit, Inbox, LayoutDashboard, PenLine, RotateCcw, Search, Settings, Sparkles, TimerReset } from 'lucide-react'
import { Navigate, Route, Routes } from 'react-router-dom'
import { AppShell } from './components/AppShell'
import { useWorkspace } from './components/workspace-context'
import { Button } from './components/ui'
import { OnboardingPage } from './pages/OnboardingPage'
import { PlaceholderPage } from './pages/PlaceholderPage'

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
          element={
            <PlaceholderPage
              eyebrow="Explore"
              title="Find the knowledge already in your vault."
              description="Search concepts, aliases, and scaffold modules with graph context."
            >
              <Search size={26} />
            </PlaceholderPage>
          }
        />
        <Route
          path="/create/*"
          element={
            <PlaceholderPage
              eyebrow="Create"
              title="Begin with concept intelligence, not a blank page."
              description="Investigate, scaffold, edit, review, and accept knowledge in one workflow."
            >
              <PenLine size={26} />
            </PlaceholderPage>
          }
        />
        <Route
          path="/sources/*"
          element={
            <PlaceholderPage
              eyebrow="Source intelligence"
              title="Understand what your sources contribute."
              description="Process material once, retrieve relevant evidence, and keep citations attached."
            >
              <Sparkles size={26} />
            </PlaceholderPage>
          }
        />
        <Route
          path="/backlog"
          element={
            <PlaceholderPage
              eyebrow="Learning work"
              title="Keep the next useful learning step visible."
              description="Prioritize missing prerequisites, open questions, and concept expansions."
            >
              <Inbox size={26} />
            </PlaceholderPage>
          }
        />
        <Route
          path="/retention"
          element={
            <PlaceholderPage
              eyebrow="Active recall"
              title="Review the weak slice, not the entire note."
              description="Focused prompts adapt to concepts, modules, and prerequisite strength."
            >
              <TimerReset size={26} />
            </PlaceholderPage>
          }
        />
        <Route
          path="/mastery"
          element={
            <PlaceholderPage
              eyebrow="Evidence"
              title="See what is strong, fragile, and worth doing next."
              description="Mastery is calculated from observable learning evidence."
            >
              <LayoutDashboard size={26} />
            </PlaceholderPage>
          }
        />
        <Route
          path="/profile"
          element={
            <PlaceholderPage
              eyebrow="Personal model"
              title="Make personalization transparent and editable."
              description="Inspect the evidence behind how Studium adapts to your learning."
            >
              <Sparkles size={26} />
            </PlaceholderPage>
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

export default App

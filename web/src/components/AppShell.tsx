import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import clsx from 'clsx'
import {
  BookOpenText,
  BrainCircuit,
  Check,
  ChevronDown,
  CircleGauge,
  Clock3,
  Command,
  DatabaseZap,
  Files,
  Inbox,
  LayoutDashboard,
  Menu,
  PenLine,
  RefreshCw,
  Search,
  Settings,
  Sparkles,
  UserRound,
  X,
} from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { api } from '../lib/api'
import type { Job, SyncReport } from '../lib/types'
import { useToast } from './toast-context'
import { useWorkspace } from './workspace-context'
import { Badge, Button, IconButton, Progress } from './ui'

const primaryNavigation = [
  { to: '/search', label: 'Search', icon: Search },
  { to: '/create', label: 'Create', icon: PenLine },
  { to: '/sources', label: 'Sources', icon: Files },
  { to: '/backlog', label: 'Backlog', icon: Inbox },
  { to: '/retention', label: 'Retention', icon: Clock3 },
  { to: '/mastery', label: 'Mastery', icon: LayoutDashboard },
]

const secondaryNavigation = [
  { to: '/profile', label: 'Learning profile', icon: UserRound },
  { to: '/settings', label: 'Settings', icon: Settings },
]

export function AppShell() {
  const [mobileOpen, setMobileOpen] = useState(false)
  const [commandOpen, setCommandOpen] = useState(false)
  const [jobsOpen, setJobsOpen] = useState(false)
  const [query, setQuery] = useState('')
  const commandInput = useRef<HTMLInputElement>(null)
  const navigate = useNavigate()
  const { health, refresh } = useWorkspace()
  const { push } = useToast()
  const queryClient = useQueryClient()

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') {
        event.preventDefault()
        setCommandOpen((open) => !open)
      }
      if (event.key === 'Escape') {
        setCommandOpen(false)
        setJobsOpen(false)
        setMobileOpen(false)
      }
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [])

  useEffect(() => {
    if (commandOpen) window.setTimeout(() => commandInput.current?.focus(), 30)
  }, [commandOpen])

  const syncMutation = useMutation({
    mutationFn: () =>
      api<{ report: SyncReport }>('/api/index/sync', {
        method: 'POST',
        body: { embeddings: true, background: false },
      }),
    onSuccess: async ({ report }) => {
      await refresh()
      await queryClient.invalidateQueries()
      push(
        report.status === 'no_changes' ? 'Vault is already current' : 'Vault synchronized',
        {
          description: `Index revision ${report.revision_after}`,
          tone: report.status === 'partial_success' ? 'warning' : 'success',
        },
      )
    },
    onError: (error: Error) => push('Synchronization failed', { description: error.message, tone: 'danger' }),
  })

  const jobsQuery = useQuery({
    queryKey: ['jobs'],
    queryFn: () => api<{ jobs: Job[] }>('/api/jobs'),
    enabled: jobsOpen,
    refetchInterval: jobsOpen ? 2_000 : false,
  })
  const retryJobMutation = useMutation({
    mutationFn: (jobId: string) =>
      api<{ job: Job }>(`/api/jobs/${jobId}/retry`, { method: 'POST' }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['jobs'] })
      push('Job queued again', { tone: 'success' })
    },
    onError: (error: Error) =>
      push('Job could not be retried', { description: error.message, tone: 'danger' }),
  })

  const submitSearch = () => {
    const trimmed = query.trim()
    if (!trimmed) return
    navigate(`/search?q=${encodeURIComponent(trimmed)}`)
    setCommandOpen(false)
    setQuery('')
  }

  const navigation = (items: typeof primaryNavigation) =>
    items.map(({ to, label, icon: Icon }) => (
      <NavLink
        key={to}
        to={to}
        className={({ isActive }) => clsx('nav-link', isActive && 'nav-link--active')}
        onClick={() => setMobileOpen(false)}
      >
        <Icon size={18} strokeWidth={1.8} aria-hidden />
        <span>{label}</span>
      </NavLink>
    ))

  return (
    <div className="app-shell">
      <aside className={clsx('sidebar', mobileOpen && 'sidebar--open')}>
        <div className="brand">
          <div className="brand__mark" aria-hidden>
            <BrainCircuit size={22} />
          </div>
          <div>
            <strong>Studium</strong>
            <span>Learning workspace</span>
          </div>
          <IconButton
            label="Close navigation"
            className="sidebar__close"
            onClick={() => setMobileOpen(false)}
          >
            <X size={18} />
          </IconButton>
        </div>

        <button className="vault-switcher" type="button" onClick={() => navigate('/settings?section=vault')}>
          <span className="vault-switcher__icon">
            <BookOpenText size={17} />
          </span>
          <span className="vault-switcher__copy">
            <small>Active vault</small>
            <strong>{health?.vault_name ?? 'No vault'}</strong>
          </span>
          <ChevronDown size={15} />
        </button>

        <nav className="sidebar__nav" aria-label="Main navigation">
          <p className="nav-caption">Workspace</p>
          {navigation(primaryNavigation)}
        </nav>

        <nav className="sidebar__nav sidebar__nav--secondary" aria-label="Personalization">
          <p className="nav-caption">Personal</p>
          {navigation(secondaryNavigation)}
        </nav>

        <div className="sidebar__status">
          <div className="status-line">
            <span className="status-dot status-dot--ok" />
            <span>Index revision {health?.index_revision ?? 0}</span>
            <Check size={14} />
          </div>
          <p>{health?.embedding?.model_id ?? 'Embedding model unavailable'}</p>
        </div>
      </aside>

      {mobileOpen && (
        <button
          className="mobile-backdrop"
          type="button"
          aria-label="Close navigation"
          onClick={() => setMobileOpen(false)}
        />
      )}

      <div className="app-main">
        <header className="app-topbar">
          <div className="topbar__left">
            <IconButton label="Open navigation" className="mobile-menu" onClick={() => setMobileOpen(true)}>
              <Menu size={20} />
            </IconButton>
            <button className="command-trigger" type="button" onClick={() => setCommandOpen(true)}>
              <Search size={16} aria-hidden />
              <span>Search your knowledge</span>
              <kbd>
                <Command size={11} /> K
              </kbd>
            </button>
          </div>
          <div className="topbar__actions">
            <div className="topbar-popover-anchor">
              <IconButton label="Background jobs" onClick={() => setJobsOpen((open) => !open)}>
                <DatabaseZap size={18} />
              </IconButton>
              {jobsOpen && (
                <div className="popover jobs-popover">
                  <div className="popover__header">
                    <div>
                      <p className="eyebrow">Activity</p>
                      <h3>Background jobs</h3>
                    </div>
                    <IconButton label="Close jobs" onClick={() => setJobsOpen(false)}>
                      <X size={16} />
                    </IconButton>
                  </div>
                  <div className="job-list">
                    {jobsQuery.data?.jobs.length ? (
                      jobsQuery.data.jobs.slice(0, 8).map((job) => (
                        <div className="job-row" key={job.id}>
                          <div className="job-row__header">
                            <strong>{job.job_type.replaceAll('_', ' ')}</strong>
                            <Badge
                              tone={
                                job.status === 'completed'
                                  ? 'success'
                                  : job.status === 'failed'
                                    ? 'danger'
                                    : 'blue'
                              }
                            >
                              {job.status}
                            </Badge>
                          </div>
                          {(job.status === 'queued' || job.status === 'running') && (
                            <Progress value={job.progress} />
                          )}
                          {job.message && <p>{job.message}</p>}
                          {job.status === 'failed' && job.error && <p className="job-row__error">{job.error}</p>}
                          {job.retryable && (
                            <Button
                              variant="ghost"
                              size="small"
                              loading={retryJobMutation.isPending && retryJobMutation.variables === job.id}
                              onClick={() => retryJobMutation.mutate(job.id)}
                            >
                              <RefreshCw size={13} /> Retry
                            </Button>
                          )}
                        </div>
                      ))
                    ) : (
                      <p className="popover__empty">No recent background activity.</p>
                    )}
                  </div>
                </div>
              )}
            </div>
            <Button
              variant="ghost"
              size="small"
              loading={syncMutation.isPending}
              onClick={() => syncMutation.mutate()}
            >
              <RefreshCw size={15} /> Sync
            </Button>
            <button className="avatar" type="button" onClick={() => navigate('/profile')} aria-label="Open profile">
              <Sparkles size={16} />
            </button>
          </div>
        </header>
        <main className="page-container">
          <Outlet />
        </main>
      </div>

      {commandOpen && (
        <div className="dialog-backdrop" role="presentation" onMouseDown={() => setCommandOpen(false)}>
          <div
            className="command-dialog"
            role="dialog"
            aria-modal="true"
            aria-label="Search Studium"
            onMouseDown={(event) => event.stopPropagation()}
          >
            <div className="command-dialog__input">
              <Search size={20} />
              <input
                ref={commandInput}
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === 'Enter') submitSearch()
                }}
                placeholder="Find a concept, module, or source…"
              />
              <kbd>Esc</kbd>
            </div>
            <div className="command-dialog__body">
              <p className="nav-caption">Quick actions</p>
              <button type="button" onClick={submitSearch}>
                <Search size={17} />
                <span>
                  Search knowledge
                  <small>Exact, semantic, and module retrieval</small>
                </span>
              </button>
              <button
                type="button"
                onClick={() => {
                  navigate('/create')
                  setCommandOpen(false)
                }}
              >
                <PenLine size={17} />
                <span>
                  Start a learning session
                  <small>Investigate the vault before creating</small>
                </span>
              </button>
              <button
                type="button"
                onClick={() => {
                  navigate('/retention')
                  setCommandOpen(false)
                }}
              >
                <CircleGauge size={17} />
                <span>
                  Begin due reviews
                  <small>Focused active recall</small>
                </span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

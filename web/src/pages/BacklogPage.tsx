import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import clsx from 'clsx'
import {
  ArrowRight,
  CheckCircle2,
  GitBranch,
  Inbox,
  LoaderCircle,
  Plus,
  Search,
  Sparkles,
  Target,
} from 'lucide-react'
import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { useToast } from '../components/toast-context'
import { Badge, Button, EmptyState, Field, Input, PageHeader, Panel, Textarea } from '../components/ui'
import { api } from '../lib/api'
import type { BacklogItem, BacklogStatus } from '../lib/types'

const STATUSES: Array<{ value: BacklogStatus | 'active'; label: string }> = [
  { value: 'active', label: 'Active' },
  { value: 'open', label: 'Open' },
  { value: 'in_progress', label: 'In progress' },
  { value: 'deferred', label: 'Deferred' },
  { value: 'completed', label: 'Completed' },
]

export function BacklogPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { push } = useToast()
  const [statusFilter, setStatusFilter] = useState<BacklogStatus | 'active'>('active')
  const [originFilter, setOriginFilter] = useState('')
  const [query, setQuery] = useState('')
  const [adding, setAdding] = useState(false)
  const [title, setTitle] = useState('')
  const [reason, setReason] = useState('')
  const [priority, setPriority] = useState(60)

  const itemsQuery = useQuery({
    queryKey: ['backlog', statusFilter, originFilter, query],
    queryFn: async () => {
      const search = new URLSearchParams()
      if (statusFilter !== 'active') search.set('status', statusFilter)
      if (originFilter) search.set('origin', originFilter)
      if (query.trim()) search.set('query', query.trim())
      const result = await api<{ items: BacklogItem[] }>(`/api/backlog?${search}`)
      return statusFilter === 'active'
        ? { items: result.items.filter((item) => ['open', 'in_progress', 'deferred'].includes(item.status)) }
        : result
    },
  })
  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['backlog'] })
  const createMutation = useMutation({
    mutationFn: () =>
      api<BacklogItem>('/api/backlog', {
        method: 'POST',
        body: {
          title,
          reason,
          priority,
          item_type: 'new_concept',
          origin: 'manual',
          required_by: [],
          metadata: {},
        },
      }),
    onSuccess: async () => {
      await invalidate()
      setTitle('')
      setReason('')
      setAdding(false)
      push('Added to backlog', { tone: 'success' })
    },
    onError: (error: Error) =>
      push('Could not add item', { description: error.message, tone: 'danger' }),
  })
  const deriveMutation = useMutation({
    mutationFn: () => api<{ items: BacklogItem[] }>('/api/backlog/derive', { method: 'POST' }),
    onSuccess: async (result) => {
      await invalidate()
      push('Graph scan complete', {
        description: `${result.items.length} missing relationship candidate(s) are represented.`,
        tone: 'success',
      })
    },
  })
  const updateMutation = useMutation({
    mutationFn: ({ id, values }: { id: string; values: Record<string, unknown> }) =>
      api<BacklogItem>(`/api/backlog/${id}`, { method: 'PATCH', body: values }),
    onSuccess: () => invalidate(),
  })
  const resolveMutation = useMutation({
    mutationFn: (item: BacklogItem) =>
      api<BacklogItem>(`/api/backlog/${item.id}/confirm-resolution`, {
        method: 'POST',
        body: { concept_id: item.resolution_candidate?.concept_id ?? null },
      }),
    onSuccess: async () => {
      await invalidate()
      push('Backlog item resolved', {
        description: 'The accepted concept match was confirmed by you.',
        tone: 'success',
      })
    },
  })
  const promoteMutation = useMutation({
    mutationFn: (item: BacklogItem) =>
      api<{
        intent: string
        user_context: string
        source_type: string
        source_title: string
        source_unit: string
      }>(`/api/backlog/${item.id}/promote`, { method: 'POST' }),
    onSuccess: (handoff) => {
      const params = new URLSearchParams({
        intent: handoff.intent,
        context: handoff.user_context,
        sourceType: handoff.source_type,
        sourceTitle: handoff.source_title,
        sourceUnit: handoff.source_unit,
      })
      navigate(`/create?${params}`)
    },
  })

  const items = itemsQuery.data?.items ?? []
  const groups = [
    { label: 'Do next', description: 'Priority 75–100', items: items.filter((item) => item.priority >= 75) },
    { label: 'Develop', description: 'Priority 45–74', items: items.filter((item) => item.priority >= 45 && item.priority < 75) },
    { label: 'Later', description: 'Priority below 45', items: items.filter((item) => item.priority < 45) },
  ]
  const submit = (event: FormEvent) => {
    event.preventDefault()
    createMutation.mutate()
  }

  return (
    <div className="page learning-page backlog-page">
      <PageHeader
        eyebrow="Backlog"
        title="Keep the next useful learning step visible."
        description="Missing prerequisites, open questions, and intentional expansions stay prioritized without polluting your Markdown vault."
        actions={
          <div className="page-action-row">
            <Button variant="secondary" loading={deriveMutation.isPending} onClick={() => deriveMutation.mutate()}>
              <GitBranch size={14} /> Scan missing graph links
            </Button>
            <Button variant="primary" onClick={() => setAdding((value) => !value)}>
              <Plus size={14} /> Add item
            </Button>
          </div>
        }
      />

      <div className="learning-stat-row">
        <Stat icon={<Inbox />} value={items.length} label="Visible items" />
        <Stat icon={<Target />} value={items.filter((item) => item.priority >= 75).length} label="High priority" />
        <Stat icon={<GitBranch />} value={items.filter((item) => item.origin === 'graph').length} label="Graph-derived" />
        <Stat icon={<CheckCircle2 />} value={items.filter((item) => item.resolution_candidate).length} label="Ready to resolve" />
      </div>

      {adding && (
        <Panel className="learning-inline-form">
          <form onSubmit={submit}>
            <div>
              <p className="eyebrow">Manual candidate</p>
              <h2>Preserve a learning intention.</h2>
            </div>
            <Field label="Concept or question">
              <Input value={title} onChange={(event) => setTitle(event.target.value)} required autoFocus />
            </Field>
            <Field label="Why this belongs in your backlog">
              <Textarea value={reason} onChange={(event) => setReason(event.target.value)} rows={2} required />
            </Field>
            <Field label={`Priority · ${priority}`}>
              <input type="range" min="0" max="100" value={priority} onChange={(event) => setPriority(Number(event.target.value))} />
            </Field>
            <div>
              <Button type="submit" variant="primary" loading={createMutation.isPending}>Add to backlog</Button>
              <Button variant="ghost" onClick={() => setAdding(false)}>Cancel</Button>
            </div>
          </form>
        </Panel>
      )}

      <div className="learning-toolbar">
        <div className="learning-search">
          <Search size={14} />
          <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Filter concepts, questions, or gaps" />
        </div>
        <div className="learning-filter-tabs" role="tablist" aria-label="Backlog status">
          {STATUSES.map((item) => (
            <button
              key={item.value}
              type="button"
              className={statusFilter === item.value ? 'active' : ''}
              aria-selected={statusFilter === item.value}
              role="tab"
              onClick={() => setStatusFilter(item.value)}
            >
              {item.label}
            </button>
          ))}
        </div>
        <select value={originFilter} onChange={(event) => setOriginFilter(event.target.value)} aria-label="Filter backlog origin">
          <option value="">All origins</option>
          {['search', 'create', 'graph', 'review', 'retention', 'manual'].map((origin) => (
            <option key={origin} value={origin}>{label(origin)}</option>
          ))}
        </select>
      </div>

      {itemsQuery.isLoading ? (
        <Panel className="learning-loading"><LoaderCircle className="spin" /> Prioritizing backlog…</Panel>
      ) : items.length === 0 ? (
        <Panel>
          <EmptyState
            icon={<Inbox size={24} />}
            title="Nothing is waiting here"
            description="Save a search gap, derive missing graph targets, or add a learning intention manually."
            action={<Button variant="primary" onClick={() => setAdding(true)}>Add an item</Button>}
          />
        </Panel>
      ) : (
        <div className="backlog-groups">
          {groups.filter((group) => group.items.length).map((group) => (
            <section key={group.label} className="backlog-group">
              <header>
                <div><h2>{group.label}</h2><span>{group.description}</span></div>
                <Badge>{group.items.length}</Badge>
              </header>
              <div className="backlog-grid">
                {group.items.map((item) => (
                  <article className={clsx('backlog-card', `backlog-card--${item.status}`)} key={item.id}>
                    <header>
                      <span className="priority-meter" style={{ '--priority': `${item.priority}%` } as React.CSSProperties}>
                        <i />
                        {item.priority}
                      </span>
                      <div>
                        <Badge tone={item.origin === 'graph' ? 'blue' : 'neutral'}>{item.origin}</Badge>
                        <Badge>{label(item.item_type)}</Badge>
                      </div>
                    </header>
                    <h3>{item.title}</h3>
                    <p>{item.reason}</p>
                    {item.required_by.length > 0 && (
                      <div className="backlog-context">
                        <GitBranch size={13} />
                        Required by {item.required_by.length} concept{item.required_by.length === 1 ? '' : 's'}
                      </div>
                    )}
                    {item.resolution_candidate && item.status !== 'completed' && (
                      <div className="backlog-resolution">
                        <CheckCircle2 size={14} />
                        <span>
                          <strong>Accepted match found</strong>
                          <small>{item.resolution_candidate.title}</small>
                        </span>
                        <Button size="small" variant="secondary" loading={resolveMutation.isPending} onClick={() => resolveMutation.mutate(item)}>
                          Confirm
                        </Button>
                      </div>
                    )}
                    <footer>
                      <select
                        value={item.status}
                        aria-label={`Status for ${item.title}`}
                        onChange={(event) => updateMutation.mutate({ id: item.id, values: { status: event.target.value } })}
                      >
                        {STATUSES.filter((status) => status.value !== 'active').map((status) => (
                          <option key={status.value} value={status.value}>{status.label}</option>
                        ))}
                        <option value="dismissed">Dismissed</option>
                      </select>
                      {item.status !== 'completed' && (
                        <Button variant="primary" size="small" loading={promoteMutation.isPending} onClick={() => promoteMutation.mutate(item)}>
                          <Sparkles size={13} /> Start learning <ArrowRight size={13} />
                        </Button>
                      )}
                    </footer>
                  </article>
                ))}
              </div>
            </section>
          ))}
        </div>
      )}
    </div>
  )
}

function Stat({ icon, value, label: text }: { icon: React.ReactNode; value: number; label: string }) {
  return (
    <Panel className="learning-stat">
      <span>{icon}</span>
      <div><strong>{value}</strong><small>{text}</small></div>
    </Panel>
  )
}

function label(value: string) {
  return value.replaceAll('_', ' ').replace(/\b\w/g, (letter) => letter.toUpperCase())
}


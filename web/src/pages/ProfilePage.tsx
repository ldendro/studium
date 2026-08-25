import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import clsx from 'clsx'
import {
  Check,
  EyeOff,
  FileText,
  LoaderCircle,
  Pencil,
  Pin,
  Plus,
  RefreshCw,
  ShieldCheck,
  Sparkles,
  X,
} from 'lucide-react'
import { useState, type FormEvent } from 'react'
import { Markdown } from '../components/Markdown'
import { useToast } from '../components/toast-context'
import { Badge, Button, EmptyState, Field, Input, PageHeader, Panel, Textarea } from '../components/ui'
import { api } from '../lib/api'
import type { ProfileObservation } from '../lib/types'

const CATEGORIES: ProfileObservation['category'][] = [
  'goal',
  'active_context',
  'learning_preference',
  'strength',
  'gap',
  'topic_priority',
]

export function ProfilePage() {
  const queryClient = useQueryClient()
  const { push } = useToast()
  const [filter, setFilter] = useState<'all' | ProfileObservation['status']>('all')
  const [adding, setAdding] = useState(false)
  const [category, setCategory] = useState<ProfileObservation['category']>('goal')
  const [statement, setStatement] = useState('')
  const [editingId, setEditingId] = useState<string | null>(null)
  const [editingStatement, setEditingStatement] = useState('')

  const observationsQuery = useQuery({
    queryKey: ['profile-observations', filter],
    queryFn: () =>
      api<{ observations: ProfileObservation[] }>(
        `/api/profile/observations${filter === 'all' ? '' : `?status=${filter}`}`,
      ),
  })
  const soulQuery = useQuery({
    queryKey: ['profile-soul'],
    queryFn: () => api<{ path: string; markdown: string }>('/api/profile/soul'),
  })
  const refresh = async () => {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ['profile-observations'] }),
      queryClient.invalidateQueries({ queryKey: ['profile-soul'] }),
    ])
  }
  const createMutation = useMutation({
    mutationFn: () =>
      api<ProfileObservation>('/api/profile/observations', {
        method: 'POST',
        body: {
          category,
          statement,
          evidence: [{ type: 'manual_entry', recorded_at: new Date().toISOString() }],
          confidence: 1,
          status: 'accepted',
          pinned: false,
          source: 'manual',
        },
      }),
    onSuccess: async () => {
      await refresh()
      setStatement('')
      setAdding(false)
      push('Profile observation accepted', {
        description: 'The local soul.md projection was regenerated.',
        tone: 'success',
      })
    },
    onError: (error: Error) =>
      push('Observation not saved', { description: error.message, tone: 'danger' }),
  })
  const updateMutation = useMutation({
    mutationFn: ({ id, values }: { id: string; values: Record<string, unknown> }) =>
      api<ProfileObservation>(`/api/profile/observations/${id}`, {
        method: 'PATCH',
        body: values,
      }),
    onSuccess: async () => {
      await refresh()
      setEditingId(null)
    },
  })
  const inferMutation = useMutation({
    mutationFn: () =>
      api<{ observations: ProfileObservation[] }>('/api/profile/infer', { method: 'POST' }),
    onSuccess: async (result) => {
      await refresh()
      push('Evidence scan complete', {
        description: `${result.observations.length} evidence-backed proposal(s) are ready to inspect.`,
        tone: 'success',
      })
    },
    onError: (error: Error) =>
      push('Evidence scan failed', { description: error.message, tone: 'danger' }),
  })
  const observations = observationsQuery.data?.observations ?? []
  const accepted = observations.filter((item) => item.status === 'accepted').length
  const proposed = observations.filter((item) => item.status === 'proposed').length
  const pinned = observations.filter((item) => item.pinned).length
  const submit = (event: FormEvent) => {
    event.preventDefault()
    createMutation.mutate()
  }

  return (
    <div className="page learning-page profile-page">
      <PageHeader
        eyebrow="Personal model"
        title="Make personalization transparent and editable."
        description="Studium proposes observations from learning evidence. Nothing influences Create, Review, Retention, or Backlog until you accept or pin it."
        actions={
          <div className="page-action-row">
            <Button variant="secondary" loading={inferMutation.isPending} onClick={() => inferMutation.mutate()}>
              <RefreshCw size={14} /> Scan learning evidence
            </Button>
            <Button variant="primary" onClick={() => setAdding((value) => !value)}>
              <Plus size={14} /> Add observation
            </Button>
          </div>
        }
      />

      <div className="learning-stat-row">
        <Stat icon={<ShieldCheck />} value={accepted} label="Accepted" tone="success" />
        <Stat icon={<Sparkles />} value={proposed} label="Proposed" tone="accent" />
        <Stat icon={<Pin />} value={pinned} label="Pinned context" />
        <Stat icon={<FileText />} value={observations.reduce((count, item) => count + item.evidence.length, 0)} label="Evidence links" />
      </div>

      {adding && (
        <Panel className="learning-inline-form profile-add-form">
          <form onSubmit={submit}>
            <div><p className="eyebrow">Manual context</p><h2>Tell Studium what should guide adaptation.</h2></div>
            <Field label="Category">
              <select className="input" value={category} onChange={(event) => setCategory(event.target.value as ProfileObservation['category'])}>
                {CATEGORIES.map((item) => <option value={item} key={item}>{label(item)}</option>)}
              </select>
            </Field>
            <Field label="Observation">
              <Textarea value={statement} onChange={(event) => setStatement(event.target.value)} rows={3} required autoFocus />
            </Field>
            <div>
              <Button type="submit" variant="primary" loading={createMutation.isPending}>Accept observation</Button>
              <Button variant="ghost" onClick={() => setAdding(false)}>Cancel</Button>
            </div>
          </form>
        </Panel>
      )}

      <div className="profile-workspace">
        <Panel className="profile-observations">
          <header>
            <div>
              <p className="eyebrow">Structured observations</p>
              <h2>Evidence before adaptation</h2>
            </div>
            <div className="learning-filter-tabs" role="tablist" aria-label="Profile status">
              {(['all', 'proposed', 'accepted', 'rejected', 'disabled'] as const).map((value) => (
                <button
                  type="button"
                  role="tab"
                  aria-selected={filter === value}
                  className={filter === value ? 'active' : ''}
                  key={value}
                  onClick={() => setFilter(value)}
                >
                  {label(value)}
                </button>
              ))}
            </div>
          </header>
          {observationsQuery.isLoading ? (
            <div className="learning-loading"><LoaderCircle className="spin" /></div>
          ) : observations.length === 0 ? (
            <EmptyState
              icon={<Sparkles size={24} />}
              title="No observations in this view"
              description="Add context manually or scan retention and backlog evidence for reviewable proposals."
              action={<Button onClick={() => setAdding(true)}>Add context</Button>}
            />
          ) : (
            <div className="profile-observation-list">
              {observations.map((item) => (
                <article className={clsx('profile-observation', `profile-observation--${item.status}`)} key={item.id}>
                  <header>
                    <div>
                      <Badge tone={item.status === 'accepted' ? 'success' : item.status === 'proposed' ? 'accent' : 'neutral'}>
                        {item.status}
                      </Badge>
                      <Badge>{label(item.category)}</Badge>
                    </div>
                    <span>{Math.round(item.confidence * 100)}% confidence</span>
                  </header>
                  {editingId === item.id ? (
                    <div className="profile-observation__edit">
                      <Input value={editingStatement} onChange={(event) => setEditingStatement(event.target.value)} autoFocus />
                      <Button size="small" variant="primary" onClick={() => updateMutation.mutate({ id: item.id, values: { statement: editingStatement } })}>
                        Save
                      </Button>
                      <Button size="small" variant="ghost" onClick={() => setEditingId(null)}>Cancel</Button>
                    </div>
                  ) : <p>{item.statement}</p>}
                  <details>
                    <summary>{item.evidence.length} evidence link{item.evidence.length === 1 ? '' : 's'} · {item.source}</summary>
                    {item.evidence.length ? (
                      <pre>{JSON.stringify(item.evidence, null, 2)}</pre>
                    ) : <span>No linked evidence; this was entered manually.</span>}
                  </details>
                  <footer>
                    {item.status === 'proposed' && (
                      <>
                        <Button size="small" variant="primary" onClick={() => updateMutation.mutate({ id: item.id, values: { status: 'accepted' } })}>
                          <Check size={12} /> Accept
                        </Button>
                        <Button size="small" variant="ghost" onClick={() => updateMutation.mutate({ id: item.id, values: { status: 'rejected' } })}>
                          <X size={12} /> Reject
                        </Button>
                      </>
                    )}
                    <Button size="small" variant="ghost" onClick={() => updateMutation.mutate({ id: item.id, values: { pinned: !item.pinned } })}>
                      <Pin size={12} /> {item.pinned ? 'Unpin' : 'Pin'}
                    </Button>
                    <Button size="small" variant="ghost" onClick={() => {
                      setEditingId(item.id)
                      setEditingStatement(item.statement)
                    }}>
                      <Pencil size={12} /> Edit
                    </Button>
                    <Button size="small" variant="ghost" onClick={() => updateMutation.mutate({ id: item.id, values: { status: item.status === 'disabled' ? 'accepted' : 'disabled' } })}>
                      <EyeOff size={12} /> {item.status === 'disabled' ? 'Enable' : 'Disable'}
                    </Button>
                  </footer>
                </article>
              ))}
            </div>
          )}
        </Panel>

        <Panel className="soul-panel">
          <header>
            <div><FileText size={18} /><span><p className="eyebrow">Local projection</p><h2>soul.md</h2></span></div>
            <Badge tone="success">Local only</Badge>
          </header>
          <p>
            Human-readable accepted context used by recommendation, review, scheduling,
            and priority services. Proposed or rejected observations are excluded.
          </p>
          <code>{soulQuery.data?.path ?? 'Preparing local profile path…'}</code>
          <div className="soul-preview">
            {soulQuery.isLoading ? <LoaderCircle className="spin" /> : <Markdown value={soulQuery.data?.markdown ?? ''} />}
          </div>
        </Panel>
      </div>
    </div>
  )
}

function Stat({
  icon,
  value,
  label: text,
  tone = 'neutral',
}: {
  icon: React.ReactNode
  value: number
  label: string
  tone?: 'neutral' | 'success' | 'accent'
}) {
  return (
    <Panel className={`learning-stat learning-stat--${tone}`}>
      <span>{icon}</span>
      <div><strong>{value}</strong><small>{text}</small></div>
    </Panel>
  )
}

function label(value: string) {
  return value.replaceAll('_', ' ').replace(/\b\w/g, (letter) => letter.toUpperCase())
}


import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import clsx from 'clsx'
import {
  Activity,
  ArrowRight,
  CircleGauge,
  GitBranch,
  LayoutDashboard,
  LoaderCircle,
  RefreshCw,
  Sparkles,
  TimerReset,
  TrendingUp,
} from 'lucide-react'
import { lazy, Suspense, useCallback, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useToast } from '../components/toast-context'
import { Badge, Button, EmptyState, PageHeader, Panel } from '../components/ui'
import { api } from '../lib/api'
import type { GraphProjection, MasteryRecord, MasterySummary } from '../lib/types'

const KnowledgeGraph = lazy(() =>
  import('../components/KnowledgeGraph').then((module) => ({ default: module.KnowledgeGraph })),
)

export function MasteryPage() {
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const { push } = useToast()
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [domain, setDomain] = useState('')
  const summaryQuery = useQuery({
    queryKey: ['mastery', 'summary'],
    queryFn: () => api<MasterySummary>('/api/mastery/summary'),
  })
  const graphQuery = useQuery({
    queryKey: ['mastery', 'graph'],
    queryFn: () => api<GraphProjection>('/api/mastery/graph'),
  })
  const recomputeMutation = useMutation({
    mutationFn: () =>
      api<{ concepts: MasteryRecord[] }>('/api/mastery/recompute', {
        method: 'POST',
        body: { concept_id: null },
      }),
    onSuccess: async (result) => {
      await queryClient.invalidateQueries({ queryKey: ['mastery'] })
      push('Mastery evidence refreshed', {
        description: `${result.concepts.length} accepted concepts were recomputed.`,
        tone: 'success',
      })
    },
    onError: (error: Error) =>
      push('Mastery refresh failed', { description: error.message, tone: 'danger' }),
  })
  const records = summaryQuery.data?.concepts ?? []
  const filtered = domain ? records.filter((record) => record.domains.includes(domain)) : records
  const selected = filtered.find((record) => record.concept_id === selectedId) ?? filtered[0] ?? null
  const domains = summaryQuery.data?.domains ?? []
  const graph = useMemo(() => {
    if (!graphQuery.data || !domain) return graphQuery.data
    const allowed = new Set(
      graphQuery.data.nodes.filter((node) => node.domains.includes(domain)).map((node) => node.id),
    )
    return {
      ...graphQuery.data,
      nodes: graphQuery.data.nodes.filter((node) => allowed.has(node.id)),
      edges: graphQuery.data.edges.filter((edge) => allowed.has(edge.source) && allowed.has(edge.target)),
    }
  }, [domain, graphQuery.data])
  const selectGraphNode = useCallback((conceptId: string) => setSelectedId(conceptId), [])

  if (summaryQuery.isLoading) {
    return <div className="page"><Panel className="learning-loading"><LoaderCircle className="spin" /> Aggregating learning evidence…</Panel></div>
  }

  return (
    <div className="page learning-page mastery-page">
      <PageHeader
        eyebrow="Mastery"
        title="See what is strong, fragile, and worth doing next."
        description="Acceptance is not mastery. Scores combine retention outcomes, module completion, Agent Review, recency, and graph dependencies with visible weights."
        actions={
          <Button variant="primary" loading={recomputeMutation.isPending} onClick={() => recomputeMutation.mutate()}>
            <RefreshCw size={14} /> Recompute evidence
          </Button>
        }
      />

      <div className="learning-stat-row">
        <Stat icon={<CircleGauge />} value={`${Math.round((summaryQuery.data?.average_score ?? 0) * 100)}%`} label="Average evidence" />
        <Stat icon={<TrendingUp />} value={summaryQuery.data?.state_counts.strong ?? 0} label="Strong concepts" tone="success" />
        <Stat icon={<Activity />} value={summaryQuery.data?.state_counts.fragile ?? 0} label="Fragile concepts" tone="danger" />
        <Stat icon={<GitBranch />} value={records.reduce((count, record) => count + record.weak_prerequisites.length, 0)} label="Weak prerequisites" />
      </div>

      {records.length === 0 ? (
        <Panel>
          <EmptyState
            icon={<LayoutDashboard size={25} />}
            title="No mastery evidence yet"
            description="Accept concepts and complete retention reviews, then compute your first evidence snapshot."
            action={<Button variant="primary" onClick={() => recomputeMutation.mutate()}>Compute mastery</Button>}
          />
        </Panel>
      ) : (
        <>
          <div className="mastery-domain-strip">
            <button type="button" className={!domain ? 'active' : ''} onClick={() => setDomain('')}>
              <span>All domains</span><strong>{records.length}</strong>
            </button>
            {domains.map((item) => (
              <button type="button" className={domain === item.domain ? 'active' : ''} key={item.domain} onClick={() => setDomain(item.domain)}>
                <span>{label(item.domain)}</span>
                <strong>{Math.round(item.score * 100)}%</strong>
                <i style={{ width: `${item.score * 100}%` }} />
              </button>
            ))}
          </div>

          <div className="mastery-workspace">
            <Panel className="mastery-graph-panel">
              <header>
                <div><p className="eyebrow">Prerequisite flow</p><h2>Evidence overlay</h2></div>
                <div className="mastery-legend">
                  {(['strong', 'developing', 'fragile', 'unassessed'] as const).map((state) => (
                    <span key={state} data-state={state}><i /> {label(state)}</span>
                  ))}
                </div>
              </header>
              {graph ? (
                <Suspense fallback={<div className="learning-loading"><LoaderCircle className="spin" /></div>}>
                  <KnowledgeGraph graph={graph} onSelect={selectGraphNode} mode="mastery" />
                </Suspense>
              ) : <div className="learning-loading"><LoaderCircle className="spin" /></div>}
            </Panel>

            <Panel className="mastery-detail">
              {selected ? (
                <>
                  <header>
                    <div className={`mastery-score mastery-score--${selected.state}`}>
                      <strong>{Math.round(selected.score * 100)}</strong><span>%</span>
                    </div>
                    <div>
                      <p className="eyebrow">{selected.domains.map(label).join(' · ')}</p>
                      <h2>{selected.concept_title}</h2>
                      <Badge tone={stateTone(selected.state)}>{label(selected.state)}</Badge>
                    </div>
                  </header>
                  <section className="mastery-evidence">
                    <p className="eyebrow">Evidence breakdown</p>
                    {Object.entries(selected.signals).map(([name, value]) => (
                      <div key={name}>
                        <span>{label(name)}</span>
                        <code>{summarizeSignal(value)}</code>
                      </div>
                    ))}
                  </section>
                  {selected.trend.length > 1 && (
                    <section className="mastery-trend">
                      <p className="eyebrow">Trend snapshots</p>
                      <div>
                        {[...selected.trend].reverse().map((point, index) => (
                          <i
                            key={`${point.created_at}:${index}`}
                            title={`${Math.round(point.score * 100)}% · ${new Date(point.created_at).toLocaleDateString()}`}
                            style={{ height: `${Math.max(8, point.score * 100)}%` }}
                          />
                        ))}
                      </div>
                    </section>
                  )}
                  {selected.weak_prerequisites.length > 0 && (
                    <section className="mastery-prerequisites">
                      <p className="eyebrow">Weak prerequisites</p>
                      {selected.weak_prerequisites.map((item) => (
                        <button type="button" key={item.concept_id} onClick={() => setSelectedId(item.concept_id)}>
                          <GitBranch size={13} />
                          <span><strong>{item.title}</strong><small>{item.reason}</small></span>
                          <Badge tone="warning">{Math.round(item.score * 100)}%</Badge>
                        </button>
                      ))}
                    </section>
                  )}
                  <section className="mastery-actions">
                    <p className="eyebrow">Recommended next actions</p>
                    {selected.recommendations.map((recommendation) => (
                      <div key={recommendation}><Sparkles size={13} /> {recommendation}</div>
                    ))}
                    <footer>
                      <Button variant="primary" onClick={() => navigate('/retention')}>
                        <TimerReset size={14} /> Review weak module
                      </Button>
                      <Button variant="secondary" onClick={() => navigate(`/search?concept=${encodeURIComponent(selected.concept_id)}`)}>
                        Inspect evidence <ArrowRight size={14} />
                      </Button>
                    </footer>
                  </section>
                </>
              ) : null}
            </Panel>
          </div>

          <section className="mastery-concept-list">
            <header><div><p className="eyebrow">Concept evidence</p><h2>Ranked by weakest signal</h2></div><Badge>{filtered.length}</Badge></header>
            <div>
              {filtered.map((record) => (
                <button
                  type="button"
                  key={record.concept_id}
                  className={clsx(record.concept_id === selected?.concept_id && 'active')}
                  onClick={() => setSelectedId(record.concept_id)}
                >
                  <span className={`mastery-dot mastery-dot--${record.state}`} />
                  <span><strong>{record.concept_title}</strong><small>{record.domains.map(label).join(' · ')}</small></span>
                  <i><b style={{ width: `${record.score * 100}%` }} /></i>
                  <strong>{Math.round(record.score * 100)}%</strong>
                </button>
              ))}
            </div>
          </section>
        </>
      )}
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
  value: number | string
  label: string
  tone?: 'neutral' | 'success' | 'danger'
}) {
  return (
    <Panel className={`learning-stat learning-stat--${tone}`}>
      <span>{icon}</span>
      <div><strong>{value}</strong><small>{text}</small></div>
    </Panel>
  )
}

function stateTone(state: MasteryRecord['state']) {
  if (state === 'strong') return 'success' as const
  if (state === 'developing') return 'blue' as const
  if (state === 'fragile') return 'warning' as const
  return 'neutral' as const
}

function summarizeSignal(value: unknown) {
  if (typeof value !== 'object' || value === null) return String(value)
  return Object.entries(value)
    .map(([key, item]) => `${label(key)}: ${typeof item === 'number' ? Math.round(item * 100) / 100 : String(item)}`)
    .join(' · ')
}

function label(value: string) {
  return value.replaceAll('_', ' ').replace(/\b\w/g, (letter) => letter.toUpperCase())
}


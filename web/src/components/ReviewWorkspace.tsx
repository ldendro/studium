import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import clsx from 'clsx'
import {
  AlertTriangle,
  ArrowRight,
  Check,
  CheckCircle2,
  FileCheck2,
  GitPullRequestArrow,
  LoaderCircle,
  MessageSquareText,
  Play,
  RotateCcw,
  ShieldCheck,
  Sparkles,
  X,
} from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { api } from '../lib/api'
import type {
  AcceptanceGate,
  ConceptDetail,
  ReviewFinding,
  ReviewQueueItem,
  ReviewReadiness,
  ReviewSession,
} from '../lib/types'
import { useToast } from './toast-context'
import { Badge, Button, EmptyState, Panel, Textarea } from './ui'

interface ReviewWorkspaceProps {
  selectedConceptId: string | null
  onSelectConcept: (conceptId: string | null) => void
  onCreate: () => void
  onAccepted: (conceptId: string) => void
}

export function ReviewWorkspace({
  selectedConceptId,
  onSelectConcept,
  onCreate,
  onAccepted,
}: ReviewWorkspaceProps) {
  const queryClient = useQueryClient()
  const { push } = useToast()
  const queueQuery = useQuery({
    queryKey: ['review-queue'],
    queryFn: () => api<{ items: ReviewQueueItem[] }>('/api/review/queue'),
  })
  const items = queueQuery.data?.items ?? []
  const selectedId = selectedConceptId ?? items[0]?.concept_id ?? null
  const selectedItem = items.find((item) => item.concept_id === selectedId) ?? null

  useEffect(() => {
    if (!selectedConceptId && selectedId) onSelectConcept(selectedId)
  }, [onSelectConcept, selectedConceptId, selectedId])

  const sessionQuery = useQuery({
    queryKey: ['review-session', selectedItem?.latest_review?.id],
    queryFn: () =>
      api<ReviewSession>(`/api/review/sessions/${selectedItem?.latest_review?.id}`),
    enabled: Boolean(selectedItem?.latest_review?.id),
  })
  const conceptQuery = useQuery({
    queryKey: ['concept-detail', selectedId, 'review'],
    queryFn: () => api<ConceptDetail>(`/api/concepts/${selectedId}`),
    enabled: Boolean(selectedId),
  })
  const gateQuery = useQuery({
    queryKey: ['review-gate', selectedId, sessionQuery.data?.id],
    queryFn: () => api<AcceptanceGate>(`/api/review/concepts/${selectedId}/gate`),
    enabled: Boolean(selectedId && sessionQuery.data),
  })

  const refreshReview = async () => {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ['review-queue'] }),
      queryClient.invalidateQueries({ queryKey: ['review-session'] }),
      queryClient.invalidateQueries({ queryKey: ['review-gate'] }),
      queryClient.invalidateQueries({ queryKey: ['concept-detail'] }),
    ])
  }

  const submitMutation = useMutation({
    mutationFn: (conceptId: string) =>
      api<{ review: ReviewSession }>('/api/review/submit', {
        method: 'POST',
        body: { concept_id: conceptId },
      }),
    onSuccess: async (result) => {
      await refreshReview()
      queryClient.setQueryData(['review-session', result.review.id], result.review)
      push('Review completed', {
        description: `${result.review.summary.critical_count} critical and ${result.review.summary.recommended_count} recommended findings.`,
        tone: result.review.summary.open_critical_count ? 'warning' : 'success',
      })
    },
    onError: (error: Error) =>
      push('Review could not run', { description: error.message, tone: 'danger' }),
  })

  const decisionMutation = useMutation({
    mutationFn: ({
      finding,
      action,
      replacement,
      decisionNote,
    }: {
      finding: ReviewFinding
      action: 'accept' | 'edit' | 'reject' | 'resolve' | 'reopen'
      replacement?: string
      decisionNote?: string
    }) =>
      api(`/api/review/findings/${finding.id}/decision`, {
        method: 'POST',
        body: {
          action,
          replacement: replacement ?? null,
          decision_note: decisionNote ?? null,
        },
      }),
    onSuccess: async () => {
      await refreshReview()
      push('Finding updated', {
        description: 'The review report and acceptance gate were recalculated.',
        tone: 'success',
      })
    },
    onError: (error: Error) =>
      push('Finding update failed', { description: error.message, tone: 'danger' }),
  })

  if (queueQuery.isLoading) {
    return (
      <Panel className="review-loading">
        <LoaderCircle className="spin" />
        Loading committed drafts…
      </Panel>
    )
  }
  if (queueQuery.isError) {
    return (
      <Panel className="review-loading review-loading--error">
        <AlertTriangle />
        <strong>Review queue unavailable</strong>
        <span>{queueQuery.error.message}</span>
      </Panel>
    )
  }
  if (!items.length) {
    return (
      <Panel className="review-empty">
        <EmptyState
          icon={<ShieldCheck size={25} />}
          title="No committed drafts need review"
          description="Create and safely commit a draft first. Agent Review will keep it out of accepted Search until every blocking finding is resolved."
          action={<Button variant="primary" onClick={onCreate}>Create a draft</Button>}
        />
      </Panel>
    )
  }

  return (
    <div className="review-layout">
      <Panel className="review-queue">
        <header>
          <div>
            <p className="eyebrow">Committed drafts</p>
            <strong>{items.length} awaiting acceptance</strong>
          </div>
          <Badge tone="accent">{items.length}</Badge>
        </header>
        <div className="review-queue__list">
          {items.map((item) => (
            <button
              type="button"
              className={clsx('review-queue__row', item.concept_id === selectedId && 'active')}
              key={item.concept_id}
              onClick={() => onSelectConcept(item.concept_id)}
            >
              <span className="review-queue__icon"><FileCheck2 size={16} /></span>
              <span>
                <strong>{item.canonical_title}</strong>
                <small>{item.file_path}</small>
                <i>
                  <Badge tone={readinessTone(item.latest_review?.readiness)}>
                    {item.latest_review ? label(item.latest_review.readiness) : 'Not reviewed'}
                  </Badge>
                  {item.open_critical_count > 0 && (
                    <Badge tone="danger">{item.open_critical_count} blocking</Badge>
                  )}
                </i>
              </span>
              <ArrowRight size={14} />
            </button>
          ))}
        </div>
        <footer>
          <Button variant="ghost" size="small" onClick={onCreate}>
            <Sparkles size={14} /> New learning session
          </Button>
        </footer>
      </Panel>

      <section className="review-detail">
        {!selectedItem ? null : (
          <ReviewDetail
            item={selectedItem}
            concept={conceptQuery.data ?? null}
            conceptLoading={conceptQuery.isLoading}
            session={sessionQuery.data ?? null}
            sessionLoading={sessionQuery.isLoading}
            gate={gateQuery.data ?? null}
            submitting={submitMutation.isPending}
            deciding={decisionMutation.isPending}
            onSubmit={() => submitMutation.mutate(selectedItem.concept_id)}
            onDecision={(finding, action, replacement, decisionNote) =>
              decisionMutation.mutate({ finding, action, replacement, decisionNote })
            }
            onRefresh={refreshReview}
            onAccepted={onAccepted}
          />
        )}
      </section>
    </div>
  )
}

function ReviewDetail({
  item,
  concept,
  conceptLoading,
  session,
  sessionLoading,
  gate,
  submitting,
  deciding,
  onSubmit,
  onDecision,
  onRefresh,
  onAccepted,
}: {
  item: ReviewQueueItem
  concept: ConceptDetail | null
  conceptLoading: boolean
  session: ReviewSession | null
  sessionLoading: boolean
  gate: AcceptanceGate | null
  submitting: boolean
  deciding: boolean
  onSubmit: () => void
  onDecision: (
    finding: ReviewFinding,
    action: 'accept' | 'edit' | 'reject' | 'resolve' | 'reopen',
    replacement?: string,
    decisionNote?: string,
  ) => void
  onRefresh: () => Promise<void>
  onAccepted: (conceptId: string) => void
}) {
  const [activeFinding, setActiveFinding] = useState<string | null>(null)
  const active = session?.findings.find((item) => item.id === activeFinding) ?? null

  return (
    <div className="review-workspace">
      <header className="review-workspace__header">
        <div>
          <p className="eyebrow">Agent Review</p>
          <h2>{item.canonical_title}</h2>
          <span>{item.file_path}</span>
        </div>
        <div>
          {session && (
            <Badge tone={readinessTone(session.readiness)}>{label(session.readiness)}</Badge>
          )}
          <Button variant="secondary" loading={submitting} onClick={onSubmit}>
            {session ? <RotateCcw size={14} /> : <Play size={14} />}
            {session ? 'Re-review' : 'Run review'}
          </Button>
        </div>
      </header>

      {!session && !sessionLoading ? (
        <div className="review-start">
          <ShieldCheck size={31} />
          <h3>Run a review before promotion.</h3>
          <p>
            Studium checks structure, essential module coverage, conceptual placeholders,
            relationships, and source grounding. A configured model adds conservative
            conceptual comments.
          </p>
          <Button variant="primary" size="large" loading={submitting} onClick={onSubmit}>
            Run Agent Review <ArrowRight size={15} />
          </Button>
        </div>
      ) : sessionLoading || conceptLoading ? (
        <div className="review-start"><LoaderCircle className="spin" /> Loading review report…</div>
      ) : session && concept ? (
        <div className="review-document-layout">
          <div className="review-document">
            <div className="review-document__bar">
              <span><GitPullRequestArrow size={14} /> Reviewed Markdown</span>
              <small>{session.summary.agent_mode.replace('provider:', '')}</small>
            </div>
            <AnchoredDocument markdown={concept.raw_markdown} finding={active} />
          </div>
          <aside className="review-rail">
            <div className="review-summary">
              <div>
                <span className={session.summary.open_critical_count ? 'danger' : 'success'}>
                  {session.summary.open_critical_count ? <AlertTriangle /> : <CheckCircle2 />}
                </span>
                <div>
                  <strong>
                    {session.summary.open_critical_count
                      ? `${session.summary.open_critical_count} acceptance blocker${session.summary.open_critical_count === 1 ? '' : 's'}`
                      : 'No critical blockers'}
                  </strong>
                  <small>{session.summary.open_recommended_count} recommendations remain</small>
                </div>
              </div>
              <dl>
                <div><dt>Critical</dt><dd>{session.summary.critical_count}</dd></div>
                <div><dt>Recommended</dt><dd>{session.summary.recommended_count}</dd></div>
                <div><dt>Optional</dt><dd>{session.summary.optional_count}</dd></div>
              </dl>
            </div>
            <div className="review-findings">
              {session.findings.length ? session.findings.map((finding) => (
                <FindingCard
                  key={finding.id}
                  finding={finding}
                  active={activeFinding === finding.id}
                  busy={deciding}
                  onActivate={() => setActiveFinding(finding.id)}
                  onDecision={(action, replacement, note) =>
                    onDecision(finding, action, replacement, note)
                  }
                />
              )) : (
                <div className="review-no-findings">
                  <CheckCircle2 size={20} />
                  No findings. This draft is structurally ready.
                </div>
              )}
            </div>
            <AcceptancePanel
              conceptId={item.concept_id}
              gate={gate}
              onRefresh={onRefresh}
              onAccepted={onAccepted}
            />
          </aside>
        </div>
      ) : null}
    </div>
  )
}

function AnchoredDocument({
  markdown,
  finding,
}: {
  markdown: string
  finding: ReviewFinding | null
}) {
  const parts = useMemo(() => {
    if (!finding?.quoted_text) return { before: markdown, match: '', after: '' }
    const index = markdown.indexOf(finding.quoted_text)
    if (index < 0) return { before: markdown, match: '', after: '' }
    return {
      before: markdown.slice(0, index),
      match: finding.quoted_text,
      after: markdown.slice(index + finding.quoted_text.length),
    }
  }, [finding, markdown])
  return (
    <pre className="review-markdown" aria-label="Reviewed Markdown document">
      {parts.before}
      {parts.match && <mark className={`review-anchor--${finding?.severity}`}>{parts.match}</mark>}
      {parts.after}
    </pre>
  )
}

function FindingCard({
  finding,
  active,
  busy,
  onActivate,
  onDecision,
}: {
  finding: ReviewFinding
  active: boolean
  busy: boolean
  onActivate: () => void
  onDecision: (
    action: 'accept' | 'edit' | 'reject' | 'resolve' | 'reopen',
    replacement?: string,
    note?: string,
  ) => void
}) {
  const [editing, setEditing] = useState(false)
  const [replacement, setReplacement] = useState(finding.proposed_patch ?? '')
  const closed = finding.status === 'applied' || finding.status === 'resolved'
  return (
    <article
      className={clsx(
        'review-finding',
        `review-finding--${finding.severity}`,
        active && 'active',
        closed && 'resolved',
      )}
      onClick={onActivate}
    >
      <header>
        <span><MessageSquareText size={13} /> {label(finding.category)}</span>
        <div>
          <Badge tone={severityTone(finding.severity)}>{finding.severity}</Badge>
          {finding.status !== 'open' && <Badge>{finding.status}</Badge>}
        </div>
      </header>
      <p>{finding.message}</p>
      {finding.anchor?.line_start && <small>Line {finding.anchor.line_start}</small>}
      {finding.quoted_text && <blockquote>{finding.quoted_text}</blockquote>}
      {finding.proposed_patch && !editing && (
        <div className="review-patch">
          <span>Suggested replacement</span>
          <code>{finding.proposed_patch}</code>
        </div>
      )}
      {editing && (
        <div className="review-patch-editor" onClick={(event) => event.stopPropagation()}>
          <Textarea value={replacement} rows={4} onChange={(event) => setReplacement(event.target.value)} />
          <div>
            <Button size="small" variant="primary" disabled={!replacement.trim()} onClick={() => onDecision('edit', replacement)}>
              Apply edited patch
            </Button>
            <Button size="small" variant="ghost" onClick={() => setEditing(false)}>Cancel</Button>
          </div>
        </div>
      )}
      <footer onClick={(event) => event.stopPropagation()}>
        {closed ? (
          <Button size="small" variant="ghost" onClick={() => onDecision('reopen')}>
            <RotateCcw size={12} /> Reopen
          </Button>
        ) : (
          <>
            {finding.proposed_patch && (
              <Button size="small" variant="primary" loading={busy} onClick={() => onDecision('accept')}>
                <Check size={12} /> Accept patch
              </Button>
            )}
            {finding.proposed_patch && (
              <Button size="small" variant="secondary" onClick={() => setEditing(true)}>Edit</Button>
            )}
            <Button size="small" variant="ghost" onClick={() => onDecision('resolve', undefined, 'Resolved manually after review.')}>
              Mark resolved
            </Button>
            <Button size="small" variant="ghost" onClick={() => onDecision('reject')}>
              <X size={12} /> Reject
            </Button>
          </>
        )}
      </footer>
    </article>
  )
}

function AcceptancePanel({
  conceptId,
  gate,
  onRefresh,
  onAccepted,
}: {
  conceptId: string
  gate: AcceptanceGate | null
  onRefresh: () => Promise<void>
  onAccepted: (conceptId: string) => void
}) {
  const { push } = useToast()
  const [acknowledged, setAcknowledged] = useState(false)
  const acceptMutation = useMutation({
    mutationFn: () =>
      api(`/api/review/concepts/${conceptId}/accept`, {
        method: 'POST',
        body: { acknowledge_recommended: acknowledged },
      }),
    onSuccess: async () => {
      await onRefresh()
      push('Concept accepted', {
        description: 'Markdown lifecycle metadata was promoted and Search was reindexed.',
        tone: 'success',
      })
      onAccepted(conceptId)
    },
    onError: (error: Error) =>
      push('Acceptance blocked', { description: error.message, tone: 'danger' }),
  })
  if (!gate) return <div className="acceptance-panel"><LoaderCircle className="spin" /></div>
  const enabled = gate.can_accept && (!gate.requires_acknowledgement || acknowledged)
  return (
    <div className={clsx('acceptance-panel', gate.can_accept ? 'ready' : 'blocked')}>
      <header>
        {gate.can_accept ? <ShieldCheck size={19} /> : <AlertTriangle size={19} />}
        <div>
          <strong>{gate.can_accept ? 'Acceptance gate ready' : 'Acceptance gate blocked'}</strong>
          <small>Promotion is an explicit, versioned safe write.</small>
        </div>
      </header>
      {gate.blockers.map((blocker) => (
        <div className="acceptance-blocker" key={blocker}><X size={12} /> {blocker}</div>
      ))}
      {gate.requires_acknowledgement && (
        <label className="acceptance-ack">
          <input
            type="checkbox"
            checked={acknowledged}
            onChange={(event) => setAcknowledged(event.target.checked)}
          />
          I reviewed the remaining recommendations.
        </label>
      )}
      {gate.preview_diff && (
        <details>
          <summary>Preview lifecycle write</summary>
          <pre>{gate.preview_diff}</pre>
        </details>
      )}
      <Button
        variant="primary"
        size="large"
        disabled={!enabled}
        loading={acceptMutation.isPending}
        onClick={() => acceptMutation.mutate()}
      >
        Accept into vault <ShieldCheck size={14} />
      </Button>
    </div>
  )
}

function readinessTone(readiness?: ReviewReadiness) {
  if (readiness === 'approved') return 'success' as const
  if (readiness === 'approved_with_suggestions') return 'warning' as const
  if (readiness === 'needs_revision') return 'danger' as const
  return 'neutral' as const
}

function severityTone(severity: ReviewFinding['severity']) {
  if (severity === 'critical') return 'danger' as const
  if (severity === 'recommended') return 'warning' as const
  return 'blue' as const
}

function label(value: string) {
  return value.replaceAll('_', ' ').replace(/\b\w/g, (letter) => letter.toUpperCase())
}


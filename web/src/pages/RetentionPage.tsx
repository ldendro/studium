import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import clsx from 'clsx'
import {
  ArrowRight,
  Brain,
  CheckCircle2,
  Clock3,
  Eye,
  Flame,
  Layers3,
  LoaderCircle,
  Pin,
  Play,
  RotateCcw,
  Sparkles,
  Target,
  TimerReset,
} from 'lucide-react'
import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useToast } from '../components/toast-context'
import { Badge, Button, EmptyState, PageHeader, Panel, Textarea } from '../components/ui'
import { api } from '../lib/api'
import type { RetentionCard, RetentionReviewResult } from '../lib/types'

type Queue = 'due' | 'overdue' | 'upcoming'

export function RetentionPage() {
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const { push } = useToast()
  const [queue, setQueue] = useState<Queue>('due')
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [response, setResponse] = useState('')
  const [revealed, setRevealed] = useState(false)
  const [rating, setRating] = useState<number | null>(null)
  const [confidence, setConfidence] = useState(3)
  const [startedAt, setStartedAt] = useState(() => Date.now())
  const [result, setResult] = useState<RetentionReviewResult | null>(null)

  const statsQuery = useQuery({
    queryKey: ['retention-stats'],
    queryFn: () =>
      api<{
        due: number
        overdue: number
        upcoming: number
        total_cards: number
        review_count: number
        average_score: number
        study_days: number
        lapses: number
      }>('/api/retention/stats'),
  })
  const cardsQuery = useQuery({
    queryKey: ['retention-cards', queue],
    queryFn: () => api<{ cards: RetentionCard[] }>(`/api/retention/cards?queue=${queue}&limit=200`),
  })
  const cards = cardsQuery.data?.cards ?? []
  const selected = cards.find((card) => card.id === selectedId) ?? cards[0] ?? null

  const resetAttempt = () => {
    setResponse('')
    setRevealed(false)
    setRating(null)
    setResult(null)
  }
  const selectCard = (cardId: string | null) => {
    setSelectedId(cardId)
    resetAttempt()
  }

  const refresh = async () => {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ['retention-cards'] }),
      queryClient.invalidateQueries({ queryKey: ['retention-stats'] }),
      queryClient.invalidateQueries({ queryKey: ['mastery'] }),
    ])
  }
  const generateMutation = useMutation({
    mutationFn: () =>
      api<{ cards: RetentionCard[] }>('/api/retention/cards/generate', {
        method: 'POST',
        body: { concept_id: null },
      }),
    onSuccess: async (data) => {
      await refresh()
      push('Retention queue generated', {
        description: `${data.cards.length} module-specific cards are available.`,
        tone: 'success',
      })
    },
    onError: (error: Error) =>
      push('Card generation failed', { description: error.message, tone: 'danger' }),
  })
  const reviewMutation = useMutation({
    mutationFn: (card: RetentionCard) =>
      api<RetentionReviewResult>('/api/retention/review', {
        method: 'POST',
        body: {
          card_id: card.id,
          response,
          self_rating: rating,
          confidence,
          latency_ms: Date.now() - startedAt,
          hints_used: revealed ? 1 : 0,
        },
      }),
    onSuccess: async (data) => {
      setResult(data)
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['retention-stats'] }),
        queryClient.invalidateQueries({ queryKey: ['mastery'] }),
      ])
      push('Review recorded', {
        description: `Next interval: ${data.next_interval_days} day${data.next_interval_days === 1 ? '' : 's'}.`,
        tone: data.evaluation === 'again' ? 'warning' : 'success',
      })
    },
    onError: (error: Error) =>
      push('Review could not be saved', { description: error.message, tone: 'danger' }),
  })
  const pinMutation = useMutation({
    mutationFn: (card: RetentionCard) =>
      api<RetentionCard>(`/api/retention/cards/${card.id}`, {
        method: 'PATCH',
        body: { pinned: !card.pinned, suspended: null, prompt: null },
      }),
    onSuccess: () => refresh(),
  })
  const queueCounts = {
    due: statsQuery.data?.due ?? 0,
    overdue: statsQuery.data?.overdue ?? 0,
    upcoming: statsQuery.data?.upcoming ?? 0,
  }
  const completion = useMemo(() => {
    const total = (statsQuery.data?.due ?? 0) + (statsQuery.data?.overdue ?? 0)
    return total ? Math.max(0, 1 - cards.length / total) : 1
  }, [cards.length, statsQuery.data])

  return (
    <div className="page learning-page retention-page">
      <PageHeader
        eyebrow="Retention"
        title="Review the weak slice, not the whole note."
        description="Module-specific active recall uses a transparent SM-2-style schedule, graph context, confidence, and observable outcomes."
        actions={
          <Button variant="primary" loading={generateMutation.isPending} onClick={() => generateMutation.mutate()}>
            <Sparkles size={14} /> Generate from accepted notes
          </Button>
        }
      />

      <div className="learning-stat-row">
        <Stat icon={<TimerReset />} value={statsQuery.data?.due ?? 0} label="Due now" />
        <Stat icon={<Clock3 />} value={statsQuery.data?.overdue ?? 0} label="Overdue" tone="danger" />
        <Stat icon={<Target />} value={`${Math.round((statsQuery.data?.average_score ?? 0) * 100)}%`} label="Recall score" />
        <Stat icon={<Flame />} value={statsQuery.data?.study_days ?? 0} label="Study days" tone="accent" />
      </div>

      <div className="retention-session-bar">
        <div>
          <span>Focused queue</span>
          <strong>{cards.length} {queue} card{cards.length === 1 ? '' : 's'}</strong>
        </div>
        <div className="retention-progress"><i style={{ width: `${completion * 100}%` }} /></div>
        <div className="learning-filter-tabs" role="tablist" aria-label="Retention queue">
          {(['due', 'overdue', 'upcoming'] as Queue[]).map((value) => (
            <button
              key={value}
              type="button"
              role="tab"
              aria-selected={queue === value}
              className={queue === value ? 'active' : ''}
              onClick={() => { setQueue(value); selectCard(null) }}
            >
              {label(value)} <span>{queueCounts[value]}</span>
            </button>
          ))}
        </div>
      </div>

      {cardsQuery.isLoading ? (
        <Panel className="learning-loading"><LoaderCircle className="spin" /> Loading focused prompts…</Panel>
      ) : !selected ? (
        <Panel>
          <EmptyState
            icon={<CheckCircle2 size={24} />}
            title={queue === 'upcoming' ? 'No upcoming cards' : `Your ${queue} queue is clear`}
            description="Generate cards from accepted notes, or return when the scheduler surfaces the next weak module."
            action={<Button onClick={() => generateMutation.mutate()}>Generate cards</Button>}
          />
        </Panel>
      ) : (
        <div className="retention-workspace">
          <Panel className="retention-queue">
            <header><span>{label(queue)} queue</span><Badge>{cards.length}</Badge></header>
            <div>
              {cards.map((card) => (
                <button
                  type="button"
                  key={card.id}
                  className={clsx(card.id === selected.id && 'active')}
                  onClick={() => selectCard(card.id)}
                >
                  <span><Layers3 size={14} /></span>
                  <span>
                    <strong>{card.concept_title}</strong>
                    <small>{label(card.module_type ?? 'concept overview')}</small>
                    <i>priority {Math.round(card.priority_score)}</i>
                  </span>
                  {card.pinned && <Pin size={12} />}
                </button>
              ))}
            </div>
          </Panel>

          <Panel className="retention-card">
            <header>
              <div>
                <p className="eyebrow">{label(selected.module_type ?? 'Concept overview')}</p>
                <h2>{selected.concept_title}</h2>
              </div>
              <div>
                <Badge tone={selected.queue === 'overdue' ? 'danger' : 'accent'}>{selected.queue}</Badge>
                <Button size="small" variant="ghost" onClick={() => pinMutation.mutate(selected)}>
                  <Pin size={13} /> {selected.pinned ? 'Unpin' : 'Pin'}
                </Button>
              </div>
            </header>
            <div className="retention-prompt">
              <span><Brain size={18} /></span>
              <p>{selected.prompt}</p>
            </div>
            {selected.prerequisite_context.length > 0 && (
              <div className="retention-context">
                <strong>Prerequisite context</strong>
                <span>{selected.prerequisite_context.join(' · ')}</span>
              </div>
            )}
            <label className="retention-response">
              <span>Your reconstruction</span>
              <Textarea
                rows={9}
                value={response}
                onChange={(event) => setResponse(event.target.value)}
                placeholder="Answer from memory. Reasoning and checks matter more than polished prose."
                disabled={reviewMutation.isPending || Boolean(result)}
              />
            </label>
            {!revealed && !result ? (
              <Button variant="secondary" disabled={!response.trim()} onClick={() => setRevealed(true)}>
                <Eye size={14} /> Reveal expected components
              </Button>
            ) : (
              <div className="retention-reveal">
                <p className="eyebrow">Expected components</p>
                <ul>
                  {selected.expected_components.map((component) => <li key={component}>{component}</li>)}
                </ul>
              </div>
            )}
            {revealed && !result && (
              <div className="retention-evaluation">
                <div>
                  <span>How complete was your recall?</span>
                  <div>
                    {[0, 1, 2, 3, 4, 5].map((value) => (
                      <button type="button" className={rating === value ? 'active' : ''} key={value} onClick={() => setRating(value)}>
                        {value}
                      </button>
                    ))}
                  </div>
                </div>
                <div>
                  <span>Confidence</span>
                  <div>
                    {[1, 2, 3, 4, 5].map((value) => (
                      <button type="button" className={confidence === value ? 'active' : ''} key={value} onClick={() => setConfidence(value)}>
                        {value}
                      </button>
                    ))}
                  </div>
                </div>
                <Button variant="primary" size="large" disabled={rating === null} loading={reviewMutation.isPending} onClick={() => reviewMutation.mutate(selected)}>
                  Record outcome <ArrowRight size={14} />
                </Button>
              </div>
            )}
            {result && (
              <div className={`retention-result retention-result--${result.evaluation}`}>
                <header>
                  <CheckCircle2 size={20} />
                  <div><strong>{label(result.evaluation)}</strong><span>{Math.round(result.score * 100)}% evidence score</span></div>
                  <Badge>next in {result.next_interval_days}d</Badge>
                </header>
                {result.feedback.map((item) => <p key={item}>{item}</p>)}
                <div>
                  <Button variant="primary" onClick={() => {
                    selectCard(cards.find((card) => card.id !== selected.id)?.id ?? null)
                    void refresh()
                  }}>
                    Next card <Play size={13} />
                  </Button>
                  {result.evaluation === 'again' && (
                    <Button variant="secondary" onClick={() => {
                      const params = new URLSearchParams({
                        concept: selected.concept_id,
                        moduleType: 'misconception_debugging',
                        intent: `Debug the misconception exposed while recalling ${selected.concept_title}`,
                      })
                      navigate(`/create?${params}`)
                    }}>
                      <Sparkles size={13} /> Add debugging module
                    </Button>
                  )}
                  <Button variant="ghost" onClick={() => {
                    resetAttempt()
                  }}>
                    <RotateCcw size={13} /> Retry
                  </Button>
                </div>
              </div>
            )}
          </Panel>
        </div>
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
  tone?: 'neutral' | 'danger' | 'accent'
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


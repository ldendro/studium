import type { EditorView } from '@codemirror/view'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import clsx from 'clsx'
import {
  AlertTriangle,
  ArrowDown,
  ArrowLeft,
  ArrowRight,
  ArrowUp,
  Bold,
  BookOpen,
  Check,
  CheckCircle2,
  ChevronRight,
  ClipboardCheck,
  Code2,
  Diff,
  FileClock,
  GitBranch,
  GripVertical,
  Heading2,
  Italic,
  Lightbulb,
  Link,
  List,
  LoaderCircle,
  PenLine,
  Plus,
  Quote,
  Save,
  Search,
  ShieldCheck,
  Sparkles,
  Trash2,
  X,
} from 'lucide-react'
import {
  lazy,
  Suspense,
  useEffect,
  useMemo,
  useRef,
  useState,
  type FormEvent,
  type ReactNode,
} from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { Markdown } from '../components/Markdown'
import { useToast } from '../components/toast-context'
import {
  Badge,
  Button,
  EmptyState,
  Field,
  IconButton,
  Input,
  PageHeader,
  Panel,
  Textarea,
} from '../components/ui'
import { api } from '../lib/api'
import type {
  CreateIntent,
  CreateProposal,
  DraftPreview,
  DraftSnapshot,
  GeneratedDraft,
  ModuleProposal,
} from '../lib/types'

type CreateView = 'new' | 'drafts' | 'review'
type WorkflowStep = 'intent' | 'proposal' | 'editor' | 'commit' | 'done'

const MODULE_TYPES = [
  'conceptual_explanation',
  'worked_example',
  'code_implementation',
  'implementation_notes',
  'comparison',
  'derivation',
  'application',
  'misconception_debugging',
  'custom',
]

const SOURCE_TYPES = [
  'book',
  'paper',
  'article',
  'video',
  'class',
  'documentation',
  'podcast',
  'project',
  'work',
  'chatbot',
]

const MarkdownEditor = lazy(() =>
  import('../components/MarkdownEditor').then((module) => ({
    default: module.MarkdownEditor,
  })),
)

export function CreatePage() {
  const [params] = useSearchParams()
  const navigate = useNavigate()
  const { push } = useToast()
  const queryClient = useQueryClient()
  const initialIntent = params.get('intent') ?? ''
  const targetConcept = params.get('concept')
  const [view, setView] = useState<CreateView>('new')
  const [step, setStep] = useState<WorkflowStep>('intent')
  const [intent, setIntent] = useState<CreateIntent>(() => ({
    intent: initialIntent,
    learning_goal: '',
    user_context: '',
    source_type: null,
    source_title: null,
    source_unit: null,
    source_section: null,
    source_link: null,
    source_id: null,
    target_concept_id: targetConcept,
    target_module_id: null,
    requested_module_type: null,
    scaffold_preferences: [],
    search_context: {},
  }))
  const [proposal, setProposal] = useState<CreateProposal | null>(null)
  const [draft, setDraft] = useState<GeneratedDraft | null>(null)
  const [markdownValue, setMarkdownValue] = useState('')
  const [previewMode, setPreviewMode] = useState<'write' | 'preview'>('write')
  const [snapshotId, setSnapshotId] = useState<string | null>(null)
  const [lastSaved, setLastSaved] = useState<string | null>(null)
  const [approvals, setApprovals] = useState({
    metadata: true,
    graph: true,
    source: true,
  })
  const [commitResult, setCommitResult] = useState<Record<string, unknown> | null>(null)
  const editorRef = useRef<EditorView | null>(null)

  const proposeMutation = useMutation({
    mutationFn: (payload: CreateIntent) =>
      api<CreateProposal>('/api/create/propose', { method: 'POST', body: payload }),
    onSuccess: (result) => {
      setProposal(result)
      setStep('proposal')
    },
    onError: (error: Error) =>
      push('Recommendation failed', { description: error.message, tone: 'danger' }),
  })
  const draftMutation = useMutation({
    mutationFn: (payload: CreateProposal) =>
      api<GeneratedDraft>('/api/create/draft', { method: 'POST', body: payload }),
    onSuccess: (result) => {
      setDraft(result)
      setMarkdownValue(result.markdown)
      setStep('editor')
      setPreviewMode('write')
    },
    onError: (error: Error) =>
      push('Draft generation failed', { description: error.message, tone: 'danger' }),
  })
  const previewMutation = useMutation({
    mutationFn: (payload: GeneratedDraft) =>
      api<DraftPreview>('/api/create/preview', { method: 'POST', body: payload }),
    onSuccess: () => setStep('commit'),
    onError: (error: Error) =>
      push('Preview failed', { description: error.message, tone: 'danger' }),
  })
  const commitMutation = useMutation({
    mutationFn: (payload: GeneratedDraft) =>
      api<Record<string, unknown>>('/api/create/commit', { method: 'POST', body: payload }),
    onSuccess: async (result) => {
      setCommitResult(result)
      setStep('done')
      await queryClient.invalidateQueries()
      push('Draft committed safely', {
        description: 'The Markdown note was written and the index was synchronized.',
        tone: 'success',
      })
    },
    onError: (error: Error) =>
      push('Commit was blocked', { description: error.message, tone: 'danger' }),
  })
  const autosaveMutation = useMutation({
    mutationFn: (payload: {
      draft: GeneratedDraft
      title: string
      recommendation: Record<string, unknown> | null
      snapshot_id: string | null
    }) =>
      api<DraftSnapshot>('/api/create/drafts', { method: 'PUT', body: payload }),
    onSuccess: (saved) => {
      setSnapshotId(saved.id)
      setLastSaved(saved.updated_at)
      void queryClient.invalidateQueries({ queryKey: ['create-drafts'] })
    },
  })
  const autosaveRef = useRef(autosaveMutation.mutate)
  useEffect(() => {
    autosaveRef.current = autosaveMutation.mutate
  }, [autosaveMutation.mutate])
  const draftsQuery = useQuery({
    queryKey: ['create-drafts'],
    queryFn: () => api<{ drafts: DraftSnapshot[] }>('/api/create/drafts'),
    enabled: view === 'drafts',
  })

  const currentDraft = useMemo(
    () => (draft ? { ...draft, markdown: markdownValue } : null),
    [draft, markdownValue],
  )

  useEffect(() => {
    if (!currentDraft || step !== 'editor') return
    window.localStorage.setItem('studium:create-autosave', JSON.stringify(currentDraft))
    const timer = window.setTimeout(() => {
      autosaveRef.current({
        draft: currentDraft,
        title: proposal?.canonical_title ?? currentDraft.concept_id,
        recommendation: proposal?.raw_recommendation ?? null,
        snapshot_id: snapshotId,
      })
    }, 1400)
    return () => window.clearTimeout(timer)
  }, [currentDraft, proposal, snapshotId, step])

  const submitIntent = (event: FormEvent) => {
    event.preventDefault()
    proposeMutation.mutate(intent)
  }

  const generate = () => {
    if (!proposal) return
    draftMutation.mutate({
      ...proposal,
      aliases_to_add: approvals.metadata ? proposal.aliases_to_add : [],
      relationships: proposal.relationships.map((item) => ({
        ...item,
        selected: approvals.graph && item.selected,
      })),
      encounter: proposal.encounter
        ? { ...proposal.encounter, selected: approvals.source && proposal.encounter.selected }
        : null,
    })
  }

  const preview = () => {
    if (currentDraft) previewMutation.mutate(currentDraft)
  }

  const commit = () => {
    if (currentDraft) commitMutation.mutate(currentDraft)
  }

  const reset = () => {
    setStep('intent')
    setProposal(null)
    setDraft(null)
    setMarkdownValue('')
    setSnapshotId(null)
    setCommitResult(null)
    setIntent((current) => ({ ...current, intent: '', target_concept_id: null }))
  }

  const restoreDraft = (saved: DraftSnapshot) => {
    const restored: GeneratedDraft = {
      proposal_id: `restored_${saved.id}`,
      operation: saved.operation,
      concept_id: saved.concept_id,
      target_path: saved.target_path,
      markdown: saved.markdown,
      selected_modules: [],
      warnings: [],
    }
    setDraft(restored)
    setMarkdownValue(saved.markdown)
    setSnapshotId(saved.id)
    setLastSaved(saved.updated_at)
    setView('new')
    setStep('editor')
  }

  return (
    <div className="page create-page">
      <PageHeader
        eyebrow="Create"
        title="Shape understanding before writing."
        description="Every session investigates your vault first, proposes a learning structure, and shows the exact Markdown change before commit."
        actions={
          <div className="create-view-tabs" role="tablist" aria-label="Create workspace">
            <button className={view === 'new' ? 'active' : ''} onClick={() => setView('new')} role="tab">
              <PenLine size={14} /> New
            </button>
            <button className={view === 'drafts' ? 'active' : ''} onClick={() => setView('drafts')} role="tab">
              <FileClock size={14} /> Drafts
              {draftsQuery.data?.drafts.length ? <span>{draftsQuery.data.drafts.length}</span> : null}
            </button>
            <button className={view === 'review' ? 'active' : ''} onClick={() => setView('review')} role="tab">
              <ShieldCheck size={14} /> Review queue
            </button>
          </div>
        }
      />

      {view === 'drafts' ? (
        <DraftLibrary
          drafts={draftsQuery.data?.drafts ?? []}
          loading={draftsQuery.isLoading}
          onRestore={restoreDraft}
          onNew={() => { setView('new'); reset() }}
        />
      ) : view === 'review' ? (
        <ReviewQueuePreview onNew={() => setView('new')} />
      ) : (
        <>
          <WorkflowProgress step={step} />
          {step === 'intent' && (
            <IntentStep
              intent={intent}
              setIntent={setIntent}
              onSubmit={submitIntent}
              loading={proposeMutation.isPending}
            />
          )}
          {step === 'proposal' && proposal && (
            <ProposalStep
              proposal={proposal}
              setProposal={setProposal}
              approvals={approvals}
              setApprovals={setApprovals}
              onBack={() => setStep('intent')}
              onGenerate={generate}
              loading={draftMutation.isPending}
              onOpenMatch={(id) => navigate(`/search?concept=${encodeURIComponent(id)}&q=${encodeURIComponent(intent.intent)}`)}
            />
          )}
          {step === 'editor' && currentDraft && (
            <EditorStep
              draft={currentDraft}
              title={proposal?.canonical_title ?? currentDraft.concept_id}
              markdownValue={markdownValue}
              setMarkdownValue={setMarkdownValue}
              previewMode={previewMode}
              setPreviewMode={setPreviewMode}
              editorRef={editorRef}
              lastSaved={lastSaved}
              saving={autosaveMutation.isPending}
              onBack={() => setStep(proposal ? 'proposal' : 'intent')}
              onPreview={preview}
              previewing={previewMutation.isPending}
            />
          )}
          {step === 'commit' && currentDraft && previewMutation.data && (
            <CommitStep
              draft={currentDraft}
              preview={previewMutation.data}
              onBack={() => setStep('editor')}
              onCommit={commit}
              committing={commitMutation.isPending}
            />
          )}
          {step === 'done' && currentDraft && (
            <DoneStep
              draft={currentDraft}
              result={commitResult}
              onReview={() => setView('review')}
              onInspect={() => navigate(`/search?concept=${encodeURIComponent(currentDraft.concept_id)}`)}
              onNew={reset}
            />
          )}
        </>
      )}
    </div>
  )
}

function WorkflowProgress({ step }: { step: WorkflowStep }) {
  const steps: Array<{ id: WorkflowStep; label: string }> = [
    { id: 'intent', label: 'Investigate' },
    { id: 'proposal', label: 'Shape' },
    { id: 'editor', label: 'Write' },
    { id: 'commit', label: 'Preview' },
  ]
  const current = step === 'done' ? steps.length : steps.findIndex((item) => item.id === step)
  return (
    <div className="workflow-progress" aria-label="Create workflow progress">
      {steps.map((item, index) => (
        <div key={item.id} className={clsx(index <= current && 'active', index < current && 'complete')}>
          <span>{index < current ? <Check size={12} /> : index + 1}</span>
          <strong>{item.label}</strong>
          {index < steps.length - 1 && <i />}
        </div>
      ))}
    </div>
  )
}

function IntentStep({
  intent,
  setIntent,
  onSubmit,
  loading,
}: {
  intent: CreateIntent
  setIntent: React.Dispatch<React.SetStateAction<CreateIntent>>
  onSubmit: (event: FormEvent) => void
  loading: boolean
}) {
  const [sourceOpen, setSourceOpen] = useState(Boolean(intent.source_type))
  return (
    <div className="intent-layout">
      <form className="intent-form" onSubmit={onSubmit}>
        <div className="intent-form__heading">
          <div className="intent-form__icon"><Sparkles size={20} /></div>
          <div>
            <p className="eyebrow">Learning intent</p>
            <h2>What are you trying to understand?</h2>
            <p>Describe the gap, task, or explanation you want—not just a note title.</p>
          </div>
        </div>
        <Field label="Intent or concept">
          <Textarea
            value={intent.intent}
            onChange={(event) => setIntent((current) => ({ ...current, intent: event.target.value }))}
            placeholder="For example: derive the gradient update manually and understand why the negative sign moves toward a minimum"
            rows={4}
            required
            autoFocus
          />
        </Field>
        <Field label="What should you be able to do afterward?" hint="Optional, but improves scaffold selection.">
          <Input
            value={intent.learning_goal}
            onChange={(event) => setIntent((current) => ({ ...current, learning_goal: event.target.value }))}
            placeholder="Explain, calculate, implement, compare…"
          />
        </Field>
        <Field label="Context you want Studium to respect" hint="Constraints, background, or current confusion.">
          <Textarea
            value={intent.user_context}
            onChange={(event) => setIntent((current) => ({ ...current, user_context: event.target.value }))}
            placeholder="I know basic derivatives but chain rule notation still slows me down."
            rows={2}
          />
        </Field>
        <button className="source-toggle" type="button" onClick={() => setSourceOpen((open) => !open)}>
          <BookOpen size={16} />
          <span>
            <strong>Attach encounter context</strong>
            <small>Connect this session to a book, paper, class, or source in your library.</small>
          </span>
          <ChevronRight className={sourceOpen ? 'rotate-90' : ''} size={16} />
        </button>
        {sourceOpen && (
          <div className="source-fields">
            <Field label="Source type">
              <select
                className="input"
                value={intent.source_type ?? ''}
                onChange={(event) =>
                  setIntent((current) => ({ ...current, source_type: event.target.value || null }))
                }
              >
                <option value="">Choose type</option>
                {SOURCE_TYPES.map((type) => <option key={type} value={type}>{formatLabel(type)}</option>)}
              </select>
            </Field>
            <Field label="Source title">
              <Input
                value={intent.source_title ?? ''}
                onChange={(event) => setIntent((current) => ({ ...current, source_title: event.target.value || null }))}
                placeholder="The book, paper, lecture, or article"
              />
            </Field>
            <Field label="Unit / chapter">
              <Input
                value={intent.source_unit ?? ''}
                onChange={(event) => setIntent((current) => ({ ...current, source_unit: event.target.value || null }))}
                placeholder="Chapter 4"
              />
            </Field>
            <Field label="Section">
              <Input
                value={intent.source_section ?? ''}
                onChange={(event) => setIntent((current) => ({ ...current, source_section: event.target.value || null }))}
                placeholder="4.2 Gradient methods"
              />
            </Field>
          </div>
        )}
        <div className="intent-form__actions">
          <span><Search size={14} /> Studium searches your vault before recommending a change.</span>
          <Button type="submit" variant="primary" size="large" loading={loading}>
            Investigate intent <ArrowRight size={16} />
          </Button>
        </div>
      </form>
      <aside className="intent-principles">
        <p className="eyebrow">How Create works</p>
        <h3>No blind generation.</h3>
        <Principle icon={<Search />} title="Investigate first">
          Exact identity, module, semantic, and graph context are checked before creation.
        </Principle>
        <Principle icon={<Lightbulb />} title="Structure for learning">
          Scaffolds ask you to reconstruct, calculate, implement, compare, or diagnose.
        </Principle>
        <Principle icon={<ShieldCheck />} title="Commit explicitly">
          Every note mutation remains a validated WriteProposal with a visible diff.
        </Principle>
      </aside>
    </div>
  )
}

function Principle({ icon, title, children }: { icon: ReactNode; title: string; children: ReactNode }) {
  return (
    <div className="principle">
      <span>{icon}</span>
      <div><strong>{title}</strong><p>{children}</p></div>
    </div>
  )
}

function ProposalStep({
  proposal,
  setProposal,
  approvals,
  setApprovals,
  onBack,
  onGenerate,
  loading,
  onOpenMatch,
}: {
  proposal: CreateProposal
  setProposal: React.Dispatch<React.SetStateAction<CreateProposal | null>>
  approvals: { metadata: boolean; graph: boolean; source: boolean }
  setApprovals: React.Dispatch<React.SetStateAction<{ metadata: boolean; graph: boolean; source: boolean }>>
  onBack: () => void
  onGenerate: () => void
  loading: boolean
  onOpenMatch: (id: string) => void
}) {
  const updateModule = (index: number, values: Partial<ModuleProposal>) =>
    setProposal((current) =>
      current
        ? { ...current, modules: current.modules.map((module, i) => i === index ? { ...module, ...values } : module) }
        : current,
    )
  const moveModule = (from: number, direction: -1 | 1) =>
    setProposal((current) => {
      if (!current) return current
      const to = from + direction
      if (to < 0 || to >= current.modules.length) return current
      const modules = [...current.modules]
      ;[modules[from], modules[to]] = [modules[to], modules[from]]
      return { ...current, modules }
    })
  const removeModule = (index: number) =>
    setProposal((current) =>
      current ? { ...current, modules: current.modules.filter((_, i) => i !== index) } : current,
    )
  const addModule = () =>
    setProposal((current) =>
      current
        ? {
            ...current,
            modules: [
              ...current.modules,
              {
                id: `module_custom_${crypto.randomUUID().slice(0, 8)}`,
                type: 'custom',
                title: 'Custom Practice',
                focus: null,
                selected: true,
                reason: 'Added manually.',
                origin: 'manual',
              },
            ],
          }
        : current,
    )

  return (
    <div className="proposal-layout">
      <section className="proposal-main">
        <div className="recommendation-banner">
          <span className="recommendation-banner__icon"><Sparkles size={20} /></span>
          <div>
            <p className="eyebrow">Recommendation</p>
            <h2>{formatLabel(proposal.action)}</h2>
            <p>{proposal.evidence[0] ?? 'The recommendation is grounded in the current index revision.'}</p>
          </div>
          <div className="recommendation-banner__meta">
            <Badge tone={proposal.confidence === 'high' ? 'success' : 'warning'}>{proposal.confidence} confidence</Badge>
            <Badge>{proposal.reasoning_mode}</Badge>
          </div>
        </div>

        {proposal.possible_matches.length > 0 && (
          <Panel className="possible-matches">
            <div className="proposal-section-heading">
              <div><Search size={16} /><span><strong>Possible existing matches</strong><small>Check before creating a duplicate.</small></span></div>
            </div>
            <div className="match-list">
              {proposal.possible_matches.map((match) => (
                <button type="button" key={match.concept_id} onClick={() => onOpenMatch(match.concept_id)}>
                  <span><strong>{match.title}</strong><small>{match.evidence.join(' · ')}</small></span>
                  <Badge tone={match.vault_status === 'accepted' ? 'success' : 'warning'}>{match.vault_status ?? 'indexed'}</Badge>
                  <ChevronRight size={15} />
                </button>
              ))}
            </div>
          </Panel>
        )}

        <Panel className="proposal-editor">
          <div className="proposal-section-heading">
            <div><PenLine size={16} /><span><strong>Concept identity</strong><small>Edit the proposed metadata before drafting.</small></span></div>
            <ApprovalSwitch
              checked={approvals.metadata}
              onChange={(checked) => setApprovals((current) => ({ ...current, metadata: checked }))}
              label="Apply metadata"
            />
          </div>
          <div className="proposal-metadata-grid">
            <Field label="Canonical title">
              <Input
                value={proposal.canonical_title}
                onChange={(event) => setProposal((current) => current ? { ...current, canonical_title: event.target.value } : current)}
              />
            </Field>
            <Field label="Concept type">
              <select
                className="input"
                value={proposal.concept_type}
                onChange={(event) => setProposal((current) => current ? { ...current, concept_type: event.target.value } : current)}
              >
                {['general_concept', 'mathematical_concept', 'algorithm', 'programming_concept', 'system_design_concept', 'theory_concept', 'process_concept', 'tooling_concept'].map((type) => (
                  <option value={type} key={type}>{formatLabel(type)}</option>
                ))}
              </select>
            </Field>
            <Field label="Domains" hint="Comma-separated controlled slugs.">
              <Input
                value={proposal.domains.join(', ')}
                onChange={(event) =>
                  setProposal((current) =>
                    current
                      ? { ...current, domains: event.target.value.split(',').map((item) => item.trim()).filter(Boolean) }
                      : current,
                  )
                }
              />
            </Field>
            <Field label="Aliases to add">
              <Input
                value={proposal.aliases_to_add.join(', ')}
                onChange={(event) =>
                  setProposal((current) =>
                    current
                      ? { ...current, aliases_to_add: event.target.value.split(',').map((item) => item.trim()).filter(Boolean) }
                      : current,
                  )
                }
              />
            </Field>
          </div>
        </Panel>

        <Panel className="proposal-editor">
          <div className="proposal-section-heading">
            <div><ClipboardCheck size={16} /><span><strong>Active-learning scaffold</strong><small>Select, edit, and order independent practice modules.</small></span></div>
            <Button variant="ghost" size="small" onClick={addModule}><Plus size={14} /> Add module</Button>
          </div>
          <div className="module-proposals">
            {proposal.modules.map((module, index) => (
              <div className={clsx('module-proposal', !module.selected && 'module-proposal--off')} key={module.id}>
                <GripVertical size={15} />
                <label className="check-control">
                  <input type="checkbox" checked={module.selected} onChange={(event) => updateModule(index, { selected: event.target.checked })} />
                  <span />
                </label>
                <div className="module-proposal__fields">
                  <Input value={module.title} onChange={(event) => updateModule(index, { title: event.target.value })} />
                  <div>
                    <select className="input" value={module.type} onChange={(event) => updateModule(index, { type: event.target.value })}>
                      {MODULE_TYPES.map((type) => <option key={type} value={type}>{formatLabel(type)}</option>)}
                    </select>
                    <Input value={module.focus ?? ''} onChange={(event) => updateModule(index, { focus: event.target.value || null })} placeholder="Optional focus" />
                  </div>
                  <small>{module.reason}</small>
                </div>
                <div className="module-proposal__actions">
                  <IconButton label="Move module up" onClick={() => moveModule(index, -1)} disabled={index === 0}><ArrowUp size={14} /></IconButton>
                  <IconButton label="Move module down" onClick={() => moveModule(index, 1)} disabled={index === proposal.modules.length - 1}><ArrowDown size={14} /></IconButton>
                  <IconButton label="Remove module" onClick={() => removeModule(index)}><Trash2 size={14} /></IconButton>
                </div>
              </div>
            ))}
            {proposal.modules.length === 0 && (
              <EmptyState compact title="No expansion needed yet" description="Add a module if this existing concept needs a specific new learning surface." action={<Button onClick={addModule}><Plus size={14} /> Add module</Button>} />
            )}
          </div>
        </Panel>

        <div className="proposal-subgrid">
          <Panel className="proposal-editor">
            <div className="proposal-section-heading">
              <div><GitBranch size={16} /><span><strong>Graph proposals</strong><small>Direction remains explicit.</small></span></div>
              <ApprovalSwitch
                checked={approvals.graph}
                onChange={(checked) => setApprovals((current) => ({ ...current, graph: checked }))}
                label="Apply graph"
              />
            </div>
            {proposal.relationships.length ? proposal.relationships.map((relationship, index) => (
              <label className="relationship-proposal" key={`${relationship.target_title}:${index}`}>
                <input
                  type="checkbox"
                  checked={relationship.selected}
                  onChange={(event) =>
                    setProposal((current) =>
                      current
                        ? {
                            ...current,
                            relationships: current.relationships.map((item, i) =>
                              i === index ? { ...item, selected: event.target.checked } : item,
                            ),
                          }
                        : current,
                    )
                  }
                />
                <span><strong>{formatLabel(relationship.relationship_type)}</strong><small>{relationship.target_title}</small></span>
              </label>
            )) : <p className="muted">No graph position is asserted without sufficient evidence.</p>}
          </Panel>
          <Panel className="proposal-editor">
            <div className="proposal-section-heading">
              <div><BookOpen size={16} /><span><strong>Source encounter</strong><small>Keep provenance with the note.</small></span></div>
              <ApprovalSwitch
                checked={approvals.source}
                onChange={(checked) => setApprovals((current) => ({ ...current, source: checked }))}
                label="Apply source"
              />
            </div>
            {proposal.encounter ? (
              <div className="encounter-summary">
                <Badge tone="blue">{proposal.encounter.source_type}</Badge>
                <strong>{proposal.encounter.source_title}</strong>
                <small>{proposal.encounter.unit || proposal.encounter.section || 'Whole source'}</small>
              </div>
            ) : <p className="muted">This session is recorded as Studium-origin unless a source is attached.</p>}
          </Panel>
        </div>
      </section>
      <aside className="proposal-rail">
        <div>
          <p className="eyebrow">Write target</p>
          <h3>{proposal.canonical_title}</h3>
          <code>{proposal.target_path}</code>
        </div>
        <dl>
          <div><dt>Operation</dt><dd>{proposal.target_concept_id ? 'Update draft' : 'Create draft'}</dd></div>
          <div><dt>Index revision</dt><dd>{proposal.index_revision}</dd></div>
          <div><dt>Selected modules</dt><dd>{proposal.modules.filter((item) => item.selected).length}</dd></div>
        </dl>
        {proposal.warnings.length > 0 && (
          <div className="proposal-warning"><AlertTriangle size={15} /><span>{proposal.warnings.join(' ')}</span></div>
        )}
        <Button variant="primary" size="large" loading={loading} onClick={onGenerate}>
          Generate editable draft <ArrowRight size={16} />
        </Button>
        <Button variant="ghost" onClick={onBack}><ArrowLeft size={15} /> Refine intent</Button>
        <small>Nothing has been written to your vault.</small>
      </aside>
    </div>
  )
}

function ApprovalSwitch({ checked, onChange, label }: { checked: boolean; onChange: (checked: boolean) => void; label: string }) {
  return (
    <label className="approval-switch">
      <input type="checkbox" checked={checked} onChange={(event) => onChange(event.target.checked)} />
      <span />
      <small>{label}</small>
    </label>
  )
}

function EditorStep({
  draft,
  title,
  markdownValue,
  setMarkdownValue,
  previewMode,
  setPreviewMode,
  editorRef,
  lastSaved,
  saving,
  onBack,
  onPreview,
  previewing,
}: {
  draft: GeneratedDraft
  title: string
  markdownValue: string
  setMarkdownValue: (value: string) => void
  previewMode: 'write' | 'preview'
  setPreviewMode: (value: 'write' | 'preview') => void
  editorRef: React.MutableRefObject<EditorView | null>
  lastSaved: string | null
  saving: boolean
  onBack: () => void
  onPreview: () => void
  previewing: boolean
}) {
  const format = (before: string, after = before, placeholder = 'text') => {
    const view = editorRef.current
    if (!view) return
    const selection = view.state.selection.main
    const selected = view.state.sliceDoc(selection.from, selection.to) || placeholder
    view.dispatch({
      changes: { from: selection.from, to: selection.to, insert: `${before}${selected}${after}` },
      selection: { anchor: selection.from + before.length, head: selection.from + before.length + selected.length },
    })
    view.focus()
  }
  const insertLine = (prefix: string, placeholder: string) => format(prefix, '', placeholder)
  return (
    <div className="editor-workspace">
      <header className="editor-header">
        <div>
          <p className="eyebrow">{draft.operation} draft</p>
          <h2>{title}</h2>
          <span>{draft.target_path}</span>
        </div>
        <div className="editor-header__actions">
          <span className="autosave-status">
            {saving ? <LoaderCircle className="spin" size={13} /> : <Check size={13} />}
            {saving ? 'Saving…' : lastSaved ? `Saved ${relativeTime(lastSaved)}` : 'Saved locally'}
          </span>
          <div className="editor-mode-tabs">
            <button className={previewMode === 'write' ? 'active' : ''} onClick={() => setPreviewMode('write')}>Write</button>
            <button className={previewMode === 'preview' ? 'active' : ''} onClick={() => setPreviewMode('preview')}>Preview</button>
          </div>
          <Button variant="primary" loading={previewing} onClick={onPreview}>
            Review diff <ArrowRight size={15} />
          </Button>
        </div>
      </header>
      <div className="editor-toolbar" role="toolbar" aria-label="Markdown formatting">
        <IconButton label="Heading" onClick={() => insertLine('## ', 'Heading')}><Heading2 size={15} /></IconButton>
        <IconButton label="Bold" onClick={() => format('**', '**', 'bold text')}><Bold size={15} /></IconButton>
        <IconButton label="Italic" onClick={() => format('_', '_', 'emphasis')}><Italic size={15} /></IconButton>
        <span />
        <IconButton label="Bulleted list" onClick={() => insertLine('- ', 'List item')}><List size={15} /></IconButton>
        <IconButton label="Quote" onClick={() => insertLine('> ', 'Quote')}><Quote size={15} /></IconButton>
        <IconButton label="Code" onClick={() => format('`', '`', 'code')}><Code2 size={15} /></IconButton>
        <IconButton label="Link" onClick={() => format('[', '](url)', 'label')}><Link size={15} /></IconButton>
      </div>
      <div className="editor-body">
        <aside className="editor-outline">
          <p className="nav-caption">Document outline</p>
          {outlineFromMarkdown(markdownValue).map((heading, index) => (
            <button key={`${heading.title}:${index}`} type="button" style={{ paddingLeft: `${8 + (heading.level - 1) * 8}px` }}>
              {heading.title}
            </button>
          ))}
          <div className="editor-outline__footer">
            <Save size={13} /> {markdownValue.split(/\s+/).filter(Boolean).length} words
          </div>
        </aside>
        <div className="editor-surface">
          {previewMode === 'write' ? (
            <Suspense fallback={<div className="editor-loading"><LoaderCircle className="spin" /></div>}>
              <MarkdownEditor
                value={markdownValue}
                onCreateEditor={(view) => { editorRef.current = view }}
                onChange={setMarkdownValue}
              />
            </Suspense>
          ) : (
            <div className="editor-preview"><Markdown value={markdownValue.replace(/^---[\s\S]*?---\s*/, '')} /></div>
          )}
        </div>
      </div>
      <footer className="editor-footer">
        <Button variant="ghost" onClick={onBack}><ArrowLeft size={14} /> Back to scaffold</Button>
        <span><ShieldCheck size={13} /> Draft only · safe write preview required</span>
      </footer>
    </div>
  )
}

function CommitStep({
  draft,
  preview,
  onBack,
  onCommit,
  committing,
}: {
  draft: GeneratedDraft
  preview: DraftPreview
  onBack: () => void
  onCommit: () => void
  committing: boolean
}) {
  return (
    <div className="commit-layout">
      <Panel className="diff-panel">
        <div className="diff-panel__header">
          <div><Diff size={17} /><span><p className="eyebrow">WriteProposal</p><h2>{preview.would_create ? 'Create note' : 'Update note'}</h2></span></div>
          <Badge tone={preview.can_commit ? 'success' : 'danger'}>{preview.can_commit ? 'Validated' : 'Blocked'}</Badge>
        </div>
        <div className="diff-file"><code>{preview.target_path}</code><span>{draft.operation}</span></div>
        <pre className="diff-view" aria-label="Markdown diff">{preview.diff || 'No content changes.'}</pre>
      </Panel>
      <aside className="commit-rail">
        <div className={clsx('validation-card', preview.can_commit ? 'validation-card--ok' : 'validation-card--blocked')}>
          {preview.can_commit ? <CheckCircle2 size={21} /> : <AlertTriangle size={21} />}
          <div>
            <strong>{preview.can_commit ? 'Safe to commit' : 'Commit blocked'}</strong>
            <p>{preview.can_commit ? 'Schema, path, collision, and note validation passed.' : 'Resolve critical validation errors before writing.'}</p>
          </div>
        </div>
        {preview.critical_errors.map((issue, index) => (
          <div className="validation-issue" key={index}><X size={14} /><span>{String(issue.message ?? 'Validation error')}</span></div>
        ))}
        {preview.warnings.map((issue, index) => (
          <div className="validation-issue validation-issue--warning" key={index}><AlertTriangle size={14} /><span>{String(issue.message ?? 'Warning')}</span></div>
        ))}
        <dl>
          <div><dt>Target</dt><dd>{preview.target_path}</dd></div>
          <div><dt>Operation</dt><dd>{preview.operation}</dd></div>
          <div><dt>After commit</dt><dd>Sync index + open review</dd></div>
        </dl>
        <Button variant="primary" size="large" loading={committing} disabled={!preview.can_commit} onClick={onCommit}>
          Commit to vault <ShieldCheck size={16} />
        </Button>
        <Button variant="ghost" onClick={onBack}><ArrowLeft size={14} /> Continue editing</Button>
      </aside>
    </div>
  )
}

function DoneStep({
  draft,
  result,
  onReview,
  onInspect,
  onNew,
}: {
  draft: GeneratedDraft
  result: Record<string, unknown> | null
  onReview: () => void
  onInspect: () => void
  onNew: () => void
}) {
  return (
    <div className="create-done">
      <div className="create-done__mark"><CheckCircle2 size={32} /></div>
      <Badge tone="success">Index revision {String(result?.index_revision ?? 'updated')}</Badge>
      <h2>Your draft is in the vault.</h2>
      <p>
        <code>{draft.target_path}</code> was committed through the safe-write pipeline. It remains a
        draft until review accepts it, so accepted-note Search stays trustworthy.
      </p>
      <div>
        <Button variant="primary" size="large" onClick={onReview}>Open Agent Review <ArrowRight size={16} /></Button>
        <Button variant="secondary" size="large" onClick={onInspect}>Inspect concept</Button>
      </div>
      <button type="button" onClick={onNew}>Start another learning session</button>
    </div>
  )
}

function DraftLibrary({
  drafts,
  loading,
  onRestore,
  onNew,
}: {
  drafts: DraftSnapshot[]
  loading: boolean
  onRestore: (draft: DraftSnapshot) => void
  onNew: () => void
}) {
  if (loading) return <Panel className="draft-library"><LoaderCircle className="spin" /></Panel>
  return (
    <Panel className="draft-library">
      <div className="draft-library__header">
        <div><p className="eyebrow">Local drafts</p><h2>Continue where you left off.</h2><p>Autosaved drafts live in app data until committed or removed.</p></div>
        <Button variant="primary" onClick={onNew}><Plus size={15} /> New session</Button>
      </div>
      {drafts.length ? (
        <div className="draft-grid">
          {drafts.map((draft) => (
            <button type="button" key={draft.id} onClick={() => onRestore(draft)}>
              <span className="draft-card__icon"><FileClock size={19} /></span>
              <Badge>{draft.target_path ? 'Vault draft' : 'Local draft'}</Badge>
              <h3>{draft.title}</h3>
              <p>{draft.target_path}</p>
              <footer><span>Saved {relativeTime(draft.updated_at)}</span><ArrowRight size={15} /></footer>
            </button>
          ))}
        </div>
      ) : (
        <EmptyState icon={<FileClock size={24} />} title="No autosaved drafts" description="Begin a session and Studium will preserve your editor state locally and on the local service." action={<Button onClick={onNew}>Start creating</Button>} />
      )}
    </Panel>
  )
}

function ReviewQueuePreview({ onNew }: { onNew: () => void }) {
  return (
    <Panel className="review-queue-preview">
      <div><ShieldCheck size={25} /><Badge tone="accent">Integrated workflow</Badge></div>
      <h2>Draft review belongs here—not in a disconnected tab.</h2>
      <p>Committed drafts move into structural and conceptual review. Findings, anchored comments, patch decisions, and acceptance all stay attached to the Create workflow.</p>
      <Button variant="primary" onClick={onNew}>Create a draft to review</Button>
    </Panel>
  )
}

function outlineFromMarkdown(value: string) {
  return value
    .split('\n')
    .map((line) => /^(#{1,4})\s+(.+)$/.exec(line))
    .filter((match): match is RegExpExecArray => match !== null)
    .map((match) => ({ level: match[1].length, title: match[2] }))
}

function relativeTime(value: string) {
  const seconds = Math.round((Date.now() - new Date(value).getTime()) / 1000)
  if (seconds < 15) return 'just now'
  if (seconds < 60) return `${seconds}s ago`
  const minutes = Math.round(seconds / 60)
  if (minutes < 60) return `${minutes}m ago`
  const hours = Math.round(minutes / 60)
  if (hours < 24) return `${hours}h ago`
  return new Date(value).toLocaleDateString()
}

function formatLabel(value: string) {
  return value.replaceAll('_', ' ').replace(/\b\w/g, (letter) => letter.toUpperCase())
}

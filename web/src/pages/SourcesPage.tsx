import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import clsx from 'clsx'
import {
  AlertTriangle,
  ArrowRight,
  BookOpen,
  Check,
  ChevronRight,
  Clipboard,
  File,
  FileText,
  Filter,
  Globe2,
  Highlighter,
  Layers3,
  LoaderCircle,
  Plus,
  Quote,
  RefreshCw,
  Search,
  Sparkles,
  Trash2,
  UploadCloud,
  X,
} from 'lucide-react'
import { useMemo, useRef, useState, type DragEvent, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
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
  Progress,
  Skeleton,
} from '../components/ui'
import { api, upload } from '../lib/api'
import type {
  SearchResponse,
  SourceContribution,
  SourceRecord,
  RetrievalHit,
} from '../lib/types'

type DetailTab = 'overview' | 'evidence' | 'chunks'

export function SourcesPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { push } = useToast()
  const [libraryQuery, setLibraryQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [tab, setTab] = useState<DetailTab>('overview')
  const [uploadOpen, setUploadOpen] = useState(false)
  const sourcesQuery = useQuery({
    queryKey: ['sources', libraryQuery, statusFilter],
    queryFn: () =>
      api<{ sources: SourceRecord[] }>(
        `/api/sources?query=${encodeURIComponent(libraryQuery)}&status=${encodeURIComponent(statusFilter)}`,
      ),
    refetchInterval: (query) =>
      query.state.data?.sources.some((source) => !['ready', 'failed'].includes(source.status))
        ? 1_500
        : false,
  })
  const sourceId = selectedId ?? sourcesQuery.data?.sources[0]?.id ?? null
  const detailQuery = useQuery({
    queryKey: ['source-detail', sourceId],
    queryFn: () => api<SourceRecord>(`/api/sources/${sourceId}?include_chunks=true`),
    enabled: Boolean(sourceId),
    refetchInterval: (query) =>
      query.state.data && !['ready', 'failed'].includes(query.state.data.status) ? 1_500 : false,
  })
  const deleteMutation = useMutation({
    mutationFn: (id: string) => api(`/api/sources/${id}`, { method: 'DELETE' }),
    onSuccess: async () => {
      setSelectedId(null)
      await queryClient.invalidateQueries({ queryKey: ['sources'] })
      push('Source removed', { tone: 'success' })
    },
    onError: (error: Error) => push('Could not remove source', { description: error.message, tone: 'danger' }),
  })
  const retryMutation = useMutation({
    mutationFn: (id: string) => api(`/api/sources/${id}/retry`, { method: 'POST' }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['sources'] })
      push('Source processing restarted', { tone: 'success' })
    },
  })

  const selected = detailQuery.data
  return (
    <div className="page sources-page">
      <PageHeader
        eyebrow="Source intelligence"
        title="Know what a source contributes."
        description="Preserve originals, inspect extraction, retrieve grounded evidence, and compare it against concepts already in your vault."
        actions={
          <Button variant="primary" onClick={() => setUploadOpen(true)}>
            <Plus size={15} /> Add source
          </Button>
        }
      />

      <div className="source-library-toolbar">
        <div className="source-search">
          <Search size={15} />
          <input
            value={libraryQuery}
            onChange={(event) => setLibraryQuery(event.target.value)}
            placeholder="Search source library…"
          />
        </div>
        <label>
          <Filter size={14} />
          <select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}>
            <option value="">All statuses</option>
            <option value="ready">Ready</option>
            <option value="queued">Queued</option>
            <option value="extracting">Extracting</option>
            <option value="chunking">Chunking</option>
            <option value="embedding">Embedding</option>
            <option value="failed">Needs attention</option>
          </select>
        </label>
        <span>{sourcesQuery.data?.sources.length ?? 0} sources</span>
      </div>

      {sourcesQuery.isLoading ? (
        <SourceLibrarySkeleton />
      ) : sourcesQuery.data?.sources.length ? (
        <div className="source-workspace">
          <Panel className="source-list-pane">
            <div className="pane-heading">
              <div><p className="eyebrow">Library</p><h2>Original sources</h2></div>
            </div>
            <div className="source-list">
              {sourcesQuery.data.sources.map((source) => (
                <button
                  type="button"
                  key={source.id}
                  className={clsx('source-list-item', source.id === sourceId && 'active')}
                  onClick={() => { setSelectedId(source.id); setTab('overview') }}
                >
                  <SourceIcon type={source.source_type} />
                  <span>
                    <strong>{source.title}</strong>
                    <small>{formatLabel(source.source_type)} · {formatBytes(source.size_bytes)}</small>
                    {!['ready', 'failed'].includes(source.status) && (
                      <Progress value={statusProgress(source.status)} />
                    )}
                  </span>
                  <Badge tone={statusTone(source.status)}>{formatLabel(source.status)}</Badge>
                </button>
              ))}
            </div>
          </Panel>

          <Panel className="source-detail-pane">
            {detailQuery.isLoading ? (
              <div className="source-detail-loading"><Skeleton /><Skeleton /><Skeleton /></div>
            ) : selected ? (
              <>
                <header className="source-detail-header">
                  <SourceIcon type={selected.source_type} large />
                  <div>
                    <div><Badge tone={statusTone(selected.status)}>{formatLabel(selected.status)}</Badge><Badge>{formatLabel(selected.source_type)}</Badge></div>
                    <h2>{selected.title}</h2>
                    <p>{selected.original_filename} · {formatBytes(selected.size_bytes)}</p>
                  </div>
                  <div className="source-detail-header__actions">
                    {selected.status === 'failed' && (
                      <Button variant="secondary" size="small" loading={retryMutation.isPending} onClick={() => retryMutation.mutate(selected.id)}>
                        <RefreshCw size={14} /> Retry
                      </Button>
                    )}
                    <IconButton label="Delete source" onClick={() => {
                      if (window.confirm(`Remove “${selected.title}” and its processed data?`)) deleteMutation.mutate(selected.id)
                    }}>
                      <Trash2 size={15} />
                    </IconButton>
                  </div>
                </header>
                <div className="source-detail-tabs" role="tablist">
                  {(['overview', 'evidence', 'chunks'] as DetailTab[]).map((value) => (
                    <button key={value} className={tab === value ? 'active' : ''} onClick={() => setTab(value)} role="tab">
                      {formatLabel(value)}
                    </button>
                  ))}
                </div>
                <div className="source-detail-content">
                  {selected.status === 'failed' ? (
                    <div className="source-error">
                      <AlertTriangle size={20} />
                      <div><strong>Processing failed</strong><p>{selected.processing_error}</p></div>
                    </div>
                  ) : selected.status !== 'ready' ? (
                    <ProcessingState source={selected} />
                  ) : tab === 'overview' ? (
                    <SourceOverview source={selected} />
                  ) : tab === 'evidence' ? (
                    <RetrievalWorkspace source={selected} />
                  ) : (
                    <ChunkBrowser source={selected} />
                  )}
                </div>
              </>
            ) : null}
          </Panel>

          <Panel className="source-action-pane">
            {selected?.status === 'ready' ? (
              <ContributionWorkspace
                source={selected}
                onCreate={(contribution, conceptTitle) => {
                  const moduleType = contribution.proposed_module?.type ?? 'conceptual_explanation'
                  navigate(
                    `/create?intent=${encodeURIComponent(contribution.summary)}` +
                      `&concept=${encodeURIComponent(contribution.concept_id)}` +
                      `&source=${encodeURIComponent(selected.id)}` +
                      `&sourceTitle=${encodeURIComponent(selected.title)}` +
                      `&sourceType=documentation&moduleType=${encodeURIComponent(moduleType)}` +
                      `&conceptTitle=${encodeURIComponent(conceptTitle)}`,
                  )
                }}
              />
            ) : (
              <EmptyState
                compact
                icon={<Sparkles size={22} />}
                title="Intelligence appears when ready"
                description="Once extraction and indexing finish, compare this source with any accepted concept."
              />
            )}
          </Panel>
        </div>
      ) : (
        <EmptyState
          icon={<UploadCloud size={26} />}
          title="Build a reusable source library"
          description="Add PDF, Markdown, text, HTML, subtitle, or transcript files. Originals stay local and deduplicate automatically."
          action={<Button variant="primary" onClick={() => setUploadOpen(true)}><Plus size={15} /> Add first source</Button>}
        />
      )}

      {uploadOpen && (
        <UploadDialog
          onClose={() => setUploadOpen(false)}
          onUploaded={async (source) => {
            setUploadOpen(false)
            setSelectedId(source.id)
            await queryClient.invalidateQueries({ queryKey: ['sources'] })
          }}
        />
      )}
    </div>
  )
}

function UploadDialog({
  onClose,
  onUploaded,
}: {
  onClose: () => void
  onUploaded: (source: SourceRecord) => void
}) {
  const { push } = useToast()
  const fileInput = useRef<HTMLInputElement>(null)
  const [file, setFile] = useState<File | null>(null)
  const [title, setTitle] = useState('')
  const [dragging, setDragging] = useState(false)
  const [progress, setProgress] = useState(0)
  const [uploading, setUploading] = useState(false)
  const choose = (selected: File | undefined) => {
    if (!selected) return
    setFile(selected)
    if (!title) setTitle(selected.name.replace(/\.[^.]+$/, ''))
  }
  const submit = async (event: FormEvent) => {
    event.preventDefault()
    if (!file) return
    const form = new FormData()
    form.append('file', file)
    if (title.trim()) form.append('title', title.trim())
    setUploading(true)
    try {
      const result = await upload<{ source: SourceRecord; duplicate: boolean }>(
        '/api/sources/upload',
        form,
        setProgress,
      )
      push(result.duplicate ? 'Source already exists' : 'Source added', {
        description: result.duplicate
          ? 'Studium reused the existing processed source.'
          : 'Extraction and indexing are running in the background.',
        tone: result.duplicate ? 'neutral' : 'success',
      })
      onUploaded(result.source)
    } catch (error) {
      push('Upload failed', {
        description: error instanceof Error ? error.message : String(error),
        tone: 'danger',
      })
      setUploading(false)
    }
  }
  const drop = (event: DragEvent) => {
    event.preventDefault()
    setDragging(false)
    choose(event.dataTransfer.files[0])
  }
  return (
    <div className="dialog-backdrop" role="presentation" onMouseDown={onClose}>
      <form className="upload-dialog" onSubmit={submit} onMouseDown={(event) => event.stopPropagation()}>
        <header>
          <div><p className="eyebrow">Local ingestion</p><h2>Add a source</h2></div>
          <IconButton label="Close upload" type="button" onClick={onClose}><X size={17} /></IconButton>
        </header>
        <button
          className={clsx('upload-dropzone', dragging && 'active', file && 'has-file')}
          type="button"
          onClick={() => fileInput.current?.click()}
          onDragOver={(event) => { event.preventDefault(); setDragging(true) }}
          onDragLeave={() => setDragging(false)}
          onDrop={drop}
        >
          {file ? <FileText size={26} /> : <UploadCloud size={28} />}
          <strong>{file ? file.name : 'Drop a source here'}</strong>
          <span>{file ? formatBytes(file.size) : 'PDF, Markdown, text, HTML, SRT, VTT, or transcript JSON'}</span>
          <input
            ref={fileInput}
            type="file"
            hidden
            accept=".pdf,.md,.markdown,.txt,.html,.htm,.srt,.vtt,.json,text/*,application/pdf"
            onChange={(event) => choose(event.target.files?.[0])}
          />
        </button>
        <Field label="Display title">
          <Input value={title} onChange={(event) => setTitle(event.target.value)} placeholder="Source title" />
        </Field>
        {uploading && <Progress value={progress} label="Upload progress" />}
        <div className="upload-dialog__notes">
          <Check size={14} /><span>Original preserved</span>
          <Check size={14} /><span>Content-hash deduplication</span>
          <Check size={14} /><span>Local processing</span>
        </div>
        <footer>
          <Button type="button" variant="ghost" onClick={onClose}>Cancel</Button>
          <Button type="submit" variant="primary" loading={uploading} disabled={!file}>Add and process</Button>
        </footer>
      </form>
    </div>
  )
}

function SourceOverview({ source }: { source: SourceRecord }) {
  const sample = source.chunks?.slice(0, 4) ?? []
  return (
    <div className="source-overview">
      <div className="source-stat-grid">
        <div><span>Chunks</span><strong>{source.chunk_count}</strong></div>
        <div><span>Pages</span><strong>{source.page_count ?? '—'}</strong></div>
        <div><span>Words</span><strong>{formatCount((source.chunks ?? []).reduce((sum, chunk) => sum + chunk.token_count, 0))}</strong></div>
        <div><span>Fingerprint</span><strong>{source.content_hash.slice(0, 8)}</strong></div>
      </div>
      {Object.keys(source.metadata).length > 0 && (
        <section>
          <h3>Extracted metadata</h3>
          <dl className="source-metadata">
            {Object.entries(source.metadata).slice(0, 8).map(([key, value]) => (
              <div key={key}><dt>{formatLabel(key)}</dt><dd>{String(value)}</dd></div>
            ))}
          </dl>
        </section>
      )}
      <section>
        <h3>Extraction preview</h3>
        <div className="extraction-preview">
          {sample.map((chunk) => (
            <article key={chunk.id}>
              <span>{chunk.page ? `Page ${chunk.page}` : chunk.section ?? `Chunk ${chunk.ordinal + 1}`}</span>
              <p>{chunk.text}</p>
            </article>
          ))}
        </div>
      </section>
    </div>
  )
}

function RetrievalWorkspace({ source }: { source: SourceRecord }) {
  const { push } = useToast()
  const [query, setQuery] = useState('')
  const mutation = useMutation({
    mutationFn: () =>
      api<{ hits: RetrievalHit[] }>('/api/sources/retrieve', {
        method: 'POST',
        body: { query, source_id: source.id, limit: 12 },
      }),
  })
  return (
    <div className="retrieval-workspace">
      <form onSubmit={(event) => { event.preventDefault(); if (query.trim()) mutation.mutate() }}>
        <Search size={16} />
        <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Ask what this source says about…" />
        <Button variant="primary" size="small" type="submit" loading={mutation.isPending}>Retrieve</Button>
      </form>
      {!mutation.data ? (
        <EmptyState compact icon={<Highlighter size={22} />} title="Retrieve grounded passages" description="Search this processed source semantically and lexically. Every result includes a durable locator." />
      ) : mutation.data.hits.length ? (
        <div className="evidence-list">
          {mutation.data.hits.map((hit) => (
            <article key={hit.chunk_id}>
              <header><Badge tone="blue">{hit.citation.locator}</Badge><span>{Math.round(hit.score * 100)}% relevance</span></header>
              <p>{hit.text}</p>
              <button type="button" onClick={async () => {
                await navigator.clipboard.writeText(`“${hit.citation.quote}” — ${hit.source_title}, ${hit.citation.locator}`)
                push('Citation copied', { tone: 'success' })
              }}><Clipboard size={13} /> Copy citation</button>
            </article>
          ))}
        </div>
      ) : (
        <EmptyState compact title="No grounded passage found" description="Try a more specific phrase or inspect the extracted chunks." />
      )}
    </div>
  )
}

function ChunkBrowser({ source }: { source: SourceRecord }) {
  const [query, setQuery] = useState('')
  const chunks = useMemo(
    () =>
      (source.chunks ?? []).filter((chunk) =>
        chunk.text.toLowerCase().includes(query.toLowerCase()),
      ),
    [query, source.chunks],
  )
  return (
    <div className="chunk-browser">
      <div className="chunk-browser__search"><Search size={14} /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Filter extracted chunks…" /></div>
      <div>
        {chunks.map((chunk) => (
          <details key={chunk.id}>
            <summary>
              <span>#{chunk.ordinal + 1}</span>
              <strong>{chunk.section ?? (chunk.page ? `Page ${chunk.page}` : 'Document')}</strong>
              <small>{chunk.token_count} words</small>
            </summary>
            <p>{chunk.text}</p>
          </details>
        ))}
      </div>
    </div>
  )
}

function ContributionWorkspace({
  source,
  onCreate,
}: {
  source: SourceRecord
  onCreate: (contribution: SourceContribution, conceptTitle: string) => void
}) {
  const { push } = useToast()
  const [query, setQuery] = useState('')
  const [selectedConcept, setSelectedConcept] = useState<{ id: string; title: string } | null>(null)
  const searchQuery = useQuery({
    queryKey: ['source-concept-search', query],
    queryFn: () =>
      api<SearchResponse>('/api/search', {
        method: 'POST',
        body: { text: query, include_modules: false },
      }),
    enabled: query.trim().length > 1 && !selectedConcept,
  })
  const analysisMutation = useMutation({
    mutationFn: () =>
      api<SourceContribution>('/api/sources/contributions/analyze', {
        method: 'POST',
        body: { source_id: source.id, concept_id: selectedConcept?.id, focus: query },
      }),
    onError: (error: Error) => push('Comparison failed', { description: error.message, tone: 'danger' }),
  })
  const contribution = analysisMutation.data
  return (
    <div className="contribution-workspace">
      <div className="contribution-workspace__heading">
        <span><Sparkles size={18} /></span>
        <div><p className="eyebrow">Concept-conditioned</p><h3>Compare to your vault</h3><p>Classify what this source adds before changing a note.</p></div>
      </div>
      <Field label="Accepted concept">
        <div className="concept-picker">
          {selectedConcept ? (
            <button type="button" className="concept-picker__selected" onClick={() => { setSelectedConcept(null); setQuery('') }}>
              <span><Check size={13} /> {selectedConcept.title}</span><X size={13} />
            </button>
          ) : (
            <><Search size={14} /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search concepts…" /></>
          )}
        </div>
      </Field>
      {!selectedConcept && searchQuery.data?.ranked_concepts.length ? (
        <div className="concept-picker-results">
          {searchQuery.data.ranked_concepts.slice(0, 5).map((concept) => (
            <button type="button" key={concept.concept_id} onClick={() => setSelectedConcept({ id: concept.concept_id, title: concept.canonical_title })}>
              <span><strong>{concept.canonical_title}</strong><small>{concept.match_explanations[0]}</small></span><ChevronRight size={13} />
            </button>
          ))}
        </div>
      ) : null}
      <Button variant="primary" loading={analysisMutation.isPending} disabled={!selectedConcept} onClick={() => analysisMutation.mutate()}>
        <Sparkles size={15} /> Analyze contribution
      </Button>
      {contribution && selectedConcept && (
        <div className="contribution-result">
          <Badge tone="accent">{formatLabel(contribution.classification)}</Badge>
          <h4>{contribution.proposed_module?.title ?? 'Source contribution'}</h4>
          <p>{contribution.summary}</p>
          <div className="citation-stack">
            {contribution.evidence.slice(0, 3).map((citation) => (
              <blockquote key={citation.chunk_id}><Quote size={12} /><span>{citation.quote}</span><cite>{citation.source_title}, {citation.locator}</cite></blockquote>
            ))}
          </div>
          <Button variant="secondary" onClick={() => onCreate(contribution, selectedConcept.title)}>
            Open proposal in Create <ArrowRight size={14} />
          </Button>
        </div>
      )}
    </div>
  )
}

function ProcessingState({ source }: { source: SourceRecord }) {
  const stages = ['queued', 'extracting', 'chunking', 'embedding', 'ready']
  const current = stages.indexOf(source.status)
  return (
    <div className="source-processing">
      <LoaderCircle className="spin" size={25} />
      <h3>{formatLabel(source.status)} source</h3>
      <p>The original is safe. Studium is preparing recoverable, provenance-aware chunks.</p>
      <Progress value={statusProgress(source.status)} />
      <div>
        {stages.slice(0, -1).map((stage, index) => <span key={stage} className={index <= current ? 'active' : ''}>{formatLabel(stage)}</span>)}
      </div>
    </div>
  )
}

function SourceLibrarySkeleton() {
  return (
    <div className="source-workspace">
      {[1, 2, 3].map((item) => <Panel className="source-skeleton" key={item}><Skeleton /><Skeleton /><Skeleton /></Panel>)}
    </div>
  )
}

function SourceIcon({ type, large = false }: { type: string; large?: boolean }) {
  const Icon = type === 'html' ? Globe2 : type === 'transcript' ? BookOpen : type === 'pdf' ? FileText : File
  return <span className={clsx('source-icon', `source-icon--${type}`, large && 'source-icon--large')}><Icon size={large ? 22 : 16} /></span>
}

function statusTone(status: SourceRecord['status']): 'success' | 'warning' | 'danger' | 'blue' | 'neutral' {
  if (status === 'ready') return 'success'
  if (status === 'failed') return 'danger'
  if (status === 'queued') return 'neutral'
  return 'blue'
}

function statusProgress(status: SourceRecord['status']) {
  return { queued: 0.05, extracting: 0.22, chunking: 0.48, embedding: 0.72, ready: 1, failed: 1 }[status]
}

function formatBytes(value: number) {
  if (value < 1024) return `${value} B`
  if (value < 1024 ** 2) return `${(value / 1024).toFixed(1)} KB`
  return `${(value / 1024 ** 2).toFixed(1)} MB`
}

function formatCount(value: number) {
  return new Intl.NumberFormat('en-US', { notation: value > 9999 ? 'compact' : 'standard' }).format(value)
}

function formatLabel(value: string) {
  return value.replaceAll('_', ' ').replace(/\b\w/g, (letter) => letter.toUpperCase())
}

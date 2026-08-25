import { useMutation, useQuery } from '@tanstack/react-query'
import clsx from 'clsx'
import {
  ArrowRight,
  BookOpen,
  Box,
  ChevronDown,
  ChevronRight,
  CircleDot,
  ExternalLink,
  GitBranch,
  Inbox,
  Layers3,
  Network,
  PenLine,
  Search,
  SlidersHorizontal,
  Sparkles,
  X,
} from 'lucide-react'
import {
  lazy,
  Suspense,
  useCallback,
  useEffect,
  useRef,
  useState,
  type FormEvent,
  type ReactNode,
} from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { Markdown } from '../components/Markdown'
import { useToast } from '../components/toast-context'
import { Badge, Button, EmptyState, IconButton, PageHeader, Panel, Skeleton } from '../components/ui'
import { api } from '../lib/api'
import type {
  ConceptDetail,
  GraphProjection,
  SearchConcept,
  SearchFacets,
  SearchModule,
  SearchResponse,
} from '../lib/types'

type FilterKey = 'domains' | 'concept_types' | 'review_statuses'

const EMPTY_FILTERS: Record<FilterKey, string[]> = {
  domains: [],
  concept_types: [],
  review_statuses: [],
}

const KnowledgeGraph = lazy(() =>
  import('../components/KnowledgeGraph').then((module) => ({ default: module.KnowledgeGraph })),
)

export function SearchPage() {
  const [params, setParams] = useSearchParams()
  const navigate = useNavigate()
  const { push } = useToast()
  const initialQuery = params.get('q') ?? ''
  const [input, setInput] = useState(initialQuery)
  const [query, setQuery] = useState(initialQuery)
  const [selectedId, setSelectedId] = useState<string | null>(params.get('concept'))
  const [selectedModule, setSelectedModule] = useState<string | null>(params.get('module'))
  const [filters, setFilters] = useState(EMPTY_FILTERS)
  const [filtersOpen, setFiltersOpen] = useState(false)

  const facetsQuery = useQuery({
    queryKey: ['search-facets'],
    queryFn: () => api<SearchFacets>('/api/search/facets'),
  })
  const searchQuery = useQuery({
    queryKey: ['search', query, filters],
    queryFn: () =>
      api<SearchResponse>('/api/search', {
        method: 'POST',
        body: {
          text: query,
          filters: {
            domains: filters.domains,
            concept_types: filters.concept_types,
            review_statuses: filters.review_statuses,
            vault_statuses: [],
          },
          include_modules: true,
        },
      }),
    enabled: Boolean(query.trim()),
  })
  const detailQuery = useQuery({
    queryKey: ['concept-detail', selectedId],
    queryFn: () => api<ConceptDetail>(`/api/concepts/${encodeURIComponent(selectedId ?? '')}`),
    enabled: Boolean(selectedId),
  })
  const graphQuery = useQuery({
    queryKey: ['graph', selectedId],
    queryFn: () =>
      api<GraphProjection>(
        selectedId ? `/api/graph?center=${encodeURIComponent(selectedId)}` : '/api/graph',
      ),
  })
  const backlogMutation = useMutation({
    mutationFn: () =>
      api('/api/backlog', {
        method: 'POST',
        body: {
          title: query,
          item_type: 'new_concept',
          reason: 'No accepted concept matched this Search query.',
          origin: 'search',
          source_query: query,
        },
      }),
    onSuccess: () => push('Added to backlog', { description: query, tone: 'success' }),
    onError: (error: Error) => push('Could not add backlog item', { description: error.message, tone: 'danger' }),
  })

  const submit = (event: FormEvent) => {
    event.preventDefault()
    const value = input.trim()
    if (!value) return
    setQuery(value)
    setSelectedId(null)
    setSelectedModule(null)
    setParams({ q: value })
  }

  const selectConcept = useCallback(
    (conceptId: string, moduleId?: string | null) => {
      setSelectedId(conceptId)
      setSelectedModule(moduleId ?? null)
      const next = new URLSearchParams(params)
      if (query) next.set('q', query)
      next.set('concept', conceptId)
      if (moduleId) next.set('module', moduleId)
      else next.delete('module')
      setParams(next, { replace: true })
    },
    [params, query, setParams],
  )

  const activeFilterCount = Object.values(filters).reduce((sum, values) => sum + values.length, 0)
  const results = searchQuery.data
  const concepts = results?.ranked_concepts ?? []
  const modules = results?.module_hits ?? []
  const hasResults = concepts.length > 0 || modules.length > 0

  return (
    <div className="page search-page">
      <PageHeader
        eyebrow="Explore"
        title="Find what you already know."
        description="Search concept identities, note content, and scaffold modules—then inspect their graph context without leaving Studium."
        actions={
          <Button variant="secondary" onClick={() => setFiltersOpen((open) => !open)}>
            <SlidersHorizontal size={15} /> Filters
            {activeFilterCount > 0 && <Badge tone="accent">{activeFilterCount}</Badge>}
          </Button>
        }
      />

      <form className="search-hero" onSubmit={submit}>
        <Search size={21} aria-hidden />
        <input
          value={input}
          onChange={(event) => setInput(event.target.value)}
          placeholder="Search a concept, alias, module, or learning question…"
          aria-label="Search your knowledge"
        />
        {input && (
          <IconButton
            type="button"
            label="Clear search"
            onClick={() => {
              setInput('')
              setQuery('')
              setSelectedId(null)
              setParams({})
            }}
          >
            <X size={16} />
          </IconButton>
        )}
        <Button variant="primary" type="submit">
          Search
        </Button>
      </form>

      {filtersOpen && (
        <Panel className="filter-panel">
          <div className="filter-panel__heading">
            <div>
              <p className="eyebrow">Narrow results</p>
              <h2>Search filters</h2>
            </div>
            <Button variant="ghost" size="small" onClick={() => setFilters(EMPTY_FILTERS)}>
              Clear all
            </Button>
          </div>
          <div className="filter-groups">
            {(['domains', 'concept_types', 'review_statuses'] as FilterKey[]).map((key) => (
              <FilterGroup
                key={key}
                label={key.replaceAll('_', ' ')}
                options={facetsQuery.data?.[key] ?? []}
                selected={filters[key]}
                onToggle={(value) =>
                  setFilters((current) => ({
                    ...current,
                    [key]: current[key].includes(value)
                      ? current[key].filter((item) => item !== value)
                      : [...current[key], value],
                  }))
                }
              />
            ))}
          </div>
        </Panel>
      )}

      {!query ? (
        <SearchWelcome onSearch={(value) => { setInput(value); setQuery(value); setParams({ q: value }) }} />
      ) : (
        <div className="search-workspace">
          <Panel className="results-pane">
            <div className="pane-heading">
              <div>
                <p className="eyebrow">Results</p>
                <h2>{searchQuery.isLoading ? 'Searching…' : `${concepts.length + modules.length} matches`}</h2>
              </div>
              {results && <Badge tone={results.search_status === 'complete' ? 'success' : 'warning'}>{results.search_status}</Badge>}
            </div>
            <div className="results-scroll">
              {searchQuery.isLoading && <ResultsSkeleton />}
              {searchQuery.error && (
                <EmptyState
                  compact
                  title="Search could not complete"
                  description={searchQuery.error.message}
                  action={<Button onClick={() => void searchQuery.refetch()}>Try again</Button>}
                />
              )}
              {!searchQuery.isLoading && !searchQuery.error && hasResults && (
                <>
                  {concepts.length > 0 && (
                    <ResultGroup title="Concepts" count={concepts.length}>
                      {concepts.map((concept) => (
                        <ConceptResult
                          key={concept.concept_id}
                          concept={concept}
                          selected={selectedId === concept.concept_id && !selectedModule}
                          onClick={() => selectConcept(concept.concept_id)}
                        />
                      ))}
                    </ResultGroup>
                  )}
                  {modules.length > 0 && (
                    <ResultGroup title="Scaffold modules" count={modules.length}>
                      {modules.map((module) => (
                        <ModuleResult
                          key={`${module.concept_id}:${module.module_id}`}
                          module={module}
                          selected={selectedModule === module.module_id}
                          onClick={() => selectConcept(module.concept_id, module.module_id)}
                        />
                      ))}
                    </ResultGroup>
                  )}
                </>
              )}
              {!searchQuery.isLoading && !searchQuery.error && !hasResults && (
                <MissingResult
                  query={query}
                  recommendation={results?.recommendation}
                  onCreate={() => navigate(`/create?intent=${encodeURIComponent(query)}`)}
                  onBacklog={() => backlogMutation.mutate()}
                  adding={backlogMutation.isPending}
                />
              )}
            </div>
          </Panel>

          <Panel className="graph-pane">
            {graphQuery.isLoading ? (
              <div className="graph-loading">
                <Skeleton className="graph-loading__node" />
                <Skeleton className="graph-loading__line" />
              </div>
            ) : graphQuery.data?.nodes.length ? (
              <Suspense fallback={<div className="graph-loading"><Skeleton className="graph-loading__node" /></div>}>
                <KnowledgeGraph graph={graphQuery.data} onSelect={selectConcept} />
              </Suspense>
            ) : (
              <EmptyState
                compact
                icon={<Network size={24} />}
                title="No accepted graph yet"
                description="Accepted concepts and their typed relationships will appear here."
              />
            )}
          </Panel>

          <Panel className="detail-pane">
            {!selectedId ? (
              <EmptyState
                compact
                icon={<BookOpen size={24} />}
                title="Select a result"
                description="Open a concept or scaffold module to inspect its note, modules, sources, and relationships."
              />
            ) : detailQuery.isLoading ? (
              <DetailSkeleton />
            ) : detailQuery.error ? (
              <EmptyState
                compact
                title="Concept unavailable"
                description={detailQuery.error.message}
              />
            ) : detailQuery.data ? (
              <ConceptView
                detail={detailQuery.data}
                targetModule={selectedModule}
                onNavigate={selectConcept}
                onCreate={() =>
                  navigate(`/create?intent=${encodeURIComponent(query)}&concept=${encodeURIComponent(detailQuery.data.concept_id)}`)
                }
              />
            ) : null}
          </Panel>
        </div>
      )}
    </div>
  )
}

function FilterGroup({
  label,
  options,
  selected,
  onToggle,
}: {
  label: string
  options: Array<{ value: string; label: string; count: number }>
  selected: string[]
  onToggle: (value: string) => void
}) {
  return (
    <fieldset className="filter-group">
      <legend>{label}</legend>
      {options.length ? (
        options.map((option) => (
          <label key={option.value}>
            <input
              type="checkbox"
              checked={selected.includes(option.value)}
              onChange={() => onToggle(option.value)}
            />
            <span>{option.label}</span>
            <small>{option.count}</small>
          </label>
        ))
      ) : (
        <p>No values indexed.</p>
      )}
    </fieldset>
  )
}

function SearchWelcome({ onSearch }: { onSearch: (value: string) => void }) {
  const suggestions = ['stochastic gradient descent', 'manual parameter update', 'prerequisites for backpropagation']
  return (
    <div className="search-welcome">
      <div className="search-welcome__mark">
        <GitBranch size={30} />
      </div>
      <h2>Explore your connected knowledge.</h2>
      <p>
        Exact identities return immediately. Broader questions combine lexical, semantic, and
        module retrieval without exposing retrieval internals.
      </p>
      <div className="search-suggestions">
        {suggestions.map((suggestion) => (
          <button type="button" key={suggestion} onClick={() => onSearch(suggestion)}>
            <Search size={13} /> {suggestion}
          </button>
        ))}
      </div>
    </div>
  )
}

function ResultGroup({
  title,
  count,
  children,
}: {
  title: string
  count: number
  children: ReactNode
}) {
  return (
    <section className="result-group">
      <h3>
        {title} <span>{count}</span>
      </h3>
      <div>{children}</div>
    </section>
  )
}

function ConceptResult({
  concept,
  selected,
  onClick,
}: {
  concept: SearchConcept
  selected: boolean
  onClick: () => void
}) {
  return (
    <button className={clsx('result-card', selected && 'result-card--selected')} type="button" onClick={onClick}>
      <span className="result-card__icon">
        <CircleDot size={15} />
      </span>
      <span className="result-card__body">
        <strong>{concept.canonical_title}</strong>
        <span className="result-card__meta">
          {formatLabel(concept.concept_type ?? 'concept')} · {concept.domains.map(formatLabel).join(', ') || 'General'}
        </span>
        <span className="result-card__evidence">{concept.match_explanations[0]}</span>
      </span>
      <ChevronRight size={15} />
    </button>
  )
}

function ModuleResult({
  module,
  selected,
  onClick,
}: {
  module: SearchModule
  selected: boolean
  onClick: () => void
}) {
  return (
    <button className={clsx('result-card', selected && 'result-card--selected')} type="button" onClick={onClick}>
      <span className="result-card__icon result-card__icon--module">
        <Layers3 size={15} />
      </span>
      <span className="result-card__body">
        <strong>{module.title}</strong>
        <span className="result-card__meta">
          {module.parent_canonical_title} · {formatLabel(module.module_type ?? 'module')}
        </span>
        <span className="result-card__evidence">{module.match_explanations[0]}</span>
      </span>
      <ChevronRight size={15} />
    </button>
  )
}

function MissingResult({
  query,
  recommendation,
  onCreate,
  onBacklog,
  adding,
}: {
  query: string
  recommendation: Record<string, unknown> | null | undefined
  onCreate: () => void
  onBacklog: () => void
  adding: boolean
}) {
  const action = typeof recommendation?.action === 'string' ? recommendation.action : 'create_new_concept'
  return (
    <div className="missing-result">
      <div className="missing-result__icon">
        <Sparkles size={22} />
      </div>
      <Badge tone="accent">Knowledge gap</Badge>
      <h3>“{query}” does not appear to exist yet.</h3>
      <p>
        Studium recommends <strong>{formatLabel(action)}</strong>. Create will inspect related
        concepts again before proposing any vault change.
      </p>
      <Button variant="primary" onClick={onCreate}>
        Open in Create <ArrowRight size={15} />
      </Button>
      <Button variant="ghost" loading={adding} onClick={onBacklog}>
        <Inbox size={15} /> Preserve in backlog
      </Button>
    </div>
  )
}

function ConceptView({
  detail,
  targetModule,
  onNavigate,
  onCreate,
}: {
  detail: ConceptDetail
  targetModule: string | null
  onNavigate: (conceptId: string) => void
  onCreate: () => void
}) {
  const [openModules, setOpenModules] = useState<Set<string>>(new Set())
  const targetRef = useRef<HTMLDivElement>(null)
  useEffect(() => {
    if (!targetModule) return
    window.setTimeout(() => targetRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 80)
  }, [targetModule])

  const overview = detail.sections.find((section) => section.title === 'Concept Overview')
  return (
    <article className="concept-view">
      <header className="concept-view__header">
        <div className="concept-view__status">
          <Badge tone="success">{detail.vault_status}</Badge>
          <Badge>{formatLabel(detail.concept_type)}</Badge>
        </div>
        <h2>{detail.canonical_title}</h2>
        {detail.aliases.length > 0 && <p className="concept-view__aliases">Also: {detail.aliases.join(', ')}</p>}
        <div className="concept-view__domains">
          {detail.domains.map((domain) => <Badge key={domain} tone="blue">{formatLabel(domain)}</Badge>)}
        </div>
        <div className="concept-view__actions">
          <Button variant="primary" size="small" onClick={onCreate}>
            <PenLine size={14} /> Extend concept
          </Button>
          <a className="button button--ghost button--small" href={detail.obsidian_uri}>
            <ExternalLink size={14} /> Obsidian
          </a>
        </div>
      </header>

      {overview && (
        <section className="concept-view__overview">
          <Markdown value={overview.markdown} />
        </section>
      )}

      {detail.modules.length > 0 && (
        <section className="concept-modules">
          <div className="section-title">
            <span>
              <Layers3 size={15} /> Scaffold modules
            </span>
            <small>{detail.modules.length}</small>
          </div>
          {detail.modules.map((module) => {
            const open = openModules.has(module.id) || targetModule === module.id
            return (
              <div
                className={clsx('concept-module', targetModule === module.id && 'concept-module--target')}
                key={module.id}
                ref={targetModule === module.id ? targetRef : undefined}
              >
                <button
                  type="button"
                  onClick={() =>
                    setOpenModules((current) => {
                      const next = new Set(current)
                      if (next.has(module.id)) next.delete(module.id)
                      else next.add(module.id)
                      return next
                    })
                  }
                >
                  <span>
                    <strong>{module.title}</strong>
                    <small>{formatLabel(module.type)} · {formatLabel(module.status)}</small>
                  </span>
                  <ChevronDown className={open ? 'rotate-180' : ''} size={15} />
                </button>
                {open && (
                  <div className="concept-module__content">
                    {module.markdown ? (
                      <Markdown value={module.markdown} />
                    ) : (
                      <p className="muted">This module is scaffolded but has no written content yet.</p>
                    )}
                  </div>
                )}
              </div>
            )
          })}
        </section>
      )}

      <section className="concept-relationships">
        <div className="section-title">
          <span>
            <GitBranch size={15} /> Connections
          </span>
          <small>{detail.relationships.length}</small>
        </div>
        {detail.relationships.length ? detail.relationships.map((relationship, index) => (
          <button
            type="button"
            key={`${relationship.id ?? index}:${relationship.relationship_type}`}
            onClick={() => relationship.target_id && onNavigate(relationship.target_id)}
            disabled={!relationship.target_id}
          >
            <span className={`relationship-dot relationship-dot--${relationship.relationship_type}`} />
            <span>
              <small>{formatLabel(relationship.relationship_type)}</small>
              <strong>{relationship.target_title}</strong>
            </span>
            {relationship.target_id && <ChevronRight size={14} />}
          </button>
        )) : <p className="muted">No direct relationships are recorded yet.</p>}
      </section>

      <details className="concept-metadata">
        <summary>
          <Box size={14} /> Note metadata
        </summary>
        <dl>
          <div><dt>Concept ID</dt><dd>{detail.concept_id}</dd></div>
          <div><dt>Status</dt><dd>{formatLabel(detail.status)} / {formatLabel(detail.review_status)}</dd></div>
          <div><dt>Vault path</dt><dd>{detail.file_path}</dd></div>
          <div><dt>Encounters</dt><dd>{detail.learning_encounters.length}</dd></div>
        </dl>
      </details>
    </article>
  )
}

function ResultsSkeleton() {
  return (
    <div className="results-skeleton">
      {[1, 2, 3, 4].map((item) => (
        <div key={item}>
          <Skeleton className="results-skeleton__title" />
          <Skeleton />
          <Skeleton className="results-skeleton__short" />
        </div>
      ))}
    </div>
  )
}

function DetailSkeleton() {
  return (
    <div className="detail-skeleton">
      <Skeleton className="detail-skeleton__badge" />
      <Skeleton className="detail-skeleton__title" />
      <Skeleton />
      <Skeleton />
      <Skeleton className="detail-skeleton__body" />
    </div>
  )
}

function formatLabel(value: string) {
  return value.replaceAll('_', ' ').replace(/\b\w/g, (letter) => letter.toUpperCase())
}

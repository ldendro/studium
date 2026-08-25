export type SyncStatus = 'success' | 'partial_success' | 'failed' | 'no_changes'

export interface SyncReport {
  sync_id: string
  status: SyncStatus
  revision_before: number
  revision_after: number
  counts: Record<string, number>
  warnings: string[]
  errors: string[]
  started_at: string
  finished_at: string
}

export interface WorkspaceHealth {
  status: 'ok' | 'onboarding'
  workspace_open: boolean
  vault_id?: string
  vault_name?: string
  vault_path?: string
  index_revision?: number
  index_database?: string
  app_database?: string
  last_sync?: SyncReport | null
  embedding?: {
    model_id: string
    model_revision: string | null
    dimension: number
    normalizes_embeddings: boolean
  }
  llm?: {
    healthy: boolean | null
    ready: boolean | null
    model_id: string | null
    message: string
  }
  app_schema_version?: number
}

export interface Job {
  id: string
  job_type: string
  status: 'queued' | 'running' | 'completed' | 'failed'
  progress: number
  message: string | null
  payload: Record<string, unknown>
  result: Record<string, unknown> | null
  error: string | null
  created_at: string
  started_at: string | null
  finished_at: string | null
}

export type NoticeTone = 'neutral' | 'success' | 'warning' | 'danger'

export interface SearchFacet {
  value: string
  label: string
  count: number
}

export interface SearchFacets {
  domains: SearchFacet[]
  concept_types: SearchFacet[]
  review_statuses: SearchFacet[]
  vault_statuses: SearchFacet[]
}

export interface SearchModule {
  module_id: string
  concept_id: string
  parent_canonical_title: string | null
  title: string
  module_type: string | null
  anchor: string | null
  snippet: string | null
  fused_rank: number
  match_explanations: string[]
}

export interface SearchConcept {
  concept_id: string
  canonical_title: string
  aliases: string[]
  concept_type: string | null
  domains: string[]
  overview_excerpt: string | null
  status: string | null
  vault_status: string | null
  review_status: string | null
  fused_rank: number
  fused_score: number
  matching_modules: Array<{
    module_id: string
    title: string
    module_type: string | null
    anchor: string | null
  }>
  match_explanations: string[]
}

export interface SearchResponse {
  query: {
    text: string
    filters: Record<string, string[]>
  }
  index_revision: number
  search_status: string
  resolution_state: 'exact_match' | 'related_results' | 'ambiguous_results' | 'no_results'
  ranked_concepts: SearchConcept[]
  module_hits: SearchModule[]
  warnings: string[]
  recommendation: Record<string, unknown> | null
}

export interface ConceptSection {
  id: string
  title: string
  level: number
  markdown: string
  line: number
}

export interface ConceptModule {
  id: string
  type: string
  title: string
  status: string
  origin: string | null
  focus: string | null
  anchor: string | null
  markdown: string
}

export interface GraphRelationship {
  id: number | null
  source_concept_id: string
  relationship_type: string
  target_id: string | null
  target_title: string
  vault_status: string
  learning_role: string
  confidence: string
  status: string
  derived_inverse: boolean
}

export interface ConceptDetail {
  concept_id: string
  canonical_title: string
  aliases: string[]
  concept_type: string
  domains: string[]
  status: string
  review_status: string
  vault_status: string
  file_path: string
  updated_at: string | null
  overview_markdown: string
  body_markdown: string
  raw_markdown: string
  sections: ConceptSection[]
  modules: ConceptModule[]
  relationships: GraphRelationship[]
  learning_encounters: Array<Record<string, unknown>>
  warnings: Array<Record<string, unknown>>
  obsidian_uri: string
}

export interface GraphNode {
  id: string
  title: string
  concept_type: string
  domains: string[]
  status: string
  vault_status: string
  review_status: string
  selected: boolean
}

export interface GraphEdge {
  id: string
  source: string
  target: string
  relationship_type: string
  learning_role: string
  confidence: string
  status: string
}

export interface GraphProjection {
  center: string | null
  nodes: GraphNode[]
  edges: GraphEdge[]
  legend: Record<string, string>
}

export interface CreateIntent {
  intent: string
  learning_goal: string
  user_context: string
  source_type: string | null
  source_title: string | null
  source_unit: string | null
  source_section: string | null
  source_link: string | null
  source_id: string | null
  target_concept_id: string | null
  target_module_id: string | null
  requested_module_type: string | null
  scaffold_preferences: string[]
  search_context: Record<string, unknown>
}

export interface ModuleProposal {
  id: string
  type: string
  title: string
  focus: string | null
  selected: boolean
  reason: string
  origin: string
}

export interface RelationshipProposal {
  relationship_type: string
  target_title: string
  target_id: string | null
  learning_role: string
  confidence: string
  selected: boolean
  evidence: string
}

export interface EncounterProposal {
  source_type: string
  source_title: string
  unit: string | null
  section: string | null
  link: string | null
  source_id: string | null
  selected: boolean
}

export interface CreateProposal {
  proposal_id: string
  action: string
  canonical_title: string
  target_concept_id: string | null
  target_path: string
  concept_type: string
  domains: string[]
  aliases_to_add: string[]
  modules: ModuleProposal[]
  relationships: RelationshipProposal[]
  encounter: EncounterProposal | null
  possible_matches: Array<{
    concept_id: string
    title: string
    evidence: string[]
    vault_status: string | null
  }>
  backlog_candidates: Array<Record<string, unknown>>
  evidence: string[]
  warnings: string[]
  confidence: string
  reasoning_mode: string
  index_revision: number
  intent: CreateIntent
  raw_recommendation: Record<string, unknown>
}

export interface GeneratedDraft {
  proposal_id: string
  operation: 'create' | 'update' | 'no_change'
  concept_id: string
  target_path: string
  markdown: string
  selected_modules: string[]
  warnings: string[]
}

export interface DraftPreview {
  operation: string
  target_path: string
  would_create: boolean
  would_update: boolean
  can_commit: boolean
  diff: string
  warnings: Array<Record<string, unknown>>
  critical_errors: Array<Record<string, unknown>>
}

export interface DraftSnapshot {
  id: string
  concept_id: string
  title: string
  target_path: string
  operation: 'create' | 'update' | 'no_change'
  markdown: string
  recommendation: Record<string, unknown> | null
  created_at: string
  updated_at: string
}

export type ReviewSeverity = 'critical' | 'recommended' | 'optional'
export type ReviewFindingStatus = 'open' | 'resolved' | 'applied' | 'rejected'
export type ReviewReadiness =
  | 'needs_revision'
  | 'approved_with_suggestions'
  | 'approved'

export interface ReviewAnchor {
  target_type: string
  module_id: string | null
  heading: string | null
  start_offset: number | null
  end_offset: number | null
  line_start: number | null
  line_end: number | null
}

export interface ReviewFinding {
  id: string
  review_id: string
  concept_id: string
  module_id: string | null
  category: 'preflight' | 'coverage' | 'conceptual' | 'relationship' | 'source_grounding'
  severity: ReviewSeverity
  message: string
  anchor: ReviewAnchor | null
  quoted_text: string | null
  proposed_patch: string | null
  status: ReviewFindingStatus
  decision_note: string | null
  created_at: string
  resolved_at: string | null
}

export interface ReviewSummary {
  critical_count: number
  recommended_count: number
  optional_count: number
  open_critical_count: number
  open_recommended_count: number
  missing_essential_modules: string[]
  content_hash: string
  agent_mode: string
  can_accept: boolean
  blockers: string[]
}

export interface ReviewSession {
  id: string
  concept_id: string
  file_path: string
  status: 'queued' | 'running' | 'completed' | 'failed'
  readiness: ReviewReadiness
  summary: ReviewSummary
  created_at: string
  completed_at: string | null
  findings: ReviewFinding[]
}

export interface ReviewQueueItem {
  concept_id: string
  canonical_title: string
  file_path: string
  concept_type: string
  status: string
  review_status: string
  vault_status: 'draft'
  updated_at: string | null
  latest_review: {
    id: string
    status: ReviewSession['status']
    readiness: ReviewReadiness
    completed_at: string | null
  } | null
  open_critical_count: number
}

export interface AcceptanceGate {
  concept_id: string
  review_id: string | null
  readiness: ReviewReadiness | null
  can_accept: boolean
  requires_acknowledgement: boolean
  blockers: string[]
  recommendations: string[]
  preview_diff: string
}

export interface PatchPreview {
  finding_id: string
  target_path: string
  replacement: string
  diff: string
  can_commit: boolean
  warnings: Array<Record<string, unknown>>
  critical_errors: Array<Record<string, unknown>>
}

export interface SourceRecord {
  id: string
  title: string
  source_type: 'pdf' | 'markdown' | 'text' | 'html' | 'transcript'
  status: 'queued' | 'extracting' | 'chunking' | 'embedding' | 'ready' | 'failed'
  original_filename: string
  asset_path: string
  mime_type: string | null
  content_hash: string
  size_bytes: number
  page_count: number | null
  metadata: Record<string, unknown>
  processing_error: string | null
  created_at: string
  updated_at: string
  chunk_count: number
  chunks?: SourceChunk[]
}

export interface SourceChunk {
  id: string
  source_id: string
  ordinal: number
  text: string
  section: string | null
  page: number | null
  timestamp_start: number | null
  timestamp_end: number | null
  char_start: number | null
  char_end: number | null
  token_count: number
}

export interface Citation {
  source_id: string
  source_title: string
  chunk_id: string
  locator: string
  quote: string
  section: string | null
  page: number | null
  timestamp_start: number | null
  timestamp_end: number | null
}

export interface RetrievalHit {
  chunk_id: string
  source_id: string
  source_title: string
  text: string
  score: number
  semantic_score: number
  lexical_score: number
  citation: Citation
}

export interface SourceContribution {
  id: string
  source_id: string
  concept_id: string
  classification: string
  summary: string
  evidence: Citation[]
  proposed_module: {
    type: string
    title: string
    focus: string
    source_id: string
    citations: Citation[]
  } | null
  status: 'proposed' | 'accepted' | 'rejected'
  created_at?: string
  updated_at?: string
}

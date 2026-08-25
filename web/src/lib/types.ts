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

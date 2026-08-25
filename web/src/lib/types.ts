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

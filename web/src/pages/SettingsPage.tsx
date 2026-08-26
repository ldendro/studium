import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Archive,
  CheckCircle2,
  CloudOff,
  Database,
  Download,
  ExternalLink,
  FileArchive,
  FolderOpen,
  HardDrive,
  HeartPulse,
  KeyRound,
  LockKeyhole,
  RefreshCw,
  RotateCcw,
  Save,
  Server,
  ShieldCheck,
  Trash2,
  Upload,
} from 'lucide-react'
import { useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { api } from '../lib/api'
import type {
  Job,
  ProductArtifact,
  ProductOverview,
  ProviderConfiguration,
  WorkspaceHealth,
} from '../lib/types'
import { useToast } from '../components/toast-context'
import { useWorkspace } from '../components/workspace-context'
import { Badge, Button, EmptyState, Field, Input, PageHeader, Panel, Skeleton } from '../components/ui'

type SettingsSection = 'vault' | 'models' | 'privacy' | 'exports' | 'recovery' | 'data'

const sections: Array<{ id: SettingsSection; label: string }> = [
  { id: 'vault', label: 'Vault' },
  { id: 'models', label: 'Models' },
  { id: 'privacy', label: 'Privacy' },
  { id: 'exports', label: 'Export' },
  { id: 'recovery', label: 'Recovery' },
  { id: 'data', label: 'Data' },
]

export function SettingsPage() {
  const [params, setParams] = useSearchParams()
  const requested = params.get('section')
  const section = sections.some((item) => item.id === requested)
    ? (requested as SettingsSection)
    : 'vault'
  const overview = useQuery({
    queryKey: ['product-overview'],
    queryFn: () => api<ProductOverview>('/api/product/overview'),
  })

  return (
    <div className="page settings-page">
      <PageHeader
        eyebrow="Local control"
        title="Your data, models, and recovery."
        description="Studium is local by default. These controls make every storage location and every route outside this device explicit."
        actions={
          <Button variant="ghost" loading={overview.isFetching} onClick={() => void overview.refetch()}>
            <RefreshCw size={15} /> Refresh
          </Button>
        }
      />
      <nav className="settings-tabs" aria-label="Settings sections">
        {sections.map((item) => (
          <button
            className={item.id === section ? 'settings-tab settings-tab--active' : 'settings-tab'}
            key={item.id}
            type="button"
            aria-current={item.id === section ? 'page' : undefined}
            onClick={() => setParams({ section: item.id })}
          >
            {item.label}
          </button>
        ))}
      </nav>
      {overview.isLoading && (
        <div className="settings-loading" aria-label="Loading settings">
          <Skeleton />
          <Skeleton />
          <Skeleton />
        </div>
      )}
      {overview.isError && (
        <EmptyState
          icon={<CloudOff size={24} />}
          title="Settings are unavailable"
          description={overview.error.message}
          action={<Button onClick={() => void overview.refetch()}>Try again</Button>}
        />
      )}
      {overview.data && (
        <SettingsWorkspace
          key={`${overview.data.providers.embedding_provider}:${overview.data.providers.llm_provider}:${overview.data.providers.llm_model}`}
          overview={overview.data}
          section={section}
        />
      )}
    </div>
  )
}

function SettingsWorkspace({
  overview,
  section,
}: {
  overview: ProductOverview
  section: SettingsSection
}) {
  const { health, refresh } = useWorkspace()
  const { push } = useToast()
  const client = useQueryClient()
  const [providers, setProviders] = useState(overview.providers)
  const [vaultPath, setVaultPath] = useState(health?.vault_path ?? '')
  const [appDataPath, setAppDataPath] = useState('')
  const [restoreBackup, setRestoreBackup] = useState<string | null>(null)
  const [restorePath, setRestorePath] = useState('')
  const [restoreAppData, setRestoreAppData] = useState('')
  const [restoreConfirmation, setRestoreConfirmation] = useState('')
  const [clearTarget, setClearTarget] = useState<{ id: string; confirmation: string } | null>(null)
  const [clearConfirmation, setClearConfirmation] = useState('')

  const invalidateProduct = async () => {
    await client.invalidateQueries({ queryKey: ['product-overview'] })
    await client.invalidateQueries({ queryKey: ['jobs'] })
  }

  const providerMutation = useMutation({
    mutationFn: () =>
      api<{ reindex_job: Job | null }>('/api/product/providers', {
        method: 'PUT',
        body: providerPayload(providers),
      }),
    onSuccess: async ({ reindex_job }) => {
      await invalidateProduct()
      await refresh()
      push('Model settings saved', {
        description: reindex_job
          ? 'A background job is rebuilding the embedding space.'
          : 'The selected routing is active.',
        tone: 'success',
      })
    },
    onError: (error: Error) => push('Could not save model settings', { description: error.message, tone: 'danger' }),
  })

  const probeMutation = useMutation({
    mutationFn: () =>
      api<{
        embedding: { model_id: string; dimension: number }
        llm: { healthy: boolean; ready: boolean; model_id: string | null; message: string }
      }>('/api/product/providers/probe', { method: 'POST' }),
    onError: (error: Error) => push('Provider probe failed', { description: error.message, tone: 'danger' }),
  })

  const switchMutation = useMutation({
    mutationFn: () =>
      api<WorkspaceHealth>('/api/workspace/open', {
        method: 'POST',
        body: {
          vault_path: vaultPath,
          app_data_path: appDataPath.trim() || null,
        },
      }),
    onSuccess: async () => {
      await client.clear()
      await refresh()
      window.location.assign('/search')
    },
    onError: (error: Error) => push('Could not open vault', { description: error.message, tone: 'danger' }),
  })

  const closeMutation = useMutation({
    mutationFn: () => api('/api/workspace/close', { method: 'POST' }),
    onSuccess: async () => {
      await client.clear()
      window.location.assign('/')
    },
  })

  const exportMutation = useMutation({
    mutationFn: (kind: 'markdown' | 'sources' | 'complete') =>
      api<{ job: Job }>('/api/product/exports', {
        method: 'POST',
        body: { kind, background: true },
      }),
    onSuccess: async () => {
      await invalidateProduct()
      push('Export queued', {
        description: 'Progress is available from the activity button. Refresh this page when it completes.',
        tone: 'success',
      })
    },
    onError: (error: Error) => push('Export could not start', { description: error.message, tone: 'danger' }),
  })

  const backupMutation = useMutation({
    mutationFn: () =>
      api<{ job: Job }>('/api/product/backups', {
        method: 'POST',
        body: { background: true },
      }),
    onSuccess: async () => {
      await invalidateProduct()
      push('Backup queued', {
        description: 'Studium will verify the archive before marking the job complete.',
        tone: 'success',
      })
    },
    onError: (error: Error) => push('Backup could not start', { description: error.message, tone: 'danger' }),
  })

  const verifyMutation = useMutation({
    mutationFn: (id: string) =>
      api<{ valid: boolean; checked_files: number; errors: string[] }>(
        `/api/product/backups/${id}/verify`,
        { method: 'POST' },
      ),
    onSuccess: (result) =>
      push(result.valid ? 'Backup is healthy' : 'Backup failed verification', {
        description: result.valid
          ? `${result.checked_files} archived files passed checksum verification.`
          : result.errors.join(' '),
        tone: result.valid ? 'success' : 'danger',
      }),
  })

  const restoreMutation = useMutation({
    mutationFn: () =>
      api<{ vault_path: string }>(`/api/product/backups/${restoreBackup}/restore`, {
        method: 'POST',
        body: {
          target_vault_path: restorePath,
          app_data_path: restoreAppData.trim() || null,
          confirmation: restoreConfirmation,
        },
      }),
    onSuccess: (result) => {
      push('Recovery copy created', {
        description: `Recovered to ${result.vault_path}. The active vault was not changed.`,
        tone: 'success',
      })
      setRestoreBackup(null)
      setRestoreConfirmation('')
    },
    onError: (error: Error) => push('Recovery failed', { description: error.message, tone: 'danger' }),
  })

  const clearMutation = useMutation({
    mutationFn: ({ id, confirmation }: { id: string; confirmation: string }) =>
      api(`/api/product/data/${id}`, {
        method: 'DELETE',
        body: { confirmation },
      }),
    onSuccess: async () => {
      await invalidateProduct()
      await refresh()
      push('Local data cleared', { tone: 'success' })
      setClearTarget(null)
      setClearConfirmation('')
    },
    onError: (error: Error) => push('Data was not cleared', { description: error.message, tone: 'danger' }),
  })

  if (section === 'vault') {
    return (
      <div className="settings-grid">
        <Panel className="settings-card settings-card--wide">
          <div className="settings-card__heading">
            <span className="settings-icon settings-icon--blue"><FolderOpen size={19} /></span>
            <div><h2>Active vault</h2><p>Markdown remains the durable source of truth.</p></div>
            <Badge tone="success">Open</Badge>
          </div>
          <dl className="settings-facts">
            <div><dt>Name</dt><dd>{health?.vault_name}</dd></div>
            <div><dt>Path</dt><dd><code>{health?.vault_path}</code></dd></div>
            <div><dt>Index revision</dt><dd>{health?.index_revision}</dd></div>
            <div><dt>App schema</dt><dd>v{health?.app_schema_version}</dd></div>
          </dl>
        </Panel>
        <Panel className="settings-card">
          <div className="settings-card__heading">
            <span className="settings-icon"><RotateCcw size={19} /></span>
            <div><h2>Switch vault</h2><p>Open another local directory.</p></div>
          </div>
          <form className="settings-form" onSubmit={(event) => { event.preventDefault(); switchMutation.mutate() }}>
            <Field label="Vault directory"><Input value={vaultPath} onChange={(event) => setVaultPath(event.target.value)} required /></Field>
            <Field label="Application data override" hint="Leave blank to use the system default."><Input value={appDataPath} onChange={(event) => setAppDataPath(event.target.value)} /></Field>
            <Button variant="primary" loading={switchMutation.isPending} type="submit"><FolderOpen size={15} /> Open vault</Button>
          </form>
        </Panel>
        <Panel className="settings-card">
          <div className="settings-card__heading">
            <span className="settings-icon settings-icon--red"><CloudOff size={19} /></span>
            <div><h2>Return to onboarding</h2><p>Close runtime resources without deleting files.</p></div>
          </div>
          <p className="settings-copy">Your vault, index, app database, exports, and backups remain exactly where they are.</p>
          <Button variant="secondary" loading={closeMutation.isPending} onClick={() => closeMutation.mutate()}>Close active vault</Button>
        </Panel>
      </div>
    )
  }

  if (section === 'models') {
    return (
      <div className="settings-grid">
        <Panel className="settings-card settings-card--wide">
          <div className="settings-card__heading">
            <span className="settings-icon settings-icon--accent"><Server size={19} /></span>
            <div><h2>Model routing</h2><p>Deterministic workflows work even when language-model assistance is disabled.</p></div>
            <Badge tone={providers.route === 'remote' ? 'warning' : 'success'}>{providers.route}</Badge>
          </div>
          <div className="settings-form settings-form--columns">
            <Field label="Embedding provider">
              <select className="input" value={providers.embedding_provider} onChange={(event) => setProviders({ ...providers, embedding_provider: event.target.value as ProviderConfiguration['embedding_provider'] })}>
                <option value="local_hash">Local feature hashing (built in)</option>
                <option value="sentence_transformers">Sentence Transformers (optional)</option>
              </select>
            </Field>
            <Field label="Embedding model" hint="Used only by Sentence Transformers.">
              <Input value={providers.embedding_model} onChange={(event) => setProviders({ ...providers, embedding_model: event.target.value })} />
            </Field>
            <Field label="Language model">
              <select className="input" value={providers.llm_provider} onChange={(event) => setProviders({ ...providers, llm_provider: event.target.value as ProviderConfiguration['llm_provider'] })}>
                <option value="disabled">Disabled — deterministic mode</option>
                <option value="openai_compatible">OpenAI-compatible endpoint</option>
              </select>
            </Field>
            <Field label="Model identifier"><Input value={providers.llm_model} disabled={providers.llm_provider === 'disabled'} onChange={(event) => setProviders({ ...providers, llm_model: event.target.value })} /></Field>
            <Field label="Base URL"><Input value={providers.llm_base_url} disabled={providers.llm_provider === 'disabled'} onChange={(event) => setProviders({ ...providers, llm_base_url: event.target.value })} /></Field>
            <Field label="API-key environment variable" hint={providers.api_key_configured ? 'A value is available to the local service.' : 'No value is currently set; local Ollama-style endpoints do not require one.'}>
              <Input value={providers.llm_api_key_env} disabled={providers.llm_provider === 'disabled'} onChange={(event) => setProviders({ ...providers, llm_api_key_env: event.target.value })} />
            </Field>
          </div>
          <div className="settings-actions">
            <Button variant="primary" loading={providerMutation.isPending} onClick={() => providerMutation.mutate()}><Save size={15} /> Save routing</Button>
            <Button loading={probeMutation.isPending} onClick={() => probeMutation.mutate()}><HeartPulse size={15} /> Probe now</Button>
          </div>
          {probeMutation.data && (
            <div className="provider-health" aria-live="polite">
              <CheckCircle2 size={17} />
              <span><strong>{probeMutation.data.embedding.model_id}</strong><small>{probeMutation.data.embedding.dimension} dimensions</small></span>
              <span><strong>{probeMutation.data.llm.model_id ?? 'Deterministic mode'}</strong><small>{probeMutation.data.llm.message}</small></span>
            </div>
          )}
        </Panel>
      </div>
    )
  }

  if (section === 'privacy') {
    return (
      <div className="settings-grid">
        <Panel className="settings-card settings-card--wide">
          <div className="privacy-hero">
            <span><ShieldCheck size={27} /></span>
            <div>
              <p className="eyebrow">Content boundary</p>
              <h2>{providers.remote_data_allowed ? 'Remote routing is explicitly allowed.' : 'Your note content stays on this device.'}</h2>
              <p>Studium never adds analytics, cloud sync, or authentication traffic. A remote model can receive content only after this control is enabled and a remote URL is saved.</p>
            </div>
          </div>
          <label className="settings-toggle">
            <input type="checkbox" checked={providers.remote_data_allowed} onChange={(event) => setProviders({ ...providers, remote_data_allowed: event.target.checked })} />
            <span><strong>Allow note content to reach a remote model endpoint</strong><small>Localhost and loopback endpoints do not require this permission.</small></span>
          </label>
          <Button variant="primary" loading={providerMutation.isPending} onClick={() => providerMutation.mutate()}><Save size={15} /> Save privacy control</Button>
        </Panel>
        <Panel className="settings-card">
          <div className="settings-card__heading"><span className="settings-icon"><KeyRound size={19} /></span><div><h2>Secrets</h2><p>Keys are never stored in the app database.</p></div></div>
          <p className="settings-copy">Set <code>{providers.llm_api_key_env}</code> in the environment that starts Studium. The UI sees only whether a value exists.</p>
        </Panel>
        <Panel className="settings-card">
          <div className="settings-card__heading"><span className="settings-icon"><LockKeyhole size={19} /></span><div><h2>Content-safe logs</h2><p>Request bodies and prompts are omitted.</p></div></div>
          <p className="settings-copy">Diagnostics contain event names, status codes, timing, job IDs, and exception types—not Markdown, source excerpts, search text, or credentials.</p>
        </Panel>
      </div>
    )
  }

  if (section === 'exports') {
    return (
      <div className="settings-stack">
        <Panel className="settings-card">
          <div className="settings-card__heading"><span className="settings-icon settings-icon--blue"><FileArchive size={19} /></span><div><h2>Portable exports</h2><p>ZIP archives include a manifest and per-file checksums.</p></div></div>
          <div className="export-options">
            <ExportOption title="Markdown" description="Every Markdown file, preserving vault-relative paths." onClick={() => exportMutation.mutate('markdown')} />
            <ExportOption title="Sources" description="Original local source assets, organized by stable source ID." onClick={() => exportMutation.mutate('sources')} />
            <ExportOption title="Complete" description="Markdown and source assets together. Learning history stays private." onClick={() => exportMutation.mutate('complete')} />
          </div>
        </Panel>
        <ArtifactList title="Recent exports" artifacts={overview.exports} empty="No exports have been generated yet." />
      </div>
    )
  }

  if (section === 'recovery') {
    return (
      <div className="settings-stack">
        <Panel className="settings-card settings-card--wide">
          <div className="settings-card__heading"><span className="settings-icon settings-icon--accent"><Archive size={19} /></span><div><h2>Backup and recovery</h2><p>A backup contains the vault, a consistent SQLite snapshot, sources, and your generated learning profile.</p></div></div>
          <div className="settings-actions">
            <Button variant="primary" loading={backupMutation.isPending} onClick={() => backupMutation.mutate()}><HardDrive size={15} /> Create verified backup</Button>
          </div>
          <p className="settings-copy">Recovery always creates a separate copy. It never overwrites the active vault.</p>
        </Panel>
        <Panel className="settings-card artifact-panel">
          <div className="artifact-panel__header"><div><p className="eyebrow">Snapshots</p><h2>Available backups</h2></div></div>
          {overview.backups.length ? (
            <div className="artifact-list">
              {overview.backups.map((artifact) => (
                <div className="artifact-row" key={artifact.id}>
                  <Archive size={18} />
                  <span><strong>{new Date(artifact.created_at).toLocaleString()}</strong><small>{artifact.file_count} files · {formatBytes(artifact.size_bytes)}</small></span>
                  <div className="artifact-row__actions">
                    <Button size="small" onClick={() => verifyMutation.mutate(artifact.id)}>Verify</Button>
                    <Button size="small" onClick={() => { setRestoreBackup(artifact.id); setRestorePath(`${health?.vault_path ?? ''}-recovered`) }}><RotateCcw size={14} /> Restore copy</Button>
                    <a className="button button--ghost button--small" href={artifact.download_url}><Download size={14} /> Download</a>
                  </div>
                </div>
              ))}
            </div>
          ) : <EmptyState compact icon={<Archive size={20} />} title="No backups yet" description="Create one before a risky import or major editing session." />}
        </Panel>
        {restoreBackup && (
          <Panel className="settings-card settings-card--wide recovery-form">
            <div className="settings-card__heading"><span className="settings-icon settings-icon--red"><RotateCcw size={19} /></span><div><h2>Restore a separate copy</h2><p>The target must not exist and must be separate from the active vault.</p></div></div>
            <Field label="Recovered vault path"><Input value={restorePath} onChange={(event) => setRestorePath(event.target.value)} /></Field>
            <Field label="Application data root" hint="Leave blank to use the current system default."><Input value={restoreAppData} onChange={(event) => setRestoreAppData(event.target.value)} /></Field>
            <Field label="Type RESTORE COPY to confirm"><Input value={restoreConfirmation} onChange={(event) => setRestoreConfirmation(event.target.value)} /></Field>
            <div className="settings-actions">
              <Button variant="danger" loading={restoreMutation.isPending} disabled={restoreConfirmation !== 'RESTORE COPY' || !restorePath.trim()} onClick={() => restoreMutation.mutate()}><RotateCcw size={15} /> Restore copy</Button>
              <Button variant="ghost" onClick={() => setRestoreBackup(null)}>Cancel</Button>
            </div>
          </Panel>
        )}
      </div>
    )
  }

  return (
    <div className="settings-stack">
      <Panel className="settings-card settings-card--wide">
        <div className="settings-card__heading"><span className="settings-icon settings-icon--blue"><Database size={19} /></span><div><h2>Data locations</h2><p>Markdown and rebuildable or app-specific data remain visibly separate.</p></div></div>
        <div className="data-location-list">
          {overview.locations.map((location) => (
            <div className="data-location" key={location.id}>
              <span className="data-location__icon">{location.id === 'vault' ? <FolderOpen size={17} /> : <Database size={17} />}</span>
              <span><strong>{location.label}</strong><code>{location.path}</code></span>
              <small>{formatBytes(location.size_bytes)}</small>
              {location.clearable && location.confirmation && (
                <Button variant="ghost" size="small" onClick={() => { setClearTarget({ id: location.id, confirmation: location.confirmation ?? '' }); setClearConfirmation('') }}>
                  <Trash2 size={14} /> {location.id === 'derived_index' ? 'Reset' : 'Clear'}
                </Button>
              )}
            </div>
          ))}
        </div>
      </Panel>
      {clearTarget && (
        <Panel className="settings-card settings-card--wide destructive-panel">
          <div><p className="eyebrow">Confirmation required</p><h2>Clear {clearTarget.id.replaceAll('_', ' ')}?</h2><p>This affects local application data only. Vault Markdown is never included in a clear action.</p></div>
          <Field label={`Type ${clearTarget.confirmation} to confirm`}><Input value={clearConfirmation} onChange={(event) => setClearConfirmation(event.target.value)} /></Field>
          <div className="settings-actions">
            <Button variant="danger" loading={clearMutation.isPending} disabled={clearConfirmation !== clearTarget.confirmation} onClick={() => clearMutation.mutate({ id: clearTarget.id, confirmation: clearConfirmation })}><Trash2 size={15} /> Confirm clear</Button>
            <Button variant="ghost" onClick={() => setClearTarget(null)}>Cancel</Button>
          </div>
        </Panel>
      )}
    </div>
  )
}

function ExportOption({ title, description, onClick }: { title: string; description: string; onClick: () => void }) {
  return (
    <button className="export-option" type="button" onClick={onClick}>
      <Upload size={18} />
      <span><strong>{title}</strong><small>{description}</small></span>
      <ExternalLink size={15} />
    </button>
  )
}

function ArtifactList({ title, artifacts, empty }: { title: string; artifacts: ProductArtifact[]; empty: string }) {
  return (
    <Panel className="settings-card artifact-panel">
      <div className="artifact-panel__header"><div><p className="eyebrow">Portable files</p><h2>{title}</h2></div></div>
      {artifacts.length ? (
        <div className="artifact-list">
          {artifacts.map((artifact) => (
            <div className="artifact-row" key={artifact.id}>
              <FileArchive size={18} />
              <span><strong>{artifact.kind ?? artifact.artifact_type}</strong><small>{new Date(artifact.created_at).toLocaleString()} · {artifact.file_count} files · {formatBytes(artifact.size_bytes)}</small></span>
              <a className="button button--ghost button--small" href={artifact.download_url}><Download size={14} /> Download</a>
            </div>
          ))}
        </div>
      ) : <EmptyState compact icon={<FileArchive size={20} />} title="Nothing here yet" description={empty} />}
    </Panel>
  )
}

function providerPayload(providers: ProviderConfiguration) {
  return {
    embedding_provider: providers.embedding_provider,
    embedding_model: providers.embedding_model,
    llm_provider: providers.llm_provider,
    llm_base_url: providers.llm_base_url,
    llm_model: providers.llm_model,
    llm_api_key_env: providers.llm_api_key_env,
    remote_data_allowed: providers.remote_data_allowed,
  }
}

function formatBytes(value: number) {
  if (value < 1024) return `${value} B`
  if (value < 1024 ** 2) return `${(value / 1024).toFixed(1)} KB`
  if (value < 1024 ** 3) return `${(value / 1024 ** 2).toFixed(1)} MB`
  return `${(value / 1024 ** 3).toFixed(1)} GB`
}

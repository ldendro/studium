import { useMutation } from '@tanstack/react-query'
import {
  ArchiveRestore,
  ArrowRight,
  BookOpenText,
  CheckCircle2,
  FileArchive,
  FolderOpen,
  LockKeyhole,
  Plus,
  SearchCheck,
  Sparkles,
  Upload,
} from 'lucide-react'
import { useState, type FormEvent } from 'react'
import { api, upload } from '../lib/api'
import type { VaultInspection, WorkspaceHealth } from '../lib/types'
import { useToast } from '../components/toast-context'
import { useWorkspace } from '../components/workspace-context'
import { Badge, Button, Field, Input } from '../components/ui'

type OnboardingMode = 'open' | 'create' | 'import'

export function OnboardingPage() {
  const [mode, setMode] = useState<OnboardingMode>('open')
  const [vaultPath, setVaultPath] = useState('')
  const [appDataPath, setAppDataPath] = useState('')
  const [demo, setDemo] = useState(true)
  const [archive, setArchive] = useState<File | null>(null)
  const { refresh } = useWorkspace()
  const { push } = useToast()
  const openMutation = useMutation({
    mutationFn: () =>
      api<WorkspaceHealth>('/api/workspace/open', {
        method: 'POST',
        body: {
          vault_path: vaultPath,
          app_data_path: appDataPath.trim() || null,
        },
      }),
    onSuccess: async () => {
      await refresh()
      push('Vault opened', {
        description: 'Your concept index is synchronized and ready.',
        tone: 'success',
      })
    },
    onError: (error: Error) =>
      push('Could not open this vault', { description: error.message, tone: 'danger' }),
  })

  const createMutation = useMutation({
    mutationFn: () =>
      api<{ workspace: WorkspaceHealth; demo: Record<string, unknown> | null }>(
        '/api/workspace/create',
        {
          method: 'POST',
          body: {
            vault_path: vaultPath,
            app_data_path: appDataPath.trim() || null,
            demo,
          },
        },
      ),
    onSuccess: async ({ demo: seeded }) => {
      await refresh()
      push(seeded ? 'Demo workspace is ready' : 'Vault created', {
        description: seeded
          ? 'Search, sources, review, retention, mastery, and profile data are ready to explore.'
          : 'Your empty Markdown-first workspace is open.',
        tone: 'success',
      })
    },
    onError: (error: Error) =>
      push('Could not create this vault', { description: error.message, tone: 'danger' }),
  })

  const importMutation = useMutation({
    mutationFn: () => {
      if (!archive) throw new Error('Choose a ZIP archive first.')
      const form = new FormData()
      form.set('file', archive)
      form.set('target_vault_path', vaultPath)
      if (appDataPath.trim()) form.set('app_data_path', appDataPath.trim())
      return upload<{ workspace: WorkspaceHealth; import: VaultInspection }>(
        '/api/product/vault/import',
        form,
      )
    },
    onSuccess: async ({ import: report }) => {
      await refresh()
      push('Vault imported', {
        description: `${report.imported_files ?? 0} files imported; ${report.valid_concepts} valid concepts indexed.`,
        tone: report.invalid_markdown ? 'warning' : 'success',
      })
    },
    onError: (error: Error) =>
      push('Could not import this archive', { description: error.message, tone: 'danger' }),
  })

  const inspectMutation = useMutation({
    mutationFn: () =>
      api<VaultInspection>(`/api/workspace/inspect?path=${encodeURIComponent(vaultPath)}`),
  })

  const submit = (event: FormEvent) => {
    event.preventDefault()
    if (!vaultPath.trim()) return
    if (mode === 'open') openMutation.mutate()
    if (mode === 'create') createMutation.mutate()
    if (mode === 'import') importMutation.mutate()
  }

  const pending =
    openMutation.isPending || createMutation.isPending || importMutation.isPending

  return (
    <main className="onboarding">
      <div className="onboarding__ambient" aria-hidden />
      <div className="onboarding__brand">
        <span className="brand__mark">
          <Sparkles size={20} />
        </span>
        <strong>Studium</strong>
      </div>
      <section className="onboarding__content">
        <div className="onboarding__intro">
          <p className="eyebrow">Your learning system</p>
          <h1>Turn what you study into knowledge you can retrieve.</h1>
          <p>
            Studium keeps your Markdown vault portable while helping you search, scaffold,
            review, and retain connected concepts.
          </p>
          <div className="onboarding__principles">
            <div>
              <BookOpenText size={19} />
              <span>
                <strong>Markdown stays yours</strong>
                <small>Every concept remains Obsidian-compatible.</small>
              </span>
            </div>
            <div>
              <LockKeyhole size={19} />
              <span>
                <strong>Local by default</strong>
                <small>Your learning history stays on this device.</small>
              </span>
            </div>
            <div>
              <CheckCircle2 size={19} />
              <span>
                <strong>You approve every change</strong>
                <small>AI proposes; your vault changes only when you decide.</small>
              </span>
            </div>
          </div>
        </div>
        <form className="onboarding__card onboarding__card--product" onSubmit={submit}>
          <div className="onboarding__card-icon">
            {mode === 'open' && <FolderOpen size={22} />}
            {mode === 'create' && <Plus size={22} />}
            {mode === 'import' && <ArchiveRestore size={22} />}
          </div>
          <h2>
            {mode === 'open' && 'Open your Studium vault'}
            {mode === 'create' && 'Create a local workspace'}
            {mode === 'import' && 'Import a portable vault'}
          </h2>
          <p>
            {mode === 'open' && 'Validate and index an existing local directory without moving it.'}
            {mode === 'create' && 'Start empty or seed a coherent workspace that demonstrates every learning loop.'}
            {mode === 'import' && 'Safely extract a ZIP into a new directory, then validate it before indexing.'}
          </p>
          <div className="onboarding-modes" aria-label="Workspace setup method">
            <button type="button" aria-pressed={mode === 'open'} onClick={() => setMode('open')}>
              <FolderOpen size={14} /> Open
            </button>
            <button type="button" aria-pressed={mode === 'create'} onClick={() => setMode('create')}>
              <Plus size={14} /> Create
            </button>
            <button type="button" aria-pressed={mode === 'import'} onClick={() => setMode('import')}>
              <Upload size={14} /> Import ZIP
            </button>
          </div>
          {mode === 'import' && (
            <Field label="Vault archive" hint="ZIP only; compressed size is limited to 200 MB.">
              <label className="file-picker">
                <FileArchive size={17} />
                <span>{archive?.name ?? 'Choose a ZIP archive'}</span>
                <input
                  type="file"
                  accept=".zip,application/zip"
                  onChange={(event) => setArchive(event.target.files?.[0] ?? null)}
                  required
                />
              </label>
            </Field>
          )}
          <Field
            label={mode === 'open' ? 'Existing vault directory' : 'New vault directory'}
            hint={
              mode === 'open'
                ? 'Example: /Users/you/Documents/Studium'
                : 'The target must not exist or must be empty.'
            }
          >
            <Input
              value={vaultPath}
              onChange={(event) => setVaultPath(event.target.value)}
              placeholder="/path/to/your/vault"
              autoFocus
              required
            />
          </Field>
          {mode === 'open' && (
            <div className="vault-inspection">
              <Button
                size="small"
                type="button"
                loading={inspectMutation.isPending}
                disabled={!vaultPath.trim()}
                onClick={() => inspectMutation.mutate()}
              >
                <SearchCheck size={14} /> Inspect before opening
              </Button>
              {inspectMutation.data && (
                <div aria-live="polite">
                  <Badge tone={inspectMutation.data.ready ? 'success' : 'danger'}>
                    {inspectMutation.data.ready ? 'Ready' : 'Unavailable'}
                  </Badge>
                  <span>
                    {inspectMutation.data.markdown_files} Markdown ·{' '}
                    {inspectMutation.data.valid_concepts} valid concepts
                  </span>
                  <small>{inspectMutation.data.message}</small>
                </div>
              )}
            </div>
          )}
          {mode === 'create' && (
            <label className="onboarding-demo">
              <input type="checkbox" checked={demo} onChange={(event) => setDemo(event.target.checked)} />
              <span>
                <strong>Seed the guided demonstration workspace</strong>
                <small>Includes connected concepts, a grounded source, review draft, backlog, retention evidence, mastery, and profile preferences.</small>
              </span>
            </label>
          )}
          <details>
            <summary>Advanced storage</summary>
            <Field
              label="Application data directory"
              hint="Optional. Indexes, source processing, and learning history live here."
            >
              <Input
                value={appDataPath}
                onChange={(event) => setAppDataPath(event.target.value)}
                placeholder="Use system default"
              />
            </Field>
          </details>
          <Button variant="primary" size="large" loading={pending} type="submit">
            {mode === 'open' && 'Open vault'}
            {mode === 'create' && (demo ? 'Create demo workspace' : 'Create empty vault')}
            {mode === 'import' && 'Import and open'}
            <ArrowRight size={17} />
          </Button>
          <small className="onboarding__privacy">
            Files stay on this device. Remote model routing requires explicit opt-in in Settings.
          </small>
        </form>
      </section>
    </main>
  )
}

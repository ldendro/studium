import { useMutation } from '@tanstack/react-query'
import { ArrowRight, BookOpenText, CheckCircle2, FolderOpen, LockKeyhole, Sparkles } from 'lucide-react'
import { useState, type FormEvent } from 'react'
import { api } from '../lib/api'
import type { WorkspaceHealth } from '../lib/types'
import { useToast } from '../components/toast-context'
import { useWorkspace } from '../components/workspace-context'
import { Button, Field, Input } from '../components/ui'

export function OnboardingPage() {
  const [vaultPath, setVaultPath] = useState('')
  const [appDataPath, setAppDataPath] = useState('')
  const { refresh } = useWorkspace()
  const { push } = useToast()
  const mutation = useMutation({
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

  const submit = (event: FormEvent) => {
    event.preventDefault()
    if (vaultPath.trim()) mutation.mutate()
  }

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
        <form className="onboarding__card" onSubmit={submit}>
          <div className="onboarding__card-icon">
            <FolderOpen size={22} />
          </div>
          <h2>Open your Studium vault</h2>
          <p>Select an existing directory. Studium will validate and index its concept notes.</p>
          <Field label="Vault directory" hint="Example: /Users/you/Documents/Studium">
            <Input
              value={vaultPath}
              onChange={(event) => setVaultPath(event.target.value)}
              placeholder="/path/to/your/vault"
              autoFocus
              required
            />
          </Field>
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
          <Button variant="primary" size="large" loading={mutation.isPending} type="submit">
            Open vault <ArrowRight size={17} />
          </Button>
          <small className="onboarding__privacy">
            Nothing is uploaded. Model and privacy controls can be changed later.
          </small>
        </form>
      </section>
    </main>
  )
}

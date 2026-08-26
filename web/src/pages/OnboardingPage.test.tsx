import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { renderWithApp } from '../test/render'
import { OnboardingPage } from './OnboardingPage'

function jsonResponse(body: unknown, status = 200): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    headers: {
      get: (name: string) => (name.toLowerCase() === 'content-type' ? 'application/json' : null),
    },
    json: async () => body,
    text: async () => JSON.stringify(body),
  } as unknown as Response
}

describe('OnboardingPage', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
    vi.restoreAllMocks()
  })

  it('creates a demonstration workspace and refreshes health', async () => {
    const refresh = vi.fn(async () => undefined)
    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input)
      if (url.includes('/api/workspace/create')) {
        return jsonResponse({
          workspace: { status: 'ok', workspace_open: true, vault_name: 'demo' },
          demo: { seeded: true },
        }, 201)
      }
      return jsonResponse({ detail: `unexpected ${url}` }, 500)
    })
    vi.stubGlobal('fetch', fetchMock)
    const user = userEvent.setup()
    renderWithApp(<OnboardingPage />, { workspace: { refresh } })

    await user.click(screen.getByRole('button', { name: 'Create' }))
    expect(screen.getByRole('heading', { name: 'Create a local workspace' })).toBeVisible()
    await user.type(screen.getByLabelText('New vault directory'), '/tmp/studium-demo')
    await user.click(screen.getByRole('button', { name: 'Create demo workspace' }))

    await screen.findByText('Demo workspace is ready')
    expect(refresh).toHaveBeenCalled()
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/workspace/create',
      expect.objectContaining({
        method: 'POST',
      }),
    )
    const createCall = fetchMock.mock.calls.find(([url]) => String(url).includes('/api/workspace/create'))
    expect(createCall).toBeDefined()
    const init = createCall?.[1] as RequestInit
    expect(JSON.parse(String(init.body))).toMatchObject({
      vault_path: '/tmp/studium-demo',
      demo: true,
    })
  })

  it('inspects an existing vault before opening', async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input)
      if (url.includes('/api/workspace/inspect')) {
        return jsonResponse({
          path: '/tmp/existing-vault',
          exists: true,
          is_directory: true,
          markdown_files: 4,
          valid_concepts: 3,
          invalid_markdown: 0,
          ready: true,
          message: 'Vault can be opened.',
        })
      }
      return jsonResponse({ detail: `unexpected ${url}` }, 500)
    })
    vi.stubGlobal('fetch', fetchMock)
    const user = userEvent.setup()
    renderWithApp(<OnboardingPage />)

    await user.type(screen.getByLabelText('Existing vault directory'), '/tmp/existing-vault')
    await user.click(screen.getByRole('button', { name: 'Inspect before opening' }))
    expect(await screen.findByText(/3 valid concepts/)).toBeVisible()
    expect(screen.getByText('Ready')).toBeVisible()
  })
})

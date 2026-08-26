import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, type RenderOptions } from '@testing-library/react'
import type { PropsWithChildren, ReactElement } from 'react'
import { MemoryRouter } from 'react-router-dom'
import { ToastProvider } from '../components/ToastProvider'
import { WorkspaceContext, type WorkspaceContextValue } from '../components/workspace-context'
import type { WorkspaceHealth } from '../lib/types'

export const closedWorkspace: WorkspaceHealth = {
  status: 'onboarding',
  workspace_open: false,
}

export function createQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  })
}

export function renderWithApp(
  ui: ReactElement,
  options: RenderOptions & {
    workspace?: Partial<WorkspaceContextValue>
    route?: string
  } = {},
) {
  const queryClient = createQueryClient()
  const workspace: WorkspaceContextValue = {
    health: closedWorkspace,
    loading: false,
    error: null,
    refresh: async () => undefined,
    ...options.workspace,
  }
  const route = options.route ?? '/'
  const renderOptions: RenderOptions = { container: options.container, baseElement: options.baseElement }
  function Wrapper({ children }: PropsWithChildren) {
    return (
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={[route]}>
          <ToastProvider>
            <WorkspaceContext.Provider value={workspace}>{children}</WorkspaceContext.Provider>
          </ToastProvider>
        </MemoryRouter>
      </QueryClientProvider>
    )
  }
  return { ...render(ui, { wrapper: Wrapper, ...renderOptions }), workspace }
}

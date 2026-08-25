import { useQuery, useQueryClient } from '@tanstack/react-query'
import { createContext, useContext, useMemo, type PropsWithChildren } from 'react'
import { api } from '../lib/api'
import type { WorkspaceHealth } from '../lib/types'

interface WorkspaceContextValue {
  health: WorkspaceHealth | undefined
  loading: boolean
  error: Error | null
  refresh: () => Promise<void>
}

const WorkspaceContext = createContext<WorkspaceContextValue | null>(null)

export function WorkspaceProvider({ children }: PropsWithChildren) {
  const client = useQueryClient()
  const query = useQuery({
    queryKey: ['workspace-health'],
    queryFn: () => api<WorkspaceHealth>('/api/health'),
    refetchInterval: (current) =>
      current.state.data?.workspace_open && current.state.data.last_sync?.status === 'failed'
        ? 10_000
        : 30_000,
    retry: 1,
  })
  const value = useMemo<WorkspaceContextValue>(
    () => ({
      health: query.data,
      loading: query.isLoading,
      error: query.error,
      refresh: async () => {
        await client.invalidateQueries({ queryKey: ['workspace-health'] })
      },
    }),
    [client, query.data, query.error, query.isLoading],
  )
  return <WorkspaceContext.Provider value={value}>{children}</WorkspaceContext.Provider>
}

export function useWorkspace() {
  const context = useContext(WorkspaceContext)
  if (!context) throw new Error('useWorkspace must be used inside WorkspaceProvider')
  return context
}

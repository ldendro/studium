import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useMemo, type PropsWithChildren } from 'react'
import { api } from '../lib/api'
import type { WorkspaceHealth } from '../lib/types'
import { WorkspaceContext, type WorkspaceContextValue } from './workspace-context'

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

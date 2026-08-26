import { createContext, useContext } from 'react'
import type { WorkspaceHealth } from '../lib/types'

export interface WorkspaceContextValue {
  health: WorkspaceHealth | undefined
  loading: boolean
  error: Error | null
  refresh: () => Promise<void>
}

export const WorkspaceContext = createContext<WorkspaceContextValue | null>(null)

export function useWorkspace() {
  const context = useContext(WorkspaceContext)
  if (!context) throw new Error('useWorkspace must be used inside WorkspaceProvider')
  return context
}

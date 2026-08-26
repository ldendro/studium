import { createContext, useContext } from 'react'
import type { NoticeTone } from '../lib/types'

export interface ToastApi {
  push: (title: string, options?: { description?: string; tone?: NoticeTone }) => void
}

export const ToastContext = createContext<ToastApi | null>(null)

export function useToast(): ToastApi {
  const context = useContext(ToastContext)
  if (!context) throw new Error('useToast must be used within ToastProvider')
  return context
}

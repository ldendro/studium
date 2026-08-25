import { CheckCircle2, Info, TriangleAlert, X, XCircle } from 'lucide-react'
import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type PropsWithChildren,
} from 'react'
import type { NoticeTone } from '../lib/types'

interface Toast {
  id: number
  title: string
  description?: string
  tone: NoticeTone
}

interface ToastApi {
  push: (title: string, options?: { description?: string; tone?: NoticeTone }) => void
}

const ToastContext = createContext<ToastApi | null>(null)

let nextToastId = 1

export function ToastProvider({ children }: PropsWithChildren) {
  const [toasts, setToasts] = useState<Toast[]>([])

  const dismiss = useCallback((id: number) => {
    setToasts((current) => current.filter((toast) => toast.id !== id))
  }, [])

  const push = useCallback(
    (title: string, options?: { description?: string; tone?: NoticeTone }) => {
      const id = nextToastId++
      setToasts((current) => [
        ...current,
        {
          id,
          title,
          description: options?.description,
          tone: options?.tone ?? 'neutral',
        },
      ])
      window.setTimeout(() => dismiss(id), 5200)
    },
    [dismiss],
  )

  const value = useMemo(() => ({ push }), [push])
  return (
    <ToastContext.Provider value={value}>
      {children}
      <div className="toast-region" role="region" aria-label="Notifications">
        {toasts.map((toast) => {
          const Icon =
            toast.tone === 'success'
              ? CheckCircle2
              : toast.tone === 'warning'
                ? TriangleAlert
                : toast.tone === 'danger'
                  ? XCircle
                  : Info
          return (
            <div key={toast.id} className={`toast toast--${toast.tone}`} role="status">
              <Icon size={18} aria-hidden />
              <div className="toast__copy">
                <strong>{toast.title}</strong>
                {toast.description && <p>{toast.description}</p>}
              </div>
              <button
                className="icon-button icon-button--subtle"
                type="button"
                aria-label="Dismiss notification"
                onClick={() => dismiss(toast.id)}
              >
                <X size={16} />
              </button>
            </div>
          )
        })}
      </div>
    </ToastContext.Provider>
  )
}

export function useToast(): ToastApi {
  const context = useContext(ToastContext)
  if (!context) throw new Error('useToast must be used within ToastProvider')
  return context
}

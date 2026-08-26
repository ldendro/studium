import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter } from 'react-router-dom'
import './index.css'
import App from './App.tsx'
import { RootErrorBoundary } from './components/RootErrorBoundary'
import { ToastProvider } from './components/ToastProvider'
import { WorkspaceProvider } from './components/WorkspaceProvider'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 15_000,
      refetchOnWindowFocus: false,
    },
  },
})

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <RootErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <ToastProvider>
            <WorkspaceProvider>
              <App />
            </WorkspaceProvider>
          </ToastProvider>
        </BrowserRouter>
      </QueryClientProvider>
    </RootErrorBoundary>
  </StrictMode>,
)

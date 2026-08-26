import { Component, type ErrorInfo, type ReactNode } from 'react'

export class RootErrorBoundary extends Component<{ children: ReactNode }, { error: Error | null }> {
  constructor(props: { children: ReactNode }) {
    super(props)
    this.state = { error: null }
  }

  static getDerivedStateFromError(error: Error) {
    return { error }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('Studium failed to render', error, info.componentStack)
  }

  render() {
    if (this.state.error) {
      return (
        <main className="fatal-state">
          <p className="eyebrow">Display problem</p>
          <h1>Studium could not render this screen.</h1>
          <p>{this.state.error.message}</p>
        </main>
      )
    }
    return this.props.children
  }
}

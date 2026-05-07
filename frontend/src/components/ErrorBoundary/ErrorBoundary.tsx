import { Component, ErrorInfo, ReactNode } from 'react'

interface Props {
  children: ReactNode
  fallback?: ReactNode
  onError?: (error: Error, info: ErrorInfo) => void
}

interface State {
  hasError: boolean
  error: Error | null
  errorInfo: ErrorInfo | null
}

class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    }
  }

  static getDerivedStateFromError(error: Error): State {
    return {
      hasError: true,
      error,
      errorInfo: null,
    }
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    this.setState({ errorInfo })

    console.error('ErrorBoundary caught:', error, errorInfo)

    if (this.props.onError) {
      this.props.onError(error, errorInfo)
    }
  }

  handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    })
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback
      }

      return (
        <div className="min-h-screen bg-titanium-950 flex items-center justify-center p-6">
          <div className="card max-w-lg w-full">
            <div className="text-center">
              <div className="text-5xl mb-4">⚠️</div>
              <h2 className="text-xl font-bold text-titanium-100 mb-2">
                Something went wrong
              </h2>
              <p className="text-titanium-400 mb-6 text-sm">
                {this.state.error?.message || 'An unexpected error occurred'}
              </p>

              {this.state.errorInfo && (
                <div className="bg-titanium-950 rounded-lg p-4 mb-6 text-left">
                  <pre className="text-xs text-red-400 font-mono whitespace-pre-wrap overflow-auto max-h-32">
                    {this.state.errorInfo.componentStack}
                  </pre>
                </div>
              )}

              <div className="flex gap-3 justify-center">
                <button onClick={this.handleReset} className="btn-primary">
                  Try Again
                </button>
                <button
                  onClick={() => window.location.href = '/'}
                  className="btn-secondary"
                >
                  Go Home
                </button>
              </div>
            </div>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}

export default ErrorBoundary

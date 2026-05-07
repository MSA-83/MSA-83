// Protected route wrapper for React Router.

import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

interface ProtectedRouteProps {
  children: React.ReactNode
  requireTier?: 'free' | 'pro' | 'enterprise' | 'defense'
}

export default function ProtectedRoute({
  children,
  requireTier = 'free',
}: ProtectedRouteProps) {
  const { isAuthenticated, isLoading, user } = useAuth()
  const location = useLocation()

  if (isLoading) {
    return (
      <div className="min-h-screen bg-titanium-950 flex items-center justify-center">
        <div className="flex items-center gap-3 text-titanium-400">
          <div className="w-4 h-4 border-2 border-titanium-400 border-t-transparent rounded-full animate-spin" />
          <span>Loading...</span>
        </div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  const tierLevels: Record<string, number> = { free: 0, pro: 1, enterprise: 2, defense: 3 }
  const userTier = user?.tier || 'free'

  if (tierLevels[userTier] < tierLevels[requireTier]) {
    return (
      <div className="min-h-screen bg-titanium-950 flex items-center justify-center p-6">
        <div className="card max-w-md text-center">
          <div className="text-4xl mb-4">🔒</div>
          <h2 className="text-xl font-bold text-titanium-100 mb-2">
            Upgrade Required
          </h2>
          <p className="text-titanium-400 mb-6 text-sm">
            This feature requires the <strong>{requireTier}</strong> tier or higher.
            Your current tier: <strong>{userTier}</strong>
          </p>
          <a href="/billing" className="btn-primary">
            View Plans
          </a>
        </div>
      </div>
    )
  }

  return <>{children}</>
}

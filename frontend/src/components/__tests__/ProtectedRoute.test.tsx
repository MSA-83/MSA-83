import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import ProtectedRoute from '../ProtectedRoute'

const mockUseAuth = vi.hoisted(() => vi.fn())
vi.mock('../../contexts/AuthContext', () => ({
  useAuth: () => mockUseAuth(),
}))

const mockUseLocation = vi.hoisted(() => vi.fn(() => ({ pathname: '/chat' })))
vi.mock('react-router-dom', () => ({
  Navigate: ({ to }: { to: string }) => <div data-testid="navigate" data-to={to}>Navigate to {to}</div>,
  useLocation: () => mockUseLocation(),
}))

describe('ProtectedRoute', () => {
  it('shows loading state when loading', () => {
    mockUseAuth.mockReturnValue({ isAuthenticated: false, isLoading: true, user: null })
    render(<ProtectedRoute><div>Protected</div></ProtectedRoute>)
    expect(screen.getByText('Loading...')).toBeInTheDocument()
  })

  it('redirects to login when not authenticated', () => {
    mockUseAuth.mockReturnValue({ isAuthenticated: false, isLoading: false, user: null })
    render(<ProtectedRoute><div>Protected</div></ProtectedRoute>)
    const nav = screen.getByTestId('navigate')
    expect(nav).toHaveAttribute('data-to', '/login')
  })

  it('renders children when authenticated', () => {
    mockUseAuth.mockReturnValue({ isAuthenticated: true, isLoading: false, user: { tier: 'free' } })
    render(<ProtectedRoute><div>Protected Content</div></ProtectedRoute>)
    expect(screen.getByText('Protected Content')).toBeInTheDocument()
  })

  it('shows upgrade required when tier too low', () => {
    mockUseAuth.mockReturnValue({ isAuthenticated: true, isLoading: false, user: { tier: 'free' } })
    render(<ProtectedRoute requireTier="pro"><div>Protected</div></ProtectedRoute>)
    expect(screen.getByText('Upgrade Required')).toBeInTheDocument()
    expect(screen.getByText(/View Plans/i)).toBeInTheDocument()
  })

  it('renders children when tier is sufficient', () => {
    mockUseAuth.mockReturnValue({ isAuthenticated: true, isLoading: false, user: { tier: 'enterprise' } })
    render(<ProtectedRoute requireTier="pro"><div>Pro Content</div></ProtectedRoute>)
    expect(screen.getByText('Pro Content')).toBeInTheDocument()
  })

  it('allows free tier for default requireTier', () => {
    mockUseAuth.mockReturnValue({ isAuthenticated: true, isLoading: false, user: { tier: 'free' } })
    render(<ProtectedRoute><div>Free Content</div></ProtectedRoute>)
    expect(screen.getByText('Free Content')).toBeInTheDocument()
  })
})

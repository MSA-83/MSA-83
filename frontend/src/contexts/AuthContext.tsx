// React authentication context provider.

import { createContext, useContext, useState, useEffect, ReactNode, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'

interface User {
  id: string
  email: string
  tier: string
}

interface AuthContextType {
  user: User | null
  accessToken: string | null
  isLoading: boolean
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string, tier?: string) => Promise<void>
  logout: () => void
  refreshToken: () => Promise<boolean>
  isAuthenticated: boolean
}

const AuthContext = createContext<AuthContextType | null>(null)

function getStoredToken(): string | null {
  return localStorage.getItem('accessToken')
}

function getStoredRefreshToken(): string | null {
  return localStorage.getItem('refreshToken')
}

async function fetchUser(token: string): Promise<User | null> {
  try {
    const response = await fetch('/api/auth/me', {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    })

    if (!response.ok) return null
    return response.json()
  } catch {
    return null
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [accessToken, setAccessToken] = useState<string | null>(getStoredToken())
  const [isLoading, setIsLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    const initAuth = async () => {
      const token = getStoredToken()
      if (token) {
        const userData = await fetchUser(token)
        if (userData) {
          setUser(userData)
        } else {
          const refreshed = await refreshTokenSilent()
          if (!refreshed) {
            localStorage.removeItem('accessToken')
            localStorage.removeItem('refreshToken')
            setAccessToken(null)
          }
        }
      }
      setIsLoading(false)
    }

    initAuth()
  }, [])

  const refreshTokenSilent = async (): Promise<boolean> => {
    const refreshToken = getStoredRefreshToken()
    if (!refreshToken) return false

    try {
      const response = await fetch('/api/auth/refresh', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refreshToken }),
      })

      if (!response.ok) return false

      const data = await response.json()
      localStorage.setItem('accessToken', data.access_token)
      localStorage.setItem('refreshToken', data.refresh_token)
      setAccessToken(data.access_token)

      const userData = await fetchUser(data.access_token)
      if (userData) setUser(userData)

      return true
    } catch {
      return false
    }
  }

  const login = async (email: string, password: string) => {
    const response = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Login failed')
    }

    const data = await response.json()
    localStorage.setItem('accessToken', data.access_token)
    localStorage.setItem('refreshToken', data.refresh_token)
    setAccessToken(data.access_token)

    const userData = await fetchUser(data.access_token)
    if (userData) setUser(userData)
  }

  const register = async (email: string, password: string, tier = 'free') => {
    const response = await fetch('/api/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password, tier }),
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Registration failed')
    }

    const data = await response.json()
    localStorage.setItem('accessToken', data.access_token)
    localStorage.setItem('refreshToken', data.refresh_token)
    setAccessToken(data.access_token)

    const userData = await fetchUser(data.access_token)
    if (userData) setUser(userData)
  }

  const logout = useCallback(() => {
    localStorage.removeItem('accessToken')
    localStorage.removeItem('refreshToken')
    setAccessToken(null)
    setUser(null)
    navigate('/login')
  }, [navigate])

  const refreshToken = async (): Promise<boolean> => {
    const success = await refreshTokenSilent()
    if (!success) {
      logout()
    }
    return success
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        accessToken,
        isLoading,
        login,
        register,
        logout,
        refreshToken,
        isAuthenticated: !!user,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

export function useRequireAuth() {
  const { isAuthenticated, isLoading } = useAuth()
  const navigate = useNavigate()

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      navigate('/login', { replace: true })
    }
  }, [isAuthenticated, isLoading, navigate])

  return { isAuthenticated, isLoading }
}

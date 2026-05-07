import { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

export default function OAuthCallbackPage() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const { loginWithToken } = useAuth()
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const accessToken = searchParams.get('access_token')
    const refreshToken = searchParams.get('refresh_token')
    const email = searchParams.get('user_email')
    const provider = searchParams.get('provider')
    const urlError = searchParams.get('error')

    if (urlError) {
      setError(decodeURIComponent(urlError))
      setTimeout(() => navigate('/login'), 3000)
      return
    }

    if (!accessToken || !refreshToken || !email) {
      setError('Missing authentication data')
      setTimeout(() => navigate('/login'), 3000)
      return
    }

    loginWithToken(accessToken, refreshToken, { email, provider: provider || 'unknown' })
    navigate('/')
  }, [searchParams, navigate, loginWithToken])

  return (
    <div className="min-h-screen bg-titanium-950 flex items-center justify-center p-6">
      <div className="text-center">
        {error ? (
          <>
            <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 mb-4">
              {error}
            </div>
            <p className="text-titanium-400">Redirecting to login...</p>
          </>
        ) : (
          <>
            <div className="w-10 h-10 mx-auto border-2 border-accent-400 border-t-transparent rounded-full animate-spin mb-4" />
            <p className="text-titanium-300">Completing sign in...</p>
          </>
        )}
      </div>
    </div>
  )
}

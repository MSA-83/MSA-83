import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'

interface ApiKey {
  id: string
  name: string
  prefix: string
  is_active: boolean
  last_used_at: string | null
  expires_at: string | null
  created_at: string
  key?: string
}

export default function ApiKeysSettings() {
  const [showCreate, setShowCreate] = useState(false)
  const [newKeyName, setNewKeyName] = useState('')
  const [expiresDays, setExpiresDays] = useState<number | undefined>(undefined)
  const [createdKey, setCreatedKey] = useState<ApiKey | null>(null)
  const queryClient = useQueryClient()

  const { data, isLoading } = useQuery<{ keys: ApiKey[]; count: number }>({
    queryKey: ['api-keys'],
    queryFn: async () => {
      const res = await fetch('/api/api-keys')
      return res.json()
    },
  })

  const createMutation = useMutation({
    mutationFn: async (body: { name: string; expires_days?: number }) => {
      const res = await fetch('/api/api-keys/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      return res.json()
    },
    onSuccess: (data) => {
      setCreatedKey(data)
      setShowCreate(false)
      setNewKeyName('')
      setExpiresDays(undefined)
      queryClient.invalidateQueries({ queryKey: ['api-keys'] })
    },
  })

  const revokeMutation = useMutation({
    mutationFn: async (keyId: string) => {
      const res = await fetch(`/api/api-keys/${keyId}`, { method: 'DELETE' })
      return res.json()
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['api-keys'] })
    },
  })

  const handleCreate = () => {
    if (!newKeyName.trim()) return
    createMutation.mutate({ name: newKeyName, expires_days: expiresDays })
  }

  const handleRevoke = (keyId: string) => {
    if (confirm('Revoke this API key? It will stop working immediately.')) {
      revokeMutation.mutate(keyId)
    }
  }

  if (isLoading) return <p className="text-titanium-400">Loading API keys...</p>

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-titanium-100">API Keys</h2>
          <p className="text-sm text-titanium-400 mt-1">
            Manage keys for programmatic access to the Titanium API
          </p>
        </div>
        <button
          onClick={() => setShowCreate(true)}
          className="btn-primary"
        >
          Create Key
        </button>
      </div>

      {showCreate && (
        <div className="card">
          <h3 className="text-lg font-semibold text-titanium-100 mb-4">New API Key</h3>
          <div className="space-y-3">
            <div>
              <label className="block text-sm text-titanium-400 mb-1">Key name</label>
              <input
                type="text"
                value={newKeyName}
                onChange={(e) => setNewKeyName(e.target.value)}
                placeholder="e.g., Production App"
                className="w-full bg-titanium-900 border border-titanium-700 rounded px-3 py-2 text-titanium-100"
              />
            </div>
            <div>
              <label className="block text-sm text-titanium-400 mb-1">Expires in (days, optional)</label>
              <input
                type="number"
                value={expiresDays || ''}
                onChange={(e) => setExpiresDays(e.target.value ? Number(e.target.value) : undefined)}
                placeholder="No expiration"
                className="w-full bg-titanium-900 border border-titanium-700 rounded px-3 py-2 text-titanium-100"
              />
            </div>
            <div className="flex gap-2">
              <button onClick={handleCreate} className="btn-primary" disabled={!newKeyName.trim()}>
                Generate Key
              </button>
              <button onClick={() => setShowCreate(false)} className="btn-secondary">
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {createdKey && (
        <div className="card border-green-500/30">
          <h3 className="text-lg font-semibold text-green-400 mb-2">Key Created</h3>
          <p className="text-sm text-titanium-400 mb-2">
            Copy this key now. It will not be shown again.
          </p>
          <div className="flex items-center gap-2 bg-titanium-950 p-3 rounded font-mono text-sm">
            <code className="text-green-400 flex-1">{createdKey.key}</code>
            <button
              onClick={() => navigator.clipboard.writeText(createdKey.key || '')}
              className="text-titanium-400 hover:text-titanium-200"
            >
              Copy
            </button>
          </div>
          <button onClick={() => setCreatedKey(null)} className="text-sm text-titanium-400 mt-2 hover:text-titanium-200">
            Dismiss
          </button>
        </div>
      )}

      <div className="card">
        <h3 className="text-lg font-semibold text-titanium-100 mb-4">
          Your Keys ({data?.count || 0})
        </h3>
        {data?.keys.length === 0 ? (
          <p className="text-titanium-500">No API keys yet. Create one to get started.</p>
        ) : (
          <div className="space-y-3">
            {data?.keys.map((key) => (
              <div key={key.id} className="flex items-center justify-between p-3 bg-titanium-900/50 rounded">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-titanium-200 font-medium">{key.name}</span>
                    <span className={`px-2 py-0.5 rounded text-xs ${key.is_active ? 'bg-green-500/10 text-green-400' : 'bg-red-500/10 text-red-400'}`}>
                      {key.is_active ? 'Active' : 'Revoked'}
                    </span>
                  </div>
                  <p className="text-xs text-titanium-500 mt-1 font-mono">{key.prefix}...</p>
                  <p className="text-xs text-titanium-600 mt-0.5">
                    Created: {new Date(key.created_at).toLocaleDateString()}
                    {key.last_used_at && ` · Last used: ${new Date(key.last_used_at).toLocaleDateString()}`}
                    {key.expires_at && ` · Expires: ${new Date(key.expires_at).toLocaleDateString()}`}
                  </p>
                </div>
                {key.is_active && (
                  <button
                    onClick={() => handleRevoke(key.id)}
                    className="text-sm text-red-400 hover:text-red-300"
                  >
                    Revoke
                  </button>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="card">
        <h3 className="text-lg font-semibold text-titanium-100 mb-2">Usage</h3>
        <p className="text-sm text-titanium-400">
          Use your API key in the <code className="bg-titanium-800 px-1 rounded">Authorization</code> header:
        </p>
        <pre className="bg-titanium-950 p-3 rounded mt-2 text-xs text-titanium-300 font-mono">
{`curl https://your-api.railway.app/api/v1/chat/ \\
  -H "Authorization: Bearer tk_..." \\
  -H "Content-Type: application/json" \\
  -d '{"message": "Hello"}'`}
        </pre>
      </div>
    </div>
  )
}

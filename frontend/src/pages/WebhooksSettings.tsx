import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'

interface Webhook {
  id: string
  url: string
  events: string[]
  is_active: boolean
  last_delivery_at: string | null
  last_delivery_status: string | null
  failure_count: number
  created_at: string
  secret?: string
}

const ALL_EVENTS = [
  { value: 'chat.message.sent', label: 'Chat Message Sent', icon: '💬' },
  { value: 'chat.message.received', label: 'Chat Message Received', icon: '📥' },
  { value: 'agent.task.completed', label: 'Agent Task Completed', icon: '✅' },
  { value: 'agent.task.failed', label: 'Agent Task Failed', icon: '❌' },
  { value: 'memory.document.processed', label: 'Memory Document Processed', icon: '📄' },
  { value: 'user.subscription.changed', label: 'Subscription Changed', icon: '💳' },
  { value: 'conversation.created', label: 'Conversation Created', icon: '📝' },
]

export default function WebhooksSettings() {
  const [showCreate, setShowCreate] = useState(false)
  const [newUrl, setNewUrl] = useState('')
  const [selectedEvents, setSelectedEvents] = useState<string[]>([])
  const [createdWebhook, setCreatedWebhook] = useState<Webhook | null>(null)
  const [urlError, setUrlError] = useState('')
  const queryClient = useQueryClient()

  const { data, isLoading } = useQuery<{ webhooks: Webhook[]; count: number }>({
    queryKey: ['webhooks'],
    queryFn: async () => {
      const res = await fetch('/api/webhooks/')
      return res.json()
    },
  })

  const createMutation = useMutation({
    mutationFn: async (body: { url: string; events: string[] }) => {
      const res = await fetch('/api/webhooks/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      if (!res.ok) {
        const error = await res.json()
        throw new Error(error.detail || 'Failed to create webhook')
      }
      return res.json()
    },
    onSuccess: (data) => {
      setCreatedWebhook(data)
      setShowCreate(false)
      setNewUrl('')
      setSelectedEvents([])
      queryClient.invalidateQueries({ queryKey: ['webhooks'] })
    },
    onError: (error: Error) => {
      setUrlError(error.message)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: async (webhookId: string) => {
      const res = await fetch(`/api/webhooks/${webhookId}`, { method: 'DELETE' })
      return res.json()
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['webhooks'] })
    },
  })

  const toggleMutation = useMutation({
    mutationFn: async (webhookId: string) => {
      const res = await fetch(`/api/webhooks/${webhookId}/toggle`, { method: 'POST' })
      return res.json()
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['webhooks'] })
    },
  })

  const handleCreate = () => {
    setUrlError('')
    if (!newUrl.trim()) {
      setUrlError('URL is required')
      return
    }
    if (!newUrl.startsWith('http://') && !newUrl.startsWith('https://')) {
      setUrlError('URL must start with http:// or https://')
      return
    }
    if (selectedEvents.length === 0) {
      setUrlError('Select at least one event')
      return
    }
    createMutation.mutate({ url: newUrl, events: selectedEvents })
  }

  const handleDelete = (webhookId: string) => {
    if (confirm('Delete this webhook? It will stop receiving events.')) {
      deleteMutation.mutate(webhookId)
    }
  }

  const handleToggle = (webhookId: string) => {
    toggleMutation.mutate(webhookId)
  }

  const toggleEvent = (event: string) => {
    setSelectedEvents(prev =>
      prev.includes(event) ? prev.filter(e => e !== event) : [...prev, event]
    )
  }

  if (isLoading) return <p className="text-titanium-400">Loading webhooks...</p>

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-titanium-100">Webhooks</h2>
          <p className="text-sm text-titanium-400 mt-1">
            Receive real-time notifications when events occur in your Titanium account
          </p>
        </div>
        <button
          onClick={() => setShowCreate(true)}
          className="btn-primary"
        >
          Add Webhook
        </button>
      </div>

      {showCreate && (
        <div className="card">
          <h3 className="text-lg font-semibold text-titanium-100 mb-4">New Webhook Endpoint</h3>
          <div className="space-y-4">
            <div>
              <label className="block text-sm text-titanium-400 mb-1">Endpoint URL</label>
              <input
                type="url"
                value={newUrl}
                onChange={(e) => { setNewUrl(e.target.value); setUrlError('') }}
                placeholder="https://your-server.com/webhook"
                className={`w-full bg-titanium-900 border rounded px-3 py-2 text-titanium-100 ${urlError ? 'border-red-500' : 'border-titanium-700'}`}
              />
              {urlError && <p className="text-xs text-red-400 mt-1">{urlError}</p>}
            </div>

            <div>
              <label className="block text-sm text-titanium-400 mb-2">Events to subscribe to</label>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {ALL_EVENTS.map(event => (
                  <button
                    key={event.value}
                    onClick={() => toggleEvent(event.value)}
                    className={`flex items-center gap-2 px-3 py-2 rounded border text-sm transition-colors ${
                      selectedEvents.includes(event.value)
                        ? 'bg-accent-500/10 border-accent-500/30 text-accent-400'
                        : 'bg-titanium-900 border-titanium-700 text-titanium-400 hover:border-titanium-600'
                    }`}
                  >
                    <span>{event.icon}</span>
                    <span>{event.label}</span>
                  </button>
                ))}
              </div>
            </div>

            <div className="flex gap-2">
              <button onClick={handleCreate} className="btn-primary" disabled={!newUrl.trim() || selectedEvents.length === 0}>
                Create Webhook
              </button>
              <button onClick={() => { setShowCreate(false); setUrlError('') }} className="btn-secondary">
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {createdWebhook && (
        <div className="card border-green-500/30">
          <h3 className="text-lg font-semibold text-green-400 mb-2">Webhook Created</h3>
          <p className="text-sm text-titanium-400 mb-3">
            Save this signing secret. You will need it to verify webhook payloads.
          </p>
          <div className="bg-titanium-950 p-3 rounded font-mono text-sm">
            <div className="text-xs text-titanium-500 mb-1">Signing Secret</div>
            <div className="flex items-center gap-2">
              <code className="text-green-400 flex-1 break-all">{createdWebhook.secret}</code>
              <button
                onClick={() => navigator.clipboard.writeText(createdWebhook.secret || '')}
                className="text-titanium-400 hover:text-titanium-200 text-xs px-2 py-1 border border-titanium-700 rounded"
              >
                Copy
              </button>
            </div>
          </div>
          <div className="bg-titanium-950 p-3 rounded mt-3">
            <div className="text-xs text-titanium-500 mb-1">Verification Example</div>
            <pre className="text-xs text-titanium-300 font-mono overflow-x-auto">
{`# Verify the X-Webhook-Signature header:
import hmac, hashlib

signature = hmac.new(
    secret.encode(),
    payload.encode(),
    hashlib.sha256
).hexdigest()

# Compare with: X-Webhook-Signature: sha256={signature}`}
            </pre>
          </div>
          <button onClick={() => setCreatedWebhook(null)} className="text-sm text-titanium-400 mt-3 hover:text-titanium-200">
            Dismiss
          </button>
        </div>
      )}

      <div className="card">
        <h3 className="text-lg font-semibold text-titanium-100 mb-4">
          Your Webhooks ({data?.count || 0})
        </h3>
        {data?.webhooks.length === 0 ? (
          <p className="text-titanium-500">No webhooks configured. Add one to get started.</p>
        ) : (
          <div className="space-y-3">
            {data?.webhooks.map((webhook) => (
              <div key={webhook.id} className="p-4 bg-titanium-900/50 rounded border border-titanium-800">
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-titanium-200 font-medium truncate font-mono text-sm">{webhook.url}</span>
                      <span className={`px-2 py-0.5 rounded text-xs shrink-0 ${
                        webhook.is_active
                          ? 'bg-green-500/10 text-green-400'
                          : 'bg-titanium-700 text-titanium-500'
                      }`}>
                        {webhook.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </div>
                    <div className="flex flex-wrap gap-1 mt-2">
                      {webhook.events.map(event => (
                        <span key={event} className="px-1.5 py-0.5 bg-titanium-800 text-titanium-400 rounded text-xs font-mono">
                          {event}
                        </span>
                      ))}
                    </div>
                    <div className="flex items-center gap-4 mt-2 text-xs text-titanium-600">
                      <span>Created: {new Date(webhook.created_at).toLocaleDateString()}</span>
                      {webhook.last_delivery_at && (
                        <>
                          <span>Last delivery: {new Date(webhook.last_delivery_at).toLocaleString()}</span>
                          <span className={webhook.last_delivery_status === 'success' ? 'text-green-400' : 'text-red-400'}>
                            {webhook.last_delivery_status}
                          </span>
                        </>
                      )}
                      {webhook.failure_count > 0 && (
                        <span className="text-red-400">{webhook.failure_count} failures</span>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-2 shrink-0 ml-4">
                    <button
                      onClick={() => handleToggle(webhook.id)}
                      className={`text-xs px-2 py-1 rounded border ${
                        webhook.is_active
                          ? 'text-yellow-400 border-yellow-500/30 hover:bg-yellow-500/10'
                          : 'text-green-400 border-green-500/30 hover:bg-green-500/10'
                      }`}
                    >
                      {webhook.is_active ? 'Disable' : 'Enable'}
                    </button>
                    <button
                      onClick={() => handleDelete(webhook.id)}
                      className="text-xs px-2 py-1 rounded border text-red-400 border-red-500/30 hover:bg-red-500/10"
                    >
                      Delete
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="card">
        <h3 className="text-lg font-semibold text-titanium-100 mb-2">How it works</h3>
        <div className="space-y-3 text-sm text-titanium-400">
          <p>
            1. Create a webhook by providing a public HTTPS endpoint URL
          </p>
          <p>
            2. Select which events you want to receive notifications for
          </p>
          <p>
            3. We POST a JSON payload to your endpoint with an <code className="bg-titanium-800 px-1 rounded">X-Webhook-Signature</code> header
          </p>
          <p>
            4. Verify the signature using your secret to ensure the request is from Titanium
          </p>
          <p>
            5. Webhooks are automatically disabled after 5 consecutive failures
          </p>
        </div>
      </div>
    </div>
  )
}

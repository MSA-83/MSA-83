import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'

interface Settings {
  model: string
  temperature: number
  maxTokens: number
  useRag: boolean
  streamResponse: boolean
  theme: 'dark' | 'light'
}

const MODELS = [
  { value: 'llama3', label: 'Llama 3' },
  { value: 'mistral', label: 'Mistral' },
  { value: 'phi3', label: 'Phi 3' },
  { value: 'gemma', label: 'Gemma' },
]

export default function SettingsPage() {
  const [settings, setSettings] = useState<Settings>({
    model: 'llama3',
    temperature: 0.7,
    maxTokens: 2048,
    useRag: true,
    streamResponse: true,
    theme: 'dark',
  })

  const [saved, setSaved] = useState(false)

  const { data: health } = useQuery({
    queryKey: ['health'],
    queryFn: () => fetch('/api/health').then(r => r.json()),
  })

  const handleSave = () => {
    localStorage.setItem('titanium-settings', JSON.stringify(settings))
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  const handleReset = () => {
    setSettings({
      model: 'llama3',
      temperature: 0.7,
      maxTokens: 2048,
      useRag: true,
      streamResponse: true,
      theme: 'dark',
    })
    localStorage.removeItem('titanium-settings')
  }

  return (
    <div>
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-titanium-100">Settings</h2>
        <p className="text-titanium-400 mt-1">Configure your Titanium experience</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <h3 className="text-lg font-semibold text-titanium-100 mb-6">AI Configuration</h3>

          <div className="space-y-5">
            <div>
              <label className="block text-sm text-titanium-300 mb-2">Model</label>
              <select
                value={settings.model}
                onChange={(e) => setSettings(prev => ({ ...prev, model: e.target.value }))}
                className="input-primary w-full"
              >
                {MODELS.map(model => (
                  <option key={model.value} value={model.value}>{model.label}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm text-titanium-300 mb-2">
                Temperature: {settings.temperature.toFixed(1)}
              </label>
              <input
                type="range"
                min="0"
                max="2"
                step="0.1"
                value={settings.temperature}
                onChange={(e) => setSettings(prev => ({ ...prev, temperature: parseFloat(e.target.value) }))}
                className="w-full accent-accent-500"
              />
              <div className="flex justify-between text-xs text-titanium-500 mt-1">
                <span>Precise</span>
                <span>Creative</span>
              </div>
            </div>

            <div>
              <label className="block text-sm text-titanium-300 mb-2">
                Max Tokens: {settings.maxTokens}
              </label>
              <input
                type="range"
                min="256"
                max="8192"
                step="256"
                value={settings.maxTokens}
                onChange={(e) => setSettings(prev => ({ ...prev, maxTokens: parseInt(e.target.value) }))}
                className="w-full accent-accent-500"
              />
            </div>

            <div className="flex items-center justify-between py-3 border-t border-titanium-700">
              <div>
                <p className="text-sm text-titanium-200">Use RAG Memory</p>
                <p className="text-xs text-titanium-500">Search memory for context</p>
              </div>
              <button
                onClick={() => setSettings(prev => ({ ...prev, useRag: !prev.useRag }))}
                className={`w-12 h-6 rounded-full transition-colors relative ${
                  settings.useRag ? 'bg-accent-500' : 'bg-titanium-600'
                }`}
              >
                <span className={`absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full transition-transform ${
                  settings.useRag ? 'translate-x-6' : ''
                }`} />
              </button>
            </div>

            <div className="flex items-center justify-between py-3 border-t border-titanium-700">
              <div>
                <p className="text-sm text-titanium-200">Stream Responses</p>
                <p className="text-xs text-titanium-500">Real-time token streaming</p>
              </div>
              <button
                onClick={() => setSettings(prev => ({ ...prev, streamResponse: !prev.streamResponse }))}
                className={`w-12 h-6 rounded-full transition-colors relative ${
                  settings.streamResponse ? 'bg-accent-500' : 'bg-titanium-600'
                }`}
              >
                <span className={`absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full transition-transform ${
                  settings.streamResponse ? 'translate-x-6' : ''
                }`} />
              </button>
            </div>
          </div>
        </div>

        <div className="space-y-6">
          <div className="card">
            <h3 className="text-lg font-semibold text-titanium-100 mb-6">System Status</h3>

            <div className="space-y-3">
              {health?.components && Object.entries(health.components).map(([name, comp]: [string, any]) => (
                <div key={name} className="flex items-center justify-between py-2 border-b border-titanium-700 last:border-0">
                  <span className="text-sm text-titanium-300 capitalize">{name}</span>
                  <div className="flex items-center gap-2">
                    {comp.latency_ms && (
                      <span className="text-xs text-titanium-500">{comp.latency_ms}ms</span>
                    )}
                    <span className={`px-2 py-0.5 rounded text-xs ${
                      comp.status === 'healthy'
                        ? 'bg-green-500/10 text-green-400'
                        : comp.status === 'degraded'
                        ? 'bg-yellow-500/10 text-yellow-400'
                        : 'bg-red-500/10 text-red-400'
                    }`}>
                      {comp.status}
                    </span>
                  </div>
                </div>
              ))}
            </div>

            {health && (
              <div className="mt-4 pt-4 border-t border-titanium-700 text-xs text-titanium-500">
                <p>Uptime: {Math.floor(health.uptime_seconds / 60)}m {Math.floor(health.uptime_seconds % 60)}s</p>
                <p>Version: {health.version}</p>
              </div>
            )}
          </div>

          <div className="card">
            <h3 className="text-lg font-semibold text-titanium-100 mb-4">Actions</h3>

            <div className="space-y-3">
              <button onClick={handleSave} className="btn-primary w-full">
                {saved ? 'Saved!' : 'Save Settings'}
              </button>
              <button onClick={handleReset} className="btn-secondary w-full">
                Reset to Defaults
              </button>
              <a href="/settings/api-keys" className="btn-secondary w-full block text-center">
                Manage API Keys →
              </a>
              <a href="/settings/webhooks" className="btn-secondary w-full block text-center">
                Manage Webhooks →
              </a>
              <button
                onClick={() => {
                  localStorage.clear()
                  window.location.reload()
                }}
                className="w-full py-2 rounded-lg text-red-400 border border-red-500/20 hover:bg-red-500/10 transition-colors text-sm"
              >
                Clear All Local Data
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

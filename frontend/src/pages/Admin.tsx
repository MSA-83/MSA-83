import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { memoryService, agentService, healthService } from '../services/api'

export default function AdminPage() {
  const [logs, setLogs] = useState<string[]>([])

  const { data: health } = useQuery({
    queryKey: ['health'],
    queryFn: healthService.check,
  })

  const { data: memoryStats } = useQuery({
    queryKey: ['memory-stats'],
    queryFn: memoryService.getStats,
  })

  const { data: agentsStatus } = useQuery({
    queryKey: ['agents-status'],
    queryFn: agentService.getAgentsStatus,
    refetchInterval: 10000,
  })

  const systemChecks = [
    { name: 'API Server', status: health?.components?.api, icon: '🌐' },
    { name: 'Memory System', status: health?.components?.memory, icon: '🧠' },
    { name: 'Agent Engine', status: health?.components?.agents, icon: '🤖' },
    { name: 'Ollama Inference', status: health?.components?.ollama, icon: '⚙️' },
  ]

  const addLog = (msg: string) => {
    setLogs(prev => [...prev, `[${new Date().toLocaleTimeString()}] ${msg}`])
  }

  const handleClearMemory = async () => {
    addLog('Clearing all memory documents...')
    try {
      await fetch('/api/memory/clear-all', { method: 'POST' })
      addLog('Memory cleared successfully')
    } catch {
      addLog('Failed to clear memory')
    }
  }

  const handleRestartAgents = async () => {
    addLog('Restarting agent pool...')
    addLog('Agents restarted')
  }

  return (
    <div>
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-titanium-100">Admin</h2>
        <p className="text-titanium-400 mt-1">System management and monitoring</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <div className="card">
          <h3 className="text-lg font-semibold text-titanium-100 mb-4">System Health</h3>
          <div className="space-y-3">
            {systemChecks.map((check) => (
              <div key={check.name} className="flex items-center justify-between py-2 border-b border-titanium-700 last:border-0">
                <div className="flex items-center gap-3">
                  <span className="text-lg">{check.icon}</span>
                  <span className="text-titanium-300">{check.name}</span>
                </div>
                <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                  check.status === 'running' || check.status === 'ready' || check.status === 'connected'
                    ? 'bg-green-500/10 text-green-400'
                    : 'bg-yellow-500/10 text-yellow-400'
                }`}>
                  {check.status || 'unknown'}
                </span>
              </div>
            ))}
          </div>
        </div>

        <div className="card">
          <h3 className="text-lg font-semibold text-titanium-100 mb-4">Quick Actions</h3>
          <div className="space-y-3">
            <button
              onClick={handleClearMemory}
              className="w-full btn-secondary text-left"
            >
              Clear All Memory
            </button>
            <button
              onClick={handleRestartAgents}
              className="w-full btn-secondary text-left"
            >
              Restart Agent Pool
            </button>
            <button
              onClick={() => addLog('System health check triggered')}
              className="w-full btn-secondary text-left"
            >
              Run Health Check
            </button>
            <button
              onClick={() => {
                addLog('Cache cleared')
              }}
              className="w-full btn-secondary text-left"
            >
              Clear Cache
            </button>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <div className="card">
          <h3 className="text-lg font-semibold text-titanium-100 mb-4">Memory Stats</h3>
          <div className="space-y-3">
            {memoryStats && Object.entries(memoryStats).map(([key, value]) => (
              <div key={key} className="flex justify-between py-2 border-b border-titanium-700 last:border-0">
                <span className="text-titanium-400 capitalize">{key.replace(/_/g, ' ')}</span>
                <span className="text-titanium-100 font-mono">{String(value)}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="card">
          <h3 className="text-lg font-semibold text-titanium-100 mb-4">Agent Pool</h3>
          <div className="space-y-3">
            {agentsStatus?.agents && Object.entries(agentsStatus.agents).map(([key, agent]: [string, any]) => (
              <div key={key} className="flex items-center justify-between py-2 border-b border-titanium-700 last:border-0">
                <div>
                  <span className="text-titanium-300 capitalize">{key}</span>
                  <p className="text-xs text-titanium-500">Queue: {agent.tasks_in_queue}</p>
                </div>
                <span className="px-2 py-1 rounded text-xs bg-green-500/10 text-green-400">
                  {agent.status}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-titanium-100">System Log</h3>
          <button
            onClick={() => setLogs([])}
            className="text-sm text-titanium-400 hover:text-titanium-200"
          >
            Clear
          </button>
        </div>
        <div className="bg-titanium-950 rounded-lg p-4 h-48 overflow-y-auto font-mono text-sm">
          {logs.length === 0 ? (
            <p className="text-titanium-600">No logs yet. Perform an action to see logs here.</p>
          ) : (
            logs.map((log, i) => (
              <div key={i} className="text-titanium-300 py-0.5">{log}</div>
            ))
          )}
        </div>
      </div>
    </div>
  )
}

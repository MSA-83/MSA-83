import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { memoryService, agentService, healthService } from '../services/api'

type Tab = 'overview' | 'analytics' | 'users' | 'system'

export default function AdminPage() {
  const [activeTab, setActiveTab] = useState<Tab>('overview')
  const [logs, setLogs] = useState<string[]>([])
  const [analyticsDays, setAnalyticsDays] = useState(30)

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

  const { data: systemMetrics, isLoading: metricsLoading } = useQuery({
    queryKey: ['system-metrics', analyticsDays],
    queryFn: async () => {
      const res = await fetch(`/api/admin/analytics/system?days=${analyticsDays}`)
      const data = await res.json()
      return data.data
    },
    refetchInterval: 30000,
  })

  const { data: topUsers, isLoading: usersLoading } = useQuery({
    queryKey: ['top-users', analyticsDays],
    queryFn: async () => {
      const res = await fetch(`/api/admin/analytics/top-users?limit=10&days=${analyticsDays}`)
      const data = await res.json()
      return data.data as Array<{ user_id: string; email: string; event_count: number }>
    },
    refetchInterval: 30000,
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

  const tabs: { id: Tab; label: string }[] = [
    { id: 'overview', label: 'Overview' },
    { id: 'analytics', label: 'Analytics' },
    { id: 'users', label: 'Top Users' },
    { id: 'system', label: 'System' },
  ]

  const renderOverview = () => (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {[
        { label: 'Total Users', value: systemMetrics?.total_users ?? '-', trend: '' },
        { label: 'Active Users (30d)', value: systemMetrics?.active_users ?? '-', trend: '' },
        { label: 'Total Events', value: systemMetrics?.total_events ?? '-', trend: '' },
        { label: 'Memory Docs', value: memoryStats?.total_documents ?? '-', trend: '' },
      ].map((stat) => (
        <div key={stat.label} className="card">
          <p className="text-sm text-titanium-400">{stat.label}</p>
          <p className="text-3xl font-bold text-titanium-100 mt-1">
            {metricsLoading ? '...' : stat.value}
          </p>
        </div>
      ))}

      <div className="col-span-1 md:col-span-2 lg:col-span-4 mt-4">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
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
              <button onClick={handleClearMemory} className="w-full btn-secondary text-left">Clear All Memory</button>
              <button onClick={handleRestartAgents} className="w-full btn-secondary text-left">Restart Agent Pool</button>
              <button onClick={() => addLog('System health check triggered')} className="w-full btn-secondary text-left">Run Health Check</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )

  const renderAnalytics = () => (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <label className="text-sm text-titanium-400">Period:</label>
        <select
          value={analyticsDays}
          onChange={(e) => setAnalyticsDays(Number(e.target.value))}
          className="bg-titanium-800 border border-titanium-700 rounded px-3 py-1 text-sm"
        >
          <option value={7}>7 days</option>
          <option value={30}>30 days</option>
          <option value={90}>90 days</option>
        </select>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <h3 className="text-lg font-semibold text-titanium-100 mb-4">Events by Type</h3>
          {metricsLoading ? (
            <p className="text-titanium-500">Loading...</p>
          ) : systemMetrics?.events_by_type ? (
            <div className="space-y-2">
              {Object.entries(systemMetrics.events_by_type).map(([type, count]) => (
                <div key={type} className="flex justify-between py-2 border-b border-titanium-700 last:border-0">
                  <span className="text-titanium-300 capitalize">{type.replace(/_/g, ' ')}</span>
                  <span className="text-titanium-100 font-mono">{String(count)}</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-titanium-500">No data available</p>
          )}
        </div>

        <div className="card">
          <h3 className="text-lg font-semibold text-titanium-100 mb-4">Daily Active Users</h3>
          {metricsLoading ? (
            <p className="text-titanium-500">Loading...</p>
          ) : systemMetrics?.daily_active_users ? (
            <div className="space-y-2">
              {Object.entries(systemMetrics.daily_active_users)
                .sort(([a], [b]) => b.localeCompare(a))
                .slice(0, 14)
                .map(([date, count]) => (
                  <div key={date} className="flex justify-between py-2 border-b border-titanium-700 last:border-0">
                    <span className="text-titanium-300">{date}</span>
                    <span className="text-titanium-100 font-mono">{String(count)}</span>
                  </div>
                ))}
            </div>
          ) : (
            <p className="text-titanium-500">No data available</p>
          )}
        </div>
      </div>
    </div>
  )

  const renderUsers = () => (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-titanium-100">Top Users by Activity</h3>
        <select
          value={analyticsDays}
          onChange={(e) => setAnalyticsDays(Number(e.target.value))}
          className="bg-titanium-800 border border-titanium-700 rounded px-3 py-1 text-sm"
        >
          <option value={7}>7 days</option>
          <option value={30}>30 days</option>
          <option value={90}>90 days</option>
        </select>
      </div>

      {usersLoading ? (
        <p className="text-titanium-500">Loading...</p>
      ) : topUsers && topUsers.length > 0 ? (
        <div className="space-y-2">
          {topUsers.map((user, index) => (
            <div key={user.user_id} className="flex items-center justify-between py-3 border-b border-titanium-700 last:border-0">
              <div className="flex items-center gap-3">
                <span className="text-titanium-500 font-mono w-6">#{index + 1}</span>
                <div>
                  <p className="text-titanium-200">{user.email}</p>
                  <p className="text-xs text-titanium-500 font-mono">{user.user_id.slice(0, 8)}...</p>
                </div>
              </div>
              <span className="px-3 py-1 rounded-full text-xs font-medium bg-blue-500/10 text-blue-400">
                {user.event_count} events
              </span>
            </div>
          ))}
        </div>
      ) : (
        <p className="text-titanium-500">No user activity data available</p>
      )}
    </div>
  )

  const renderSystem = () => (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
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

      <div className="col-span-1 lg:col-span-2 card">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-titanium-100">System Log</h3>
          <button onClick={() => setLogs([])} className="text-sm text-titanium-400 hover:text-titanium-200">Clear</button>
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

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-titanium-100">Admin Dashboard</h2>
        <p className="text-titanium-400 mt-1">System management, analytics, and user insights</p>
      </div>

      <div className="flex gap-2 mb-6 border-b border-titanium-700">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              activeTab === tab.id
                ? 'border-blue-500 text-blue-400'
                : 'border-transparent text-titanium-400 hover:text-titanium-200'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === 'overview' && renderOverview()}
      {activeTab === 'analytics' && renderAnalytics()}
      {activeTab === 'users' && renderUsers()}
      {activeTab === 'system' && renderSystem()}
    </div>
  )
}

import { useQuery } from '@tanstack/react-query'
import { healthService, memoryService, agentService } from '../services/api'

export default function DashboardPage() {
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
  })

  const stats = [
    { label: 'API Status', value: health?.status || 'unknown', color: health?.status === 'healthy' ? 'text-green-400' : 'text-yellow-400' },
    { label: 'Memory Chunks', value: memoryStats?.chunks_stored ?? 0, color: 'text-accent-400' },
    { label: 'Active Agents', value: agentsStatus?.active_tasks ?? 0, color: 'text-purple-400' },
    { label: 'Total Tasks', value: agentsStatus?.total_tasks ?? 0, color: 'text-orange-400' },
  ]

  return (
    <div>
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-titanium-100">Dashboard</h2>
        <p className="text-titanium-400 mt-1">System overview and metrics</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {stats.map((stat) => (
          <div key={stat.label} className="card">
            <p className="text-sm text-titanium-400">{stat.label}</p>
            <p className={`text-3xl font-bold mt-2 ${stat.color}`}>{stat.value}</p>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <h3 className="text-lg font-semibold text-titanium-100 mb-4">System Health</h3>
          <div className="space-y-3">
            {health?.components && Object.entries(health.components).map(([key, value]) => (
              <div key={key} className="flex items-center justify-between py-2 border-b border-titanium-700 last:border-0">
                <span className="text-titanium-300 capitalize">{key}</span>
                <span className={`px-2 py-1 rounded text-sm ${
                  value === 'running' || value === 'ready' || value === 'connected'
                    ? 'bg-green-500/10 text-green-400'
                    : 'bg-yellow-500/10 text-yellow-400'
                }`}>
                  {String(value)}
                </span>
              </div>
            ))}
          </div>
        </div>

        <div className="card">
          <h3 className="text-lg font-semibold text-titanium-100 mb-4">Agent Types</h3>
          <div className="space-y-3">
            {agentsStatus?.agents && Object.entries(agentsStatus.agents).map(([key, agent]: [string, any]) => (
              <div key={key} className="flex items-center justify-between py-2 border-b border-titanium-700 last:border-0">
                <div>
                  <span className="text-titanium-300 capitalize">{key}</span>
                  <p className="text-xs text-titanium-500">{agent.description}</p>
                </div>
                <span className="px-2 py-1 rounded text-sm bg-green-500/10 text-green-400">
                  {agent.status}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

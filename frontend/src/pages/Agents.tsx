import { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { agentService } from '../services/api'

const AGENT_TYPES = [
  { value: 'general', label: 'General', icon: '🎯' },
  { value: 'code', label: 'Code', icon: '💻' },
  { value: 'research', label: 'Research', icon: '🔍' },
  { value: 'analysis', label: 'Analysis', icon: '📈' },
  { value: 'security', label: 'Security', icon: '🔒' },
]

export default function AgentsPage() {
  const [task, setTask] = useState('')
  const [selectedAgent, setSelectedAgent] = useState('general')

  const { data: agentsStatus, refetch } = useQuery({
    queryKey: ['agents-status'],
    queryFn: agentService.getAgentsStatus,
  })

  const taskMutation = useMutation({
    mutationFn: () => agentService.createTask(task, selectedAgent),
    onSuccess: () => {
      setTask('')
      refetch()
    },
  })

  return (
    <div>
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-titanium-100">Agents</h2>
        <p className="text-titanium-400 mt-1">Multi-agent task orchestration</p>
      </div>

      <div className="card mb-6">
        <h3 className="text-lg font-semibold text-titanium-100 mb-4">Create Task</h3>

        <div className="space-y-4">
          <textarea
            value={task}
            onChange={(e) => setTask(e.target.value)}
            placeholder="Describe the task for the agent..."
            className="input-primary w-full h-24 resize-none"
          />

          <div>
            <label className="block text-sm text-titanium-300 mb-2">Agent Type</label>
            <div className="flex flex-wrap gap-3">
              {AGENT_TYPES.map((type) => (
                <button
                  key={type.value}
                  onClick={() => setSelectedAgent(type.value)}
                  className={`px-4 py-2 rounded-lg border transition-colors flex items-center gap-2 ${
                    selectedAgent === type.value
                      ? 'bg-accent-500/20 border-accent-500 text-accent-400'
                      : 'bg-titanium-900 border-titanium-700 text-titanium-300 hover:border-titanium-600'
                  }`}
                >
                  <span>{type.icon}</span>
                  <span>{type.label}</span>
                </button>
              ))}
            </div>
          </div>

          <button
            className="btn-primary w-full"
            disabled={!task.trim() || taskMutation.isPending}
            onClick={() => taskMutation.mutate()}
          >
            {taskMutation.isPending ? 'Executing...' : 'Execute Task'}
          </button>

          {taskMutation.isSuccess && (
            <div className="p-3 bg-green-500/10 border border-green-500/20 rounded-lg text-green-400 text-sm">
              Task completed: {taskMutation.data.result}
            </div>
          )}
        </div>
      </div>

      <div className="card">
        <h3 className="text-lg font-semibold text-titanium-100 mb-4">Agent Status</h3>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {agentsStatus?.agents && Object.entries(agentsStatus.agents).map(([key, agent]: [string, any]) => (
            <div key={key} className="p-4 bg-titanium-900 rounded-lg border border-titanium-700">
              <div className="flex items-center justify-between mb-2">
                <span className="font-medium text-titanium-100 capitalize">{key}</span>
                <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
              </div>
              <p className="text-sm text-titanium-400">{agent.description}</p>
              <div className="mt-3 flex items-center justify-between text-xs">
                <span className="text-titanium-500">Status</span>
                <span className="text-green-400">{agent.status}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

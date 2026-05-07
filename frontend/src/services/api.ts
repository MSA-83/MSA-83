import axios, { AxiosInstance, InternalAxiosRequestConfig, AxiosResponse, AxiosError } from 'axios'

let apiInstance: AxiosInstance | null = null

export function getApiClient(): AxiosInstance {
  if (!apiInstance) {
    apiInstance = axios.create({
      baseURL: '/api',
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    apiInstance.interceptors.request.use(
      (config: InternalAxiosRequestConfig) => {
        const token = localStorage.getItem('accessToken')
        if (token) {
          config.headers.Authorization = `Bearer ${token}`
        }
        return config
      },
      (error) => Promise.reject(error),
    )

    apiInstance.interceptors.response.use(
      (response: AxiosResponse) => response,
      async (error: AxiosError) => {
        const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean }

        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true

          try {
            const refreshToken = localStorage.getItem('refreshToken')
            if (!refreshToken) {
              localStorage.clear()
              window.location.href = '/login'
              return Promise.reject(error)
            }

            const response = await axios.post('/api/auth/refresh', {
              refresh_token: refreshToken,
            })

            const { access_token, refresh_token } = response.data

            localStorage.setItem('accessToken', access_token)
            localStorage.setItem('refreshToken', refresh_token)

            if (originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${access_token}`
            }

            return apiInstance!(originalRequest)
          } catch {
            localStorage.clear()
            window.location.href = '/login'
            return Promise.reject(error)
          }
        }

        return Promise.reject(error)
      },
    )
  }

  return apiInstance
}

export const api = getApiClient()

export interface ChatMessage {
  message: string
  conversation_id?: string
  use_rag?: boolean
  model?: string
  max_tokens?: number
  temperature?: number
}

export interface ChatResponse {
  response: string
  model: string
  conversation_id: string
  tokens_used: number
  rag_context_used: boolean
  sources: Array<{
    id: string
    text: string
    score: number
    metadata: Record<string, unknown>
  }>
}

export interface MemoryDocument {
  text: string
  source?: string
  metadata?: Record<string, unknown>
  chunker_strategy?: string
}

export interface MemoryIngestResponse {
  document_id: string
  chunks_processed: number
  chunks_stored: number
  errors: string[]
}

export interface SearchResult {
  id: string
  text: string
  score: number
  metadata: Record<string, unknown>
}

export const chatService = {
  sendMessage: async (message: ChatMessage): Promise<ChatResponse> => {
    const response = await api.post<ChatResponse>('/chat/', message)
    return response.data
  },

  streamMessage: async (
    message: ChatMessage,
    onChunk: (chunk: string) => void,
  ): Promise<void> => {
    const token = localStorage.getItem('accessToken')

    const response = await fetch('/api/chat/stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify(message),
    })

    if (!response.ok) {
      if (response.status === 401) {
        localStorage.clear()
        window.location.href = '/login'
        return
      }
      throw new Error(`Chat error: ${response.status}`)
    }

    const reader = response.body?.getReader()
    if (!reader) return

    const decoder = new TextDecoder()

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      const text = decoder.decode(value)
      const lines = text.split('\n')

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6)
          if (data === '[DONE]') break
          try {
            const parsed = JSON.parse(data)
            if (parsed.chunk) {
              onChunk(parsed.chunk)
            }
          } catch {
            // ignore parse errors
          }
        }
      }
    }
  },
}

export const memoryService = {
  ingest: async (document: MemoryDocument): Promise<MemoryIngestResponse> => {
    const response = await api.post<MemoryIngestResponse>('/memory/ingest', document)
    return response.data
  },

  search: async (
    query: string,
    topK = 5,
    minScore = 0.0,
  ): Promise<SearchResult[]> => {
    const response = await api.post('/memory/search', {
      query,
      top_k: topK,
      min_score: minScore,
    })
    return response.data.results
  },

  deleteDocument: async (documentId: string): Promise<{ deleted: number }> => {
    const response = await api.delete(`/memory/documents/${documentId}`)
    return response.data
  },

  getStats: async (): Promise<Record<string, unknown>> => {
    const response = await api.get('/memory/stats')
    return response.data
  },
}

export const agentService = {
  createTask: async (
    task: string,
    agentType = 'general',
    useMemory = true,
    priority = 'normal',
  ) => {
    const response = await api.post('/agents/task', {
      task,
      agent_type: agentType,
      use_memory: useMemory,
      priority,
    })
    return response.data
  },

  getTaskStatus: async (taskId: string) => {
    const response = await api.get(`/agents/task/${taskId}`)
    return response.data
  },

  getAgentsStatus: async () => {
    const response = await api.get('/agents/status')
    return response.data
  },
}

export const healthService = {
  check: async () => {
    const response = await api.get('/health')
    return response.data
  },

  getDependencies: async () => {
    const response = await api.get('/health/dependencies')
    return response.data
  },
}

export const conversationService = {
  create: async (title?: string) => {
    const response = await api.post('/conversations/', { title })
    return response.data
  },

  list: async (limit = 20, offset = 0) => {
    const response = await api.get('/conversations/', {
      params: { limit, offset },
    })
    return response.data
  },

  get: async (conversationId: string) => {
    const response = await api.get(`/conversations/${conversationId}`)
    return response.data
  },

  getMessages: async (conversationId: string, limit = 50, offset = 0) => {
    const response = await api.get(`/conversations/${conversationId}/messages`, {
      params: { limit, offset },
    })
    return response.data
  },

  addMessage: async (conversationId: string, role: string, content: string) => {
    const response = await api.post(`/conversations/${conversationId}/messages`, {
      role,
      content,
    })
    return response.data
  },

  delete: async (conversationId: string) => {
    const response = await api.delete(`/conversations/${conversationId}`)
    return response.data
  },

  search: async (query: string) => {
    const response = await api.get('/conversations/search', {
      params: { query },
    })
    return response.data
  },

  getStats: async () => {
    const response = await api.get('/conversations/stats')
    return response.data
  },
}

export const billingService = {
  getPricing: async () => {
    const response = await api.get('/billing/pricing')
    return response.data
  },

  createCheckout: async (tierId: string, billingCycle = 'monthly') => {
    const response = await api.post('/billing/checkout', {
      tier_id: tierId,
      billing_cycle: billingCycle,
    })
    return response.data
  },

  getUsage: async (userId: string) => {
    const response = await api.get(`/billing/usage/${userId}`)
    return response.data
  },
}

export const exportService = {
  conversation: async (
    conversationId: string,
    format: 'md' | 'json' | 'csv' = 'md',
    includeMetadata = false,
  ): Promise<Blob> => {
    const response = await fetch('/api/export/conversation', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${localStorage.getItem('accessToken')}`,
      },
      body: JSON.stringify({
        conversation_id: conversationId,
        format,
        include_metadata: includeMetadata,
      }),
    })
    return response.blob()
  },

  usage: async (userId: string, days = 30): Promise<Blob> => {
    const response = await fetch(`/api/export/usage/${userId}?days=${days}`, {
      headers: {
        Authorization: `Bearer ${localStorage.getItem('accessToken')}`,
      },
    })
    return response.blob()
  },

  memory: async (query?: string, format: 'md' | 'json' = 'md'): Promise<Blob> => {
    const params = new URLSearchParams()
    if (query) params.set('query', query)
    params.set('format', format)

    const response = await fetch(`/api/export/memory?${params}`, {
      headers: {
        Authorization: `Bearer ${localStorage.getItem('accessToken')}`,
      },
    })
    return response.blob()
  },
}

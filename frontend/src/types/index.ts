/** User types */
export interface User {
  id: string
  email: string
  tier: 'free' | 'pro' | 'enterprise' | 'defense'
  role?: 'user' | 'admin' | 'super_admin'
  created_at?: string
}

/** Auth types */
export interface AuthTokens {
  access_token: string
  refresh_token: string
}

export interface LoginRequest {
  email: string
  password: string
}

export interface RegisterRequest {
  email: string
  password: string
  tier?: string
}

/** Chat types */
export interface Message {
  id?: string
  role: 'user' | 'assistant' | 'system'
  content: string
  created_at?: string
  tokens_used?: number
}

export interface ChatRequest {
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
  sources: Source[]
}

export interface Source {
  id: string
  text: string
  score: number
  metadata: Record<string, unknown>
}

/** Memory types */
export interface MemoryDocument {
  text: string
  source?: string
  metadata?: Record<string, unknown>
  chunker_strategy?: string
}

export interface MemoryChunk {
  id: string
  text: string
  score: number
  metadata: Record<string, unknown>
}

export interface MemoryStats {
  total_documents: number
  total_chunks: number
  total_tokens: number
  store_type: string
}

export interface MemoryIngestResponse {
  document_id: string
  chunks_processed: number
  chunks_stored: number
  errors: string[]
}

export interface MemorySearchRequest {
  query: string
  top_k?: number
  min_score?: number
}

/** Agent types */
export interface AgentTask {
  task: string
  agent_type: string
  use_memory?: boolean
  priority?: 'low' | 'normal' | 'high' | 'critical'
  metadata?: Record<string, unknown>
}

export interface AgentTaskResponse {
  task_id: string
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'
  result?: string
  agent_type: string
}

export interface AgentStatus {
  agent_id: string
  status: string
  tasks_completed: number
  last_active: string
}

export interface AgentInfo {
  id: string
  name: string
  description: string
  status: 'active' | 'idle' | 'error'
  tasks_completed: number
  last_active: string
}

/** Billing types */
export interface PricingTier {
  id: string
  name: string
  price_monthly: number
  price_yearly: number
  description: string
  features: string[]
  max_queries?: number
  max_documents?: number
  max_agents?: number
}

export interface UsageData {
  total_queries: number
  tokens_used: number
  documents_stored: number
  agents_run: number
  period_start: string
  period_end: string
}

export interface CheckoutRequest {
  tier_id: string
  billing_cycle: 'monthly' | 'yearly'
}

export interface CheckoutResponse {
  url: string
  session_id: string
}

/** Conversation types */
export interface Conversation {
  id: string
  title: string
  created_at: string
  updated_at: string
  message_count: number
}

export interface ConversationList {
  conversations: Conversation[]
  total: number
  limit: number
  offset: number
}

/** Toast types */
export interface Toast {
  id: string
  message: string
  type: 'success' | 'error' | 'info' | 'warning'
  duration?: number
}

/** Dashboard types */
export interface DashboardStats {
  total_conversations: number
  total_messages: number
  total_documents: number
  total_agents: number
  tokens_used_today: number
  queries_today: number
}

/** Export types */
export type ExportFormat = 'md' | 'json' | 'csv'

export interface ExportRequest {
  conversation_id: string
  format: ExportFormat
  include_metadata?: boolean
}

/** WebSocket types */
export interface WSMessage {
  type: 'chat' | 'task' | 'ping' | 'pong' | 'error' | 'status'
  data?: Record<string, unknown>
  message?: string
  task_id?: string
}

/** Settings types */
export interface UserSettings {
  theme: 'light' | 'dark' | 'system'
  language: string
  default_model: string
  use_rag_by_default: boolean
  temperature: number
  max_tokens: number
  notifications_enabled: boolean
}

/** API Response wrapper */
export interface ApiResponse<T = unknown> {
  data: T
  message?: string
  error?: string
}

/** Pagination */
export interface PaginationParams {
  page: number
  limit: number
  offset: number
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  limit: number
  has_next: boolean
  has_prev: boolean
}

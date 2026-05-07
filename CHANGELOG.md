# Changelog

All notable changes to the Titanium project.

## [0.1.0] - 2026-05-07

### Added

#### Core Platform
- FastAPI backend with async endpoints
- React 18 + TypeScript frontend with Vite
- Real-time chat via SSE and WebSocket
- RAG memory system with multiple chunkers and embedders
- Multi-agent orchestration with CrewAI + LangGraph

#### Security
- JWT authentication with bcrypt password hashing
- Prompt injection detection (10 pattern types with severity ranking)
- Input validation (string, filename, JSON, email, pagination)
- SSRF protection (private IP blocking, DNS rebinding detection)
- RBAC enforcement (user/admin/super_admin roles)
- Per-tier rate limiting middleware
- Security headers middleware

#### Memory System
- Fixed-size, semantic, and markdown chunkers
- Ollama, Groq, and HuggingFace embedders
- Qdrant, Chroma, and in-memory vector stores
- Full RAG pipeline with context retrieval

#### Agent Framework
- Base executor with status tracking
- Code executor with language detection
- Research executor with RAG context
- Security audit executor
- Writing executor with 6 styles
- LangGraph workflows (code, research, security, writing)

#### Billing
- Stripe integration with 4 tiers
- Pricing tiers: Free, Cyber Ops ($29/mo), Enterprise ($99/mo), Defense (custom)
- Checkout session creation
- Usage tracking

#### Features
- Feature flag system with rollout percentages
- Redis caching with in-memory fallback
- Resend email notifications
- Structured logging with request IDs
- Prometheus metrics + Grafana dashboards

#### Export
- Markdown, JSON, CSV export for conversations
- Usage report export
- Memory data export

#### Infrastructure
- Docker Compose (production + development)
- Kubernetes manifests
- Terraform for AWS (ECS, RDS, ALB)
- GitHub Actions CI/CD pipeline
- Playwright E2E tests

#### Frontend
- Dashboard with stats
- Chat with SSE streaming + WebSocket
- Conversation sidebar with history
- Memory management page
- Agents page
- Billing/pricing page
- Settings page
- Admin page
- Protected routes with tier checking
- Toast notifications
- Keyboard shortcuts
- Error boundary
- Responsive design

### Testing
- 19 backend test files (prompt injection, input validation, RBAC, SSRF, executors, export, system prompts, security integration, API contracts, WebSocket, features, RAG security, load testing)
- 5 frontend test files (ProtectedRoute, ToastContainer, useKeyboardShortcuts, useToast, export API)
- E2E tests with Playwright (frontend pages, navigation, responsive, accessibility)
- Load testing script

### Documentation
- README with architecture diagram
- API documentation
- Contributing guide
- AGENTS.md with build protocol
- Comprehensive .env.example

# Titanium - Enterprise AI Platform

Autonomous AI-driven platform with RAG memory, multi-agent orchestration, and zero-cost free-tier deployment.

## Architecture

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Frontend   │───▶│   Backend   │───▶│   Ollama    │
│  Vite+React │    │   FastAPI   │    │  Inference  │
└─────────────┘    └──────┬──────┘    └─────────────┘
                          │
              ┌───────────┼───────────┬──────────┐
              ▼           ▼           ▼          ▼
         ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
         │ Qdrant │ │ Neon   │ │ Stripe │ │ Redis  │
         │ Vector │ │ Postgres│ │ Billing│ │ Cache  │
         └────────┘ └────────┘ └────────┘ └────────┘
```

## Features

- **RAG Memory System** - Document chunking (fixed, semantic, markdown), embedding (Ollama, Groq, HuggingFace), vector storage (Qdrant, Chroma)
- **Multi-Agent Orchestration** - CrewAI agents + LangGraph workflows (code, research, analysis, security, writing)
- **Real-time Chat** - HTTP SSE streaming + WebSocket for token-by-token responses
- **Authentication** - JWT-based auth with bcrypt password hashing, token refresh
- **Billing** - Stripe integration with 4 tiers: Personal (free), Cyber Ops ($29/mo), Enterprise ($99/mo), Defense (custom)
- **File Processing** - PDF, DOCX, TXT, MD, CSV, JSON ingestion
- **Caching** - Redis-backed caching with in-memory fallback
- **Rate Limiting** - Per-tier rate limits (requests, tokens, concurrent tasks)
- **Feature Flags** - Runtime feature toggles with rollout percentages
- **Email Notifications** - Resend integration (welcome, billing, security, task alerts)
- **Monitoring** - Prometheus metrics + Grafana dashboards with alert rules
- **CI/CD** - GitHub Actions pipeline (lint → test → build → deploy)

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 20+
- Docker & Docker Compose (optional)
- Ollama (for local inference)

### Local Development

1. **Clone and configure**
```bash
cp .env.example .env
# Edit .env with your API keys
```

2. **Start Ollama**
```bash
ollama pull llama3
ollama pull nomic-embed-text
ollama serve
```

3. **Backend**
```bash
cd backend
pip install -r requirements.txt
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

4. **Frontend**
```bash
cd frontend
npm install
npm run dev
```

5. **Open** http://localhost:3000

### Docker Compose

```bash
docker compose up -d
```

Services:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Ollama: http://localhost:11434
- Qdrant: http://localhost:6333
- Qdrant Dashboard: http://localhost:6335
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3001 (admin/titanium)
- Redis: localhost:6379

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Health check |
| GET | `/metrics` | Prometheus metrics |
| POST | `/api/auth/register` | Register user |
| POST | `/api/auth/login` | Login |
| POST | `/api/auth/refresh` | Refresh token |
| GET | `/api/auth/me` | Get current user |
| POST | `/api/chat/` | Send message |
| POST | `/api/chat/stream` | Stream response (SSE) |
| POST | `/api/memory/ingest` | Ingest text |
| POST | `/api/memory/ingest-file` | Upload file |
| POST | `/api/memory/search` | Search memory |
| POST | `/api/agents/task` | Create agent task |
| GET | `/api/agents/status` | Agent status |
| GET | `/api/billing/pricing` | Get pricing tiers |
| WS | `/ws/chat/{client_id}` | WebSocket chat |
| WS | `/ws/agents/{client_id}` | WebSocket agents |

## Pricing Tiers

| Tier | Monthly | Features |
|------|---------|----------|
| Personal | Free | 100 queries, 10 docs, 1 agent |
| Cyber Ops | $29/mo | 5K queries, 500 docs, all agents |
| Enterprise | $99/mo | Unlimited, dedicated, SSO |
| Defense | Contact | Air-gapped, classified, FedRAMP |

## Project Structure

```
titanium/
├── agents/              # Agent framework
│   ├── orchestrator/    # CrewAI crew builder
│   ├── workflows/       # LangGraph workflows
│   ├── memory/          # Agent memory
│   └── tools/           # Custom tools
├── backend/             # FastAPI backend
│   ├── routers/         # API endpoints
│   ├── services/        # Business logic
│   │   ├── auth/        # JWT authentication
│   │   ├── billing/     # Stripe integration
│   │   ├── cache/       # Redis caching
│   │   ├── features/    # Feature flags
│   │   ├── notifications/ # Email service
│   │   └── processing/  # File processing
│   ├── middleware/      # Security + errors
│   ├── models/          # SQLAlchemy models
│   └── tests/           # Test suite
├── frontend/            # Vite + React
│   └── src/
│       ├── components/  # React components
│       ├── pages/       # Page views
│       ├── hooks/       # Custom hooks
│       └── services/    # API clients
├── memory/              # RAG memory system
│   ├── chunkers/        # Document chunking
│   ├── embeddings/      # Embedding services
│   ├── stores/          # Vector stores
│   └── pipelines/       # RAG pipeline
├── infra/               # Infrastructure
│   ├── terraform/       # AWS IaC
│   └── k8s/             # Kubernetes manifests
├── monitoring/          # Prometheus + Grafana
├── deployment/          # Deploy scripts
└── .github/workflows/   # CI/CD pipeline
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Vite + React 18 + TypeScript + TailwindCSS |
| Backend | FastAPI + Python 3.11 + Pydantic |
| Database | SQLite (dev) / Neon Postgres (prod) + SQLAlchemy |
| Cache | Redis (production) / In-memory fallback |
| Vector DB | Qdrant / Chroma / InMemory |
| Inference | Ollama (local) / Groq (cloud) |
| Agents | CrewAI + LangGraph |
| Auth | JWT + bcrypt |
| Billing | Stripe |
| Email | Resend |
| Monitoring | Prometheus + Grafana |
| Deploy | Docker Compose / Railway / Kubernetes |

## Security

- P0: JWT auth, bcrypt hashing, API key rotation, RBAC
- P1: Prompt injection detection, rate limiting, security headers, input validation
- P2: Agent sandboxing, tool access control, execution timeouts
- P3: Multi-tenant isolation, audit logging, CORS policy

## License

MIT

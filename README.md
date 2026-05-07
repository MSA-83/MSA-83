# Titanium - Enterprise AI Platform

[![CI](https://github.com/MSA-83/MSA-83/actions/workflows/ci.yml/badge.svg)](https://github.com/MSA-83/MSA-83/actions/workflows/ci.yml)
[![Deploy](https://github.com/MSA-83/MSA-83/actions/workflows/deploy.yml/badge.svg)](https://github.com/MSA-83/MSA-83/actions/workflows/deploy.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Autonomous AI-driven platform with RAG memory, multi-agent orchestration, and zero-cost free-tier deployment.

## Features

- **Multi-Agent System**: Research, Security, Code, and Summarizer agents with 8+ tools
- **RAG Memory**: Document ingestion, vector search, semantic chunking
- **Multi-Model LLM**: Ollama (local), Groq (cloud), OpenAI with automatic fallback
- **Real-time Chat**: REST, WebSocket, and SSE streaming with model picker
- **OAuth Auth**: GitHub & Google login, JWT sessions, RBAC tier system
- **Admin Dashboard**: Analytics, feature flags, audit logs, user management
- **Stripe Billing**: 4-tier pricing (Free/Pro/Enterprise/Defense)
- **Security**: Per-tier rate limiting, SSRF protection, prompt injection defense
- **Observability**: OpenTelemetry tracing, Prometheus metrics, structured logging
- **Background Tasks**: ARQ queue for document processing and notifications

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Vite + React + TypeScript + TailwindCSS |
| Backend | FastAPI + Python 3.13 |
| Database | PostgreSQL (Neon) + SQLAlchemy |
| Vector DB | Qdrant / Chroma |
| Cache/Queue | Redis (Upstash) + ARQ |
| LLM | Ollama / Groq / OpenAI |
| Agents | LangGraph + CrewAI |
| Deploy | Railway / Docker Compose |
| Monitoring | Prometheus + Grafana + OpenTelemetry |
| CI/CD | GitHub Actions |

## Quick Start

### Local Development

```bash
# Clone and install
git clone https://github.com/MSA-83/MSA-83.git titanium
cd titanium
make install

# Start dev servers
make dev

# Or use Docker Compose (includes PostgreSQL, Redis, Qdrant, Ollama)
make docker
```

**URLs after start:**
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Qdrant Dashboard: http://localhost:6333/dashboard

### One-Command Deploy

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new)

## Project Structure

```
titanium/
├── agents/                    # Multi-agent system
│   ├── orchestrator/          # Master coordinator
│   ├── executors/             # Research, Security, Code, Summarizer
│   └── tools/                 # Web search, CVE lookup, code exec, file ops
├── backend/
│   ├── routers/               # FastAPI endpoints (auth, chat, memory, etc.)
│   ├── services/              # Business logic (auth, billing, cache, queue)
│   ├── security/              # RBAC, rate limiting, input validation
│   └── middleware/            # Analytics, caching, security, rate limiting
├── frontend/src/
│   ├── components/            # React UI components
│   ├── pages/                 # Chat, Admin, Memory, Agents, Settings
│   └── hooks/                 # WebSocket, notifications, auth
├── memory/                    # RAG pipeline
│   ├── chunkers/              # Fixed, sentence, semantic, markdown
│   ├── embeddings/            # Ollama, OpenAI embedding models
│   └── stores/                # Qdrant, Chroma vector stores
├── deployment/
│   ├── docker-compose.yml     # 6-service local stack
│   └── railway/               # Railway deployment config
└── .github/workflows/         # CI/CD pipelines
```

## API Reference

### Authentication
```bash
POST /api/auth/register     # Create account
POST /api/auth/login        # Get JWT tokens
GET  /api/auth/me           # Current user
GET  /api/auth/rate-limit   # Usage stats
```

### Chat
```bash
POST /api/chat/             # Send message (supports SSE streaming)
GET  /api/chat/models       # List available LLM models
GET  /api/chat/ws/{id}      # WebSocket endpoint
```

### Memory
```bash
POST /api/memory/upload     # Upload document
GET  /api/memory/documents  # List documents
POST /api/memory/query      # RAG retrieval
```

### Admin (Enterprise+ tier)
```bash
GET  /api/admin/analytics/system   # System metrics
GET  /api/admin/analytics/top-users # Top users
GET  /api/admin/flags              # Feature flags
PUT  /api/admin/flags/{name}       # Update flag (defense tier)
GET  /api/admin/audit/logs         # Audit trail
GET  /api/export/gdpr/me           # Personal data export
```

## Rate Limits

| Tier | RPM | RPH | Max Tokens | File Size |
|------|-----|-----|------------|-----------|
| Free | 10 | 100 | 2,048 | 5MB |
| Pro | 60 | 1,000 | 8,192 | 25MB |
| Enterprise | 300 | 10,000 | 32,768 | 50MB |
| Defense | ∞ | ∞ | ∞ | ∞ |

## Testing

```bash
make test-backend     # 283 pytest tests
make test-frontend    # 27 vitest tests
make e2e              # 14 Playwright tests
make lint             # Ruff + ESLint + TypeScript
```

## Environment Variables

### Required
| Variable | Description |
|----------|------------|
| `DATABASE_URL` | PostgreSQL connection string |
| `JWT_SECRET_KEY` | Secret for signing JWT tokens |

### Optional
| Variable | Description |
|----------|------------|
| `REDIS_URL` | Redis URL for caching/queue |
| `GROQ_API_KEY` | Groq API key for cloud LLM |
| `OPENAI_API_KEY` | OpenAI API key |
| `GITHUB_CLIENT_ID` | GitHub OAuth client ID |
| `GOOGLE_CLIENT_ID` | Google OAuth client ID |
| `QDRANT_URL` | Qdrant Cloud URL |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | OpenTelemetry collector URL |

## Architecture

```
┌──────────┐     ┌──────────┐     ┌──────────┐
│ Frontend │────▶│  Backend │────▶│   LLM    │
│  (React) │     │ (FastAPI)│     │(Ollama/  │
└──────────┘     └────┬─────┘     │ Groq)    │
                      │           └──────────┘
              ┌───────┼───────┐
              ▼       ▼       ▼
         ┌──────┐ ┌──────┐ ┌──────┐
         │PostgreSQL│ │Redis │ │Qdrant│
         └──────┘ └──────┘ └──────┘
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgments

- [LangGraph](https://github.com/langchain-ai/langgraph) for agent orchestration
- [CrewAI](https://github.com/crewAIInc/crewAI) for multi-agent collaboration
- [FastAPI](https://fastapi.tiangolo.com/) for the backend framework
- [Qdrant](https://qdrant.tech/) for vector search

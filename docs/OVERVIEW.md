# Titanium Project Overview

## Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │───▶│   Backend       │───▶│   Ollama        │
│   Vite+React    │    │   FastAPI       │    │   Inference     │
│   TypeScript    │    │   Python 3.11   │    │   Local LLM     │
└─────────────────┘    └──────┬──────────┘    └─────────────────┘
                              │
                    ┌─────────┼─────────┬──────────┐
                    ▼         ▼         ▼          ▼
               ┌────────┐ ┌──────┐ ┌────────┐ ┌────────┐
               │ Qdrant │ │ Neon │ │ Stripe │ │ Redis  │
               │ Vector │ │ PG   │ │Billing │ │ Cache  │
               └────────┘ └──────┘ └────────┘ └────────┘
```

## Key Components

### Backend (FastAPI)
- **Routers**: Health, Auth, Chat, Memory, Agents, Billing, Conversations, Export, WebSocket
- **Services**: Ollama inference, RAG pipeline, Agent orchestration, Stripe billing, Redis cache, Usage tracking, Email notifications, Feature flags, System prompts, Export utilities
- **Middleware**: Security headers, Rate limiting (per-tier), Prompt injection detection, Error handling, Request ID tracking, CORS
- **Security**: JWT auth, bcrypt hashing, RBAC, SSRF protection, Input validation, SQLi/XSS checks

### Memory System
- **Chunkers**: Fixed-size, Semantic, Markdown
- **Embedders**: Ollama, Groq, HuggingFace
- **Stores**: Qdrant, Chroma, In-memory
- **Pipeline**: Full RAG with context retrieval and formatting

### Agent Framework
- **Executors**: Code, Research, Security audit, Writing
- **Workflows**: LangGraph state machines for multi-step tasks
- **Orchestration**: CrewAI for role-based agent teams
- **Memory**: Agent-specific context management

### Frontend (React)
- **Pages**: Dashboard, Chat, Memory, Agents, Billing, Admin, Settings, Login
- **Components**: Layout, Error boundary, Protected routes, Toast notifications, Conversation sidebar
- **Hooks**: Auth context, Keyboard shortcuts, Toast management, WebSocket
- **Types**: 30+ TypeScript interfaces for all data structures
- **Utilities**: Date formatting, validation, export helpers

### Infrastructure
- **Docker**: Production (with GPU) + Development (without GPU)
- **Kubernetes**: Full manifests for all services
- **Terraform**: AWS ECS, RDS, ALB configuration
- **CI/CD**: GitHub Actions (lint → test → build → deploy → security scan → E2E)
- **Monitoring**: Prometheus metrics + Grafana dashboards with alerts

## Security Features
| Priority | Feature |
|----------|---------|
| P0 | JWT auth, bcrypt hashing, API key rotation, RBAC |
| P1 | Prompt injection detection (10 patterns), Rate limiting, Security headers, Input validation |
| P2 | Agent sandboxing, Tool access control, Execution timeouts |
| P3 | Multi-tenant isolation, Audit logging, CORS policy, SSRF protection |

## Pricing Tiers
| Tier | Price | Queries | Documents | Agents |
|------|-------|---------|-----------|--------|
| Free | $0 | 100/mo | 10 | 1 |
| Pro | $29/mo | 5K/mo | 500 | All |
| Enterprise | $99/mo | Unlimited | Unlimited | All + Custom |
| Defense | Custom | Unlimited | Unlimited | All + Air-gapped |

## File Structure
```
titanium/
├── agents/              # Multi-agent framework
│   ├── executors/       # Task-specific agents
│   ├── orchestrator/    # CrewAI coordinator
│   ├── tools/           # Custom agent tools
│   └── workflows/       # LangGraph state machines
├── backend/             # FastAPI backend
│   ├── routers/         # API endpoints
│   ├── services/        # Business logic
│   ├── security/        # Auth, RBAC, validation
│   ├── middleware/      # Request/response middleware
│   ├── models/          # SQLAlchemy models
│   └── tests/           # 19 test files
├── frontend/            # React + TypeScript
│   └── src/
│       ├── components/  # React components
│       ├── pages/       # Page views
│       ├── hooks/       # Custom hooks
│       ├── services/    # API clients
│       ├── types/       # TypeScript types
│       └── utils/       # Utility functions
├── memory/              # RAG memory system
│   ├── chunkers/        # Document chunking
│   ├── embeddings/      # Embedding services
│   ├── stores/          # Vector stores
│   └── pipelines/       # RAG pipeline
├── infra/               # Infrastructure as code
│   ├── terraform/       # AWS configuration
│   └── k8s/             # Kubernetes manifests
├── monitoring/          # Prometheus + Grafana
├── deployment/          # Deploy scripts
├── prompts/             # System prompts & templates
└── docs/                # Documentation
```

## Statistics
- **130 source files** (Python + TypeScript)
- **24 test files** (backend + frontend + E2E)
- **17 config files** (Docker, CI/CD, infra)
- **6 documentation files**
- **9 prompt/template files**
- **177 total files**

## Quick Start
```bash
# 1. Clone and configure
cp .env.example .env
# Edit .env with your API keys

# 2. Install dependencies
make install

# 3. Start services
docker compose up -d

# 4. Seed demo data
make seed-demo

# 5. Open app
# Frontend: http://localhost:3000
# Backend: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

## Commands
| Command | Description |
|---------|-------------|
| `make dev` | Start development servers |
| `make test` | Run all tests |
| `make lint` | Run linters |
| `make format` | Format code |
| `make seed-demo` | Seed demo data |
| `make load-test` | Run load tests |
| `make e2e` | Run E2E tests |
| `make security-scan` | Run security scans |
| `make docker` | Start Docker stack |
| `make status` | Check service status |

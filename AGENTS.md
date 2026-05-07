[build-protocol]
name=Titanium
purpose=Autonomous AI-driven platform with RAG memory, multi-agent orchestration, and zero-cost free-tier deployment
version=0.1.0

[core-principles]
1. Zero upfront cost - free-tier only stack
2. RAG-first memory architecture
3. Agent isolation and security by default
4. Modular, swappable components
5. Open-source model preference (Ollama/Llama3)

[tech-stack]
frontend=Vite + React + TypeScript + TailwindCSS
backend=FastAPI + Python 3.11+
database=Neon Postgres (free-tier)
vector-db=Qdrant (self-hosted free) or Chroma
inference=Ollama (local) / Groq (cloud free-tier)
agents=CrewAI + LangGraph
queue=Upstash Redis (free-tier)
deploy=Railway / Render (free-tier)
monitoring=Prometheus + Grafana (self-hosted)
auth=Supabase Auth / JWT

[project-structure]
titanium/
├── apps/                    # App-level entrypoints
├── agents/
│   ├── orchestrator/        # Master agent coordinator
│   ├── executors/           # Task-specific agents
│   └── memory/              # Agent memory & context
├── backend/
│   ├── routers/             # FastAPI API routes
│   ├── services/            # Business logic
│   ├── security/            # Auth, RBAC, input sanitization
│   └── middleware/          # Request/response middleware
├── frontend/src/
│   ├── components/          # React components
│   ├── pages/               # Page-level views
│   └── hooks/               # Custom React hooks
├── infra/
│   ├── terraform/           # IaC configs
│   ├── docker/              # Docker configs
│   └── k8s/                 # Kubernetes manifests
├── memory/                  # RAG memory system
│   ├── chunkers/            # Document chunking
│   ├── embeddings/          # Embedding generation
│   ├── stores/              # Vector store implementations
│   └── pipelines/           # RAG retrieval pipelines
├── monitoring/              # Observability stack
└── deployment/              # Deploy scripts & configs

[workflow]
1. Parse user intent → 2. Retrieve context from RAG → 3. Route to appropriate agent → 4. Execute task → 5. Store result in memory → 6. Return response

[security-priorities]
P0=Secret management, RBAC, API key rotation
P1=Prompt injection defense, SSRF protection, input validation
P2=Agent sandboxing, tool access control, execution timeouts
P3=Multi-tenant isolation, audit logging, rate limiting

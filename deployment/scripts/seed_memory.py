"""Seed script to ingest documentation into the Titanium memory system."""

import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from memory.pipelines.rag_pipeline import create_rag_pipeline

SEED_DOCUMENTS = [
    {
        "source": "titanium-architecture.md",
        "metadata": {"category": "architecture", "version": "0.1.0"},
        "text": """# Titanium Architecture

Titanium is an enterprise AI platform built on a modular, service-oriented architecture.

## Core Components

### RAG Memory System
The memory system uses a three-stage pipeline:
1. **Chunking**: Documents are split using FixedSizeChunker, SemanticChunker, or MarkdownChunker
2. **Embedding**: Chunks are embedded using Ollama (nomic-embed-text), Groq, or HuggingFace models
3. **Storage**: Vectors are stored in Qdrant, Chroma, or in-memory for development

### Agent Orchestration
Agents are built on CrewAI with specialized roles:
- Researcher: Information gathering and analysis
- Coder: Code generation and review
- Analyst: Data analysis and insights
- Security: Vulnerability assessment
- Writer: Content creation

### Backend Services
- FastAPI handles all HTTP and WebSocket connections
- OllamaService manages LLM inference
- RAGService handles document ingestion and retrieval
- AgentOrchestrator coordinates multi-agent tasks
- AuthService manages JWT authentication
- StripeService handles billing and subscriptions

### Frontend
- Vite + React + TypeScript
- TailwindCSS for styling
- React Query for data fetching
- Custom WebSocket hooks for real-time communication
""",
    },
    {
        "source": "titanium-api-reference.md",
        "metadata": {"category": "api", "version": "0.1.0"},
        "text": """# Titanium API Reference

## Authentication

### POST /api/auth/register
Register a new user account.
Body: { email, password, tier }
Returns: { access_token, refresh_token, token_type, expires_in }

### POST /api/auth/login
Authenticate and receive tokens.
Body: { email, password }
Returns: { access_token, refresh_token, token_type, expires_in }

### POST /api/auth/refresh
Refresh an expired access token.
Body: { refresh_token }
Returns: { access_token, refresh_token }

## Chat

### POST /api/chat/
Send a message and receive an AI response.
Body: { message, use_rag, model, max_tokens, temperature }
Returns: { response, model, conversation_id, tokens_used, rag_context_used, sources }

### POST /api/chat/stream
Stream an AI response in real-time (Server-Sent Events).
Body: { message, use_rag, model, temperature }
Returns: SSE stream of tokens

## Memory

### POST /api/memory/ingest
Ingest text content into the memory system.
Body: { text, source, metadata, chunker_strategy }
Returns: { document_id, chunks_processed, chunks_stored, errors }

### POST /api/memory/ingest-file
Upload and process a file (PDF, DOCX, TXT, MD, CSV, JSON).
Form: file (multipart), source, chunker_strategy
Returns: { file_name, document_id, chunks_processed, chunks_stored, char_count, word_count }

### POST /api/memory/search
Search the memory system for relevant context.
Body: { query, top_k, min_score, filter_metadata }
Returns: { query, results, total_results }

## Agents

### POST /api/agents/task
Create and execute an agent task.
Body: { task, agent_type, use_memory, priority }
Returns: { task_id, status, result, agent_type }

### GET /api/agents/status
Get status of all agents.
Returns: { agents, active_tasks, total_tasks }

## Billing

### GET /api/billing/pricing
Get all pricing tiers.
Returns: Array of { id, name, price_monthly, price_yearly, description, features, limits }

### POST /api/billing/checkout
Create a Stripe checkout session.
Body: { tier_id, billing_cycle }
Returns: { tier_id, status, checkout_url, message }

## Health

### GET /api/health
Check system health.
Returns: { status, version, components }

## WebSockets

### WS /ws/chat/{client_id}
Real-time chat with token streaming.
Send: { message, use_rag, model, temperature }
Receive: { type: "chunk"|"done"|"error"|"status", content }

### WS /ws/agents/{client_id}
Real-time agent task execution.
Send: { task, agent_type }
Receive: { type: "result"|"status", task_id, content }
""",
    },
    {
        "source": "titanium-security.md",
        "metadata": {"category": "security", "version": "0.1.0"},
        "text": """# Titanium Security Model

## Authentication & Authorization
- JWT tokens with configurable expiration (access: 60min, refresh: 7 days)
- bcrypt password hashing with automatic salt
- Role-based access control (RBAC) tied to subscription tier
- Token refresh flow to minimize re-authentication

## Input Protection
- Prompt injection detection via regex pattern matching
- Input validation through Pydantic models
- Rate limiting (60 req/min default, configurable per tier)
- File size limits (50MB max) with type validation

## Network Security
- Security headers: X-Content-Type-Options, X-Frame-Options, HSTS, CSP
- CORS configuration with configurable origins
- GZip compression for responses over 1KB
- Trusted host validation

## Agent Security
- Sandboxed shell execution with allowed command whitelist
- File I/O restricted to workspace directory
- Execution timeouts (30s default for tools)
- Maximum iteration limits (10 per task)

## Data Protection
- Multi-tenant data isolation via user_id scoping
- Audit logging through request middleware
- Secure token storage (client-side localStorage with HTTPS)
- Database encryption at rest (managed by Neon/PostgreSQL)

## Priority Fixes
P0: Secret management, RBAC enforcement, API key rotation
P1: Prompt injection defense, SSRF protection, input validation
P2: Agent sandboxing, tool access control, execution timeouts
P3: Multi-tenant isolation, audit logging, rate limiting
""",
    },
    {
        "source": "titanium-deployment.md",
        "metadata": {"category": "deployment", "version": "0.1.0"},
        "text": """# Titanium Deployment Guide

## Local Development
- Docker Compose with all services (backend, frontend, Ollama, Qdrant)
- Hot reload for both frontend (Vite) and backend (uvicorn --reload)
- Environment variables via .env file

## Production - Railway
1. Connect GitHub repository to Railway
2. Set environment variables in Railway dashboard
3. Deploy backend service with Python buildpack
4. Deploy frontend service with Node.js buildpack
5. Add Neon Postgres database integration
6. Configure custom domain and SSL

## Production - Kubernetes
1. Apply namespace: kubectl apply -f infra/k8s/namespace.yaml
2. Deploy Qdrant: kubectl apply -f infra/k8s/qdrant.yaml
3. Deploy Ollama (requires GPU node): kubectl apply -f infra/k8s/ollama.yaml
4. Deploy backend: kubectl apply -f infra/k8s/backend.yaml
5. Deploy frontend: kubectl apply -f infra/k8s/frontend.yaml
6. Configure ingress: kubectl apply -f infra/k8s/ingress.yaml

## Infrastructure as Code
Terraform configuration in infra/terraform/main.tf provisions:
- ECS cluster with container insights
- ECR repositories for Docker images
- RDS PostgreSQL database (or use Neon externally)
- Application Load Balancer
- Security groups with least-privilege access

## Monitoring
- Prometheus scrapes metrics from /metrics endpoint
- Grafana dashboards provisioned automatically
- Alert rules for error rate, latency, service availability
- AlertManager integration for notifications

## CI/CD Pipeline
GitHub Actions workflow:
1. Lint (ruff + mypy for Python, ESLint + TypeScript for frontend)
2. Test (pytest for backend, Jest for frontend)
3. Build Docker images
4. Push to GitHub Container Registry
5. Deploy to Railway (main branch only)
""",
    },
    {
        "source": "titanium-pricing.md",
        "metadata": {"category": "business", "version": "0.1.0"},
        "text": """# Titanium Pricing Structure

## Personal (Free)
- 100 queries per month
- 10 document uploads to memory
- 1 agent type (general)
- Ollama local inference only
- 2048 token context window
- 10 requests per minute rate limit
- Community support

## Cyber Ops ($29/month)
- 5,000 queries per month
- 500 document uploads
- All agent types (researcher, coder, analyst, security, writer)
- Groq cloud inference + Ollama local
- 8192 token context window
- 60 requests per minute rate limit
- Priority support
- Custom model fine-tuning capability

## Enterprise ($99/month)
- Unlimited queries
- Unlimited document uploads
- Unlimited agents
- Dedicated inference instances
- 32768 token context window
- 300 requests per minute rate limit
- 24/7 dedicated support
- Custom model training
- SSO & SAML integration
- Full audit logging

## Defense (Contact Sales)
- Everything in Enterprise
- Air-gapped deployment option
- Classified data handling
- Custom security protocols
- On-premise deployment
- FedRAMP compliance
- Custom SLA agreements

## Usage Tracking
All usage is tracked per user per month:
- Query count resets on the 1st of each month
- Document storage is cumulative
- Agent task execution is unlimited on Enterprise+
- Rate limiting is per-minute sliding window
""",
    },
]


async def seed():
    """Ingest all seed documents into the memory system."""
    pipeline = create_rag_pipeline(
        chunker_strategy="markdown",
        embedder_provider="ollama",
        store_type="memory",
    )

    print("Titanium Memory Seed - Starting ingestion...")
    print(f"Documents to ingest: {len(SEED_DOCUMENTS)}")
    print("-" * 50)

    total_chunks = 0
    total_stored = 0
    total_errors = 0

    for doc in SEED_DOCUMENTS:
        print(f"Ingesting: {doc['source']}...")

        result = await pipeline.ingest(
            text=doc["text"],
            metadata=doc["metadata"],
        )

        total_chunks += result.chunks_processed
        total_stored += result.chunks_stored
        total_errors += len(result.errors)

        status = "OK" if not result.errors else f"WARN ({len(result.errors)} errors)"
        print(f"  -> {result.chunks_stored} chunks stored [{status}]")

        if result.errors:
            for err in result.errors:
                print(f"     Error: {err}")

    print("-" * 50)
    print(f"Seed complete:")
    print(f"  Total chunks processed: {total_chunks}")
    print(f"  Total chunks stored: {total_stored}")
    print(f"  Total errors: {total_errors}")

    stats = await pipeline.get_stats()
    print(f"\nPipeline config:")
    print(f"  Chunker: {stats['chunker']}")
    print(f"  Embedder: {stats['embedder']}")
    print(f"  Vector Store: {stats['vector_store']}")


if __name__ == "__main__":
    asyncio.run(seed())

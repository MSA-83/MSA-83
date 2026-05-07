# Titanium Developer Handbook

## Quick Start

```bash
# Clone and setup
git clone https://github.com/MSA-83/MSA-83.git
cd titanium
make install

# Start development
make dev

# Run tests
make test-backend
make test-frontend

# Build for production
make docker
```

## Project Structure

```
titanium/
├── agents/                    # Multi-agent system
│   ├── executors/            # Task-specific agents
│   │   ├── code_executor.py
│   │   ├── research_executor.py
│   │   ├── security_executor.py
│   │   ├── summarizer_executor.py
│   │   └── writing_executor.py
│   ├── memory/               # Per-agent memory
│   ├── orchestrator/         # CrewAI orchestration
│   ├── tools/                # Agent tool definitions
│   └── workflows/            # LangGraph workflows
├── backend/                  # FastAPI application
│   ├── middleware/           # Request middleware
│   │   ├── security.py       # Security headers, CORS
│   │   ├── rate_limit.py     # Per-tier rate limiting
│   │   └── errors.py         # Unified error handling
│   ├── models/               # Database models
│   ├── routers/              # API endpoints
│   │   ├── auth.py           # JWT auth
│   │   ├── oauth.py          # Social login
│   │   ├── chat.py           # LLM chat
│   │   ├── memory.py         # RAG memory
│   │   ├── agents.py         # Agent tasks
│   │   ├── billing.py        # Stripe billing
│   │   └── export.py         # Data export
│   ├── security/             # Security modules
│   │   ├── prompt_injection.py
│   │   ├── input_validation.py
│   │   ├── rbac.py
│   │   └── ssrf.py
│   ├── services/             # Business logic
│   └── tests/                # Test suite
├── frontend/                 # React application
│   └── src/
│       ├── components/       # Reusable components
│       ├── pages/            # Route pages
│       ├── hooks/            # Custom React hooks
│       ├── contexts/         # React contexts
│       ├── services/         # API clients
│       └── types/            # TypeScript types
├── memory/                   # RAG memory system
│   ├── chunkers/             # Text chunking strategies
│   ├── embeddings/           # Embedding providers
│   ├── pipelines/            # RAG pipeline
│   └── stores/               # Vector stores
├── monitoring/               # Prometheus + Grafana
├── docs/                     # Documentation
├── prompts/                  # System prompts & templates
├── deployment/               # Deploy scripts
└── infra/                    # Terraform + K8s
```

## Adding a New Agent Type

1. Create executor in `agents/executors/`:

```python
from agents.executors.base import BaseExecutor, ExecutorStatus, TaskResult

class MyExecutor(BaseExecutor):
    def __init__(self):
        super().__init__(name="my_agent", description="Does something")

    def validate_input(self, task_input: str) -> bool:
        return bool(task_input.strip())

    async def execute(self, task_input: str, context: dict = None) -> TaskResult:
        result = f"Processed: {task_input}"
        return TaskResult(status=ExecutorStatus.COMPLETED, output=result)

my_executor = MyExecutor()
```

2. Register in `agents/executors/__init__.py`:

```python
from agents.executors.my_executor import MyExecutor, my_executor

EXECUTORS = {
    ...,
    "my_agent": my_executor,
}
```

3. Add tools in `agents/tools/agent_tools.py`:

```python
tool_sets["my_agent"] = [FileReadTool(), ShellTool()]
```

## Adding a New API Endpoint

1. Create router in `backend/routers/`:

```python
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class MyRequest(BaseModel):
    data: str

@router.post("/my-endpoint")
async def my_endpoint(request: MyRequest):
    return {"status": "ok", "received": request.data}
```

2. Register in `backend/main.py`:

```python
from backend.routers import my_router
app.include_router(my_router.router, prefix="/api/my", tags=["my"])
```

## Adding Tests

### Backend Tests

```python
import pytest
from fastapi.testclient import TestClient
from backend.main import app

@pytest.fixture
def client():
    return TestClient(app)

def test_my_endpoint(client):
    response = client.post("/api/my/my-endpoint", json={"data": "test"})
    assert response.status_code == 200
```

Run: `TITANIUM_TESTING=true .venv/bin/pytest backend/tests/test_my.py -v`

### Frontend Tests

```typescript
import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import MyComponent from '../MyComponent'

describe('MyComponent', () => {
  it('renders correctly', () => {
    render(<MyComponent />)
    expect(screen.getByText('Hello')).toBeInTheDocument()
  })
})
```

Run: `make test-frontend`

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OLLAMA_BASE_URL` | Ollama service URL | `http://localhost:11434` |
| `JWT_SECRET_KEY` | JWT signing key | `titanium-dev-secret...` |
| `DATABASE_URL` | Database connection | `sqlite:///./titanium.db` |
| `REDIS_URL` | Redis connection | `redis://localhost:6379/0` |
| `STRIPE_SECRET_KEY` | Stripe API key | (required for billing) |
| `GITHUB_CLIENT_ID` | GitHub OAuth client ID | |
| `GITHUB_CLIENT_SECRET` | GitHub OAuth secret | |
| `GOOGLE_CLIENT_ID` | Google OAuth client ID | |
| `GOOGLE_CLIENT_SECRET` | Google OAuth secret | |

## Makefile Commands

| Command | Description |
|---------|-------------|
| `make install` | Install all dependencies |
| `make dev` | Start development servers |
| `make backend` | Start backend only |
| `make frontend` | Start frontend only |
| `make test-backend` | Run backend tests |
| `make test-frontend` | Run frontend tests |
| `make lint` | Run all linters |
| `make format` | Auto-format code |
| `make docker` | Start Docker stack |
| `make migrate` | Run DB migrations |
| `make health` | Check backend health |

## Common Patterns

### Error Handling

```python
from fastapi import HTTPException, status

try:
    result = await do_something()
except ValueError as e:
    raise HTTPException(status_code=400, detail=str(e))
except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))
```

### Authentication in Routes

```python
from backend.services.auth.auth_service import get_current_user

@router.get("/protected")
async def protected_endpoint(current_user: dict = Depends(get_current_user)):
    return {"user_id": current_user["user_id"]}
```

### RAG Context Retrieval

```python
from backend.services.rag_service import RAGService

rag = RAGService()
result = await rag.retrieve_context("your query", top_k=5)
context = result.get("context_text")
```

## Deployment

### Railway

1. Connect GitHub repo to Railway
2. Add environment variables
3. Deploy automatically on push

### Docker Compose

```bash
make docker
```

### Kubernetes

```bash
kubectl apply -f infra/k8s/
```

## Troubleshooting

### Tests failing with 429

Rate limiting is active. Run with `TITANIUM_TESTING=true`:

```bash
TITANIUM_TESTING=true .venv/bin/pytest backend/tests/ -v
```

### Ollama not responding

```bash
curl http://localhost:11434/api/tags
ollama pull llama3
```

### Port conflicts

Default ports: 5173 (frontend), 8000 (backend), 11434 (Ollama), 6333 (Qdrant), 6379 (Redis)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Write tests for new functionality
4. Ensure `make test` and `make lint` pass
5. Submit a pull request

# Titanium API Reference

## Base URL

```
http://localhost:8000/api
```

## Authentication

Most endpoints require a Bearer token in the `Authorization` header:

```
Authorization: Bearer <access_token>
```

Tokens are obtained via the `/api/auth/login` or `/api/auth/register` endpoints, or through OAuth providers.

---

## Health & Status

### `GET /api/health`

System health check with component status.

**Response:**
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "timestamp": "2026-05-07T03:20:00Z",
  "uptime_seconds": 3600.5,
  "components": {
    "api": { "status": "healthy", "latency_ms": null, "error": null },
    "database": { "status": "healthy", "latency_ms": 0.1, "error": null },
    "ollama": { "status": "healthy", "latency_ms": 12.3, "error": null },
    "redis": { "status": "unhealthy", "latency_ms": 1.0, "error": "Connection refused" },
    "qdrant": { "status": "healthy", "latency_ms": 2.1, "error": null }
  }
}
```

### `GET /api/health/dependencies`

Detailed dependency status.

**Response:**
```json
{
  "ollama": { "status": "healthy", "latency_ms": 12.3, "error": null },
  "redis": { "status": "unhealthy", "latency_ms": 1.0, "error": "Connection refused" },
  "qdrant": { "status": "healthy", "latency_ms": 2.1, "error": null },
  "database": { "status": "healthy", "latency_ms": 0.1, "error": null }
}
```

---

## Authentication

### `POST /api/auth/register`

Create a new user account.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123",
  "tier": "free"
}
```

**Response:**
```json
{
  "id": "user-0001",
  "email": "user@example.com",
  "tier": "free",
  "created_at": "2026-05-07T00:00:00Z",
  "access_token": "eyJhbG...",
  "refresh_token": "eyJhbG...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### `POST /api/auth/login`

Authenticate and receive tokens.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response:** Same as register.

### `POST /api/auth/refresh`

Refresh an access token.

**Request:**
```json
{
  "refresh_token": "eyJhbG..."
}
```

### `GET /api/auth/me`

Get current authenticated user.

**Headers:** `Authorization: Bearer <token>`

**Response:**
```json
{
  "user_id": "user-0001",
  "email": "user@example.com",
  "tier": "free"
}
```

---

## OAuth

### `GET /api/auth/oauth/{provider}`

Redirect to OAuth provider (GitHub or Google).

**Path Parameters:**
- `provider`: `github` or `google`

**Query Parameters:**
- `state`: Optional CSRF protection token

**Response:** 302 Redirect to provider.

### `GET /api/auth/oauth/{provider}/callback`

Handle OAuth callback.

**Query Parameters:**
- `code`: Authorization code from provider
- `state`: State parameter (echoed back)

**Response:**
```json
{
  "user": {
    "id": "user-0002",
    "email": "user@github.com",
    "tier": "free",
    "oauth_provider": "github",
    "display_name": "githubuser",
    "avatar_url": "https://avatars.githubusercontent.com/..."
  },
  "tokens": {
    "access_token": "eyJhbG...",
    "refresh_token": "eyJhbG...",
    "token_type": "bearer",
    "expires_in": 3600
  }
}
```

---

## Chat

### `POST /api/chat/`

Send a message and get an AI response.

**Request:**
```json
{
  "message": "What is Titanium?",
  "use_rag": true,
  "model": "llama3",
  "max_tokens": 2048,
  "temperature": 0.7,
  "conversation_id": "optional-existing-id"
}
```

**Response:**
```json
{
  "response": "Titanium is an enterprise AI platform...",
  "model": "llama3",
  "conversation_id": "conv-abc123",
  "tokens_used": 156,
  "rag_context_used": true,
  "sources": [
    {
      "id": "doc-xyz-chunk-0",
      "text": "...",
      "score": 0.92,
      "metadata": { "source": "readme.md" }
    }
  ]
}
```

### `POST /api/chat/stream`

Stream an AI response using Server-Sent Events.

**Request:** Same as `/api/chat/`

**Response:** `text/event-stream` with `data: {"chunk": "..."}` frames.

---

## Memory (RAG)

### `POST /api/memory/ingest`

Ingest text into the memory system.

**Request:**
```json
{
  "text": "Titanium is an enterprise AI platform with RAG memory.",
  "source": "readme.md",
  "metadata": { "category": "docs" },
  "chunker_strategy": "fixed"
}
```

**Response:**
```json
{
  "document_id": "doc-abc123",
  "chunks_processed": 3,
  "chunks_stored": 3,
  "errors": []
}
```

### `POST /api/memory/ingest-file`

Upload and ingest a file.

**Content-Type:** `multipart/form-data`

**Fields:**
- `file`: File to upload (PDF, DOCX, TXT, MD, CSV, JSON)
- `source`: Optional source name
- `chunker_strategy`: `fixed`, `semantic`, or `markdown`

### `POST /api/memory/search`

Search the memory system.

**Request:**
```json
{
  "query": "enterprise AI platform",
  "top_k": 5,
  "min_score": 0.5
}
```

**Response:**
```json
{
  "query": "enterprise AI platform",
  "results": [
    {
      "id": "doc-abc-chunk-0",
      "text": "Titanium is an enterprise AI platform...",
      "score": 0.92,
      "rank": 1,
      "metadata": { "source": "readme.md" }
    }
  ],
  "total_results": 1
}
```

### `GET /api/memory/stats`

Get memory system statistics.

**Response:**
```json
{
  "chunker": "FixedSizeChunker",
  "embedder": "OllamaEmbedder",
  "vector_store": "InMemoryStore",
  "embedder_dimensions": 768
}
```

---

## Agents

### `POST /api/agents/task`

Create an agent task.

**Request:**
```json
{
  "task": "Analyze this code for security vulnerabilities",
  "agent_type": "security",
  "use_memory": true,
  "priority": "normal",
  "metadata": { "language": "python" }
}
```

**Response:**
```json
{
  "task_id": "task-abc123",
  "status": "completed",
  "result": "...",
  "agent_type": "security"
}
```

**Supported Agent Types:**
- `code` - Code generation, review, explanation
- `research` - Web research and analysis
- `security` - Security audits and vulnerability analysis
- `summarizer` - Text summarization
- `writing` - Content creation and editing

### `GET /api/agents/task/{task_id}`

Get task status.

### `GET /api/agents/status`

Get status of all agents.

---

## Conversations

### `POST /api/conversations/`

Create a new conversation.

**Request:**
```json
{
  "title": "My Discussion"
}
```

### `GET /api/conversations/`

List conversations.

**Response:**
```json
{
  "conversations": [
    {
      "id": "conv-abc123",
      "title": "My Discussion",
      "created_at": "2026-05-07T00:00:00Z",
      "updated_at": "2026-05-07T01:00:00Z",
      "message_count": 5
    }
  ],
  "total": 1
}
```

---

## Billing

### `GET /api/billing/pricing`

Get available pricing tiers.

### `POST /api/billing/checkout`

Initiate checkout for a tier.

**Request:**
```json
{
  "tier_id": "pro"
}
```

---

## Export

### `POST /api/export/conversation`

Export a conversation.

**Request:**
```json
{
  "conversation_id": "conv-abc123",
  "format": "md",
  "include_metadata": false
}
```

**Formats:** `md`, `json`, `csv`

### `GET /api/export/usage/{user_id}`

Export usage data for a user.

---

## Security Features

### Rate Limiting

| Tier | Requests/min | Burst |
|------|-------------|-------|
| Free | 20 | 30 |
| Pro | 100 | 150 |
| Enterprise | 500 | 750 |
| Defense | 2000 | 3000 |

### Prompt Injection Detection

All chat and agent inputs are scanned for:
- Role manipulation attempts
- Mode-switching attempts
- Tag injection
- Code injection
- System prompt extraction
- Identity override attempts

### Input Validation

- SQL injection pattern detection
- XSS pattern detection
- Path traversal prevention
- Filename validation
- JSON depth limiting
- Email format validation

### SSRF Protection

- Private IP blocking (10.x, 172.16.x, 192.168.x, 127.x)
- Metadata endpoint blocking
- DNS rebinding detection
- Dangerous scheme blocking (file://, gopher://, etc.)

---

## Error Responses

All errors follow this format:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Input validation failed",
    "details": { "field": "email", "reason": "Invalid format" },
    "timestamp": "2026-05-07T00:00:00Z",
    "request_id": "abc-123"
  }
}
```

**Common Error Codes:**
- `AUTH_REQUIRED` (401) - Missing or invalid token
- `FORBIDDEN` (403) - Insufficient permissions
- `NOT_FOUND` (404) - Resource not found
- `RATE_LIMIT_EXCEEDED` (429) - Too many requests
- `VALIDATION_ERROR` (422) - Invalid input
- `PROMPT_INJECTION` (400) - Blocked injection attempt

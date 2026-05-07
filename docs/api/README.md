# Titanium API Documentation

## Base URL
- Development: `http://localhost:8000`
- Production: `https://api.yourdomain.com`

## Authentication
Most endpoints require a Bearer token in the `Authorization` header:
```
Authorization: Bearer <access_token>
```

### Get Token
```bash
POST /api/auth/login
{
  "email": "user@example.com",
  "password": "password123"
}
```

Response:
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

### Refresh Token
```bash
POST /api/auth/refresh
{
  "refresh_token": "eyJ..."
}
```

---

## Endpoints

### Health
- `GET /api/health` - System health check
- `GET /api/health/dependencies` - Dependency status

### Auth
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login
- `POST /api/auth/refresh` - Refresh token
- `GET /api/auth/me` - Get current user

### Chat
- `POST /api/chat/` - Send message and get response
- `POST /api/chat/stream` - Stream response (SSE)

### Memory
- `POST /api/memory/ingest` - Ingest text into memory
- `POST /api/memory/ingest-file` - Upload file to memory
- `POST /api/memory/search` - Search memory
- `DELETE /api/memory/documents/{id}` - Delete document
- `GET /api/memory/stats` - Memory statistics

### Agents
- `POST /api/agents/task` - Create agent task
- `GET /api/agents/task/{id}` - Get task status
- `GET /api/agents/status` - Get all agents status
- `POST /api/agents/task/{id}/cancel` - Cancel task

### Conversations
- `POST /api/conversations/` - Create conversation
- `GET /api/conversations/` - List conversations
- `GET /api/conversations/{id}` - Get conversation
- `GET /api/conversations/{id}/messages` - Get messages
- `POST /api/conversations/{id}/messages` - Add message
- `DELETE /api/conversations/{id}` - Delete conversation
- `GET /api/conversations/search` - Search conversations
- `GET /api/conversations/stats` - Conversation stats

### Billing
- `GET /api/billing/pricing` - Get pricing tiers
- `POST /api/billing/checkout` - Create checkout session
- `GET /api/billing/usage/{user_id}` - Get usage data

### Export
- `POST /api/export/conversation` - Export conversation (md/json/csv)
- `GET /api/export/usage/{user_id}` - Export usage report
- `GET /api/export/memory` - Export memory data

### WebSocket
- `WS /ws/chat/{client_id}` - Real-time chat
- `WS /ws/agents/{client_id}` - Real-time agent tasks

### Monitoring
- `GET /metrics` - Prometheus metrics
- `GET /docs` - Swagger UI
- `GET /redoc` - ReDoc

---

## Rate Limits

| Tier | Requests/min | Tokens/day | Concurrent Tasks |
|------|-------------|------------|-----------------|
| Free | 10 | 10,000 | 1 |
| Pro | 60 | 100,000 | 5 |
| Enterprise | 300 | 1,000,000 | 20 |
| Defense | Unlimited | Unlimited | Unlimited |

---

## Error Codes

| Code | Meaning |
|------|---------|
| 400 | Bad Request - Invalid input or prompt injection detected |
| 401 | Unauthorized - Missing or invalid token |
| 402 | Payment Required - Feature requires higher tier |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error |

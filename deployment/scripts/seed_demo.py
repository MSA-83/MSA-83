"""Seed database with demo data for development."""

import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


async def seed_memory():
    """Seed memory system with sample documents."""
    from backend.services.rag_service import RAGService

    rag = RAGService()

    documents = [
        {
            "text": """
Titanium is an enterprise AI platform with RAG memory and multi-agent orchestration.
It supports real-time chat, document ingestion, and automated task execution.

Key features:
- RAG memory with semantic search
- Multi-agent workflows using CrewAI and LangGraph
- Real-time streaming via SSE and WebSocket
- Role-based access control with tier-based rate limiting
- Stripe billing integration with 4 pricing tiers
""",
            "source": "platform_overview.md",
        },
        {
            "text": """
The Titanium architecture follows a microservices pattern:

Frontend (React 18 + TypeScript) <-> Backend (FastAPI) <-> Ollama (LLM Inference)
                                                    <-> Qdrant (Vector Store)
                                                    <-> Redis (Cache)
                                                    <-> PostgreSQL (Database)

The RAG pipeline:
1. Document ingestion -> Chunking -> Embedding -> Vector storage
2. Query -> Embedding -> Similarity search -> Context retrieval -> LLM generation
""",
            "source": "architecture.md",
        },
        {
            "text": """
Security measures in Titanium:

P0 (Critical):
- JWT authentication with token rotation
- bcrypt password hashing
- RBAC enforcement
- Prompt injection detection

P1 (High):
- Input validation and sanitization
- Rate limiting per tier
- Security headers (CSP, HSTS, X-Frame-Options)
- SSRF protection

P2 (Medium):
- Agent sandboxing
- Tool access control
- Execution timeouts
- CORS policy enforcement

P3 (Low):
- Multi-tenant isolation
- Audit logging
- Request ID tracking
""",
            "source": "security.md",
        },
        {
            "text": """
Titanium Pricing Tiers:

1. Free ($0/month)
   - 100 queries/day
   - 10 documents
   - 1 agent
   - Basic RAG

2. Cyber Ops ($29/month)
   - 5,000 queries/day
   - 500 documents
   - All agents
   - File upload
   - Export capabilities

3. Enterprise ($99/month)
   - Unlimited queries
   - Unlimited documents
   - All agents + custom workflows
   - SSO integration
   - API access
   - Priority support

4. Defense (Custom pricing)
   - Air-gapped deployment
   - Classified data handling
   - FedRAMP compliance
   - Custom retention policies
   - Dedicated infrastructure
""",
            "source": "pricing.md",
        },
        {
            "text": """
API Endpoints Reference:

Authentication:
- POST /api/auth/register - Create account
- POST /api/auth/login - Login
- POST /api/auth/refresh - Refresh token
- GET /api/auth/me - Get current user

Chat:
- POST /api/chat/ - Send message
- POST /api/chat/stream - Stream response (SSE)

Memory:
- POST /api/memory/ingest - Ingest text
- POST /api/memory/ingest-file - Upload file
- POST /api/memory/search - Search memory

Agents:
- POST /api/agents/task - Create task
- GET /api/agents/task/{id} - Task status
- GET /api/agents/status - All agents status

Conversations:
- POST /api/conversations/ - Create conversation
- GET /api/conversations/ - List conversations
- GET /api/conversations/{id} - Get conversation
- DELETE /api/conversations/{id} - Delete conversation

Billing:
- GET /api/billing/pricing - Get pricing
- POST /api/billing/checkout - Create checkout

Export:
- POST /api/export/conversation - Export conversation
- GET /api/export/usage/{id} - Export usage
- GET /api/export/memory - Export memory
""",
            "source": "api_reference.md",
        },
    ]

    print("Seeding memory system...")
    for doc in documents:
        try:
            result = await rag.ingest(
                text=doc["text"],
                source=doc["source"],
                chunker_strategy="fixed",
            )
            print(f"  ✓ Ingested {doc['source']}: {result['chunks_stored']} chunks")
        except Exception as e:
            print(f"  ✗ Failed to ingest {doc['source']}: {e}")

    stats = await rag.get_stats()
    print(f"\nMemory stats: {stats}")


async def seed_users():
    """Seed database with demo users."""
    from backend.models.database import SessionLocal
    from backend.models.user import User
    from backend.services.auth.hasher import Hasher

    hasher = Hasher()
    db = SessionLocal()

    demo_users = [
        {
            "email": "demo@titanium.ai",
            "password": hasher.hash("demo1234"),
            "tier": "free",
            "role": "user",
        },
        {
            "email": "admin@titanium.ai",
            "password": hasher.hash("admin1234"),
            "tier": "enterprise",
            "role": "admin",
        },
    ]

    print("\nSeeding users...")
    for user_data in demo_users:
        existing = db.query(User).filter(User.email == user_data["email"]).first()
        if existing:
            print(f"  - User {user_data['email']} already exists, skipping")
            continue

        user = User(**user_data)
        db.add(user)
        print(f"  ✓ Created user {user_data['email']}")

    db.commit()
    db.close()


async def main():
    """Run all seeders."""
    print("=" * 50)
    print("Titanium Demo Data Seeder")
    print("=" * 50)

    await seed_memory()

    try:
        await seed_users()
    except Exception as e:
        print(f"User seeding skipped (database may not be initialized): {e}")

    print("\n" + "=" * 50)
    print("Seeding complete!")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())

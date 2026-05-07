# Quick Start Guide

## Prerequisites
- Python 3.11+
- Node.js 20+
- Docker & Docker Compose (optional)
- Ollama (for local inference)

## Option 1: Docker Compose (Recommended)

### 1. Clone and configure
```bash
cp .env.example .env
# Edit .env with your settings
```

### 2. Start all services
```bash
docker compose up -d
```

### 3. Seed demo data
```bash
make seed-demo
```

### 4. Open the app
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Grafana: http://localhost:3001 (admin/titanium)

## Option 2: Local Development

### 1. Start Ollama
```bash
ollama pull llama3
ollama pull nomic-embed-text
ollama serve
```

### 2. Install dependencies
```bash
make install
```

### 3. Start backend
```bash
make backend
```

### 4. Start frontend (new terminal)
```bash
make frontend
```

### 5. Seed demo data
```bash
make seed-demo
```

### 6. Open the app
- Frontend: http://localhost:5173
- Backend: http://localhost:8000

## First Steps

### 1. Register an account
Visit http://localhost:3000/register and create an account.

### 2. Try the chat
Go to the Chat page and send a message. The AI will respond using Ollama.

### 3. Add documents to memory
Go to the Memory page and upload a document or paste text. The system will chunk, embed, and store it.

### 4. Search your memory
Use the search box to find relevant information from your ingested documents.

### 5. Create an agent task
Go to the Agents page and create a task. The system will route it to the appropriate agent.

## Demo Accounts
After running `make seed-demo`:
- **Demo user**: demo@titanium.ai / demo1234
- **Admin**: admin@titanium.ai / admin1234

## Troubleshooting

### Ollama not responding
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Restart Ollama
ollama serve
```

### Frontend build fails
```bash
cd frontend
rm -rf node_modules
npm install
npm run dev
```

### Database issues
```bash
# Reset database
rm -f backend/titanium.db
make migrate
make seed-demo
```

### Check service status
```bash
make status
```

## Next Steps
- Read the [API documentation](api/README.md)
- Read the [deployment guide](DEPLOYMENT.md)
- Read the [project overview](OVERVIEW.md)

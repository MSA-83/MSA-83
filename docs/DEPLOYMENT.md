# Deployment Guide

## Quick Deploy (Railway)

1. Connect your GitHub repo to Railway
2. Set environment variables in Railway dashboard:
   - `JWT_SECRET_KEY` - Generate a strong random key
   - `DATABASE_URL` - Railway will auto-provision PostgreSQL
   - `REDIS_URL` - Railway will auto-provision Redis
   - `STRIPE_SECRET_KEY` - Your Stripe secret key
   - `OLLAMA_BASE_URL` - Your Ollama endpoint
3. Deploy from `main` branch

## Docker Compose

### Production
```bash
docker compose up -d
```

Services:
- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8000`
- Ollama: `http://localhost:11434`
- Qdrant: `http://localhost:6333`
- Redis: `localhost:6379`
- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3001` (admin/titanium)

### Development
```bash
docker compose -f docker-compose.dev.yml up -d
```

## Kubernetes

```bash
kubectl apply -f infra/k8s/namespace.yaml
kubectl apply -f infra/k8s/
kubectl get pods -n titanium
```

## Terraform (AWS)

```bash
cd infra/terraform
terraform init
terraform plan
terraform apply
```

## Post-Deployment

1. Run database migrations:
   ```bash
   make migrate
   ```

2. Seed demo data:
   ```bash
   python deployment/scripts/seed_demo.py
   ```

3. Configure Ollama models:
   ```bash
   bash deployment/scripts/setup-ollama.sh
   ```

4. Verify health:
   ```bash
   make health
   ```

## Environment Variables

See `.env.example` for all available configuration options.

### Required
- `JWT_SECRET_KEY` - Secret for signing JWT tokens
- `DATABASE_URL` - Database connection string
- `OLLAMA_BASE_URL` - Ollama API endpoint

### Optional
- `REDIS_URL` - Redis connection (falls back to in-memory)
- `STRIPE_SECRET_KEY` - Stripe API key for billing
- `RESEND_API_KEY` - Resend API key for emails
- `SENTRY_DSN` - Sentry error tracking
- `QDRANT_HOST`, `QDRANT_PORT` - Qdrant vector store
- `EMBEDDER_PROVIDER` - Embedding provider (ollama/groq/huggingface)

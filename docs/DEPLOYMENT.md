# Titanium Deployment Guide

## Free-Tier Stack (Zero Cost)

| Service | Purpose | Free Tier |
|---------|---------|-----------|
| **Railway** | Backend + Frontend hosting | $5 credit/month, 512MB RAM |
| **Neon** | PostgreSQL database | 0.5GB storage, 1 compute |
| **Qdrant Cloud** | Vector database | 1GB storage |
| **Groq** | LLM inference (cloud) | 30 RPM, open models |
| **Upstash** | Redis cache + queue | 10K commands/day |
| **Cloudflare** | CDN + DDoS protection | Free tier unlimited |

---

## Step 1: Database (Neon PostgreSQL)

1. Go to [neon.tech](https://neon.tech) and sign up
2. Create a new project named `titanium-db`
3. Copy the connection string:
   ```
   postgresql://user:password@ep-xxx.us-east-2.aws.neon.tech/titanium?sslmode=require
   ```
4. Set as environment variable: `DATABASE_URL`

---

## Step 2: Vector Store (Qdrant Cloud)

1. Go to [cloud.qdrant.io](https://cloud.qdrant.io) and sign up
2. Create a new cluster (free tier: 1GB)
3. Copy the URL and API key
4. Set environment variables:
   ```
   QDRANT_URL=https://xxx-xxx.us-east.aws.cloud.qdrant.io
   QDRANT_API_KEY=your-api-key
   ```

---

## Step 3: Redis Cache (Upstash)

1. Go to [upstash.com](https://upstash.com) and sign up
2. Create a new Redis database
3. Copy the REST URL and token
4. Set environment variable:
   ```
   REDIS_URL=https://xxx.upstash.io
   REDIS_TOKEN=your-token
   ```

---

## Step 4: LLM Inference (Groq)

1. Go to [console.groq.com](https://console.groq.com) and sign up
2. Create an API key
3. Set environment variables:
   ```
   GROQ_API_KEY=your-api-key
   LLM_PROVIDER=groq
   ```

---

## Step 5: OAuth Setup

### GitHub OAuth
1. Go to [github.com/settings/developers](https://github.com/settings/developers)
2. Create a new OAuth App
3. Set Homepage URL: `https://your-app.railway.app`
4. Set Authorization callback URL: `https://your-app.railway.app/api/auth/oauth/github/callback`
5. Copy Client ID and Client Secret

### Google OAuth
1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Create OAuth 2.0 credentials
3. Set Authorized redirect URI: `https://your-app.railway.app/api/auth/oauth/google/callback`
4. Copy Client ID and Client Secret

---

## Step 6: Deploy to Railway

### Backend

1. Push code to GitHub (already done: `https://github.com/MSA-83/MSA-83`)
2. Go to [railway.app](https://railway.app) and sign in with GitHub
3. Create new project → Deploy from GitHub repo
4. Set root directory: `titanium`
5. Add environment variables:

   ```
   DATABASE_URL=postgresql://...
   QDRANT_URL=https://...
   QDRANT_API_KEY=...
   REDIS_URL=https://...
   REDIS_TOKEN=...
   GROQ_API_KEY=gsk_...
   LLM_PROVIDER=groq
   JWT_SECRET_KEY=<generate-256-bit-random-string>
   GITHUB_CLIENT_ID=...
   GITHUB_CLIENT_SECRET=...
   GOOGLE_CLIENT_ID=...
   GOOGLE_CLIENT_SECRET=...
   FRONTEND_URL=https://your-frontend.railway.app
   ```

6. Set Start Command: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
7. Deploy

### Frontend

1. In the same Railway project, add another service from the same repo
2. Set root directory: `titanium/frontend`
3. Railway auto-detects Vite and builds it
4. Add environment variable:
   ```
   VITE_API_URL=https://your-backend.railway.app
   ```
5. Deploy

---

## Step 7: Custom Domain (Optional)

1. Buy a domain or use an existing one
2. Add Cloudflare as DNS provider
3. In Railway, go to Settings → Domains
4. Add your domain (e.g., `api.yourdomain.com` for backend, `yourdomain.com` for frontend)
5. Update Cloudflare DNS records to point to Railway

---

## Step 8: Verify Deployment

```bash
# Check backend health
curl https://your-backend.railway.app/api/health

# Test chat endpoint
curl -X POST https://your-backend.railway.app/api/chat/ \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, Titanium!"}'

# Test OAuth redirect
curl -I https://your-backend.railway.app/api/auth/oauth/github
```

---

## Docker Alternative

For local Docker deployment or self-hosting:

```bash
# Build and start all services
make docker

# Or manually
docker compose -f deployment/docker-compose.yml up -d
```

---

## Troubleshooting

### Database Connection Issues
- Neon uses SSL by default; ensure `?sslmode=require` in connection string
- Neon suspends inactive databases; first request may take 1-2s to wake

### Rate Limiting in Production
- Free tier: 20 req/min
- Check `X-RateLimit-Remaining` header
- If blocked, wait 60s or upgrade tier

### OAuth Callback Errors
- Ensure callback URLs exactly match (including trailing slashes)
- `FRONTEND_URL` must match the actual frontend domain
- Check Railway logs for detailed error messages

### Memory Issues on Railway
- Railway free tier: 512MB RAM
- Use `LLM_PROVIDER=groq` instead of Ollama to reduce memory
- Disable Qdrant if not using vector search: use in-memory store

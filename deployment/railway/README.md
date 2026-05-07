# Railway Deployment Guide

## Quick Deploy

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new/template?template=https://github.com/MSA-83/MSA-83)

## Prerequisites

1. **GitHub Account** - Code is at `https://github.com/MSA-83/MSA-83`
2. **Railway Account** - Sign up at [railway.app](https://railway.app)
3. **Neon PostgreSQL** - Free database at [neon.tech](https://neon.tech)
4. **(Optional) Groq API** - Free LLM at [console.groq.com](https://console.groq.com)

## Step 1: Create Railway Project

1. Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub
2. Select the `MSA-83` repository
3. Set root directory: leave blank (uses `railway.json` at root)

## Step 2: Add PostgreSQL

1. In your Railway project, click `+ New` → Database → Add PostgreSQL
2. Railway creates a managed PostgreSQL instance
3. Copy the `DATABASE_URL` variable

## Step 3: Set Environment Variables

Go to your backend service → Variables tab → Add these:

### Required
| Variable | Value |
|----------|-------|
| `DATABASE_URL` | From Railway PostgreSQL (step 2) |
| `JWT_SECRET_KEY` | Run: `openssl rand -hex 32` |

### Recommended
| Variable | Value |
|----------|-------|
| `GROQ_API_KEY` | From [console.groq.com](https://console.groq.com) |
| `FRONTEND_URL` | Your Railway frontend URL |

### Optional
| Variable | Value |
|----------|-------|
| `GITHUB_CLIENT_ID` | GitHub OAuth app ID |
| `GITHUB_CLIENT_SECRET` | GitHub OAuth secret |
| `GOOGLE_CLIENT_ID` | Google OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | Google OAuth secret |
| `QDRANT_URL` | Qdrant Cloud URL |
| `QDRANT_API_KEY` | Qdrant API key |
| `REDIS_URL` | Upstash Redis URL |
| `REDIS_TOKEN` | Upstash Redis token |

## Step 4: Configure Backend Service

1. Go to backend service → Settings
2. Set **Root Directory**: (leave blank)
3. Set **Start Command**: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT --workers 2`
4. Enable **Deploy on Push**

## Step 5: Add Frontend Service

1. Click `+ New` → GitHub Repo → Same repo
2. Set root directory: `frontend`
3. Railway auto-detects Vite, sets build command: `npm run build`
4. Set start command: `npx serve -s dist -l $PORT`
5. Add variable: `VITE_API_URL` = your backend Railway URL

## Step 6: Set Up Domains

1. Backend service → Settings → Domains → Generate Domain
2. Frontend service → Settings → Domains → Generate Domain
3. Update `FRONTEND_URL` env var with the frontend domain
4. Update OAuth callback URLs in GitHub/Google consoles

## Step 7: Verify Deployment

```bash
# Check backend health
curl https://your-backend.railway.app/api/health

# Check API docs
curl https://your-backend.railway.app/docs

# Test chat
curl -X POST https://your-backend.railway.app/api/chat/ \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello from Railway!"}'
```

## Troubleshooting

### Service won't start
- Check logs in Railway dashboard
- Verify `DATABASE_URL` is correct
- Ensure `JWT_SECRET_KEY` is set

### OAuth not working
- Callback URLs must exactly match Railway domain
- `FRONTEND_URL` must match frontend domain

### LLM not responding
- Set `GROQ_API_KEY` for cloud inference
- Or use `LLM_PROVIDER=ollama` (not available on Railway free tier)

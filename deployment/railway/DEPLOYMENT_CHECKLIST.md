# Railway Deployment Checklist

## Prerequisites
- [ ] Railway account at [railway.app](https://railway.app)
- [ ] GitHub repo connected: https://github.com/MSA-83/MSA-83
- [ ] $5 Railway credit available (free tier)

## Step 1: Create Project

1. Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub
2. Select `MSA-83/MSA-83` repository
3. Railway auto-detects `railway.json` at root → this deploys the **backend**

## Step 2: Add PostgreSQL Database

1. In project, click `+ New` → Database → Add PostgreSQL
2. Railway creates managed PostgreSQL
3. Copy `DATABASE_URL` from Variables tab

## Step 3: Configure Backend Environment Variables

Go to backend service → Variables → Add:

### Required
```
DATABASE_URL=postgresql://...  (from Step 2)
JWT_SECRET_KEY=<run: openssl rand -hex 32>
```

### Recommended
```
GROQ_API_KEY=gsk_your-key-here  (from console.groq.com)
FRONTEND_URL=https://frontend-production-xxxx.up.railway.app  (set after Step 4)
```

### Optional
```
REDIS_URL=redis://...  (Upstash)
GITHUB_CLIENT_ID=...
GITHUB_CLIENT_SECRET=...
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
```

## Step 4: Add Frontend Service

1. Click `+ New` → GitHub Repo → Select `MSA-83/MSA-83`
2. Settings → Root Directory: `frontend`
3. Railway auto-detects `railway.json` in frontend/
4. Add Variables:
   ```
   VITE_API_URL=https://backend-production-xxxx.up.railway.app
   ```

## Step 5: Connect Services

1. Go to backend Settings → Domains → Generate Domain
2. Go to frontend Settings → Domains → Generate Domain
3. Update `FRONTEND_URL` env var with frontend domain
4. Update `VITE_API_URL` env var with backend domain

## Step 6: Verify Deployment

```bash
# Check backend
curl https://backend-production-xxxx.up.railway.app/api/health

# Check frontend
curl https://frontend-production-xxxx.up.railway.app

# Check API docs
curl https://backend-production-xxxx.up.railway.app/docs
```

## Step 7: Configure OAuth (optional)

1. **GitHub**: Settings → Developer Settings → OAuth Apps
   - Homepage URL: frontend Railway domain
   - Callback: `https://backend-production-xxxx.up.railway.app/api/auth/oauth/github/callback`

2. **Google**: Cloud Console → APIs & Services → Credentials
   - Authorized JS origins: frontend Railway domain
   - Redirect URI: `https://backend-production-xxxx.up.railway.app/api/auth/oauth/google/callback`

## Troubleshooting

### Backend won't start
- Check logs in Railway dashboard
- Verify `DATABASE_URL` is valid
- Ensure `JWT_SECRET_KEY` is set

### Frontend can't reach API
- Verify `VITE_API_URL` matches backend domain
- Check CORS settings in backend

### Health check failing
- Wait 300s for first start
- Check `POSTGRES_URL` format

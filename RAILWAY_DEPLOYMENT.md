# Railway Deployment Instructions

## Overview
This guide covers deploying both the FastAPI backend and Celery worker services to Railway.

## Architecture
```
Railway Project: Modomo Dataset Management
├── Service 1: FastAPI Backend (Web API)
├── Service 2: Celery Worker (Background Jobs)  
└── Service 3: Redis (Message Broker)
```

## Prerequisites

1. **Railway CLI**: `npm install -g @railway/cli`
2. **Railway Account**: Sign up at railway.app
3. **GitHub Repository**: Connected to Railway project

## Deployment Steps

### 1. Create Railway Project
```bash
railway login
railway init
```

### 2. Deploy Redis Service
1. In Railway dashboard: "New" → "Database" → "Redis"
2. Note the `REDIS_URL` from the Redis service variables

### 3. Deploy FastAPI Backend
```bash
# Link to Railway project
railway link

# Deploy backend service
railway up --service backend
```

**Backend Configuration:**
- Uses: `railway.json`
- Dockerfile: `Dockerfile`
- Start Command: `python main.py`
- Health Check: `/health`

### 4. Deploy Celery Worker Service

**Option A: From Railway Dashboard**
1. "New" → "Service" → "GitHub Repo"
2. Select your repository
3. Set **Root Directory**: `backend`
4. Upload `railway-worker.json` as the Railway config
5. Service will use `Dockerfile.worker`

**Option B: From CLI**
```bash
# Deploy worker service with custom config
railway up --config railway-worker.json --service celery-worker
```

**Worker Configuration:**
- Uses: `railway-worker.json` 
- Dockerfile: `Dockerfile.worker`
- Start Command: Celery worker with all queues
- Health Check: `celery inspect ping`

## Environment Variables

Set these variables for **BOTH** services (Backend + Worker):

### Required Variables
```bash
# Database
DATABASE_URL=postgresql://user:pass@host:port/db
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SECRET_KEY=your-service-key

# Redis (copy from Railway Redis service)
REDIS_URL=redis://default:password@host:port

# Cloudflare R2
R2_ACCOUNT_ID=your-account-id
R2_ACCESS_KEY_ID=your-access-key
R2_SECRET_ACCESS_KEY=your-secret-key
R2_BUCKET_NAME=modomo-datasets
R2_ENDPOINT_URL=https://account-id.r2.cloudflarestorage.com
R2_PUBLIC_URL=https://pub-xyz.r2.dev

# Processing
PRODUCTION=true
JOB_TIMEOUT=1800
```

### Optional Variables
```bash
# Worker Scaling
CELERY_WORKER_CONCURRENCY=2
CELERY_WORKER_MAX_TASKS=100
CELERY_RESULT_EXPIRES=3600

# AI Processing (if using RunPod)
RUNPOD_API_KEY=your-runpod-key
RUNPOD_ENDPOINT_ID=your-endpoint-id
USE_LOCAL_AI=false
AI_PROCESSING_ENABLED=true
```

## Service Communication

The services communicate through:
1. **Redis** - Message broker for job queues
2. **Shared Database** - PostgreSQL/Supabase for data persistence
3. **Environment Variables** - Shared configuration

## Monitoring & Logs

### Check Service Health
```bash
# Backend health
curl https://your-backend.railway.app/health

# Worker health (via Railway logs)
railway logs --service celery-worker
```

### Monitor Queues
```bash
# Connect to worker service
railway shell --service celery-worker

# Inside worker shell
celery -A app.worker.celery_app inspect active
celery -A app.worker.celery_app inspect stats
```

## Scaling

### Scale Workers
1. **Horizontal**: Deploy multiple worker service replicas
2. **Vertical**: Increase `CELERY_WORKER_CONCURRENCY`
3. **Queue-based**: Add specialized worker services for specific queues

### Performance Tips
- Monitor Redis memory usage 
- Set appropriate `CELERY_WORKER_MAX_TASKS` for memory management
- Use `--without-gossip --without-mingle` flags for better startup performance

## Troubleshooting

### Common Issues

1. **Worker not connecting to Redis**
   - Check `REDIS_URL` matches in both services
   - Verify Redis service is running

2. **Tasks not being processed**
   - Check worker logs for queue registration
   - Verify task routing in `celery_app.py`

3. **Database connection errors**
   - Ensure `DATABASE_URL` and Supabase keys are correct
   - Check database service availability

### Debug Commands
```bash
# Test Celery worker locally
celery -A app.worker.celery_app worker --loglevel=debug

# Test task dispatch
python -c "from app.worker.tasks import *; result = test_task.delay()"

# Check task routing
python -c "from app.worker.celery_app import celery_app; print(celery_app.conf.task_routes)"
```

## File Structure
```
backend/
├── Dockerfile              # Main API service
├── Dockerfile.worker       # Celery worker service  
├── railway.json            # API service config
├── railway-worker.json     # Worker service config
├── deploy-worker.md        # Worker deployment guide
├── app/
│   ├── worker/
│   │   ├── celery_app.py   # Celery configuration
│   │   ├── tasks.py        # Background tasks
│   │   └── huggingface_tasks.py
│   └── ...
└── requirements.txt
```

## Success Criteria

✅ Backend API responds to health checks  
✅ Worker connects to Redis broker  
✅ Worker registers all task queues  
✅ Jobs can be queued and processed  
✅ Database operations work in both services  
✅ R2 file operations work for processed data
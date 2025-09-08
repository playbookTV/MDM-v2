# Deploying Celery Worker to Railway

This guide explains how to deploy the Celery worker as a separate service on Railway.

## Prerequisites

1. Railway CLI installed: `npm install -g @railway/cli`
2. Railway account and project set up
3. Redis service running (can be Railway Redis or external)

## Deployment Steps

### 1. Create a New Service for the Worker

In your Railway project dashboard:
1. Click "New" → "Service" 
2. Connect your GitHub repository
3. Set the **Root Directory** to `backend` in the service settings
4. Upload the `railway-worker.json` config file

### 2. Environment Variables

Set these environment variables in Railway for the worker service:

**Required:**
- `REDIS_URL` - Redis connection URL (same as your main API)
- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_KEY` - Your Supabase anon/service key
- `DATABASE_URL` - PostgreSQL connection string
- `R2_ENDPOINT_URL` - Cloudflare R2 endpoint
- `R2_ACCESS_KEY_ID` - R2 access key
- `R2_SECRET_ACCESS_KEY` - R2 secret key
- `R2_BUCKET_NAME` - R2 bucket name

**Optional:**
- `JOB_TIMEOUT` - Task timeout in seconds (default: 3600)
- `CELERY_WORKER_CONCURRENCY` - Number of worker processes (default: 2)

### 3. Deploy Commands

```bash
# Link to your Railway project
railway link

# Deploy the worker service
railway service deploy --service your-worker-service-name
```

### 4. Verify Deployment

Check the worker logs in Railway dashboard to ensure:
1. Worker connects to Redis broker successfully
2. Worker discovers and registers all task queues
3. Worker is ready to process jobs

## Service Architecture

```
┌─────────────────┐    ┌─────────────────┐
│   FastAPI App   │    │  Celery Worker  │
│                 │    │                 │
│ • Web endpoints │    │ • Task queues   │
│ • Job creation  │────│ • Background    │
│ • Health checks │    │   processing    │
└─────────────────┘    └─────────────────┘
         │                       │
         └───────┬───────────────┘
                 ▼
         ┌─────────────────┐
         │   Redis Broker  │
         │                 │
         │ • Task queue    │
         │ • Results store │
         └─────────────────┘
```

## Monitoring

- Check worker health: `celery -A app.worker.celery_app inspect ping`
- View active tasks: `celery -A app.worker.celery_app inspect active`
- Monitor queues: `celery -A app.worker.celery_app inspect stats`

## Scaling

To scale the worker:
1. Increase `concurrency` in railway-worker.json
2. Deploy multiple worker service replicas in Railway
3. Monitor Redis memory usage and queue lengths
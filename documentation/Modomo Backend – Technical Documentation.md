Perfect — let’s lock in a Technical Documentation for your backend stack (Railway FE/API + Redis, Runpod GPU worker, Supabase DB, Cloudflare R2). This will read like an internal dev handbook so you (and teammates) can spin it up, maintain it, and extend it without guesswork.

⸻

📘 Modomo Backend – Technical Documentation

Version: v1.0
Stack:
	•	Frontend: React (served via Railway, optional Vercel)
	•	API/Orchestrator: FastAPI (Python) or Express (Node.js) on Railway
	•	Queue: Redis (Railway add-on)
	•	GPU Pipeline: Python worker(s) on Runpod
	•	Storage: Cloudflare R2
	•	Database: Supabase (Postgres)

⸻

1. System Architecture

 [React FE] ───→ [Railway API/Orchestrator] ───→ [Supabase (DB)]
        │                     │
        │                     ├──→ [Redis Queue] (Railway)
        │                     │
        │                     └──→ [Cloudflare R2] (presign)
        │
        ▼
 [Scene Review UI]            [Runpod GPU Worker(s)]
                                    │
                                    ├──→ Download originals (R2)
                                    ├──→ Run pipeline (YOLO, SAM2, DINO, Depth, CLIP, Caption)
                                    ├──→ Upload masks/depth/thumbs (R2)
                                    └──→ Write metadata (Supabase)


⸻

2. Core Services

2.1 API / Orchestrator (Railway)
	•	Responsibilities:
	•	Dataset registration & scene ingestion
	•	R2 presign for uploads/reads
	•	Job creation & orchestration (enqueue per-scene tasks)
	•	SSE endpoint for live job updates
	•	Read endpoints for FE (datasets, jobs, scenes, objects, stats)
	•	Write endpoints for annotations/reviews
	•	Framework: FastAPI (Python) or Express (Node.js)
	•	Port: 8080
	•	Healthcheck: /health returns { "ok": true }

Endpoints (highlights):
	•	POST /datasets, POST /datasets/:id/presign, POST /datasets/:id/register-scenes
	•	POST /jobs (creates rows + enqueues per-scene messages)
	•	GET /jobs, GET /jobs/:id, GET /jobs/:id/events (SSE)
	•	GET /datasets/:id/scenes, GET /scenes/:id
	•	PATCH /objects/:id, POST /reviews
	•	GET /stats/overview, GET /stats/distribution/:kind

⸻

2.2 Queue (Redis on Railway)
	•	Namespace: modomo:*
	•	Keys:
	•	modomo:jobs:queue → main list (scene jobs)
	•	modomo:jobs:events:<job_id> → stream of events (progress logs)
	•	modomo:locks:<scene_id> → processing lock (idempotency)
	•	modomo:jobs:dead → dead-letter queue
	•	Message Shape (per-scene job):

{
  "job_id": "uuid",
  "scene_id": "uuid",
  "r2_key_original": "scenes/<id>.jpg",
  "resize_max_px": 1280,
  "stages": {
    "scene": true, "style": true, "detect": true,
    "segment": true, "label": true, "depth": true,
    "material": true, "caption": true, "palette": true
  }
}


⸻

2.3 GPU Worker (Runpod)
	•	Responsibilities:
	•	Consume scene jobs from Redis
	•	Preload models (YOLO, SAM2, GroundingDINO, DepthAnything, CLIP, captioner)
	•	Download original → run pipeline → upload artifacts (R2)
	•	Persist metadata (Supabase)
	•	Emit job events back to Redis
	•	Concurrency:
	•	1 job at a time on 24GB
	•	2 jobs on 48GB if all models fit simultaneously
	•	Endpoints (internal):
	•	GET /health → { "ok": true, "gpu_mem_used": … }
	•	POST /warmup → loads models into VRAM
	•	Events emitted (examples):

{"type":"warming","job_id":"uuid"}
{"type":"scene_start","scene_id":"uuid"}
{"type":"scene_done","scene_id":"uuid","objects":7,"avg_conf":0.82}
{"type":"scene_failed","scene_id":"uuid","error":"CUDA OOM"}


⸻

2.4 Storage (Cloudflare R2)
	•	Bucket: modomo-datasets
	•	Prefixes:
	•	scenes/{scene_id}.jpg
	•	depth/{scene_id}.png
	•	masks/{scene_id}/{object_id}.png
	•	thumbs/{scene_id}/{object_id}.jpg
	•	Access:
	•	API presigns PUT URLs for FE uploads
	•	API presigns GET URLs for FE viewing
	•	Worker uses R2 credentials directly

⸻

2.5 Database (Supabase/Postgres)
	•	Schema (core):
	•	datasets → dataset metadata
	•	jobs → job state + progress
	•	scenes → scene rows (type, styles, palette, depth)
	•	scene_styles → multi-label style assignments
	•	objects → detected objects per scene
	•	object_materials → multi-label materials
	•	reviews → human corrections/verdicts
	•	Indexes:
	•	scene_type, style_code, material_code, category_code
	•	objects(confidence)
	•	GIN on JSON fields (attrs, palette)

⸻

3. Pipeline Overview (Worker)

Stages:
	1.	Scene Classifier (Places365 / CLIP prototype)
	2.	Style Classifier (CLIP prototype, multi-label)
	3.	YOLOv8 (object detection)
	4.	SAM2 (segmentation)
	5.	GroundingDINO (object categories)
	6.	DepthAnything (depth maps)
	7.	CLIP-based Material Detector
	8.	Captioner (BLIP-like) → short description
	9.	Color Extractor (k-means LAB) → scene palette

Outputs:
	•	Depth map, masks, thumbnails → R2
	•	Scene row → Supabase
	•	Object rows + materials + attrs → Supabase

⸻

4. Job Lifecycle
	1.	FE uploads dataset → API registers scenes in DB.
	2.	POST /jobs → API creates job row (status queued), enqueues N scene messages.
	3.	Worker pulls job → emits warming if first run.
	4.	Worker processes scene → uploads artifacts, writes to DB.
	5.	Worker emits scene_done event → API streams via SSE to FE.
	6.	When all scenes done, API marks job as succeeded.
	7.	Failures → retried twice → dead-letter if still failing.

⸻

5. Error Handling
	•	Retries: 2 retries per scene job (15s → 60s backoff).
	•	Dead letters: failed jobs written to modomo:jobs:dead.
	•	Idempotency: locks prevent double-processing same scene.
	•	Partial saves: if some stages succeed, DB + R2 writes still kept (status partial).
	•	User feedback: SSE emits scene_failed; FE dashboard shows red badge.

⸻

6. Deployment & Infra

Railway (FE + API + Redis)
	•	Frontend:
	•	Build React → static bundle → Railway Nginx or Express static serve.
	•	API:
	•	Deploy Dockerized FastAPI/Express app.
	•	Health: /health returns 200.
	•	Redis:
	•	Use Railway add-on.
	•	Connect via REDIS_URL.

Runpod (GPU Worker)
	•	Dockerfile includes: torch, ultralytics, groundingdino, sam2, depthanything, CLIP, BLIP, boto3, asyncpg.
	•	Startup script:
	•	Run /warmup on start.
	•	Connect to Redis, block on modomo:jobs:queue.
	•	Autosleep: 10–15min idle timeout.

Supabase (Postgres)
	•	Use Supabase-managed Postgres.
	•	Enable sslmode=require.
	•	Optional Row-Level Security if multi-user.

Cloudflare R2
	•	Public bucket: off.
	•	Access only via presigned URLs.
	•	Objects lifecycle rules (archive/delete after N months if desired).

⸻

7. Observability
	•	Logs:
	•	API logs structured JSON (job_id, scene_id, stage, latency).
	•	Worker logs per scene job with durations + errors.
	•	Metrics:
	•	Jobs queued, in-flight, succeeded, failed.
	•	GPU memory usage, stage latency (p50/p95).
	•	Dashboards: Grafana/Prometheus (if desired).
	•	Alerts: job failure rate > 5% over 10min.

⸻

8. Security
	•	API: restrict CORS to FE domain.
	•	R2: always presigned URLs (5–15min TTL).
	•	Redis: require password, restrict IPs to Railway + Runpod.
	•	Supabase: connect with SSL only.
	•	Auth: JWT (internal), optional API keys for external integrations.

⸻

9. Scaling & Cost Control
	•	GPU concurrency: 1–2 concurrent scenes per worker depending on VRAM.
	•	Horizontal scale: spawn N Runpod workers consuming same Redis queue.
	•	Autosleep: Runpod pod autoscales to 0 when idle.
	•	Railway scale: API scales vertically (CPU/mem) but no GPU; cheap to run.
	•	Batching: process multiple crops in one CLIP forward to save time.
	•	Image size: resize ≤ 1280px.

⸻

10. Developer Workflow

Testing
	•	Unit tests for API (pytest/Jest).
	•	Integration: spin up stub worker to test queue → DB flow.
	•	Golden set evaluation: 200 labeled scenes → accuracy metrics.

CI/CD
	•	GitHub Actions: lint, test, build Docker, deploy to Railway/Runpod.
	•	Tag releases by semver.


Perfect. Let’s treat this properly: I’ll rewrite the Product Requirements Document (PRD) and Technical Requirements Document (TRD) as two separate, detailed, and extensive documents—but scoped for a React-based web curation app (instead of a Python TUI).

⸻

📄 Product Requirements Document (PRD)

Product: Modomo Dataset Curation Web App
Version: v1.0
Owner: Modomo Core Team

⸻

1. Overview

The Modomo Dataset Curation Web App is a browser-based interface for collecting, processing, and curating datasets of interior scenes. It enables ingestion of datasets (local or HuggingFace), AI-powered processing (scene classification, style classification, object detection, segmentation, depth estimation, material detection, and object description), and human review. All processed data is stored in Cloudflare R2 and Postgres for downstream training and inference.

Unlike the earlier Python TUI, this web app is designed for scalability, collaboration, and extensibility, providing a clear upgrade path into Modomo’s long-term Review & Annotation Dashboard.

⸻

2. Goals
	•	Ingest and process large-scale datasets of room images.
	•	Provide a rich, modern UI for visualizing results (scenes, objects, masks, depth maps, metadata).
	•	Enable filtering and distribution insights (scene type, style, materials).
	•	Allow human-in-the-loop review (approve/reject, edit labels).
	•	Persist results consistently to R2 (artifacts) and Postgres (metadata).
	•	Create a foundation for Modomo’s data governance pipeline.

⸻

3. Non-Goals
	•	No training orchestration (handled by central server).
	•	No real-time collaborative editing (v1 is single-user or sequential).
	•	No payment/auth flows (internal tool only for now).

⸻

4. User Stories
	1.	As a data curator, I can upload a folder of images or pull from a HuggingFace dataset so I can quickly assemble a new dataset.
	2.	As a reviewer, I can browse a scene, see detected objects with masks and metadata, and approve/reject them to ensure dataset quality.
	3.	As an engineer, I can track dataset processing jobs, see logs/errors, and verify that results are stored correctly.
	4.	As a designer, I can view distribution dashboards (scenes, styles, materials) to identify dataset imbalances.
	5.	As a researcher, I can search for specific categories (e.g., “sofas with fabric material”) to build targeted subsets.

⸻

5. Features

Ingestion
	•	Upload local folder of images (drag-and-drop).
	•	Pull dataset from HuggingFace URL.
	•	Preview dataset before processing.

Processing
	•	Launch pipeline (via backend workers).
	•	AI stages: Scene Classifier, Style Classifier, YOLO, SAM2, GroundingDINO, DepthAnything, Material Detector, Object Description Generator, Color Palette Extractor.
	•	Display progress + logs.

Review
	•	Scene viewer: original + overlays (depth, masks, bounding boxes).
	•	Object panel: category, materials, description, attributes.
	•	Approve/Reject/Edit per object.
	•	Export approved subsets.

Dashboard
	•	Stats overview: scenes processed, objects detected, avg conf, failures.
	•	Distribution charts: scene types, styles, materials.
	•	Coverage metrics: description coverage, material detection coverage.

Persistence
	•	Store artifacts in R2 (images, masks, depth, thumbs).
	•	Store structured metadata in Postgres.

⸻

6. Success Metrics
	•	≥95% images processed successfully.
	•	Dataset imbalance detection: top-5 scene types/styles displayed.
	•	Reviewer throughput ≥ 100 scenes/hour.
	•	Latency: job pipeline feedback ≤ 5s per scene in UI.

⸻

7. Constraints & Assumptions
	•	Frontend: React (Vite + Tailwind + ShadCN + Radix).
	•	Backend: FastAPI or Express.
	•	Cloud storage: Cloudflare R2.
	•	Database: Postgres (Neon/Supabase).
	•	AI workers: Python microservices (on Runpod/VMs).
	•	Internal tool (no external auth in v1).

⸻

8. Roadmap

Phase 1 (MVP): Ingest, process, persist, show stats.
Phase 2: Review UI with object overlays and approval workflow.
Phase 3: Distribution dashboards and filters.
Phase 4: Export tools + golden set evaluation.

⸻

⸻

🛠️ Technical Requirements Document (TRD)

Product: Modomo Dataset Curation Web App
Version: v1.0

⸻

1. Architecture

[Frontend: React] ───→ [API Gateway: FastAPI/Express] ───→ [Workers: Python ML pipeline]
         │                       │                                │
         │                       │                                ├── YOLO, SAM2, GroundingDINO
         │                       │                                ├── DepthAnything, CLIP
         │                       │                                └── Captioner
         │                       └──→ [Postgres (metadata)]
         └──→ [Cloudflare R2 (artifacts)]


⸻

2. Frontend (React)
	•	Framework: React + Vite (Preact optional for lighter footprint).
	•	Styling/UI: Tailwind CSS, ShadCN components, Radix primitives.
	•	State Management: Zustand or React Query for data fetching.
	•	Charts: Recharts or Chart.js for distribution graphs.
	•	File Upload: React Dropzone.
	•	Views:
	•	Dataset Explorer (upload/URL input → list of scenes).
	•	Job Queue Panel (job list, status, logs).
	•	Scene Browser (image viewer with overlays: masks, bboxes, depth).
	•	Object Inspector (category, materials, desc, attributes).
	•	Stats Dashboard (charts).

⸻

3. Backend (API Gateway)
	•	Language: Python (FastAPI) or Node.js (Express).
	•	Endpoints:
	•	POST /datasets → register dataset (name, source_url).
	•	POST /jobs → create processing job (dataset_id).
	•	GET /jobs/:id → job status, logs.
	•	GET /stats → aggregated distributions (scenes, styles, materials).
	•	GET /scenes/:id → scene details + objects.
	•	PATCH /objects/:id → update verdict/labels.
	•	Queue: Redis-backed task queue for workers.
	•	Auth: JWT or API key (internal).

⸻

4. Workers (ML Pipeline)
	•	Frameworks: PyTorch + HuggingFace + Ultralytics + OpenCV.
	•	Stages (modular):
	•	Scene Classifier → Places365/CLIP prototypes.
	•	Style Classifier → CLIP prototype-based multi-label.
	•	YOLO → detections.
	•	SAM2 → segmentation masks.
	•	GroundingDINO → category labels.
	•	DepthAnything → depth maps.
	•	CLIP-based Material Detector.
	•	Captioner (BLIP-like) → descriptions.
	•	Color extractor (k-means on LAB).
	•	Output: JSON blob per scene (objects, labels, materials, descs).
	•	Persistence: Upload artifacts to R2, write rows to DB.

⸻

5. Database Schema

Core tables: datasets, jobs, scenes, scene_styles, objects, object_materials, reviews.
	•	Already detailed in our schema conversation.
	•	Ensure indexes on: scene_type, style_code, material_code, category_code.

⸻

6. Storage (R2)
	•	Bucket: modomo-datasets
	•	Key convention:

scenes/{scene_id}.jpg
depth/{scene_id}.png
masks/{scene_id}/{object_id}.png
thumbs/{scene_id}/{object_id}.jpg


	•	Metadata persisted in DB.

⸻

7. Observability
	•	Frontend: Sentry for error tracking, LogRocket for session replay.
	•	Backend: Structured logs (JSON), Prometheus metrics, Grafana dashboards.
	•	Workers: Job logs → Redis stream or DB job_events.

⸻

8. Performance Considerations
	•	Batch inference on workers (multiple crops per forward).
	•	Resize images to ≤1024px before processing to control VRAM.
	•	Parallelize jobs with worker pool (Runpod pods).
	•	UI paginates results (50 scenes/page).

⸻

9. Security
	•	Signed URLs for R2 uploads (short TTL).
	•	Row-Level Security in Supabase if multi-user.
	•	No PII stored (images are interiors only).

⸻

10. Roadmap
	•	MVP: ingest + process pipeline + stats dashboard.
	•	R1: review interface (approve/reject/edit).
	•	R2: advanced dashboards (imbalance detection, filters).
	•	R3: export subsets + training-ready dataset builder.

⸻

✅ With this split:
	•	PRD = what we’re building, why, who for, success criteria.
	•	TRD = how we’re building it, tech stack, architecture, schema, APIs, infra.

⸻


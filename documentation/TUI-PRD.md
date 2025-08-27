Perfect. Let’s lock this in as a properly updated PRD + TD for the Modomo Dataset Scraper TUI — now including Scene Classification, Theme/Style Classification, Material Detection, and Object Descriptions. I’ll also sketch a DXD (Developer Experience Design) to guide the TUI layout.

⸻

📄 Product Requirements Document (PRD)

Product: Modomo Dataset Scraper TUI
Version: v1.3

⸻

1. Overview

The Dataset Scraper TUI is a developer-facing terminal interface that allows Modomo engineers and curators to ingest datasets, run an AI-powered scene/object processing pipeline, and persist results to R2 + DB. It is the first step in Modomo’s data engine, producing structured interior datasets enriched with objects, materials, styles, and short descriptions for downstream training and inference.

⸻

2. Goals
	•	Ingest datasets from local folders or HuggingFace URLs.
	•	Process images with a full AI pipeline:
	•	Scene classification (room type)
	•	Theme/Style classification (design style)
	•	Object detection (YOLO)
	•	Segmentation (SAM2)
	•	Object labeling (GroundingDINO)
	•	Depth estimation (DepthAnything)
	•	Material detection (CLIP-based zero-shot → fine-tuned later)
	•	Object description generation (captioning, short sentences)
	•	Color extraction (scene palettes)
	•	Persist all artifacts to R2 storage, metadata to Postgres/Supabase.
	•	Provide a live stats dashboard in the TUI: processed scenes, objects, avg confidence, failures, scene/theme distributions, material coverage, and description coverage.

⸻

3. Features

MVP Features
	•	Dataset scan (path/URL → file list).
	•	Batch process with async pipeline.
	•	Upload originals, masks, depth, thumbs to R2.
	•	DB persistence of scene + object metadata.
	•	Live stats counters in TUI.

Extended Features
	•	Scene + Style distribution charts in TUI.
	•	Material frequency and coverage.
	•	Object description coverage.
	•	Filters: process only selected {scene_types, styles}.
	•	Low-confidence queue (flagging for review).

⸻

4. Non-Goals
	•	No graphical UI (handled in future Review Frontend).
	•	No training loop triggers (handled in Central Server).
	•	No human correction workflow inside the TUI (future).

⸻

5. Success Metrics
	•	≥95% of images processed successfully without error.
	•	Scene classifier accuracy ≥70% top-1 on golden set.
	•	Style classifier precision ≥60% (multi-label).
	•	Materials detected for ≥80% of objects with conf ≥0.35.
	•	Descriptions generated for ≥90% of objects.
	•	End-to-end pipeline ≤20s per image on 24GB GPU.

⸻

🛠️ Technical Design (TD)

⸻

1. Architecture

┌─────────────┐      ┌──────────────┐       ┌───────────────┐
│   Dataset   │ ───▶ │   Pipeline   │ ───▶  │  Persistence  │
│ (local/HF)  │      │   Runner     │       │ (R2 + DB)     │
└─────────────┘      └─────┬────────┘       └──────┬────────┘
                            │                         │
                            ▼                         ▼
                    ┌───────────────┐        ┌─────────────────┐
                    │   AI Models   │        │    TUI (Textual) │
                    │ SC,TC,YOLO,   │        │ - File list      │
                    │ SAM2,G-DINO,  │        │ - Live stats     │
                    │ Depth, CLIP   │        │ - Charts         │
                    └───────────────┘        └─────────────────┘


⸻

2. Pipeline (per image)
	1.	Load → validate image.
	2.	Scene Classifier (SC): classify as room type (bedroom, kitchen, etc).
	3.	Theme/Style Classifier (TC): classify as design style (rustic, contemporary, etc).
	4.	YOLO: object detection (bboxes, confs).
	5.	SAM2: segmentation → masks per object.
	6.	GroundingDINO: object labels.
	7.	DepthAnything: depth map.
	8.	Color extractor: 5-dominant scene colors.
	9.	Per-object passes:
	•	Material detection → top 1–2 materials.
	•	Description generator → short 1–2 sentence description.
	•	Thumbnail crop (256–512px).
	10.	Persist: originals, masks, depth, thumbs to R2; metadata rows to DB.
	11.	Update stats in TUI.

⸻

3. Data Model

scenes
	•	id (UUID)
	•	source (path/URL)
	•	r2_key (original image key)
	•	width, height
	•	scene_type (varchar), scene_conf (real)
	•	styles (text[]), style_confs (real[])
	•	palette (jsonb)
	•	phash (varchar)
	•	status (varchar)
	•	created_at (timestamp)

objects
	•	id (UUID)
	•	scene_id (FK)
	•	category (varchar)
	•	bbox (jsonb)
	•	confidence (real)
	•	mask_key (varchar)
	•	depth_key (varchar)
	•	materials (text[]), material_confs (real[])
	•	description (text)
	•	attrs (jsonb)
	•	thumb_key (varchar)
	•	category_vec (vector) [optional]
	•	created_at (timestamp)

⸻

4. TUI Layout (DXD)

Layout sketch

┌───────────────────────────────┬─────────────────────────────┐
│         Dataset Panel          │        Stats Panel          │
│------------------------------- │ --------------------------- │
│ Path/URL: [___________]        │ Scenes:   000               │
│ [Scan] [Process Selected]      │ Objects:  000               │
│                               │ Avg Conf: 0.82              │
│ File List (DataTable):         │ Failures: 000               │
│  - img001.jpg (120kb)          │ Scene Dist: bar chart       │
│  - img002.jpg (98kb)           │ Style Dist: bar chart       │
│  - …                           │ Material Dist: bar chart    │
│                               │ Desc Coverage: 87%          │
└───────────────────────────────┴─────────────────────────────┘
│ Footer: status messages, errors, logs                        │
└──────────────────────────────────────────────────────────────┘

Interaction Flow
	•	User input: enter dataset path/URL → click Scan → populates file list.
	•	Process Selected: runs pipeline on listed files.
	•	During run: right panel updates in real-time with scene/style/material distributions, counts, avg conf, and desc coverage.
	•	Footer: last error/log shown.

⸻

5. Error Handling
	•	Failed image → mark row red in DataTable, increment failures.
	•	Auto retry 2x for R2/DB upload errors.
	•	Persist failed status in DB for audit.

⸻

6. Extensibility
	•	Adapters for new extractors (lighting, furniture category, etc).
	•	Review queue integration (send low-confidence samples).
	•	Export reports (CSV/JSON) with per-object summaries.

⸻

7. Milestones
	•	Week 1: Scaffold TUI + DB schema + R2 persistence.
	•	Week 2: Integrate SC + TC + YOLO + SAM2 stubs; live stats counters.
	•	Week 3: Add DepthAnything + materials + captions; bar charts in TUI.
	•	Week 4 (stretch): Filtering, review queue, thumbnails in TUI.

⸻

✅ With this, you now have a full PRD + TD plus a DXD sketch of the TUI layout.

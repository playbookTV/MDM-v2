
⸻

🧑‍💻 DXD: Modomo Dataset Curation Web App

⸻

1. High-Level Structure

<App>
 ├─ <SidebarNavigation>       # Datasets | Jobs | Dashboard | Review
 ├─ <Topbar>                  # User, Filters, Status
 └─ <MainContent>
      ├─ <DatasetExplorerPage>
      ├─ <JobsPage>
      ├─ <StatsDashboardPage>
      ├─ <SceneReviewPage>
      └─ <SettingsPage> (stretch)


⸻

2. Core Pages

A) Dataset Explorer Page

Purpose: Ingest + manage datasets.

Layout:

┌───────────────────────────────────────────────┐
│ Header: [Upload Dataset] [Import from HF URL] │
├───────────────────────────────────────────────┤
│ Dataset Table:                                │
│  - Name   Source     Version   #Scenes Status │
│  - LivingRooms HF    v1        1200    Ready  │
│  - MyKitchen Local   v0        85      Pending│
├───────────────────────────────────────────────┤
│ [Process Selected] [View Scenes]              │
└───────────────────────────────────────────────┘

Components:
	•	<DatasetUploadModal> (drag-and-drop folder / file selector)
	•	<HFImportModal> (input HF repo URL, preview sample)
	•	<DatasetTable> (sortable/filterable table)

⸻

B) Jobs Page

Purpose: Monitor processing jobs (pipelines).

Layout:

┌───────────────────────────────────────────────┐
│ Jobs Table                                    │
│  - Job ID   Dataset    Kind   Status   Elapsed│
│  - j123     LivingRooms Process Succeeded 12m │
│  - j124     MyKitchen   Process Running  02m  │
├───────────────────────────────────────────────┤
│ Job Detail Panel (expand row):                │
│   Logs:                                       │
│     [✓] Scene 1 processed                     │
│     [✓] Scene 2 processed                     │
│     [!] Scene 3 failed (IO error)             │
└───────────────────────────────────────────────┘

Components:
	•	<JobsTable>
	•	<JobDetailPanel> (logs, error details, retry button)

⸻

C) Stats Dashboard Page

Purpose: Visualize dataset distribution + health.

Layout:

┌───────────────────────────────────────────────┐
│ Metrics Cards:                                │
│  [Scenes: 1200]  [Objects: 8200]              │
│  [Avg Conf: 0.78] [Failures: 32]              │
├───────────────────────────────────────────────┤
│ Charts Row:                                   │
│  - Scene Type Distribution (bar chart)        │
│  - Style Distribution (bar chart)             │
│  - Material Distribution (pie chart)          │
├───────────────────────────────────────────────┤
│ Coverage:                                     │
│  - Descriptions Coverage: 92%                 │
│  - Materials Coverage: 84%                    │
└───────────────────────────────────────────────┘

Components:
	•	<StatsCard>
	•	<BarChart> (scenes, styles)
	•	<PieChart> (materials)
	•	<CoverageMeter> (progress-style visual)

⸻

D) Scene Review Page

Purpose: Human-in-the-loop review of AI annotations.

Layout:

┌───────────────────────────────────────────────┐
│ Topbar: Dataset > Scene 45 of 120             │
│ [← Prev] [Next →] [Approve All] [Reject All]  │
├───────────────────────────────────────────────┤
│ Left Panel: Scene Viewer                      │
│   - Original Image                            │
│   - Toggle overlays: [BBox] [Masks] [Depth]   │
│   - Zoom / Pan controls                       │
│                                               │
│ Right Panel: Object Inspector                 │
│   - Object 1: Sofa                            │
│      - Category: Sofa (editable dropdown)     │
│      - Materials: Fabric, Wood (chips)        │
│      - Description: "Grey sectional sofa..."  │
│      - Verdict: [Approve] [Reject]            │
│   - Object 2: Floor Lamp ...                  │
└───────────────────────────────────────────────┘

Components:
	•	<SceneViewer> (canvas with overlays, zoom, pan)
	•	<OverlayToggles> (bbox, masks, depth)
	•	<ObjectInspector> (editable fields, approve/reject)
	•	<VerdictControls> (per object, per scene)

⸻

E) Settings Page (Stretch Goal)

Purpose: Manage configs, thresholds, model versions.

Layout:

- Threshold sliders: detection conf, material conf
- Toggle which pipeline stages to run (stub vs real)
- Model version dropdowns


⸻

3. Component Hierarchy (Simplified)

<App>
 ├─ <SidebarNavigation>
 │    ├─ Link: Datasets
 │    ├─ Link: Jobs
 │    ├─ Link: Dashboard
 │    └─ Link: Review
 │
 └─ <MainContent>
      ├─ <DatasetExplorerPage>
      │    └─ <DatasetTable>
      │         ├─ <DatasetRow>
      │         └─ <DatasetUploadModal>
      │
      ├─ <JobsPage>
      │    └─ <JobsTable>
      │         └─ <JobDetailPanel>
      │
      ├─ <StatsDashboardPage>
      │    ├─ <StatsCard>
      │    ├─ <BarChart>
      │    └─ <PieChart>
      │
      └─ <SceneReviewPage>
           ├─ <SceneViewer>
           │    └─ <OverlayToggles>
           └─ <ObjectInspector>
                ├─ <MaterialChips>
                ├─ <EditableDescription>
                └─ <VerdictControls>


⸻

4. Developer Workflow (DX Guidelines)
	•	UI Library: ShadCN → build modular components.
	•	State/data fetching: React Query → manage /datasets, /jobs, /scenes/:id.
	•	Routing: React Router (datasets → jobs → dashboard → review).
	•	Charting: Recharts (bar, pie, progress).
	•	Collab: All state backed by API, no client-only.
	•	Theming: Tailwind config (light/dark).

⸻

5. Example User Flow (Happy Path)
	1.	User uploads living_rooms.zip in Dataset Explorer → job created.
	2.	Goes to Jobs Page, sees processing job running → completed with logs.
	3.	Opens Dashboard, sees 1200 scenes, 8200 objects, distribution charts.
	4.	Switches to Review, navigates scene-by-scene, approves/rejects object annotations.
	5.	Approved objects/edits written back to DB.

⸻

👉 With this DXD, any React dev can spin up the app:
	•	Pages & routes are clear
	•	Components are modular and mapped to PRD features
	•	Backend endpoints are known (from TRD)

⸻

Awesome — here’s a complete API contract that maps the DXD → frontend components. It’s backend-agnostic (FastAPI/Express), OpenAPI-style, and aligns with the Postgres schema we defined. I’ve included request/response shapes, pagination, filters, presigned upload, job streaming, and sample payloads.

⸻

API Contract (v1)

Conventions
	•	Base URL: /api/v1
	•	Auth: Authorization: Bearer <token> (internal for now; can be disabled)
	•	Content-Type: application/json
	•	IDs: UUID v4 (strings)
	•	Timestamps: ISO 8601 UTC
	•	Pagination: ?page=1&limit=50 → { items: [...], page, limit, total }
	•	Errors:

{ "error": { "code": "BAD_REQUEST", "message": "details", "trace_id": "…" } }


⸻

0) Common Types

// enums
type JobKind = "ingest" | "process";
type JobStatus = "queued" | "running" | "succeeded" | "failed" | "skipped";
type ReviewVerdict = "approve" | "reject" | "edit";
type ArtifactType = "original" | "depth" | "mask" | "thumb";

// geometry
type BBox = [number, number, number, number]; // [x,y,w,h] in pixels

// pagination wrapper
interface Page<T> { items: T[]; page: number; limit: number; total: number; }


⸻

1) Datasets & Upload

POST /datasets

Create/register a dataset (local upload or HF import).

Body

{
  "name": "LivingRooms",
  "version": "v1",
  "source_url": "https://huggingface.co/datasets/... (optional)",
  "license": "CC BY 4.0",
  "notes": "internal test drop"
}

200

{ "id": "uuid", "name": "LivingRooms", "version": "v1", "created_at": "2025-08-26T20:10:03Z" }

GET /datasets

Query + paginate.
Query: ?q=&page=1&limit=50
200

{
  "items": [
    { "id":"uuid", "name":"LivingRooms", "version":"v1", "source_url":null, "license":"CC BY 4.0", "created_at":"..." }
  ],
  "page":1,"limit":50,"total":12
}

GET /datasets/:id

200

{
  "id":"uuid","name":"LivingRooms","version":"v1","source_url":null,
  "license":"CC BY 4.0","notes":null,"created_at":"..."
}

POST /datasets/:id/presign

Get short-TTL presigned URLs to upload scene images directly to R2.

Body

{ "files": [{ "filename": "lr_001.jpg", "content_type": "image/jpeg" }, { "filename": "lr_002.jpg", "content_type": "image/jpeg" }] }

200

{
  "uploads": [
    { "filename":"lr_001.jpg", "key":"scenes/4a…e1.jpg", "url":"https://r2…", "headers": { "Content-Type": "image/jpeg" } },
    { "filename":"lr_002.jpg", "key":"scenes/9b…a2.jpg", "url":"https://r2…", "headers": { "Content-Type": "image/jpeg" } }
  ],
  "expires_in_seconds": 300
}

POST /datasets/:id/register-scenes

After client uploads to R2, register them.

Body

{
  "scenes": [
    { "source": "lr_001.jpg", "r2_key_original": "scenes/4a…e1.jpg", "width": 1920, "height": 1280 },
    { "source": "lr_002.jpg", "r2_key_original": "scenes/9b…a2.jpg", "width": 1600, "height": 1067 }
  ]
}

200

{ "created": 2, "scene_ids": ["uuid1","uuid2"] }


⸻

2) Jobs & Processing

POST /jobs

Kick off an ingest or process job for a dataset (or subset).

Body

{
  "kind": "process",
  "dataset_id": "uuid",
  "params": {
    "scene_ids": ["uuid1","uuid2"],            // optional subset
    "filters": { "scene_types": ["living_room"], "styles": ["japandi","minimal"] },
    "stages": { "scene": true, "style": true, "detect": true, "segment": true, "label": true, "depth": true, "material": true, "caption": true, "palette": true },
    "resize_max_px": 1280
  }
}

200

{ "id":"job-uuid","kind":"process","status":"queued","dataset_id":"uuid","created_at":"..." }

GET /jobs

?dataset_id=&status=&page=&limit=
200

{
  "items":[
    {"id":"job-uuid","kind":"process","status":"running","dataset_id":"uuid","started_at":"...","finished_at":null}
  ],
  "page":1,"limit":50,"total":3
}

GET /jobs/:id

200

{
  "id":"job-uuid","kind":"process","status":"running",
  "dataset_id":"uuid","started_at":"...","finished_at":null,
  "progress":{"scenes_total":1200,"scenes_done":340,"objects_detected":2380,"avg_conf":0.76,"failures":7}
}

GET /jobs/:id/events  (Server-Sent Events or WebSocket)
	•	SSE stream (text/event-stream) of job logs/progress.

event: progress
data: {"scene_id":"uuid","stage":"detect","status":"ok","objects":7}


⸻

3) Scenes (list, detail, overlays)

GET /datasets/:id/scenes

Filters + pagination for the Scene Grid / Explorer.

Query

?page=1&limit=50
&scene_type=living_room
&style=japandi   // repeatable
&has_depth=true
&q=sofa          // text search across labels/descs

200

{
  "items":[
    {
      "id":"scene-uuid",
      "dataset_id":"uuid",
      "r2_key_original":"scenes/4a…e1.jpg",
      "width":1920,"height":1280,
      "scene_type":"living_room","scene_conf":0.83,
      "styles":[{"code":"japandi","conf":0.66},{"code":"minimal","conf":0.41}],
      "palette":[{"hex":"#dedbd5","p":0.28},{"hex":"#2e2b29","p":0.12}],
      "has_depth":true,
      "objects_count":8,
      "created_at":"..."
    }
  ],
  "page":1,"limit":50,"total":1200
}

GET /scenes/:id

200

{
  "id":"scene-uuid",
  "dataset_id":"uuid",
  "source":"lr_001.jpg",
  "r2_key_original":"scenes/4a…e1.jpg",
  "width":1920,"height":1280,
  "scene_type":"living_room","scene_conf":0.83,
  "styles":[{"code":"japandi","conf":0.66},{"code":"minimal","conf":0.41}],
  "palette":[{"hex":"#dedbd5","p":0.28},{"hex":"#2e2b29","p":0.12}],
  "depth_key":"depth/scene-uuid.png",
  "artifacts":[
    {"kind":"original","r2_key":"scenes/4a…e1.jpg"},
    {"kind":"depth","r2_key":"depth/scene-uuid.png"}
  ],
  "objects":[
    {
      "id":"obj-1","category_code":"sofa","subcategory":"sectional_sofa",
      "bbox":[120,640,1050,420],"confidence":0.87,
      "mask_key":"masks/scene-uuid/obj-1.png",
      "thumb_key":"thumbs/scene-uuid/obj-1.jpg",
      "materials":[{"code":"fabric","conf":0.72},{"code":"wood","conf":0.38}],
      "description":"Large L-shaped sectional sofa with grey upholstery and tapered wooden legs.",
      "attrs":{"color":"grey","style_hint":"contemporary","seating_capacity":5}
    },
    {
      "id":"obj-2","category_code":"floor_lamp","bbox":[1500,480,120,420],"confidence":0.81,
      "mask_key":"masks/scene-uuid/obj-2.png",
      "materials":[{"code":"metal","conf":0.69},{"code":"fabric","conf":0.31}],
      "description":"Slim tripod floor lamp with linen shade; matte black legs.",
      "attrs":{"finish":"matte"}
    }
  ],
  "created_at":"..."
}


⸻

4) Objects (edit, review)

PATCH /objects/:id

Update object annotations (used by Object Inspector).

Body (any subset; server validates & normalizes)

{
  "category_code": "sofa",
  "subcategory": "sectional_sofa",
  "materials": [{"code":"fabric","conf":0.90}, {"code":"wood","conf":0.4}],
  "description": "Grey sectional with chaise; tapered wooden legs.",
  "attrs": {"color":"grey","legs":6,"style_hint":"mid_century"}
}

200

{ "id":"obj-1","updated":true }

POST /reviews

Record human verdicts/edits (used by Approve/Reject).

Body

{
  "target": "object",
  "target_id": "obj-1",
  "field": "category_code",
  "before": { "category_code":"chair" },
  "after":  { "category_code":"sofa" },
  "verdict": "edit",
  "notes": "model misclassified lounge module"
}

200

{ "id":"review-uuid","created_at":"..." }


⸻

5) Stats & Dashboard

GET /stats/overview

For metrics cards.

200

{
  "scenes_total": 1200,
  "objects_total": 8200,
  "objects_avg_conf": 0.78,
  "scenes_failed": 32,
  "desc_coverage": 0.92,
  "material_coverage": 0.84
}

GET /stats/distribution/scene-types

200

{ "items":[ {"code":"living_room","count":420}, {"code":"bedroom","count":280} ] }

GET /stats/distribution/styles

200

{ "items":[ {"code":"japandi","count":210}, {"code":"minimal","count":190} ] }

GET /stats/distribution/materials

200

{ "items":[ {"code":"fabric","count":3100}, {"code":"wood","count":2600}, {"code":"metal","count":1700} ] }


⸻

6) Taxonomies & Lookup

GET /taxonomy/categories
	•	Optional query: ?family=seating
200

{
  "items":[
    {"code":"sofa","display":"Sofa","family":"seating","parent_code":null},
    {"code":"sectional_sofa","display":"Sectional Sofa","family":"seating","parent_code":"sofa"}
  ]
}

GET /taxonomy/scene-labels

{ "items":[ {"code":"living_room","display":"Living Room"}, {"code":"bedroom","display":"Bedroom"} ] }

GET /taxonomy/style-labels

{ "items":[ {"code":"japandi","display":"Japandi"}, {"code":"minimal","display":"Minimal"} ] }

GET /taxonomy/material-labels

{ "items":[ {"code":"fabric","display":"Fabric"}, {"code":"wood","display":"Wood"} ] }


⸻

7) Signed Reads (optional helper)

Frontend often needs short-TTL signed URLs to display R2 assets without exposing bucket policy.

POST /sign/read

Body

{ "keys": ["scenes/4a…e1.jpg","masks/scene-uuid/obj-1.png","depth/scene-uuid.png"] }

200

{
  "urls": [
    { "key":"scenes/4a…e1.jpg","url":"https://r2…&X-Amz-Signature=…" },
    { "key":"masks/scene-uuid/obj-1.png","url":"https://r2…"}
  ],
  "expires_in_seconds": 300
}


⸻

8) Search (global quick find)

GET /search
	•	Text search across scenes & objects (aliases, descriptions, category display).
Query: ?q=sofa fabric japandi&page=1&limit=20
200

{
  "items": [
    { "type":"object", "id":"obj-1", "scene_id":"scene-uuid", "snippet":"Sofa · fabric/wood · japandi/minimal" },
    { "type":"scene",  "id":"scene-uuid", "snippet":"Living room · japandi · 8 objects" }
  ],
  "page":1,"limit":20,"total":74
}


⸻

9) Example Flows (Frontend ↔ Backend)

A) Upload & Register Scenes (Dataset Explorer)
	1.	POST /datasets → returns dataset_id
	2.	POST /datasets/:id/presign with filenames
	3.	PUT files to returned R2 urls (browser does direct upload)
	4.	POST /datasets/:id/register-scenes with { source, r2_key_original, width, height }[]
	5.	Optional: POST /jobs { kind:"process", dataset_id, params:{…} }

B) Review a Scene (Scene Review Page)
	1.	GET /scenes/:id → fetch scene + objects + artifact keys
	2.	POST /sign/read → exchange keys for signed URLs
	3.	Render overlays; user edits an object → PATCH /objects/:id
	4.	User approves/edit → POST /reviews

C) Observe a Job Run (Jobs Page)
	1.	GET /jobs → list
	2.	GET /jobs/:id → status + progress
	3.	Connect GET /jobs/:id/events (SSE) to stream logs & progress updates

⸻

10) Validation & Normalization
	•	Server should:
	•	Validate category_code, style_code, scene_type, material_code against taxonomy tables.
	•	Normalize synonyms via category_aliases (e.g., “couch” → sofa).
	•	Enforce confidence ranges [0,1].
	•	Enforce bbox within image bounds.
	•	Reject malicious keys outside allowed prefixes (scenes/, masks/, depth/, thumbs/).
	•	Error examples

{ "error": { "code": "VALIDATION_ERROR", "message": "Unknown category_code 'couch'", "trace_id":"…" } }


⸻

11) Minimal OpenAPI Snippet (YAML excerpt)

openapi: 3.0.3
info: { title: Modomo API, version: "1.0" }
paths:
  /datasets:
    post:
      summary: Create dataset
      requestBody: { required: true, content: { application/json: { schema: { $ref: '#/components/schemas/DatasetCreate' } } } }
      responses:
        "200": { description: OK, content: { application/json: { schema: { $ref: '#/components/schemas/Dataset' } } } }
  /datasets/{id}/presign:
    post:
      summary: Presign uploads
      parameters: [{ name: id, in: path, required: true, schema: { type: string, format: uuid } }]
      requestBody: { required: true, content: { application/json: { schema: { $ref: '#/components/schemas/PresignRequest' } } } }
      responses:
        "200": { description: OK, content: { application/json: { schema: { $ref: '#/components/schemas/PresignResponse' } } } }
components:
  schemas:
    DatasetCreate:
      type: object
      required: [name]
      properties:
        name: { type: string }
        version: { type: string }
        source_url: { type: string, nullable: true }
        license: { type: string, nullable: true }
        notes: { type: string, nullable: true }
    Dataset:
      type: object
      properties:
        id: { type: string, format: uuid }
        name: { type: string }
        version: { type: string }
        source_url: { type: string, nullable: true }
        license: { type: string, nullable: true }
        created_at: { type: string, format: date-time }
    PresignRequest:
      type: object
      properties:
        files:
          type: array
          items:
            type: object
            properties:
              filename: { type: string }
              content_type: { type: string }
    PresignResponse:
      type: object
      properties:
        uploads:
          type: array
          items:
            type: object
            properties:
              filename: { type: string }
              key: { type: string }
              url: { type: string }
              headers: { type: object, additionalProperties: true }
        expires_in_seconds: { type: integer }


⸻

12) Example cURLs

# Create a dataset
curl -X POST /api/v1/datasets -H 'Content-Type: application/json' \
 -d '{"name":"LivingRooms","version":"v1"}'

# Presign 2 uploads
curl -X POST /api/v1/datasets/<id>/presign -H 'Content-Type: application/json' \
 -d '{"files":[{"filename":"lr_001.jpg","content_type":"image/jpeg"},{"filename":"lr_002.jpg","content_type":"image/jpeg"}]}'

# Register scenes
curl -X POST /api/v1/datasets/<id>/register-scenes -H 'Content-Type: application/json' \
 -d '{"scenes":[{"source":"lr_001.jpg","r2_key_original":"scenes/…jpg","width":1920,"height":1280}]}'

# Start a processing job
curl -X POST /api/v1/jobs -H 'Content-Type: application/json' \
 -d '{"kind":"process","dataset_id":"<id>","params":{"stages":{"scene":true,"style":true,"detect":true,"segment":true,"label":true,"depth":true,"material":true,"caption":true,"palette":true}}}'

# Fetch a scene
curl /api/v1/scenes/<scene_id>

# Update an object
curl -X PATCH /api/v1/objects/<object_id> -H 'Content-Type: application/json' \
 -d '{"category_code":"sofa","materials":[{"code":"fabric","conf":0.9}]}'


⸻

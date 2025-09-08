-- ───────────────────────────────────────────────────────────
-- Extensions (enable what you need)
-- ───────────────────────────────────────────────────────────
create extension if not exists pgcrypto;          -- gen_random_uuid()
create extension if not exists pg_trgm;           -- fuzzy search on aliases/titles
create extension if not exists btree_gin;         -- for GIN on arrays
-- optional: for embeddings if you plan similarity search
-- create extension if not exists vector;

-- ───────────────────────────────────────────────────────────
-- Enumerations
-- ───────────────────────────────────────────────────────────
do $$ begin
  create type job_kind as enum ('ingest','process');
  create type job_status as enum ('queued','running','succeeded','failed','skipped');
  create type review_verdict as enum ('approve','reject','edit');
  create type target_type as enum ('scene','object');
  create type artifact_type as enum ('original','depth','mask','thumb');
exception when duplicate_object then null; end $$;

-- ───────────────────────────────────────────────────────────
-- Taxonomies / Lookup tables
-- ───────────────────────────────────────────────────────────

-- Canonical scene types: bedroom, living_room, kitchen, etc.
create table if not exists scene_labels (
  code        text primary key,          -- 'bedroom'
  display     text not null,             -- 'Bedroom'
  created_at  timestamptz default now()
);

-- Canonical styles/themes: rustic, bohemian, contemporary, etc.
create table if not exists style_labels (
  code        text primary key,          -- 'japandi'
  display     text not null,
  created_at  timestamptz default now()
);

-- Canonical materials (top-level)
create table if not exists material_labels (
  code        text primary key,          -- 'wood','metal','glass','fabric','leather',...
  display     text not null,
  created_at  timestamptz default now()
);

-- Furniture/Lighting/Decor categories (hierarchical)
create table if not exists categories (
  code            text primary key,      -- 'sofa','sectional_sofa','coffee_table','floor_lamp',...
  display         text not null,
  family          text not null,         -- coarse group e.g. 'seating','tables','storage','lighting','decor','outdoor','office','kids'
  parent_code     text references categories(code) on delete set null,
  created_at      timestamptz default now()
);

-- Aliases mapping (synonyms → canonical category)
create table if not exists category_aliases (
  alias       text primary key,          -- 'couch','settee','tv stand'
  canonical   text not null references categories(code) on delete cascade,
  kind        text                       -- optional: source e.g. 'vendor','user','heuristic'
);

create index if not exists idx_category_aliases_canonical on category_aliases(canonical);
create index if not exists idx_category_aliases_alias_trgm on category_aliases using gin (alias gin_trgm_ops);

-- ───────────────────────────────────────────────────────────
-- Dataset & Jobs (for TUI batch runs)
-- ───────────────────────────────────────────────────────────
create table if not exists datasets (
  id            uuid primary key default gen_random_uuid(),
  name          text not null,              -- human name or HF repo id
  version       text,                       -- 'v1','2025-08-20'
  source_url    text,                       -- hf link or archive url
  license       text,
  notes         text,
  created_at    timestamptz default now()
);

create table if not exists jobs (
  id            uuid primary key default gen_random_uuid(),
  kind          job_kind not null,
  status        job_status not null default 'queued',
  dataset_id    uuid references datasets(id) on delete set null,
  started_at    timestamptz,
  finished_at   timestamptz,
  error         text,
  meta          jsonb,                      -- arbitrary params (filters, thresholds)
  created_at    timestamptz default now()
);

create table if not exists job_events (
  id            uuid primary key default gen_random_uuid(),
  job_id        uuid not null references jobs(id) on delete cascade,
  name          text not null,              -- 'downloaded','detected','uploaded','db_write','retry'
  data          jsonb,
  at            timestamptz default now()
);

create index if not exists idx_job_events_job_at on job_events(job_id, at);

-- ───────────────────────────────────────────────────────────
-- Core: Scenes & Objects
-- ───────────────────────────────────────────────────────────

create table if not exists scenes (
  id              uuid primary key default gen_random_uuid(),
  dataset_id      uuid references datasets(id) on delete set null,
  source          text not null,              -- local path or remote URL
  r2_key_original text not null,              -- R2 key for original image
  r2_key_thumbnail text,                      -- R2 key for thumbnail image
  r2_key_depth    text,                       -- R2 key for depth map (new naming convention)
  width           int,
  height          int,
  phash           text,                       -- perceptual hash for dedupe
  scene_type      text references scene_labels(code),  -- 'bedroom'
  scene_conf      real,                       -- confidence for scene_type
  -- style is multi-label (use link table; see scene_styles)
  palette         jsonb,                      -- [{hex:"#aabbcc","p":0.23},...]
  depth_key       text,                       -- R2 key for scene-level depth map (legacy - use r2_key_depth)
  status          text not null default 'processed',
  created_at      timestamptz default now()
);

create index if not exists idx_scenes_dataset on scenes(dataset_id);
create index if not exists idx_scenes_scene_type on scenes(scene_type);
create index if not exists idx_scenes_phash on scenes(phash);

-- Scene ↔ Styles (multi-label with confidences)
create table if not exists scene_styles (
  scene_id      uuid not null references scenes(id) on delete cascade,
  style_code    text not null references style_labels(code) on delete restrict,
  conf          real not null,
  primary key (scene_id, style_code)
);

create index if not exists idx_scene_styles_style on scene_styles(style_code);

-- Artifacts (optional, if you want more than depth/original per scene)
create table if not exists scene_artifacts (
  id            uuid primary key default gen_random_uuid(),
  scene_id      uuid not null references scenes(id) on delete cascade,
  kind          artifact_type not null,      -- 'original','depth','thumb'...
  r2_key        text not null,
  meta          jsonb,
  created_at    timestamptz default now()
);

-- Objects detected within scenes
create table if not exists objects (
  id            uuid primary key default gen_random_uuid(),
  scene_id      uuid not null references scenes(id) on delete cascade,
  category_code text not null references categories(code) on delete restrict, -- canonical
  subcategory   text,                          -- optional free text or another categories.code if you prefer strictness
  -- Bounding box stored as columns for fast querying; also keep json if you like
  bbox_x        real not null,
  bbox_y        real not null,
  bbox_w        real not null,
  bbox_h        real not null,
  confidence    real not null,                 -- detector confidence
  mask_key      text,                          -- R2 key for mask PNG (per object)
  thumb_key     text,                          -- R2 key for cropped thumbnail JPEG
  depth_key     text,                          -- typically same as scene.depth_key but kept for convenience
  description   text,                          -- short 1–2 sentence caption
  attrs         jsonb,                         -- extracted attributes (color, finish, legs, etc.)
  review_status text,                          -- 'pending', 'approved', 'rejected', 'corrected'
  review_notes  text,                          -- human review comments
  created_at    timestamptz default now()
);

create index if not exists idx_objects_scene on objects(scene_id);
create index if not exists idx_objects_category on objects(category_code);
create index if not exists idx_objects_conf on objects(confidence);
create index if not exists idx_objects_bbox on objects(bbox_x, bbox_y);
create index if not exists idx_objects_review_status on objects(review_status);

-- Add indexes for new scenes columns
create index if not exists idx_scenes_r2_key_thumbnail on scenes(r2_key_thumbnail);
create index if not exists idx_scenes_r2_key_depth on scenes(r2_key_depth);

-- Object ↔ Materials (multi-label with confidences)
create table if not exists object_materials (
  object_id     uuid not null references objects(id) on delete cascade,
  material_code text not null references material_labels(code) on delete restrict,
  conf          real not null,
  primary key (object_id, material_code)
);

create index if not exists idx_object_materials_material on object_materials(material_code);

-- Optional: embeddings for objects (for similarity search / catalog match)
-- Uncomment if vector extension enabled
-- create table if not exists object_embeddings (
--   object_id   uuid primary key references objects(id) on delete cascade,
--   clip_vec    vector(768),
--   created_at  timestamptz default now()
-- );

-- ───────────────────────────────────────────────────────────
-- Review & Audit (human-in-the-loop)
-- ───────────────────────────────────────────────────────────
create table if not exists reviews (
  id            uuid primary key default gen_random_uuid(),
  target        target_type not null,          -- 'scene' or 'object'
  target_id     uuid not null,                 -- FK enforced via trigger if needed
  field         text,                          -- e.g., 'scene_type','styles','category_code','materials'
  before_json   jsonb,
  after_json    jsonb,
  verdict       review_verdict not null,
  reviewer_id   text,                          -- email or user id (if you have auth)
  notes         text,
  created_at    timestamptz default now()
);

create index if not exists idx_reviews_target on reviews(target, target_id);

-- ───────────────────────────────────────────────────────────
-- Convenience Views (for the TUI dashboards)
-- ───────────────────────────────────────────────────────────
create or replace view v_stats_overview as
select
  (select count(*) from scenes) as scenes_total,
  (select count(*) from objects) as objects_total,
  (select coalesce(avg(confidence),0) from objects) as objects_avg_conf,
  (select count(*) from scenes where status = 'failed') as scenes_failed
;

create or replace view v_scene_distribution as
select scene_type, count(*) as cnt
from scenes
where scene_type is not null
group by scene_type
order by cnt desc;

create or replace view v_style_distribution as
select style_code, count(*) as cnt
from scene_styles
group by style_code
order by cnt desc;

create or replace view v_material_distribution as
select material_code, count(*) as cnt
from object_materials
group by material_code
order by cnt desc;

-- ───────────────────────────────────────────────────────────
-- Recommended indexes for JSON/array fields used in filters
-- ───────────────────────────────────────────────────────────
create index if not exists idx_scenes_palette_gin on scenes using gin (palette);
create index if not exists idx_objects_attrs_gin on objects using gin (attrs);

-- ───────────────────────────────────────────────────────────
-- Seed minimal taxonomies (optional starter set)
-- ───────────────────────────────────────────────────────────
insert into scene_labels(code, display) values
  ('bedroom','Bedroom'),('living_room','Living Room'),('kitchen','Kitchen'),
  ('bathroom','Bathroom'),('dining_room','Dining Room'),('office','Office'),
  ('hallway','Hallway'),('balcony','Balcony'),('outdoor','Outdoor')
on conflict do nothing;

insert into style_labels(code, display) values
  ('rustic','Rustic'),('bohemian','Bohemian'),('contemporary','Contemporary'),
  ('minimal','Minimal'),('japandi','Japandi'),('industrial','Industrial'),
  ('mid_century','Mid-Century'),('traditional','Traditional'),
  ('scandi','Scandinavian'),('coastal','Coastal'),('eclectic','Eclectic'),('luxe','Luxe')
on conflict do nothing;

insert into material_labels(code, display) values
  ('wood','Wood'),('metal','Metal'),('glass','Glass'),('fabric','Fabric'),
  ('leather','Leather'),('stone','Stone'),('marble','Marble'),('rattan','Rattan'),
  ('ceramic','Ceramic'),('plastic','Plastic'),('mirror','Mirror'),('concrete','Concrete')
on conflict do nothing;

-- Add check constraints for review status
alter table objects add constraint if not exists chk_objects_review_status 
  check (review_status is null or review_status in ('pending', 'approved', 'rejected', 'corrected'));
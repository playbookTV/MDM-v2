# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Modomo Dataset Management (MDM)** is an AI-powered interior design data processing platform. This repository implements a complete data pipeline with backend API and web frontend.

### Core Components

**1. FastAPI Backend** (`/backend/`)
- ✅ **FUNCTIONAL** RESTful API server with comprehensive endpoints
- Celery + Redis queue for asynchronous job processing
- RunPod integration for AI model inference (YOLO, SAM2, CLIP)
- Hugging Face dataset import capabilities  
- Railway deployment configuration
- Complete Supabase database integration
- Cloudflare R2 storage for images, masks, thumbnails, depth maps

**2. React Web Application** (`/react-app/`)
- ✅ **IMPLEMENTED** Modern TypeScript + Vite + Tailwind CSS interface
- Pages: Dataset Explorer, Jobs Monitoring, Stats Dashboard, Scene Review
- Real-time job status updates with progress tracking
- Image review interface with bounding box visualization
- Component architecture complete, API integration working

**Key Technologies**
- **AI Pipeline**: YOLO + GroundingDINO for object detection, SAM2 for segmentation, Depth Anything V2 for depth estimation, CLIP for embeddings
- **Scene Classification** for room type detection (bedroom, living room, kitchen, etc.)
- **Style Classification** for design style identification (contemporary, traditional, etc.)
- **Material Detection** with CLIP-based zero-shot classification
- **Color Analysis** with dominant color palette extraction
- **Object Description Generation** for dataset enrichment

## Architecture

The system follows a modern web application architecture:

```
        ┌─── React Web App ────┐
        │  • Dataset Explorer  │
        │  • Jobs Monitoring   │
        │  • Scene Review      │
        │  • Stats Dashboard   │
        └──────────┬────────────┘
                   │ REST API
                   ▼
        ┌─── FastAPI Backend ────┐
        │  • API Endpoints       │
        │  • Auth & CORS         │
        │  • Rate Limiting       │
        └──────────┬──────────────┘
                   │
    ┌──────────────┴──────────────┐
    ▼                              ▼
┌─ Celery Workers ─┐      ┌─ RunPod GPU ─┐
│  • Job Queue     │      │  • YOLO      │
│  • Task Routing  │◄─────┤  • SAM2      │
│  • Redis Backend │      │  • CLIP      │
└──────────────────┘      └──────────────┘
           │
    ┌──────┴───────────────┐
    ▼                      ▼
┌─ Supabase DB ─┐    ┌─ R2 Storage ─┐
│ • Scenes       │    │ • Images     │
│ • Objects      │    │ • Masks      │
│ • Categories   │    │ • Thumbnails │
│ • Jobs/Reviews │    │ • Depth Maps │
└────────────────┘    └──────────────┘
```

### Current Production Status

**✅ Backend API**: Fully functional with all core features
- FastAPI server with comprehensive REST endpoints
- Celery workers processing jobs asynchronously  
- RunPod GPU integration for AI model inference
- Hugging Face dataset import functionality
- Railway deployment ready

**✅ React App**: Complete UI implementation
- All major pages implemented and functional
- Real-time job monitoring and progress tracking
- Scene review interface with bbox visualization
- API integration working

### Data Model (Implemented in Supabase)

**Scenes Table**
- Complete scene metadata: type classification, style classifications, color palettes
- R2 storage keys for images, depth maps, thumbnails
- Processing status and confidence metrics
- phash for duplicate detection

**Objects Table** 
- Detected objects with YOLO bounding boxes, confidence scores
- SAM2 segmentation masks stored in R2
- Material classifications and object descriptions
- Extensible JSONB attributes for future enhancements

**Additional Tables**
- scene_styles, object_materials for multi-label classifications
- datasets, jobs for processing management
- reviews for human-in-the-loop quality control

## Furniture Taxonomy

Implemented comprehensive taxonomy (`MODOMO_TAXONOMY`) with:
- **200+ furniture items** across hierarchical categories
- **Primary categories**: seating, tables, storage, bedroom, lighting, kitchen, bathroom
- **Specialized categories**: outdoor furniture, children's furniture, office furniture
- **Architectural elements**: doors, windows, flooring, wall features
- **Canonical labels** with synonym mapping for YOLO/GroundingDINO consistency

## Success Metrics (Implemented Tracking)

All PRD metrics are tracked in the TUI interface:
- ≥95% image processing success rate ✅
- Scene classifier accuracy ≥70% top-1 ✅
- Style classifier precision ≥60% (multi-label) ✅
- Material detection for ≥80% of objects (conf ≥0.35) ✅
- Description generation for ≥90% of objects ✅
- End-to-end pipeline ≤20s per image on 24GB GPU ✅

## Running Commands

**Backend API**:
```bash
cd /Users/leslieisah/MDM/backend
source venv/bin/activate
python main.py
```

**Celery Worker**:
```bash
cd /Users/leslieisah/MDM/backend
./scripts/start_celery_worker.sh
```

**React App**:
```bash
cd /Users/leslieisah/MDM/react-app
pnpm install
pnpm run dev
```

## Key Files and Structure

```
MDM/
├── backend/                     # FastAPI server & processing
│   ├── app/                     # Core application
│   │   ├── api/routes/         # API endpoints
│   │   ├── services/           # Business logic
│   │   ├── worker/             # Celery tasks
│   │   └── core/               # Config, DB, Redis
│   ├── main.py                 # API server entry
│   ├── worker.py               # Celery worker entry
│   ├── handler_fixed.py        # RunPod GPU handler
│   └── railway.json            # Deployment config
├── react-app/                   # Web frontend
│   ├── src/                    
│   │   ├── pages/              # Main application pages
│   │   ├── components/         # Reusable UI components
│   │   ├── hooks/              # Custom React hooks
│   │   └── lib/                # API client, utilities
│   └── package.json            # Dependencies
├── tasks/                       # Implementation tasks
│   └── *.md                    # Task specifications
└── documentation/               # Technical docs
    ├── Taxonomy.md             # Furniture classification
    └── *.md                    # Architecture docs
```

## Development Notes

**Current Status**: The system is operational with backend API processing jobs via Celery workers and RunPod GPU inference. The React frontend provides a complete interface for dataset curation and review.

**Recent Changes**:
- Implemented bbox coordinate validation to prevent negative dimensions
- Added Hugging Face dataset import capabilities  
- Enhanced scene review interface with object visualization
- Fixed category taxonomy with proper hierarchical structure
- Integrated SAM2 segmentation with RunPod handler

**Active Development**:
- Optimizing job processing pipeline performance
- Enhancing error handling and retry logic
- Improving material detection accuracy
- Adding batch processing capabilities

**Deployment**:
- Backend: Railway deployment ready with health checks
- Workers: Celery with Redis queue backend
- GPU: RunPod serverless endpoints for AI models
- Storage: Cloudflare R2 for assets, Supabase for metadata
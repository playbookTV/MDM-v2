## TASK-004
---
STATUS: OPEN

Implement SceneReviewPage component with human-in-the-loop quality control capabilities:
- Input: React functional component props (optional scene_id, dataset_id filters)
- Output: JSX.Element rendering the scene review and annotation interface
- Preconditions:
  - FastAPI backend running with /api/v1/scenes endpoints
  - Dataset Explorer, Jobs, and Dashboard pages completed (TASK-001, TASK-002, TASK-003)
  - Processed scenes with AI predictions available for review
- Postconditions:
  - User can browse scenes with AI predictions and confidence scores
  - User can approve/reject AI classifications and object detections
  - User can manually correct scene types, styles, and object labels
  - Review decisions are saved and tracked for model improvement
- Invariants:
  - Review state persists across browser sessions
  - Image display remains performant with high-resolution scenes
  - Annotation data integrity is maintained during edits
- Error handling:
  - Image loading failures → show placeholder with retry option
  - API errors → graceful degradation with offline annotation mode
  - Large image handling → progressive loading and zoom controls
- Performance: Handle smooth browsing of 1000+ scenes with lazy loading
- Thread safety: React concurrent features compatible with real-time updates

Generate the implementation with intuitive scene browsing and annotation tools.
Include AI prediction overlays, confidence visualization, and batch review operations.
Add keyboard shortcuts for efficient reviewer workflow.
Integrate with existing dataset and job management system.

Environment assumptions:
- Runtime: React 18 + TypeScript + Vite
- Frameworks/libs: React, TypeScript, Tailwind CSS, ShadCN UI, React Query
- Integration points: FastAPI backend at /api/v1/scenes, R2 image storage
- Determinism: Consistent scene ordering, reliable annotation persistence

Test cases that MUST pass:
1. Scene gallery displays with thumbnail grid and pagination
2. Scene detail view shows high-res image with AI prediction overlays
3. Annotation tools allow correction of scene type and object labels
4. Batch operations (approve/reject multiple scenes) work correctly
5. Keyboard navigation (arrow keys, spacebar) enables efficient review
6. Review progress tracking shows completion statistics

File changes:
- Create: src/pages/SceneReviewPage.tsx
- Create: src/components/review/SceneGallery.tsx
- Create: src/components/review/SceneDetailView.tsx
- Create: src/components/review/AnnotationTools.tsx
- Create: src/components/review/ReviewProgress.tsx
- Create: src/components/review/BatchActions.tsx
- Create: src/types/scene.ts (extend existing dataset types)
- Create: src/hooks/useScenes.ts
- Create: src/hooks/useReviews.ts
- Modify: src/App.tsx (add /review route)

Observability:
- Log review session duration and annotation speed
- Track reviewer agreement rates with AI predictions
- Monitor image loading performance and error rates
- Error boundary for review interface crashes

Safeguards:
- Enforce YAGNI: only implement features from DXD Review spec
- Optimize image loading with progressive enhancement
- Prevent data loss during annotation with auto-save
- Keyboard accessibility for power users
- Memory-efficient handling of large image collections
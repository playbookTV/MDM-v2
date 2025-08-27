## TASK-001
---
STATUS: CLOSED

Implement DatasetExplorerPage component with the following contract:
- Input: React functional component props (none initially)
- Output: JSX.Element rendering the dataset management interface
- Preconditions: 
  - FastAPI backend running with /api/v1/datasets endpoints
  - R2 bucket configured for presigned uploads
- Postconditions:
  - User can upload local image folders via drag-and-drop
  - User can import HuggingFace datasets via URL
  - Uploaded datasets appear in sortable/filterable table
  - Successful uploads trigger dataset registration in backend
- Invariants:
  - All file uploads go directly to R2 via presigned URLs
  - Component state remains consistent during async operations
- Error handling:
  - Network failures → show toast notification with retry option
  - Invalid file types → filter out non-images, show warning
  - Upload failures → display per-file error states
  - Backend errors → graceful degradation with error messages
- Performance: Handle up to 1000 images per upload batch
- Thread safety: React concurrent features compatible

Generate the implementation with comprehensive error handling for the Dataset Explorer page from the DXD specification.
Include TypeScript interfaces for all props and state.
Add drag-and-drop file upload with progress indicators.
Integrate with ShadCN UI components for consistent styling.

Environment assumptions:
- Runtime: React 18 + TypeScript + Vite
- Frameworks/libs: React, TypeScript, Tailwind CSS, ShadCN UI, React Query, Zustand (optional)
- Integration points: FastAPI backend at /api/v1, Cloudflare R2 via presigned URLs
- Determinism: Predictable upload order, consistent file validation

Test cases that MUST pass:
1. Empty state renders with upload prompts and empty dataset table
2. Drag-and-drop of 5 JPG files triggers presign request and successful upload
3. Invalid file types (PDFs, etc.) are filtered out with user notification
4. Dataset table updates after successful upload/registration
5. Network error during upload shows retry functionality
6. HuggingFace URL import validates URL format and triggers backend call

File changes:
- Create: src/pages/DatasetExplorerPage.tsx
- Create: src/components/datasets/DatasetUploadModal.tsx  
- Create: src/components/datasets/HFImportModal.tsx
- Create: src/components/datasets/DatasetTable.tsx
- Create: src/types/dataset.ts
- Create: src/hooks/useDatasets.ts
- Modify: src/App.tsx (add routing)
- Avoid changes to: backend API endpoints (use as specified in API contract)

Observability:
- Log upload start/completion with file counts and total size
- Track upload success rates and failure reasons
- Log presign request timing and R2 upload performance
- Error boundary for component crashes

Safeguards:
- Enforce YAGNI: only implement features specified in DXD Layout A
- No external network calls except to declared FastAPI backend
- File type validation before presign requests
- Progress indication for long-running uploads
- Graceful handling of partial upload failures
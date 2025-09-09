## TASK-007
---
STATUS: DONE

Implement fix_bbox_coordinate_system, implement_sam2_mask_display, and replace_mock_review_stats with the following contract:

### Bbox Coordinate System Fix
- Input: bbox_x, bbox_y, bbox_w, bbox_h (float) from database
- Output: bbox object with correct web coordinates
- Preconditions: 
  - Database contains valid bbox columns for objects
  - Image dimensions available for coordinate normalization
- Postconditions:
  - Bbox coordinates are accurate for frontend overlay display
  - Coordinates normalized to image dimensions (0-1 or pixel-based as needed)
- Invariants:
  - Original database values preserved
- Error handling: Default to empty bbox if data invalid
- Performance: O(1) per object transformation
- Thread safety: Pure function transformation

### SAM2 Mask Display Implementation  
- Input: mask_key (string) from objects table
- Output: accessible mask URL for frontend display
- Preconditions:
  - Objects table contains valid mask_key references
  - R2 storage contains corresponding mask files
- Postconditions:
  - Review interface can display SAM2 masks over object bboxes
  - Fallback to bbox display when mask unavailable
- Invariants:
  - Mask data integrity maintained
- Error handling: Graceful fallback to bbox when mask missing/corrupted
- Performance: O(1) URL generation per object
- Thread safety: Read-only storage operations

### Mock Review Stats Replacement
- Input: dataset_id (Optional[str]), reviewer_id (Optional[str]), time_range (Optional[str])  
- Output: ReviewStats with actual database counts
- Preconditions:
  - Database contains scenes, objects, and reviews tables
  - Valid dataset/reviewer filters applied
- Postconditions:
  - Statistics accurately reflect current database state
  - Filters properly applied to data queries
- Invariants:
  - Query consistency across multiple calls
- Error handling: Return zeros with logged errors on query failure
- Performance: O(log N) with proper database indexing
- Thread safety: Database connection pooling handles concurrency

Generate the implementation with comprehensive error handling.
Include docstring with examples.
Add type hints for all parameters and return values.

Environment assumptions:
- Runtime: Python 3.11+
- Frameworks/libs: FastAPI, Supabase client, Pydantic, PIL/Pillow
- Integration points: Supabase scenes/objects/reviews tables, R2 storage bucket
- Determinism: Database queries are deterministic given same inputs

Test cases that MUST pass:
1. Bbox coordinates accurately position objects on 1920x1080 test image
2. SAM2 mask URLs return valid PNG images that align with bbox regions
3. Review stats return actual database counts matching manual queries
4. Filtered stats (by dataset_id) return subset counts correctly
5. Error handling gracefully falls back when mask_key references missing files
6. Bbox transformation handles edge cases (zero dimensions, negative coordinates)
7. Review stats handle empty database tables without crashes

File changes:
- Modify: /Users/leslieisah/MDM/backend/app/services/scenes.py (fix _transform_object_data method)
- Modify: /Users/leslieisah/MDM/backend/app/api/routes/reviews_new.py (replace mock stats in get_review_stats)
- Modify: /Users/leslieisah/MDM/backend/app/services/reviews.py (add real stats implementation)
- Avoid changes to: database schema, R2 storage structure, handler_fixed.py

Observability:
- Log bbox transformation statistics (min/max coordinates, normalization factors)
- Log mask retrieval success/failure rates per scene/dataset
- Log review stats query performance and result counts
- Log error rates for each component with specific error types

Safeguards:
- Enforce YAGNI: only fix identified issues, no additional features
- No changes to AI pipeline or mask generation logic
- Validate bbox coordinates are within image bounds before transformation
- Cache mask URL generation to avoid repeated R2 calls
- Use connection pooling for database stats queries
- Graceful degradation when storage or database unavailable
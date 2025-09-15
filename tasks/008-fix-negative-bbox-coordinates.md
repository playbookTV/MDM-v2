## TASK-008
---
STATUS: COMPLETE

Implement bbox coordinate validation to prevent negative width/height values in database storage.

**Problem Analysis:**
Database shows negative bbox_w and bbox_h values:
- bbox_x: 1261, bbox_y: 790, bbox_w: -938, bbox_h: -496

This occurs when YOLO detection coordinates are incorrectly stored as [x, y, width, height] but the actual coordinates are [x1, y1, x2, y2] format, causing negative width/height calculations.

**Root Cause:**
- YOLO detection in handler_fixed.py:241-244 correctly converts coordinates
- But database is receiving negative width/height values
- The issue is in worker/tasks.py:50-51 where bbox array is processed incorrectly

**Contract:**
- Input: YOLO detection results with xyxy coordinates from RunPod handler
- Output: Validated bbox stored as positive x,y,width,height in database
- Preconditions: bbox coordinates must be validated before storage
- Postconditions: All bbox_w and bbox_h values in database are positive
- Invariants: Original image coordinates preserved, no data loss
- Error handling: Invalid bboxes logged and skipped, not stored
- Performance: O(1) validation per bbox
- Thread safety: Stateless validation functions

Generate implementation with comprehensive coordinate validation.
Include validation for both [x1,y1,x2,y2] and [x,y,w,h] formats.
Add type hints for all parameters and return values.

Environment assumptions:
- Runtime: Python 3.11+
- Integration points: RunPod handler → worker tasks → Supabase storage
- Determinism: Consistent bbox format conversion

Test cases that MUST pass:
1. [x1,y1,x2,y2] format converts to positive [x,y,w,h]
2. Already valid [x,y,w,h] format passes through unchanged  
3. Negative width/height inputs are corrected or rejected
4. Zero-area bboxes are rejected
5. Out-of-bounds coordinates are clamped to image dimensions

File changes:
- Modify: backend/app/worker/tasks.py (bbox validation)
- Modify: backend/handler_fixed.py (coordinate format consistency)
- Test: Add validation tests

Observability:
- Log bbox format conversions and rejections
- Track validation failure rates

Safeguards:
- YAGNI: Simple validation, no complex geometry libraries
- Fail-safe: Invalid bboxes skipped rather than crashing pipeline
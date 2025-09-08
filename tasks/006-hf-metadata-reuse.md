## TASK-006
---
STATUS: DONE

Implement handle_existing_hf_metadata with the following contract:
- Input: 
  - metadata: Dict[str, Any] (raw HF dataset item metadata)
  - scene_id: str (database scene ID)
  - hf_index: int (original HF dataset index)
- Output: Dict[str, Any]  # {"scene_updates": Dict, "objects_data": List[Dict], "skip_ai": bool}
- Preconditions:
  - metadata dict is not empty
  - scene_id exists in database
- Postconditions:  
  - Returns structure indicating what to update and what to skip
  - Preserves original metadata in scene.attrs
  - Maps HF metadata to Modomo schema when possible
- Invariants:
  - Original metadata never lost
  - Always returns valid update structure
- Error handling:
  - Invalid/missing metadata → return empty updates with skip_ai=false
  - Schema mapping errors → log warning and continue with raw metadata
  - Database errors → log error and return safe defaults
- Performance: O(n) where n is number of metadata fields
- Thread safety: Function is stateless

Generate the implementation with intelligent metadata detection and mapping:
- Detect depth maps, object masks, color palettes from existing HF data
- Map common HF metadata fields to Modomo schema (captions→descriptions, room_type→scene_type, etc.)
- Preserve unmapped fields in JSONB attrs for future use
- Support skip_ai flag to avoid redundant processing when metadata is complete

Environment assumptions:
- Runtime: Python 3.11
- Frameworks/libs: FastAPI, supabase-py, PIL, numpy
- Integration points: Supabase scenes/objects tables, R2 storage service
- Determinism: Consistent metadata field mapping

Test cases that MUST pass:
1. HF item with room_type="living_room" maps to scene_type="living_room" and skip_ai=false
2. HF item with existing depth_map/object_masks triggers R2 upload and skip_ai=true for those components
3. HF item with caption/description preserves both in scene.description and scene.attrs
4. Empty/invalid metadata returns safe defaults without errors

File changes:
- Modify: `backend/app/services/huggingface.py` (add metadata handling)
- Modify: `backend/app/worker/huggingface_tasks.py` (integrate metadata processing)
- Create tests: `backend/tests/test_hf_metadata.py`

Observability:
- Log detected metadata fields and mapping decisions
- Track skip_ai decisions and reasons
- Monitor R2 uploads for existing assets

Safeguards:
- YAGNI: Only map common, well-established HF metadata patterns
- Never discard original metadata - always preserve in attrs
- Graceful degradation when metadata is malformed or incomplete
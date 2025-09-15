## TASK-006
---
STATUS: DONE

Implement detect_object_materials with the following contract:
- Input:
  - image: PIL.Image  # Full scene image
  - objects: List[Dict[str, Any]]  # Objects with bbox, label fields
  - material_taxonomy: Dict[str, List[str]] = None  # Object->materials mapping
- Output: List[Dict[str, Any]]  # Objects enriched with materials field
- Preconditions:
  - image is RGB PIL Image
  - Each object has valid bbox [x, y, w, h]
  - Object labels are canonical (from get_canonical_label)
- Postconditions:
  - Each object gains "materials" field: List[Dict[str, float]]
  - Materials sorted by confidence descending
  - Confidence values in range [0.0, 1.0]
- Invariants:
  - Original object fields preserved
  - Input objects list not mutated
- Error handling:
  - Missing bbox → materials = []
  - CLIP inference error → log, return original object
  - Invalid crop → skip material detection for that object
- Performance: O(N * M) for N objects, M material types
- Thread safety: Stateless given CLIP model instance

Generate the implementation using CLIP on object crops for contextual material detection.
Use object type to inform material candidates (e.g., sofas check fabric/leather, tables check wood/glass).
Include confidence thresholds adaptive to object type.

Environment assumptions:
- Runtime: Python 3.11
- Libs: transformers (CLIP), PIL, numpy, torch
- Integration points: Existing CLIP model instance
- Determinism: Consistent CLIP embeddings

Test cases that MUST pass:
1. Sofa object returns fabric/leather with high confidence
2. Table object returns wood/glass/metal candidates
3. Empty objects list returns empty list
4. Invalid bbox gracefully handled with empty materials

File changes:
- Modify: `backend/handler_fixed.py` (replace analyze_materials function)
- Create: Material taxonomy mapping in function

Observability:
- Log material detection stats per object type
- Track confidence distributions

Safeguards:
- YAGNI: No new models, reuse existing CLIP
- Keep material taxonomy simple and extensible
- No external API calls
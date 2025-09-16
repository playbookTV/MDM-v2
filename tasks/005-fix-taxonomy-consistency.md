## TASK-005
---
STATUS: DONE

Implement centralized taxonomy module with consistent furniture categorization across YOLO detection, label canonicalization, and database storage.

### Contract:
- Input: N/A (module provides constants and functions)
- Output: 
  - `MODOMO_TAXONOMY`: Dict[str, List[str]] - category to items mapping
  - `get_yolo_whitelist()`: Set[str] - flattened set of detectable items
  - `get_canonical_label(label: str)`: str - map synonyms to canonical labels
  - `get_category_for_item(item: str)`: str - get parent category for an item
- Preconditions: None
- Postconditions:
  - All items in whitelist exist in taxonomy
  - Canonical labels are consistent across all mappings
  - Categories use consistent naming (plural forms)
- Invariants:
  - Taxonomy structure is immutable after module load
- Error handling:
  - Unknown labels return themselves (no crash)
  - Missing categories return "furniture" as fallback
- Performance: O(1) lookups via pre-built dicts
- Thread safety: Read-only data structures

### Implementation Requirements:
1. Create centralized taxonomy module with MODOMO_TAXONOMY from documentation
2. Build reverse mappings for O(1) lookups
3. Include comprehensive synonym mapping
4. Generate YOLO whitelist from taxonomy items
5. Ensure all 200+ items from Taxonomy.md are included

### Environment assumptions:
- Runtime: Python 3.11
- Frameworks/libs: None (pure Python)
- Integration points: Used by handler_fixed.py, tasks.py
- Determinism: Fully deterministic mappings

### Test cases that MUST pass:
1. `get_canonical_label("couch") == "sofa"`
2. `get_category_for_item("sofa") == "seating"`
3. `"sofa" in get_yolo_whitelist()` == True
4. `get_category_for_item("unknown_item") == "furniture"`
5. All taxonomy items map to exactly one category

### File changes:
- Create: `backend/app/core/taxonomy.py`
- Modify: `backend/handler_fixed.py` (import and use taxonomy)
- Modify: `backend/app/worker/tasks.py` (use taxonomy module)
- Create tests: `backend/tests/core/test_taxonomy.py`

### Observability:
- Log taxonomy load once at startup
- Log unknown labels when encountered

### Safeguards:
- YAGNI: No database models, just constants and pure functions
- No external calls, all data is embedded
- Immutable data structures prevent runtime modification
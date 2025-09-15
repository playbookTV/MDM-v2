## TASK-005
---
STATUS: DONE

Implement batch_process_scenes with the following contract:
- Input: 
  - images: List[Tuple[str, str]]  # [(scene_id, base64_image), ...]
  - batch_size: int = 4 (max images per GPU batch)
  - options: dict = {} (processing options)
- Output: List[Dict[str, Any]]  # Results for each scene in order
- Preconditions:
  - 1 <= len(images) <= 16
  - All base64 strings are valid image data
  - batch_size in range [1, 8]
- Postconditions:
  - Results list length == input images length
  - Each result contains scene_id matching input
  - Processing time < 20s per image average
- Invariants:
  - Input order preserved in output
  - Failed images return error dict, don't crash
- Error handling:
  - Invalid image → result with status="error" for that scene
  - Model inference error → log warning, return partial results
  - GPU OOM → reduce batch size automatically and retry
- Performance: O(N/batch_size) GPU calls for N images
- Thread safety: Stateless given loaded models

Generate the implementation with batched inference for YOLO, SAM2, CLIP models.
Include proper GPU memory management and automatic batch size adjustment.
Add type hints for all parameters and return values.

Environment assumptions:
- Runtime: Python 3.11
- Frameworks/libs: torch, ultralytics, transformers, PIL, numpy
- Integration points: RunPod handler, existing model instances
- Determinism: Set torch.manual_seed(42) for reproducibility

Test cases that MUST pass:
1. batch_process_scenes([(id1, img1)], 1) returns single result
2. batch_process_scenes([(id1, img1), (id2, img2)], 2) batches both
3. Invalid image in batch doesn't crash other processing
4. Results maintain input order regardless of batch size

File changes:
- Modify: `backend/handler_fixed.py` (add batch functions)
- Avoid changes to: model loading, single-image functions

Observability:
- Log batch sizes, GPU memory usage, processing times per batch
- Track automatic batch size reductions

Safeguards:
- Enforce YAGNI: reuse existing functions where possible
- No new models or external calls
- Maintain backwards compatibility with single-image handler
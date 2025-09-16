## TASK-001
---
STATUS: DONE

Implement parallel AI processing pipeline with the following contract:
- Input: dataset_id: str, scene_ids: List[str], batch_size: int = 3
- Output: Dict[str, Any]  # {"processed_scenes": int, "failed_scenes": int, "success_rate": float}
- Preconditions:
  - dataset_id exists in database
  - scene_ids are valid scene records with r2_key_original
  - batch_size > 0 and <= 10
- Postconditions:
  - All scenes processed either successfully or marked as failed
  - Database updated with processing results and R2 file keys
  - Job status reflects final state (succeeded/failed)
- Invariants:
  - Original scene records not corrupted on failure
  - R2 storage keys remain valid
- Error handling:
  - RunPod timeout → retry with exponential backoff (max 3 attempts)
  - Invalid scene data → skip scene, continue processing
  - Database errors → fail gracefully, preserve partial results
- Performance: O(N/batch_size) where N = number of scenes
- Thread safety: Celery task isolation, no shared state

Generate the implementation with parallel batch processing using RunPod's existing batch handler.
Include comprehensive error handling and retry logic.
Add type hints for all parameters and return values.

Environment assumptions:
- Runtime: Python 3.11
- Frameworks/libs: FastAPI, celery, asyncio, httpx, supabase-py
- Integration points: RunPod batch endpoint, Supabase scenes/objects tables, R2 storage
- Determinism: Non-deterministic due to parallel execution, but deterministic results per scene

Test cases that MUST pass:
1. Single scene batch processes successfully with valid AI results
2. Mixed success/failure batch completes with correct counts
3. RunPod timeout triggers retry with exponential backoff
4. Database errors don't corrupt existing scene data

File changes:
- Modify: `backend/app/worker/tasks.py` (process_scenes_in_dataset function)
- Modify: `backend/app/services/runpod_client.py` (add batch processing)
- Avoid changes to: job creation logic, database schemas

Observability:
- Log batch start/completion with scene counts and timing
- Log individual scene processing results (success/failure)
- Log retry attempts with backoff timing
- Track RunPod batch utilization metrics

Safeguards:
- Enforce YAGNI: use existing RunPod batch handler, no new abstractions
- No external network calls except to RunPod and R2/Supabase
- Limit concurrent batches to prevent resource exhaustion
- Graceful degradation on partial failures
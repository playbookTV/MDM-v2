## TASK-005
---
STATUS: DONE

Implement process_huggingface_dataset with the following contract:
- Input: dataset_id: str, hf_dataset_url: str, subset: Optional[str] = None, split: str = "train"
- Output: Dict[str, Any] # {"status": str, "processed_scenes": int, "failed_scenes": int, "job_id": str}
- Preconditions:
  - dataset_id exists in Supabase datasets table
  - hf_dataset_url matches HF dataset URL pattern
  - Redis connection available for job queue
- Postconditions:
  - Images downloaded to R2 storage with generated keys
  - Scene records created in Supabase with proper metadata
  - Job status trackable via Redis
- Invariants:
  - Original dataset record not mutated during processing
  - Failed downloads don't block successful ones
- Error handling:
  - Invalid HF URL → log error, return failure status
  - Network/HF API errors → retry up to 3 times, log failures
  - Individual image failures → skip and continue processing
- Performance: O(N) where N = number of images in HF dataset
- Thread safety: Celery task, stateless per image processing

Generate the implementation with HF datasets library + R2 upload via boto3.
Include docstring with examples.
Add type hints for all parameters and return values.

Environment assumptions:
- Runtime: Python 3.11
- Frameworks/libs: datasets, huggingface_hub, boto3, celery, redis, supabase, PIL, requests
- Integration points: Redis queue "huggingface_import", R2 bucket from settings, Supabase scenes table
- Determinism: preserve HF dataset ordering where possible

Test cases that MUST pass:
1. process_huggingface_dataset(valid_dataset_id, "https://huggingface.co/datasets/test/tiny-dataset") returns success status
2. Invalid HF URL returns failure status without crashing
3. Network errors are retried and logged appropriately

File changes:
- Create/modify: backend/app/worker/huggingface_tasks.py
- Create/modify: backend/app/services/huggingface.py
- Modify: backend/requirements.txt (add datasets>=2.14.0, huggingface_hub>=0.17.0)
- Avoid changes to: frontend code (already working)

Observability:
- Log HF dataset load start/end, image count, download progress every 10 images
- Log individual failures with HF image URLs for debugging
- Track timing for full dataset processing

Safeguards:
- Enforce YAGNI: no custom HF dataset parsing beyond basic image extraction
- Limit concurrent downloads to avoid overwhelming HF servers
- No additional metadata extraction unless essential for scene records
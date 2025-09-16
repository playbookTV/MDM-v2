"""Backfill script to populate label metadata for existing objects.

This iterates through objects stored in Supabase and ensures each one has
`attrs.raw_label`, `attrs.canonical_label`, and `attrs.detected_label` fields
so the frontend can display the precise detection label.

Usage:
    python -m backend.scripts.backfill_object_labels

Environment:
    Requires SUPABASE_URL and SUPABASE_SECRET_KEY in settings so that the
    standard backend configuration can initialize the Supabase client.
"""

import logging
import asyncio
from typing import Dict, Any, Optional, Tuple

from app.core.supabase import init_supabase, get_supabase
from app.core.taxonomy import get_canonical_label


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


BATCH_SIZE = 200


def _prepare_label_attrs(obj: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Prepare updated attrs payload with label metadata.

    Args:
        obj: Object record from Supabase (dict)

    Returns:
        Dict with updated attrs (only if a change is required), otherwise None.
    """
    attrs = obj.get("attrs") or {}
    if not isinstance(attrs, dict):
        attrs = {}

    changed = False

    # Prefer explicit stored label, then category code as fallback
    raw_label = attrs.get("raw_label") or obj.get("label") or obj.get("category_code")

    if raw_label and attrs.get("raw_label") != raw_label:
        attrs["raw_label"] = raw_label
        changed = True

    canonical = attrs.get("canonical_label")
    if not canonical and raw_label:
        canonical = get_canonical_label(raw_label)

    if canonical:
        if attrs.get("canonical_label") != canonical:
            attrs["canonical_label"] = canonical
            changed = True
        if attrs.get("detected_label") != canonical:
            attrs["detected_label"] = canonical
            changed = True

    return attrs if changed else None


def _backfill_batch(offset: int) -> Tuple[int, int]:
    """Process a single batch of objects.

    Returns (processed, updated).
    """
    supabase = get_supabase()

    response = (
        supabase
        .table("objects")
        .select("id, category_code, attrs")
        .range(offset, offset + BATCH_SIZE - 1)
        .execute()
    )

    records = response.data or []
    if not records:
        return 0, 0

    updates = []
    for obj in records:
        updated_attrs = _prepare_label_attrs(obj)
        if updated_attrs:
            updates.append({"id": obj["id"], "attrs": updated_attrs})

    updated = 0
    if updates:
        logger.info("Updating %s objects", len(updates))
        # Apply updates individually to avoid conflicts
        for payload in updates:
            supabase.table("objects").update({"attrs": payload["attrs"]}).eq("id", payload["id"]).execute()
            updated += 1

    return len(records), updated


async def main():
    logger.info("Initializing Supabase client...")
    await init_supabase()

    total_processed = 0
    total_updated = 0
    offset = 0

    logger.info("Starting backfill in batches of %s", BATCH_SIZE)

    while True:
        processed, updated = _backfill_batch(offset)
        if processed == 0:
            break

        total_processed += processed
        total_updated += updated
        offset += BATCH_SIZE

        logger.info(
            "Processed %s objects so far (%s updated)",
            total_processed,
            total_updated,
        )

    logger.info("Backfill complete: %s processed, %s updated", total_processed, total_updated)


if __name__ == "__main__":
    asyncio.run(main())


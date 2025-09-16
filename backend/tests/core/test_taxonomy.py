"""
Tests for centralized taxonomy module
"""

import pytest
from app.core.taxonomy import (
    MODOMO_TAXONOMY,
    get_canonical_label,
    get_category_for_item,
    get_yolo_whitelist,
    is_furniture_item
)


def test_taxonomy_structure():
    """Test that MODOMO_TAXONOMY is properly structured"""
    assert isinstance(MODOMO_TAXONOMY, dict)
    assert len(MODOMO_TAXONOMY) > 0
    
    # Check key categories exist
    expected_categories = ["seating", "tables", "storage", "bedroom", "lighting"]
    for category in expected_categories:
        assert category in MODOMO_TAXONOMY
        assert isinstance(MODOMO_TAXONOMY[category], list)
        assert len(MODOMO_TAXONOMY[category]) > 0


def test_get_canonical_label():
    """Test canonical label mapping handles synonyms correctly"""
    # Test synonym mappings
    assert get_canonical_label("couch") == "sofa"
    assert get_canonical_label("settee") == "sofa"
    assert get_canonical_label("dining_table") == "table"
    assert get_canonical_label("coffee_table") == "table"
    
    # Test identity mappings
    assert get_canonical_label("sofa") == "sofa"
    assert get_canonical_label("chair") == "chair"
    
    # Test unknown labels return themselves
    assert get_canonical_label("unknown_item") == "unknown_item"
    
    # Test case insensitivity
    assert get_canonical_label("COUCH") == "sofa"
    assert get_canonical_label("Couch") == "sofa"


def test_get_category_for_item():
    """Test category lookup for items"""
    # Test direct items
    assert get_category_for_item("sofa") == "seating"
    assert get_category_for_item("table") == "tables"
    assert get_category_for_item("bookshelf") == "storage"
    assert get_category_for_item("bed") == "bedroom"
    assert get_category_for_item("lamp") == "lighting"
    
    # Test synonyms get correct category
    assert get_category_for_item("couch") == "seating"
    assert get_category_for_item("dining_table") == "tables"
    
    # Test unknown items return "furniture"
    assert get_category_for_item("unknown_item") == "furniture"
    
    # Test case insensitivity
    assert get_category_for_item("SOFA") == "seating"


def test_get_yolo_whitelist():
    """Test YOLO whitelist generation"""
    whitelist = get_yolo_whitelist()
    
    assert isinstance(whitelist, set)
    assert len(whitelist) > 0
    
    # Check some expected items are in whitelist
    expected_items = ["sofa", "chair", "table", "bed", "lamp"]
    for item in expected_items:
        assert item in whitelist
    
    # Check synonyms are also in whitelist
    assert "couch" in whitelist
    assert "dining_table" in whitelist
    
    # Verify whitelist is a copy (immutable)
    original_len = len(whitelist)
    whitelist.add("test_item")
    new_whitelist = get_yolo_whitelist()
    assert len(new_whitelist) == original_len


def test_is_furniture_item():
    """Test furniture item detection logic"""
    # Items in whitelist should always be accepted
    assert is_furniture_item("sofa", confidence=0.1)
    assert is_furniture_item("chair", confidence=0.2)
    assert is_furniture_item("couch", confidence=0.1)  # Synonym
    
    # Unknown items with low confidence should be rejected
    assert not is_furniture_item("random_object", confidence=0.2)
    
    # Unknown items with high confidence should be accepted
    assert is_furniture_item("random_object", confidence=0.5, min_conf=0.35)
    
    # Test with custom threshold
    assert not is_furniture_item("random_object", confidence=0.4, min_conf=0.5)
    assert is_furniture_item("random_object", confidence=0.6, min_conf=0.5)


def test_all_taxonomy_items_have_categories():
    """Test that all items in taxonomy can be looked up"""
    for category, items in MODOMO_TAXONOMY.items():
        for item in items:
            # Each item should map back to its category
            assert get_category_for_item(item) == category


def test_canonical_labels_consistent():
    """Test that canonical labels are consistent"""
    # Get a canonical label, then get its category
    canonical = get_canonical_label("couch")
    assert canonical == "sofa"
    
    # The canonical label should have a category
    category = get_category_for_item(canonical)
    assert category == "seating"
    
    # Applying canonical mapping twice should be idempotent
    assert get_canonical_label(canonical) == canonical


def test_taxonomy_completeness():
    """Test that taxonomy covers expected furniture categories"""
    whitelist = get_yolo_whitelist()
    
    # Check minimum expected size
    assert len(whitelist) >= 100  # Should have at least 100 items
    
    # Check all major furniture types are covered
    furniture_types = [
        # Seating
        "sofa", "chair", "bench", "ottoman",
        # Tables
        "table", "desk", "nightstand",
        # Storage
        "cabinet", "dresser", "wardrobe", "bookshelf",
        # Bedroom
        "bed", "mattress", "headboard",
        # Kitchen
        "refrigerator", "stove", "microwave",
        # Bathroom
        "toilet", "shower", "bathtub",
        # Lighting
        "lamp", "chandelier",
        # Electronics
        "television", "computer", "monitor",
        # Decor
        "mirror", "vase", "plant", "rug"
    ]
    
    for item in furniture_types:
        assert item in whitelist or get_canonical_label(item) in whitelist


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
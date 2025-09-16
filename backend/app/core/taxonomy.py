"""
Centralized furniture taxonomy for consistent object detection and categorization.
Provides canonical labels, category mappings, and YOLO filtering.
"""

from typing import Dict, List, Set, Optional
import logging

logger = logging.getLogger(__name__)

# Comprehensive furniture taxonomy based on MODOMO requirements
MODOMO_TAXONOMY: Dict[str, List[str]] = {
    # Primary Furniture Categories
    "seating": [
        "sofa", "sectional", "armchair", "dining_chair", "stool", "bench", 
        "loveseat", "recliner", "chaise_lounge", "bar_stool", "office_chair", 
        "accent_chair", "ottoman", "pouffe", "couch", "chair"
    ],
    
    "tables": [
        "coffee_table", "side_table", "dining_table", "console_table", "desk", 
        "nightstand", "end_table", "accent_table", "writing_desk", "computer_desk", 
        "bar_table", "bistro_table", "nesting_tables", "dressing_table", "table"
    ],
    
    "storage": [
        "bookshelf", "cabinet", "dresser", "wardrobe", "armoire", "chest_of_drawers", 
        "credenza", "sideboard", "buffet", "china_cabinet", "display_cabinet", 
        "tv_stand", "media_console", "shoe_cabinet", "pantry_cabinet", "shelf",
        "filing_cabinet", "storage_bench", "toy_chest"
    ],
    
    "bedroom": [
        "bed", "bed_frame", "mattress", "headboard", "footboard", "bed_base", 
        "platform_bed", "bunk_bed", "daybed", "murphy_bed", "crib", "bassinet", 
        "changing_table"
    ],
    
    # Lighting & Electrical
    "lighting": [
        "lamp", "pendant_light", "floor_lamp", "table_lamp", "wall_sconce", 
        "chandelier", "ceiling_light", "track_lighting", "recessed_light", 
        "under_cabinet_light", "desk_lamp", "reading_light", "accent_lighting", 
        "string_lights"
    ],
    
    "ceiling_fixtures": [
        "ceiling_fan", "smoke_detector", "air_vent", "skylight", "beam", 
        "molding", "medallion"
    ],
    
    # Kitchen & Appliances
    "kitchen_cabinets": [
        "upper_cabinet", "lower_cabinet", "kitchen_island", "breakfast_bar", 
        "pantry", "spice_rack", "wine_rack"
    ],
    
    "kitchen_appliances": [
        "refrigerator", "stove", "oven", "microwave", "dishwasher", "range_hood", 
        "garbage_disposal", "coffee_maker", "toaster", "blender", "fridge"
    ],
    
    "kitchen_fixtures": [
        "kitchen_sink", "sink", "faucet", "backsplash", "countertop", 
        "kitchen_island_top"
    ],
    
    # Bathroom & Fixtures
    "bathroom_fixtures": [
        "toilet", "shower", "bathtub", "sink_vanity", "bathroom_sink", 
        "shower_door", "shower_curtain", "medicine_cabinet", "towel_rack", 
        "toilet_paper_holder"
    ],
    
    "bathroom_storage": [
        "linen_closet", "bathroom_cabinet", "vanity_cabinet", "over_toilet_storage"
    ],
    
    # Textiles & Soft Furnishings
    "window_treatments": [
        "curtains", "drapes", "blinds", "shades", "shutters", "valance", 
        "cornice", "window_film", "curtain"
    ],
    
    "soft_furnishings": [
        "rug", "carpet", "pillow", "cushion", "throw_pillow", "blanket", 
        "throw", "bedding", "duvet", "comforter", "sheets", "pillowcase"
    ],
    
    # Decor & Accessories
    "wall_decor": [
        "wall_art", "painting", "photograph", "poster", "wall_sculpture", 
        "wall_clock", "decorative_plate", "wall_shelf", "floating_shelf", 
        "picture", "picture_frame", "frame"
    ],
    
    "decor_accessories": [
        "mirror", "plant", "vase", "candle", "sculpture", "decorative_bowl", 
        "clock", "lamp_shade", "decorative_object", "potted_plant", "book"
    ],
    
    # Architectural Elements
    "doors_windows": [
        "door", "window", "french_doors", "sliding_door", "bifold_door", 
        "pocket_door", "window_frame", "door_frame"
    ],
    
    "architectural_features": [
        "fireplace", "mantle", "column", "pillar", "archway", "niche", 
        "built_in_shelf", "wainscoting", "chair_rail", "radiator"
    ],
    
    # Electronics & Technology
    "entertainment": [
        "tv", "television", "stereo", "speakers", "gaming_console", 
        "dvd_player", "sound_bar", "monitor", "computer", "laptop"
    ],
    
    "smart_home": [
        "smart_speaker", "security_camera", "thermostat", "smart_switch", 
        "home_hub", "air_conditioner"
    ],
    
    # Outdoor & Patio
    "outdoor_furniture": [
        "patio_chair", "outdoor_table", "patio_umbrella", "outdoor_sofa", 
        "deck_chair", "garden_bench", "outdoor_dining_set"
    ],
    
    # Miscellaneous
    "miscellaneous": [
        "room_divider", "partition", "bar_cart", "coat_rack",
        "umbrella_stand", "magazine_rack"
    ]
}

# Synonym mapping for canonical labels
LABEL_SYNONYMS: Dict[str, str] = {
    # Seating synonyms
    "couch": "sofa",
    "settee": "sofa",
    "divan": "sofa",
    "chesterfield": "sofa",
    
    # Chair synonyms  
    "armchair": "chair",
    "dining_chair": "chair",
    "office_chair": "chair",
    "desk_chair": "office_chair",
    "swivel_chair": "office_chair",
    
    # Table synonyms
    "dining_table": "table",
    "coffee_table": "table",
    "side_table": "table",
    "end_table": "side_table",
    "console": "console_table",
    
    # Storage synonyms
    "bookcase": "bookshelf",
    "shelves": "shelf",
    "cupboard": "cabinet",
    "chest": "chest_of_drawers",
    "bureau": "dresser",
    
    # Bedroom synonyms
    "bedframe": "bed_frame",
    "bed_frame": "bed",
    
    # Kitchen synonyms
    "fridge": "refrigerator",
    "cooktop": "stove",
    "range": "stove",
    
    # Electronics synonyms
    "tv": "television",
    "screen": "monitor",
    "display": "monitor",
    
    # Decor synonyms
    "pot": "vase",
    "potted_plant": "plant",
    "picture": "picture_frame",
    "painting": "wall_art",
    "artwork": "wall_art",
    
    # General synonyms
    "ottoman": "ottoman",  # Keep as-is, it's in seating
    "bench": "bench",      # Keep as-is, it's in seating
}

# Pre-build reverse mappings for O(1) lookups
_item_to_category: Dict[str, str] = {}
_canonical_labels: Dict[str, str] = {}
_yolo_whitelist: Set[str] = set()

def _initialize_mappings():
    """Initialize reverse mappings and whitelist on module load."""
    global _item_to_category, _canonical_labels, _yolo_whitelist
    
    # Build item to category mapping
    for category, items in MODOMO_TAXONOMY.items():
        for item in items:
            _item_to_category[item] = category
            _yolo_whitelist.add(item)
    
    # Build canonical label mapping (including identity mappings)
    for item in _yolo_whitelist:
        _canonical_labels[item] = item  # Identity mapping by default
    
    # Override with synonyms
    for synonym, canonical in LABEL_SYNONYMS.items():
        _canonical_labels[synonym] = canonical
        _yolo_whitelist.add(synonym)  # Also detect synonyms
    
    logger.info(f"Taxonomy initialized with {len(MODOMO_TAXONOMY)} categories, "
                f"{len(_yolo_whitelist)} detectable items")

def get_yolo_whitelist() -> Set[str]:
    """
    Get the set of all furniture items YOLO should detect.
    
    Returns:
        Set of lowercase item labels to filter YOLO detections.
    """
    return _yolo_whitelist.copy()

def get_canonical_label(label: str) -> str:
    """
    Map a label to its canonical form, handling synonyms.
    
    Args:
        label: Raw label from YOLO or other detector (case-insensitive)
        
    Returns:
        Canonical label from taxonomy, or original label if unknown
        
    Examples:
        >>> get_canonical_label("couch")
        'sofa'
        >>> get_canonical_label("dining_table") 
        'table'
        >>> get_canonical_label("unknown_item")
        'unknown_item'
    """
    label_lower = label.lower().strip()
    canonical = _canonical_labels.get(label_lower, label_lower)
    
    if canonical == label_lower and label_lower not in _yolo_whitelist:
        logger.debug(f"Unknown label encountered: {label}")
    
    return canonical

def get_category_for_item(item: str) -> str:
    """
    Get the parent category for a furniture item.
    
    Args:
        item: Furniture item label (case-insensitive)
        
    Returns:
        Category name from MODOMO_TAXONOMY, or "furniture" if unknown
        
    Examples:
        >>> get_category_for_item("sofa")
        'seating'
        >>> get_category_for_item("coffee_table")
        'tables'
        >>> get_category_for_item("unknown")
        'furniture'
    """
    # First try to get canonical label
    canonical = get_canonical_label(item)
    
    # Then lookup category
    category = _item_to_category.get(canonical)
    
    if category is None:
        # Try direct lookup with original item
        category = _item_to_category.get(item.lower())
    
    return category or "furniture"

def is_furniture_item(label: str, confidence: float = 0.0, min_conf: float = 0.35) -> bool:
    """
    Check if a detected label is a furniture item worth keeping.
    
    Args:
        label: Detection label from YOLO
        confidence: Detection confidence score
        min_conf: Minimum confidence for non-furniture items
        
    Returns:
        True if item should be kept in detections
    """
    label_lower = label.lower().strip()
    
    # Always keep items in our whitelist
    if label_lower in _yolo_whitelist:
        return True
    
    # Keep high-confidence detections even if not in whitelist
    return confidence > min_conf

# Initialize mappings on module load
_initialize_mappings()
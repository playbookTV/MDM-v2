#!/usr/bin/env python3
"""
Populate the categories table with the Modomo furniture taxonomy
"""

import asyncio
from app.core.supabase import init_supabase, get_supabase

# Based on the MODOMO_TAXONOMY from documentation
FURNITURE_CATEGORIES = {
    # Primary categories
    "seating": "Chairs, sofas, and other seating furniture",
    "tables": "All types of tables",
    "storage": "Storage and organization furniture",
    "bedroom": "Bedroom furniture",
    "lighting": "Lighting fixtures and lamps",
    "kitchen_cabinets": "Kitchen storage and cabinets",
    "kitchen_appliances": "Kitchen appliances",
    "bathroom": "Bathroom fixtures and furniture",
    "decor": "Decorative items and accessories",
    "electronics": "Electronic devices and entertainment",
    "outdoor": "Outdoor and patio furniture",
    "office": "Office and workspace furniture",
    
    # Specific items (most common from taxonomy)
    "sofa": "Sofa or couch",
    "chair": "Chair (general)",
    "armchair": "Armchair", 
    "dining_chair": "Dining chair",
    "office_chair": "Office chair",
    "stool": "Stool or bar stool",
    "bench": "Bench seating",
    "ottoman": "Ottoman or footstool",
    
    "coffee_table": "Coffee table",
    "dining_table": "Dining table", 
    "desk": "Desk or work table",
    "side_table": "Side or end table",
    "console_table": "Console table",
    "nightstand": "Nightstand or bedside table",
    
    "bookshelf": "Bookshelf or bookcase",
    "cabinet": "Cabinet (general)",
    "dresser": "Dresser or chest of drawers",
    "wardrobe": "Wardrobe or armoire",
    "tv_stand": "TV stand or media console",
    
    "bed": "Bed frame",
    "mattress": "Mattress",
    "crib": "Baby crib",
    
    "lamp": "Lamp (general)",
    "floor_lamp": "Floor lamp",
    "table_lamp": "Table lamp",
    "pendant_light": "Pendant light",
    "chandelier": "Chandelier",
    
    "refrigerator": "Refrigerator",
    "stove": "Stove or range",
    "oven": "Oven",
    "microwave": "Microwave",
    "dishwasher": "Dishwasher",
    "sink": "Sink",
    
    "toilet": "Toilet",
    "bathtub": "Bathtub",
    "shower": "Shower",
    "vanity": "Bathroom vanity",
    
    "mirror": "Mirror",
    "plant": "Plant or potted plant",
    "vase": "Vase",
    "rug": "Rug or carpet",
    "curtains": "Curtains or drapes",
    "pillow": "Pillow or cushion",
    "artwork": "Wall art or painting",
    "clock": "Clock",
    
    "tv": "Television",
    "computer": "Computer or laptop",
    "monitor": "Computer monitor",
    "speakers": "Speakers",
    
    # Generic fallbacks
    "furniture": "Generic furniture item",
    "appliance": "Generic appliance",
    "fixture": "Generic fixture",
    "object": "Generic object",
    "unknown": "Unknown or unclassified item"
}

async def populate_categories():
    """Populate categories table"""
    
    await init_supabase()
    supabase = get_supabase()
    
    print("📝 Populating categories table...")
    
    # First, check existing categories
    existing = supabase.table("categories").select("code").execute()
    existing_codes = {cat['code'] for cat in existing.data}
    
    print(f"Found {len(existing_codes)} existing categories")
    
    # Prepare categories to insert
    new_categories = []
    
    # Add missing plant categories first (critical fix)
    plant_categories = {
        "potted plant": ("Potted Plant", "decor"),
        "potted_plant": ("Potted Plant", "decor"),
        "houseplant": ("Houseplant", "decor"),
        "planter": ("Planter", "decor"),
    }
    
    # Combine with existing furniture categories
    all_categories = {}
    for code, name in FURNITURE_CATEGORIES.items():
        # Determine family based on category type
        if code in ["sofa", "chair", "armchair", "dining_chair", "office_chair", "stool", "bench", "ottoman"]:
            family = "seating"
        elif code in ["coffee_table", "dining_table", "desk", "side_table", "console_table", "nightstand"]:
            family = "tables"
        elif code in ["bookshelf", "cabinet", "dresser", "wardrobe", "tv_stand"]:
            family = "storage"
        elif code in ["bed", "mattress", "crib"]:
            family = "bedroom"
        elif code in ["lamp", "floor_lamp", "table_lamp", "pendant_light", "chandelier"]:
            family = "lighting"
        elif code in ["refrigerator", "stove", "oven", "microwave", "dishwasher", "sink"]:
            family = "kitchen"
        elif code in ["toilet", "bathtub", "shower", "vanity"]:
            family = "bathroom"
        elif code in ["tv", "computer", "monitor", "speakers"]:
            family = "electronics"
        elif code in ["mirror", "plant", "vase", "rug", "curtains", "pillow", "artwork", "clock"]:
            family = "decor"
        else:
            family = "other"
        
        all_categories[code] = (name, family)
    
    # Add plant categories
    all_categories.update(plant_categories)
    
    for code, (display_name, family) in all_categories.items():
        if code not in existing_codes:
            new_categories.append({
                "code": code,
                "display": display_name,  # Changed from "name" to "display"
                "family": family,  # Added required family field
                "parent_code": None  # Can be updated later for hierarchical structure
            })
    
    if new_categories:
        print(f"Inserting {len(new_categories)} new categories...")
        
        # Insert in batches to avoid issues
        batch_size = 50
        for i in range(0, len(new_categories), batch_size):
            batch = new_categories[i:i+batch_size]
            result = supabase.table("categories").insert(batch).execute()
            print(f"  Inserted batch {i//batch_size + 1}: {len(batch)} categories")
        
        print(f"✅ Successfully added {len(new_categories)} categories")
    else:
        print("✅ All categories already exist")
    
    # Show total count
    final_count = supabase.table("categories").select("code", count="exact").execute()
    print(f"\n📊 Total categories in database: {final_count.count}")
    
    # Show some examples
    sample = supabase.table("categories").select("*").limit(10).execute()
    print("\n📋 Sample categories:")
    for cat in sample.data[:5]:
        print(f"  - {cat['code']}: {cat.get('display', cat.get('name', 'N/A'))} (family: {cat.get('family', 'N/A')})")

if __name__ == "__main__":
    asyncio.run(populate_categories())
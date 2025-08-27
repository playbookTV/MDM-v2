"""
Modomo Furniture Taxonomy
Comprehensive furniture and decor categorization for object detection
"""

# Enhanced Configuration for better object detection
MODOMO_TAXONOMY = {
    # Primary Furniture Categories
    "seating": ["sofa", "sectional", "armchair", "dining_chair", "stool", "bench", "loveseat", "recliner", "chaise_lounge", "bar_stool", "office_chair", "accent_chair", "ottoman", "pouffe"],
    
    "tables": ["coffee_table", "side_table", "dining_table", "console_table", "desk", "nightstand", "end_table", "accent_table", "writing_desk", "computer_desk", "bar_table", "bistro_table", "nesting_tables", "dressing_table"],
    
    "storage": ["bookshelf", "cabinet", "dresser", "wardrobe", "armoire", "chest_of_drawers", "credenza", "sideboard", "buffet", "china_cabinet", "display_cabinet", "tv_stand", "media_console", "shoe_cabinet", "pantry_cabinet"],
    
    "bedroom": ["bed_frame", "mattress", "headboard", "footboard", "bed_base", "platform_bed", "bunk_bed", "daybed", "murphy_bed", "crib", "bassinet", "changing_table"],
    
    # Lighting & Electrical
    "lighting": ["pendant_light", "floor_lamp", "table_lamp", "wall_sconce", "chandelier", "ceiling_light", "track_lighting", "recessed_light", "under_cabinet_light", "desk_lamp", "reading_light", "accent_lighting", "string_lights"],
    
    "ceiling_fixtures": ["ceiling_fan", "smoke_detector", "air_vent", "skylight", "beam", "molding", "medallion"],
    
    # Kitchen & Appliances
    "kitchen_cabinets": ["upper_cabinet", "lower_cabinet", "kitchen_island", "breakfast_bar", "pantry", "spice_rack", "wine_rack"],
    
    "kitchen_appliances": ["refrigerator", "stove", "oven", "microwave", "dishwasher", "range_hood", "garbage_disposal", "coffee_maker", "toaster", "blender"],
    
    "kitchen_fixtures": ["kitchen_sink", "faucet", "backsplash", "countertop", "kitchen_island_top"],
    
    # Bathroom & Fixtures
    "bathroom_fixtures": ["toilet", "shower", "bathtub", "sink_vanity", "bathroom_sink", "shower_door", "shower_curtain", "medicine_cabinet", "towel_rack", "toilet_paper_holder"],
    
    "bathroom_storage": ["linen_closet", "bathroom_cabinet", "vanity_cabinet", "over_toilet_storage"],
    
    # Textiles & Soft Furnishings
    "window_treatments": ["curtains", "drapes", "blinds", "shades", "shutters", "valance", "cornice", "window_film"],
    
    "soft_furnishings": ["rug", "carpet", "pillow", "cushion", "throw_pillow", "blanket", "throw", "bedding", "duvet", "comforter", "sheets", "pillowcase"],
    
    "upholstery": ["sofa_cushions", "chair_cushions", "seat_cushions", "back_cushions"],
    
    # Decor & Accessories
    "wall_decor": ["wall_art", "painting", "photograph", "poster", "wall_sculpture", "wall_clock", "decorative_plate", "wall_shelf", "floating_shelf"],
    
    "decor_accessories": ["mirror", "plant", "vase", "candle", "sculpture", "decorative_bowl", "picture_frame", "clock", "lamp_shade", "decorative_object"],
    
    "plants_planters": ["potted_plant", "hanging_plant", "planter", "flower_pot", "garden_planter", "herb_garden"],
    
    # Architectural Elements
    "doors_windows": ["door", "window", "french_doors", "sliding_door", "bifold_door", "pocket_door", "window_frame", "door_frame"],
    
    "architectural_features": ["fireplace", "mantle", "column", "pillar", "archway", "niche", "built_in_shelf", "wainscoting", "chair_rail"],
    
    "flooring": ["hardwood_floor", "tile_floor", "carpet_floor", "laminate_floor", "vinyl_floor", "stone_floor"],
    
    "wall_features": ["accent_wall", "brick_wall", "stone_wall", "wood_paneling", "wallpaper"],
    
    # Electronics & Technology
    "entertainment": ["tv", "television", "stereo", "speakers", "gaming_console", "dvd_player", "sound_bar"],
    
    "home_office": ["computer", "monitor", "printer", "desk_accessories", "filing_cabinet", "desk_organizer"],
    
    "smart_home": ["smart_speaker", "security_camera", "thermostat", "smart_switch", "home_hub"],
    
    # Outdoor & Patio
    "outdoor_furniture": ["patio_chair", "outdoor_table", "patio_umbrella", "outdoor_sofa", "deck_chair", "garden_bench", "outdoor_dining_set"],
    
    "outdoor_decor": ["outdoor_plant", "garden_sculpture", "outdoor_lighting", "wind_chime", "bird_feeder"],
    
    # Specialty Items
    "exercise_equipment": ["treadmill", "exercise_bike", "weights", "yoga_mat", "exercise_ball"],
    
    "children_furniture": ["toy_chest", "kids_table", "kids_chair", "high_chair", "play_table", "toy_storage"],
    
    "office_furniture": ["conference_table", "office_desk", "executive_chair", "meeting_chair", "whiteboard", "bulletin_board"],
    
    # Miscellaneous
    "room_dividers": ["screen", "room_divider", "partition", "bookcase_divider"],
    
    "seasonal_decor": ["christmas_tree", "holiday_decoration", "seasonal_pillow", "seasonal_wreath"],
    
    "hardware_fixtures": ["door_handle", "cabinet_hardware", "light_switch", "outlet", "vent_cover"]
}



Got it 👍 — if Modomo’s pipeline is going to detect, tag, and describe objects properly, then furniture categories need to be exhaustive, hierarchical, and normalized. Otherwise you’ll get a messy dataset (e.g., “sofa”, “couch”, “settee” all treated as different).

Here’s a structured, exhaustive taxonomy of furniture categories, grouped into logical families. This gives you both broad categories (for training) and fine-grained subcategories (for tagging/descriptions).

⸻

🪑 Modomo Furniture Category Taxonomy

⸻

1. Seating
	•	Sofas & Couches
	•	Sofa / Couch (general)
	•	Sectional Sofa
	•	Loveseat
	•	Chaise Lounge
	•	Futon / Sleeper Sofa
	•	Daybed
	•	Settee
	•	Chairs
	•	Armchair
	•	Recliner
	•	Rocking Chair
	•	Accent Chair
	•	Wingback Chair
	•	Club Chair
	•	Lounge Chair
	•	Slipper Chair
	•	Barrel Chair
	•	Parsons Chair
	•	Folding Chair
	•	Beanbag
	•	Gaming Chair
	•	Dining Seating
	•	Dining Chair
	•	Side Chair
	•	Counter Stool
	•	Bar Stool
	•	Bench (dining)
	•	Outdoor Seating
	•	Adirondack Chair
	•	Hammock
	•	Swing Chair
	•	Patio Sofa
	•	Outdoor Bench

⸻

2. Tables
	•	Living / Accent
	•	Coffee Table
	•	Side Table / End Table
	•	Nesting Tables
	•	Console Table / Sofa Table
	•	Dining
	•	Dining Table (rectangular, round, oval, extendable)
	•	Breakfast Table
	•	Pub Table / Bar Table
	•	Work
	•	Office Desk
	•	Executive Desk
	•	Writing Desk
	•	Standing Desk
	•	Computer Desk
	•	Drafting Table
	•	Bedroom
	•	Nightstand / Bedside Table
	•	Vanity Table
	•	Dressing Table
	•	Outdoor
	•	Picnic Table
	•	Patio Table

⸻

3. Storage & Organization
	•	Cabinets
	•	Sideboard / Buffet
	•	Credenza
	•	Hutch
	•	China Cabinet
	•	Display Cabinet
	•	Bar Cabinet
	•	Shelving
	•	Bookcase
	•	Wall Shelf
	•	Floating Shelves
	•	Corner Shelf
	•	Ladder Shelf
	•	Wardrobes & Dressers
	•	Wardrobe / Armoire
	•	Dresser / Chest of Drawers
	•	Tallboy / Highboy
	•	Lowboy
	•	Closet System
	•	Other Storage
	•	Storage Bench
	•	Blanket Chest / Hope Chest
	•	Toy Chest
	•	Shoe Rack
	•	Media Console / TV Stand
	•	Record Cabinet
	•	Storage Ottoman

⸻

4. Bedroom Furniture
	•	Beds
	•	Platform Bed
	•	Panel Bed
	•	Canopy Bed
	•	Four-Poster Bed
	•	Sleigh Bed
	•	Murphy Bed
	•	Trundle Bed
	•	Bunk Bed
	•	Loft Bed
	•	Crib
	•	Toddler Bed
	•	Mattresses (optional if you want to track separately)
	•	Bedside Furniture
	•	Nightstand
	•	Bedside Table
	•	Bed Bench

⸻

5. Office Furniture
	•	Desks (covered above)
	•	Office Chairs
	•	Task Chair
	•	Executive Chair
	•	Ergonomic Chair
	•	Conference Furniture
	•	Conference Table
	•	Conference Chair
	•	Storage
	•	Filing Cabinet
	•	Printer Stand
	•	Bookcase (office)
	•	Credenza (office)

⸻

6. Lighting

(Not strictly “furniture” but critical for interiors — keep in taxonomy)
	•	Floor Lamps
	•	Tripod Lamp
	•	Torchiere Lamp
	•	Arc Lamp
	•	Table Lamps
	•	Desk Lamp
	•	Bedside Lamp
	•	Accent Lamp
	•	Ceiling Lighting
	•	Chandelier
	•	Pendant Light
	•	Flush Mount / Semi-Flush
	•	Track Lighting
	•	Wall Lighting
	•	Sconce
	•	Swing-Arm Wall Lamp
	•	Special
	•	LED Strip
	•	Smart Lamp

⸻

7. Dining & Kitchen Furniture
	•	Dining Table (already covered)
	•	Dining Chairs / Benches
	•	Bar Stools / Counter Stools
	•	Kitchen Island
	•	Baker’s Rack
	•	Pantry Cabinet

⸻

8. Outdoor Furniture
	•	Patio Table
	•	Patio Chairs
	•	Chaise Lounge (outdoor)
	•	Adirondack Chair
	•	Garden Bench
	•	Outdoor Sofa / Sectional
	•	Hammock / Swing
	•	Fire Pit Table

⸻

9. Children’s Furniture
	•	Crib
	•	Toddler Bed
	•	Bunk Bed (kids)
	•	Changing Table
	•	Toy Chest
	•	Kids’ Desk + Chair
	•	Kids’ Bookcase
	•	Rocking Horse / Play Seating

⸻

10. Miscellaneous / Decor Furniture
	•	Ottomans (standard, pouf, storage)
	•	Poufs
	•	Vanity Stools
	•	Plant Stands
	•	Coat Rack / Hall Tree
	•	Room Divider / Folding Screen
	•	Bar Cart
	•	Mirror with Storage
	•	Entryway Bench
	•	Shoe Storage Bench

⸻

🔑 Notes on Implementation
	1.	Canonical labels vs synonyms
	•	Canonical: sofa
	•	Synonyms: couch, settee → map to sofa in DB
	•	Keep synonyms in a label_aliases YAML file for clean mapping.
	2.	Granularity
	•	YOLO/SAM may give broad outputs (e.g., “chair”).
	•	GroundingDINO + CLIP prototypes can refine to subtype (e.g., “wingback chair”).
	3.	Storage in DB (objects table)
	•	category → canonical (sofa, dining_table, wardrobe)
	•	subcategory (optional) → more fine-grained (sectional sofa, sleigh bed)
	•	aliases in JSON for provenance

⸻

Example DB Entry for a Single Object

{
  "id": "obj-uuid",
  "scene_id": "scene-uuid",
  "category": "sofa",
  "subcategory": "sectional sofa",
  "bbox": [120, 240, 400, 600],
  "confidence": 0.87,
  "materials": ["fabric","wood"],
  "description": "Large L-shaped sectional sofa with neutral grey upholstery and wooden tapered legs.",
  "attrs": {
    "color": "grey",
    "style_hint": "contemporary",
    "seating_capacity": 5
  },
  "mask_key": "masks/scene-uuid/obj-uuid.png",
  "depth_key": "depth/scene-uuid.png",
  "thumb_key": "thumbs/scene-uuid/obj-uuid.jpg"
}


⸻

👉 With this taxonomy in place, Modomo’s pipeline can consistently:
	•	Detect core furniture categories
	•	Map them to fine-grained subtypes
	•	Enrich them with materials, descriptions, and attributes
	•	Ensure dataset cleanliness across synonyms

⸻

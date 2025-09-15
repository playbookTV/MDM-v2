#!/usr/bin/env python3
"""
Check the actual schema of the categories table in Supabase
"""

import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get Supabase credentials from environment
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://ltsghtegbauatqbemwqd.supabase.co")
# Try service role key from environment, or use the one from .env file
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY") or "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imx0c2dodGVnYmF1YXRxYmVtd3FkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MjU5OTk4MDksImV4cCI6MjA3MTU3NTgwOX0.hzyRSYZFlPQnWl9CyezJUW1fWd_TW4hipVPLEv6EXqk"

def check_categories_schema():
    """Check the schema of the categories table"""
    
    # Create Supabase client
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    print("=== Checking Categories Table Schema ===\n")
    
    # Query 1: Get column information
    print("1. Column Information:")
    query = """
    SELECT 
        column_name, 
        data_type, 
        is_nullable, 
        column_default,
        character_maximum_length
    FROM information_schema.columns 
    WHERE table_schema='public' AND table_name='categories' 
    ORDER BY ordinal_position
    """
    
    try:
        result = supabase.rpc('sql_query', {'query': query}).execute()
        print("Categories table columns:")
        for col in result.data:
            print(f"  - {col['column_name']}: {col['data_type']} (nullable: {col['is_nullable']}, default: {col['column_default']})")
    except:
        # Try direct query if RPC doesn't work
        print("Trying alternative query method...")
        
    # Query 2: Get sample existing categories
    print("\n2. Sample Existing Categories:")
    try:
        result = supabase.table('categories').select("*").limit(10).execute()
        
        if result.data:
            print(f"Found {len(result.data)} sample categories:")
            for cat in result.data[:5]:
                print(f"  - Code: {cat.get('code')}")
                print(f"    Display: {cat.get('display', 'N/A')}")
                print(f"    Family: {cat.get('family', 'N/A')}")
                print(f"    Parent: {cat.get('parent_code', 'N/A')}")
                print()
        else:
            print("No categories found in table")
            
    except Exception as e:
        print(f"Error fetching categories: {e}")
    
    # Query 3: Check what category codes are being used by objects
    print("\n3. Category codes used by objects:")
    try:
        result = supabase.table('objects').select("category_code").execute()
        
        if result.data:
            # Count unique category codes
            category_counts = {}
            for obj in result.data:
                code = obj.get('category_code')
                if code:
                    category_counts[code] = category_counts.get(code, 0) + 1
            
            # Sort by count
            sorted_cats = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)
            
            print(f"Top category codes in objects table:")
            for code, count in sorted_cats[:10]:
                print(f"  - {code}: {count} objects")
        else:
            print("No objects found")
            
    except Exception as e:
        print(f"Error fetching objects: {e}")
    
    # Query 4: Find missing categories
    print("\n4. Missing categories (in objects but not in categories):")
    try:
        # Get all category codes from objects
        objects_result = supabase.table('objects').select("category_code").execute()
        object_codes = set(obj['category_code'] for obj in objects_result.data if obj.get('category_code'))
        
        # Get all category codes from categories
        categories_result = supabase.table('categories').select("code").execute()
        category_codes = set(cat['code'] for cat in categories_result.data)
        
        # Find missing
        missing = object_codes - category_codes
        
        if missing:
            print(f"Found {len(missing)} missing category codes:")
            for code in sorted(missing)[:20]:
                print(f"  - '{code}'")
        else:
            print("No missing categories found")
            
    except Exception as e:
        print(f"Error checking missing categories: {e}")

if __name__ == "__main__":
    check_categories_schema()
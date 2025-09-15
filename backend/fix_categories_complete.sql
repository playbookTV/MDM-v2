-- Complete SQL to fix categories table with proper schema detection
-- This handles all possible NOT NULL constraints

DO $$
DECLARE
    v_columns TEXT[];
    v_sql TEXT;
BEGIN
    -- First, check what columns exist and which are NOT NULL
    SELECT array_agg(column_name ORDER BY ordinal_position)
    INTO v_columns
    FROM information_schema.columns
    WHERE table_schema = 'public' 
      AND table_name = 'categories'
      AND is_nullable = 'NO';
    
    -- Check if parent category exists first
    IF NOT EXISTS (SELECT 1 FROM public.categories WHERE code = 'decor_accessories') THEN
        -- Insert parent category first based on schema
        IF 'display' = ANY(v_columns) THEN
            INSERT INTO public.categories (code, display) VALUES 
                ('decor_accessories', 'Decor & Accessories')
            ON CONFLICT (code) DO NOTHING;
        ELSE
            INSERT INTO public.categories (code) VALUES 
                ('decor_accessories')
            ON CONFLICT (code) DO NOTHING;
        END IF;
    END IF;
    
    -- Now insert the missing categories based on what columns are NOT NULL
    IF 'display' = ANY(v_columns) AND 'description' = ANY(v_columns) THEN
        -- Both display and description are NOT NULL
        INSERT INTO public.categories (code, display, description, parent_code) VALUES 
            ('potted plant', 'Potted Plant', 'Indoor plants in decorative containers', 'decor_accessories'),
            ('potted_plant', 'Potted Plant', 'Indoor plants in decorative containers (underscore variant)', 'decor_accessories'),
            ('plant', 'Plant', 'General plant category', 'decor_accessories'),
            ('houseplant', 'Houseplant', 'Indoor decorative plants', 'decor_accessories'),
            ('planter', 'Planter', 'Plant containers and planters', 'decor_accessories')
        ON CONFLICT (code) DO NOTHING;
        
    ELSIF 'display' = ANY(v_columns) THEN
        -- Only display is NOT NULL
        INSERT INTO public.categories (code, display, parent_code) VALUES 
            ('potted plant', 'Potted Plant', 'decor_accessories'),
            ('potted_plant', 'Potted Plant', 'decor_accessories'),
            ('plant', 'Plant', 'decor_accessories'),
            ('houseplant', 'Houseplant', 'decor_accessories'),
            ('planter', 'Planter', 'decor_accessories')
        ON CONFLICT (code) DO NOTHING;
        
    ELSIF 'name' = ANY(v_columns) THEN
        -- name is NOT NULL (alternative column name)
        INSERT INTO public.categories (code, name, parent_code) VALUES 
            ('potted plant', 'Potted Plant', 'decor_accessories'),
            ('potted_plant', 'Potted Plant', 'decor_accessories'),
            ('plant', 'Plant', 'decor_accessories'),
            ('houseplant', 'Houseplant', 'decor_accessories'),
            ('planter', 'Planter', 'decor_accessories')
        ON CONFLICT (code) DO NOTHING;
        
    ELSIF 'category_name' = ANY(v_columns) THEN
        -- category_name is NOT NULL (another alternative)
        INSERT INTO public.categories (code, category_name, parent_code) VALUES 
            ('potted plant', 'Potted Plant', 'decor_accessories'),
            ('potted_plant', 'Potted Plant', 'decor_accessories'),
            ('plant', 'Plant', 'decor_accessories'),
            ('houseplant', 'Houseplant', 'decor_accessories'),
            ('planter', 'Planter', 'decor_accessories')
        ON CONFLICT (code) DO NOTHING;
        
    ELSE
        -- Minimal insert with just code
        INSERT INTO public.categories (code) VALUES 
            ('potted plant'),
            ('potted_plant'),
            ('plant'),
            ('houseplant'),
            ('planter')
        ON CONFLICT (code) DO NOTHING;
    END IF;
    
    RAISE NOTICE 'Categories insert completed successfully';
    
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE 'Error inserting categories: %', SQLERRM;
        RAISE;
END $$;

-- Verify what was inserted
SELECT 
    code,
    COALESCE(
        (SELECT display FROM public.categories c2 WHERE c2.code = c.code LIMIT 1),
        (SELECT name FROM public.categories c3 WHERE c3.code = c.code LIMIT 1),
        (SELECT category_name FROM public.categories c4 WHERE c4.code = c.code LIMIT 1),
        'N/A'
    ) AS display_name,
    parent_code,
    created_at
FROM public.categories c
WHERE code IN ('potted plant', 'potted_plant', 'plant', 'houseplant', 'planter', 'decor_accessories')
ORDER BY code;

-- Also check if there are any other object categories that might be missing
-- This will help identify other potential foreign key violations
SELECT DISTINCT o.category_code
FROM public.objects o
LEFT JOIN public.categories c ON o.category_code = c.code
WHERE c.code IS NULL
LIMIT 20;
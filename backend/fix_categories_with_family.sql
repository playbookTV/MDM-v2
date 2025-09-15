-- Complete SQL to fix categories table including the family column
-- Based on error: null value in column "family" of relation "categories" violates not-null constraint

-- First, let's check the exact schema
SELECT column_name, data_type, is_nullable, column_default 
FROM information_schema.columns 
WHERE table_schema='public' AND table_name='categories' 
ORDER BY ordinal_position;

-- Check if parent category exists and has the family value we need
SELECT * FROM public.categories WHERE code = 'decor_accessories';

-- Insert parent category if missing
INSERT INTO public.categories (code, display, family, parent_code) VALUES 
    ('decor_accessories', 'Decor & Accessories', 'decor', NULL)
ON CONFLICT (code) DO NOTHING;

-- Now insert the missing plant-related categories
-- Using 'decor' as the family since they're under decor_accessories
INSERT INTO public.categories (code, display, family, parent_code) VALUES 
    ('potted plant', 'Potted Plant', 'decor', 'decor_accessories'),
    ('potted_plant', 'Potted Plant', 'decor', 'decor_accessories'),
    ('plant', 'Plant', 'decor', 'decor_accessories'),
    ('houseplant', 'Houseplant', 'decor', 'decor_accessories'),
    ('planter', 'Planter', 'decor', 'decor_accessories')
ON CONFLICT (code) DO NOTHING;

-- Also add any other common object categories that might be detected
-- to prevent future foreign key violations
INSERT INTO public.categories (code, display, family, parent_code) VALUES 
    -- Common YOLO/object detection labels
    ('person', 'Person', 'other', NULL),
    ('book', 'Book', 'decor', 'decor_accessories'),
    ('bottle', 'Bottle', 'decor', 'decor_accessories'),
    ('cup', 'Cup', 'kitchen', 'kitchen_accessories'),
    ('bowl', 'Bowl', 'kitchen', 'kitchen_accessories'),
    ('knife', 'Knife', 'kitchen', 'kitchen_accessories'),
    ('spoon', 'Spoon', 'kitchen', 'kitchen_accessories'),
    ('fork', 'Fork', 'kitchen', 'kitchen_accessories'),
    ('banana', 'Banana', 'other', NULL),
    ('apple', 'Apple', 'other', NULL),
    ('orange', 'Orange', 'other', NULL),
    ('broccoli', 'Broccoli', 'other', NULL),
    ('carrot', 'Carrot', 'other', NULL),
    ('hot dog', 'Hot Dog', 'other', NULL),
    ('pizza', 'Pizza', 'other', NULL),
    ('donut', 'Donut', 'other', NULL),
    ('cake', 'Cake', 'other', NULL),
    ('cell phone', 'Cell Phone', 'electronics', NULL),
    ('keyboard', 'Keyboard', 'office', 'home_office'),
    ('mouse', 'Mouse', 'office', 'home_office'),
    ('remote', 'Remote', 'electronics', NULL),
    ('scissors', 'Scissors', 'office', NULL),
    ('teddy bear', 'Teddy Bear', 'decor', 'decor_accessories'),
    ('hair drier', 'Hair Drier', 'bathroom', 'bathroom_accessories'),
    ('toothbrush', 'Toothbrush', 'bathroom', 'bathroom_accessories')
ON CONFLICT (code) DO NOTHING;

-- Verify the additions
SELECT code, display, family, parent_code, created_at
FROM public.categories 
WHERE code IN ('potted plant', 'potted_plant', 'plant', 'houseplant', 'planter', 'decor_accessories')
ORDER BY code;

-- Check if there are still any missing categories from objects table
SELECT DISTINCT o.category_code, COUNT(*) as count
FROM public.objects o
LEFT JOIN public.categories c ON o.category_code = c.code
WHERE c.code IS NULL
GROUP BY o.category_code
ORDER BY count DESC
LIMIT 20;
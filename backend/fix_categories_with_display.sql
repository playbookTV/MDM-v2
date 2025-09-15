-- Fix for categories table with display column (NOT NULL constraint)
-- Based on error: null value in column "display" of relation "categories" violates not-null constraint

-- First check the actual schema
-- SELECT column_name, data_type, is_nullable FROM information_schema.columns 
-- WHERE table_schema='public' AND table_name='categories' ORDER BY ordinal_position;

-- Insert categories with display values to satisfy NOT NULL constraint
INSERT INTO public.categories (code, display, description, parent_code) VALUES 
  ('potted plant', 'Potted Plant', 'Indoor plants in decorative containers', 'decor_accessories')
ON CONFLICT (code) DO NOTHING;

INSERT INTO public.categories (code, display, description, parent_code) VALUES 
  ('potted_plant', 'Potted Plant', 'Indoor plants in decorative containers (underscore variant)', 'decor_accessories'),
  ('plant', 'Plant', 'General plant category', 'decor_accessories'),
  ('houseplant', 'Houseplant', 'Indoor decorative plants', 'decor_accessories'),
  ('planter', 'Planter', 'Plant containers and planters', 'decor_accessories')
ON CONFLICT (code) DO NOTHING;

-- Verify the additions
SELECT code, display, description, parent_code, created_at
FROM public.categories 
WHERE code IN ('potted plant', 'potted_plant', 'plant', 'houseplant', 'planter')
ORDER BY code;
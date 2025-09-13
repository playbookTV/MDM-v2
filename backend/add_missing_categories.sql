-- Add missing categories to fix foreign key constraint violations
-- Based on the error: Key (category_code)=(potted plant) is not present in table "categories"

-- First, let's see what categories currently exist
-- SELECT * FROM categories ORDER BY code;

-- Add missing category mappings that are used in the worker tasks
INSERT INTO categories (code, name, description, parent_code) VALUES 
('potted plant', 'Potted Plant', 'Indoor plants in decorative containers', 'decor_accessories')
ON CONFLICT (code) DO NOTHING;

-- Add other potentially missing categories that might be detected
INSERT INTO categories (code, name, description, parent_code) VALUES 
('potted_plant', 'Potted Plant', 'Indoor plants in decorative containers (underscore variant)', 'decor_accessories'),
('plant', 'Plant', 'General plant category', 'decor_accessories'),
('houseplant', 'Houseplant', 'Indoor decorative plants', 'decor_accessories'),
('planter', 'Planter', 'Plant containers and planters', 'decor_accessories')
ON CONFLICT (code) DO NOTHING;

-- Verify the additions
SELECT code, name, description, parent_code 
FROM categories 
WHERE code IN ('potted plant', 'potted_plant', 'plant', 'houseplant', 'planter')
ORDER BY code;
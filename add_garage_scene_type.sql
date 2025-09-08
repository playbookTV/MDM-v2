-- Add garage as a valid scene type
INSERT INTO scene_labels(code, display) VALUES ('garage', 'Garage')
ON CONFLICT (code) DO NOTHING;
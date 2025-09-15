-- Add review sessions table to track reviewer sessions
-- Run this to update the existing database schema

-- Review sessions to track reviewer activity
CREATE TABLE IF NOT EXISTS review_sessions (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  dataset_id    UUID REFERENCES datasets(id) ON DELETE SET NULL,
  name          TEXT NOT NULL DEFAULT 'Review Session',
  reviewer_id   TEXT NOT NULL DEFAULT 'anonymous',
  started_at    TIMESTAMPTZ DEFAULT NOW(),
  ended_at      TIMESTAMPTZ,
  scenes_count  INTEGER DEFAULT 0,
  created_at    TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_review_sessions_dataset ON review_sessions(dataset_id);
CREATE INDEX IF NOT EXISTS idx_review_sessions_reviewer ON review_sessions(reviewer_id);
CREATE INDEX IF NOT EXISTS idx_review_sessions_started ON review_sessions(started_at);

-- Update reviews table to link to sessions
ALTER TABLE reviews ADD COLUMN IF NOT EXISTS session_id UUID REFERENCES review_sessions(id) ON DELETE SET NULL;
CREATE INDEX IF NOT EXISTS idx_reviews_session ON reviews(session_id);

-- Add timing columns to reviews for calculating average review times
ALTER TABLE reviews ADD COLUMN IF NOT EXISTS review_time_seconds INTEGER;
CREATE INDEX IF NOT EXISTS idx_reviews_time ON reviews(review_time_seconds);
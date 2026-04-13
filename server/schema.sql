-- Ivy Database Schema
-- PostgreSQL 15+ with JSONB support

-- Enable UUID extension for LangGraph
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Job status enum
CREATE TYPE job_status AS ENUM (
    'pending',
    'ingesting',
    'timeline',
    'plot_hole',
    'complete',
    'failed'
);

-- Severity enum for plot holes
CREATE TYPE plot_hole_severity AS ENUM ('high', 'medium', 'low');

-- Hole type enum
CREATE TYPE plot_hole_type AS ENUM (
    'timeline_paradox',
    'location_conflict',
    'dead_character_speaks',
    'unresolved_setup'
);

-- =============================================================================
-- CORE TABLES
-- =============================================================================

-- Job tracking
CREATE TABLE IF NOT EXISTS jobs (
    job_id TEXT PRIMARY KEY,
    status job_status NOT NULL DEFAULT 'pending',
    pdf_filename TEXT,
    pdf_key TEXT,
    current_agent TEXT,
    completed_agents TEXT[] DEFAULT '{}',
    error TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Chapters (JSONB for flexible metadata)
CREATE TABLE IF NOT EXISTS chapters (
    chapter_id TEXT PRIMARY KEY,
    job_id TEXT NOT NULL REFERENCES jobs(job_id) ON DELETE CASCADE,
    chapter_num INTEGER NOT NULL,
    title TEXT,
    summary JSONB DEFAULT '[]',
    key_events JSONB DEFAULT '[]',
    characters TEXT[] DEFAULT '{}',
    temporal_markers TEXT[] DEFAULT '{}',
    raw_text TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Timeline events (normalized for graph queries)
CREATE TABLE IF NOT EXISTS timeline_events (
    event_id TEXT PRIMARY KEY,
    job_id TEXT NOT NULL REFERENCES jobs(job_id) ON DELETE CASCADE,
    description TEXT NOT NULL,
    chapter_num INTEGER NOT NULL,
    event_order INTEGER NOT NULL,
    chapter_title TEXT,
    characters_present TEXT[] DEFAULT '{}',
    location TEXT,
    causes TEXT[] DEFAULT '{}',
    caused_by TEXT[] DEFAULT '{}',
    time_reference TEXT,
    inferred_date TEXT,
    inferred_year INTEGER,
    relative_time_anchor TEXT,
    confidence FLOAT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Character interactions (for NetworkX graph export)
CREATE TABLE IF NOT EXISTS character_interactions (
    job_id TEXT NOT NULL REFERENCES jobs(job_id) ON DELETE CASCADE,
    char_a TEXT NOT NULL,
    char_b TEXT NOT NULL,
    chapter_num INTEGER NOT NULL,
    interaction_type TEXT,
    PRIMARY KEY (job_id, char_a, char_b, chapter_num)
);

-- Plot holes
CREATE TABLE IF NOT EXISTS plot_holes (
    hole_id TEXT PRIMARY KEY,
    job_id TEXT NOT NULL REFERENCES jobs(job_id) ON DELETE CASCADE,
    hole_type plot_hole_type,
    severity plot_hole_severity DEFAULT 'medium',
    description TEXT NOT NULL,
    chapters_involved INTEGER[] DEFAULT '{}',
    characters_involved TEXT[] DEFAULT '{}',
    events_involved TEXT[] DEFAULT '{}',
    confidence FLOAT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Entities (characters, locations, etc.)
CREATE TABLE IF NOT EXISTS entities (
    entity_id TEXT PRIMARY KEY,
    job_id TEXT NOT NULL REFERENCES jobs(job_id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    entity_type TEXT,
    appears_in_chapters INTEGER[] DEFAULT '{}',
    aliases TEXT[] DEFAULT '{}',
    role TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =============================================================================
-- LANGGRAPH CHECKPOINT TABLES
-- =============================================================================

-- Checkpoint saves (LangGraph state persistence)
CREATE TABLE IF NOT EXISTS checkpoints (
    thread_id TEXT NOT NULL,
    checkpoint_ns TEXT NOT NULL DEFAULT '',
    checkpoint_id TEXT NOT NULL,
    parent_checkpoint_id TEXT,
    type TEXT,
    checkpoint JSONB NOT NULL,
    metadata JSONB DEFAULT '{}',
    PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id)
);

-- Checkpoint writes (pending writes)
CREATE TABLE IF NOT EXISTS checkpoint_writes (
    thread_id TEXT NOT NULL,
    checkpoint_ns TEXT NOT NULL DEFAULT '',
    checkpoint_id TEXT NOT NULL,
    task_id TEXT NOT NULL,
    idx INTEGER NOT NULL,
    channel TEXT NOT NULL,
    type TEXT,
    value JSONB,
    PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id, task_id, idx)
);

-- Checkpoint pending sends
CREATE TABLE IF NOT EXISTS checkpoint_pending_sends (
    thread_id TEXT NOT NULL,
    checkpoint_ns TEXT NOT NULL DEFAULT '',
    checkpoint_id TEXT NOT NULL,
    idx INTEGER NOT NULL,
    channel TEXT NOT NULL,
    value JSONB,
    PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id, idx)
);

-- =============================================================================
-- INDEXES
-- =============================================================================

-- Jobs indexes
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON jobs(created_at);

-- Chapters indexes
CREATE INDEX IF NOT EXISTS idx_chapters_job ON chapters(job_id);
CREATE INDEX IF NOT EXISTS idx_chapters_job_num ON chapters(job_id, chapter_num);

-- Timeline indexes
CREATE INDEX IF NOT EXISTS idx_timeline_job ON timeline_events(job_id);
CREATE INDEX IF NOT EXISTS idx_timeline_order ON timeline_events(job_id, event_order);
CREATE INDEX IF NOT EXISTS idx_timeline_chapter ON timeline_events(job_id, chapter_num);

-- Character interactions indexes
CREATE INDEX IF NOT EXISTS idx_interactions_job ON character_interactions(job_id);
CREATE INDEX IF NOT EXISTS idx_interactions_char ON character_interactions(char_a, char_b);

-- Plot holes indexes
CREATE INDEX IF NOT EXISTS idx_plotholes_job ON plot_holes(job_id);
CREATE INDEX IF NOT EXISTS idx_plotholes_severity ON plot_holes(job_id, severity);

-- Entities indexes
CREATE INDEX IF NOT EXISTS idx_entities_job ON entities(job_id);
CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(job_id, entity_type);

-- Checkpoint indexes
CREATE INDEX IF NOT EXISTS idx_checkpoints_thread ON checkpoints(thread_id);

-- =============================================================================
-- TRIGGERS
-- =============================================================================

-- Auto-update updated_at on jobs
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_jobs_updated_at
    BEFORE UPDATE ON jobs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- COMMENTS
-- =============================================================================

COMMENT ON TABLE jobs IS 'Manuscript processing jobs';
COMMENT ON TABLE chapters IS 'Extracted chapter data from PDFs';
COMMENT ON TABLE timeline_events IS 'Global story timeline with causality links';
COMMENT ON TABLE character_interactions IS 'Character relationship edges for NetworkX graph';
COMMENT ON TABLE plot_holes IS 'Detected plot inconsistencies and continuity errors';
COMMENT ON TABLE entities IS 'Characters, locations, and other story entities';
COMMENT ON TABLE checkpoints IS 'LangGraph checkpoint state persistence';

-- theLuhmann Database Schema
-- Minimal Zettelkasten schema inspired by Niklas Luhmann's slip-box method

-- Main notes table
CREATE TABLE IF NOT EXISTS zettelkasten (
    zettel_id TEXT PRIMARY KEY,
    note TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Links between notes (directional)
CREATE TABLE IF NOT EXISTS zettel_links (
    from_zettel_id TEXT REFERENCES zettelkasten(zettel_id) ON DELETE CASCADE,
    to_zettel_id TEXT REFERENCES zettelkasten(zettel_id) ON DELETE CASCADE,
    PRIMARY KEY (from_zettel_id, to_zettel_id),
    CHECK(from_zettel_id != to_zettel_id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_zl_from ON zettel_links(from_zettel_id);
CREATE INDEX IF NOT EXISTS idx_zl_to ON zettel_links(to_zettel_id);

-- Optional: Insight index for categorization
CREATE TABLE IF NOT EXISTS insight_index (
    id TEXT PRIMARY KEY,
    index_name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS zettel_insight_index (
    zettel_id TEXT REFERENCES zettelkasten(zettel_id) ON DELETE CASCADE,
    index_id TEXT REFERENCES insight_index(id) ON DELETE CASCADE,
    PRIMARY KEY (zettel_id, index_id)
);

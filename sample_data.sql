-- Sample data for testing theLuhmann
-- Run with: sqlite3 data/zettel.db < sample_data.sql

INSERT INTO zettelkasten (zettel_id, note) VALUES
('1', 'The Zettelkasten method is a note-taking system developed by Niklas Luhmann. Each note should contain one atomic idea that can be understood on its own.'),
('1/1', 'Atomic notes force clarity of thought. If you cannot express an idea in a single note, you may not fully understand it yet.'),
('1/1a', 'The constraint of atomicity is a feature, not a bug. It creates pressure to refine thinking.'),
('1/2', 'Links between notes are where the real value emerges. The structure reveals unexpected connections.'),
('2', 'Luhmann produced over 70 books and 400 articles using his Zettelkasten. The system scaled with his thinking.'),
('2/1', 'The slip-box becomes a conversation partner. You write to it, and it surprises you with connections you forgot you made.'),
('3', 'Digital Zettelkasten tools must preserve the core principles: atomicity, unique IDs, bidirectional links, and emergent structure.');

INSERT INTO zettel_links (from_zettel_id, to_zettel_id) VALUES
('1', '1/1'),
('1', '1/2'),
('1/1', '1/1a'),
('1/2', '2/1'),
('2', '1'),
('2', '2/1'),
('3', '1'),
('3', '2');

-- Sample insights
INSERT INTO insight_index (id, index_name) VALUES
('methodology', 'Methodology'),
('philosophy', 'Philosophy'),
('writing', 'Writing'),
('knowledge-management', 'Knowledge Management'),
('emergence', 'Emergence');

-- Tag some cards with insights
INSERT INTO zettel_insight_index (zettel_id, index_id) VALUES
('1', 'methodology'),
('1', 'knowledge-management'),
('1/1', 'philosophy'),
('1/1', 'writing'),
('1/1a', 'philosophy'),
('1/2', 'emergence'),
('2', 'methodology'),
('3', 'knowledge-management');

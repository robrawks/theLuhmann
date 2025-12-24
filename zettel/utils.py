"""Zettelkasten TUI utilities - session trail, character counting, database helpers."""

import re
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from config import DB_PATH


@dataclass
class TrailEntry:
    """A single entry in the session trail."""
    zettel_id: str
    timestamp: datetime = field(default_factory=datetime.now)


class SessionTrail:
    """
    Manages the session history of checked-out cards.

    Supports:
    - Linear history with backtracking
    - Windowed display for long trails
    - Jump to any visible position
    """

    def __init__(self, window_size: int = 20):
        self.entries: list[TrailEntry] = []
        self.position: int = -1  # Current position in trail (-1 = empty)
        self.window_start: int = 0  # Display window start
        self.window_size: int = window_size  # Can be updated dynamically

    @property
    def current(self) -> Optional[str]:
        """Get current zettel_id or None if empty."""
        if 0 <= self.position < len(self.entries):
            return self.entries[self.position].zettel_id
        return None

    @property
    def total(self) -> int:
        """Total entries in trail."""
        return len(self.entries)

    @property
    def can_go_back(self) -> bool:
        """Can we go back in the trail?"""
        return self.position > 0

    @property
    def can_go_forward(self) -> bool:
        """Can we go forward (after backtracking)?"""
        return self.position < len(self.entries) - 1

    def checkout(self, zettel_id: str) -> None:
        """
        Add a card to the trail.

        Appends to the end of the trail (preserves full history).
        """
        # Don't add duplicates of current
        if self.current == zettel_id:
            return

        # Always append to end (no truncation - preserve full history)
        self.entries.append(TrailEntry(zettel_id))
        self.position = len(self.entries) - 1

        # Adjust window to show current
        self._adjust_window()

    def back(self) -> Optional[str]:
        """
        Go back one step in the trail.

        Returns the zettel_id we went back to, or None if already at start.
        """
        if self.position > 0:
            self.position -= 1
            self._adjust_window()
            return self.current
        return None

    def forward(self) -> Optional[str]:
        """
        Go forward one step in the trail (if we backtracked).

        Returns the zettel_id we went to, or None if at end.
        """
        if self.position < len(self.entries) - 1:
            self.position += 1
            self._adjust_window()
            return self.current
        return None

    def jump_to_display_index(self, display_index: int) -> Optional[str]:
        """
        Jump to a trail position by display index (1-based, from window).

        Args:
            display_index: 1-based index within the visible window

        Returns:
            The zettel_id jumped to, or None if invalid index.
        """
        actual_index = self.window_start + display_index - 1
        if 0 <= actual_index < len(self.entries):
            self.position = actual_index
            self._adjust_window()
            return self.current
        return None

    def get_visible_entries(self) -> list[tuple[int, str, bool]]:
        """
        Get the visible window of trail entries.

        Returns:
            List of (actual_position, zettel_id, is_current) tuples.
            actual_position is 1-based actual trail position (not window position).
        """
        result = []
        end = min(self.window_start + self.window_size, len(self.entries))

        for i in range(self.window_start, end):
            actual_pos = i + 1  # 1-based actual position in trail
            is_current = (i == self.position)
            result.append((actual_pos, self.entries[i].zettel_id, is_current))

        return result

    def get_overflow_info(self) -> tuple[int, int]:
        """
        Get info about entries outside the visible window.

        Returns:
            (entries_before_window, entries_after_window)
        """
        before = self.window_start
        after = max(0, len(self.entries) - (self.window_start + self.window_size))
        return (before, after)

    def page_older(self) -> bool:
        """
        Page the window to show older entries.

        Returns True if window moved.
        """
        if self.window_start > 0:
            self.window_start = max(0, self.window_start - self.window_size)
            return True
        return False

    def page_newer(self) -> bool:
        """
        Page the window to show newer entries.

        Returns True if window moved.
        """
        max_start = max(0, len(self.entries) - self.window_size)
        if self.window_start < max_start:
            self.window_start = min(max_start, self.window_start + self.window_size)
            return True
        return False

    def _adjust_window(self) -> None:
        """Adjust window to ensure current position is visible."""
        if self.position < self.window_start:
            self.window_start = self.position
        elif self.position >= self.window_start + self.window_size:
            self.window_start = self.position - self.window_size + 1


def count_effective_chars(text: str) -> int:
    """
    Count characters excluding content in [brackets].

    Square brackets and their contents don't count toward the 825 limit.
    This allows for references, citations, or annotations.

    Examples:
        "Hello world" -> 11
        "Hello [citation] world" -> 12 (not 22)
        "The [ref1] quick [ref2] fox" -> 14
    """
    # Remove all [content] patterns (non-greedy)
    clean = re.sub(r'\[.*?\]', '', text)
    return len(clean.strip())


def get_char_status(text: str) -> tuple[int, int, str]:
    """
    Get character count status for card creation.

    Returns:
        (effective_count, total_count, status)
        status is one of: 'ok', 'warn', 'over'
    """
    effective = count_effective_chars(text)
    total = len(text)

    if effective > 825:
        status = 'over'
    elif effective > 700:
        status = 'warn'
    else:
        status = 'ok'

    return (effective, total, status)


class ZettelDB:
    """Database helper for Zettelkasten operations."""

    def __init__(self, db_path: Path = None):
        self.db_path = db_path or DB_PATH

    def get_connection(self) -> sqlite3.Connection:
        """Get a database connection with row factory."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def get_card(self, zettel_id: str) -> Optional[dict]:
        """Get a single card by ID."""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                zettel_id,
                note,
                created_at,
                modified_at
            FROM zettelkasten
            WHERE zettel_id = ?
        """, (zettel_id,))

        row = cursor.fetchone()
        conn.close()

        if row:
            return dict(row)
        return None

    def get_card_with_links(self, zettel_id: str) -> Optional[dict]:
        """Get a card with its outbound and inbound links."""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Get the card
        card = self.get_card(zettel_id)
        if not card:
            conn.close()
            return None

        # Get outbound links
        cursor.execute("""
            SELECT z.zettel_id, z.note
            FROM zettel_links zl
            JOIN zettelkasten z ON zl.to_zettel_id = z.zettel_id
            WHERE zl.from_zettel_id = ?
            ORDER BY z.zettel_id
        """, (zettel_id,))
        card['outbound'] = [dict(r) for r in cursor.fetchall()]

        # Get inbound links
        cursor.execute("""
            SELECT z.zettel_id, z.note
            FROM zettel_links zl
            JOIN zettelkasten z ON zl.from_zettel_id = z.zettel_id
            WHERE zl.to_zettel_id = ?
            ORDER BY z.zettel_id
        """, (zettel_id,))
        card['inbound'] = [dict(r) for r in cursor.fetchall()]

        # Get insights (optional - may not exist in all schemas)
        try:
            cursor.execute("""
                SELECT ii.index_name
                FROM zettel_insight_index zii
                JOIN insight_index ii ON zii.index_id = ii.id
                WHERE zii.zettel_id = ?
            """, (zettel_id,))
            card['insights'] = [r['index_name'] for r in cursor.fetchall()]
        except sqlite3.OperationalError:
            card['insights'] = []

        # Get connection count
        card['connection_count'] = len(card['outbound']) + len(card['inbound'])

        conn.close()
        return card

    def get_paths(self, zettel_id: str, limit: int = 10) -> list[dict]:
        """
        Get 2-hop paths from a card.

        Returns list of {hop1_id, hop2_id, hop2_preview} dicts.
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT DISTINCT
                z2.zettel_id as hop1_id,
                z3.zettel_id as hop2_id,
                z2.note as hop1_note,
                z3.note as hop2_note
            FROM zettel_links zl1
            JOIN zettelkasten z2 ON zl1.to_zettel_id = z2.zettel_id
            JOIN zettel_links zl2 ON z2.zettel_id = zl2.from_zettel_id
            JOIN zettelkasten z3 ON zl2.to_zettel_id = z3.zettel_id
            WHERE zl1.from_zettel_id = ? AND z3.zettel_id != ?
            LIMIT ?
        """, (zettel_id, zettel_id, limit))

        paths = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return paths

    def get_all_cards(self, limit: int = 100, order_by: str = 'created_at DESC') -> list[dict]:
        """Get all cards with connection counts."""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute(f"""
            SELECT
                z.zettel_id,
                z.note,
                z.created_at,
                (
                    SELECT COUNT(*) FROM zettel_links WHERE from_zettel_id = z.zettel_id
                ) + (
                    SELECT COUNT(*) FROM zettel_links WHERE to_zettel_id = z.zettel_id
                ) as connection_count
            FROM zettelkasten z
            ORDER BY {order_by}
            LIMIT ?
        """, (limit,))

        cards = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return cards

    def get_hubs(self, limit: int = 20) -> list[dict]:
        """Get most connected cards."""
        return self.get_all_cards(limit=limit, order_by='connection_count DESC')

    def get_orphans(self) -> list[dict]:
        """Get cards with no connections."""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT z.zettel_id, z.note, z.created_at, 0 as connection_count
            FROM zettelkasten z
            WHERE z.zettel_id NOT IN (
                SELECT from_zettel_id FROM zettel_links
                UNION
                SELECT to_zettel_id FROM zettel_links
            )
            ORDER BY z.created_at DESC
        """)

        orphans = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return orphans

    def search_cards(self, query: str, limit: int = 50) -> list[dict]:
        """Search cards by note content."""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                z.zettel_id,
                z.note,
                z.created_at,
                (
                    SELECT COUNT(*) FROM zettel_links WHERE from_zettel_id = z.zettel_id
                ) + (
                    SELECT COUNT(*) FROM zettel_links WHERE to_zettel_id = z.zettel_id
                ) as connection_count
            FROM zettelkasten z
            WHERE z.note LIKE ?
            ORDER BY z.zettel_id
            LIMIT ?
        """, (f'%{query}%', limit))

        results = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return results

    def get_stats(self) -> dict:
        """Get Zettelkasten statistics."""
        conn = self.get_connection()
        cursor = conn.cursor()

        total_notes = cursor.execute("SELECT COUNT(*) FROM zettelkasten").fetchone()[0]
        total_links = cursor.execute("SELECT COUNT(*) FROM zettel_links").fetchone()[0]

        orphan_count = cursor.execute("""
            SELECT COUNT(*) FROM zettelkasten z
            WHERE z.zettel_id NOT IN (
                SELECT from_zettel_id FROM zettel_links
                UNION
                SELECT to_zettel_id FROM zettel_links
            )
        """).fetchone()[0]

        # Insight count is optional
        try:
            insight_count = cursor.execute("SELECT COUNT(*) FROM insight_index").fetchone()[0]
        except sqlite3.OperationalError:
            insight_count = 0

        conn.close()

        avg_connections = (total_links * 2) / total_notes if total_notes > 0 else 0

        return {
            'total_notes': total_notes,
            'total_links': total_links,
            'orphan_count': orphan_count,
            'insight_count': insight_count,
            'avg_connections': round(avg_connections, 1),
        }

    def get_insight_index(self) -> list[dict]:
        """Get all insights with card counts."""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT
                    ii.id,
                    ii.index_name,
                    COUNT(zii.zettel_id) as card_count
                FROM insight_index ii
                LEFT JOIN zettel_insight_index zii ON ii.id = zii.index_id
                GROUP BY ii.id, ii.index_name
                ORDER BY card_count DESC
            """)
            insights = [dict(r) for r in cursor.fetchall()]
        except sqlite3.OperationalError:
            insights = []

        conn.close()
        return insights

    def get_all_insights_simple(self) -> list[dict]:
        """Get all insights (id, name) without card counts - for tag picker."""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT id, index_name as name
                FROM insight_index
                ORDER BY index_name
            """)
            insights = [dict(r) for r in cursor.fetchall()]
        except sqlite3.OperationalError:
            insights = []

        conn.close()
        return insights

    def search_insights(self, query: str) -> list[dict]:
        """Search insights by name (case-insensitive substring match)."""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT id, index_name as name
                FROM insight_index
                WHERE LOWER(index_name) LIKE LOWER(?)
                ORDER BY index_name
            """, (f'%{query}%',))
            insights = [dict(r) for r in cursor.fetchall()]
        except sqlite3.OperationalError:
            insights = []

        conn.close()
        return insights

    def _slugify(self, name: str) -> str:
        """Convert a name to a slug for insight ID."""
        # Lowercase, replace spaces with hyphens, remove special chars
        slug = name.lower().strip()
        slug = re.sub(r'\s+', '-', slug)
        slug = re.sub(r'[^a-z0-9\-]', '', slug)
        return slug

    def create_insight(self, name: str) -> Optional[str]:
        """
        Create a new insight tag.

        Returns the insight ID (slug) if created, None if already exists.
        """
        insight_id = self._slugify(name)
        if not insight_id:
            return None

        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                "INSERT INTO insight_index (id, index_name) VALUES (?, ?)",
                (insight_id, name.strip())
            )
            conn.commit()
            return insight_id
        except sqlite3.IntegrityError:
            return None  # Already exists
        except sqlite3.OperationalError:
            return None
        finally:
            conn.close()

    def get_card_insights(self, zettel_id: str) -> list[dict]:
        """Get insights for a specific card."""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT ii.id, ii.index_name as name
                FROM zettel_insight_index zii
                JOIN insight_index ii ON zii.index_id = ii.id
                WHERE zii.zettel_id = ?
                ORDER BY ii.index_name
            """, (zettel_id,))
            insights = [dict(r) for r in cursor.fetchall()]
        except sqlite3.OperationalError:
            insights = []

        conn.close()
        return insights

    def add_insight_to_card(self, zettel_id: str, insight_id: str) -> bool:
        """Tag a card with an insight."""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                "INSERT INTO zettel_insight_index (zettel_id, index_id) VALUES (?, ?)",
                (zettel_id, insight_id)
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False  # Already tagged or invalid
        except sqlite3.OperationalError:
            return False
        finally:
            conn.close()

    def remove_insight_from_card(self, zettel_id: str, insight_id: str) -> bool:
        """Remove an insight tag from a card."""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                "DELETE FROM zettel_insight_index WHERE zettel_id = ? AND index_id = ?",
                (zettel_id, insight_id)
            )
            deleted = cursor.rowcount > 0
            conn.commit()
            return deleted
        except sqlite3.OperationalError:
            return False
        finally:
            conn.close()

    def get_cards_by_insight(self, insight_id: str) -> list[dict]:
        """Get all cards tagged with a specific insight."""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT
                    z.zettel_id,
                    z.note,
                    z.created_at,
                    (
                        SELECT COUNT(*) FROM zettel_links WHERE from_zettel_id = z.zettel_id
                    ) + (
                        SELECT COUNT(*) FROM zettel_links WHERE to_zettel_id = z.zettel_id
                    ) as connection_count
                FROM zettelkasten z
                JOIN zettel_insight_index zii ON z.zettel_id = zii.zettel_id
                WHERE zii.index_id = ?
                ORDER BY z.created_at DESC
            """, (insight_id,))
            cards = [dict(r) for r in cursor.fetchall()]
        except sqlite3.OperationalError:
            cards = []

        conn.close()
        return cards

    def card_exists(self, zettel_id: str) -> bool:
        """Check if a card exists."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM zettelkasten WHERE zettel_id = ?", (zettel_id,))
        exists = cursor.fetchone() is not None
        conn.close()
        return exists

    def create_card(self, zettel_id: str, note: str, link_to: list[str] = None) -> bool:
        """
        Create a new card with optional links.

        Returns True if created successfully.
        """
        if self.card_exists(zettel_id):
            return False

        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            # Insert the card
            cursor.execute("""
                INSERT INTO zettelkasten (zettel_id, note, created_at, modified_at)
                VALUES (?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """, (zettel_id, note))

            # Create links
            if link_to:
                for target_id in link_to:
                    if self.card_exists(target_id):
                        cursor.execute("""
                            INSERT INTO zettel_links (from_zettel_id, to_zettel_id)
                            VALUES (?, ?)
                        """, (zettel_id, target_id))

            conn.commit()
            return True
        except Exception:
            conn.rollback()
            return False
        finally:
            conn.close()

    def add_link(self, from_id: str, to_id: str) -> bool:
        """Add a link between two cards."""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            # Check if link exists
            cursor.execute(
                "SELECT 1 FROM zettel_links WHERE from_zettel_id = ? AND to_zettel_id = ?",
                (from_id, to_id)
            )
            if cursor.fetchone():
                return False  # Already exists

            cursor.execute(
                "INSERT INTO zettel_links (from_zettel_id, to_zettel_id) VALUES (?, ?)",
                (from_id, to_id)
            )
            conn.commit()
            return True
        except Exception:
            conn.rollback()
            return False
        finally:
            conn.close()

    def link_exists(self, from_id: str, to_id: str) -> bool:
        """Check if a link already exists between two cards."""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT 1 FROM zettel_links WHERE from_zettel_id = ? AND to_zettel_id = ?",
                (from_id, to_id)
            )
            return cursor.fetchone() is not None
        finally:
            conn.close()

    def append_link_annotation(self, from_id: str, to_id: str, reason: str) -> bool:
        """
        Append a link annotation to a card and create the database link.

        This is the ONLY way to modify card content after creation (append-only model).
        Appends: \\n\\n->{to_id}: {reason}

        Returns True if successful.
        """
        if from_id == to_id:
            return False  # Can't link to self

        if not reason or not reason.strip():
            return False  # Reason is required

        if not self.card_exists(from_id):
            return False  # Source must exist

        if not self.card_exists(to_id):
            return False  # Target must exist

        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            # Check if link already exists
            cursor.execute(
                "SELECT 1 FROM zettel_links WHERE from_zettel_id = ? AND to_zettel_id = ?",
                (from_id, to_id)
            )
            if cursor.fetchone():
                return False  # Link already exists

            # Build annotation
            annotation = f"\n\n→{to_id}: {reason}"

            # Append to note (single transaction)
            cursor.execute(
                "UPDATE zettelkasten SET note = note || ?, modified_at = CURRENT_TIMESTAMP WHERE zettel_id = ?",
                (annotation, from_id)
            )

            # Create link
            cursor.execute(
                "INSERT INTO zettel_links (from_zettel_id, to_zettel_id) VALUES (?, ?)",
                (from_id, to_id)
            )

            conn.commit()
            return True
        except Exception:
            conn.rollback()
            return False
        finally:
            conn.close()

    def delete_link(self, from_id: str, to_id: str) -> bool:
        """Delete a link between two cards. For testing/cleanup."""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "DELETE FROM zettel_links WHERE from_zettel_id = ? AND to_zettel_id = ?",
                (from_id, to_id)
            )
            deleted = cursor.rowcount > 0
            conn.commit()
            return deleted
        except Exception:
            conn.rollback()
            return False
        finally:
            conn.close()

    def delete_card(self, zettel_id: str) -> bool:
        """Delete a card and its links (CASCADE). For testing/cleanup."""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM zettelkasten WHERE zettel_id = ?", (zettel_id,))
            deleted = cursor.rowcount > 0
            conn.commit()
            return deleted
        except Exception:
            conn.rollback()
            return False
        finally:
            conn.close()

    def delete_cards_by_prefix(self, prefix: str) -> int:
        """Delete all cards starting with prefix. Returns count deleted."""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "DELETE FROM zettelkasten WHERE zettel_id LIKE ?",
                (prefix + '%',)
            )
            count = cursor.rowcount
            conn.commit()
            return count
        except Exception:
            conn.rollback()
            return 0
        finally:
            conn.close()

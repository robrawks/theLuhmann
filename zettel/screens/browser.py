"""Note browser screen with DataTable."""

import sqlite3
from pathlib import Path
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Static, DataTable
from textual.containers import Container, Vertical


class BrowserScreen(Screen):
    """Note browser with table view."""

    BINDINGS = [
        ("escape", "app.pop_screen", "Back"),
    ]

    def __init__(self, db_path: Path, mode: str = "all", **kwargs):
        super().__init__(**kwargs)
        self.db_path = db_path
        self.mode = mode  # all, hubs, orphans, search

    def compose(self) -> ComposeResult:
        """Compose the browser."""
        with Container(id="browser-container"):
            yield Static(self._get_title(), id="browser-title")

            with Vertical(id="browser-layout"):
                yield DataTable(id="notes-table", zebra_stripes=True, cursor_type="row")

    def _get_connection(self):
        """Get database connection."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _get_title(self) -> str:
        """Get screen title based on mode."""
        if self.mode == "hubs":
            return "Hub Notes (Most Connected)"
        elif self.mode == "orphans":
            return "Orphaned Notes"
        else:
            return "Browse All Notes"

    def on_mount(self) -> None:
        """Initialize the browser table."""
        table = self.query_one("#notes-table", DataTable)

        # Add columns
        table.add_column("ID", width=15)
        table.add_column("Note", width=60)
        table.add_column("Links", width=8)
        table.add_column("Created", width=12)

        # Load data based on mode
        conn = self._get_connection()
        cursor = conn.cursor()

        if self.mode == "hubs":
            cursor.execute("""
                SELECT
                    z.zettel_id,
                    z.note,
                    (
                        SELECT COUNT(*) FROM zettel_links WHERE from_zettel_id = z.zettel_id
                    ) + (
                        SELECT COUNT(*) FROM zettel_links WHERE to_zettel_id = z.zettel_id
                    ) as connection_count,
                    z.created_at
                FROM zettelkasten z
                ORDER BY connection_count DESC
                LIMIT 50
            """)
        elif self.mode == "orphans":
            cursor.execute("""
                SELECT
                    z.zettel_id,
                    z.note,
                    0 as connection_count,
                    z.created_at
                FROM zettelkasten z
                WHERE z.zettel_id NOT IN (
                    SELECT from_zettel_id FROM zettel_links
                    UNION
                    SELECT to_zettel_id FROM zettel_links
                )
                ORDER BY z.created_at DESC
            """)
        else:  # all
            cursor.execute("""
                SELECT
                    z.zettel_id,
                    z.note,
                    (
                        SELECT COUNT(*) FROM zettel_links WHERE from_zettel_id = z.zettel_id
                    ) + (
                        SELECT COUNT(*) FROM zettel_links WHERE to_zettel_id = z.zettel_id
                    ) as connection_count,
                    z.created_at
                FROM zettelkasten z
                ORDER BY z.created_at DESC
                LIMIT 100
            """)

        notes = cursor.fetchall()
        conn.close()

        # Add rows
        for note in notes:
            # Truncate note text
            text = note['note'].replace('\n', ' ')[:60]
            if len(note['note']) > 60:
                text += "..."

            # Format date
            created = note['created_at'][:10] if note['created_at'] else "unknown"

            table.add_row(
                note['zettel_id'],
                text,
                str(note['connection_count']),
                created,
                key=note['zettel_id']
            )

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle row selection - show card view."""
        zettel_id = event.row_key.value
        self.app.show_card(zettel_id)

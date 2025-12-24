"""Single note card view with links."""

import sqlite3
from pathlib import Path
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Static, DataTable
from textual.containers import Container, Vertical, Horizontal


class CardViewScreen(Screen):
    """Single note card view."""

    BINDINGS = [
        ("escape", "app.pop_screen", "Back"),
    ]

    def __init__(self, db_path: Path, zettel_id: str, **kwargs):
        super().__init__(**kwargs)
        self.db_path = db_path
        self.zettel_id = zettel_id

    def compose(self) -> ComposeResult:
        """Compose the card view."""
        with Container(id="card-container"):
            yield Static(f"Zettel: {self.zettel_id}", id="card-title")

            with Horizontal(id="card-layout"):
                # Left column: Note content
                with Vertical(id="content-column", classes="column"):
                    yield Static("Note Content", classes="section-title")
                    yield Static(self._get_note_content(), id="note-content")
                    yield Static(self._get_metadata(), id="note-metadata", classes="meta-info")

                # Right column: Links
                with Vertical(id="links-column", classes="column"):
                    yield Static("Outbound Links", classes="section-title")
                    yield DataTable(id="outbound-table", zebra_stripes=True, cursor_type="row")

                    yield Static("Inbound Links", classes="section-title")
                    yield DataTable(id="inbound-table", zebra_stripes=True, cursor_type="row")

    def _get_connection(self):
        """Get database connection."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _get_note_content(self) -> str:
        """Get the note content."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT note
            FROM zettelkasten
            WHERE zettel_id = ?
        """, (self.zettel_id,))

        note = cursor.fetchone()
        conn.close()

        if not note:
            return f"Note {self.zettel_id} not found"

        return note['note']

    def _get_metadata(self) -> str:
        """Get note metadata."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                created_at,
                modified_at,
                char_count,
                (
                    SELECT COUNT(*) FROM zettel_links WHERE from_zettel_id = ?
                ) + (
                    SELECT COUNT(*) FROM zettel_links WHERE to_zettel_id = ?
                ) as connection_count
            FROM zettelkasten
            WHERE zettel_id = ?
        """, (self.zettel_id, self.zettel_id, self.zettel_id))

        metadata = cursor.fetchone()
        conn.close()

        if not metadata:
            return ""

        lines = []
        lines.append(f"Created: {metadata['created_at'][:10] if metadata['created_at'] else 'unknown'}")
        lines.append(f"Modified: {metadata['modified_at'][:10] if metadata['modified_at'] else 'unknown'}")
        lines.append(f"Characters: {metadata['char_count'] or len(self._get_note_content())}")
        lines.append(f"Total Connections: {metadata['connection_count']}")

        return "\n".join(lines)

    def on_mount(self) -> None:
        """Initialize the card view."""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Setup outbound links table
        outbound_table = self.query_one("#outbound-table", DataTable)
        outbound_table.add_column("ID", width=15)
        outbound_table.add_column("Note", width=50)

        cursor.execute("""
            SELECT z.zettel_id, z.note
            FROM zettel_links zl
            JOIN zettelkasten z ON zl.to_zettel_id = z.zettel_id
            WHERE zl.from_zettel_id = ?
            ORDER BY z.zettel_id
        """, (self.zettel_id,))

        links_from = cursor.fetchall()

        for link in links_from:
            text = link['note'].replace('\n', ' ')[:50]
            if len(link['note']) > 50:
                text += "..."
            outbound_table.add_row(link['zettel_id'], text, key=link['zettel_id'])

        # Setup inbound links table
        inbound_table = self.query_one("#inbound-table", DataTable)
        inbound_table.add_column("ID", width=15)
        inbound_table.add_column("Note", width=50)

        cursor.execute("""
            SELECT z.zettel_id, z.note
            FROM zettel_links zl
            JOIN zettelkasten z ON zl.from_zettel_id = z.zettel_id
            WHERE zl.to_zettel_id = ?
            ORDER BY z.zettel_id
        """, (self.zettel_id,))

        links_to = cursor.fetchall()

        for link in links_to:
            text = link['note'].replace('\n', ' ')[:50]
            if len(link['note']) > 50:
                text += "..."
            inbound_table.add_row(link['zettel_id'], text, key=link['zettel_id'])

        conn.close()

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle link selection - navigate to linked note."""
        zettel_id = event.row_key.value
        self.app.show_card(zettel_id)

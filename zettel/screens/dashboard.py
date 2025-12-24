"""Dashboard screen showing Zettelkasten overview and stats."""

import sqlite3
from pathlib import Path
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Static, Button
from textual.containers import Container, Vertical, Horizontal


class DashboardScreen(Screen):
    """Dashboard overview screen."""

    BINDINGS = [
        ("escape", "app.pop_screen", "Back"),
    ]

    def __init__(self, db_path: Path, **kwargs):
        super().__init__(**kwargs)
        self.db_path = db_path

    def compose(self) -> ComposeResult:
        """Compose the dashboard."""
        with Container(id="zettel-dashboard"):
            yield Static("Zettelkasten - Knowledge Network", id="dashboard-title")

            with Horizontal(id="stats-row"):
                with Vertical(classes="stat-card"):
                    yield Static(self._get_total_notes(), classes="stat-value")
                    yield Static("Total Notes", classes="stat-label")

                with Vertical(classes="stat-card"):
                    yield Static(self._get_total_links(), classes="stat-value")
                    yield Static("Total Links", classes="stat-label")

                with Vertical(classes="stat-card"):
                    yield Static(self._get_orphan_count(), classes="stat-value")
                    yield Static("Orphans", classes="stat-label")

                with Vertical(classes="stat-card"):
                    yield Static(self._get_avg_connections(), classes="stat-value")
                    yield Static("Avg Connections", classes="stat-label")

            with Horizontal(id="main-layout"):
                # Left column: Recent notes
                with Vertical(id="recent-column", classes="column"):
                    yield Static("Recent Notes", classes="section-title")
                    yield Static(self._get_recent_notes(), id="recent-notes")

                # Middle column: Quick actions
                with Vertical(id="actions-column", classes="column"):
                    yield Static("Quick Actions", classes="section-title")
                    yield Button("Browse All (s)", id="btn-browse", variant="primary")
                    yield Button("New Note (n)", id="btn-new", variant="primary")
                    yield Button("Search (/)", id="btn-search", variant="default")
                    yield Static("")
                    yield Static("Views", classes="section-title")
                    yield Button("Hubs (h)", id="btn-hubs", variant="default")
                    yield Button("Orphans (o)", id="btn-orphans", variant="default")
                    yield Button("Insights (i)", id="btn-insights", variant="default")

                # Right column: Hub notes
                with Vertical(id="hubs-column", classes="column"):
                    yield Static("Hub Notes (Most Connected)", classes="section-title")
                    yield Static(self._get_hub_notes(), id="hub-notes")

    def _get_connection(self):
        """Get database connection."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _get_total_notes(self) -> str:
        """Get total note count."""
        conn = self._get_connection()
        count = conn.execute("SELECT COUNT(*) FROM zettelkasten").fetchone()[0]
        conn.close()
        return str(count)

    def _get_total_links(self) -> str:
        """Get total link count."""
        conn = self._get_connection()
        count = conn.execute("SELECT COUNT(*) FROM zettel_links").fetchone()[0]
        conn.close()
        return str(count)

    def _get_orphan_count(self) -> str:
        """Get orphan count."""
        conn = self._get_connection()
        count = conn.execute("""
            SELECT COUNT(*) FROM zettelkasten z
            WHERE z.zettel_id NOT IN (
                SELECT from_zettel_id FROM zettel_links
                UNION
                SELECT to_zettel_id FROM zettel_links
            )
        """).fetchone()[0]
        conn.close()
        return str(count)

    def _get_avg_connections(self) -> str:
        """Get average connections per note."""
        conn = self._get_connection()
        total_notes = conn.execute("SELECT COUNT(*) FROM zettelkasten").fetchone()[0]
        total_links = conn.execute("SELECT COUNT(*) FROM zettel_links").fetchone()[0]
        conn.close()

        if total_notes == 0:
            return "0.0"

        avg = (total_links * 2) / total_notes
        return f"{avg:.1f}"

    def _get_recent_notes(self) -> str:
        """Get recent notes."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                z.zettel_id,
                z.note,
                (
                    SELECT COUNT(*) FROM zettel_links WHERE from_zettel_id = z.zettel_id
                ) + (
                    SELECT COUNT(*) FROM zettel_links WHERE to_zettel_id = z.zettel_id
                ) as connection_count
            FROM zettelkasten z
            ORDER BY z.created_at DESC
            LIMIT 10
        """)

        notes = cursor.fetchall()
        conn.close()

        if not notes:
            return "No notes yet.\n\nCreate your first note!"

        lines = []
        for note in notes:
            text = note['note'].replace('\n', ' ')[:60]
            if len(note['note']) > 60:
                text += "..."
            lines.append(f"{note['zettel_id']:12} ({note['connection_count']:2} links)")
            lines.append(f"  {text}")
            lines.append("")

        return "\n".join(lines)

    def _get_hub_notes(self) -> str:
        """Get hub notes (most connected)."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                z.zettel_id,
                z.note,
                (
                    SELECT COUNT(*) FROM zettel_links WHERE from_zettel_id = z.zettel_id
                ) + (
                    SELECT COUNT(*) FROM zettel_links WHERE to_zettel_id = z.zettel_id
                ) as connection_count
            FROM zettelkasten z
            ORDER BY connection_count DESC
            LIMIT 10
        """)

        hubs = cursor.fetchall()
        conn.close()

        if not hubs:
            return "No notes yet."

        lines = []
        for hub in hubs:
            if hub['connection_count'] == 0:
                continue
            text = hub['note'].replace('\n', ' ')[:50]
            if len(hub['note']) > 50:
                text += "..."
            lines.append(f"{hub['zettel_id']:12} ({hub['connection_count']:2} links)")
            lines.append(f"  {text}")
            lines.append("")

        return "\n".join(lines) if lines else "No connected notes yet."

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id

        if button_id == "btn-browse":
            self.app.action_show_browser()
        elif button_id == "btn-new":
            self.app.action_new_note()
        elif button_id == "btn-search":
            self.app.action_search()
        elif button_id == "btn-hubs":
            self.app.action_show_hubs()
        elif button_id == "btn-orphans":
            self.app.action_show_orphans()
        elif button_id == "btn-insights":
            self.app.action_show_insights()

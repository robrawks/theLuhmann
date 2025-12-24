"""Search Modal - Quick search overlay."""

from typing import Callable

from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Static, Input, DataTable
from textual.containers import Vertical
from textual.binding import Binding

from zettel.utils import ZettelDB


class SearchModal(ModalScreen):
    """
    Search modal for finding cards by content.

    Features:
    - Live search as you type
    - Results shown in a table
    - Enter to select, Escape to cancel
    """

    BINDINGS = [
        Binding("escape", "dismiss", "Close"),
    ]

    def __init__(
        self,
        db: ZettelDB,
        on_selected: Callable[[str], bool] = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.db = db
        self.on_selected = on_selected

    def compose(self) -> ComposeResult:
        """Compose the search modal."""
        with Vertical(id="search-container"):
            yield Input(placeholder="Search notes...", id="search-input")

            with Vertical(id="search-results"):
                yield DataTable(id="search-table", zebra_stripes=True, cursor_type="row")

    def on_mount(self) -> None:
        """Initialize the modal."""
        # Setup table
        table = self.query_one("#search-table", DataTable)
        table.add_column("ID", width=12)
        table.add_column("Note", width=50)
        table.add_column("#", width=4)

        # Focus search input
        search_input = self.query_one("#search-input", Input)
        search_input.focus()

    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle search input changes."""
        query = event.value.strip()

        table = self.query_one("#search-table", DataTable)
        table.clear()

        if len(query) < 2:
            return

        # Search and populate results
        results = self.db.search_cards(query, limit=20)

        for card in results:
            preview = card['note'].replace('\n', ' ')[:45]
            if len(card['note']) > 45:
                preview += "..."

            table.add_row(
                card['zettel_id'],
                preview,
                str(card['connection_count']),
                key=card['zettel_id']
            )

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle result selection."""
        zettel_id = event.row_key.value
        self.dismiss()
        if self.on_selected:
            self.on_selected(zettel_id)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle Enter in search - select first result."""
        table = self.query_one("#search-table", DataTable)
        if table.row_count > 0:
            # Get first row's zettel_id from first column
            first_row = table.get_row_at(0)
            zettel_id = first_row[0]
            if zettel_id:
                self.dismiss()
                if self.on_selected:
                    self.on_selected(str(zettel_id))

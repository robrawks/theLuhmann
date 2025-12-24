"""Browse Screen - Main entry point with inline filtering and insight index."""

from typing import Callable, Optional

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Static, DataTable, Input
from textual.containers import Vertical, Horizontal
from textual.binding import Binding
from textual.reactive import reactive

from zettel.utils import ZettelDB


class BrowseScreen(Screen):
    """
    Main browse screen - the default entry point.

    Features:
    - Scrollable list of all cards (default view)
    - Inline filter with / key
    - Insight index toggle with i key
    - Hub/orphan quick filters
    - Enter to select → switches to card view
    """

    BINDINGS = [
        Binding("j", "cursor_down", "Down", show=False),
        Binding("k", "cursor_up", "Up", show=False),
        Binding("slash", "start_filter", "Filter", show=True),
        Binding("i", "toggle_insights", "Insights"),
        Binding("h", "show_hubs", "Hubs"),
        Binding("o", "show_orphans", "Orphans"),
        Binding("r", "show_recent", "Recent"),
        Binding("n", "new_card", "New"),
        Binding("escape", "clear_or_quit", "Clear/Quit"),
        Binding("q", "quit_app", "Quit"),
    ]

    # View mode: "cards" or "insights"
    view_mode: reactive[str] = reactive("cards")
    filter_text: reactive[str] = reactive("")
    card_mode: reactive[str] = reactive("recent")  # recent, hubs, orphans

    def __init__(
        self,
        db: ZettelDB = None,
        on_selected: Callable[[str], bool] = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.db = db or ZettelDB()
        self.on_selected = on_selected
        self._all_cards: list[dict] = []
        self._all_insights: list[dict] = []

    def compose(self) -> ComposeResult:
        """Compose the browse screen."""
        with Vertical(id="browse-panel"):
            with Horizontal(id="browse-header"):
                yield Static("ZETTELKASTEN", id="browse-title")
                yield Input(placeholder="Filter...", id="filter-input")
                yield Static("", id="browse-stats")

            yield DataTable(id="browse-table", zebra_stripes=True, cursor_type="row")

            yield Static(
                "[↑↓/jk] navigate  [Enter] select  [/] filter  [i] insights  [h] hubs  [o] orphans  [n] new  [q] quit",
                id="browse-help"
            )

    def on_mount(self) -> None:
        """Initialize the screen."""
        # Setup table
        table = self.query_one("#browse-table", DataTable)
        self._setup_card_columns(table)

        # Hide filter input initially
        filter_input = self.query_one("#filter-input", Input)
        filter_input.display = False

        # Load cards
        self._load_cards()

        # Focus the table
        table.focus()

    def _setup_card_columns(self, table: DataTable) -> None:
        """Setup columns for card view."""
        table.clear(columns=True)
        table.add_column("ID", width=12)
        table.add_column("Note", width=50)
        table.add_column("#", width=4)
        table.add_column("Created", width=10)

    def _setup_insight_columns(self, table: DataTable) -> None:
        """Setup columns for insight index view."""
        table.clear(columns=True)
        table.add_column("Insight", width=30)
        table.add_column("Cards", width=8)

    def _load_cards(self, filter_text: str = "") -> None:
        """Load cards based on current mode and filter."""
        table = self.query_one("#browse-table", DataTable)
        table.clear()

        # Fetch based on mode
        if self.card_mode == "hubs":
            cards = self.db.get_hubs(limit=100)
            title = "[bold cyan]HUBS[/] (Most Connected)"
        elif self.card_mode == "orphans":
            cards = self.db.get_orphans()
            title = "[bold red]ORPHANS[/] (No Connections)"
        else:
            cards = self.db.get_all_cards(order_by='zettel_id')
            title = "[bold cyan]ZETTELKASTEN[/]"

        self._all_cards = cards

        # Apply filter (zettel_id only - numeric search)
        if filter_text:
            cards = [c for c in cards if filter_text in c['zettel_id']]
            title += f" [dim](id: {filter_text})[/]"

        # Update title and stats
        self.query_one("#browse-title", Static).update(title)
        self.query_one("#browse-stats", Static).update(f"[dim]{len(cards)} notes[/]")

        # Populate table
        for card in cards:
            preview = card['note'].replace('\n', ' ')[:45]
            if len(card['note']) > 45:
                preview += "..."

            created = card['created_at'][:10] if card['created_at'] else ''

            table.add_row(
                card['zettel_id'],
                preview,
                str(card['connection_count']),
                created,
                key=card['zettel_id']
            )

    def _load_insights(self, filter_text: str = "") -> None:
        """Load insight index."""
        table = self.query_one("#browse-table", DataTable)
        table.clear()

        insights = self.db.get_insight_index()
        self._all_insights = insights

        # Apply filter
        if filter_text:
            filter_lower = filter_text.lower()
            insights = [i for i in insights if filter_lower in i['index_name'].lower()]

        # Update title
        title = "[bold purple]INSIGHT INDEX[/]"
        if filter_text:
            title += f" [dim](filter: {filter_text})[/]"
        self.query_one("#browse-title", Static).update(title)
        self.query_one("#browse-stats", Static).update(f"[dim]{len(insights)} tags[/]")

        # Populate table
        for insight in insights:
            table.add_row(
                insight['index_name'],
                str(insight['card_count']),
                key=f"insight:{insight['id']}"
            )

    def action_start_filter(self) -> None:
        """Show and focus the filter input."""
        filter_input = self.query_one("#filter-input", Input)
        filter_input.display = True
        filter_input.value = ""
        # Update placeholder based on view mode
        if self.view_mode == "insights":
            filter_input.placeholder = "Search insights..."
        else:
            filter_input.placeholder = "Filter by ID..."
        filter_input.focus()

    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle filter input changes."""
        if event.input.id == "filter-input":
            self.filter_text = event.value
            if self.view_mode == "insights":
                self._load_insights(event.value)
            else:
                self._load_cards(event.value)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle filter input submit - refocus table."""
        if event.input.id == "filter-input":
            table = self.query_one("#browse-table", DataTable)
            table.focus()

    def action_toggle_insights(self) -> None:
        """Toggle between cards and insight index view."""
        table = self.query_one("#browse-table", DataTable)

        if self.view_mode == "cards":
            self.view_mode = "insights"
            self._setup_insight_columns(table)
            self._load_insights(self.filter_text)
        else:
            self.view_mode = "cards"
            self._setup_card_columns(table)
            self._load_cards(self.filter_text)

        table.focus()

    def action_show_hubs(self) -> None:
        """Show most connected cards."""
        self.view_mode = "cards"
        self.card_mode = "hubs"
        table = self.query_one("#browse-table", DataTable)
        self._setup_card_columns(table)
        self._load_cards(self.filter_text)
        table.focus()

    def action_show_orphans(self) -> None:
        """Show orphan cards."""
        self.view_mode = "cards"
        self.card_mode = "orphans"
        table = self.query_one("#browse-table", DataTable)
        self._setup_card_columns(table)
        self._load_cards(self.filter_text)
        table.focus()

    def action_show_recent(self) -> None:
        """Show recent cards (default)."""
        self.view_mode = "cards"
        self.card_mode = "recent"
        table = self.query_one("#browse-table", DataTable)
        self._setup_card_columns(table)
        self._load_cards(self.filter_text)
        table.focus()

    def action_clear_or_quit(self) -> None:
        """Clear filter or quit if no filter."""
        filter_input = self.query_one("#filter-input", Input)

        if filter_input.display and filter_input.value:
            # Clear filter
            filter_input.value = ""
            filter_input.display = False
            self.filter_text = ""
            if self.view_mode == "insights":
                self._load_insights()
            else:
                self._load_cards()
            self.query_one("#browse-table", DataTable).focus()
        elif filter_input.display:
            # Just hide empty filter
            filter_input.display = False
            self.query_one("#browse-table", DataTable).focus()
        else:
            # No filter active - quit
            self.app.exit()

    def action_quit_app(self) -> None:
        """Quit the application."""
        self.app.exit()

    def action_new_card(self) -> None:
        """Create a new card."""
        from zettel.screens.create_modal import CreateModal
        self.app.push_screen(CreateModal(db=self.db, on_created=self._on_card_created))

    def _on_card_created(self, zettel_id: str) -> None:
        """Handle newly created card."""
        self._load_cards(self.filter_text)
        self.notify(f"Created {zettel_id}")

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle row selection."""
        key = event.row_key.value

        if self.view_mode == "insights" and key.startswith("insight:"):
            # Selected an insight - show cards with this insight
            insight_id = key.split(":")[1]
            self._show_cards_by_insight(insight_id)
        else:
            # Selected a card - switch to card view
            if self.on_selected:
                self.on_selected(key)
            else:
                # Push main screen with this card
                from zettel.screens.main import MainScreen
                self.app.push_screen(MainScreen(initial_card=key))

    def _show_cards_by_insight(self, insight_id: str) -> None:
        """Show cards filtered by a specific insight."""
        table = self.query_one("#browse-table", DataTable)

        # Switch to cards view mode
        self.view_mode = "cards"
        self.card_mode = "insight"
        self._setup_card_columns(table)

        # Get cards with this insight
        cards = self.db.get_cards_by_insight(insight_id)
        self._all_cards = cards

        # Find insight name for title
        insight_name = insight_id
        for i in self._all_insights:
            if i['id'] == insight_id:
                insight_name = i['index_name']
                break

        # Update title and stats
        self.query_one("#browse-title", Static).update(f"[bold purple]#{insight_name}[/]")
        self.query_one("#browse-stats", Static).update(f"[dim]{len(cards)} notes[/]")

        # Populate table
        table.clear()
        for card in cards:
            preview = card['note'].replace('\n', ' ')[:45]
            if len(card['note']) > 45:
                preview += "..."

            created = card['created_at'][:10] if card['created_at'] else ''

            table.add_row(
                card['zettel_id'],
                preview,
                str(card['connection_count']),
                created,
                key=card['zettel_id']
            )

        table.focus()

    def action_cursor_down(self) -> None:
        """Move cursor down (vim binding)."""
        table = self.query_one("#browse-table", DataTable)
        table.action_cursor_down()

    def action_cursor_up(self) -> None:
        """Move cursor up (vim binding)."""
        table = self.query_one("#browse-table", DataTable)
        table.action_cursor_up()

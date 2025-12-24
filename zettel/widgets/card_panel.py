"""Card Panel - Main content display for a single zettel."""

from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Static
from textual.containers import Horizontal, VerticalScroll
from textual.reactive import reactive

from zettel.utils import ZettelDB, count_effective_chars


class CardPanel(Widget):
    """
    Card content panel showing a single zettel.

    Displays:
    - Card ID and metadata (created date, char count, link count)
    - Full note content (scrollable)
    - Insight tags
    """

    # Reactive card data
    zettel_id: reactive[str] = reactive("")
    note_content: reactive[str] = reactive("")
    created_at: reactive[str] = reactive("")
    char_count: reactive[int] = reactive(0)
    connection_count: reactive[int] = reactive(0)
    insights: reactive[list[str]] = reactive([])

    def __init__(self, db: ZettelDB = None, **kwargs):
        super().__init__(**kwargs)
        self.db = db or ZettelDB()

    def compose(self) -> ComposeResult:
        """Compose the card panel."""
        with Horizontal(id="card-header"):
            yield Static("", id="card-id")
            yield Static("", id="card-meta")

        with VerticalScroll(id="card-content"):
            yield Static("", id="card-text")

        yield Static("", id="card-insights")

    def load_card(self, zettel_id: str) -> bool:
        """
        Load a card by ID.

        Returns True if card was found and loaded.
        """
        card = self.db.get_card_with_links(zettel_id)
        if not card:
            return False

        self.zettel_id = card['zettel_id']
        self.note_content = card['note']
        self.created_at = card['created_at'][:10] if card['created_at'] else 'unknown'
        self.char_count = count_effective_chars(card['note'])
        self.connection_count = card['connection_count']
        self.insights = card.get('insights', [])

        self._update_display()
        return True

    def _update_display(self) -> None:
        """Update the display widgets."""
        # Update ID
        id_widget = self.query_one("#card-id", Static)
        id_widget.update(f"[bold cyan]{self.zettel_id}[/]")

        # Update metadata
        meta_widget = self.query_one("#card-meta", Static)
        meta_widget.update(
            f"[dim]{self.created_at}  |  {self.char_count} chars  |  {self.connection_count} links[/]"
        )

        # Update content
        text_widget = self.query_one("#card-text", Static)
        text_widget.update(self.note_content)

        # Update insights
        insights_widget = self.query_one("#card-insights", Static)
        if self.insights:
            tags = "  ".join([f"[purple]#{tag}[/]" for tag in self.insights])
            insights_widget.update(tags)
        else:
            insights_widget.update("")

    def clear(self) -> None:
        """Clear the card display."""
        self.zettel_id = ""
        self.note_content = ""
        self.created_at = ""
        self.char_count = 0
        self.connection_count = 0
        self.insights = []

        # Clear widgets
        self.query_one("#card-id", Static).update("[dim]No card selected[/]")
        self.query_one("#card-meta", Static).update("")
        self.query_one("#card-text", Static).update(
            "[dim]Use [b]/[/b] to search or [b]b[/b] to browse cards[/]"
        )
        self.query_one("#card-insights", Static).update("")

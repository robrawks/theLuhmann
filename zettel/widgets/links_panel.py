"""Links Panel - Outbound and inbound links with hotkey navigation."""

from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Static
from textual.containers import Vertical, Horizontal
from textual.reactive import reactive
from textual.message import Message

from zettel.utils import ZettelDB


class LinksPanel(Widget):
    """
    Links panel showing outbound and inbound connections.

    Features:
    - Numbered links (1-3 outbound, 4-6 inbound) for quick jumping
    - Truncated previews of linked cards
    - Visual distinction between directions
    """

    class LinkJump(Message):
        """Message sent when user jumps to a linked card."""
        def __init__(self, zettel_id: str) -> None:
            self.zettel_id = zettel_id
            super().__init__()

    # Reactive data
    zettel_id: reactive[str] = reactive("")
    outbound: reactive[list[dict]] = reactive([])
    inbound: reactive[list[dict]] = reactive([])

    def __init__(self, db: ZettelDB = None, **kwargs):
        super().__init__(**kwargs)
        self.db = db or ZettelDB()

    def compose(self) -> ComposeResult:
        """Compose the links panel."""
        with Horizontal(id="links-sections"):
            with Vertical(id="outbound-section"):
                yield Static("[bold #d4a574]OUTBOUND →[/]", classes="links-title")
                yield Static("", id="outbound-list")

            with Vertical(id="inbound-section"):
                yield Static("[bold #d4a574]← INBOUND[/]", classes="links-title")
                yield Static("", id="inbound-list")

    def load_links(self, zettel_id: str) -> None:
        """Load links for a card."""
        self.zettel_id = zettel_id

        card = self.db.get_card_with_links(zettel_id)
        if card:
            self.outbound = card.get('outbound', [])
            self.inbound = card.get('inbound', [])
        else:
            self.outbound = []
            self.inbound = []

        self._update_display()

    def _update_display(self) -> None:
        """Update the display widgets."""
        # Update outbound list
        outbound_widget = self.query_one("#outbound-list", Static)
        if self.outbound:
            lines = []
            for i, link in enumerate(self.outbound[:3], 1):
                preview = self._truncate(link['note'], 35)
                lines.append(f"[cyan bold][{i}][/] [#d4a574]{link['zettel_id']:12}[/]")
                lines.append(f"    [dim]{preview}[/]")
            outbound_widget.update("\n".join(lines))
        else:
            outbound_widget.update("[dim]  (no outbound links)[/]")

        # Update inbound list
        inbound_widget = self.query_one("#inbound-list", Static)
        if self.inbound:
            lines = []
            for i, link in enumerate(self.inbound[:3], 4):
                preview = self._truncate(link['note'], 35)
                lines.append(f"[cyan bold][{i}][/] [#d4a574]{link['zettel_id']:12}[/]")
                lines.append(f"    [dim]{preview}[/]")
            inbound_widget.update("\n".join(lines))
        else:
            inbound_widget.update("[dim]  (no inbound links)[/]")

    def _truncate(self, text: str, max_len: int) -> str:
        """Truncate text and clean newlines."""
        clean = text.replace('\n', ' ')
        if len(clean) > max_len:
            return clean[:max_len] + "..."
        return clean

    def handle_key(self, key: str) -> bool:
        """
        Handle a keypress for link navigation.

        Keys 1-3 jump to outbound links.
        Keys 4-6 jump to inbound links.

        Returns True if the key was handled.
        """
        if not key.isdigit():
            return False

        num = int(key)

        # Outbound links: 1, 2, 3
        if 1 <= num <= 3:
            idx = num - 1
            if idx < len(self.outbound):
                self.post_message(self.LinkJump(self.outbound[idx]['zettel_id']))
                return True

        # Inbound links: 4, 5, 6
        elif 4 <= num <= 6:
            idx = num - 4
            if idx < len(self.inbound):
                self.post_message(self.LinkJump(self.inbound[idx]['zettel_id']))
                return True

        return False

    def get_link_by_number(self, num: int) -> str | None:
        """Get the zettel_id for a numbered link."""
        if 1 <= num <= 3:
            idx = num - 1
            if idx < len(self.outbound):
                return self.outbound[idx]['zettel_id']
        elif 4 <= num <= 6:
            idx = num - 4
            if idx < len(self.inbound):
                return self.inbound[idx]['zettel_id']
        return None

    def clear(self) -> None:
        """Clear the links display."""
        self.zettel_id = ""
        self.outbound = []
        self.inbound = []
        self.query_one("#outbound-list", Static).update("[dim]  (no card selected)[/]")
        self.query_one("#inbound-list", Static).update("[dim]  (no card selected)[/]")

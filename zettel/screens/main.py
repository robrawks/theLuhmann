"""Main Screen - Single screen with all panels for Zettelkasten navigation."""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Static, Footer
from textual.containers import Horizontal, Vertical
from textual.binding import Binding

from zettel.widgets.trail_panel import TrailPanel
from zettel.widgets.card_panel import CardPanel
from zettel.widgets.links_panel import LinksPanel
from zettel.utils import SessionTrail, ZettelDB


class MainScreen(Screen):
    """
    Main Zettelkasten screen with persistent panels.

    Layout:
    ┌─────────────────────────────────────┬──────────────┐
    │           CARD PANEL                │    TRAIL     │
    │  (content, metadata)                │   PANEL      │
    ├─────────────────────────────────────│              │
    │           LINKS PANEL               │              │
    │  (outbound [1-3], inbound [4-6])    │              │
    └─────────────────────────────────────┴──────────────┘

    Keybindings:
    - 1-6: Jump to numbered links (1-3 outbound, 4-6 inbound)
    - Backspace: Go back in trail
    - Backslash: Go forward in trail
    - Tab: Focus trail panel (then ↑↓ to navigate, Enter to jump)
    - ← / → or [ / ]: Page trail window (older/newer)
    - Escape: Return to browser (or unfocus trail)
    - n: New card
    - p: Show paths
    - /: Search
    - q: Quit
    """

    BINDINGS = [
        # Link jumping (1-6)
        Binding("1", "jump_1", "Link 1", show=False),
        Binding("2", "jump_2", "Link 2", show=False),
        Binding("3", "jump_3", "Link 3", show=False),
        Binding("4", "jump_4", "Link 4", show=False),
        Binding("5", "jump_5", "Link 5", show=False),
        Binding("6", "jump_6", "Link 6", show=False),
        # Trail navigation
        Binding("backspace", "go_back", "Back", show=True),
        Binding("backslash", "go_forward", "Fwd", show=True),
        Binding("left", "trail_older", "← Page", show=False),
        Binding("right", "trail_newer", "→ Page", show=False),
        Binding("tab", "focus_trail", "Trail", show=True),
        # Other actions
        Binding("escape", "back_to_browser", "Browser"),
        Binding("n", "new_card", "New"),
        Binding("l", "add_link", "Link"),
        Binding("p", "show_paths", "Paths"),
        Binding("slash", "search", "Search"),
        Binding("s", "show_stats", "Stats"),
        Binding("q", "quit", "Quit"),
    ]

    def __init__(self, initial_card: str = None, **kwargs):
        super().__init__(**kwargs)
        self.trail = SessionTrail()  # Window size set dynamically by TrailPanel
        self.db = ZettelDB()
        self._current_card: str | None = None
        self._initial_card: str | None = initial_card

    def compose(self) -> ComposeResult:
        """Compose the main screen."""
        with Horizontal(id="main-container"):
            with Vertical(id="content-area"):
                yield CardPanel(db=self.db, id="card-widget")
                yield LinksPanel(db=self.db, id="links-widget")

            with Vertical(id="trail-area"):
                yield TrailPanel(trail=self.trail, id="trail-widget")

        yield Footer()

    def on_mount(self) -> None:
        """Initialize the screen."""
        if self._initial_card:
            # Load the initial card directly
            self.checkout_card(self._initial_card)
        else:
            # Show welcome state
            card_panel = self.query_one("#card-widget", CardPanel)
            card_panel.clear()

            links_panel = self.query_one("#links-widget", LinksPanel)
            links_panel.clear()

    def checkout_card(self, zettel_id: str) -> bool:
        """
        Check out a card and update all panels.

        Returns True if card was found.
        """
        card_panel = self.query_one("#card-widget", CardPanel)
        links_panel = self.query_one("#links-widget", LinksPanel)
        trail_panel = self.query_one("#trail-widget", TrailPanel)

        # Try to load the card
        if not card_panel.load_card(zettel_id):
            self.notify(f"Card {zettel_id} not found", severity="error")
            return False

        # Update links panel
        links_panel.load_links(zettel_id)

        # Add to trail
        trail_panel.checkout(zettel_id)

        self._current_card = zettel_id
        return True

    # Link jumping actions
    def action_jump_1(self) -> None:
        self._jump_to_link(1)

    def action_jump_2(self) -> None:
        self._jump_to_link(2)

    def action_jump_3(self) -> None:
        self._jump_to_link(3)

    def action_jump_4(self) -> None:
        self._jump_to_link(4)

    def action_jump_5(self) -> None:
        self._jump_to_link(5)

    def action_jump_6(self) -> None:
        self._jump_to_link(6)

    def _jump_to_link(self, num: int) -> None:
        """Jump to a numbered link."""
        links_panel = self.query_one("#links-widget", LinksPanel)
        zettel_id = links_panel.get_link_by_number(num)
        if zettel_id:
            self.checkout_card(zettel_id)
        else:
            self.notify(f"No link [{num}]", severity="warning")

    # Trail navigation actions
    def action_trail_older(self) -> None:
        """Page trail to show older entries."""
        trail_panel = self.query_one("#trail-widget", TrailPanel)
        if self.trail.page_older():
            trail_panel.refresh_trail()

    def action_trail_newer(self) -> None:
        """Page trail to show newer entries."""
        trail_panel = self.query_one("#trail-widget", TrailPanel)
        if self.trail.page_newer():
            trail_panel.refresh_trail()

    def action_back_to_browser(self) -> None:
        """Return to the browse screen."""
        self.app.pop_screen()

    def _load_card_without_trail(self, zettel_id: str) -> None:
        """Load a card without adding to trail (for trail jumps)."""
        card_panel = self.query_one("#card-widget", CardPanel)
        links_panel = self.query_one("#links-widget", LinksPanel)

        if card_panel.load_card(zettel_id):
            links_panel.load_links(zettel_id)
            self._current_card = zettel_id

    def action_go_back(self) -> None:
        """Go back in the trail."""
        trail_panel = self.query_one("#trail-widget", TrailPanel)
        zettel_id = trail_panel.go_back()
        if zettel_id:
            self._load_card_without_trail(zettel_id)
        else:
            self.notify("At start of trail")

    def action_go_forward(self) -> None:
        """Go forward in the trail."""
        trail_panel = self.query_one("#trail-widget", TrailPanel)
        zettel_id = trail_panel.go_forward()
        if zettel_id:
            self._load_card_without_trail(zettel_id)
        else:
            self.notify("At end of trail")

    def action_focus_trail(self) -> None:
        """Focus the trail panel for keyboard navigation."""
        trail_panel = self.query_one("#trail-widget", TrailPanel)
        trail_panel.focus()

    def on_trail_panel_trail_selected(self, message: TrailPanel.TrailSelected) -> None:
        """Handle trail entry selection from focused trail panel."""
        self._load_card_without_trail(message.zettel_id)
        # Keep trail panel display updated
        trail_panel = self.query_one("#trail-widget", TrailPanel)
        trail_panel.refresh_trail()

    def action_new_card(self) -> None:
        """Open the new card modal."""
        from zettel.screens.create_modal import CreateModal
        self.app.push_screen(CreateModal(db=self.db, on_created=self._on_card_created))

    def action_add_link(self) -> None:
        """Open the link modal to add an annotated link from current card."""
        if not self._current_card:
            self.notify("No card selected")
            return

        from zettel.screens.link_modal import LinkModal
        self.app.push_screen(LinkModal(
            from_id=self._current_card,
            db=self.db,
            on_linked=self._on_link_created
        ))

    def _on_link_created(self, from_id: str, to_id: str) -> None:
        """Handle a newly created link - refresh the card display."""
        # Reload current card to show the appended annotation
        card_panel = self.query_one("#card-widget", CardPanel)
        card_panel.load_card(from_id)

        # Refresh links panel to show new outbound link
        links_panel = self.query_one("#links-widget", LinksPanel)
        links_panel.load_links(from_id)

        self.notify(f"Linked {from_id} → {to_id}", severity="information")

    def _on_card_created(self, zettel_id: str) -> None:
        """Handle a newly created card."""
        self.checkout_card(zettel_id)
        self.notify(f"Created {zettel_id}", severity="information")

    def action_show_paths(self) -> None:
        """Show paths from current card."""
        if not self._current_card:
            self.notify("No card selected")
            return

        from zettel.screens.paths_modal import PathsModal
        self.app.push_screen(PathsModal(
            zettel_id=self._current_card,
            db=self.db,
            on_path_selected=self._on_path_selected
        ))

    def _on_path_selected(self, path: list[str]) -> None:
        """Handle a path selection - walk the path."""
        for zettel_id in path:
            self.checkout_card(zettel_id)

    def action_search(self) -> None:
        """Open search overlay."""
        from zettel.screens.search_modal import SearchModal
        self.app.push_screen(SearchModal(
            db=self.db,
            on_selected=self.checkout_card
        ))

    def action_browse(self) -> None:
        """Open browse screen."""
        from zettel.screens.browse_screen import BrowseScreen
        self.app.push_screen(BrowseScreen(
            db=self.db,
            mode="all",
            on_selected=self.checkout_card
        ))

    def action_show_hubs(self) -> None:
        """Show hub cards."""
        from zettel.screens.browse_screen import BrowseScreen
        self.app.push_screen(BrowseScreen(
            db=self.db,
            mode="hubs",
            on_selected=self.checkout_card
        ))

    def action_show_orphans(self) -> None:
        """Show orphan cards."""
        from zettel.screens.browse_screen import BrowseScreen
        self.app.push_screen(BrowseScreen(
            db=self.db,
            mode="orphans",
            on_selected=self.checkout_card
        ))

    def action_show_stats(self) -> None:
        """Show Zettelkasten statistics."""
        stats = self.db.get_stats()
        self.notify(
            f"Notes: {stats['total_notes']}  |  "
            f"Links: {stats['total_links']}  |  "
            f"Orphans: {stats['orphan_count']}  |  "
            f"Avg: {stats['avg_connections']}",
            title="Zettelkasten Stats"
        )

    def on_trail_panel_trail_jump(self, message: TrailPanel.TrailJump) -> None:
        """Handle trail jump message."""
        self._load_card_without_trail(message.zettel_id)

    def on_links_panel_link_jump(self, message: LinksPanel.LinkJump) -> None:
        """Handle link jump message."""
        self.checkout_card(message.zettel_id)

    def on_key(self, event) -> None:
        """Handle key events for trail paging."""
        if event.key == "[" or event.key == "bracketleft":
            trail_panel = self.query_one("#trail-widget", TrailPanel)
            if self.trail.page_older():
                trail_panel.refresh_trail()
                event.stop()

        elif event.key == "]" or event.key == "bracketright":
            trail_panel = self.query_one("#trail-widget", TrailPanel)
            if self.trail.page_newer():
                trail_panel.refresh_trail()
                event.stop()

"""theLuhmann - Zettelkasten TUI Application."""

from pathlib import Path
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Header, Footer

from .screens.browse_screen import BrowseScreen
from .screens.main import MainScreen
from config import DB_PATH, STYLES_PATH


class ZettelApp(App):
    """
    theLuhmann - Zettelkasten TUI inspired by Niklas Luhmann.

    Two-mode application:
    - Browse Mode (default): Scrollable list of all cards with filtering
    - Card Mode: 3-panel view with card content, links, and trail

    Key Features:
    - Browse all cards with inline filtering
    - Quick card hopping via number keys (1-6 for links)
    - Session trail with backtracking
    - 2-hop path discovery
    - Annotated linking (append-only)
    """

    TITLE = "theLuhmann"
    CSS_PATH = str(STYLES_PATH)

    BINDINGS = [
        Binding("q", "quit", "Quit"),
    ]

    def __init__(self, initial_card: str = None, **kwargs):
        super().__init__(**kwargs)
        self.db_path = DB_PATH
        self.initial_card = initial_card

    def compose(self) -> ComposeResult:
        """Compose the app UI."""
        yield Header()
        yield Footer()

    def on_mount(self) -> None:
        """Initialize the app."""
        if self.initial_card:
            # Go directly to card view if card specified
            self.push_screen(MainScreen(initial_card=self.initial_card))
        else:
            # Default to browse screen
            self.push_screen(BrowseScreen())


def main(card: str = None) -> None:
    """Run the Zettelkasten app."""
    app = ZettelApp(initial_card=card)
    app.run()


if __name__ == "__main__":
    import sys
    initial = sys.argv[1] if len(sys.argv) > 1 else None
    main(initial)

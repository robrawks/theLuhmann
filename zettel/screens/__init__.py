"""Zettelkasten TUI screens."""

from zettel.screens.main import MainScreen
from zettel.screens.browse_screen import BrowseScreen
from zettel.screens.create_modal import CreateModal
from zettel.screens.paths_modal import PathsModal
from zettel.screens.search_modal import SearchModal

# Keep old screens for reference (can delete later)
# from .dashboard import DashboardScreen
# from .browser import BrowserScreen
# from .card_view import CardViewScreen

__all__ = [
    'MainScreen',
    'BrowseScreen',
    'CreateModal',
    'PathsModal',
    'SearchModal',
]

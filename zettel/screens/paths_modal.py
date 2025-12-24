"""Paths Modal - 2-hop path discovery from a card."""

from typing import Callable, Optional

from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Static
from textual.containers import Vertical, VerticalScroll
from textual.binding import Binding

from zettel.utils import ZettelDB


class PathsModal(ModalScreen):
    """
    Modal showing 2-hop paths from a card.

    Allows exploring how ideas connect through intermediate cards.
    Press 1-9 to walk a path (adds all cards to trail).
    """

    BINDINGS = [
        Binding("escape", "dismiss", "Close"),
        Binding("1", "select_1", "", show=False),
        Binding("2", "select_2", "", show=False),
        Binding("3", "select_3", "", show=False),
        Binding("4", "select_4", "", show=False),
        Binding("5", "select_5", "", show=False),
        Binding("6", "select_6", "", show=False),
        Binding("7", "select_7", "", show=False),
        Binding("8", "select_8", "", show=False),
        Binding("9", "select_9", "", show=False),
    ]

    def __init__(
        self,
        zettel_id: str,
        db: ZettelDB,
        on_path_selected: Callable[[list[str]], None] = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.zettel_id = zettel_id
        self.db = db
        self.on_path_selected = on_path_selected
        self.paths: list[dict] = []

    def compose(self) -> ComposeResult:
        """Compose the paths modal."""
        with Vertical(id="paths-container"):
            yield Static(f"PATHS FROM {self.zettel_id}", id="paths-title")

            with VerticalScroll(id="paths-list"):
                yield Static("", id="paths-content")

            yield Static("[1-9] Walk path  [Esc] Close", id="paths-help")

    def on_mount(self) -> None:
        """Load paths on mount."""
        self.paths = self.db.get_paths(self.zettel_id, limit=9)
        self._update_display()

    def _update_display(self) -> None:
        """Update the paths display."""
        content = self.query_one("#paths-content", Static)

        if not self.paths:
            content.update("[dim]No 2-hop paths found from this card.[/]")
            return

        lines = []
        for i, path in enumerate(self.paths, 1):
            hop1_id = path['hop1_id']
            hop2_id = path['hop2_id']
            hop2_preview = path['hop2_note'].replace('\n', ' ')[:50]

            lines.append(
                f"[cyan bold][{i}][/] [#d4a574]{self.zettel_id}[/] → "
                f"[#d4a574]{hop1_id}[/] → [#d4a574]{hop2_id}[/]"
            )
            lines.append(f"    [dim]└─ {hop2_preview}...[/]")
            lines.append("")

        content.update("\n".join(lines))

    def _select_path(self, num: int) -> None:
        """Select and walk a path."""
        if 1 <= num <= len(self.paths):
            path = self.paths[num - 1]
            # Return the full path: start → hop1 → hop2
            path_ids = [self.zettel_id, path['hop1_id'], path['hop2_id']]
            self.dismiss()
            if self.on_path_selected:
                self.on_path_selected(path_ids)

    def action_select_1(self) -> None:
        self._select_path(1)

    def action_select_2(self) -> None:
        self._select_path(2)

    def action_select_3(self) -> None:
        self._select_path(3)

    def action_select_4(self) -> None:
        self._select_path(4)

    def action_select_5(self) -> None:
        self._select_path(5)

    def action_select_6(self) -> None:
        self._select_path(6)

    def action_select_7(self) -> None:
        self._select_path(7)

    def action_select_8(self) -> None:
        self._select_path(8)

    def action_select_9(self) -> None:
        self._select_path(9)

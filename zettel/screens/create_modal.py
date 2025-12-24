"""Create Modal - New card creation with live character counting."""

from typing import Callable, Optional

from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Static, Input, TextArea, Button
from textual.containers import Vertical, Horizontal
from textual.binding import Binding

from zettel.utils import ZettelDB, get_char_status


class CreateModal(ModalScreen):
    """
    Modal for creating a new Zettel card.

    Features:
    - Live character counting with [] exclusion
    - Color-coded warnings (green < 700, yellow < 825, red > 825)
    - Link validation
    - Cancel with Escape
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
    ]

    def __init__(
        self,
        db: ZettelDB,
        on_created: Callable[[str], None] = None,
        initial_id: str = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.db = db
        self.on_created = on_created
        self.initial_id = initial_id

    def compose(self) -> ComposeResult:
        """Compose the create modal."""
        with Vertical(id="create-container"):
            yield Static("CREATE NEW ZETTEL", id="create-title")

            with Horizontal(id="create-id-row"):
                yield Static("Card ID:", id="create-id-label")
                yield Input(
                    placeholder="e.g., 1620/1a",
                    id="create-id-input",
                    value=self.initial_id or ""
                )

            with Vertical(id="create-content-area"):
                yield Static("Note Content:", id="create-content-label")
                yield TextArea(id="create-textarea")
                yield Static("", id="create-char-count")

            with Horizontal(id="create-links-row"):
                yield Static("Link to:", id="create-links-label")
                yield Input(
                    placeholder="Space-separated IDs (optional)",
                    id="create-links-input"
                )

            with Horizontal(id="create-buttons"):
                yield Button("Create", variant="primary", id="btn-create")
                yield Button("Cancel", id="btn-cancel")

    def on_mount(self) -> None:
        """Initialize the modal."""
        self._update_char_count()

        # Focus the ID input first
        id_input = self.query_one("#create-id-input", Input)
        id_input.focus()

    def on_text_area_changed(self, event: TextArea.Changed) -> None:
        """Handle text changes in the content area."""
        self._update_char_count()

    def _update_char_count(self) -> None:
        """Update the character count display."""
        textarea = self.query_one("#create-textarea", TextArea)
        text = textarea.text

        effective, total, status = get_char_status(text)

        count_widget = self.query_one("#create-char-count", Static)

        if status == 'over':
            style_class = "char-count-over"
            msg = f"[bold red]{effective}[/] / 825 chars (OVER LIMIT!)"
            if effective != total:
                msg += f" [dim]({total} total, {total - effective} in [])[/]"
        elif status == 'warn':
            style_class = "char-count-warn"
            msg = f"[yellow]{effective}[/] / 825 chars"
            if effective != total:
                msg += f" [dim]({total} total)[/]"
        else:
            style_class = "char-count-ok"
            msg = f"[green]{effective}[/] / 825 chars"
            if effective != total:
                msg += f" [dim]({total} total)[/]"

        count_widget.update(msg)
        count_widget.remove_class("char-count-ok", "char-count-warn", "char-count-over")
        count_widget.add_class(style_class)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "btn-create":
            self._do_create()
        elif event.button.id == "btn-cancel":
            self.action_cancel()

    def _do_create(self) -> None:
        """Attempt to create the card."""
        # Get values
        id_input = self.query_one("#create-id-input", Input)
        textarea = self.query_one("#create-textarea", TextArea)
        links_input = self.query_one("#create-links-input", Input)

        zettel_id = id_input.value.strip()
        note = textarea.text.strip()
        links_text = links_input.value.strip()

        # Validate ID
        if not zettel_id:
            self.notify("Card ID is required", severity="error")
            id_input.focus()
            return

        if self.db.card_exists(zettel_id):
            self.notify(f"Card {zettel_id} already exists", severity="error")
            id_input.focus()
            return

        # Validate content
        if not note:
            self.notify("Note content is required", severity="error")
            textarea.focus()
            return

        effective, _, status = get_char_status(note)
        if status == 'over':
            self.notify(
                f"Note is {effective} chars (max 825). Shorten it.",
                severity="error"
            )
            textarea.focus()
            return

        # Parse and validate links
        link_to = []
        if links_text:
            for link_id in links_text.split():
                if self.db.card_exists(link_id):
                    link_to.append(link_id)
                else:
                    self.notify(f"Link target {link_id} not found", severity="warning")

        # Create the card
        if self.db.create_card(zettel_id, note, link_to):
            self.dismiss()
            if self.on_created:
                self.on_created(zettel_id)
        else:
            self.notify("Failed to create card", severity="error")

    def action_cancel(self) -> None:
        """Cancel and close the modal."""
        self.dismiss()

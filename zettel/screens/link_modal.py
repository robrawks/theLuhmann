"""Link Modal - Add annotated link from current card to target."""

from typing import Callable, Optional

from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Static, Input, Button
from textual.containers import Vertical, Horizontal
from textual.binding import Binding

from zettel.utils import ZettelDB


class LinkModal(ModalScreen):
    """
    Modal for adding an annotated link from current card to another.

    Both target and reason are REQUIRED. This enforces the principle that
    post-creation links must be documented - the reason lives in the prose.

    Appends to current card: →{target}: {reason}
    Creates database link for navigation.
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("enter", "submit", "Submit", show=False),
    ]

    def __init__(
        self,
        from_id: str,
        db: ZettelDB,
        on_linked: Callable[[str, str], None] = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.from_id = from_id
        self.db = db
        self.on_linked = on_linked

    def compose(self) -> ComposeResult:
        """Compose the link modal."""
        with Vertical(id="link-container"):
            yield Static(f"LINK FROM {self.from_id}", id="link-title")

            with Horizontal(id="link-target-row"):
                yield Static("Target:", id="link-target-label")
                yield Input(
                    placeholder="e.g., 1634/1a",
                    id="link-target-input"
                )

            with Horizontal(id="link-reason-row"):
                yield Static("Why:", id="link-reason-label")
                yield Input(
                    placeholder="Why does this connect? (required)",
                    id="link-reason-input"
                )

            yield Static("", id="link-preview")

            with Horizontal(id="link-buttons"):
                yield Button("Create Link", variant="primary", id="btn-link")
                yield Button("Cancel", id="btn-cancel")

    def on_mount(self) -> None:
        """Focus the target input."""
        target_input = self.query_one("#link-target-input", Input)
        target_input.focus()

    def on_input_changed(self, event: Input.Changed) -> None:
        """Update preview as user types."""
        self._update_preview()

    def _update_preview(self) -> None:
        """Update the preview display."""
        target = self.query_one("#link-target-input", Input).value.strip()
        reason = self.query_one("#link-reason-input", Input).value.strip()

        preview = self.query_one("#link-preview", Static)

        if target and reason:
            preview.update(f"[dim]Will append:[/]\n[gold1]→{target}: {reason}[/]")
        elif target:
            preview.update("[dim]Enter reason to see preview[/]")
        else:
            preview.update("")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "btn-link":
            self._do_link()
        elif event.button.id == "btn-cancel":
            self.action_cancel()

    def action_submit(self) -> None:
        """Handle Enter key to submit form."""
        self._do_link()

    def _do_link(self) -> None:
        """Attempt to create the annotated link."""
        target = self.query_one("#link-target-input", Input).value.strip()
        reason = self.query_one("#link-reason-input", Input).value.strip()

        # Validate target
        if not target:
            self.notify("Target card ID is required", severity="error")
            self.query_one("#link-target-input", Input).focus()
            return

        if target == self.from_id:
            self.notify("Cannot link to self", severity="error")
            self.query_one("#link-target-input", Input).focus()
            return

        if not self.db.card_exists(target):
            self.notify(f"Card {target} not found", severity="error")
            self.query_one("#link-target-input", Input).focus()
            return

        # Validate reason (REQUIRED)
        if not reason:
            self.notify("Reason is required - why does this connect?", severity="error")
            self.query_one("#link-reason-input", Input).focus()
            return

        # Check for existing link (uses proper DB method, no connection leak)
        if self.db.link_exists(self.from_id, target):
            self.notify(f"Link to {target} already exists", severity="error")
            return

        # Create the annotated link
        if self.db.append_link_annotation(self.from_id, target, reason):
            self.dismiss()
            if self.on_linked:
                self.on_linked(self.from_id, target)
        else:
            self.notify("Failed to create link", severity="error")

    def action_cancel(self) -> None:
        """Cancel and close the modal."""
        self.dismiss()

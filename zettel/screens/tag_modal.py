"""Tag Modal - Add/remove insight tags from a card."""

from typing import Callable

from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Static, Input, Button
from textual.containers import Vertical, Horizontal, ScrollableContainer
from textual.binding import Binding
from textual.reactive import reactive

from zettel.utils import ZettelDB


class TagModal(ModalScreen):
    """
    Modal for managing insight tags on a card.

    Features:
    - View current tags with ability to remove
    - Search existing insights by typing
    - Create new insights inline
    - Add insights to the current card
    """

    BINDINGS = [
        Binding("escape", "close", "Close"),
        Binding("down", "next_suggestion", "Next", show=False),
        Binding("up", "prev_suggestion", "Prev", show=False),
        Binding("enter", "select_suggestion", "Select", show=False),
    ]

    # Currently selected suggestion index (-1 = none, last = create new)
    selected_index: reactive[int] = reactive(-1)

    def __init__(
        self,
        zettel_id: str,
        db: ZettelDB,
        on_changed: Callable[[], None] = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.zettel_id = zettel_id
        self.db = db
        self.on_changed = on_changed
        self._current_tags: list[dict] = []
        self._suggestions: list[dict] = []
        self._search_text: str = ""

    def compose(self) -> ComposeResult:
        """Compose the tag modal."""
        with Vertical(id="tag-container"):
            yield Static("TAG CARD", id="tag-title")

            # Current tags section
            yield Static("Current tags:", id="tag-current-label")
            yield Horizontal(id="tag-current-tags")

            yield Static("", id="tag-divider")

            # Search/create input
            yield Static("Add or create:", id="tag-add-label")
            yield Input(placeholder="Type to search or create...", id="tag-input")

            # Suggestions list
            with ScrollableContainer(id="tag-suggestions-container"):
                yield Vertical(id="tag-suggestions")

            # Buttons
            with Horizontal(id="tag-buttons"):
                yield Button("Done", variant="primary", id="btn-done")

    def on_mount(self) -> None:
        """Initialize the modal."""
        self._load_current_tags()
        self._load_suggestions("")
        self.query_one("#tag-input", Input).focus()

    def _load_current_tags(self) -> None:
        """Load and display current tags for this card."""
        self._current_tags = self.db.get_card_insights(self.zettel_id)
        self._render_current_tags()

    def _render_current_tags(self) -> None:
        """Render the current tags display."""
        container = self.query_one("#tag-current-tags", Horizontal)
        container.remove_children()

        if not self._current_tags:
            container.mount(Static("[dim]No tags yet[/]", classes="tag-empty"))
        else:
            for tag in self._current_tags:
                # Create a tag chip with remove button
                chip = Horizontal(
                    Static(f"[purple]{tag['name']}[/]", classes="tag-chip-name"),
                    Button("×", id=f"remove-{tag['id']}", classes="tag-chip-remove"),
                    classes="tag-chip"
                )
                container.mount(chip)

    def _load_suggestions(self, query: str) -> None:
        """Load suggestions based on search query."""
        self._search_text = query.strip()

        if self._search_text:
            # Search for matching insights
            all_insights = self.db.search_insights(self._search_text)
        else:
            # Show all insights
            all_insights = self.db.get_all_insights_simple()

        # Filter out already-applied tags
        current_ids = {t['id'] for t in self._current_tags}
        self._suggestions = [i for i in all_insights if i['id'] not in current_ids]

        # Reset selection
        self.selected_index = 0 if self._suggestions else -1

        self._render_suggestions()

    def _render_suggestions(self) -> None:
        """Render the suggestions list."""
        container = self.query_one("#tag-suggestions", Vertical)

        # Build all content as a single update to avoid duplicate ID issues
        lines = []

        # Existing insights that match
        for i, insight in enumerate(self._suggestions):
            is_selected = (i == self.selected_index)
            prefix = "[reverse]→ " if is_selected else "  "
            suffix = "[/]" if is_selected else ""
            lines.append(f"{prefix}{insight['name']}{suffix}")

        # "Create new" option if there's search text and no exact match
        if self._search_text:
            exact_match = any(
                s['name'].lower() == self._search_text.lower()
                for s in self._suggestions
            )
            if not exact_match:
                create_index = len(self._suggestions)
                is_selected = (self.selected_index == create_index)
                prefix = "[reverse]→ " if is_selected else "  "
                suffix = "[/]" if is_selected else ""
                lines.append(f'{prefix}[green]+ Create "{self._search_text}"[/]{suffix}')

        if not self._suggestions and not self._search_text:
            lines.append("[dim]No insights yet. Type to create one.[/]")

        # Update the container with a single Static widget (no ID to avoid async removal race)
        container.remove_children()
        if lines:
            container.mount(Static("\n".join(lines)))

    def _get_max_index(self) -> int:
        """Get the maximum valid selection index."""
        max_idx = len(self._suggestions) - 1

        # Add 1 for "create new" if applicable
        if self._search_text:
            exact_match = any(
                s['name'].lower() == self._search_text.lower()
                for s in self._suggestions
            )
            if not exact_match:
                max_idx += 1

        return max_idx

    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle search input changes."""
        if event.input.id == "tag-input":
            self._load_suggestions(event.value)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle Enter key in input - select current suggestion."""
        if event.input.id == "tag-input":
            self.action_select_suggestion()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id

        if button_id == "btn-done":
            self.action_close()
        elif button_id and button_id.startswith("remove-"):
            # Remove tag button clicked
            insight_id = button_id[7:]  # Strip "remove-" prefix
            self._remove_tag(insight_id)

    def _remove_tag(self, insight_id: str) -> None:
        """Remove a tag from the card."""
        if self.db.remove_insight_from_card(self.zettel_id, insight_id):
            self._load_current_tags()
            self._load_suggestions(self._search_text)
            self.notify(f"Removed tag", severity="information")

    def _add_tag(self, insight_id: str, insight_name: str) -> None:
        """Add an existing insight as a tag."""
        if self.db.add_insight_to_card(self.zettel_id, insight_id):
            self._load_current_tags()
            self._load_suggestions(self._search_text)
            # Clear input
            self.query_one("#tag-input", Input).value = ""
            self.notify(f"Added: {insight_name}", severity="information")

    def _create_and_add_tag(self, name: str) -> None:
        """Create a new insight and add it to the card."""
        insight_id = self.db.create_insight(name)
        if insight_id:
            self.db.add_insight_to_card(self.zettel_id, insight_id)
            self._load_current_tags()
            # Clear input and reload suggestions
            self.query_one("#tag-input", Input).value = ""
            self._load_suggestions("")
            self.notify(f"Created: {name}", severity="information")
        else:
            self.notify("Failed to create insight", severity="error")

    def action_next_suggestion(self) -> None:
        """Move to next suggestion."""
        max_idx = self._get_max_index()
        if max_idx >= 0:
            self.selected_index = min(self.selected_index + 1, max_idx)
            self._render_suggestions()

    def action_prev_suggestion(self) -> None:
        """Move to previous suggestion."""
        if self.selected_index > 0:
            self.selected_index -= 1
            self._render_suggestions()

    def action_select_suggestion(self) -> None:
        """Select the current suggestion."""
        if self.selected_index < 0:
            # No selection - if there's text, create new
            if self._search_text:
                self._create_and_add_tag(self._search_text)
            return

        if self.selected_index < len(self._suggestions):
            # Selected an existing insight
            insight = self._suggestions[self.selected_index]
            self._add_tag(insight['id'], insight['name'])
        else:
            # Selected "create new"
            if self._search_text:
                self._create_and_add_tag(self._search_text)

    def action_close(self) -> None:
        """Close the modal."""
        if self.on_changed:
            self.on_changed()
        self.dismiss()

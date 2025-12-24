"""Trail Panel - Session history sidebar with navigation."""

from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Static
from textual.containers import Vertical
from textual.reactive import reactive
from textual.message import Message
from textual.binding import Binding

from zettel.utils import SessionTrail


class TrailPanel(Widget):
    """
    Session trail panel showing checkout history.

    Displays a windowed view of the session trail with:
    - Numbered entries (1-8) for quick jumping
    - Current position marker
    - Overflow indicators for long trails
    - Page navigation with [ and ]
    - Focus mode: Tab to focus, arrows to navigate, Enter to select
    """

    can_focus = True

    BINDINGS = [
        Binding("up", "cursor_up", "Up", show=False),
        Binding("down", "cursor_down", "Down", show=False),
        Binding("k", "cursor_up", "Up", show=False),
        Binding("j", "cursor_down", "Down", show=False),
        Binding("enter", "select_entry", "Select", show=False),
        Binding("escape", "unfocus", "Back", show=False),
    ]

    class TrailJump(Message):
        """Message sent when user jumps to a trail entry."""
        def __init__(self, zettel_id: str) -> None:
            self.zettel_id = zettel_id
            super().__init__()

    class TrailSelected(Message):
        """Message sent when user selects a trail entry via Enter."""
        def __init__(self, zettel_id: str) -> None:
            self.zettel_id = zettel_id
            super().__init__()

    # Reactive trail data - when this changes, we re-render
    trail_data: reactive[list[tuple[int, str, bool]]] = reactive([])
    total_count: reactive[int] = reactive(0)
    overflow_before: reactive[int] = reactive(0)
    overflow_after: reactive[int] = reactive(0)
    cursor_index: reactive[int] = reactive(0)  # Cursor for focused navigation

    def __init__(self, trail: SessionTrail, **kwargs):
        super().__init__(**kwargs)
        self.trail = trail

    def compose(self) -> ComposeResult:
        """Compose the trail panel."""
        with Vertical():
            yield Static("TRAIL", id="trail-title")
            yield Static("", id="trail-count")
            yield Static("", id="trail-overflow")
            yield Static("", id="trail-list")
            yield Static("[<] older  [>] newer", id="trail-nav")

    def on_mount(self) -> None:
        """Initialize the panel."""
        self._update_window_size()
        self.refresh_trail()

    def on_resize(self, event) -> None:
        """Handle resize to update window size."""
        self._update_window_size()
        self.refresh_trail()

    def _update_window_size(self) -> None:
        """Calculate window size based on available height."""
        # Get panel height and subtract header/footer elements
        # Title (1) + count (1) + overflow (1) + nav hints (1) + padding (2) = ~6 lines overhead
        available_height = self.size.height - 6
        if available_height > 0:
            self.trail.window_size = max(1, available_height)
        else:
            self.trail.window_size = 8  # Fallback

    def refresh_trail(self) -> None:
        """Refresh the trail display from current state."""
        self.trail_data = self.trail.get_visible_entries()
        self.total_count = self.trail.total
        before, after = self.trail.get_overflow_info()
        self.overflow_before = before
        self.overflow_after = after
        self._update_display()

    def _update_display(self) -> None:
        """Update the display widgets."""
        # Update count
        count_widget = self.query_one("#trail-count", Static)
        if self.total_count > 0:
            count_widget.update(f"({self.total_count} total)")
        else:
            count_widget.update("")

        # Update overflow indicator
        overflow_widget = self.query_one("#trail-overflow", Static)
        if self.overflow_before > 0:
            overflow_widget.update(f"  ↑ {self.overflow_before} more")
        else:
            overflow_widget.update("")

        # Update trail list
        list_widget = self.query_one("#trail-list", Static)
        if not self.trail_data:
            list_widget.update("  (empty)")
        else:
            lines = []
            is_focused = self.has_focus
            for i, (actual_pos, zettel_id, is_current) in enumerate(self.trail_data):
                marker = " [bold gold1]←[/]" if is_current else ""
                # Format position with consistent width
                pos_str = f"{actual_pos:>3}"
                # Highlight cursor when focused
                if is_focused and i == self.cursor_index:
                    lines.append(f"[reverse][cyan]{pos_str}[/] {zettel_id}{marker}[/reverse]")
                else:
                    style = "bold gold1" if is_current else "white"
                    lines.append(f"[cyan]{pos_str}[/] [{style}]{zettel_id}[/]{marker}")
            list_widget.update("\n".join(lines))

        # Update nav hints
        nav_widget = self.query_one("#trail-nav", Static)
        if self.overflow_before > 0 or self.overflow_after > 0:
            nav_widget.update("[dim][<] older  [>] newer[/]")
        else:
            nav_widget.update("")

    def checkout(self, zettel_id: str) -> None:
        """Add a card to the trail and refresh display."""
        self.trail.checkout(zettel_id)
        self.refresh_trail()

    def go_back(self) -> str | None:
        """Go back in trail, refresh, and return the new current ID."""
        result = self.trail.back()
        if result:
            self.refresh_trail()
        return result

    def go_forward(self) -> str | None:
        """Go forward in trail, refresh, and return the new current ID."""
        result = self.trail.forward()
        if result:
            self.refresh_trail()
        return result

    # Focus mode actions
    def action_cursor_up(self) -> None:
        """Move cursor up in trail list."""
        if self.cursor_index > 0:
            self.cursor_index -= 1
            self._update_display()

    def action_cursor_down(self) -> None:
        """Move cursor down in trail list."""
        if self.cursor_index < len(self.trail_data) - 1:
            self.cursor_index += 1
            self._update_display()

    def action_select_entry(self) -> None:
        """Select the current cursor entry."""
        if self.trail_data and 0 <= self.cursor_index < len(self.trail_data):
            actual_pos, zettel_id, _ = self.trail_data[self.cursor_index]
            # Update trail position (actual_pos is 1-based, convert to 0-based index)
            self.trail.position = actual_pos - 1
            self.post_message(self.TrailSelected(zettel_id))

    def action_unfocus(self) -> None:
        """Return focus to main screen."""
        self.blur()
        self._update_display()  # Remove cursor highlight

    def on_focus(self) -> None:
        """When focused, set cursor to current trail position."""
        # Find the current position in visible entries
        for i, (_, _, is_current) in enumerate(self.trail_data):
            if is_current:
                self.cursor_index = i
                break
        self._update_display()

    def on_blur(self) -> None:
        """When blurred, update display to remove cursor."""
        self._update_display()

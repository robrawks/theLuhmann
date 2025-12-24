# theLuhmann

A terminal-based Zettelkasten application inspired by Niklas Luhmann's slip-box method.

Built with [Textual](https://textual.textualize.io/) for a rich TUI experience.

## Philosophy

This app embodies Luhmann's principles:

- **Atomic notes**: Each card captures one idea (825 char soft limit)
- **Unique IDs**: Branching notation like `1620/1a` for related ideas
- **Bidirectional links**: Navigate both outbound and inbound connections
- **Append-only**: Cards are immutable after creation; new connections require documented reasons
- **Trail navigation**: Track your thinking path through the slip-box

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/theLuhmann.git
cd theLuhmann

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Initialize database
sqlite3 data/zettel.db < schema.sql
```

## Usage

```bash
# Run the app
./bin/zettel

# Or with a specific card
./bin/zettel 1620
```

### Configuration

Set `ZETTEL_DB_PATH` environment variable to use a custom database location:

```bash
export ZETTEL_DB_PATH=/path/to/your/zettel.db
./bin/zettel
```

## Keybindings

### Browse Mode
| Key | Action |
|-----|--------|
| `↑/↓` or `j/k` | Navigate cards |
| `Enter` | Open selected card |
| `/` | Filter by ID |
| `Escape` | Clear filter |
| `q` | Quit |

### Card Mode
| Key | Action |
|-----|--------|
| `1-6` | Jump to numbered link |
| `Backspace` | Go back in trail |
| `\` | Go forward in trail |
| `Tab` | Focus trail panel |
| `[` / `]` | Page trail older/newer |
| `n` | New card |
| `l` | Add link (with annotation) |
| `p` | Show 2-hop paths |
| `/` | Search |
| `s` | Show stats |
| `Escape` | Return to browse |
| `q` | Quit |

### Trail Panel (when focused)
| Key | Action |
|-----|--------|
| `↑/↓` or `j/k` | Move cursor |
| `Enter` | Jump to selected |
| `Escape` | Unfocus |

## The Linking Philosophy

When creating a new card, you write your note and reference other cards naturally:

> "This extends the concept in 1634/1a about organizational dynamics..."

Then list the referenced cards in the links field.

When adding a link to an *existing* card, you must provide a reason:

```
Target: 1634/1a
Why: extends to organizational contexts
```

This appends to your card: `→1634/1a: extends to organizational contexts`

The reason becomes part of the permanent record - because the connection *is* the thinking.

## Database Schema

Minimal schema for maximum flexibility:

```sql
-- Notes
CREATE TABLE zettelkasten (
    zettel_id TEXT PRIMARY KEY,
    note TEXT NOT NULL,
    created_at TIMESTAMP,
    modified_at TIMESTAMP
);

-- Directional links
CREATE TABLE zettel_links (
    from_zettel_id TEXT,
    to_zettel_id TEXT,
    PRIMARY KEY (from_zettel_id, to_zettel_id)
);
```

## License

MIT

## Acknowledgments

- Niklas Luhmann for the Zettelkasten method
- [Textual](https://textual.textualize.io/) for the TUI framework
- The Zettelkasten community for ongoing inspiration

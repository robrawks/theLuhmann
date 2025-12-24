# theLuhmann

> In the age of endless insight editing, bubble graph thirst traps, and sterile PARA second brains. **The Luhmann is wisdom that grows.**

A terminal-based Zettelkasten built on immutability. No endless rewrites. No graph theater. Just atomic ideas that accumulate into something real.

Built with [Textual](https://textual.textualize.io/) for an 80s terminal aesthetic.

## The Manifesto

In an era in which nothing is permanent and everything can be doubted, we fool ourselves into believing we are doing work. That we're thinking critically. But all we are doing is pontificating into digital post-its.

We develop intricate systems to link data. We see backlinks and forward links and bubble graphs. But at what point does insight come out? Where is the writing? Where is the knowledge that we ourselves generate?

We feed our PKM systems like farmers feed their pigs. We shovel insights and thoughts and expect meat, but what do we get? Little bubble graphs and perfect metadata in our markdown files.

Those pieces of our knowledge, those insights, are just text files. Text files can be changed and altered. You wake up one morning with a flash of insight given to you by a muse. The next day you delete everything because it doesn't fit with the aesthetic of the rest of your thoughts. You don't see your knowledge grow over time. You don't see the blind alleyways or the mistakes. All that you see is perfect wisdom that reflects who you are right now but not the wisdom that reflected who you were five minutes ago or ten years ago. It's a neutered system, corporate and sterile, producing nothing but a reflection of who you are at this moment. You can't look in the past and see how you used to think about a topic and you can't link that old self to the new self.

Luhmann doesn't allow you to change mistakes. You believed in topic A and you find out five years later that you were horrifically wrong. There is no deleting that mistake. You link to it with a new card and explain why it was a fallacy. You get to see your evolution of thought, your wisdom grow.

The system possesses no graphical interface, no fancy bubble charts that you can post on social media for likes. All it possesses is links manually typed. You make a typo and commit-save. You can't fix it. Your mistakes are who you are; it's what makes you who you are.

There are no notes other than the Zettel. No bibliography notes. No fleeting notes. No literature notes. There is just insight, atomic-sized and limited to 825 characters.

The Luhmann is a thinking partner for your thinking. Not a system someone else built to sell you courses.

**Wisdom is not perfection, but growth.**

---

## Principles

- **Atomic notes**: Each card captures one idea (825 char limit)
- **Unique IDs**: Branching notation like `1620/1a` for related ideas
- **Bidirectional links**: Navigate both outbound and inbound connections
- **Immutable**: Cards cannot be edited after creation; link with annotations instead
- **Trail navigation**: Track your thinking path through the slip-box

## Installation

```bash
# Clone the repository
git clone https://github.com/robrawks/theLuhmann.git
cd theLuhmann

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Initialize database (empty)
sqlite3 data/zettel.db < schema.sql

# OR initialize with sample data to explore
sqlite3 data/zettel.db < schema.sql
sqlite3 data/zettel.db < sample_data.sql
```

## Reset Database

To clear all data and start fresh:

```bash
./scripts/reset_db.sh              # Empty database
./scripts/reset_db.sh --with-samples  # With sample cards
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
| `t` | Tag card (add/remove insights) |
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

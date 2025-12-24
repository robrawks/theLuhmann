"""
theLuhmann Configuration

Database path resolution (in order):
1. ZETTEL_DB_PATH environment variable
2. ./data/zettel.db (relative to project root)
"""

import os
from pathlib import Path

# Project root is where this config.py lives
PROJECT_ROOT = Path(__file__).parent.resolve()

# Database path - configurable via environment variable
DB_PATH = Path(os.environ.get(
    "ZETTEL_DB_PATH",
    PROJECT_ROOT / "data" / "zettel.db"
))

# Styles path
STYLES_PATH = PROJECT_ROOT / "styles" / "zettel.tcss"

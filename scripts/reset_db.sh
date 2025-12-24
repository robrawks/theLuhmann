#!/bin/bash
# Reset the database - removes all data and recreates schema
# Usage: ./scripts/reset_db.sh [--with-samples]

cd "$(dirname "$0")/.."

echo "This will DELETE all data in data/zettel.db"
read -p "Are you sure? (y/N) " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    rm -f data/zettel.db
    sqlite3 data/zettel.db < schema.sql
    echo "✓ Database reset with empty schema"

    if [[ "$1" == "--with-samples" ]]; then
        sqlite3 data/zettel.db < sample_data.sql
        echo "✓ Sample data loaded"
    fi
else
    echo "Cancelled"
fi

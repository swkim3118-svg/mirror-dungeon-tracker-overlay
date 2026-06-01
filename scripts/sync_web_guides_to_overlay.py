import argparse
import os
import sqlite3


TABLES = {
    "decks": """
        CREATE TABLE IF NOT EXISTS decks (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            keywords TEXT,
            description TEXT
        )
    """,
    "deck_identities": """
        CREATE TABLE IF NOT EXISTS deck_identities (
            id INTEGER PRIMARY KEY,
            deck_id INTEGER NOT NULL,
            identity_name TEXT NOT NULL,
            character TEXT,
            priority INTEGER DEFAULT 1,
            role TEXT,
            notes TEXT
        )
    """,
    "deck_floor_packs": """
        CREATE TABLE IF NOT EXISTS deck_floor_packs (
            id INTEGER PRIMARY KEY,
            deck_id INTEGER NOT NULL,
            floor_number INTEGER NOT NULL,
            pack_name TEXT NOT NULL,
            key_gifts TEXT,
            priority INTEGER DEFAULT 1,
            notes TEXT
        )
    """,
}


def sync(source, destination):
    destination = os.path.abspath(destination)
    os.makedirs(os.path.dirname(destination), exist_ok=True)
    conn = sqlite3.connect(destination)
    try:
        conn.execute("ATTACH DATABASE ? AS src", (os.path.abspath(source),))
        conn.execute("DROP TABLE IF EXISTS deck_floor_packs")
        conn.execute("DROP TABLE IF EXISTS deck_identities")
        conn.execute("DROP TABLE IF EXISTS decks")
        for ddl in TABLES.values():
            conn.execute(ddl)

        conn.execute("""
            INSERT INTO decks (id, name, keywords, description)
            SELECT id, name, keywords, description FROM src.decks
        """)
        conn.execute("""
            INSERT INTO deck_identities
                (id, deck_id, identity_name, character, priority, role, notes)
            SELECT id, deck_id, identity_name, character, priority, role, notes
            FROM src.deck_identities
        """)
        conn.execute("""
            INSERT INTO deck_floor_packs
                (id, deck_id, floor_number, pack_name, key_gifts, priority, notes)
            SELECT id, deck_id, floor_number, pack_name, key_gifts, priority, notes
            FROM src.deck_floor_packs
        """)
        conn.commit()

        for table in TABLES:
            count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            print(f"{table}: {count}")
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument(
        "--destination",
        default=os.path.join(os.path.dirname(__file__), "..", "data", "mirror_dungeon.db"),
    )
    args = parser.parse_args()
    sync(args.source, args.destination)


if __name__ == "__main__":
    main()

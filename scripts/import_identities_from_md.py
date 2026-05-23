import json
import os
import re
import sqlite3


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(ROOT, "data", "mirror_dungeon.db")
MD_PATH = os.path.join(ROOT, "outputs", "limbus_identity.md")


def ensure_table(conn):
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS identities (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            name_en TEXT,
            character TEXT,
            character_en TEXT,
            season TEXT,
            grade INTEGER,
            affiliation TEXT,
            season_type TEXT,
            keywords TEXT,
            resources TEXT,
            types TEXT,
            min_speed INTEGER,
            max_speed INTEGER,
            min_weight INTEGER,
            max_weight INTEGER,
            before_image TEXT,
            after_image TEXT,
            after_profile_image TEXT,
            release_date TEXT,
            hp INTEGER,
            defense TEXT,
            defense_type TEXT,
            skill1 TEXT,
            skill2 TEXT,
            skill3 TEXT,
            passive TEXT,
            support_passive TEXT
        )
        """
    )


def split_md_row(line):
    return [part.strip() for part in line.strip().strip("|").split("|")]


def parse_grade(text):
    match = re.search(r"\d+", text or "")
    if match:
        return int(match.group(0))
    stars = text.count("\u2605")
    if stars:
        return stars
    return 1


def parse_speed(text):
    match = re.search(r"(\d+)\s*-\s*(\d+)", text or "")
    if not match:
        return None, None
    return int(match.group(1)), int(match.group(2))


def parse_int(text):
    match = re.search(r"\d+", text or "")
    return int(match.group(0)) if match else None


def parse_identities(path):
    identities = []
    character = None
    with open(path, "r", encoding="utf-8-sig") as f:
        for raw in f:
            line = raw.strip()
            heading = re.match(r"^##\s+🔹\s+(.+?)\s+\(\d+개 인격\)", line)
            if heading:
                character = heading.group(1).strip()
                continue
            if not line.startswith("|") or line.startswith("|----") or "| ID |" in line:
                continue

            cols = split_md_row(line)
            if len(cols) < 14 or not cols[0].isdigit():
                continue

            min_speed, max_speed = parse_speed(cols[6])
            identity = {
                "id": int(cols[0]),
                "name": cols[1],
                "name_en": None,
                "character": character,
                "character_en": None,
                "season": None,
                "grade": parse_grade(cols[2]),
                "affiliation": cols[3],
                "season_type": None,
                "keywords": json.dumps([], ensure_ascii=False),
                "resources": json.dumps([], ensure_ascii=False),
                "types": json.dumps([cols[8]] if cols[8] else [], ensure_ascii=False),
                "min_speed": min_speed,
                "max_speed": max_speed,
                "min_weight": None,
                "max_weight": None,
                "before_image": None,
                "after_image": None,
                "after_profile_image": None,
                "release_date": cols[4],
                "hp": parse_int(cols[5]),
                "defense": cols[7],
                "defense_type": cols[8],
                "skill1": cols[9],
                "skill2": cols[10],
                "skill3": cols[11],
                "passive": cols[12],
                "support_passive": cols[13],
            }
            identities.append(identity)
    return identities


def import_identities():
    if not os.path.exists(MD_PATH):
        raise FileNotFoundError(MD_PATH)

    identities = parse_identities(MD_PATH)
    conn = sqlite3.connect(DB_PATH)
    try:
        ensure_table(conn)
        conn.executemany(
            """
            INSERT INTO identities (
                id, name, name_en, character, character_en, season, grade,
                affiliation, season_type, keywords, resources, types,
                min_speed, max_speed, min_weight, max_weight,
                before_image, after_image, after_profile_image,
                release_date, hp, defense, defense_type,
                skill1, skill2, skill3, passive, support_passive
            )
            VALUES (
                :id, :name, :name_en, :character, :character_en, :season, :grade,
                :affiliation, :season_type, :keywords, :resources, :types,
                :min_speed, :max_speed, :min_weight, :max_weight,
                :before_image, :after_image, :after_profile_image,
                :release_date, :hp, :defense, :defense_type,
                :skill1, :skill2, :skill3, :passive, :support_passive
            )
            ON CONFLICT(id) DO UPDATE SET
                name = excluded.name,
                character = excluded.character,
                grade = excluded.grade,
                affiliation = excluded.affiliation,
                types = excluded.types,
                min_speed = excluded.min_speed,
                max_speed = excluded.max_speed,
                release_date = excluded.release_date,
                hp = excluded.hp,
                defense = excluded.defense,
                defense_type = excluded.defense_type,
                skill1 = excluded.skill1,
                skill2 = excluded.skill2,
                skill3 = excluded.skill3,
                passive = excluded.passive,
                support_passive = excluded.support_passive
            """,
            identities,
        )
        conn.commit()
    finally:
        conn.close()
    print(f"Imported {len(identities)} identities from {MD_PATH}")


if __name__ == "__main__":
    import_identities()

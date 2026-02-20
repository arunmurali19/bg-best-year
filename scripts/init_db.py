"""Initialize the tournament database from pipeline output."""

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from webapp.app import create_app

DATA_DIR = ROOT / "data"


def main():
    app = create_app()

    with app.app_context():
        from webapp.database import get_db, init_db

        init_db()
        db = get_db()

        # Disable FK checks during bulk insert, re-enable after
        db.execute("PRAGMA foreign_keys = OFF")

        # Load tournament data
        with open(DATA_DIR / "tournament_seed.json") as f:
            tournament = json.load(f)

        # Insert years
        for y in tournament["years"]:
            db.execute(
                "INSERT OR REPLACE INTO years (year, total_games, top500_games, score, seed) "
                "VALUES (?, ?, ?, ?, ?)",
                (y["year"], y["total_games"], y["top500_games"], y["score"], y["seed"]),
            )

        # Insert games (only for tournament years)
        tournament_years = {y["year"] for y in tournament["years"]}
        with open(DATA_DIR / "bgg_games.csv", "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rank_str = row.get("rank", "").strip()
                if not rank_str or rank_str.lower() in ("", "none", "null"):
                    continue
                try:
                    rank = int(float(rank_str))
                except (ValueError, TypeError):
                    continue
                if rank < 1 or rank > 1000:
                    continue
                year = int(row["year_published"]) if row.get("year_published") else None
                if year not in tournament_years:
                    continue
                db.execute(
                    "INSERT OR REPLACE INTO games (game_id, name, year_published, rank, thumbnail_url) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (int(row["game_id"]), row["name"], year, rank, row.get("thumbnail_url", "")),
                )

        # Insert matches
        for m in tournament["matches"]:
            db.execute(
                "INSERT OR REPLACE INTO matches "
                "(match_id, round, position, year_a, year_b, winner, next_match_id, is_active) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (m["match_id"], m["round"], m["position"],
                 m.get("year_a"), m.get("year_b"), m.get("winner"),
                 m.get("next_match_id"), 0),
            )

        # Set tournament state
        db.execute(
            "INSERT OR REPLACE INTO tournament_state (key, value) VALUES ('current_round', '1')"
        )
        db.execute(
            "INSERT OR REPLACE INTO tournament_state (key, value) VALUES ('tournament_name', 'Board Game Best Year')"
        )

        # Activate round 1
        db.execute("UPDATE matches SET is_active = 1 WHERE round = 1")

        db.execute("PRAGMA foreign_keys = ON")
        db.commit()

        # Summary
        game_count = db.execute("SELECT COUNT(*) FROM games").fetchone()[0]
        year_count = db.execute("SELECT COUNT(*) FROM years").fetchone()[0]
        match_count = db.execute("SELECT COUNT(*) FROM matches").fetchone()[0]
        print(f"Database initialized:")
        print(f"  {year_count} years, {game_count} games, {match_count} matches")
        print(f"  Round 1 activated with 16 matchups")


if __name__ == "__main__":
    main()

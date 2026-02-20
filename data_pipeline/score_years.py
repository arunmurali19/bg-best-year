"""Filter top 2000 games from BGG CSV and score each year."""

import csv
import json
import os
from collections import defaultdict
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
CSV_PATH = DATA_DIR / "bgg_games.csv"


def score_for_rank(rank: int) -> float:
    """Tiered scoring: higher-ranked games contribute more."""
    if rank <= 20:
        return 10
    elif rank <= 100:
        return 6
    elif rank <= 250:
        return 5
    elif rank <= 500:
        return 4
    elif rank <= 750:
        return 3
    elif rank <= 1000:
        return 2
    elif rank <= 2000:
        return 1
    return 0


def load_top_games(max_rank: int = 2000) -> list[dict]:
    """Load games ranked 1 through max_rank from the CSV."""
    games = []
    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rank_str = row.get("rank", "").strip()
            if not rank_str or rank_str.lower() in ("", "none", "null"):
                continue
            try:
                rank = int(float(rank_str))
            except (ValueError, TypeError):
                continue
            if 1 <= rank <= max_rank:
                games.append({
                    "game_id": int(row["game_id"]),
                    "name": row["name"],
                    "rank": rank,
                    "year_published": int(row["year_published"]) if row.get("year_published") else None,
                    "thumbnail_url": row.get("thumbnail_url", ""),
                })
    games.sort(key=lambda g: g["rank"])
    return games


def score_years(games: list[dict]) -> list[dict]:
    """Group games by year and compute scores."""
    by_year = defaultdict(list)
    for g in games:
        if g["year_published"] and g["year_published"] > 0:
            by_year[g["year_published"]].append(g)

    year_scores = []
    for year, year_games in sorted(by_year.items()):
        total = len(year_games)
        top500 = sum(1 for g in year_games if g["rank"] <= 500)
        score = sum(score_for_rank(g["rank"]) for g in year_games)
        year_scores.append({
            "year": year,
            "total_games": total,
            "top500_games": top500,
            "score": score,
            "games": sorted(year_games, key=lambda g: g["rank"]),
        })

    year_scores.sort(key=lambda y: y["score"], reverse=True)
    return year_scores


def write_internal_analysis(year_scores: list[dict]) -> None:
    """Write CSV with per-year breakdown by tier."""
    out = DATA_DIR / "internal_analysis.csv"
    with open(out, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "year", "rank_1_20", "rank_21_100", "rank_101_250", "rank_251_500",
            "rank_501_750", "rank_751_1000", "rank_1001_2000",
            "total_top1000", "total_top2000", "total_top500", "score"
        ])
        for ys in sorted(year_scores, key=lambda y: y["year"]):
            games = ys["games"]
            t0 = sum(1 for g in games if g["rank"] <= 20)
            t1 = sum(1 for g in games if 21 <= g["rank"] <= 100)
            t2 = sum(1 for g in games if 101 <= g["rank"] <= 250)
            t3 = sum(1 for g in games if 251 <= g["rank"] <= 500)
            t4 = sum(1 for g in games if 501 <= g["rank"] <= 750)
            t5 = sum(1 for g in games if 751 <= g["rank"] <= 1000)
            t6 = sum(1 for g in games if 1001 <= g["rank"] <= 2000)
            top1000 = sum(1 for g in games if g["rank"] <= 1000)
            writer.writerow([
                ys["year"], t0, t1, t2, t3, t4, t5, t6,
                top1000, ys["total_games"], ys["top500_games"], ys["score"]
            ])
    print(f"  Written: {out}")


def write_year_scores(year_scores: list[dict]) -> None:
    """Write year scores JSON (without full game lists)."""
    out = DATA_DIR / "year_scores.json"
    output = []
    for ys in year_scores:
        output.append({
            "year": ys["year"],
            "total_games": ys["total_games"],
            "top500_games": ys["top500_games"],
            "score": ys["score"],
        })
    with open(out, "w") as f:
        json.dump(output, f, indent=2)
    print(f"  Written: {out}")


def run():
    print("Step 1: Loading top 2000 games from CSV...")
    games = load_top_games(2000)
    print(f"  Found {len(games)} games")

    print("Step 2: Scoring years...")
    year_scores = score_years(games)
    print(f"  {len(year_scores)} years with at least one top-2000 game")
    print(f"  Top 5 years by score: {[(y['year'], y['score']) for y in year_scores[:5]]}")

    write_year_scores(year_scores)
    write_internal_analysis(year_scores)

    return games, year_scores


if __name__ == "__main__":
    run()

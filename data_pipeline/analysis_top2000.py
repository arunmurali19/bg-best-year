"""Compare top-1000 vs top-2000 scoring to see if expanding is worthwhile."""

import csv
from collections import defaultdict
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
CSV_PATH = DATA_DIR / "bgg_games.csv"


def score_top1000(rank: int) -> float:
    """Current scoring (top 1000)."""
    if rank <= 20:
        return 8
    elif rank <= 100:
        return 5
    elif rank <= 250:
        return 4
    elif rank <= 500:
        return 3
    elif rank <= 750:
        return 2
    elif rank <= 1000:
        return 1
    return 0


def score_top2000(rank: int) -> float:
    """Proposed scoring (top 2000)."""
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


def load_games(max_rank: int) -> list[dict]:
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
                year = int(row["year_published"]) if row.get("year_published") else None
                if year and year > 0:
                    games.append({"rank": rank, "year": year, "name": row["name"]})
    return games


def main():
    games = load_games(2000)
    print(f"Loaded {len(games)} games (rank 1-2000)")

    by_year = defaultdict(list)
    for g in games:
        by_year[g["year"]].append(g)

    rows = []
    for year in sorted(by_year.keys()):
        yg = by_year[year]
        t_1_20 = sum(1 for g in yg if g["rank"] <= 20)
        t_21_100 = sum(1 for g in yg if 21 <= g["rank"] <= 100)
        t_101_250 = sum(1 for g in yg if 101 <= g["rank"] <= 250)
        t_251_500 = sum(1 for g in yg if 251 <= g["rank"] <= 500)
        t_501_750 = sum(1 for g in yg if 501 <= g["rank"] <= 750)
        t_751_1000 = sum(1 for g in yg if 751 <= g["rank"] <= 1000)
        t_1001_2000 = sum(1 for g in yg if 1001 <= g["rank"] <= 2000)
        total_top1000 = sum(1 for g in yg if g["rank"] <= 1000)
        total_top2000 = len(yg)

        score_1k = sum(score_top1000(g["rank"]) for g in yg)
        score_2k = sum(score_top2000(g["rank"]) for g in yg)

        rows.append({
            "year": year,
            "rank_1_20": t_1_20,
            "rank_21_100": t_21_100,
            "rank_101_250": t_101_250,
            "rank_251_500": t_251_500,
            "rank_501_750": t_501_750,
            "rank_751_1000": t_751_1000,
            "rank_1001_2000": t_1001_2000,
            "total_top1000": total_top1000,
            "total_top2000": total_top2000,
            "score_top1000": score_1k,
            "score_top2000": score_2k,
        })

    # Sort by top-2000 score descending
    rows.sort(key=lambda r: r["score_top2000"], reverse=True)

    # Add rank columns
    rows_by_1k = sorted(rows, key=lambda r: r["score_top1000"], reverse=True)
    rank_1k = {r["year"]: i + 1 for i, r in enumerate(rows_by_1k)}
    for r in rows:
        r["rank_top1000"] = rank_1k[r["year"]]

    rows_by_2k = sorted(rows, key=lambda r: r["score_top2000"], reverse=True)
    rank_2k = {r["year"]: i + 1 for i, r in enumerate(rows_by_2k)}
    for r in rows:
        r["rank_top2000"] = rank_2k[r["year"]]
        r["rank_change"] = r["rank_top1000"] - r["rank_top2000"]  # positive = moved up

    # Write CSV
    out = DATA_DIR / "internal_analysis_top2000.csv"
    fieldnames = [
        "year", "rank_top1000", "rank_top2000", "rank_change",
        "rank_1_20", "rank_21_100", "rank_101_250", "rank_251_500",
        "rank_501_750", "rank_751_1000", "rank_1001_2000",
        "total_top1000", "total_top2000",
        "score_top1000", "score_top2000",
    ]
    with open(out, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nWritten: {out}")
    print(f"\n{'='*80}")
    print(f"{'Year':>6} {'Rk(1K)':>7} {'Rk(2K)':>7} {'Change':>7} {'Score1K':>8} {'Score2K':>8} {'Top1K':>6} {'1K-2K':>6}")
    print(f"{'='*80}")
    for r in rows[:40]:
        change_str = f"+{r['rank_change']}" if r['rank_change'] > 0 else str(r['rank_change'])
        if r['rank_change'] == 0:
            change_str = "-"
        print(f"{r['year']:>6} {r['rank_top1000']:>7} {r['rank_top2000']:>7} {change_str:>7} {r['score_top1000']:>8.0f} {r['score_top2000']:>8.0f} {r['total_top1000']:>6} {r['rank_1001_2000']:>6}")

    # Highlight biggest movers
    movers = sorted(rows, key=lambda r: abs(r["rank_change"]), reverse=True)
    print(f"\nBiggest rank changes (top 2000 vs top 1000):")
    for r in movers[:10]:
        direction = "UP" if r["rank_change"] > 0 else "DOWN"
        print(f"  {r['year']}: {direction} {abs(r['rank_change'])} places "
              f"(#{r['rank_top1000']} -> #{r['rank_top2000']}, "
              f"+{r['rank_1001_2000']} games from 1001-2000 range)")

    # Check if top 32 would change
    top32_1k = set(r["year"] for r in sorted(rows, key=lambda r: r["score_top1000"], reverse=True)[:32])
    top32_2k = set(r["year"] for r in sorted(rows, key=lambda r: r["score_top2000"], reverse=True)[:32])
    new_in = top32_2k - top32_1k
    dropped = top32_1k - top32_2k
    print(f"\nTop 32 changes:")
    print(f"  Years that would enter top 32: {sorted(new_in) if new_in else 'None'}")
    print(f"  Years that would drop out:     {sorted(dropped) if dropped else 'None'}")


if __name__ == "__main__":
    main()

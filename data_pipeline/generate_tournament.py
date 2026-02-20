"""Master pipeline: score years, seed bracket, generate tournament."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from data_pipeline.score_years import run as run_scoring
from data_pipeline.seed_bracket import run as run_seeding


def main():
    print("=" * 60)
    print("Board Game Best Year - Tournament Generator")
    print("=" * 60)

    games, year_scores = run_scoring()
    tournament = run_seeding(year_scores)

    print("\n" + "=" * 60)
    print("Tournament bracket generated successfully!")
    print(f"  Top seed: {tournament['years'][0]['year']} (score: {tournament['years'][0]['score']})")
    print(f"  Bottom seed: {tournament['years'][-1]['year']} (score: {tournament['years'][-1]['score']})")
    print(f"  Round 1 matchups: {len([m for m in tournament['matches'] if m['round'] == 1])}")
    print("=" * 60)


if __name__ == "__main__":
    main()

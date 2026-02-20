"""Tennis-style seeding and bracket generation for the tournament."""

import json
import math
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"

# Tournament configuration
TOTAL_YEARS = 32
BRACKET_SIZE = 32  # Must be power of 2


def tennis_seed_positions(n: int) -> list[int]:
    """Generate tennis-style seed positions for an n-team bracket.

    Returns a flat list where adjacent pairs form round-1 matchups.
    E.g. for n=4: [1, 4, 2, 3] means matchups (1v4) and (2v3).
    For n=8: [1, 8, 4, 5, 2, 7, 3, 6] means (1v8), (4v5), (2v7), (3v6).

    This ensures:
      - #1 and #2 can only meet in the final
      - #1-#4 can only meet in the semis
      - #1-#8 can only meet in the quarters
    """
    bracket = [1, 2]
    while len(bracket) < n:
        new_bracket = []
        next_sum = len(bracket) * 2 + 1
        for seed in bracket:
            new_bracket.append(seed)
            new_bracket.append(next_sum - seed)
        bracket = new_bracket
    return bracket


def generate_bracket(year_scores: list[dict], total_years: int = TOTAL_YEARS,
                     bracket_size: int = BRACKET_SIZE) -> dict:
    """Generate the full tournament bracket.

    Args:
        year_scores: List of year dicts sorted by score descending.
        total_years: Number of years to include.
        bracket_size: Bracket size (power of 2).

    Returns:
        Tournament dict with years, matches, and metadata.
    """
    if total_years > len(year_scores):
        raise ValueError(f"Not enough years: need {total_years}, have {len(year_scores)}")

    selected = year_scores[:total_years]
    for i, ys in enumerate(selected):
        ys["seed"] = i + 1

    num_rounds = int(math.log2(bracket_size))
    play_in_count = max(0, total_years - bracket_size)

    # For now we handle the simple case: total_years == bracket_size
    # Play-in support can be added later for total_years > bracket_size
    if play_in_count > 0:
        raise NotImplementedError(
            f"Play-in rounds needed for {total_years} years in a {bracket_size} bracket. "
            "This is planned for future expansion."
        )

    positions = tennis_seed_positions(bracket_size)

    # Build all matches
    matches = []
    match_id = 0

    # Round 1
    r1_count = bracket_size // 2
    for i in range(0, len(positions), 2):
        seed_a = positions[i]
        seed_b = positions[i + 1]
        year_a = selected[seed_a - 1]
        year_b = selected[seed_b - 1]
        match_id += 1
        matches.append({
            "match_id": match_id,
            "round": 1,
            "position": match_id,
            "year_a": year_a["year"],
            "year_b": year_b["year"],
            "winner": None,
            "next_match_id": r1_count + (match_id + 1) // 2,
        })

    # Rounds 2 through final
    offset = r1_count
    for round_num in range(2, num_rounds + 1):
        matches_in_round = bracket_size // (2 ** round_num)
        next_round_offset = offset + matches_in_round
        for pos in range(1, matches_in_round + 1):
            match_id += 1
            next_mid = None
            if round_num < num_rounds:
                next_mid = next_round_offset + (pos + 1) // 2
            matches.append({
                "match_id": match_id,
                "round": round_num,
                "position": pos,
                "year_a": None,
                "year_b": None,
                "winner": None,
                "next_match_id": next_mid,
            })
        offset = next_round_offset

    round_names = []
    for r in range(1, num_rounds + 1):
        remaining = bracket_size // (2 ** (r - 1))
        if remaining == 2:
            round_names.append("Final")
        elif remaining == 4:
            round_names.append("Semifinals")
        elif remaining == 8:
            round_names.append("Quarterfinals")
        else:
            round_names.append(f"Round of {remaining}")

    return {
        "bracket_size": bracket_size,
        "total_years": total_years,
        "num_rounds": num_rounds,
        "round_names": round_names,
        "years": [{
            "year": y["year"],
            "seed": y["seed"],
            "score": y["score"],
            "total_games": y["total_games"],
            "top500_games": y["top500_games"],
        } for y in selected],
        "matches": matches,
    }


def write_tournament(tournament: dict) -> None:
    out = DATA_DIR / "tournament_seed.json"
    with open(out, "w") as f:
        json.dump(tournament, f, indent=2)
    print(f"  Written: {out}")


def run(year_scores: list[dict]):
    print(f"Step 3: Selecting top {TOTAL_YEARS} years and seeding bracket...")
    tournament = generate_bracket(year_scores, TOTAL_YEARS, BRACKET_SIZE)
    print(f"  {len(tournament['matches'])} total matches across {tournament['num_rounds']} rounds")
    print(f"  Rounds: {tournament['round_names']}")
    write_tournament(tournament)
    return tournament


if __name__ == "__main__":
    import json
    scores_path = DATA_DIR / "year_scores.json"
    with open(scores_path) as f:
        year_scores = json.load(f)
    run(year_scores)

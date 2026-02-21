"""Tournament logic: bracket queries, round advancement."""

from webapp.database import get_db


def get_current_round():
    db = get_db()
    row = db.execute(
        "SELECT value FROM tournament_state WHERE key = 'current_round'"
    ).fetchone()
    return int(row["value"]) if row else 1


def get_round_name(round_num):
    db = get_db()
    total_matches_r1 = db.execute(
        "SELECT COUNT(*) as c FROM matches WHERE round = 1"
    ).fetchone()["c"]
    bracket_size = total_matches_r1 * 2
    remaining = bracket_size // (2 ** (round_num - 1))
    if remaining == 2:
        return "Final"
    elif remaining == 4:
        return "Semifinals"
    elif remaining == 8:
        return "Quarterfinals"
    else:
        return f"Round of {remaining}"


def get_active_matchups():
    db = get_db()
    matches = db.execute("""
        SELECT m.*, ya.year as ya_year, yb.year as yb_year
        FROM matches m
        LEFT JOIN years ya ON m.year_a = ya.year
        LEFT JOIN years yb ON m.year_b = yb.year
        WHERE m.is_active = 1 AND m.winner IS NULL
        ORDER BY m.position
    """).fetchall()
    return [dict(m) for m in matches]


def get_match(match_id):
    db = get_db()
    match = db.execute("""
        SELECT m.*
        FROM matches m
        WHERE m.match_id = ?
    """, (match_id,)).fetchone()
    return dict(match) if match else None


def get_games_for_year(year):
    db = get_db()
    games = db.execute(
        "SELECT * FROM games WHERE year_published = ? ORDER BY rank",
        (year,)
    ).fetchall()
    return [dict(g) for g in games]


def get_all_matches():
    db = get_db()
    matches = db.execute("""
        SELECT * FROM matches ORDER BY round, position
    """).fetchall()
    result = []
    for m in matches:
        d = dict(m)
        if m["winner"]:
            mid = m["match_id"]
            d["votes_a"] = db.execute(
                "SELECT COUNT(*) as c FROM votes WHERE match_id = ? AND voted_for = ?",
                (mid, m["year_a"])
            ).fetchone()["c"]
            d["votes_b"] = db.execute(
                "SELECT COUNT(*) as c FROM votes WHERE match_id = ? AND voted_for = ?",
                (mid, m["year_b"])
            ).fetchone()["c"]
        else:
            d["votes_a"] = 0
            d["votes_b"] = 0
        result.append(d)
    return result


def get_all_years():
    db = get_db()
    years = db.execute("SELECT * FROM years ORDER BY seed").fetchall()
    return [dict(y) for y in years]


def advance_round():
    """Tally votes for active matches, set winners.

    Wave-aware: if the current round has >4 matches and unactivated ones remain,
    activates the next batch of 4 instead of jumping to the next round.
    """
    db = get_db()
    current_round = get_current_round()

    active_matches = db.execute(
        "SELECT * FROM matches WHERE round = ? AND is_active = 1 AND winner IS NULL",
        (current_round,)
    ).fetchall()

    if not active_matches:
        return {"error": "No active matches to advance"}

    results = []
    for match in active_matches:
        mid = match["match_id"]
        votes_a = db.execute(
            "SELECT COUNT(*) as c FROM votes WHERE match_id = ? AND voted_for = ?",
            (mid, match["year_a"])
        ).fetchone()["c"]
        votes_b = db.execute(
            "SELECT COUNT(*) as c FROM votes WHERE match_id = ? AND voted_for = ?",
            (mid, match["year_b"])
        ).fetchone()["c"]

        # Winner is whichever year got more votes; tie goes to year_a (higher seed)
        winner = match["year_a"] if votes_a >= votes_b else match["year_b"]

        db.execute(
            "UPDATE matches SET winner = ?, is_active = 0 WHERE match_id = ?",
            (winner, mid)
        )

        # Place winner into next match
        if match["next_match_id"]:
            next_match = db.execute(
                "SELECT * FROM matches WHERE match_id = ?",
                (match["next_match_id"],)
            ).fetchone()
            if next_match["year_a"] is None:
                db.execute(
                    "UPDATE matches SET year_a = ? WHERE match_id = ?",
                    (winner, match["next_match_id"])
                )
            else:
                db.execute(
                    "UPDATE matches SET year_b = ? WHERE match_id = ?",
                    (winner, match["next_match_id"])
                )

        results.append({
            "match_id": mid,
            "year_a": match["year_a"],
            "year_b": match["year_b"],
            "votes_a": votes_a,
            "votes_b": votes_b,
            "winner": winner,
        })

    # Check for remaining unactivated matches in the current round
    pending = db.execute(
        "SELECT match_id FROM matches WHERE round = ? AND is_active = 0 AND winner IS NULL "
        "ORDER BY position",
        (current_round,)
    ).fetchall()

    if pending:
        # More waves left in this round — activate next batch of up to 4
        for row in pending[:4]:
            db.execute(
                "UPDATE matches SET is_active = 1 WHERE match_id = ?", (row["match_id"],)
            )
        next_round = current_round
    else:
        # All matches in this round done — advance to next round
        next_round = current_round + 1
        next_matches = db.execute(
            "SELECT match_id FROM matches WHERE round = ? ORDER BY position", (next_round,)
        ).fetchall()
        if next_matches:
            if len(next_matches) > 4:
                # Large round: start with first wave of 4
                for row in next_matches[:4]:
                    db.execute(
                        "UPDATE matches SET is_active = 1 WHERE match_id = ?", (row["match_id"],)
                    )
            else:
                # Small round (QF/SF/Final): activate all at once
                db.execute(
                    "UPDATE matches SET is_active = 1 WHERE round = ?", (next_round,)
                )
            db.execute(
                "UPDATE tournament_state SET value = ? WHERE key = 'current_round'",
                (str(next_round),)
            )

    db.commit()
    return {"advanced": len(results), "results": results, "next_round": next_round}


def get_wave_info():
    """Returns (current_wave, total_waves) if the current round uses wave mode, else None.

    Wave mode applies when a round has more than 4 matches.
    """
    db = get_db()
    current_round = get_current_round()
    total = db.execute(
        "SELECT COUNT(*) as c FROM matches WHERE round = ?", (current_round,)
    ).fetchone()["c"]
    if total <= 4:
        return None
    completed = db.execute(
        "SELECT COUNT(*) as c FROM matches WHERE round = ? AND winner IS NOT NULL",
        (current_round,)
    ).fetchone()["c"]
    return ((completed // 4) + 1, total // 4)


def reset_current_wave():
    """Clear votes for the currently active (no-winner) matches so the wave can be re-voted."""
    db = get_db()
    current_round = get_current_round()
    active = db.execute(
        "SELECT match_id FROM matches WHERE round = ? AND is_active = 1 AND winner IS NULL",
        (current_round,)
    ).fetchall()
    for row in active:
        db.execute("DELETE FROM votes WHERE match_id = ?", (row["match_id"],))
    db.commit()
    return {"cleared_matches": len(active)}


def reset_current_round():
    """Roll back the entire current round: clear all its votes, re-open first wave.

    Also NULLs out the year slots in the next round that were populated by this
    round's (now-cancelled) winners.
    """
    db = get_db()
    current_round = get_current_round()

    # Clear votes and reset all matches in this round
    for row in db.execute(
        "SELECT match_id FROM matches WHERE round = ?", (current_round,)
    ).fetchall():
        db.execute("DELETE FROM votes WHERE match_id = ?", (row["match_id"],))
    db.execute(
        "UPDATE matches SET winner = NULL, is_active = 0 WHERE round = ?",
        (current_round,)
    )

    # NULL out year slots that were filled in the next round by this round's winners
    db.execute(
        "UPDATE matches SET year_a = NULL, year_b = NULL WHERE round = ?",
        (current_round + 1,)
    )

    # Re-activate first wave of this round
    first_wave = db.execute(
        "SELECT match_id FROM matches WHERE round = ? ORDER BY position LIMIT 4",
        (current_round,)
    ).fetchall()
    for row in first_wave:
        db.execute("UPDATE matches SET is_active = 1 WHERE match_id = ?", (row["match_id"],))

    db.commit()
    return {"round_reset": current_round}


def get_completed_matches(round_num=None):
    db = get_db()
    if round_num:
        matches = db.execute(
            "SELECT * FROM matches WHERE round = ? AND winner IS NOT NULL ORDER BY position",
            (round_num,)
        ).fetchall()
    else:
        matches = db.execute(
            "SELECT * FROM matches WHERE winner IS NOT NULL ORDER BY round, position"
        ).fetchall()

    result = []
    for m in matches:
        mid = m["match_id"]
        votes_a = db.execute(
            "SELECT COUNT(*) as c FROM votes WHERE match_id = ? AND voted_for = ?",
            (mid, m["year_a"])
        ).fetchone()["c"]
        votes_b = db.execute(
            "SELECT COUNT(*) as c FROM votes WHERE match_id = ? AND voted_for = ?",
            (mid, m["year_b"])
        ).fetchone()["c"]
        d = dict(m)
        d["votes_a"] = votes_a
        d["votes_b"] = votes_b
        result.append(d)
    return result


def get_tournament_winner():
    db = get_db()
    # The final is the match with no next_match_id
    final = db.execute(
        "SELECT * FROM matches WHERE next_match_id IS NULL AND winner IS NOT NULL"
    ).fetchone()
    return dict(final) if final else None


import json as _json


def is_results_revealed(round_num: int) -> bool:
    db = get_db()
    row = db.execute(
        "SELECT value FROM tournament_state WHERE key = 'results_revealed'"
    ).fetchone()
    if not row:
        return False
    try:
        return round_num in _json.loads(row["value"])
    except Exception:
        return False


def reveal_results_for_round(round_num: int):
    db = get_db()
    row = db.execute(
        "SELECT value FROM tournament_state WHERE key = 'results_revealed'"
    ).fetchone()
    try:
        revealed = _json.loads(row["value"]) if row else []
    except Exception:
        revealed = []
    if round_num not in revealed:
        revealed.append(round_num)
    db.execute(
        "INSERT OR REPLACE INTO tournament_state (key, value) VALUES ('results_revealed', ?)",
        (_json.dumps(revealed),)
    )
    db.commit()


def get_voting_deadline() -> str | None:
    db = get_db()
    row = db.execute(
        "SELECT value FROM tournament_state WHERE key = 'voting_deadline'"
    ).fetchone()
    if not row or not row["value"].strip():
        return None
    return row["value"].strip()


def set_voting_deadline(deadline_str: str):
    db = get_db()
    db.execute(
        "INSERT OR REPLACE INTO tournament_state (key, value) VALUES ('voting_deadline', ?)",
        (deadline_str,)
    )
    db.commit()

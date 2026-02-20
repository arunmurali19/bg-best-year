"""Voting logic: cast votes, check status, get results."""

import uuid
from flask import request
from webapp.database import get_db


def get_or_create_voter_id():
    """Get voter UUID from cookie, or generate a new one."""
    voter_id = request.cookies.get("voter_id")
    if not voter_id:
        voter_id = str(uuid.uuid4())
    return voter_id


def cast_vote(match_id: int, voted_for: int, voter_id: str) -> dict:
    """Cast a vote. Returns success status and current results."""
    db = get_db()

    # Verify match is active
    match = db.execute(
        "SELECT * FROM matches WHERE match_id = ? AND is_active = 1 AND winner IS NULL",
        (match_id,)
    ).fetchone()
    if not match:
        return {"success": False, "error": "Match is not active"}

    # Verify voted_for is one of the two years in the match
    if voted_for not in (match["year_a"], match["year_b"]):
        return {"success": False, "error": "Invalid year for this match"}

    # Try to insert (UNIQUE constraint on match_id, voter_id prevents duplicates)
    cursor = db.execute(
        "INSERT OR IGNORE INTO votes (match_id, voted_for, voter_id, ip_address) "
        "VALUES (?, ?, ?, ?)",
        (match_id, voted_for, voter_id, request.remote_addr),
    )
    db.commit()

    already_voted = cursor.rowcount == 0
    results = get_match_results(match_id)

    return {
        "success": not already_voted,
        "already_voted": already_voted,
        "results": results,
    }


def get_match_results(match_id: int) -> dict:
    """Get vote counts for a match."""
    db = get_db()
    match = db.execute(
        "SELECT * FROM matches WHERE match_id = ?", (match_id,)
    ).fetchone()
    if not match:
        return {}

    votes_a = db.execute(
        "SELECT COUNT(*) as c FROM votes WHERE match_id = ? AND voted_for = ?",
        (match_id, match["year_a"])
    ).fetchone()["c"]
    votes_b = db.execute(
        "SELECT COUNT(*) as c FROM votes WHERE match_id = ? AND voted_for = ?",
        (match_id, match["year_b"])
    ).fetchone()["c"]

    total = votes_a + votes_b
    return {
        "year_a": match["year_a"],
        "year_b": match["year_b"],
        "votes_a": votes_a,
        "votes_b": votes_b,
        "pct_a": round(votes_a / total * 100, 1) if total > 0 else 0,
        "pct_b": round(votes_b / total * 100, 1) if total > 0 else 0,
        "total": total,
    }


def has_voted(match_id: int, voter_id: str) -> int | None:
    """Check if voter already voted on this match. Returns voted_for year or None."""
    db = get_db()
    row = db.execute(
        "SELECT voted_for FROM votes WHERE match_id = ? AND voter_id = ?",
        (match_id, voter_id),
    ).fetchone()
    return row["voted_for"] if row else None

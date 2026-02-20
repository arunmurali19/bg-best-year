"""Voting logic: cast votes, check finalization, get results."""

import uuid
from datetime import datetime
from flask import request
from webapp.database import get_db


def get_or_create_voter_id():
    """Get voter UUID from cookie, or generate a new one."""
    voter_id = request.cookies.get("voter_id")
    if not voter_id:
        voter_id = str(uuid.uuid4())
    return voter_id


def is_voter_finalized(voter_id: str) -> bool:
    """True if voter explicitly finalised OR the voting deadline has passed."""
    db = get_db()
    row = db.execute(
        "SELECT 1 FROM voter_finalizations WHERE voter_id = ?", (voter_id,)
    ).fetchone()
    if row:
        return True
    # Check if deadline has passed
    dl = db.execute(
        "SELECT value FROM tournament_state WHERE key = 'voting_deadline'"
    ).fetchone()
    if dl and dl["value"].strip():
        try:
            if datetime.now() > datetime.fromisoformat(dl["value"].strip()):
                return True
        except Exception:
            pass
    return False


def finalize_voter(voter_id: str):
    """Lock in this voter's picks — they can no longer change votes."""
    db = get_db()
    db.execute(
        "INSERT OR IGNORE INTO voter_finalizations (voter_id) VALUES (?)", (voter_id,)
    )
    db.commit()


def cast_vote(match_id: int, voted_for: int, voter_id: str) -> dict:
    """Cast or change a vote. Rejected if voter is finalised or match inactive."""
    db = get_db()

    match = db.execute(
        "SELECT * FROM matches WHERE match_id = ? AND is_active = 1 AND winner IS NULL",
        (match_id,)
    ).fetchone()
    if not match:
        return {"success": False, "error": "Match is not active"}

    if is_voter_finalized(voter_id):
        return {"success": False, "error": "Your votes are finalised"}

    if voted_for not in (match["year_a"], match["year_b"]):
        return {"success": False, "error": "Invalid year for this match"}

    # INSERT OR REPLACE allows changing a previous vote
    db.execute(
        "INSERT OR REPLACE INTO votes (match_id, voted_for, voter_id, ip_address) "
        "VALUES (?, ?, ?, ?)",
        (match_id, voted_for, voter_id, request.remote_addr),
    )
    db.commit()

    return {"success": True, "voted_for": voted_for}


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


def has_voted(match_id: int, voter_id: str):
    """Returns the year the voter chose for this match, or None."""
    db = get_db()
    row = db.execute(
        "SELECT voted_for FROM votes WHERE match_id = ? AND voter_id = ?",
        (match_id, voter_id),
    ).fetchone()
    return row["voted_for"] if row else None

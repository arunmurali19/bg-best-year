"""Admin routes: advance rounds, view stats."""

import json
from flask import Blueprint, render_template, redirect, url_for, current_app, request
from webapp.services import tournament
from webapp.database import get_db

admin_bp = Blueprint("admin", __name__)


def check_secret(secret):
    return secret == current_app.config["ADMIN_SECRET"]


@admin_bp.route("/admin/<secret>")
def dashboard(secret):
    if not check_secret(secret):
        return "Unauthorized", 403

    current_round = tournament.get_current_round()
    round_name = tournament.get_round_name(current_round)
    active = tournament.get_active_matchups()
    completed = tournament.get_completed_matches()
    winner = tournament.get_tournament_winner()

    db = get_db()
    # Vote stats for active matches
    for m in active:
        mid = m["match_id"]
        votes_a = db.execute(
            "SELECT COUNT(*) as c FROM votes WHERE match_id = ? AND voted_for = ?",
            (mid, m["year_a"])
        ).fetchone()["c"]
        votes_b = db.execute(
            "SELECT COUNT(*) as c FROM votes WHERE match_id = ? AND voted_for = ?",
            (mid, m["year_b"])
        ).fetchone()["c"]
        m["votes_a"] = votes_a
        m["votes_b"] = votes_b
        m["total_votes"] = votes_a + votes_b

    total_votes = db.execute("SELECT COUNT(*) as c FROM votes").fetchone()["c"]
    unique_voters = db.execute(
        "SELECT COUNT(DISTINCT voter_id) as c FROM votes"
    ).fetchone()["c"]

    # Build seed lookup for admin view
    year_seeds = {r["year"]: r["seed"] for r in
                  db.execute("SELECT year, seed FROM years ORDER BY seed").fetchall()}

    # Revealed rounds
    row = db.execute(
        "SELECT value FROM tournament_state WHERE key = 'results_revealed'"
    ).fetchone()
    try:
        revealed_rounds = json.loads(row["value"]) if row else []
    except Exception:
        revealed_rounds = []

    # Group completed matches by round for the reveal UI
    completed_by_round = {}
    for m in completed:
        r = m["round"]
        if r not in completed_by_round:
            completed_by_round[r] = {
                "name": tournament.get_round_name(r),
                "matches": [],
                "revealed": r in revealed_rounds,
            }
        completed_by_round[r]["matches"].append(m)

    deadline = tournament.get_voting_deadline() or ""

    return render_template(
        "admin.html",
        secret=secret,
        current_round=current_round,
        round_name=round_name,
        active=active,
        completed=completed,
        completed_by_round=completed_by_round,
        winner=winner,
        total_votes=total_votes,
        unique_voters=unique_voters,
        year_seeds=year_seeds,
        revealed_rounds=revealed_rounds,
        deadline=deadline,
    )


@admin_bp.route("/admin/<secret>/advance", methods=["POST"])
def advance(secret):
    if not check_secret(secret):
        return "Unauthorized", 403

    tournament.advance_round()
    return redirect(url_for("admin.dashboard", secret=secret))


@admin_bp.route("/admin/<secret>/reveal/<int:round_num>", methods=["POST"])
def reveal_round(secret, round_num):
    if not check_secret(secret):
        return "Unauthorized", 403

    tournament.reveal_results_for_round(round_num)
    return redirect(url_for("admin.dashboard", secret=secret))


@admin_bp.route("/admin/<secret>/set_deadline", methods=["POST"])
def set_deadline(secret):
    if not check_secret(secret):
        return "Unauthorized", 403

    deadline = request.form.get("deadline", "").strip()
    tournament.set_voting_deadline(deadline)
    return redirect(url_for("admin.dashboard", secret=secret))


@admin_bp.route("/admin/<secret>/reset", methods=["POST"])
def reset_tournament(secret):
    if not check_secret(secret):
        return "Unauthorized", 403

    db = get_db()
    db.execute("DELETE FROM votes")
    db.execute("UPDATE matches SET winner = NULL, is_active = 0")
    db.execute("UPDATE matches SET year_a = NULL, year_b = NULL WHERE round > 1")
    db.execute("UPDATE matches SET is_active = 1 WHERE round = 1")
    db.execute("UPDATE tournament_state SET value = '1' WHERE key = 'current_round'")

    # Re-populate round 1 from tournament seed
    from pathlib import Path
    seed_path = Path(current_app.root_path).parent / "data" / "tournament_seed.json"
    with open(seed_path) as f:
        t = json.load(f)
    for m in t["matches"]:
        if m["round"] == 1:
            db.execute(
                "UPDATE matches SET year_a = ?, year_b = ? WHERE match_id = ?",
                (m["year_a"], m["year_b"], m["match_id"])
            )

    db.commit()
    return redirect(url_for("admin.dashboard", secret=secret))

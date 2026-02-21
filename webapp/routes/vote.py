"""Voting routes: landing page, matchup detail, vote submission."""

from flask import Blueprint, render_template, request, jsonify, make_response
from webapp.services import tournament, voting

vote_bp = Blueprint("vote", __name__)


@vote_bp.route("/")
def index():
    current_round = tournament.get_current_round()
    round_name = tournament.get_round_name(current_round)
    matchups = tournament.get_active_matchups()
    winner = tournament.get_tournament_winner()
    revealed = tournament.is_results_revealed(current_round)
    deadline = tournament.get_voting_deadline()

    voter_id = voting.get_or_create_voter_id()
    voter_finalized = voting.is_voter_finalized(voter_id)
    wave_info = tournament.get_wave_info()

    all_voted = bool(matchups)
    for m in matchups:
        m["user_voted"] = voting.has_voted(m["match_id"], voter_id)
        if not m["user_voted"]:
            all_voted = False
        if m["user_voted"] and revealed:
            m["results"] = voting.get_match_results(m["match_id"])

    resp = make_response(render_template(
        "index.html",
        matchups=matchups,
        current_round=current_round,
        round_name=round_name,
        winner=winner,
        voting_deadline=deadline,
        voter_finalized=voter_finalized,
        all_voted=all_voted,
        wave_info=wave_info,
    ))
    resp.set_cookie("voter_id", voter_id, max_age=365 * 24 * 3600, samesite="Lax", secure=True)
    return resp


@vote_bp.route("/matchup/<int:match_id>")
def matchup(match_id):
    match = tournament.get_match(match_id)
    if not match:
        return "Match not found", 404

    games_a = tournament.get_games_for_year(match["year_a"]) if match["year_a"] else []
    games_b = tournament.get_games_for_year(match["year_b"]) if match["year_b"] else []

    voter_id = voting.get_or_create_voter_id()
    user_voted = voting.has_voted(match_id, voter_id)
    voter_finalized = voting.is_voter_finalized(voter_id)
    revealed = tournament.is_results_revealed(match["round"])
    results = voting.get_match_results(match_id) if revealed and (user_voted or match["winner"]) else None

    round_name = tournament.get_round_name(match["round"])
    # Flip only Round 1 (same rule as bracket): odd match_ids show year_b on left.
    # Rounds 2+ never flip so winners stay in the position they earned.
    flip = match["round"] == 1 and match["match_id"] % 2 != 0
    deadline = tournament.get_voting_deadline()

    resp = make_response(render_template(
        "matchup.html",
        match=match,
        games_a=games_a,
        games_b=games_b,
        user_voted=user_voted,
        voter_finalized=voter_finalized,
        results=results,
        revealed=revealed,
        round_name=round_name,
        flip=flip,
        voting_deadline=deadline,
    ))
    resp.set_cookie("voter_id", voter_id, max_age=365 * 24 * 3600, samesite="Lax", secure=True)
    return resp


@vote_bp.route("/matchup/<int:match_id>/vote", methods=["POST"])
def submit_vote(match_id):
    data = request.get_json()
    if not data or "year" not in data:
        return jsonify({"success": False, "error": "Missing year"}), 400

    voter_id = voting.get_or_create_voter_id()
    result = voting.cast_vote(match_id, int(data["year"]), voter_id)

    resp = jsonify(result)
    resp.set_cookie("voter_id", voter_id, max_age=365 * 24 * 3600, samesite="Lax", secure=True)
    return resp


@vote_bp.route("/results")
def results():
    current_round = tournament.get_current_round()
    completed = tournament.get_completed_matches()

    # Only show rounds where admin has revealed results
    rounds = {}
    for m in completed:
        r = m["round"]
        if not tournament.is_results_revealed(r):
            continue
        if r not in rounds:
            rounds[r] = {"name": tournament.get_round_name(r), "matches": []}
        rounds[r]["matches"].append(m)

    return render_template("results.html", rounds=rounds, current_round=current_round)

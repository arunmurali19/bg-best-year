"""Bracket display routes."""

from flask import Blueprint, render_template, jsonify
from webapp.services import tournament

bracket_bp = Blueprint("bracket", __name__)


@bracket_bp.route("/bracket")
def bracket_page():
    matches = tournament.get_all_matches()
    current_round = tournament.get_current_round()
    winner = tournament.get_tournament_winner()

    # Assign each match to a section (Blue, Red, Yellow, Green)
    # based on which quadrant of the bracket it belongs to.
    # R1: 16 matches split into 4 groups of 4
    # Each group feeds through successive rounds until semifinals.
    section_map = {}
    r1_matches = [m for m in matches if m["round"] == 1]
    r1_matches.sort(key=lambda m: m["position"])

    quarter_size = len(r1_matches) // 4
    sections = ["blue", "red", "yellow", "green"]

    for i, m in enumerate(r1_matches):
        sec = sections[i // quarter_size] if quarter_size > 0 else "blue"
        section_map[m["match_id"]] = sec

    # Propagate sections to later rounds via next_match_id
    match_by_id = {m["match_id"]: m for m in matches}
    for m in sorted(matches, key=lambda x: (x["round"], x["position"])):
        mid = m["match_id"]
        if mid in section_map and m.get("next_match_id"):
            nid = m["next_match_id"]
            if nid not in section_map:
                section_map[nid] = section_map[mid]
            # If next match already assigned to a different section,
            # it's a merge point (semi/final) - mark as "merge"
            elif section_map[nid] != section_map[mid]:
                section_map[nid] = "merge"

    # Flip only Round 1 to randomise which year appears on top.
    # Rounds 2+ must NOT flip: the winner from the top R1 match fills year_a of the
    # next match, so showing year_a on top preserves correct bracket progression.
    flip_map = {m["match_id"]: (m["round"] == 1 and m["match_id"] % 2 != 0) for m in matches}

    return render_template(
        "bracket.html",
        matches=matches,
        current_round=current_round,
        winner=winner,
        section_map=section_map,
        flip_map=flip_map,
    )


@bracket_bp.route("/bracket/data")
def bracket_data():
    matches = tournament.get_all_matches()
    years = tournament.get_all_years()
    current_round = tournament.get_current_round()

    # Strip seed from public API
    for y in years:
        y.pop("seed", None)

    return jsonify({
        "matches": matches,
        "years": years,
        "current_round": current_round,
    })

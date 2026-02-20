document.addEventListener("DOMContentLoaded", function () {
    document.getElementById("matchup-columns");

    // Attach listeners to all vote buttons (including switch-btn)
    function attachListeners() {
        document.querySelectorAll(".vote-btn:not([disabled])").forEach(function (btn) {
            btn.addEventListener("click", handleVote);
        });
    }

    function handleVote() {
        var btn = this;
        var matchId = btn.dataset.match;
        var year = parseInt(btn.dataset.year);

        // Disable all buttons while request is in flight
        document.querySelectorAll(".vote-btn").forEach(function (b) {
            b.disabled = true;
        });

        fetch("/matchup/" + matchId + "/vote", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ year: year }),
        })
            .then(function (resp) { return resp.json(); })
            .then(function (data) {
                if (data.success) {
                    showVotedState(data.voted_for);
                } else {
                    // Re-enable on error
                    document.querySelectorAll(".vote-btn").forEach(function (b) {
                        b.disabled = false;
                    });
                }
            })
            .catch(function () {
                document.querySelectorAll(".vote-btn").forEach(function (b) {
                    b.disabled = false;
                });
            });
    }

    function showVotedState(votedYear) {
        // Update banner
        var banner = document.getElementById("results-banner");
        if (!banner) {
            banner = document.createElement("div");
            banner.id = "results-banner";
            var title = document.querySelector(".matchup-title");
            title.parentNode.insertBefore(banner, title.nextSibling);
        }
        banner.className = "voted-notice";
        banner.innerHTML =
            "<p><strong>&#10003; You voted for " + votedYear + ".</strong></p>" +
            "<p class=\"voted-subtext\">You can still change your pick below, or go back and finalise all your votes.</p>";

        // Update buttons: current pick → disabled; other year → switch button
        document.querySelectorAll(".vote-btn").forEach(function (b) {
            var bYear = parseInt(b.dataset.year);
            if (bYear === votedYear) {
                b.className = "vote-btn current-pick";
                b.disabled = true;
                b.textContent = "\u2713 Current pick";
                b.closest(".year-column").classList.add("selected");
            } else {
                b.className = "vote-btn switch-btn";
                b.disabled = false;
                b.textContent = "Switch to " + bYear;
                b.closest(".year-column").classList.remove("selected");
                b.removeEventListener("click", handleVote);
                b.addEventListener("click", handleVote);
            }
        });
    }

    attachListeners();
});

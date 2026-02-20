document.addEventListener("DOMContentLoaded", function () {
    const buttons = document.querySelectorAll(".vote-btn");
    const flip = document.getElementById("matchup-columns")?.dataset.flip === "true";

    buttons.forEach(function (btn) {
        btn.addEventListener("click", function () {
            const matchId = btn.dataset.match;
            const year = btn.dataset.year;

            // Disable all vote buttons immediately
            buttons.forEach(function (b) {
                b.disabled = true;
                b.textContent = "Voting...";
            });

            fetch("/matchup/" + matchId + "/vote", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ year: parseInt(year) }),
            })
                .then(function (resp) { return resp.json(); })
                .then(function (data) {
                    if (data.results) {
                        showResults(data.results, parseInt(year), flip);
                    }
                    // Update buttons
                    buttons.forEach(function (b) {
                        if (b.dataset.year === year) {
                            b.textContent = "Voted!";
                            b.closest(".year-column").classList.add("selected");
                        } else {
                            b.remove();
                        }
                    });
                })
                .catch(function (err) {
                    console.error("Vote failed:", err);
                    buttons.forEach(function (b) {
                        b.disabled = false;
                        b.textContent = "Vote for " + b.dataset.year;
                    });
                });
        });
    });

    function showResults(results, votedYear, flipped) {
        // If the display is flipped, year_b is shown on the left (bar-a)
        var leftYear  = flipped ? results.year_b : results.year_a;
        var leftPct   = flipped ? results.pct_b  : results.pct_a;
        var rightYear = flipped ? results.year_a  : results.year_b;
        var rightPct  = flipped ? results.pct_a   : results.pct_b;

        var banner = document.getElementById("results-banner");
        if (!banner) {
            banner = document.createElement("div");
            banner.id = "results-banner";
            banner.className = "results-banner";
            var title = document.querySelector(".matchup-title");
            title.parentNode.insertBefore(banner, title.nextSibling);
        }
        banner.innerHTML =
            '<div class="result-row">' +
            '<div class="result-side-label">' +
            "<strong>" + leftYear + "</strong>" +
            "<span>" + leftPct + "%</span>" +
            "</div>" +
            '<div class="result-bar">' +
            '<div class="bar-fill bar-a" style="width: ' + leftPct + '%"></div>' +
            '<div class="bar-fill bar-b" style="width: ' + rightPct + '%"></div>' +
            "</div>" +
            '<div class="result-side-label right-label">' +
            "<span>" + rightPct + "%</span>" +
            "<strong>" + rightYear + "</strong>" +
            "</div>" +
            "</div>" +
            '<p class="vote-count">' + results.total + " total vote" +
            (results.total !== 1 ? "s" : "") + "</p>";
    }
});

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
                    // Show thank-you notice — results are revealed by admin later
                    showThankYou(parseInt(year));
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

    function showThankYou(votedYear) {
        // Replace or create the banner with a thank-you message
        var banner = document.getElementById("results-banner");
        if (!banner) {
            banner = document.createElement("div");
            banner.id = "results-banner";
            var title = document.querySelector(".matchup-title");
            title.parentNode.insertBefore(banner, title.nextSibling);
        }
        banner.className = "voted-notice";
        banner.innerHTML =
            "<p><strong>&#10003; Thank you for voting!</strong></p>" +
            "<p class=\"voted-subtext\">Results will be revealed by the admin after the round ends.</p>";

        // Update columns: mark the voted year, remove the other button
        buttons.forEach(function (b) {
            if (parseInt(b.dataset.year) === votedYear) {
                b.closest(".year-column").classList.add("selected");
                b.disabled = true;
                b.textContent = "Voted!";
            } else {
                b.remove();
            }
        });
    }
});

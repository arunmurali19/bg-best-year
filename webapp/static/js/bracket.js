document.addEventListener("DOMContentLoaded", function () {
    // Use rAF to ensure DOM is fully painted before measuring
    requestAnimationFrame(function () {
        layoutBracket();
        fitBracket();
        drawBracketLines();
    });

    window.addEventListener("resize", function () {
        layoutBracket();
        fitBracket();
        drawBracketLines();
    });

    // Keep the mobile back bar pinned to the bottom of the VISUAL viewport.
    // position:fixed is relative to the layout viewport and disappears when the
    // user pinch-zooms. Switching to position:absolute lets us place the element
    // at exact document-coordinate offsets derived from the visualViewport API.
    function repositionMobileBar() {
        var bar = document.querySelector(".mobile-back-bar");
        if (!bar || !window.visualViewport) return;
        var vv    = window.visualViewport;
        var s     = vv.scale || 1;          // pinch-zoom factor (1 = no zoom)
        var barW  = bar.offsetWidth  || 120;
        var barH  = bar.offsetHeight || 44;
        // pageLeft/pageTop = visual viewport origin in document coordinates
        var pageLeft = vv.pageLeft !== undefined ? vv.pageLeft : (window.scrollX + vv.offsetLeft);
        var pageTop  = vv.pageTop  !== undefined ? vv.pageTop  : (window.scrollY + vv.offsetTop);

        // Scale the element down by 1/s so it keeps the same visual size at any zoom.
        // With transform-origin: left top the left/top edges stay at the CSS pixel
        // positions we set, and the element shrinks inward/downward.
        bar.style.position        = "absolute";
        bar.style.bottom          = "auto";
        bar.style.transformOrigin = "left top";
        bar.style.transform       = "scale(" + (1 / s) + ")";
        // Centre horizontally: left edge = viewport_centre - half_scaled_width
        bar.style.left = Math.round(pageLeft + vv.width / 2 - barW / (2 * s)) + "px";
        // Pin bottom edge 19 CSS-px above the visual viewport bottom
        bar.style.top  = Math.round(pageTop + vv.height - barH / s - 19) + "px";
    }

    if (window.visualViewport) {
        window.visualViewport.addEventListener("resize", repositionMobileBar);
        window.visualViewport.addEventListener("scroll", repositionMobileBar);
        window.addEventListener("scroll", repositionMobileBar);
        repositionMobileBar();
    }
});

/**
 * Positions each bracket-match absolutely within its round-matches container
 * so that every match is vertically centred between the two matches that feed
 * into it — the classic knockout-bracket alignment.
 *
 * Formula for left side (positions 1..LEFT_SLOTS in R1):
 *   y_center(round R, 0-indexed slot S) = 2^(R-1) * (S + 0.5) * UNIT
 *
 * Right side uses the same formula after mapping its DB position to a 0-indexed slot.
 * The final is centred in the column (TOTAL_HEIGHT / 2).
 */
function layoutBracket() {
    var bracketEl = document.querySelector(".bracket");
    if (!bracketEl) return;

    var numRounds = parseInt(bracketEl.getAttribute("data-num-rounds") || "5");

    // Measure the natural height of a single bracket-match (two bracket-team rows)
    var sampleMatch = document.querySelector(".bracket-match");
    if (!sampleMatch) return;
    // Temporarily clear absolute positioning to get intrinsic height
    sampleMatch.style.position = "static";
    var MATCH_HEIGHT = sampleMatch.offsetHeight || 48;
    sampleMatch.style.position = "absolute";

    var GAP = 14;                              // minimum vertical gap between matches
    var UNIT = MATCH_HEIGHT + GAP;             // height of one Round-1 slot
    // Number of Round-1 slots on each half (left or right)
    var LEFT_SLOTS = Math.pow(2, numRounds - 2);   // 8 for a 32-team (5-round) bracket
    var TOTAL_HEIGHT = LEFT_SLOTS * UNIT;

    // Measure round header height so we can account for it in column height
    var sampleHeader = document.querySelector(".round-label");
    var HEADER_HEIGHT = sampleHeader ? Math.ceil(sampleHeader.getBoundingClientRect().height) : 0;
    var COLUMN_HEIGHT = TOTAL_HEIGHT + HEADER_HEIGHT;

    // Apply column height (header + match area); let round-matches fill via flex
    document.querySelectorAll(".bracket-round").forEach(function (col) {
        col.style.height = COLUMN_HEIGHT + "px";
    });
    // Clear any previously set height on round-matches so CSS flex:1 controls it
    document.querySelectorAll(".round-matches").forEach(function (rm) {
        rm.style.height = "";
    });
    // Clear bracket-scroll height; let content determine it naturally
    var scroll = document.getElementById("bracket-scroll");
    if (scroll) scroll.style.height = "";

    // Position every match
    document.querySelectorAll(".bracket-match").forEach(function (el) {
        var side  = el.getAttribute("data-side")  || "left";
        var round = parseInt(el.getAttribute("data-round") || "1");
        var pos   = parseInt(el.getAttribute("data-pos")   || "1");

        var yCenter;

        if (side === "final") {
            // The final is always centred in the column
            yCenter = TOTAL_HEIGHT / 2;
        } else {
            var slot;
            if (side === "right") {
                // First DB position on the right half for this round:
                // right-half first pos = 2^(numRounds - round - 1) + 1
                var firstRight = Math.pow(2, numRounds - round - 1) + 1;
                slot = pos - firstRight;
            } else {
                // Left half: positions always start at 1
                slot = pos - 1;
            }
            var factor = Math.pow(2, round - 1);
            yCenter = factor * (slot + 0.5) * UNIT;
        }

        el.style.top = (yCenter - MATCH_HEIGHT / 2) + "px";
    });
}

/**
 * Scales the entire bracket-scroll element down via CSS transform so it
 * fits the available width without a horizontal scrollbar.
 */
function fitBracket() {
    var scroll    = document.getElementById("bracket-scroll");
    var container = document.getElementById("bracket-container");
    if (!scroll || !container) return;

    // Reset to measure natural width
    scroll.style.transform       = "none";
    scroll.style.transformOrigin = "top left";
    container.style.height       = "";

    var naturalWidth = scroll.scrollWidth;
    var availWidth   = container.clientWidth;

    if (naturalWidth > availWidth && availWidth > 0) {
        var scale = availWidth / naturalWidth;
        scroll.style.transform = "scale(" + scale + ")";
        // Pico CSS uses border-box sizing: padding is subtracted from the height value,
        // so we add it back to prevent the bottom of the bracket from being clipped.
        var cs = window.getComputedStyle(container);
        var vPad = parseFloat(cs.paddingTop) + parseFloat(cs.paddingBottom);
        container.style.height   = Math.ceil(scroll.scrollHeight * scale + vPad) + "px";
        container.style.overflow = "hidden";
    } else {
        container.style.overflow = "";
    }
}

/**
 * Draws SVG elbow-connector lines between each match and the match it feeds into.
 * Left-side matches connect right-edge → left-edge of destination.
 * Right-side matches connect left-edge → right-edge of destination (mirrored).
 */
function drawBracketLines() {
    var svg    = document.getElementById("bracket-svg");
    var scroll = document.getElementById("bracket-scroll");
    if (!svg || !scroll) return;

    svg.setAttribute("width",  scroll.scrollWidth);
    svg.setAttribute("height", scroll.scrollHeight);
    svg.innerHTML = "";

    // Current CSS scale applied to scroll (needed to convert screen coords → SVG coords)
    var scale = 1;
    var transform = scroll.style.transform || "";
    var scaleMatch = transform.match(/scale\(([^)]+)\)/);
    if (scaleMatch) scale = parseFloat(scaleMatch[1]);

    var scrollRect = scroll.getBoundingClientRect();
    var matches    = document.querySelectorAll(".bracket-match");
    var matchMap   = {};
    matches.forEach(function (el) {
        matchMap[el.getAttribute("data-match-id")] = el;
    });

    matches.forEach(function (el) {
        var nextId = el.getAttribute("data-next-match");
        if (!nextId) return;
        var nextEl = matchMap[nextId];
        if (!nextEl) return;

        var side    = el.getAttribute("data-side") || "left";
        var srcRect = el.getBoundingClientRect();
        var dstRect = nextEl.getBoundingClientRect();

        // Convert screen coordinates to unscaled SVG coordinates
        var srcX, dstX;
        var srcY = (srcRect.top  + srcRect.height / 2 - scrollRect.top)  / scale;
        var dstY = (dstRect.top  + dstRect.height / 2 - scrollRect.top)  / scale;

        if (side === "right") {
            // Right-side: exit from left edge, arrive at right edge of destination
            srcX = (srcRect.left  - scrollRect.left) / scale;
            dstX = (dstRect.right - scrollRect.left) / scale;
        } else {
            // Left-side (and final's inbound connectors): exit right, arrive left
            srcX = (srcRect.right - scrollRect.left) / scale;
            dstX = (dstRect.left  - scrollRect.left) / scale;
        }

        var midX = (srcX + dstX) / 2;

        var path = document.createElementNS("http://www.w3.org/2000/svg", "path");
        path.setAttribute("d",
            "M " + srcX + " " + srcY +
            " H " + midX +
            " V " + dstY +
            " H " + dstX
        );
        path.setAttribute("fill",         "none");
        path.setAttribute("stroke",       "#666666");
        path.setAttribute("stroke-width", "2");
        svg.appendChild(path);
    });
}

// Heatmap of one game at a time (ADR-014) with the region hover popup.
// All decisions (featured game, top lists, eligibility) arrive precomputed in
// the view model; this file only paints. The view calls initRegionMap once.
function initRegionMap({
    regions, games, featuredAppId, concentrationsByGame,
    geojsonUrl, mapElement, panelElement, headlineElement,
    searchInputElement, searchResultsElement,
}) {
    const regionByCountry = new Map();
    regions.forEach(region => {
        region.memberCountries.forEach(code => regionByCountry.set(code, region));
    });
    const gameById = new Map(games.map(game => [game.appId, game]));

    // ADR-014: single-hue log ramp (validated sequential blues), clamped to
    // [1/8, 8] — ~2% of real scores fall outside. White = tracked but no
    // signal for the shown game; gray = region outside the dataset.
    const rampBlues = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"];
    const color = d3.scaleSequentialLog(d3.interpolateRgbBasis(rampBlues))
        .domain([1 / 8, 8])
        .clamp(true);
    const trackedNoSignalFill = "#ffffff";
    const noDataFill = "#e3e3e3";

    const width = 960;
    const height = 500;
    const svg = d3.select(mapElement).append("svg")
        .attr("viewBox", `0 0 ${width} ${height}`);

    const popup = d3.select(mapElement).append("div")
        .attr("class", "map-popup")
        .style("display", "none");

    let activeGame = gameById.get(featuredAppId);
    let mode = "heatmap";
    let selectedRegion = null;

    const panelHintHtml =
        '<p class="region-panel-hint">Click a region to see which games are disproportionately popular there.</p>';

    function concentrationInRegion(game, region) {
        if (!game) return undefined;
        const byRegion = concentrationsByGame[game.appId];
        return byRegion ? byRegion[region.code] : undefined;
    }

    function showHeadline() {
        headlineElement.innerHTML = activeGame
            ? `Where is <strong>${activeGame.name}</strong> popular?`
            : "No tracked games yet — the first daily run will fill the map.";
    }

    function activeGameLine(region) {
        if (!activeGame) return "";
        const concentration = concentrationInRegion(activeGame, region);
        return concentration === undefined
            ? `<p class="popup-game-line popup-no-signal">${activeGame.name}: fewer than 50 reviews in this language — not enough signal</p>`
            : `<p class="popup-game-line">${activeGame.name} <span class="concentration">×${concentration.toFixed(2)}</span> here</p>`;
    }

    function blendedNote(region) {
        return region.blended
            ? `<p class="region-panel-blended">Blended region: one shared review language across ${region.memberCountries.join(", ")}.</p>`
            : "";
    }

    function showPopup(region, event) {
        const topThree = region.games.slice(0, 3).map(game =>
            `<li>${game.name} <span class="concentration">×${game.concentration.toFixed(2)}</span></li>`);
        popup
            .style("display", "block")
            .html(
                `<h3>${region.displayName}</h3>` +
                activeGameLine(region) +
                `<ol>${topThree.join("")}</ol>` +
                blendedNote(region));
        movePopup(event);
    }

    function movePopup(event) {
        const [x, y] = d3.pointer(event, mapElement);
        popup.style("left", `${x + 14}px`).style("top", `${y + 14}px`);
    }

    function hidePopup() {
        popup.style("display", "none");
    }

    function showRegionInPanel(region) {
        const gameItems = region.games.map(game =>
            `<li><a href="${game.storeUrl}" target="_blank" rel="noopener">${game.name}</a>` +
            ` <span class="concentration">×${game.concentration.toFixed(2)}</span></li>`);
        panelElement.innerHTML =
            `<h2>${region.displayName}</h2>` +
            blendedNote(region) +
            `<ol>${gameItems.join("")}</ol>`;
    }

    function showPanelHint() {
        panelElement.innerHTML = panelHintHtml;
    }

    showHeadline();

    // ADR-014/#14: typeahead over the embedded game list, no server round trip.
    const MAX_SUGGESTIONS = 10;
    const noMatchHtml =
        '<p class="search-no-match">Not tracked yet — we currently follow ' +
        "Steam's top 100 most-played games.</p>";

    function matchingGames(query) {
        const trimmed = query.trim().toLowerCase();
        const matches = trimmed === ""
            ? games
            : games.filter(game => game.name.toLowerCase().includes(trimmed));
        return matches.slice(0, MAX_SUGGESTIONS);
    }

    function renderSuggestions() {
        const matches = matchingGames(searchInputElement.value);
        searchResultsElement.innerHTML = matches.length === 0
            ? noMatchHtml
            : `<ul>${matches.map(game =>
                `<li data-app-id="${game.appId}">${game.name}</li>`).join("")}</ul>`;
    }

    searchInputElement.addEventListener("input", renderSuggestions);
    searchInputElement.addEventListener("focus", renderSuggestions);

    // Set once the map has finished loading (below) — selecting a game needs
    // the painting/mode functions that live inside that async callback.
    let selectGame = () => {};

    searchResultsElement.addEventListener("click", event => {
        const item = event.target.closest("li[data-app-id]");
        if (!item) return;
        selectGame(gameById.get(Number(item.dataset.appId)));
        searchInputElement.value = "";
        searchResultsElement.innerHTML = "";
    });

    d3.json(geojsonUrl).then(world => {
        const projection = d3.geoNaturalEarth1().fitSize([width, height], world);
        const path = d3.geoPath(projection);

        const regionOf = feature => regionByCountry.get(feature.properties.iso_a2);

        // SELECTED MODE (ADR-014/#11): heatmap gone — the selected region is
        // highlighted, other tracked regions go white, no-data stays gray.
        function fillFor(feature) {
            const region = regionOf(feature);
            if (!region) return noDataFill;
            if (mode === "selected") return trackedNoSignalFill;
            const concentration = concentrationInRegion(activeGame, region);
            return concentration === undefined ? trackedNoSignalFill : color(concentration);
        }

        svg.append("rect")
            .attr("width", width)
            .attr("height", height)
            .attr("fill", "transparent")
            .on("click", () => exitSelectedMode());

        const countries = svg.selectAll("path")
            .data(world.features)
            .join("path")
            .attr("d", path)
            .attr("fill", fillFor)
            .attr("stroke", "#cbcbcb")
            .attr("stroke-width", 0.5)
            .attr("class", feature => regionOf(feature) ? "country has-data" : "country");

        function setRegionHighlight(region, highlighted) {
            countries
                .filter(feature => regionOf(feature) === region)
                .classed("highlighted", highlighted);
        }

        function paintSelection() {
            countries.classed("selected", feature => regionOf(feature) === selectedRegion);
        }

        function enterSelectedMode(region) {
            mode = "selected";
            selectedRegion = region;
            countries.attr("fill", fillFor);
            paintSelection();
            showRegionInPanel(region);
        }

        function exitSelectedMode() {
            if (mode !== "selected") return;
            mode = "heatmap";
            selectedRegion = null;
            countries.attr("fill", fillFor);
            paintSelection();
            showPanelHint();
        }

        countries
            .on("mouseover", (event, feature) => {
                const region = regionOf(feature);
                if (!region) return;
                setRegionHighlight(region, true);
                showPopup(region, event);
            })
            .on("mousemove", (event, feature) => {
                if (regionOf(feature)) movePopup(event);
            })
            .on("mouseout", (event, feature) => {
                const region = regionOf(feature);
                if (!region) return;
                setRegionHighlight(region, false);
                hidePopup();
            })
            .on("click", (event, feature) => {
                event.stopPropagation();
                const region = regionOf(feature);
                if (!region) {
                    exitSelectedMode();
                } else if (mode === "selected" && region === selectedRegion) {
                    exitSelectedMode();
                } else {
                    enterSelectedMode(region);
                }
            });

        countries.filter(feature => !regionOf(feature))
            .append("title")
            .text(feature => `${feature.properties.name} — no data yet`);

        selectGame = game => {
            exitSelectedMode();
            activeGame = game;
            showHeadline();
            countries.attr("fill", fillFor);
        };

        document.addEventListener("keydown", event => {
            if (event.key === "Escape") exitSelectedMode();
        });
    });
}

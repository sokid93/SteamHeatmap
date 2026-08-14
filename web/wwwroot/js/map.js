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

    // ADR-014's encoding, ADR-015's colors: the ramp runs dark→light because it
    // sits on a dark surface now, so magnitude still reads as "more ink". Single
    // hue (11° spread), monotone lightness with every adjacent gap over the
    // 0.06 OKLCH floor, low end at 2.01:1 against the surface — validated, not
    // eyeballed. Still clamped to [1/8, 8]; ~2% of real scores fall outside.
    const rampBlues = ["#33587c", "#2f6ea6", "#2b86c9", "#439fe2", "#6fb8ef", "#9ed3f8", "#c9e9ff"];
    const color = d3.scaleSequentialLog(d3.interpolateRgbBasis(rampBlues))
        .domain([1 / 8, 8])
        .clamp(true);
    // Both neutral, so neither can be mistaken for a low rung of the blue ramp:
    // a region with no signal is a different category, not a smaller number.
    // Tracked-but-silent stays slightly more present than never-tracked.
    const trackedNoSignalFill = "#3d464e";
    const noDataFill = "#262b30";
    // Borders read as gaps between countries: darker than every fill, including
    // the ramp's low end.
    const countryStroke = "#131b24";

    // Height and viewBox are derived from the land once the geojson loads
    // (#21) — the map is cropped to what it actually draws.
    const width = 960;
    // Height 0 until the geojson lands: an svg with no viewBox and no intrinsic
    // size falls back to the replaced-element default of 150px, which would sit
    // under the loading placeholder and collapse when the map arrives (#19).
    const svg = d3.select(mapElement).append("svg").attr("height", 0);

    // Visibility is a class, not a display toggle, so CSS can transition it
    // (#20). Keeping the node in layout also means offsetWidth is measurable
    // while hidden, which is what movePopup's edge-flip needs.
    const popup = d3.select(mapElement).append("div")
        .attr("class", "map-popup");

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
            .classed("visible", true)
            .html(
                `<h3>${region.displayName}</h3>` +
                activeGameLine(region) +
                `<ol>${topThree.join("")}</ol>` +
                blendedNote(region));
        movePopup(event);
    }

    function movePopup(event) {
        const [x, y] = d3.pointer(event, mapElement);
        const popupWidth = popup.node().offsetWidth;
        const overflowsRight = x + 14 + popupWidth > mapElement.clientWidth;
        const left = overflowsRight ? x - 14 - popupWidth : x + 14;
        popup.style("left", `${left}px`).style("top", `${y + 14}px`);
    }

    function hidePopup() {
        popup.classed("visible", false);
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
        scheduleCatalogSearch(searchInputElement.value.trim().toLowerCase(), matches);
    }

    // #26: the embedded dataset (above) only covers today's top-100 ∪
    // still-relevant searched games (ADR-014) — the full catalog lives
    // server-side in steam_apps (#24). Local matches render first and
    // instantly; this only supplements them once local coverage runs thin,
    // and only with entries the local filter couldn't have found. Results
    // are informational only at this stage (no data-app-id, so the existing
    // click handler below already ignores them) — #27 makes them selectable.
    const CATALOG_SEARCH_DEBOUNCE_MS = 250;
    let catalogSearchTimer = null;
    let catalogSearchToken = 0;

    function renderCatalogResults(query, localMatches, catalogEntries) {
        // A slower response for a query the box no longer holds must not
        // clobber what's rendered for what's typed now.
        if (searchInputElement.value.trim().toLowerCase() !== query) return;
        const localIds = new Set(localMatches.map(game => game.appId));
        const untracked = catalogEntries.filter(entry => !localIds.has(entry.appId));
        if (untracked.length === 0) return;
        const items = untracked
            .map(entry => `<li class="search-untracked">${entry.name}` +
                '<span class="search-untracked-note">not yet tracked</span></li>')
            .join("");
        searchResultsElement.insertAdjacentHTML("beforeend", `<ul class="search-untracked-list">${items}</ul>`);
    }

    function scheduleCatalogSearch(query, localMatches) {
        clearTimeout(catalogSearchTimer);
        if (query === "" || localMatches.length >= MAX_SUGGESTIONS) return;
        const requestToken = ++catalogSearchToken;
        catalogSearchTimer = setTimeout(() => {
            fetch(`/Home/SearchCatalog?q=${encodeURIComponent(query)}`)
                .then(response => response.ok ? response.json() : [])
                .then(entries => {
                    if (requestToken !== catalogSearchToken) return; // superseded by a newer keystroke
                    renderCatalogResults(query, localMatches, entries);
                })
                .catch(() => {}); // best-effort supplement; local matches already rendered
        }, CATALOG_SEARCH_DEBOUNCE_MS);
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
        // #21: Antarctica is permanently grey no-data and takes ~15% of the
        // box, and fitting the rest of the world into a fixed 960x500 letterboxed
        // it besides. Drop AQ, then take the viewBox from the drawn land's own
        // bounds so the map fills its surface instead of padding itself with
        // empty ocean. Every other no-data country still renders (ADR-014).
        const land = {
            type: "FeatureCollection",
            features: world.features.filter(feature => feature.properties.iso_a2 !== "AQ"),
        };
        const projection = d3.geoNaturalEarth1().fitWidth(width, land);
        const path = d3.geoPath(projection);

        // Fiji sits on the antimeridian, so d3 draws it as two slivers pinned to
        // opposite edges and its bounding box spans the whole map. Measuring the
        // crop from it would spend 10% of the map's scale on empty ocean, so the
        // crop is measured from every other country and Fiji's slivers fall
        // outside the viewBox. No tracked region maps to FJ — it was grey
        // no-data either way. Rotating the projection instead doesn't help:
        // Chukotka and the Aleutians straddle the antimeridian too, so every
        // central meridian splits something.
        const cropReference = {
            type: "FeatureCollection",
            features: land.features.filter(feature => feature.properties.iso_a2 !== "FJ"),
        };
        const [[minX, minY], [maxX, maxY]] = path.bounds(cropReference);
        svg.attr("viewBox", `${minX} ${minY} ${maxX - minX} ${maxY - minY}`)
            .attr("height", null);

        // The svg now has a height, so the placeholder can go without the box
        // collapsing between the two (#19). Same tick as the paint below.
        const placeholder = mapElement.querySelector(".map-loading");
        if (placeholder) placeholder.remove();

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
            .attr("x", minX)
            .attr("y", minY)
            .attr("width", maxX - minX)
            .attr("height", maxY - minY)
            .attr("fill", "transparent")
            .on("click", () => exitSelectedMode());

        const countries = svg.selectAll("path")
            .data(land.features)
            .join("path")
            .attr("d", path)
            .attr("fill", fillFor)
            .attr("stroke", countryStroke)
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

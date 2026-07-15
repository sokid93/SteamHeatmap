// World heatmap and region panel. `regions` is the serialized
// RegionMapViewModel.Regions (camelCase); the view calls this once.
function initRegionMap({ regions, geojsonUrl, mapElement, panelElement }) {
    const regionByCountry = new Map();
    regions.forEach(region => {
        region.memberCountries.forEach(code => regionByCountry.set(code, region));
    });

    const width = 960;
    const height = 500;
    const svg = d3.select(mapElement).append("svg")
        .attr("viewBox", `0 0 ${width} ${height}`);

    const color = d3.scaleSequential(d3.interpolateYlOrRd).domain([0, 2]);
    const noDataFill = "#e3e3e3";

    function showRegionInPanel(region) {
        const blendedNote = region.blended
            ? `<p class="region-panel-blended">Blended region: one shared review language across ${region.memberCountries.join(", ")}.</p>`
            : "";
        const gameItems = region.games.map(game => {
            const concentration = game.concentration.toFixed(3);
            return `<li><a href="${game.storeUrl}" target="_blank" rel="noopener">${game.name}</a>` +
                ` <span class="concentration">×${concentration}</span></li>`;
        });
        panelElement.innerHTML =
            `<h2>${region.displayName}</h2>` +
            blendedNote +
            `<ol>${gameItems.join("")}</ol>`;
    }

    d3.json(geojsonUrl).then(world => {
        const projection = d3.geoNaturalEarth1().fitSize([width, height], world);
        const path = d3.geoPath(projection);

        const regionOf = feature => regionByCountry.get(feature.properties.iso_a2);

        const countries = svg.selectAll("path")
            .data(world.features)
            .join("path")
            .attr("d", path)
            .attr("fill", feature => {
                const region = regionOf(feature);
                return region ? color(region.topConcentration) : noDataFill;
            })
            .attr("stroke", "#fff")
            .attr("stroke-width", 0.5)
            .attr("class", feature => regionOf(feature) ? "country has-data" : "country");

        function setRegionHighlight(region, highlighted) {
            countries
                .filter(feature => regionOf(feature) === region)
                .classed("highlighted", highlighted);
        }

        countries
            .on("mouseover", (event, feature) => {
                const region = regionOf(feature);
                if (!region) return;
                setRegionHighlight(region, true);
                showRegionInPanel(region);
            })
            .on("mouseout", (event, feature) => {
                const region = regionOf(feature);
                if (region) setRegionHighlight(region, false);
            })
            .on("click", (event, feature) => {
                const region = regionOf(feature);
                if (region) showRegionInPanel(region);
            });

        countries.append("title")
            .text(feature => {
                const region = regionOf(feature);
                return region
                    ? `${feature.properties.name} — ${region.displayName}`
                    : `${feature.properties.name} — no data yet`;
            });
    });
}

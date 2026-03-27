/**
 * Creek Level - Map and gauge visualization
 */
(function () {
    "use strict";

    // -- State --
    let map = null;
    let deckOverlay = null;
    let allSites = [];
    let filteredSites = [];
    let selectedSiteNo = null;
    let currentState = "CA";

    // -- Color constants --
    const COLORS = {
        normal: [59, 130, 246],   // blue
        stable: [59, 130, 246],
        rising: [234, 179, 8],    // yellow
        high: [239, 68, 68],      // red
        falling: [34, 197, 94],   // green
    };

    const TREND_LABELS = {
        normal: "Normal",
        stable: "Normal",
        rising: "Rising",
        high: "High",
        falling: "Falling",
    };

    const TREND_ARROWS = {
        normal: "--",
        stable: "--",
        rising: "^",
        high: "^^",
        falling: "v",
    };

    // -- State centers (approximate) --
    const STATE_CENTERS = {
        AL: [-86.9, 32.8], AK: [-153.4, 64.2], AZ: [-111.1, 34.0],
        AR: [-92.2, 34.7], CA: [-119.4, 37.2], CO: [-105.7, 39.5],
        CT: [-72.7, 41.6], DE: [-75.5, 39.2], FL: [-81.5, 27.6],
        GA: [-83.5, 32.2], HI: [-155.5, 19.9], ID: [-114.7, 44.1],
        IL: [-89.4, 40.6], IN: [-86.1, 40.3], IA: [-93.1, 41.9],
        KS: [-98.5, 38.5], KY: [-84.3, 37.8], LA: [-91.2, 30.9],
        ME: [-69.4, 45.3], MD: [-76.6, 39.0], MA: [-71.5, 42.2],
        MI: [-84.5, 44.3], MN: [-94.7, 46.7], MS: [-89.3, 32.3],
        MO: [-91.8, 38.6], MT: [-110.4, 46.9], NE: [-99.9, 41.5],
        NV: [-116.4, 38.8], NH: [-71.5, 43.2], NJ: [-74.4, 40.1],
        NM: [-105.9, 34.5], NY: [-75.0, 43.0], NC: [-79.0, 35.8],
        ND: [-101.0, 47.5], OH: [-82.8, 40.4], OK: [-97.0, 35.0],
        OR: [-120.6, 43.8], PA: [-77.2, 41.2], RI: [-71.5, 41.7],
        SC: [-81.2, 34.0], SD: [-99.9, 43.9], TN: [-86.0, 35.5],
        TX: [-99.9, 31.0], UT: [-111.1, 39.3], VT: [-72.6, 44.6],
        VA: [-78.7, 37.4], WA: [-120.7, 47.7], WV: [-80.5, 38.6],
        WI: [-89.6, 43.8], WY: [-107.3, 43.1],
    };

    // -- DOM refs --
    const stateSelect = document.getElementById("state-select");
    const searchInput = document.getElementById("search-input");
    const stationCount = document.getElementById("station-count");
    const mapLoading = document.getElementById("map-loading");
    const sidebarContent = document.getElementById("sidebar-content");
    const siteDetail = document.getElementById("site-detail");
    const detailBack = document.getElementById("detail-back");
    const detailTitle = document.getElementById("detail-title");
    const detailCharts = document.getElementById("detail-charts");

    // -- Init --
    function init() {
        mapboxgl.accessToken = window.MAPBOX_TOKEN;
        map = new mapboxgl.Map({
            container: "map",
            style: "mapbox://styles/mapbox/dark-v11",
            center: STATE_CENTERS.CA || [-119.4, 37.2],
            zoom: 6,
            attributionControl: false,
        });
        map.addControl(new mapboxgl.NavigationControl(), "top-right");
        map.addControl(new mapboxgl.AttributionControl({ compact: true }), "bottom-right");

        map.on("load", () => {
            initDeckOverlay();
            loadSites(currentState);
        });

        stateSelect.addEventListener("change", (e) => {
            currentState = e.target.value;
            loadSites(currentState);
        });

        searchInput.addEventListener("input", () => {
            filterSites(searchInput.value);
        });

        detailBack.addEventListener("click", () => {
            closeSiteDetail();
        });
    }

    // -- Deck.gl overlay --
    function initDeckOverlay() {
        deckOverlay = new deck.MapboxOverlay({
            interleaved: true,
            layers: [],
        });
        map.addControl(deckOverlay);
    }

    function updateDeckLayer(sites) {
        if (!deckOverlay) return;

        const scatterLayer = new deck.ScatterplotLayer({
            id: "gauges",
            data: sites,
            getPosition: d => [d.lng, d.lat],
            getRadius: d => {
                if (d.trend === "high") return 800;
                if (d.trend === "rising") return 600;
                return 400;
            },
            getFillColor: d => {
                const c = COLORS[d.trend] || COLORS.normal;
                return [...c, 200];
            },
            getLineColor: d => {
                const c = COLORS[d.trend] || COLORS.normal;
                return [...c, 255];
            },
            lineWidthMinPixels: 1,
            stroked: true,
            radiusMinPixels: 4,
            radiusMaxPixels: 20,
            pickable: true,
            onClick: (info) => {
                if (info.object) {
                    openSiteDetail(info.object);
                }
            },
            onHover: (info) => {
                if (info.object) {
                    showPopup(info.object);
                } else {
                    hidePopup();
                }
            },
            updateTriggers: {
                getFillColor: sites.map(s => s.trend),
                getRadius: sites.map(s => s.trend),
            },
        });

        deckOverlay.setProps({ layers: [scatterLayer] });
    }

    // -- Popup --
    let popup = null;

    function showPopup(site) {
        if (popup) popup.remove();
        const trendClass = `trend-${site.trend || "stable"}`;
        const trendLabel = TREND_LABELS[site.trend] || "Normal";
        const arrow = TREND_ARROWS[site.trend] || "--";
        const val = site.latest_value != null ? site.latest_value.toFixed(2) : "--";

        popup = new mapboxgl.Popup({
            closeButton: false,
            closeOnClick: false,
            offset: 12,
        })
            .setLngLat([site.lng, site.lat])
            .setHTML(`
                <div class="popup-title">${escapeHtml(site.name)}</div>
                <div class="popup-value">${val}<span class="popup-unit">${site.unit || "ft"}</span></div>
                <div class="popup-trend ${trendClass}">${arrow} ${trendLabel}</div>
                <div class="popup-site-id">${site.site_no}</div>
            `)
            .addTo(map);
    }

    function hidePopup() {
        if (popup) {
            popup.remove();
            popup = null;
        }
    }

    // -- Load sites from API --
    async function loadSites(state) {
        mapLoading.classList.remove("hidden");
        sidebarContent.innerHTML = '<div class="sidebar-empty">Loading gauges...</div>';
        stationCount.textContent = "--";
        searchInput.value = "";

        try {
            const resp = await fetch(`/api/sites?state=${state}`);
            if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
            const data = await resp.json();

            allSites = data.sites || [];
            filteredSites = allSites;

            stationCount.textContent = allSites.length;
            updateDeckLayer(allSites);
            renderSidebar(allSites);

            // Fly to state
            const center = STATE_CENTERS[state];
            if (center) {
                map.flyTo({ center, zoom: 6, duration: 1200 });
            }

            // Load sparklines for visible sites
            loadSparklines(allSites.slice(0, 30));
        } catch (err) {
            console.error("Failed to load sites:", err);
            sidebarContent.innerHTML = `<div class="sidebar-empty">Error loading gauges: ${escapeHtml(err.message)}</div>`;
        } finally {
            mapLoading.classList.add("hidden");
        }
    }

    // -- Filter --
    function filterSites(query) {
        const q = query.toLowerCase().trim();
        if (!q) {
            filteredSites = allSites;
        } else {
            filteredSites = allSites.filter(s =>
                s.name.toLowerCase().includes(q) || s.site_no.includes(q)
            );
        }
        stationCount.textContent = filteredSites.length;
        updateDeckLayer(filteredSites);
        renderSidebar(filteredSites);
    }

    // -- Sidebar rendering --
    function renderSidebar(sites) {
        if (sites.length === 0) {
            sidebarContent.innerHTML = '<div class="sidebar-empty">No gauges found</div>';
            return;
        }

        // Sort: high first, then rising, then by name
        const order = { high: 0, rising: 1, falling: 2, stable: 3, normal: 3 };
        const sorted = [...sites].sort((a, b) => {
            const oa = order[a.trend] ?? 3;
            const ob = order[b.trend] ?? 3;
            if (oa !== ob) return oa - ob;
            return a.name.localeCompare(b.name);
        });

        // Only render first 100 for performance
        const toRender = sorted.slice(0, 100);

        sidebarContent.innerHTML = toRender.map(s => {
            const trendClass = `trend-${s.trend || "stable"}`;
            const trendLabel = TREND_LABELS[s.trend] || "Normal";
            const val = s.latest_value != null ? s.latest_value.toFixed(2) : "--";
            const active = s.site_no === selectedSiteNo ? " active" : "";

            return `
                <div class="gauge-item${active}" data-site="${s.site_no}">
                    <div class="gauge-item-header">
                        <span class="gauge-name">${escapeHtml(truncate(s.name, 50))}</span>
                        <span class="gauge-value ${trendClass}">${val} ft</span>
                    </div>
                    <div class="gauge-meta">
                        <span class="gauge-trend ${trendClass}">${trendLabel}</span>
                        <span>${s.site_no}</span>
                    </div>
                    <div class="gauge-sparkline" id="spark-${s.site_no}"></div>
                </div>
            `;
        }).join("");

        // Click handlers
        sidebarContent.querySelectorAll(".gauge-item").forEach(el => {
            el.addEventListener("click", () => {
                const siteNo = el.dataset.site;
                const site = allSites.find(s => s.site_no === siteNo);
                if (site) openSiteDetail(site);
            });
        });
    }

    // -- Sparklines (D3) --
    async function loadSparklines(sites) {
        // Load history for each site and draw sparklines
        // Batch in groups to avoid hammering the API
        const batch = sites.slice(0, 20);

        for (const site of batch) {
            try {
                const resp = await fetch(`/api/site/${site.site_no}?period=P1D`);
                if (!resp.ok) continue;
                const data = await resp.json();
                const series = data.series?.["00065"];
                if (series?.values?.length > 0) {
                    drawSparkline(`spark-${site.site_no}`, series.values);
                }
            } catch {
                // Skip failed sparklines
            }
        }
    }

    function drawSparkline(containerId, values) {
        const container = document.getElementById(containerId);
        if (!container || values.length < 2) return;

        const w = container.clientWidth || 280;
        const h = 32;
        const margin = { top: 2, right: 2, bottom: 2, left: 2 };

        const nums = values.map(v => v.value);
        const x = d3.scaleLinear().domain([0, values.length - 1]).range([margin.left, w - margin.right]);
        const y = d3.scaleLinear()
            .domain([d3.min(nums) * 0.95, d3.max(nums) * 1.05])
            .range([h - margin.bottom, margin.top]);

        const line = d3.line()
            .x((d, i) => x(i))
            .y(d => y(d.value))
            .curve(d3.curveMonotoneX);

        const area = d3.area()
            .x((d, i) => x(i))
            .y0(h - margin.bottom)
            .y1(d => y(d.value))
            .curve(d3.curveMonotoneX);

        const svg = d3.select(`#${containerId}`)
            .append("svg")
            .attr("width", w)
            .attr("height", h)
            .attr("class", "gauge-sparkline");

        svg.append("path")
            .datum(values)
            .attr("class", "sparkline-area")
            .attr("d", area);

        svg.append("path")
            .datum(values)
            .attr("class", "sparkline-line")
            .attr("d", line);
    }

    // -- Site detail --
    async function openSiteDetail(site) {
        selectedSiteNo = site.site_no;
        detailTitle.textContent = site.name;
        detailCharts.innerHTML = '<div class="sidebar-empty">Loading history...</div>';
        siteDetail.style.display = "flex";

        // Fly to site on map
        map.flyTo({ center: [site.lng, site.lat], zoom: 12, duration: 1000 });

        try {
            const resp = await fetch(`/api/site/${site.site_no}?period=P1D`);
            if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
            const data = await resp.json();

            detailCharts.innerHTML = "";

            for (const [paramCd, series] of Object.entries(data.series || {})) {
                if (!series.values || series.values.length === 0) continue;

                const latest = series.values[series.values.length - 1];
                const panel = document.createElement("div");
                panel.className = "detail-chart-panel";
                panel.innerHTML = `
                    <div class="detail-chart-title">${escapeHtml(series.name)}</div>
                    <div class="detail-chart-value">${latest.value.toFixed(2)} <span style="font-size: 0.75rem; color: var(--text-muted);">${escapeHtml(series.unit)}</span></div>
                    <div class="detail-chart-svg" id="detail-chart-${paramCd}"></div>
                `;
                detailCharts.appendChild(panel);

                drawDetailChart(`detail-chart-${paramCd}`, series.values, series.unit);
            }

            if (detailCharts.children.length === 0) {
                detailCharts.innerHTML = '<div class="sidebar-empty">No data available for this site</div>';
            }
        } catch (err) {
            detailCharts.innerHTML = `<div class="sidebar-empty">Error: ${escapeHtml(err.message)}</div>`;
        }
    }

    function closeSiteDetail() {
        selectedSiteNo = null;
        siteDetail.style.display = "none";
    }

    function drawDetailChart(containerId, values, unit) {
        const container = document.getElementById(containerId);
        if (!container || values.length < 2) return;

        const w = container.clientWidth || 300;
        const h = 100;
        const margin = { top: 8, right: 8, bottom: 24, left: 40 };

        const parseTime = d => new Date(d.time);
        const nums = values.map(v => v.value);

        const x = d3.scaleTime()
            .domain(d3.extent(values, parseTime))
            .range([margin.left, w - margin.right]);

        const y = d3.scaleLinear()
            .domain([d3.min(nums) * 0.95, d3.max(nums) * 1.05])
            .range([h - margin.bottom, margin.top]);

        const line = d3.line()
            .x(d => x(parseTime(d)))
            .y(d => y(d.value))
            .curve(d3.curveMonotoneX);

        const area = d3.area()
            .x(d => x(parseTime(d)))
            .y0(h - margin.bottom)
            .y1(d => y(d.value))
            .curve(d3.curveMonotoneX);

        const svg = d3.select(`#${containerId}`)
            .append("svg")
            .attr("width", w)
            .attr("height", h)
            .attr("class", "detail-chart-svg");

        // Area
        svg.append("path")
            .datum(values)
            .attr("class", "chart-area")
            .attr("d", area);

        // Line
        svg.append("path")
            .datum(values)
            .attr("class", "chart-line")
            .attr("d", line);

        // X axis
        svg.append("g")
            .attr("class", "chart-axis")
            .attr("transform", `translate(0,${h - margin.bottom})`)
            .call(d3.axisBottom(x).ticks(5).tickFormat(d3.timeFormat("%H:%M")));

        // Y axis
        svg.append("g")
            .attr("class", "chart-axis")
            .attr("transform", `translate(${margin.left},0)`)
            .call(d3.axisLeft(y).ticks(4).tickFormat(d => d.toFixed(1)));
    }

    // -- Helpers --
    function escapeHtml(str) {
        if (!str) return "";
        const div = document.createElement("div");
        div.textContent = str;
        return div.innerHTML;
    }

    function truncate(str, len) {
        if (!str) return "";
        return str.length > len ? str.slice(0, len) + "..." : str;
    }

    // -- Start --
    init();
})();

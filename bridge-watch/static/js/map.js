/* Bridge Watch -- deck.gl ScatterplotLayer on Mapbox GL */

(function () {
    "use strict";

    const COLORS = {
        good: [34, 197, 94],
        fair: [234, 179, 8],
        poor: [239, 68, 68],
        unknown: [100, 116, 139],
    };

    // State approximate centers for camera fly-to
    const STATE_CENTERS = {
        "01": [-86.8, 32.8], "02": [-153.5, 64.2], "04": [-111.9, 34.2],
        "05": [-92.4, 34.8], "06": [-119.4, 37.2], "08": [-105.5, 39.0],
        "09": [-72.7, 41.6], "10": [-75.5, 39.0], "11": [-77.0, 38.9],
        "12": [-81.7, 28.6], "13": [-83.5, 32.7], "15": [-155.5, 19.9],
        "16": [-114.7, 44.1], "17": [-89.4, 40.0], "18": [-86.3, 39.8],
        "19": [-93.5, 42.0], "20": [-98.3, 38.5], "21": [-84.3, 37.8],
        "22": [-91.9, 30.5], "23": [-69.4, 45.3], "24": [-76.6, 39.0],
        "25": [-71.8, 42.2], "26": [-84.5, 44.3], "27": [-94.3, 46.3],
        "28": [-89.7, 32.7], "29": [-92.5, 38.4], "30": [-109.6, 47.0],
        "31": [-99.8, 41.5], "32": [-116.6, 38.8], "33": [-71.6, 43.2],
        "34": [-74.4, 40.1], "35": [-106.0, 34.5], "36": [-75.5, 43.0],
        "37": [-79.4, 35.5], "38": [-100.5, 47.5], "39": [-82.8, 40.4],
        "40": [-97.5, 35.5], "41": [-120.6, 44.0], "42": [-77.2, 41.2],
        "44": [-71.5, 41.7], "45": [-80.9, 33.8], "46": [-100.2, 44.4],
        "47": [-86.6, 35.9], "48": [-99.3, 31.5], "49": [-111.9, 39.3],
        "50": [-72.6, 44.0], "51": [-79.4, 37.5], "53": [-120.7, 47.4],
        "54": [-80.6, 38.6], "55": [-89.6, 44.5], "56": [-107.6, 43.0],
    };

    let map;
    let deckOverlay;
    let bridgeData = [];

    // ---- DOM refs ----
    const stateSelect = document.getElementById("state-select");
    const loading = document.getElementById("loading");
    const tooltip = document.getElementById("tooltip");

    // Stats
    const statTotal = document.getElementById("stat-total");
    const statGood = document.getElementById("stat-good");
    const statFair = document.getElementById("stat-fair");
    const statPoor = document.getElementById("stat-poor");
    const barGood = document.getElementById("bar-good");
    const barFair = document.getElementById("bar-fair");
    const barPoor = document.getElementById("bar-poor");

    // Tooltip fields
    const tipName = document.getElementById("tip-name");
    const tipCondition = document.getElementById("tip-condition");
    const tipYear = document.getElementById("tip-year");
    const tipAdt = document.getElementById("tip-adt");
    const tipDeck = document.getElementById("tip-deck");
    const tipSuper = document.getElementById("tip-super");
    const tipSub = document.getElementById("tip-sub");

    // ---- Initialize Mapbox ----
    mapboxgl.accessToken = window.MAPBOX_TOKEN;

    map = new mapboxgl.Map({
        container: "map",
        style: "mapbox://styles/mapbox/dark-v11",
        center: [-119.4, 37.2],
        zoom: 6,
        antialias: true,
    });

    map.addControl(new mapboxgl.NavigationControl(), "bottom-right");

    // ---- deck.gl overlay ----
    function buildDeckLayer() {
        // Compute max ADT for radius scaling
        const maxAdt = Math.max(1, ...bridgeData.map(b => b.adt || 1));

        return new deck.ScatterplotLayer({
            id: "bridges",
            data: bridgeData,
            getPosition: d => [d.lng, d.lat],
            getRadius: d => {
                const adt = d.adt || 1;
                // Scale radius: min 40m, max 800m based on traffic
                return 40 + 760 * Math.sqrt(adt / maxAdt);
            },
            getFillColor: d => COLORS[d.condition] || COLORS.unknown,
            opacity: 0.7,
            pickable: true,
            radiusMinPixels: 2,
            radiusMaxPixels: 20,
            onHover: onHover,
            onClick: onClick,
        });
    }

    function updateDeck() {
        const layer = buildDeckLayer();
        if (deckOverlay) {
            deckOverlay.setProps({ layers: [layer] });
        } else {
            deckOverlay = new deck.MapboxOverlay({
                layers: [layer],
                getTooltip: null,
            });
            map.addControl(deckOverlay);
        }
    }

    // ---- Tooltip ----
    function onHover(info) {
        if (!info.object) {
            tooltip.classList.remove("visible");
            return;
        }
        showTooltip(info.object, info.x, info.y);
    }

    function onClick(info) {
        if (!info.object) {
            tooltip.classList.remove("visible");
            return;
        }
        showTooltip(info.object, info.x, info.y);
    }

    function ratingLabel(val) {
        if (val == null) return "N/A";
        return String(val);
    }

    function showTooltip(bridge, x, y) {
        tipName.textContent = bridge.name || "Unknown";
        tipCondition.textContent = bridge.condition;
        tipCondition.className = "condition-badge " + bridge.condition;
        tipYear.textContent = bridge.year_built || "N/A";
        tipAdt.textContent = bridge.adt != null ? bridge.adt.toLocaleString() : "N/A";
        tipDeck.textContent = ratingLabel(bridge.deck);
        tipSuper.textContent = ratingLabel(bridge.superstructure);
        tipSub.textContent = ratingLabel(bridge.substructure);

        // Position tooltip, keeping it on screen
        const pad = 16;
        let left = x + pad;
        let top = y + pad;
        const rect = tooltip.getBoundingClientRect();
        if (left + 260 > window.innerWidth) left = x - 260 - pad;
        if (top + 200 > window.innerHeight) top = y - 200 - pad;

        tooltip.style.left = left + "px";
        tooltip.style.top = top + "px";
        tooltip.classList.add("visible");
    }

    // ---- Stats update ----
    function updateStats(stats) {
        statTotal.textContent = stats.total.toLocaleString();
        statGood.textContent = stats.good.toLocaleString() + " (" + stats.pct_good + "%)";
        statFair.textContent = stats.fair.toLocaleString() + " (" + stats.pct_fair + "%)";
        statPoor.textContent = stats.poor.toLocaleString() + " (" + stats.pct_poor + "%)";

        barGood.style.width = stats.pct_good + "%";
        barFair.style.width = stats.pct_fair + "%";
        barPoor.style.width = stats.pct_poor + "%";
    }

    // ---- Data fetching ----
    async function loadBridges(stateCode) {
        loading.classList.add("active");
        tooltip.classList.remove("visible");

        try {
            const resp = await fetch("/api/bridges?state=" + encodeURIComponent(stateCode));
            if (!resp.ok) throw new Error("API returned " + resp.status);
            const data = await resp.json();

            bridgeData = data.bridges || [];
            updateStats(data.stats);
            updateDeck();

            // Fly to state center
            const center = STATE_CENTERS[stateCode];
            if (center) {
                map.flyTo({ center: center, zoom: 6, duration: 1200 });
            }
        } catch (err) {
            console.error("Failed to load bridges:", err);
            bridgeData = [];
            updateStats({ total: 0, good: 0, fair: 0, poor: 0, pct_good: 0, pct_fair: 0, pct_poor: 0 });
        } finally {
            loading.classList.remove("active");
        }
    }

    // ---- Events ----
    stateSelect.addEventListener("change", function () {
        loadBridges(this.value);
    });

    map.on("load", function () {
        loadBridges(stateSelect.value);
    });
})();

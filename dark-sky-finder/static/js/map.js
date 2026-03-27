/* Dark Sky Finder - Map & UI logic */

(function () {
    "use strict";

    const MAPBOX_TOKEN = window.__MAPBOX_TOKEN || "";

    // --- Moon phase calculation ---
    // Reference new moon: Jan 6, 2000 18:14 UTC
    const KNOWN_NEW_MOON = new Date(Date.UTC(2000, 0, 6, 18, 14, 0));
    const SYNODIC_MONTH = 29.53058770576;

    function getMoonPhase(date) {
        const diffMs = date.getTime() - KNOWN_NEW_MOON.getTime();
        const diffDays = diffMs / (1000 * 60 * 60 * 24);
        const phase = ((diffDays % SYNODIC_MONTH) + SYNODIC_MONTH) % SYNODIC_MONTH;
        const fraction = phase / SYNODIC_MONTH; // 0..1

        let name, quality, qualityClass, illumination;
        if (fraction < 0.0338) {
            name = "New Moon";
            quality = "Excellent";
            qualityClass = "excellent";
            illumination = 0;
        } else if (fraction < 0.216) {
            name = "Waxing Crescent";
            quality = "Good";
            qualityClass = "good";
            illumination = Math.round(fraction * 100);
        } else if (fraction < 0.284) {
            name = "First Quarter";
            quality = "Fair";
            qualityClass = "fair";
            illumination = 50;
        } else if (fraction < 0.466) {
            name = "Waxing Gibbous";
            quality = "Poor";
            qualityClass = "poor";
            illumination = Math.round(fraction * 100 + 20);
        } else if (fraction < 0.534) {
            name = "Full Moon";
            quality = "Poor";
            qualityClass = "poor";
            illumination = 100;
        } else if (fraction < 0.716) {
            name = "Waning Gibbous";
            quality = "Poor";
            qualityClass = "poor";
            illumination = Math.round((1 - fraction) * 100 + 20);
        } else if (fraction < 0.784) {
            name = "Last Quarter";
            quality = "Fair";
            qualityClass = "fair";
            illumination = 50;
        } else if (fraction < 0.966) {
            name = "Waning Crescent";
            quality = "Good";
            qualityClass = "good";
            illumination = Math.round((1 - fraction) * 100);
        } else {
            name = "New Moon";
            quality = "Excellent";
            qualityClass = "excellent";
            illumination = 0;
        }

        return { name, quality, qualityClass, illumination, fraction };
    }

    function drawMoonSVG(fraction) {
        // Draw a moon phase SVG: circle with shadow overlay
        const size = 64;
        const r = 28;
        const cx = size / 2;
        const cy = size / 2;

        // illumination side based on phase
        // fraction 0 = new (dark), 0.5 = full (bright)
        const illuminated = fraction <= 0.5 ? fraction * 2 : (1 - fraction) * 2;
        // which side is lit
        const waxing = fraction <= 0.5;

        // Compute the terminator curve using an ellipse approach
        const terminatorX = r * (1 - 2 * illuminated);

        let d;
        if (waxing) {
            // Right side is lit
            d = `M ${cx} ${cy - r} A ${r} ${r} 0 0 1 ${cx} ${cy + r} A ${Math.abs(terminatorX)} ${r} 0 0 ${illuminated < 0.5 ? 1 : 0} ${cx} ${cy - r} Z`;
        } else {
            // Left side is lit
            d = `M ${cx} ${cy - r} A ${r} ${r} 0 0 0 ${cx} ${cy + r} A ${Math.abs(terminatorX)} ${r} 0 0 ${illuminated < 0.5 ? 0 : 1} ${cx} ${cy - r} Z`;
        }

        return `<svg width="${size}" height="${size}" viewBox="0 0 ${size} ${size}" xmlns="http://www.w3.org/2000/svg">
            <circle cx="${cx}" cy="${cy}" r="${r}" fill="#e2e8f0" />
            <path d="${d}" fill="#0f172a" opacity="0.9" />
            <circle cx="${cx}" cy="${cy}" r="${r}" fill="none" stroke="#475569" stroke-width="1" />
        </svg>`;
    }

    // --- State ---
    let map = null;
    let deckOverlay = null;
    let allDarkSky = [];
    let allCities = [];
    let userLat = 39.8;
    let userLng = -98.5;
    let nearestSpots = [];

    // --- Init ---
    async function init() {
        renderMoonPhase();
        await loadLocations();
        initMap();
        await findNearest(userLat, userLng);
    }

    function renderMoonPhase() {
        const now = new Date();
        const moon = getMoonPhase(now);
        const moonVisual = document.getElementById("moon-visual");
        const moonName = document.getElementById("moon-name");
        const moonIllum = document.getElementById("moon-illumination");
        const moonQuality = document.getElementById("moon-quality");

        if (moonVisual) moonVisual.innerHTML = drawMoonSVG(moon.fraction);
        if (moonName) moonName.textContent = moon.name;
        if (moonIllum) moonIllum.textContent = `${moon.illumination}% illuminated`;
        if (moonQuality) {
            moonQuality.textContent = `${moon.quality} for stargazing`;
            moonQuality.className = `moon-quality ${moon.qualityClass}`;
        }
    }

    async function loadLocations() {
        try {
            const resp = await fetch("/api/locations");
            const data = await resp.json();
            allDarkSky = data.dark_sky || [];
            allCities = data.cities || [];
        } catch (e) {
            console.error("Failed to load locations:", e);
        }
    }

    function initMap() {
        mapboxgl.accessToken = MAPBOX_TOKEN;
        map = new mapboxgl.Map({
            container: "map",
            style: "mapbox://styles/mapbox/dark-v11",
            center: [userLng, userLat],
            zoom: 4,
        });

        map.addControl(new mapboxgl.NavigationControl(), "bottom-right");

        map.on("load", () => {
            renderDeckLayers();
            loadCloudGrid();
        });
    }

    function bortleToColor(bortle) {
        if (bortle <= 1) return [34, 197, 94, 220];     // green
        if (bortle <= 2) return [74, 222, 128, 200];     // light green
        if (bortle <= 3) return [163, 230, 53, 180];     // lime
        if (bortle <= 4) return [250, 204, 21, 160];     // yellow
        if (bortle <= 6) return [251, 146, 60, 140];     // orange
        if (bortle <= 7) return [239, 68, 68, 120];      // red
        return [239, 68, 68, 100];                       // dark red
    }

    function bortleToRadius(bortle) {
        if (bortle <= 1) return 12000;
        if (bortle <= 2) return 10000;
        if (bortle <= 3) return 8000;
        return 6000;
    }

    function renderDeckLayers() {
        if (deckOverlay) {
            map.removeControl(deckOverlay);
        }

        const darkSkyLayer = new deck.ScatterplotLayer({
            id: "dark-sky-spots",
            data: allDarkSky,
            getPosition: d => [d.lng, d.lat],
            getFillColor: d => bortleToColor(d.bortle_class),
            getRadius: d => bortleToRadius(d.bortle_class),
            radiusMinPixels: 4,
            radiusMaxPixels: 20,
            pickable: true,
            onClick: ({object}) => {
                if (object) {
                    flyToSpot(object);
                    findNearest(object.lat, object.lng);
                }
            },
        });

        const cityLayer = new deck.ScatterplotLayer({
            id: "bright-cities",
            data: allCities,
            getPosition: d => [d.lng, d.lat],
            getFillColor: [239, 68, 68, 80],
            getRadius: 25000,
            radiusMinPixels: 6,
            radiusMaxPixels: 30,
            pickable: true,
        });

        deckOverlay = new deck.MapboxOverlay({
            layers: [cityLayer, darkSkyLayer],
            getTooltip: ({object}) => {
                if (!object) return null;
                const bortle = object.bortle_class;
                const type = object.type === "park" ? "Dark Sky Site" : "City";
                return {
                    html: `<b>${object.name}, ${object.state}</b><br/>Bortle Class: ${bortle}<br/>${type}`,
                    style: {
                        backgroundColor: "rgba(15,23,42,0.9)",
                        color: "#f1f5f9",
                        fontSize: "13px",
                        padding: "8px 12px",
                        borderRadius: "6px",
                        border: "1px solid #475569",
                    },
                };
            },
        });

        map.addControl(deckOverlay);
    }

    function flyToSpot(spot) {
        map.flyTo({ center: [spot.lng, spot.lat], zoom: 8, duration: 1500 });
    }

    async function findNearest(lat, lng) {
        const panel = document.getElementById("nearest-spots");
        if (!panel) return;
        panel.innerHTML = `<div class="loading-indicator"><div class="spinner"></div> Finding nearest spots...</div>`;

        try {
            const resp = await fetch(`/api/nearest?lat=${lat}&lng=${lng}&limit=5`);
            const data = await resp.json();
            nearestSpots = data.results || [];
            renderNearestSpots();
            // Also fetch cloud cover for the search location
            fetchCloudForecast(lat, lng);
        } catch (e) {
            panel.innerHTML = `<p style="color:var(--text-muted)">Failed to load spots.</p>`;
        }
    }

    function renderNearestSpots() {
        const panel = document.getElementById("nearest-spots");
        if (!panel) return;
        if (nearestSpots.length === 0) {
            panel.innerHTML = `<p style="color:var(--text-muted)">No spots found.</p>`;
            return;
        }

        panel.innerHTML = nearestSpots.map(s => `
            <div class="spot-card" data-lat="${s.lat}" data-lng="${s.lng}">
                <div class="spot-card-header">
                    <h4>${s.name}</h4>
                    <span class="spot-distance">${s.distance_miles} mi</span>
                </div>
                <div class="spot-meta">
                    <span class="bortle-badge bortle-${s.bortle_class}">Bortle ${s.bortle_class}</span>
                    <span>${s.state}</span>
                </div>
            </div>
        `).join("");

        panel.querySelectorAll(".spot-card").forEach(card => {
            card.addEventListener("click", () => {
                const lat = parseFloat(card.dataset.lat);
                const lng = parseFloat(card.dataset.lng);
                flyToSpot({ lat, lng });
                fetchCloudForecast(lat, lng);
            });
        });
    }

    async function fetchCloudForecast(lat, lng) {
        const container = document.getElementById("cloud-forecast");
        if (!container) return;
        container.innerHTML = `<div class="loading-indicator"><div class="spinner"></div> Loading forecast...</div>`;

        try {
            const resp = await fetch(`/api/cloud-cover?lat=${lat}&lng=${lng}`);
            const data = await resp.json();
            renderCloudForecast(data.hours || []);
        } catch (e) {
            container.innerHTML = `<p style="color:var(--text-muted)">Failed to load forecast.</p>`;
        }
    }

    function renderCloudForecast(hours) {
        const container = document.getElementById("cloud-forecast");
        if (!container) return;

        // Show evening/night hours (18:00 - 05:00)
        const nightHours = hours.filter(h => {
            const hour = parseInt(h.time.split("T")[1].split(":")[0], 10);
            return hour >= 18 || hour <= 5;
        });

        const display = nightHours.length > 0 ? nightHours : hours.slice(0, 12);

        container.innerHTML = display.map(h => {
            const time = h.time.split("T")[1].substring(0, 5);
            const cover = h.cloud_cover;
            const color = cover < 25 ? "#22c55e" : cover < 50 ? "#a3e635" : cover < 75 ? "#f59e0b" : "#ef4444";
            return `
                <div class="cloud-hour">
                    <span class="time-label">${time}</span>
                    <div class="cloud-bar-track">
                        <div class="cloud-bar-fill" style="width:${cover}%;background:${color}"></div>
                    </div>
                    <span class="cloud-pct">${cover}%</span>
                </div>
            `;
        }).join("");
    }

    async function loadCloudGrid() {
        // Fetch cloud cover grid for the CONUS and render as a heatmap-like overlay
        try {
            const resp = await fetch("/api/cloud-grid?step=3");
            const data = await resp.json();
            const grid = data.grid || [];
            if (grid.length === 0) return;

            const cloudLayer = new deck.ScatterplotLayer({
                id: "cloud-cover-grid",
                data: grid,
                getPosition: d => [d.lng, d.lat],
                getFillColor: d => {
                    const c = d.cloud_cover;
                    if (c < 25) return [34, 197, 94, 30];
                    if (c < 50) return [163, 230, 53, 40];
                    if (c < 75) return [245, 158, 11, 50];
                    return [239, 68, 68, 60];
                },
                getRadius: 80000,
                radiusMinPixels: 15,
                radiusMaxPixels: 80,
                pickable: false,
            });

            // Re-render all layers with cloud grid underneath
            const darkSkyLayer = new deck.ScatterplotLayer({
                id: "dark-sky-spots",
                data: allDarkSky,
                getPosition: d => [d.lng, d.lat],
                getFillColor: d => bortleToColor(d.bortle_class),
                getRadius: d => bortleToRadius(d.bortle_class),
                radiusMinPixels: 4,
                radiusMaxPixels: 20,
                pickable: true,
                onClick: ({object}) => {
                    if (object) {
                        flyToSpot(object);
                        findNearest(object.lat, object.lng);
                    }
                },
            });

            const cityLayer = new deck.ScatterplotLayer({
                id: "bright-cities",
                data: allCities,
                getPosition: d => [d.lng, d.lat],
                getFillColor: [239, 68, 68, 80],
                getRadius: 25000,
                radiusMinPixels: 6,
                radiusMaxPixels: 30,
                pickable: true,
            });

            if (deckOverlay) map.removeControl(deckOverlay);
            deckOverlay = new deck.MapboxOverlay({
                layers: [cloudLayer, cityLayer, darkSkyLayer],
                getTooltip: ({object}) => {
                    if (!object) return null;
                    if (object.bortle_class !== undefined) {
                        const type = object.type === "park" ? "Dark Sky Site" : "City";
                        return {
                            html: `<b>${object.name}, ${object.state}</b><br/>Bortle Class: ${object.bortle_class}<br/>${type}`,
                            style: {
                                backgroundColor: "rgba(15,23,42,0.9)",
                                color: "#f1f5f9",
                                fontSize: "13px",
                                padding: "8px 12px",
                                borderRadius: "6px",
                                border: "1px solid #475569",
                            },
                        };
                    }
                    return null;
                },
            });
            map.addControl(deckOverlay);
        } catch (e) {
            console.error("Failed to load cloud grid:", e);
        }
    }

    // --- Search ---
    function initSearch() {
        const input = document.getElementById("search-input");
        if (!input) return;

        input.addEventListener("keydown", async (e) => {
            if (e.key !== "Enter") return;
            const query = input.value.trim();
            if (!query) return;

            // Try Mapbox geocoding
            try {
                const resp = await fetch(
                    `https://api.mapbox.com/geocoding/v5/mapbox.places/${encodeURIComponent(query)}.json?access_token=${MAPBOX_TOKEN}&country=us&limit=1`
                );
                const data = await resp.json();
                if (data.features && data.features.length > 0) {
                    const [lng, lat] = data.features[0].center;
                    map.flyTo({ center: [lng, lat], zoom: 6, duration: 1500 });
                    await findNearest(lat, lng);
                }
            } catch (err) {
                console.error("Geocoding failed:", err);
            }
        });
    }

    // --- Boot ---
    document.addEventListener("DOMContentLoaded", () => {
        init();
        initSearch();
    });
})();

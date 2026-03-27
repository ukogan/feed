/**
 * Risk Map: Combined earthquake + wildfire risk visualizer for California.
 * Uses Deck.gl layers on Mapbox GL JS.
 */

// State
let map;
let deckOverlay;
let earthquakeData = [];
let fireData = [];
let alertData = [];
let searchMarker = null;

// Layer visibility
let showQuakes = true;
let showFires = true;
let showAlerts = true;

// DOM refs
const timeSlider = document.getElementById('time-slider');
const timeRangeLabel = document.getElementById('time-range-label');
const statQuakes = document.getElementById('stat-quakes');
const statMaxMag = document.getElementById('stat-max-mag');
const statFires = document.getElementById('stat-fires');
const statAlerts = document.getElementById('stat-alerts');
const loadingEl = document.getElementById('loading');
const addressSearch = document.getElementById('address-search');
const searchBtn = document.getElementById('search-btn');
const alertsPanel = document.getElementById('alerts-panel');
const alertsList = document.getElementById('alerts-list');

// Checkboxes
const layerQuakes = document.getElementById('layer-quakes');
const layerFires = document.getElementById('layer-fires');
const layerAlerts = document.getElementById('layer-alerts');


function magnitudeToRadius(mag) {
    // Scale magnitude to pixel radius: M1 = 3px, M5 = 25px, M7+ = 50px
    return Math.pow(2, mag) * 1.5;
}

function magnitudeToColor(mag) {
    // Yellow (small) -> Orange (medium) -> Red (large)
    if (mag < 2) return [250, 204, 21, 160];    // yellow
    if (mag < 3) return [251, 146, 60, 180];     // orange
    if (mag < 4) return [249, 115, 22, 200];     // dark orange
    if (mag < 5) return [239, 68, 68, 220];      // red
    return [220, 38, 38, 255];                    // dark red
}

function recencyToOpacity(timestamp) {
    const now = Date.now();
    const age = now - timestamp;
    const dayMs = 86400000;
    // Recent quakes are more opaque
    if (age < dayMs) return 255;
    if (age < 7 * dayMs) return 200;
    if (age < 30 * dayMs) return 150;
    return 100;
}

function formatTimeRange(days) {
    if (days <= 7) return `Last ${days} days`;
    if (days <= 30) return `Last ${days} days`;
    if (days <= 90) return `Last ${days} days`;
    return `Last ${days} days`;
}

function updateStats() {
    statQuakes.textContent = earthquakeData.length.toLocaleString();

    const maxMag = earthquakeData.length > 0
        ? Math.max(...earthquakeData.map(q => q.magnitude))
        : 0;
    statMaxMag.textContent = maxMag > 0 ? `M${maxMag.toFixed(1)}` : '--';

    statFires.textContent = fireData.length.toLocaleString();
    statAlerts.textContent = alertData.length.toLocaleString();
}

function renderAlerts() {
    if (alertData.length === 0) {
        alertsPanel.classList.remove('visible');
        return;
    }

    alertsPanel.classList.toggle('visible', showAlerts);

    alertsList.innerHTML = alertData.map(a => `
        <div class="alert-item">
            <div class="alert-event">${escapeHtml(a.event)}</div>
            <div>${escapeHtml(a.headline)}</div>
            ${a.areas ? `<div style="color: var(--text-muted); margin-top: 0.25rem;">${escapeHtml(a.areas)}</div>` : ''}
        </div>
    `).join('');
}

function escapeHtml(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

function buildLayers() {
    const layers = [];

    // Fire perimeters (polygons)
    if (showFires && fireData.length > 0) {
        const polygonData = fireData.filter(f =>
            f.geometry && f.geometry.coordinates && f.geometry.coordinates.length > 0
        );

        // Flatten MultiPolygon and Polygon into individual polygons
        const flatPolygons = [];
        for (const fire of polygonData) {
            const geo = fire.geometry;
            if (geo.type === 'Polygon') {
                flatPolygons.push({
                    ...fire,
                    polygon: geo.coordinates[0],
                });
            } else if (geo.type === 'MultiPolygon') {
                for (const poly of geo.coordinates) {
                    flatPolygons.push({
                        ...fire,
                        polygon: poly[0],
                    });
                }
            }
        }

        layers.push(new deck.PolygonLayer({
            id: 'fire-perimeters',
            data: flatPolygons,
            getPolygon: d => d.polygon,
            getFillColor: [239, 68, 68, 80],
            getLineColor: [239, 68, 68, 200],
            getLineWidth: 2,
            lineWidthMinPixels: 1,
            filled: true,
            stroked: true,
            pickable: true,
        }));
    }

    // Earthquakes (scatterplot)
    if (showQuakes && earthquakeData.length > 0) {
        layers.push(new deck.ScatterplotLayer({
            id: 'earthquakes',
            data: earthquakeData,
            getPosition: d => [d.lng, d.lat],
            getRadius: d => magnitudeToRadius(d.magnitude) * 200,
            getFillColor: d => {
                const color = magnitudeToColor(d.magnitude);
                color[3] = recencyToOpacity(d.time);
                return color;
            },
            radiusMinPixels: 2,
            radiusMaxPixels: 40,
            pickable: true,
            antialiasing: true,
            transitions: {
                getRadius: { duration: 300 },
            },
        }));
    }

    return layers;
}

function updateDeck() {
    if (!deckOverlay) return;
    deckOverlay.setProps({ layers: buildLayers() });
}


// Data fetching
async function fetchEarthquakes(days) {
    try {
        const resp = await fetch(`/api/earthquakes?days=${days}&min_mag=0.5`);
        const data = await resp.json();
        earthquakeData = data.earthquakes || [];
    } catch (err) {
        console.error('Failed to fetch earthquakes:', err);
        earthquakeData = [];
    }
}

async function fetchFires() {
    try {
        const resp = await fetch('/api/fires');
        const data = await resp.json();
        fireData = data.fires || [];
    } catch (err) {
        console.error('Failed to fetch fires:', err);
        fireData = [];
    }
}

async function fetchAlerts() {
    try {
        const resp = await fetch('/api/fire-weather');
        const data = await resp.json();
        alertData = data.alerts || [];
    } catch (err) {
        console.error('Failed to fetch fire weather alerts:', err);
        alertData = [];
    }
}

async function loadAllData() {
    loadingEl.style.display = 'flex';

    const days = parseInt(timeSlider.value);
    await Promise.all([
        fetchEarthquakes(days),
        fetchFires(),
        fetchAlerts(),
    ]);

    updateStats();
    renderAlerts();
    updateDeck();

    loadingEl.style.display = 'none';
}

async function refreshEarthquakes() {
    const days = parseInt(timeSlider.value);
    timeRangeLabel.textContent = formatTimeRange(days);

    await fetchEarthquakes(days);
    updateStats();
    updateDeck();
}


// Address search
async function searchAddress() {
    const query = addressSearch.value.trim();
    if (!query || !MAPBOX_TOKEN) return;

    try {
        const resp = await fetch(
            `https://api.mapbox.com/geocoding/v5/mapbox.places/${encodeURIComponent(query)}.json` +
            `?access_token=${MAPBOX_TOKEN}&bbox=-125,32,-114,42&limit=1`
        );
        const data = await resp.json();

        if (data.features && data.features.length > 0) {
            const [lng, lat] = data.features[0].center;
            const placeName = data.features[0].place_name;

            // Fly to location
            map.flyTo({ center: [lng, lat], zoom: 10 });

            // Add/update marker
            if (searchMarker) searchMarker.remove();
            searchMarker = new mapboxgl.Marker({ color: '#ef4444' })
                .setLngLat([lng, lat])
                .setPopup(new mapboxgl.Popup().setHTML(
                    `<div class="risk-popup-title">${escapeHtml(placeName)}</div>` +
                    `<div class="risk-popup-detail">Analyzing nearby risks...</div>`
                ))
                .addTo(map);
            searchMarker.togglePopup();

            // Analyze local risk
            analyzeLocalRisk(lat, lng, placeName);
        }
    } catch (err) {
        console.error('Geocoding failed:', err);
    }
}

function analyzeLocalRisk(lat, lng, placeName) {
    const radiusKm = 50;
    const radiusDeg = radiusKm / 111;

    // Count nearby earthquakes
    const nearbyQuakes = earthquakeData.filter(q => {
        const dlat = q.lat - lat;
        const dlng = q.lng - lng;
        return Math.sqrt(dlat * dlat + dlng * dlng) < radiusDeg;
    });

    // Count nearby fires
    const nearbyFires = fireData.filter(f => {
        const dlat = f.centroid_lat - lat;
        const dlng = f.centroid_lng - lng;
        return Math.sqrt(dlat * dlat + dlng * dlng) < radiusDeg;
    });

    const maxNearbyMag = nearbyQuakes.length > 0
        ? Math.max(...nearbyQuakes.map(q => q.magnitude))
        : 0;

    // Update popup
    if (searchMarker) {
        const popup = searchMarker.getPopup();
        popup.setHTML(
            `<div class="risk-popup-title">${escapeHtml(placeName)}</div>` +
            `<div class="risk-popup-detail">` +
            `<strong>${nearbyQuakes.length}</strong> earthquakes within ${radiusKm}km<br>` +
            `Max magnitude: <strong>M${maxNearbyMag.toFixed(1)}</strong><br>` +
            `<strong>${nearbyFires.length}</strong> active fire(s) nearby` +
            `</div>`
        );
    }
}


// Map initialization
function initMap() {
    mapboxgl.accessToken = MAPBOX_TOKEN;

    map = new mapboxgl.Map({
        container: 'map',
        style: 'mapbox://styles/mapbox/dark-v11',
        center: [-119.5, 37.0],
        zoom: 5.5,
        pitch: 0,
    });

    map.addControl(new mapboxgl.NavigationControl(), 'bottom-right');

    map.on('load', () => {
        deckOverlay = new deck.MapboxOverlay({
            layers: [],
            getTooltip: ({ object, layer }) => {
                if (!object) return null;

                if (layer && layer.id === 'earthquakes') {
                    const date = new Date(object.time).toLocaleDateString();
                    return {
                        html: `<div style="font-family: var(--font-sans); font-size: 13px;">
                            <strong>M${object.magnitude.toFixed(1)}</strong> - ${escapeHtml(object.place)}<br>
                            <span style="color: #94a3b8;">Depth: ${object.depth.toFixed(1)}km | ${date}</span>
                        </div>`,
                        style: {
                            background: 'rgba(15,23,42,0.9)',
                            color: '#f1f5f9',
                            border: '1px solid #334155',
                            borderRadius: '4px',
                            padding: '6px 10px',
                        }
                    };
                }

                if (layer && layer.id === 'fire-perimeters') {
                    const acres = object.acres ? Math.round(object.acres).toLocaleString() : 'N/A';
                    const containment = object.containment != null ? `${object.containment}%` : 'N/A';
                    return {
                        html: `<div style="font-family: var(--font-sans); font-size: 13px;">
                            <strong style="color: #ef4444;">${escapeHtml(object.name)}</strong><br>
                            <span style="color: #94a3b8;">${acres} acres | ${containment} contained</span>
                        </div>`,
                        style: {
                            background: 'rgba(15,23,42,0.9)',
                            color: '#f1f5f9',
                            border: '1px solid #334155',
                            borderRadius: '4px',
                            padding: '6px 10px',
                        }
                    };
                }

                return null;
            }
        });
        map.addControl(deckOverlay);

        loadAllData();
    });
}


// Event listeners
let sliderTimeout = null;
timeSlider.addEventListener('input', () => {
    timeRangeLabel.textContent = formatTimeRange(parseInt(timeSlider.value));
    clearTimeout(sliderTimeout);
    sliderTimeout = setTimeout(refreshEarthquakes, 300);
});

layerQuakes.addEventListener('change', () => {
    showQuakes = layerQuakes.checked;
    updateDeck();
});

layerFires.addEventListener('change', () => {
    showFires = layerFires.checked;
    updateDeck();
});

layerAlerts.addEventListener('change', () => {
    showAlerts = layerAlerts.checked;
    renderAlerts();
});

searchBtn.addEventListener('click', searchAddress);
addressSearch.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') searchAddress();
});


// Init
if (MAPBOX_TOKEN) {
    initMap();
} else {
    loadingEl.innerHTML = `
        <div class="feed-panel" style="text-align: center; padding: 2rem;">
            <p style="color: var(--text-muted);">Set MAPBOX_TOKEN in .env to load the map</p>
            <p style="color: var(--text-muted); font-size: 0.75rem; margin-top: 0.5rem;">
                Data APIs will still work at /api/earthquakes, /api/fires, /api/fire-weather
            </p>
        </div>
    `;
}

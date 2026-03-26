/**
 * Flight Explorer Map
 * Deck.gl ScatterplotLayer + IconLayer on Mapbox for aircraft visualization.
 */

let map;
let deckOverlay;
let currentLat = null;
let currentLng = null;
let refreshTimer = null;
const REFRESH_INTERVAL = 10000; // 10 seconds

// DOM refs
const addressInput = document.getElementById('address-input');
const searchBtn = document.getElementById('search-btn');
const tailInput = document.getElementById('tail-input');
const tailBtn = document.getElementById('tail-btn');
const aircraftList = document.getElementById('aircraft-list');
const statFlights = document.getElementById('stat-flights');
const statSeats = document.getElementById('stat-seats');
const statTypes = document.getElementById('stat-types');
const statusText = document.getElementById('status-text');
const detailPanel = document.getElementById('detail-panel');
const detailTitle = document.getElementById('detail-title');
const detailGrid = document.getElementById('detail-grid');
const detailClose = document.getElementById('detail-close');


function altitudeColor(alt) {
    // Low (green) to high (blue/purple)
    if (alt < 5000) return [34, 197, 94];
    if (alt < 15000) return [250, 204, 21];
    if (alt < 25000) return [245, 158, 11];
    if (alt < 35000) return [56, 189, 248];
    return [139, 92, 246];
}

function formatAlt(ft) {
    if (!ft || ft === 'ground') return 'GND';
    return `FL${Math.round(ft / 100)}`;
}

function formatSpeed(kts) {
    if (!kts) return '';
    return `${Math.round(kts)} kts`;
}


// ── Map Rendering ──

function updateMap(aircraft) {
    if (!deckOverlay) return;

    const scatterData = aircraft.filter(ac => ac.lat && ac.lng && !ac.on_ground);

    const scatterLayer = new deck.ScatterplotLayer({
        id: 'aircraft-scatter',
        data: scatterData,
        getPosition: d => [d.lng, d.lat],
        getRadius: d => Math.max(3, Math.min(8, (d.altitude_ft || 10000) / 5000)),
        getFillColor: d => altitudeColor(d.altitude_ft || 0),
        radiusUnits: 'pixels',
        radiusMinPixels: 3,
        radiusMaxPixels: 10,
        pickable: true,
        autoHighlight: true,
        highlightColor: [255, 255, 255, 80],
    });

    // User location marker
    const layers = [scatterLayer];

    if (currentLat && currentLng) {
        const userLayer = new deck.ScatterplotLayer({
            id: 'user-location',
            data: [{ lat: currentLat, lng: currentLng }],
            getPosition: d => [d.lng, d.lat],
            getRadius: 8,
            getFillColor: [56, 189, 248],
            getLineColor: [255, 255, 255],
            lineWidthMinPixels: 2,
            stroked: true,
            radiusUnits: 'pixels',
        });
        layers.push(userLayer);

        // Radius circle
        const radiusCircle = new deck.ScatterplotLayer({
            id: 'radius-circle',
            data: [{ lat: currentLat, lng: currentLng }],
            getPosition: d => [d.lng, d.lat],
            getRadius: 10 * 1852, // 10 NM in meters
            getFillColor: [56, 189, 248, 15],
            getLineColor: [56, 189, 248, 60],
            lineWidthMinPixels: 1,
            stroked: true,
            filled: true,
            radiusUnits: 'meters',
        });
        layers.unshift(radiusCircle);
    }

    deckOverlay.setProps({
        layers,
        getTooltip: ({ object }) => {
            if (!object || !object.callsign) return null;
            const lines = [
                object.callsign || object.hex,
                object.type_code ? `Type: ${object.type_code}` : '',
                object.altitude_ft ? `Alt: ${object.altitude_ft.toLocaleString()} ft` : '',
                object.speed_kts ? `Speed: ${Math.round(object.speed_kts)} kts` : '',
                object.tail_number ? `Reg: ${object.tail_number}` : '',
                object.seat_count ? `Seats: ${object.seat_count}` : '',
            ].filter(Boolean);

            return {
                html: `<div style="font-family:var(--font-mono);font-size:12px;line-height:1.5">${lines.join('<br>')}</div>`,
                style: {
                    background: 'rgba(15,23,42,0.95)',
                    color: '#f1f5f9',
                    border: '1px solid #334155',
                    borderRadius: '6px',
                    padding: '6px 10px',
                }
            };
        }
    });
}


// ── Aircraft List ──

function renderAircraftList(aircraft) {
    if (!aircraft || aircraft.length === 0) {
        aircraftList.innerHTML = `
            <div class="empty-state">
                <span>No aircraft detected overhead</span>
            </div>`;
        return;
    }

    aircraftList.innerHTML = aircraft.map(ac => `
        <div class="aircraft-item" data-hex="${ac.hex}" data-reg="${ac.tail_number || ''}">
            <span class="ac-type">${ac.type_code || '??'}</span>
            <div class="ac-info">
                <span class="ac-callsign">${ac.callsign || ac.tail_number || ac.hex}</span>
                <span class="ac-detail">
                    ${ac.description || ac.owner || ''}
                    ${ac.seat_count ? ` / ${ac.seat_count} seats` : ''}
                    ${ac.distance_nm ? ` / ${ac.distance_nm.toFixed(1)} NM` : ''}
                </span>
            </div>
            <span class="ac-alt">${formatAlt(ac.altitude_ft)}<br>${formatSpeed(ac.speed_kts)}</span>
        </div>
    `).join('');
}


// ── Stats ──

function updateStats(summary) {
    statFlights.textContent = summary.total_flights || '--';
    statSeats.textContent = summary.total_seats ? summary.total_seats.toLocaleString() : '--';
    statTypes.textContent = summary.unique_types ? summary.unique_types.length : '--';
}


// ── Search & Data Loading ──

async function searchLocation(query) {
    statusText.textContent = 'Searching...';

    try {
        const response = await fetch(`/api/geocode?address=${encodeURIComponent(query)}`);
        const data = await response.json();

        if (data.error) {
            statusText.textContent = data.error;
            return;
        }

        currentLat = data.lat;
        currentLng = data.lng;

        map.flyTo({ center: [currentLng, currentLat], zoom: 10 });
        loadOverhead();
        startAutoRefresh();
    } catch (err) {
        statusText.textContent = `Error: ${err.message}`;
    }
}

async function loadOverhead() {
    if (!currentLat || !currentLng) return;

    statusText.textContent = 'Scanning...';

    try {
        const response = await fetch(`/api/overhead?lat=${currentLat}&lng=${currentLng}&radius=10`);
        const data = await response.json();

        if (data.error) {
            statusText.textContent = data.error;
            return;
        }

        updateMap(data.aircraft);
        renderAircraftList(data.aircraft);
        updateStats(data.summary);

        const now = new Date().toLocaleTimeString();
        statusText.textContent = `${data.aircraft.length} aircraft / Updated ${now}`;
    } catch (err) {
        statusText.textContent = `Error: ${err.message}`;
    }
}

function startAutoRefresh() {
    if (refreshTimer) clearInterval(refreshTimer);
    refreshTimer = setInterval(loadOverhead, REFRESH_INTERVAL);
}

async function trackAircraft(identifier) {
    statusText.textContent = `Looking up ${identifier}...`;

    try {
        const response = await fetch(`/api/aircraft/${encodeURIComponent(identifier)}`);
        const data = await response.json();

        if (data.error) {
            statusText.textContent = data.error;
            return;
        }

        const ac = data.aircraft[0];
        if (ac && ac.lat && ac.lng) {
            map.flyTo({ center: [ac.lng, ac.lat], zoom: 8 });
            updateMap(data.aircraft);
        }

        showDetail(ac);
        statusText.textContent = `Tracking ${identifier}`;
    } catch (err) {
        statusText.textContent = `Error: ${err.message}`;
    }
}

function showDetail(ac) {
    if (!ac) return;

    detailTitle.textContent = ac.callsign || ac.tail_number || ac.hex;
    detailGrid.innerHTML = [
        ['Registration', ac.tail_number || 'N/A'],
        ['Type', ac.type_code || 'Unknown'],
        ['Description', ac.description || ''],
        ['Owner', ac.owner || ''],
        ['Altitude', ac.alt_baro ? `${ac.alt_baro.toLocaleString()} ft` : 'N/A'],
        ['Speed', ac.ground_speed ? `${Math.round(ac.ground_speed)} kts` : 'N/A'],
        ['Heading', ac.heading ? `${Math.round(ac.heading)}deg` : 'N/A'],
        ['Seats', ac.seat_count || 'Unknown'],
        ['Hex', ac.hex],
    ].filter(([_, v]) => v).map(([label, value]) => `
        <span class="detail-label">${label}</span>
        <span class="detail-value">${value}</span>
    `).join('');

    detailPanel.classList.add('visible');
}


// ── Event Listeners ──

searchBtn.addEventListener('click', () => {
    const q = addressInput.value.trim();
    if (q) searchLocation(q);
});

addressInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
        const q = addressInput.value.trim();
        if (q) searchLocation(q);
    }
});

tailBtn.addEventListener('click', () => {
    const id = tailInput.value.trim();
    if (id) trackAircraft(id);
});

tailInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
        const id = tailInput.value.trim();
        if (id) trackAircraft(id);
    }
});

detailClose.addEventListener('click', () => {
    detailPanel.classList.remove('visible');
});

// Click on aircraft in list
aircraftList.addEventListener('click', (e) => {
    const item = e.target.closest('.aircraft-item');
    if (!item) return;
    const reg = item.dataset.reg;
    const hex = item.dataset.hex;
    if (reg) {
        tailInput.value = reg;
        trackAircraft(reg);
    } else if (hex) {
        trackAircraft(hex);
    }
});


// ── Map Init ──

function initMap() {
    mapboxgl.accessToken = MAPBOX_TOKEN;

    map = new mapboxgl.Map({
        container: 'map',
        style: 'mapbox://styles/mapbox/dark-v11',
        center: [-98.5, 39.8],
        zoom: 4,
    });

    map.addControl(new mapboxgl.NavigationControl(), 'bottom-right');

    map.on('load', () => {
        deckOverlay = new deck.MapboxOverlay({ layers: [] });
        map.addControl(deckOverlay);

        // Try browser geolocation
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                (pos) => {
                    currentLat = pos.coords.latitude;
                    currentLng = pos.coords.longitude;
                    map.flyTo({ center: [currentLng, currentLat], zoom: 10 });
                    loadOverhead();
                    startAutoRefresh();
                    addressInput.placeholder = 'Your location detected';
                },
                () => {
                    statusText.textContent = 'Enter an address to get started';
                }
            );
        }
    });
}

if (MAPBOX_TOKEN) {
    initMap();
} else {
    statusText.textContent = 'Set MAPBOX_TOKEN in .env';
}

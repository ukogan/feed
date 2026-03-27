/**
 * Flight Explorer Map
 * Deck.gl ScatterplotLayer + ArcLayer on Mapbox for aircraft visualization.
 * Supports both real-time and historical flight data.
 */

let map;
let deckOverlay;
let currentLat = null;
let currentLng = null;
let refreshTimer = null;
let historyDays = 1;
let historyTracks = [];
let liveAircraft = [];
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
const historyBtn = document.getElementById('history-btn');
const historyStatsEl = document.getElementById('history-stats');
const histFlightsEl = document.getElementById('hist-flights');
const histUniqueEl = document.getElementById('hist-unique');
const histSeatsEl = document.getElementById('hist-seats');
const historyRepeatEl = document.getElementById('history-repeat');
const historyLegend = document.getElementById('history-legend');


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

function dateNDaysAgo(n) {
    const d = new Date();
    d.setDate(d.getDate() - n);
    return d.toISOString().split('T')[0];
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

    // Add historical track arcs if loaded
    if (historyTracks.length > 0) {
        const arcData = buildArcData(historyTracks);
        if (arcData.length > 0) {
            const arcLayer = new deck.ArcLayer({
                id: 'history-arcs',
                data: arcData,
                getSourcePosition: d => d.source,
                getTargetPosition: d => d.target,
                getSourceColor: [251, 146, 60, 120],
                getTargetColor: [251, 146, 60, 40],
                getWidth: 1.5,
                pickable: true,
                autoHighlight: true,
                highlightColor: [251, 146, 60, 200],
            });
            layers.unshift(arcLayer);
        }
    }

    deckOverlay.setProps({
        layers,
        getTooltip: ({ object }) => {
            if (!object) return null;

            // Historical arc tooltip
            if (object.callsign !== undefined && object.source !== undefined) {
                const lines = [
                    object.callsign || object.hex || '',
                    object.type_code ? `Type: ${object.type_code}` : '',
                    object.registration ? `Reg: ${object.registration}` : '',
                    object.date ? `Date: ${object.date}` : '',
                ].filter(Boolean);
                return {
                    html: `<div style="font-family:var(--font-mono);font-size:12px;line-height:1.5">${lines.join('<br>')}</div>`,
                    style: {
                        background: 'rgba(15,23,42,0.95)',
                        color: '#f1f5f9',
                        border: '1px solid #fb923c',
                        borderRadius: '6px',
                        padding: '6px 10px',
                    }
                };
            }

            // Live aircraft tooltip
            if (!object.callsign) return null;
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


/**
 * Build arc data from historical tracks.
 * Each track becomes one arc from first to last position within the search area.
 */
function buildArcData(tracks) {
    const arcs = [];
    for (const track of tracks) {
        const positions = track.positions;
        if (!positions || positions.length < 2) continue;

        const first = positions[0];
        const last = positions[positions.length - 1];

        arcs.push({
            source: [first.lng, first.lat],
            target: [last.lng, last.lat],
            hex: track.hex,
            callsign: track.callsign || '',
            registration: track.registration || '',
            type_code: track.type_code || '',
            date: track.date || '',
        });
    }
    return arcs;
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
        historyBtn.disabled = false;
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

        liveAircraft = data.aircraft;
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
        loadAircraftHistory(identifier);
        statusText.textContent = `Tracking ${identifier}`;
    } catch (err) {
        statusText.textContent = `Error: ${err.message}`;
    }
}

async function loadAircraftHistory(identifier) {
    try {
        const start = dateNDaysAgo(30);
        const end = dateNDaysAgo(0);
        const resp = await fetch(
            `/api/aircraft/${encodeURIComponent(identifier)}/history?start=${start}&end=${end}`
        );
        const data = await resp.json();

        if (data.error || !data.tracks || data.tracks.length === 0) return;

        // Show historical tracks on map as arcs
        historyTracks = data.tracks;
        updateMap(liveAircraft);
        historyLegend.classList.add('visible');
    } catch (_) {
        // Historical data may not be available; ignore silently
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


// ── History ──

async function loadHistory() {
    if (!currentLat || !currentLng) return;

    historyBtn.disabled = true;
    historyBtn.textContent = 'Loading...';
    statusText.textContent = `Loading ${historyDays}-day history...`;

    try {
        // Load stats and tracks in parallel
        const start = dateNDaysAgo(historyDays);
        const end = dateNDaysAgo(0);

        const [statsResp, tracksResp] = await Promise.all([
            fetch(`/api/stats/history?lat=${currentLat}&lng=${currentLng}&days=${historyDays}&radius=10`),
            fetch(`/api/overhead/history/tracks?lat=${currentLat}&lng=${currentLng}&start=${start}&end=${end}&radius=10&limit=200`),
        ]);

        const statsData = await statsResp.json();
        const tracksData = await tracksResp.json();

        // Update history stats
        if (!statsData.error) {
            historyStatsEl.style.display = 'block';
            histFlightsEl.textContent = statsData.total_flights || '--';
            histUniqueEl.textContent = statsData.unique_aircraft || '--';
            histSeatsEl.textContent = statsData.total_seats ? statsData.total_seats.toLocaleString() : '--';

            // Repeat visitors
            if (statsData.repeat_visitors && statsData.repeat_visitors.length > 0) {
                historyRepeatEl.innerHTML = `
                    <div class="repeat-title">Repeat Visitors</div>
                    ${statsData.repeat_visitors.slice(0, 10).map(rv => `
                        <div class="repeat-item" data-reg="${rv.registration || ''}" data-hex="${rv.hex}">
                            <span class="repeat-reg">${rv.registration || rv.callsign || rv.hex}</span>
                            <span class="repeat-count">${rv.days_seen} days</span>
                        </div>
                    `).join('')}
                `;
            } else {
                historyRepeatEl.innerHTML = '';
            }
        }

        // Show tracks on map
        if (!tracksData.error && tracksData.tracks) {
            historyTracks = tracksData.tracks;
            updateMap(liveAircraft);
            historyLegend.classList.add('visible');
        }

        statusText.textContent = `History loaded: ${statsData.total_flights || 0} flights over ${historyDays} day(s)`;
    } catch (err) {
        statusText.textContent = `History error: ${err.message}`;
    } finally {
        historyBtn.disabled = false;
        historyBtn.textContent = 'Load History';
    }
}

function clearHistory() {
    historyTracks = [];
    historyStatsEl.style.display = 'none';
    historyRepeatEl.innerHTML = '';
    historyLegend.classList.remove('visible');
    updateMap(liveAircraft);
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

// History range buttons
document.querySelectorAll('.range-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.range-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        historyDays = parseInt(btn.dataset.days, 10);
        clearHistory();
    });
});

// History load button
historyBtn.addEventListener('click', loadHistory);

// Click on repeat visitor
historyRepeatEl.addEventListener('click', (e) => {
    const item = e.target.closest('.repeat-item');
    if (!item) return;
    const reg = item.dataset.reg;
    const hex = item.dataset.hex;
    const identifier = reg || hex;
    if (identifier) {
        tailInput.value = identifier;
        trackAircraft(identifier);
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
                    historyBtn.disabled = false;
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

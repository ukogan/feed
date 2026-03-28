/**
 * Above Me - Deep dive into what's flying overhead at 94062.
 * Uses ADSB.lol for real-time + OpenSky for historical flight data.
 */

let map;
let deckOverlay;
let selectedDays = 7;
let aboveData = null;
let trackData = null;

// Default: 94062 Redwood City
const DEFAULT_LAT = 37.47;
const DEFAULT_LNG = -122.23;

// Get lat/lng from URL params or use defaults
const urlParams = new URLSearchParams(window.location.search);
const centerLat = parseFloat(urlParams.get('lat')) || DEFAULT_LAT;
const centerLng = parseFloat(urlParams.get('lng')) || DEFAULT_LNG;

// DOM refs
const scanBtn = document.getElementById('scan-btn');
const spinner = document.getElementById('loading-spinner');
const statusText = document.getElementById('status-text');
const statOverhead = document.getElementById('stat-overhead');
const statFlights = document.getElementById('stat-flights');
const statSeats = document.getElementById('stat-seats');
const destSection = document.getElementById('destinations-section');
const destTbody = document.getElementById('dest-tbody');
const countrySection = document.getElementById('country-section');
const countryChart = document.getElementById('country-chart');
const stateSection = document.getElementById('state-section');
const stateChart = document.getElementById('state-chart');
const aircraftGrid = document.getElementById('aircraft-grid');


// ---- Utilities ----

function formatAlt(ft) {
    if (!ft || ft === 'ground') return 'GND';
    return 'FL' + Math.round(ft / 100);
}

function formatNum(n) {
    if (n === null || n === undefined) return '--';
    return n.toLocaleString();
}

function setLoading(on) {
    spinner.classList.toggle('visible', on);
    scanBtn.disabled = on;
    scanBtn.textContent = on ? 'Scanning...' : 'Scan';
}


// ---- Map ----

function initMap() {
    mapboxgl.accessToken = MAPBOX_TOKEN;

    map = new mapboxgl.Map({
        container: 'above-map',
        style: 'mapbox://styles/mapbox/dark-v11',
        center: [centerLng, centerLat],
        zoom: 9,
    });

    map.addControl(new mapboxgl.NavigationControl(), 'bottom-right');

    map.on('load', () => {
        deckOverlay = new deck.MapboxOverlay({ layers: [] });
        map.addControl(deckOverlay);
    });
}

function updateMapLayers() {
    if (!deckOverlay) return;

    const layers = [];

    // User location
    layers.push(new deck.ScatterplotLayer({
        id: 'user-loc',
        data: [{ lat: centerLat, lng: centerLng }],
        getPosition: d => [d.lng, d.lat],
        getRadius: 8,
        getFillColor: [56, 189, 248],
        getLineColor: [255, 255, 255],
        lineWidthMinPixels: 2,
        stroked: true,
        radiusUnits: 'pixels',
    }));

    // Radius circle (10 NM)
    layers.push(new deck.ScatterplotLayer({
        id: 'radius-ring',
        data: [{ lat: centerLat, lng: centerLng }],
        getPosition: d => [d.lng, d.lat],
        getRadius: 10 * 1852,
        getFillColor: [56, 189, 248, 12],
        getLineColor: [56, 189, 248, 50],
        lineWidthMinPixels: 1,
        stroked: true,
        filled: true,
        radiusUnits: 'meters',
    }));

    // Overhead aircraft dots
    if (aboveData && aboveData.overhead) {
        const acData = aboveData.overhead.filter(ac => ac.lat && ac.lng && !ac.on_ground);
        layers.push(new deck.ScatterplotLayer({
            id: 'overhead-ac',
            data: acData,
            getPosition: d => [d.lng, d.lat],
            getRadius: 5,
            getFillColor: [34, 211, 238],
            radiusUnits: 'pixels',
            radiusMinPixels: 4,
            radiusMaxPixels: 8,
            pickable: true,
            autoHighlight: true,
            highlightColor: [255, 255, 255, 80],
        }));
    }

    // Destination airports (sized by seat count)
    if (aboveData && aboveData.analysis && aboveData.analysis.destinations) {
        const dests = aboveData.analysis.destinations.filter(d => d.lat && d.lng);
        const maxSeats = Math.max(1, ...dests.map(d => d.total_seats));

        layers.push(new deck.ScatterplotLayer({
            id: 'dest-airports',
            data: dests,
            getPosition: d => [d.lng, d.lat],
            getRadius: d => 4 + (d.total_seats / maxSeats) * 16,
            getFillColor: d => {
                const intensity = Math.min(255, 100 + (d.count / Math.max(1, dests[0].count)) * 155);
                return [167, 139, 250, intensity];
            },
            radiusUnits: 'pixels',
            radiusMinPixels: 4,
            radiusMaxPixels: 20,
            pickable: true,
            autoHighlight: true,
            highlightColor: [167, 139, 250, 200],
        }));
    }

    // Flight track arcs
    if (trackData && trackData.tracks) {
        const arcData = [];
        for (const t of trackData.tracks) {
            if (!t.waypoints || t.waypoints.length < 2) continue;
            const first = t.waypoints[0];
            const last = t.waypoints[t.waypoints.length - 1];
            if (first.latitude == null || last.latitude == null) continue;
            arcData.push({
                source: [first.longitude, first.latitude],
                target: [last.longitude, last.latitude],
                callsign: t.callsign,
                type_code: t.type_code,
                departure: t.departure,
                arrival: t.arrival,
            });
        }

        if (arcData.length > 0) {
            layers.push(new deck.ArcLayer({
                id: 'flight-arcs',
                data: arcData,
                getSourcePosition: d => d.source,
                getTargetPosition: d => d.target,
                getSourceColor: [251, 146, 60, 160],
                getTargetColor: [251, 146, 60, 50],
                getWidth: 1.5,
                pickable: true,
                autoHighlight: true,
                highlightColor: [251, 146, 60, 220],
            }));
        }
    }

    deckOverlay.setProps({
        layers,
        getTooltip: ({ object }) => {
            if (!object) return null;
            const lines = [];
            if (object.callsign) lines.push(object.callsign);
            if (object.type_code) lines.push('Type: ' + object.type_code);
            if (object.code) lines.push(object.code + (object.name ? ' - ' + object.name : ''));
            if (object.altitude_ft) lines.push('Alt: ' + object.altitude_ft.toLocaleString() + ' ft');
            if (object.distance_nm) lines.push('Dist: ' + object.distance_nm.toFixed(1) + ' NM');
            if (object.total_seats) lines.push('Seats: ' + object.total_seats.toLocaleString());
            if (object.count) lines.push('Flights: ' + object.count);
            if (object.departure) lines.push('From: ' + object.departure);
            if (object.arrival) lines.push('To: ' + object.arrival);
            if (object.tail_number) lines.push('Reg: ' + object.tail_number);
            if (object.seat_count) lines.push('Seats: ' + object.seat_count);
            if (lines.length === 0) return null;
            return {
                html: '<div style="font-family:var(--font-mono);font-size:12px;line-height:1.5">' + lines.join('<br>') + '</div>',
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


// ---- Stats Rendering ----

function renderStats(data) {
    const analysis = data.analysis;

    statOverhead.textContent = formatNum(data.overhead_count);
    statFlights.textContent = formatNum(analysis.total_flights);
    statSeats.textContent = formatNum(analysis.total_seats);

    // Destinations table
    if (analysis.destinations && analysis.destinations.length > 0) {
        destSection.style.display = '';
        destTbody.innerHTML = analysis.destinations.slice(0, 20).map(d => {
            return '<tr>' +
                '<td><span class="dest-code">' + escapeHtml(d.code) + '</span>' +
                (d.name && d.name !== d.code ? '<br><span class="dest-name">' + escapeHtml(d.name) + '</span>' : '') +
                '</td>' +
                '<td>' + d.count + '</td>' +
                '<td>' + formatNum(d.total_seats) + '</td>' +
                '<td>' + escapeHtml(d.country || '?') + '</td>' +
                '</tr>';
        }).join('');
    } else {
        destSection.style.display = 'none';
    }

    // Country chart
    if (analysis.by_country && analysis.by_country.length > 0) {
        countrySection.style.display = '';
        renderBarChart(countryChart, analysis.by_country.slice(0, 10), 'country', 'total_seats');
    } else {
        countrySection.style.display = 'none';
    }

    // State chart
    if (analysis.by_state && analysis.by_state.length > 0) {
        stateSection.style.display = '';
        renderBarChart(stateChart, analysis.by_state.slice(0, 10), 'state', 'total_seats');
    } else {
        stateSection.style.display = 'none';
    }
}

function renderBarChart(container, items, labelKey, valueKey) {
    const maxVal = Math.max(1, ...items.map(d => d[valueKey]));
    container.innerHTML = items.map(d => {
        const pct = (d[valueKey] / maxVal) * 100;
        return '<div class="bar-row">' +
            '<span class="bar-label">' + escapeHtml(d[labelKey]) + '</span>' +
            '<span class="bar-track"><span class="bar-fill" style="width:' + pct + '%"></span></span>' +
            '<span class="bar-value">' + formatNum(d[valueKey]) + '</span>' +
            '</div>';
    }).join('');
}


// ---- Aircraft List ----

function renderAircraftList(data) {
    const overhead = data.overhead || [];
    const details = (data.analysis && data.analysis.aircraft_details) || [];

    if (overhead.length === 0) {
        aircraftGrid.innerHTML = '<div class="empty-state">No aircraft detected overhead</div>';
        return;
    }

    // Build lookup from hex to flight details
    const detailMap = {};
    for (const d of details) {
        detailMap[d.hex] = d;
    }

    aircraftGrid.innerHTML = overhead.map(ac => {
        const detail = detailMap[ac.hex] || {};
        const flights = detail.flights || [];

        let historyHtml = '';
        if (flights.length > 0) {
            historyHtml = '<div class="ac-history">' +
                flights.slice(0, 5).map(f => {
                    const route = [f.departure, f.arrival].filter(Boolean).join(' -> ') || 'Unknown route';
                    const cs = f.callsign || '';
                    return '<div class="ac-flight-row">' +
                        '<span class="route">' + escapeHtml(route) + '</span>' +
                        (cs ? '<span>' + escapeHtml(cs) + '</span>' : '') +
                        '</div>';
                }).join('') +
                (flights.length > 5 ? '<div class="ac-flight-row" style="color:var(--text-muted)">+ ' + (flights.length - 5) + ' more flights</div>' : '') +
                '</div>';
        }

        const altStr = formatAlt(ac.altitude_ft);
        const distStr = ac.distance_nm ? ac.distance_nm.toFixed(1) + ' NM' : '';

        return '<div class="ac-card" data-hex="' + ac.hex + '">' +
            '<span class="ac-type-badge">' + escapeHtml(ac.type_code || '??') + '</span>' +
            '<div class="ac-main">' +
                '<span class="ac-callsign">' + escapeHtml(ac.callsign || ac.tail_number || ac.hex) + '</span>' +
                '<span class="ac-detail">' +
                    escapeHtml(ac.description || ac.owner || '') +
                    (ac.seat_count ? ' / ' + ac.seat_count + ' seats' : '') +
                    (distStr ? ' / ' + distStr : '') +
                '</span>' +
            '</div>' +
            '<span class="ac-alt">' + altStr + '</span>' +
            historyHtml +
            '</div>';
    }).join('');
}


// ---- Data Loading ----

async function runScan() {
    setLoading(true);
    statusText.textContent = 'Scanning overhead aircraft...';

    try {
        // Fetch main analysis and tracks in parallel
        const [aboveResp, tracksResp] = await Promise.all([
            fetch('/api/above-me?lat=' + centerLat + '&lng=' + centerLng + '&days=' + selectedDays),
            fetch('/api/above-me/tracks?lat=' + centerLat + '&lng=' + centerLng + '&days=' + selectedDays),
        ]);

        aboveData = await aboveResp.json();
        trackData = await tracksResp.json();

        if (aboveData.error) {
            statusText.textContent = 'Error: ' + aboveData.error;
            setLoading(false);
            return;
        }

        // Render everything
        renderStats(aboveData);
        renderAircraftList(aboveData);
        updateMapLayers();

        const now = new Date().toLocaleTimeString();
        const acCount = aboveData.overhead_count || 0;
        const flCount = (aboveData.analysis && aboveData.analysis.total_flights) || 0;
        statusText.textContent = acCount + ' aircraft overhead, ' + flCount + ' flights in ' + selectedDays + 'd / ' + now;

    } catch (err) {
        statusText.textContent = 'Error: ' + err.message;
    } finally {
        setLoading(false);
    }
}


// ---- Helpers ----

function escapeHtml(s) {
    if (!s) return '';
    return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}


// ---- Event Listeners ----

scanBtn.addEventListener('click', runScan);

// Range buttons
document.querySelectorAll('.range-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.range-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        selectedDays = parseInt(btn.dataset.days, 10);
    });
});

// Click aircraft card to expand
aircraftGrid.addEventListener('click', (e) => {
    const card = e.target.closest('.ac-card');
    if (!card) return;
    card.classList.toggle('expanded');
});


// ---- Init ----

if (MAPBOX_TOKEN) {
    initMap();
} else {
    statusText.textContent = 'Set MAPBOX_TOKEN in .env';
}

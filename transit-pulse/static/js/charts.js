/**
 * Transit Pulse: BART reliability dashboard with Mapbox map and D3 charts.
 * Auto-refreshes every 30 seconds.
 */

// State
let map;
let stations = [];
let stationMarkers = {};
let reliability = {};
let sampleDepartures = {};
let selectedStation = null;
let refreshTimer = null;
let lastRefresh = null;
let countdownTimer = null;

// DOM refs
const statOntime = document.getElementById('stat-ontime');
const statStations = document.getElementById('stat-stations');
const statDelayed = document.getElementById('stat-delayed');
const stationListEl = document.getElementById('station-list');
const loadingEl = document.getElementById('loading');
const refreshDot = document.getElementById('refresh-dot');
const refreshLabel = document.getElementById('refresh-label');


function escapeHtml(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

function formatDelay(seconds) {
    if (seconds <= 0) return 'On time';
    if (seconds < 60) return seconds + 's delay';
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return secs > 0 ? mins + 'm ' + secs + 's' : mins + 'm';
}

function delayStatusColor(score) {
    // score is on_time_pct
    if (score === null || score === undefined) return '#64748b';
    if (score >= 95) return '#22c55e';
    if (score >= 80) return '#eab308';
    return '#ef4444';
}

function delayDotClass(score) {
    if (score === null || score === undefined) return '';
    if (score >= 95) return 'on-time';
    if (score >= 80) return 'minor-delay';
    return 'major-delay';
}


// ---- Data fetching ----

async function fetchDashboard() {
    refreshDot.classList.add('loading');
    refreshLabel.textContent = 'Refreshing...';

    try {
        const resp = await fetch('/api/dashboard');
        const data = await resp.json();

        stations = data.stations || [];
        reliability = data.reliability || {};
        sampleDepartures = data.sample_departures || {};

        if (data.errors && data.errors.length > 0) {
            console.warn('Dashboard errors:', data.errors);
        }

        updateStats();
        renderStationList();
        updateMapMarkers();
        renderDelayChart();

        loadingEl.style.display = 'none';
        lastRefresh = Date.now();
    } catch (err) {
        console.error('Failed to load dashboard:', err);
        stationListEl.innerHTML =
            '<div style="padding: 2rem; text-align: center; color: #ef4444; font-size: 0.8125rem;">' +
            'Failed to load data</div>';
    } finally {
        refreshDot.classList.remove('loading');
        updateRefreshLabel();
    }
}


// ---- Stats panel ----

function updateStats() {
    const stationScores = reliability.stations || {};
    const allScores = Object.values(stationScores);

    statStations.textContent = stations.length.toString();

    if (allScores.length === 0) {
        statOntime.textContent = '--';
        statDelayed.textContent = '--';
        return;
    }

    const totalDeps = allScores.reduce((sum, s) => sum + s.total_departures, 0);
    const totalDelayed = allScores.reduce((sum, s) => sum + s.delayed, 0);
    const systemOnTime = totalDeps > 0
        ? ((totalDeps - totalDelayed) / totalDeps * 100)
        : 100;

    statOntime.textContent = systemOnTime.toFixed(1) + '%';
    if (systemOnTime >= 95) {
        statOntime.className = 'stat-value good';
    } else if (systemOnTime >= 80) {
        statOntime.className = 'stat-value warn';
    } else {
        statOntime.className = 'stat-value bad';
    }

    statDelayed.textContent = totalDelayed.toString();
}


// ---- Station list (sidebar) ----

function renderStationList() {
    const stationScores = reliability.stations || {};

    // Sort: delayed stations first, then alphabetical
    const sorted = [...stations].sort((a, b) => {
        const scoreA = stationScores[a.abbr]?.on_time_pct ?? 100;
        const scoreB = stationScores[b.abbr]?.on_time_pct ?? 100;
        if (scoreA !== scoreB) return scoreA - scoreB;
        return a.name.localeCompare(b.name);
    });

    stationListEl.innerHTML = sorted.map(stn => {
        const score = stationScores[stn.abbr];
        const pct = score ? score.on_time_pct : null;
        const avgDelay = score ? score.avg_delay_seconds : 0;
        const dotClass = delayDotClass(pct);
        const isSelected = selectedStation === stn.abbr;

        let delayText = '--';
        let delayClass = '';
        if (score) {
            if (avgDelay > 0) {
                delayText = formatDelay(Math.round(avgDelay));
                delayClass = avgDelay > 120 ? 'major' : 'delayed';
            } else {
                delayText = 'On time';
            }
        }

        return '<div class="station-item' + (isSelected ? ' selected' : '') +
            '" data-station="' + stn.abbr + '">' +
            '<span class="station-dot ' + dotClass + '"></span>' +
            '<span class="station-name">' + escapeHtml(stn.name) + '</span>' +
            '<span class="station-delay-info ' + delayClass + '">' + delayText + '</span>' +
            '</div>';
    }).join('');

    stationListEl.querySelectorAll('.station-item').forEach(el => {
        el.addEventListener('click', () => {
            const abbr = el.dataset.station;
            if (selectedStation === abbr) {
                selectedStation = null;
            } else {
                selectedStation = abbr;
            }
            renderStationList();
            highlightMapStation(selectedStation);
        });
    });
}


// ---- Mapbox map ----

function initMap() {
    mapboxgl.accessToken = MAPBOX_TOKEN;

    map = new mapboxgl.Map({
        container: 'map',
        style: 'mapbox://styles/mapbox/dark-v11',
        center: [-122.2, 37.75],
        zoom: 10,
    });

    map.addControl(new mapboxgl.NavigationControl(), 'bottom-right');

    map.on('load', () => {
        fetchDashboard();
    });
}

function updateMapMarkers() {
    const stationScores = reliability.stations || {};

    // Remove old markers
    Object.values(stationMarkers).forEach(m => m.remove());
    stationMarkers = {};

    stations.forEach(stn => {
        if (!stn.lat || !stn.lng) return;

        const score = stationScores[stn.abbr];
        const pct = score ? score.on_time_pct : null;
        const color = delayStatusColor(pct);
        const avgDelay = score ? score.avg_delay_seconds : 0;

        // Create a colored circle marker
        const el = document.createElement('div');
        el.style.width = '14px';
        el.style.height = '14px';
        el.style.borderRadius = '50%';
        el.style.background = color;
        el.style.border = '2px solid rgba(255,255,255,0.3)';
        el.style.cursor = 'pointer';
        el.style.transition = 'transform 0.2s, box-shadow 0.2s';

        if (selectedStation === stn.abbr) {
            el.style.transform = 'scale(1.5)';
            el.style.boxShadow = '0 0 8px ' + color;
        }

        // Popup content
        let popupHtml = '<div class="popup-title">' + escapeHtml(stn.name) + '</div>';
        popupHtml += '<div class="popup-detail">';
        if (score) {
            popupHtml += 'On-time: <strong>' + (pct !== null ? pct.toFixed(1) + '%' : '--') + '</strong><br>';
            popupHtml += 'Departures: <strong>' + score.total_departures + '</strong><br>';
            if (avgDelay > 0) {
                popupHtml += 'Avg delay: <strong>' + formatDelay(Math.round(avgDelay)) + '</strong>';
            } else {
                popupHtml += 'Status: <strong style="color: #22c55e;">On time</strong>';
            }
        } else {
            popupHtml += 'No departure data';
        }
        popupHtml += '</div>';

        const popup = new mapboxgl.Popup({ offset: 10, maxWidth: '240px' })
            .setHTML(popupHtml);

        const marker = new mapboxgl.Marker({ element: el })
            .setLngLat([stn.lng, stn.lat])
            .setPopup(popup)
            .addTo(map);

        el.addEventListener('click', () => {
            selectedStation = stn.abbr;
            renderStationList();
            highlightMapStation(stn.abbr);
        });

        stationMarkers[stn.abbr] = marker;
    });
}

function highlightMapStation(abbr) {
    // Update marker styles
    Object.entries(stationMarkers).forEach(([key, marker]) => {
        const el = marker.getElement();
        if (key === abbr) {
            el.style.transform = 'scale(1.5)';
            el.style.boxShadow = '0 0 8px ' + el.style.background;
            marker.togglePopup();
        } else {
            el.style.transform = 'scale(1)';
            el.style.boxShadow = 'none';
        }
    });

    // Fly to selected station
    if (abbr && stationMarkers[abbr]) {
        const lngLat = stationMarkers[abbr].getLngLat();
        map.flyTo({ center: lngLat, zoom: 13, duration: 800 });
    }
}


// ---- D3 bar chart: delays by line/direction ----

function renderDelayChart() {
    const lineScores = reliability.lines || {};
    const entries = Object.entries(lineScores)
        .filter(([name]) => name !== 'Unknown')
        .sort((a, b) => b[1].delayed - a[1].delayed);

    if (entries.length === 0) {
        document.getElementById('chart-subtitle').textContent = 'No data available';
        return;
    }

    const svg = d3.select('#delay-chart');
    svg.selectAll('*').remove();

    const container = document.querySelector('.chart-container');
    const width = container.clientWidth;
    const height = container.clientHeight;
    const margin = { top: 10, right: 60, bottom: 25, left: 90 };
    const innerW = width - margin.left - margin.right;
    const innerH = height - margin.top - margin.bottom;

    svg.attr('viewBox', '0 0 ' + width + ' ' + height);

    const g = svg.append('g')
        .attr('transform', 'translate(' + margin.left + ',' + margin.top + ')');

    // Scales
    const y = d3.scaleBand()
        .domain(entries.map(d => d[0]))
        .range([0, innerH])
        .padding(0.3);

    const maxDelayed = d3.max(entries, d => d[1].delayed) || 1;
    const x = d3.scaleLinear()
        .domain([0, maxDelayed])
        .range([0, innerW])
        .nice();

    // Grid lines
    g.append('g')
        .attr('class', 'grid')
        .call(d3.axisBottom(x)
            .ticks(5)
            .tickSize(innerH)
            .tickFormat('')
        );

    // Bars
    g.selectAll('.bar')
        .data(entries)
        .join('rect')
        .attr('class', 'bar')
        .attr('y', d => y(d[0]))
        .attr('x', 0)
        .attr('height', y.bandwidth())
        .attr('width', d => x(d[1].delayed))
        .attr('fill', d => d[1].color || '#a855f7')
        .attr('opacity', 0.8)
        .attr('rx', 3);

    // Y axis labels
    g.append('g')
        .attr('class', 'axis')
        .call(d3.axisLeft(y).tickSize(0).tickPadding(8))
        .selectAll('text')
        .style('fill', '#94a3b8')
        .style('font-size', '11px');

    g.select('.axis .domain').remove();

    // Value labels on bars
    g.selectAll('.bar-value')
        .data(entries)
        .join('text')
        .attr('class', 'bar-value')
        .attr('x', d => x(d[1].delayed) + 6)
        .attr('y', d => y(d[0]) + y.bandwidth() / 2)
        .attr('dy', '0.35em')
        .text(d => {
            const avg = d[1].avg_delay_seconds;
            return d[1].delayed + ' delayed' + (avg > 0 ? ' (avg ' + avg.toFixed(0) + 's)' : '');
        })
        .style('fill', '#94a3b8')
        .style('font-size', '10px')
        .style('font-family', "'JetBrains Mono', monospace");

    // X axis
    g.append('g')
        .attr('class', 'axis')
        .attr('transform', 'translate(0,' + innerH + ')')
        .call(d3.axisBottom(x).ticks(5).tickSize(0).tickPadding(6))
        .select('.domain').remove();

    document.getElementById('chart-subtitle').textContent =
        'Delayed departures by BART line';
}


// ---- Auto-refresh ----

function updateRefreshLabel() {
    if (!lastRefresh) {
        refreshLabel.textContent = 'Connecting...';
        return;
    }
    const elapsed = Math.floor((Date.now() - lastRefresh) / 1000);
    const remaining = Math.max(0, 30 - elapsed);
    refreshLabel.textContent = 'Refresh in ' + remaining + 's';
}

function startAutoRefresh() {
    // Refresh data every 30 seconds
    refreshTimer = setInterval(() => {
        fetchDashboard();
    }, 30000);

    // Update countdown label every second
    countdownTimer = setInterval(updateRefreshLabel, 1000);
}


// ---- Init ----

if (MAPBOX_TOKEN) {
    initMap();
    startAutoRefresh();
} else {
    loadingEl.innerHTML =
        '<div class="feed-panel" style="text-align: center; padding: 2rem;">' +
        '<p style="color: var(--text-muted);">Set MAPBOX_TOKEN in .env to load the map</p>' +
        '<p style="color: var(--text-muted); font-size: 0.75rem; margin-top: 0.5rem;">' +
        'API endpoints still work at /api/stations, /api/departures, /api/reliability</p>' +
        '</div>';
}

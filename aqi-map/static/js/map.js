/**
 * AQI Time-Slider Map
 * Deck.gl HeatmapLayer on Mapbox GL JS with animated time controls.
 */

// EPA AQI color scale: Good(green) -> Hazardous(maroon)
const AQI_COLOR_RANGE = [
    [0, 228, 0],       // Good (0-50)
    [255, 255, 0],     // Moderate (51-100)
    [255, 126, 0],     // Unhealthy for Sensitive (101-150)
    [255, 0, 0],       // Unhealthy (151-200)
    [143, 63, 151],    // Very Unhealthy (201-300)
    [126, 0, 35],      // Hazardous (301+)
];

const MONTH_NAMES = [
    '', 'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
];

let map;
let deckOverlay;
let currentData = [];
let yearDataCache = {};
let isPlaying = false;
let playInterval = null;

// DOM refs
const monthSlider = document.getElementById('month-slider');
const yearSelect = document.getElementById('year-select');
const currentDateEl = document.getElementById('current-date');
const playBtn = document.getElementById('play-btn');
const playIcon = document.getElementById('play-icon');
const pauseIcon = document.getElementById('pause-icon');
const statStations = document.getElementById('stat-stations');
const statAvg = document.getElementById('stat-avg');
const statMax = document.getElementById('stat-max');


function aqiToWeight(aqi) {
    // Normalize AQI to 0-1 range for heatmap weight
    return Math.min(aqi / 200, 1.0);
}

function aqiToColor(aqi) {
    if (aqi <= 50) return '#00e400';
    if (aqi <= 100) return '#ffff00';
    if (aqi <= 150) return '#ff7e00';
    if (aqi <= 200) return '#ff0000';
    if (aqi <= 300) return '#8f3f97';
    return '#7e0023';
}

function updateStats(data) {
    if (!data || data.length === 0) {
        statStations.textContent = '--';
        statAvg.textContent = '--';
        statMax.textContent = '--';
        return;
    }
    const aqis = data.map(d => d.aqi);
    const avg = aqis.reduce((a, b) => a + b, 0) / aqis.length;
    const max = Math.max(...aqis);

    statStations.textContent = data.length.toLocaleString();
    statAvg.textContent = avg.toFixed(0);
    statAvg.style.color = aqiToColor(avg);
    statMax.textContent = max.toFixed(0);
    statMax.style.color = aqiToColor(max);
}

function updateHeatmap(data) {
    currentData = data;
    updateStats(data);

    if (!deckOverlay) return;

    const heatmapLayer = new deck.HeatmapLayer({
        id: 'aqi-heatmap',
        data: data,
        getPosition: d => [d.lng, d.lat],
        getWeight: d => aqiToWeight(d.aqi),
        radiusPixels: 60,
        intensity: 1.2,
        threshold: 0.05,
        colorRange: AQI_COLOR_RANGE,
        aggregation: 'MEAN',
        transitions: {
            getWeight: { duration: 300 }
        }
    });

    deckOverlay.setProps({ layers: [heatmapLayer] });
}

async function fetchAQIData(year, month) {
    // Check cache first
    const cacheKey = `${year}-${month}`;
    if (yearDataCache[cacheKey]) {
        return yearDataCache[cacheKey];
    }

    try {
        const response = await fetch(`/api/aqi?year=${year}&month=${month}`);
        const data = await response.json();
        yearDataCache[cacheKey] = data;
        return data;
    } catch (err) {
        console.error('Failed to fetch AQI data:', err);
        return [];
    }
}

async function prefetchYear(year) {
    // Prefetch all months for a year in the background
    const promises = [];
    for (let m = 1; m <= 12; m++) {
        const key = `${year}-${m}`;
        if (!yearDataCache[key]) {
            promises.push(fetchAQIData(year, m));
        }
    }
    await Promise.all(promises);
}

async function updateDisplay() {
    const year = parseInt(yearSelect.value);
    const month = parseInt(monthSlider.value);
    currentDateEl.textContent = `${MONTH_NAMES[month]} ${year}`;

    const data = await fetchAQIData(year, month);
    updateHeatmap(data);
}

function togglePlay() {
    isPlaying = !isPlaying;
    playIcon.style.display = isPlaying ? 'none' : 'block';
    pauseIcon.style.display = isPlaying ? 'block' : 'none';
    playBtn.classList.toggle('playing', isPlaying);

    if (isPlaying) {
        // Prefetch current year
        prefetchYear(parseInt(yearSelect.value));

        playInterval = setInterval(() => {
            let month = parseInt(monthSlider.value);
            let year = parseInt(yearSelect.value);

            month++;
            if (month > 12) {
                month = 1;
                // Move to next year if available
                const options = Array.from(yearSelect.options).map(o => parseInt(o.value));
                const nextIdx = options.indexOf(year) + 1;
                if (nextIdx < options.length) {
                    year = options[nextIdx];
                    yearSelect.value = year;
                    prefetchYear(year);
                } else {
                    // Loop back to start
                    year = options[0];
                    yearSelect.value = year;
                    prefetchYear(year);
                }
            }
            monthSlider.value = month;
            updateDisplay();
        }, 600);
    } else {
        clearInterval(playInterval);
        playInterval = null;
    }
}

async function loadAvailableYears() {
    try {
        const response = await fetch('/api/years');
        const years = await response.json();

        if (years.length === 0) {
            yearSelect.innerHTML = '<option value="2024">2024</option>';
            currentDateEl.textContent = 'No data yet -- run backfill scripts';
            return;
        }

        yearSelect.innerHTML = years.map(y =>
            `<option value="${y}"${y === years[years.length - 1] ? ' selected' : ''}>${y}</option>`
        ).join('');

        // Load initial data
        await updateDisplay();
        // Prefetch the selected year
        prefetchYear(parseInt(yearSelect.value));
    } catch (err) {
        console.error('Failed to load years:', err);
        currentDateEl.textContent = 'Error loading data';
    }
}

function initMap() {
    mapboxgl.accessToken = MAPBOX_TOKEN;

    map = new mapboxgl.Map({
        container: 'map',
        style: 'mapbox://styles/mapbox/dark-v11',
        center: [-98.5, 39.8],  // Center of US
        zoom: 4,
        pitch: 0,
    });

    map.addControl(new mapboxgl.NavigationControl(), 'bottom-right');

    map.on('load', () => {
        deckOverlay = new deck.MapboxOverlay({
            layers: [],
            getTooltip: ({ object }) => {
                if (!object) return null;
                return {
                    html: `<div style="font-family: var(--font-sans); font-size: 13px;">
                        <strong>AQI: ${object.aqi?.toFixed(0) || 'N/A'}</strong>
                    </div>`,
                    style: {
                        background: 'rgba(15,23,42,0.9)',
                        color: '#f1f5f9',
                        border: '1px solid #334155',
                        borderRadius: '4px',
                        padding: '4px 8px',
                    }
                };
            }
        });
        map.addControl(deckOverlay);

        loadAvailableYears();
    });
}

// Event listeners
monthSlider.addEventListener('input', updateDisplay);
yearSelect.addEventListener('change', () => {
    prefetchYear(parseInt(yearSelect.value));
    updateDisplay();
});
playBtn.addEventListener('click', togglePlay);

// Keyboard shortcuts
document.addEventListener('keydown', (e) => {
    if (e.code === 'Space') {
        e.preventDefault();
        togglePlay();
    } else if (e.code === 'ArrowRight') {
        monthSlider.value = Math.min(12, parseInt(monthSlider.value) + 1);
        updateDisplay();
    } else if (e.code === 'ArrowLeft') {
        monthSlider.value = Math.max(1, parseInt(monthSlider.value) - 1);
        updateDisplay();
    }
});

// Init
if (MAPBOX_TOKEN) {
    initMap();
} else {
    currentDateEl.textContent = 'Set MAPBOX_TOKEN in .env to load the map';
}

/**
 * Energy Grid Charts
 * D3.js stacked area chart for fuel mix + donut chart for current mix.
 */

let currentISO = 'CISO';
let currentHours = 24;

// Format hour as "3 PM"
function formatHour(h) {
    if (h === 0) return '12 AM';
    if (h === 12) return '12 PM';
    return h > 12 ? `${h - 12} PM` : `${h} AM`;
}

// Format time window
function formatWindow(start, end) {
    return `${formatHour(start)} - ${formatHour(end)}`;
}

// Carbon intensity color
function carbonColor(value) {
    if (value < 200) return '#22c55e';
    if (value < 400) return '#f59e0b';
    return '#ef4444';
}

// ── Stacked Area Chart ──

function renderStackedArea(records) {
    const container = document.getElementById('fuel-chart');
    container.innerHTML = '';

    if (!records || records.length === 0) {
        container.innerHTML = '<div class="loading-state">No data available</div>';
        return;
    }

    const margin = { top: 10, right: 20, bottom: 30, left: 50 };
    const width = container.clientWidth - margin.left - margin.right;
    const height = container.clientHeight - margin.top - margin.bottom;

    if (width <= 0 || height <= 0) return;

    const svg = d3.select(container)
        .append('svg')
        .attr('width', width + margin.left + margin.right)
        .attr('height', height + margin.top + margin.bottom)
        .append('g')
        .attr('transform', `translate(${margin.left},${margin.top})`);

    // Process data: group by period
    const byPeriod = d3.group(records, d => d.period);
    const fuelTypes = [...new Set(records.map(d => d.fueltype || d['type-name'] || 'OTH'))];

    const timeData = Array.from(byPeriod, ([period, recs]) => {
        const entry = { period: new Date(period) };
        for (const fuel of fuelTypes) {
            const r = recs.find(x => (x.fueltype || x['type-name']) === fuel);
            entry[fuel] = r && r.value ? Math.max(0, +r.value) : 0;
        }
        return entry;
    }).sort((a, b) => a.period - b.period);

    if (timeData.length === 0) return;

    // Stack
    const stack = d3.stack()
        .keys(fuelTypes)
        .order(d3.stackOrderDescending);

    const series = stack(timeData);

    // Scales
    const x = d3.scaleTime()
        .domain(d3.extent(timeData, d => d.period))
        .range([0, width]);

    const y = d3.scaleLinear()
        .domain([0, d3.max(series, s => d3.max(s, d => d[1]))])
        .nice()
        .range([height, 0]);

    // Fuel colors from API data
    const fuelColors = {};
    records.forEach(r => {
        const fuel = r.fueltype || r['type-name'] || 'OTH';
        if (r.fuel_color) fuelColors[fuel] = r.fuel_color;
    });
    const color = d => fuelColors[d] || '#94a3b8';

    // Area generator
    const area = d3.area()
        .x(d => x(d.data.period))
        .y0(d => y(d[0]))
        .y1(d => y(d[1]))
        .curve(d3.curveBasis);

    // Render areas
    svg.selectAll('.fuel-area')
        .data(series)
        .join('path')
        .attr('class', 'fuel-area')
        .attr('d', area)
        .attr('fill', d => color(d.key))
        .attr('opacity', 0.85);

    // X axis
    svg.append('g')
        .attr('transform', `translate(0,${height})`)
        .call(d3.axisBottom(x).ticks(6).tickFormat(d3.timeFormat('%b %d %H:%M')))
        .selectAll('text')
        .style('fill', '#64748b')
        .style('font-size', '10px');

    svg.selectAll('.domain, .tick line').style('stroke', '#334155');

    // Y axis
    svg.append('g')
        .call(d3.axisLeft(y).ticks(5).tickFormat(d => d >= 1000 ? `${d/1000}k` : d))
        .selectAll('text')
        .style('fill', '#64748b')
        .style('font-size', '10px');

    // Y axis label
    svg.append('text')
        .attr('transform', 'rotate(-90)')
        .attr('y', -40)
        .attr('x', -height / 2)
        .attr('text-anchor', 'middle')
        .style('fill', '#64748b')
        .style('font-size', '10px')
        .text('MWh');
}


// ── Donut Chart ──

function renderDonut(fuelBreakdown) {
    const svg = d3.select('#donut-chart');
    svg.selectAll('*').remove();

    const legendEl = document.getElementById('donut-legend');
    legendEl.innerHTML = '';

    if (!fuelBreakdown || Object.keys(fuelBreakdown).length === 0) return;

    const size = 140;
    const radius = size / 2;
    const innerRadius = radius * 0.6;

    svg.attr('width', size).attr('height', size);

    const g = svg.append('g')
        .attr('transform', `translate(${radius},${radius})`);

    const entries = Object.entries(fuelBreakdown)
        .filter(([_, v]) => v.mwh > 0)
        .sort((a, b) => b[1].mwh - a[1].mwh);

    const pie = d3.pie()
        .value(d => d[1].mwh)
        .sort(null);

    const arc = d3.arc()
        .innerRadius(innerRadius)
        .outerRadius(radius - 2);

    g.selectAll('path')
        .data(pie(entries))
        .join('path')
        .attr('d', arc)
        .attr('fill', d => d.data[1].color || '#94a3b8')
        .attr('stroke', '#1e293b')
        .attr('stroke-width', 1);

    // Legend
    const total = entries.reduce((sum, [_, v]) => sum + v.mwh, 0);
    entries.slice(0, 8).forEach(([code, info]) => {
        const pct = ((info.mwh / total) * 100).toFixed(0);
        const item = document.createElement('div');
        item.className = 'legend-item';
        item.innerHTML = `
            <span class="legend-dot" style="background: ${info.color || '#94a3b8'}"></span>
            <span>${info.name || code}</span>
            <span class="legend-value">${pct}%</span>
        `;
        legendEl.appendChild(item);
    });
}


// ── Advice Cards ──

function renderAdvice(advice) {
    const container = document.getElementById('advice-cards');

    if (!advice || !advice.best_windows || advice.best_windows.length === 0) {
        container.innerHTML = '<div class="loading-state" style="height:auto;padding:1rem;">No pattern data</div>';
        return;
    }

    container.innerHTML = advice.best_windows.map((w, i) => `
        <div class="advice-card ${i === 0 ? 'best' : 'good'}">
            <div class="advice-time">${formatWindow(w.start_hour, w.end_hour)}</div>
            <div class="advice-detail">
                ${w.avg_carbon_intensity.toFixed(0)} gCO2/kWh
                &middot; ${w.avg_renewable_pct.toFixed(0)}% renewable
            </div>
            <span class="advice-tag ${i === 0 ? 'best' : 'good'}">
                ${i === 0 ? 'Best time to charge' : 'Good alternative'}
            </span>
        </div>
    `).join('');
}


// ── Data Loading ──

async function loadFuelMix() {
    document.getElementById('fuel-chart').innerHTML =
        '<div class="loading-state"><div class="feed-spinner" style="margin-right:0.5rem;"></div>Loading...</div>';

    try {
        const response = await fetch(`/api/fuel-mix?iso=${currentISO}&hours=${currentHours}`);
        const data = await response.json();

        if (data.error) {
            document.getElementById('fuel-chart').innerHTML =
                `<div class="loading-state">${data.error}</div>`;
            return;
        }

        renderStackedArea(data);

        // Update current mix from latest data
        const latestPeriod = [...new Set(data.map(d => d.period))].sort().pop();
        if (latestPeriod) {
            const latest = data.filter(d => d.period === latestPeriod);
            const breakdown = {};
            let totalMwh = 0;
            latest.forEach(r => {
                const fuel = r.fueltype || r['type-name'] || 'OTH';
                const val = r.value ? Math.max(0, +r.value) : 0;
                breakdown[fuel] = {
                    mwh: val,
                    name: r.fuel_name || fuel,
                    color: r.fuel_color || '#94a3b8',
                };
                totalMwh += val;
            });

            renderDonut(breakdown);

            // Calculate stats
            const fuelTotals = {};
            Object.entries(breakdown).forEach(([k, v]) => { fuelTotals[k] = v.mwh; });

            // We need carbon.py values -- approximate client-side
            const CO2 = {COL:980,NG:410,NUC:12,SUN:45,WND:11,WAT:24,OIL:890,OTH:500,GEO:38,BIO:230,WAS:500,STG:0,PS:0};
            const RENEWABLE = new Set(['SUN','WND','WAT','GEO','BIO']);

            let weightedCO2 = 0;
            let renewableMwh = 0;
            Object.entries(fuelTotals).forEach(([fuel, mwh]) => {
                weightedCO2 += mwh * (CO2[fuel] || 500);
                if (RENEWABLE.has(fuel)) renewableMwh += mwh;
            });

            const carbonIntensity = totalMwh > 0 ? weightedCO2 / totalMwh : 0;
            const renewablePct = totalMwh > 0 ? (renewableMwh / totalMwh) * 100 : 0;

            document.getElementById('carbon-value').textContent = carbonIntensity.toFixed(0);
            document.getElementById('carbon-value').style.color = carbonColor(carbonIntensity);
            document.getElementById('renewable-value').textContent = renewablePct.toFixed(0) + '%';
        }
    } catch (err) {
        console.error('Failed to load fuel mix:', err);
        document.getElementById('fuel-chart').innerHTML =
            `<div class="loading-state">Error: ${err.message}</div>`;
    }
}

async function loadAdvice() {
    try {
        const response = await fetch(`/api/advice?iso=${currentISO}`);
        const data = await response.json();
        if (data.error) {
            document.getElementById('advice-cards').innerHTML =
                `<div class="loading-state" style="height:auto;padding:1rem;">${data.error}</div>`;
            return;
        }
        renderAdvice(data);
    } catch (err) {
        console.error('Failed to load advice:', err);
    }
}

function setISO(iso) {
    currentISO = iso;
    document.querySelectorAll('.iso-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.iso === iso);
    });
    document.getElementById('chart-iso-label').textContent = iso;
    loadFuelMix();
    loadAdvice();
}


// ── Event Listeners ──

document.getElementById('iso-buttons').addEventListener('click', (e) => {
    const btn = e.target.closest('.iso-btn');
    if (btn) setISO(btn.dataset.iso);
});

document.getElementById('hours-select').addEventListener('change', (e) => {
    currentHours = parseInt(e.target.value);
    loadFuelMix();
});

// Resize handler
let resizeTimer;
window.addEventListener('resize', () => {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(loadFuelMix, 250);
});

// Initial load
loadFuelMix();
loadAdvice();

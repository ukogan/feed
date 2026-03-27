/**
 * Permit Pulse Charts
 * D3.js bar chart for city comparison + line chart for monthly trends.
 */

let currentCity = 'nyc';
let currentTypeFilter = 'all';
let allCityData = null;

const TYPE_COLORS = {
    'New Construction': '#10b981',
    'Renovation': '#38bdf8',
    'Demolition': '#ef4444',
    'Sign': '#f59e0b',
    'Other': '#64748b',
};

function formatCurrency(value) {
    if (value >= 1e9) return '$' + (value / 1e9).toFixed(1) + 'B';
    if (value >= 1e6) return '$' + (value / 1e6).toFixed(1) + 'M';
    if (value >= 1e3) return '$' + (value / 1e3).toFixed(0) + 'K';
    return '$' + value.toFixed(0);
}

function formatNumber(n) {
    if (n >= 1e6) return (n / 1e6).toFixed(1) + 'M';
    if (n >= 1e3) return (n / 1e3).toFixed(1) + 'K';
    return n.toString();
}

// ── Bar Chart: Permits by City ──

function renderBarChart(data) {
    const container = document.getElementById('bar-chart');
    container.innerHTML = '';

    const entries = Object.entries(data)
        .filter(([_, v]) => !v.error)
        .map(([key, v]) => ({
            city: key,
            name: v.name,
            count: v.count || 0,
        }))
        .sort((a, b) => b.count - a.count);

    if (entries.length === 0) {
        container.innerHTML = '<div class="loading-state">No data available</div>';
        return;
    }

    const rect = container.getBoundingClientRect();
    const margin = { top: 10, right: 20, bottom: 30, left: 50 };
    const width = rect.width - margin.left - margin.right;
    const height = Math.max(rect.height, 200) - margin.top - margin.bottom;

    const svg = d3.select(container).append('svg')
        .attr('width', rect.width)
        .attr('height', height + margin.top + margin.bottom);

    const g = svg.append('g')
        .attr('transform', `translate(${margin.left},${margin.top})`);

    const x = d3.scaleBand()
        .domain(entries.map(d => d.name))
        .range([0, width])
        .padding(0.3);

    const y = d3.scaleLinear()
        .domain([0, d3.max(entries, d => d.count) * 1.1])
        .range([height, 0]);

    // Bars
    g.selectAll('.bar')
        .data(entries)
        .join('rect')
        .attr('class', 'bar')
        .attr('x', d => x(d.name))
        .attr('y', d => y(d.count))
        .attr('width', x.bandwidth())
        .attr('height', d => height - y(d.count))
        .attr('fill', 'var(--accent)')
        .attr('rx', 3)
        .attr('opacity', 0.85);

    // Bar labels
    g.selectAll('.bar-label')
        .data(entries)
        .join('text')
        .attr('x', d => x(d.name) + x.bandwidth() / 2)
        .attr('y', d => y(d.count) - 5)
        .attr('text-anchor', 'middle')
        .attr('fill', 'var(--text-secondary)')
        .attr('font-size', '0.6875rem')
        .attr('font-family', 'var(--font-mono)')
        .text(d => formatNumber(d.count));

    // X axis
    g.append('g')
        .attr('transform', `translate(0,${height})`)
        .call(d3.axisBottom(x).tickSize(0))
        .selectAll('text')
        .attr('fill', 'var(--text-muted)')
        .attr('font-size', '0.625rem');

    g.selectAll('.domain').attr('stroke', 'var(--border)');
    g.selectAll('.tick line').attr('stroke', 'var(--border)');

    // Y axis
    g.append('g')
        .call(d3.axisLeft(y).ticks(5).tickFormat(formatNumber).tickSize(-width))
        .selectAll('text')
        .attr('fill', 'var(--text-muted)')
        .attr('font-size', '0.625rem');

    g.selectAll('.tick line').attr('stroke', 'var(--border)').attr('opacity', 0.3);
    g.selectAll('.domain').remove();
}

// ── Trend Line Chart ──

function renderTrendChart(monthlyData, cityName) {
    const container = document.getElementById('trend-chart');
    container.innerHTML = '';

    if (!monthlyData || monthlyData.length === 0) {
        container.innerHTML = '<div class="loading-state">No trend data</div>';
        return;
    }

    const rect = container.getBoundingClientRect();
    const margin = { top: 10, right: 20, bottom: 30, left: 50 };
    const width = rect.width - margin.left - margin.right;
    const height = Math.max(rect.height, 180) - margin.top - margin.bottom;

    const svg = d3.select(container).append('svg')
        .attr('width', rect.width)
        .attr('height', height + margin.top + margin.bottom);

    const g = svg.append('g')
        .attr('transform', `translate(${margin.left},${margin.top})`);

    const parseMonth = d3.timeParse('%Y-%m');
    const data = monthlyData.map(d => ({
        date: parseMonth(d.month),
        count: d.count,
        value: d.value,
    })).filter(d => d.date);

    const x = d3.scaleTime()
        .domain(d3.extent(data, d => d.date))
        .range([0, width]);

    const y = d3.scaleLinear()
        .domain([0, d3.max(data, d => d.count) * 1.15])
        .range([height, 0]);

    // Area
    const area = d3.area()
        .x(d => x(d.date))
        .y0(height)
        .y1(d => y(d.count))
        .curve(d3.curveMonotoneX);

    g.append('path')
        .datum(data)
        .attr('d', area)
        .attr('fill', 'var(--accent)')
        .attr('opacity', 0.15);

    // Line
    const line = d3.line()
        .x(d => x(d.date))
        .y(d => y(d.count))
        .curve(d3.curveMonotoneX);

    g.append('path')
        .datum(data)
        .attr('d', line)
        .attr('fill', 'none')
        .attr('stroke', 'var(--accent)')
        .attr('stroke-width', 2);

    // Dots
    g.selectAll('.dot')
        .data(data)
        .join('circle')
        .attr('cx', d => x(d.date))
        .attr('cy', d => y(d.count))
        .attr('r', 3)
        .attr('fill', 'var(--accent)');

    // X axis
    g.append('g')
        .attr('transform', `translate(0,${height})`)
        .call(d3.axisBottom(x).ticks(6).tickFormat(d3.timeFormat('%b %y')).tickSize(0))
        .selectAll('text')
        .attr('fill', 'var(--text-muted)')
        .attr('font-size', '0.625rem');

    // Y axis
    g.append('g')
        .call(d3.axisLeft(y).ticks(5).tickFormat(formatNumber).tickSize(-width))
        .selectAll('text')
        .attr('fill', 'var(--text-muted)')
        .attr('font-size', '0.625rem');

    g.selectAll('.tick line').attr('stroke', 'var(--border)').attr('opacity', 0.3);
    g.selectAll('.domain').remove();
}

// ── Sidebar Updates ──

function updateStats(stats) {
    document.getElementById('total-permits').textContent = formatNumber(stats.total_permits);
    document.getElementById('avg-value').textContent = formatCurrency(stats.avg_value);
    document.getElementById('total-value').textContent = formatCurrency(stats.total_value);

    const yoyEl = document.getElementById('yoy-change');
    if (stats.yoy_change !== null && stats.yoy_change !== undefined) {
        const sign = stats.yoy_change >= 0 ? '+' : '';
        yoyEl.textContent = sign + stats.yoy_change + '%';
        yoyEl.style.color = stats.yoy_change >= 0 ? '#22c55e' : '#ef4444';
    } else {
        yoyEl.textContent = 'N/A';
        yoyEl.style.color = 'var(--text-muted)';
    }
}

function updateTypeBreakdown(byType) {
    const el = document.getElementById('type-breakdown');
    if (!byType || Object.keys(byType).length === 0) {
        el.innerHTML = '<span style="color:var(--text-muted);font-size:0.8125rem;">No data</span>';
        return;
    }

    el.innerHTML = Object.entries(byType).map(([type, count]) => `
        <div class="type-row">
            <span class="type-dot" style="background:${TYPE_COLORS[type] || '#64748b'}"></span>
            <span class="type-name">${type}</span>
            <span class="type-count">${formatNumber(count)}</span>
        </div>
    `).join('');
}

function updateHotZones(zones) {
    const el = document.getElementById('hot-zones');
    if (!zones || zones.length === 0) {
        el.innerHTML = '<span style="color:var(--text-muted);font-size:0.8125rem;">No data</span>';
        return;
    }

    el.innerHTML = zones.map((z, i) => `
        <div class="hot-zone-item">
            <span style="color:var(--text-muted);font-size:0.6875rem;margin-right:0.5rem;">${i + 1}</span>
            <span class="hot-zone-name">${z.neighborhood}</span>
            <span class="hot-zone-count">${formatNumber(z.count)}</span>
        </div>
    `).join('');
}

// ── Data Loading ──

async function loadAllCities() {
    try {
        const resp = await fetch('/api/permits/all?limit=500&months=12');
        const data = await resp.json();
        allCityData = data;
        renderBarChart(data);
    } catch (err) {
        console.error('Failed to load all cities:', err);
        document.getElementById('bar-chart').innerHTML =
            '<div class="loading-state">Failed to load data</div>';
    }
}

async function loadCityAnalytics(city) {
    try {
        const resp = await fetch(`/api/analytics?city=${city}&months=12`);
        const data = await resp.json();

        if (data.error) {
            console.error('API error:', data.error);
            return;
        }

        updateStats(data.stats);
        updateTypeBreakdown(data.by_type);
        updateHotZones(data.hot_zones);
        renderTrendChart(data.monthly, data.city_name);
        document.getElementById('chart-city-label').textContent = data.city_name;
    } catch (err) {
        console.error('Failed to load analytics:', err);
    }
}

// ── Init ──

document.addEventListener('DOMContentLoaded', () => {
    loadAllCities();
    loadCityAnalytics(currentCity);

    // City buttons
    document.getElementById('city-buttons').addEventListener('click', (e) => {
        const btn = e.target.closest('.city-btn');
        if (!btn) return;

        document.querySelectorAll('.city-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');

        const city = btn.dataset.city;
        if (city === 'all') {
            currentCity = 'all';
            document.getElementById('chart-city-label').textContent = 'All Cities';
            // Show combined stats from allCityData
            if (allCityData) {
                let totalPermits = 0;
                let totalValue = 0;
                Object.values(allCityData).forEach(v => {
                    if (v.stats) {
                        totalPermits += v.stats.total_permits;
                        totalValue += v.stats.total_value;
                    }
                });
                updateStats({
                    total_permits: totalPermits,
                    total_value: totalValue,
                    avg_value: totalPermits > 0 ? totalValue / totalPermits : 0,
                    yoy_change: null,
                });
            }
        } else {
            currentCity = city;
            loadCityAnalytics(city);
        }
    });

    // Type filter buttons
    document.getElementById('type-filters').addEventListener('click', (e) => {
        const btn = e.target.closest('.filter-btn');
        if (!btn) return;

        document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        currentTypeFilter = btn.dataset.type;
        // Re-render with filter applied if needed
    });
});

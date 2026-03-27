/**
 * Court Flow App
 * Search, court activity heatmap, filing timeline, trending topics.
 */

let currentQuery = 'antitrust';
let currentCourt = '';

// ── Helpers ──

function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str || '';
    return div.innerHTML;
}

// ── Court Activity Bar Chart (heatmap-style) ──

function renderCourtChart(byCourt) {
    const container = document.getElementById('heatmap-chart');
    container.innerHTML = '';

    if (!byCourt || byCourt.length === 0) {
        container.innerHTML = '<div class="loading-state">No court data</div>';
        return;
    }

    const rect = container.getBoundingClientRect();
    const margin = { top: 10, right: 20, bottom: 30, left: 140 };
    const width = rect.width - margin.left - margin.right;
    const height = Math.max(rect.height, 200) - margin.top - margin.bottom;

    const data = byCourt.slice(0, 10);

    const svg = d3.select(container).append('svg')
        .attr('width', rect.width)
        .attr('height', height + margin.top + margin.bottom);

    const g = svg.append('g')
        .attr('transform', `translate(${margin.left},${margin.top})`);

    const y = d3.scaleBand()
        .domain(data.map(d => d.court))
        .range([0, height])
        .padding(0.25);

    const x = d3.scaleLinear()
        .domain([0, d3.max(data, d => d.count) * 1.1])
        .range([0, width]);

    // Color scale
    const colorScale = d3.scaleSequential(d3.interpolateYlOrRd)
        .domain([0, d3.max(data, d => d.count)]);

    // Bars
    g.selectAll('.bar')
        .data(data)
        .join('rect')
        .attr('x', 0)
        .attr('y', d => y(d.court))
        .attr('width', d => x(d.count))
        .attr('height', y.bandwidth())
        .attr('fill', d => colorScale(d.count))
        .attr('rx', 3)
        .attr('opacity', 0.85);

    // Count labels
    g.selectAll('.bar-label')
        .data(data)
        .join('text')
        .attr('x', d => x(d.count) + 5)
        .attr('y', d => y(d.court) + y.bandwidth() / 2 + 4)
        .attr('fill', 'var(--text-secondary)')
        .attr('font-size', '0.6875rem')
        .attr('font-family', 'var(--font-mono)')
        .text(d => d.count);

    // Y axis (court names)
    g.append('g')
        .call(d3.axisLeft(y).tickSize(0))
        .selectAll('text')
        .attr('fill', 'var(--text-secondary)')
        .attr('font-size', '0.625rem');

    g.selectAll('.domain').remove();
}

// ── Filing Timeline ──

function renderTimeline(byDate) {
    const container = document.getElementById('timeline-chart');
    container.innerHTML = '';

    if (!byDate || byDate.length === 0) {
        container.innerHTML = '<div class="loading-state">No timeline data</div>';
        return;
    }

    const rect = container.getBoundingClientRect();
    const margin = { top: 10, right: 20, bottom: 30, left: 40 };
    const width = rect.width - margin.left - margin.right;
    const height = Math.max(rect.height, 180) - margin.top - margin.bottom;

    const svg = d3.select(container).append('svg')
        .attr('width', rect.width)
        .attr('height', height + margin.top + margin.bottom);

    const g = svg.append('g')
        .attr('transform', `translate(${margin.left},${margin.top})`);

    const parseDate = d3.timeParse('%Y-%m-%d');
    const data = byDate.map(d => ({
        date: parseDate(d.date),
        count: d.count,
    })).filter(d => d.date);

    if (data.length === 0) {
        container.innerHTML = '<div class="loading-state">No valid dates</div>';
        return;
    }

    const x = d3.scaleTime()
        .domain(d3.extent(data, d => d.date))
        .range([0, width]);

    const y = d3.scaleLinear()
        .domain([0, d3.max(data, d => d.count) * 1.2])
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
        .call(d3.axisBottom(x).ticks(6).tickFormat(d3.timeFormat('%b %d')).tickSize(0))
        .selectAll('text')
        .attr('fill', 'var(--text-muted)')
        .attr('font-size', '0.625rem');

    // Y axis
    g.append('g')
        .call(d3.axisLeft(y).ticks(5).tickSize(-width))
        .selectAll('text')
        .attr('fill', 'var(--text-muted)')
        .attr('font-size', '0.625rem');

    g.selectAll('.tick line').attr('stroke', 'var(--border)').attr('opacity', 0.3);
    g.selectAll('.domain').remove();
}

// ── Sidebar Updates ──

function updateStats(stats) {
    document.getElementById('total-filings').textContent = stats.total_filings;
    document.getElementById('courts-count').textContent = stats.courts_involved;
    document.getElementById('per-day').textContent = stats.filings_per_day;

    const dateRange = stats.date_range;
    if (dateRange) {
        document.getElementById('date-range').textContent =
            dateRange.start.slice(5) + ' to ' + dateRange.end.slice(5);
    } else {
        document.getElementById('date-range').textContent = '--';
    }
}

function updateCourtBreakdown(byCourt) {
    const el = document.getElementById('court-breakdown');
    if (!byCourt || byCourt.length === 0) {
        el.innerHTML = '<span style="color:var(--text-muted);font-size:0.8125rem;">No data</span>';
        return;
    }

    const max = Math.max(...byCourt.map(c => c.count));

    el.innerHTML = byCourt.slice(0, 8).map(c => `
        <div class="court-row">
            <span class="court-name">${escapeHtml(c.court)}</span>
            <div class="court-bar-bg">
                <div class="court-bar" style="width:${(c.count / max * 100).toFixed(0)}%"></div>
            </div>
            <span class="court-count">${c.count}</span>
        </div>
    `).join('');
}

function updateResults(results) {
    const el = document.getElementById('results-list');
    if (!results || results.length === 0) {
        el.innerHTML = '<span style="color:var(--text-muted);font-size:0.8125rem;">No results found</span>';
        return;
    }

    el.innerHTML = results.map(r => {
        const url = r.absolute_url
            ? `https://www.courtlistener.com${r.absolute_url}`
            : '#';
        return `
            <div class="result-item">
                <div class="result-case-name">
                    <a href="${escapeHtml(url)}" target="_blank" rel="noopener">${escapeHtml(r.case_name)}</a>
                </div>
                <div class="result-meta">
                    <span>${escapeHtml(r.court)}</span>
                    <span>${escapeHtml(r.date_filed)}</span>
                    ${r.judge ? `<span>Judge: ${escapeHtml(r.judge)}</span>` : ''}
                </div>
                ${r.snippet ? `<div class="result-snippet">${r.snippet}</div>` : ''}
            </div>
        `;
    }).join('');
}

// ── Trending Topics ──

async function loadTrending() {
    try {
        const resp = await fetch('/api/trending?days=30');
        const data = await resp.json();
        renderTrending(data.trending);
    } catch (err) {
        console.error('Failed to load trending:', err);
        document.getElementById('trending-list').innerHTML =
            '<span style="color:var(--text-muted);font-size:0.8125rem;">Failed to load</span>';
    }
}

function renderTrending(trending) {
    const el = document.getElementById('trending-list');
    if (!trending || trending.length === 0) {
        el.innerHTML = '<span style="color:var(--text-muted);font-size:0.8125rem;">No trending data</span>';
        return;
    }

    el.innerHTML = trending.map((t, i) => `
        <div class="trending-item" data-topic="${escapeHtml(t.topic)}">
            <span class="trending-rank">${i + 1}</span>
            <span class="trending-topic">${escapeHtml(t.topic)}</span>
            <span class="trending-count">${t.count}</span>
        </div>
    `).join('');
}

// ── Search ──

async function doSearch(query, court) {
    document.getElementById('query-label').textContent = query;

    // Show loading
    document.getElementById('heatmap-chart').innerHTML =
        '<div class="loading-state"><div class="feed-spinner" style="margin-right:0.5rem;"></div>Searching...</div>';
    document.getElementById('timeline-chart').innerHTML =
        '<div class="loading-state"><div class="feed-spinner" style="margin-right:0.5rem;"></div>Loading...</div>';
    document.getElementById('results-list').innerHTML =
        '<div class="loading-state" style="height:auto;padding:1rem;"><div class="feed-spinner" style="margin-right:0.5rem;"></div>Searching...</div>';

    try {
        const params = new URLSearchParams({ q: query, limit: 20 });
        if (court) params.set('court', court);

        const resp = await fetch(`/api/search?${params}`);
        const data = await resp.json();

        if (data.error) {
            console.error('Search error:', data.error);
            document.getElementById('results-list').innerHTML =
                `<span style="color:#ef4444;font-size:0.8125rem;">Error: ${escapeHtml(data.error)}</span>`;
            return;
        }

        updateStats(data.stats);
        updateCourtBreakdown(data.by_court);
        renderCourtChart(data.by_court);
        renderTimeline(data.by_date);
        updateResults(data.results);
    } catch (err) {
        console.error('Search failed:', err);
        document.getElementById('results-list').innerHTML =
            '<span style="color:#ef4444;font-size:0.8125rem;">Search failed. CourtListener may be rate-limiting.</span>';
    }
}

// ── Init ──

document.addEventListener('DOMContentLoaded', () => {
    doSearch(currentQuery, currentCourt);
    loadTrending();

    // Search button
    document.getElementById('search-btn').addEventListener('click', () => {
        currentQuery = document.getElementById('search-input').value.trim() || 'antitrust';
        currentCourt = document.getElementById('court-select').value;
        doSearch(currentQuery, currentCourt);
    });

    // Enter key in search
    document.getElementById('search-input').addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            currentQuery = e.target.value.trim() || 'antitrust';
            currentCourt = document.getElementById('court-select').value;
            doSearch(currentQuery, currentCourt);
        }
    });

    // Trending topic click
    document.getElementById('trending-list').addEventListener('click', (e) => {
        const item = e.target.closest('.trending-item');
        if (!item) return;
        const topic = item.dataset.topic;
        document.getElementById('search-input').value = topic;
        currentQuery = topic;
        doSearch(currentQuery, currentCourt);
    });
});

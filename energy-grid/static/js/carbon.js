/**
 * Personal Carbon Accountant
 * Interactive usage editor + D3 charts for carbon analysis.
 */

// ── State ──

let usageProfile = [];
let presets = {};
let analysisResult = null;

// ── Presets ──

async function loadPresets() {
    try {
        const response = await fetch('/api/carbon-account/presets');
        presets = await response.json();
        applyPreset('average_household');
    } catch (err) {
        console.error('Failed to load presets:', err);
        // Fallback default
        usageProfile = Array(24).fill(1.25);
        renderUsageBars();
    }
}

function applyPreset(key) {
    if (key === 'custom') return;
    const preset = presets[key];
    if (!preset) return;
    usageProfile = [...preset.hourly_kwh];
    renderUsageBars();
}

// ── Format helpers ──

function formatHour(h) {
    if (h === 0) return '12a';
    if (h === 12) return '12p';
    return h > 12 ? `${h - 12}p` : `${h}a`;
}

function formatHourFull(h) {
    if (h === 0) return '12 AM';
    if (h === 12) return '12 PM';
    return h > 12 ? `${h - 12} PM` : `${h} AM`;
}

// ── Usage Bar Editor ──

function renderUsageBars() {
    const container = document.getElementById('usage-bars');
    container.innerHTML = '';

    const maxKwh = Math.max(...usageProfile, 1);

    usageProfile.forEach((kwh, hour) => {
        const wrapper = document.createElement('div');
        wrapper.className = 'usage-bar-wrapper';
        wrapper.dataset.hour = hour;

        const barHeight = (kwh / maxKwh) * 100;
        const bar = document.createElement('div');
        bar.className = 'usage-bar';
        bar.style.height = `${barHeight}%`;

        const label = document.createElement('span');
        label.className = 'usage-bar-label';
        label.textContent = hour % 3 === 0 ? formatHour(hour) : '';

        const valueLabel = document.createElement('span');
        valueLabel.className = 'usage-bar-value';
        valueLabel.textContent = kwh.toFixed(1);

        wrapper.appendChild(valueLabel);
        wrapper.appendChild(bar);
        wrapper.appendChild(label);
        container.appendChild(wrapper);
    });

    updateUsageTotal();
    setupDragHandlers();
}

function updateUsageTotal() {
    const total = usageProfile.reduce((a, b) => a + b, 0);
    document.getElementById('usage-total').textContent = `${total.toFixed(1)} kWh`;
}

function setupDragHandlers() {
    const container = document.getElementById('usage-bars');
    let isDragging = false;
    let activeWrapper = null;
    let startY = 0;
    let startKwh = 0;

    function onPointerDown(e) {
        const wrapper = e.target.closest('.usage-bar-wrapper');
        if (!wrapper) return;
        isDragging = true;
        activeWrapper = wrapper;
        activeWrapper.classList.add('dragging');
        startY = e.clientY;
        startKwh = usageProfile[parseInt(wrapper.dataset.hour)];
        e.preventDefault();
    }

    function onPointerMove(e) {
        if (!isDragging || !activeWrapper) return;
        const hour = parseInt(activeWrapper.dataset.hour);
        const deltaY = startY - e.clientY;
        const sensitivity = 0.03;
        const newKwh = Math.max(0, Math.min(10, startKwh + deltaY * sensitivity));
        usageProfile[hour] = Math.round(newKwh * 10) / 10;

        // Update visual
        const maxKwh = Math.max(...usageProfile, 1);
        const bar = activeWrapper.querySelector('.usage-bar');
        bar.style.height = `${(usageProfile[hour] / maxKwh) * 100}%`;

        const valueLabel = activeWrapper.querySelector('.usage-bar-value');
        valueLabel.textContent = usageProfile[hour].toFixed(1);

        // Re-render all bar heights since max may have changed
        document.querySelectorAll('.usage-bar-wrapper').forEach(w => {
            const h = parseInt(w.dataset.hour);
            const b = w.querySelector('.usage-bar');
            b.style.height = `${(usageProfile[h] / maxKwh) * 100}%`;
        });

        updateUsageTotal();

        // Switch to custom preset
        document.getElementById('profile-preset').value = 'custom';
    }

    function onPointerUp() {
        if (activeWrapper) activeWrapper.classList.remove('dragging');
        isDragging = false;
        activeWrapper = null;
    }

    container.addEventListener('pointerdown', onPointerDown);
    document.addEventListener('pointermove', onPointerMove);
    document.addEventListener('pointerup', onPointerUp);
}

// ── Analysis ──

async function runAnalysis() {
    const iso = document.getElementById('carbon-iso').value;
    const periodDays = parseInt(document.getElementById('period-select').value);
    const btn = document.getElementById('analyze-btn');
    const resultsPanel = document.getElementById('results-panel');

    btn.disabled = true;
    btn.textContent = 'Analyzing...';
    resultsPanel.innerHTML = '<div class="loading-state"><div class="feed-spinner" style="margin-right:0.5rem;"></div>Fetching grid data and calculating emissions...</div>';

    try {
        const response = await fetch('/api/carbon-account', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                iso: iso,
                usage_profile: usageProfile,
                period_days: periodDays,
            }),
        });

        const data = await response.json();

        if (data.error || data.carbon?.error) {
            resultsPanel.innerHTML = `<div class="loading-state">${data.error || data.carbon.error}</div>`;
            return;
        }

        analysisResult = data;
        renderResults(data);
    } catch (err) {
        console.error('Analysis failed:', err);
        resultsPanel.innerHTML = `<div class="loading-state">Error: ${err.message}</div>`;
    } finally {
        btn.disabled = false;
        btn.textContent = 'Analyze Carbon Footprint';
    }
}

// ── Results Rendering ──

function renderResults(data) {
    const panel = document.getElementById('results-panel');
    const carbon = data.carbon;
    const opt = data.optimization;

    const vsAvgClass = carbon.vs_average_pct > 0 ? 'stat-positive' : 'stat-negative';
    const vsAvgSign = carbon.vs_average_pct > 0 ? '+' : '';
    const periodLabel = carbon.period_days === 1 ? 'today' : `this ${carbon.period_days}-day period`;

    panel.innerHTML = `
        <div class="big-stats">
            <div class="big-stat">
                <div class="big-stat-value" style="color: ${carbonColor(carbon.avg_grid_carbon)};">
                    ${carbon.period_co2_kg.toFixed(1)}<span class="big-stat-unit"> kg</span>
                </div>
                <div class="big-stat-label">CO2 produced ${periodLabel}</div>
            </div>
            <div class="big-stat">
                <div class="big-stat-value" style="color: var(--accent);">
                    ${carbon.green_kwh_pct.toFixed(0)}<span class="big-stat-unit">%</span>
                </div>
                <div class="big-stat-label">Green electricity</div>
            </div>
            <div class="big-stat">
                <div class="big-stat-value ${vsAvgClass}">
                    ${vsAvgSign}${carbon.vs_average_pct.toFixed(1)}<span class="big-stat-unit">%</span>
                </div>
                <div class="big-stat-label">vs. flat usage baseline</div>
                <div class="big-stat-sub">${carbon.vs_average_pct > 0 ? 'Dirtier than average' : 'Cleaner than average'}</div>
            </div>
            <div class="big-stat">
                <div class="big-stat-value" style="color: #22c55e;">
                    ${opt.co2_saved_kg.toFixed(1)}<span class="big-stat-unit"> kg</span>
                </div>
                <div class="big-stat-label">Potential CO2 savings</div>
                <div class="big-stat-sub">${opt.co2_saved_pct.toFixed(1)}% reduction possible</div>
            </div>
        </div>

        <div class="chart-row">
            <div class="chart-card">
                <div class="chart-card-title">Your Electricity: Green vs. Brown (24h)</div>
                <div id="green-brown-chart"></div>
            </div>
            <div class="chart-card">
                <div class="chart-card-title">Carbon Curve: Actual vs. Optimized</div>
                <div id="carbon-curve-chart"></div>
            </div>
        </div>

        <div class="opt-card">
            <div class="opt-card-header">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#22c55e" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2v4"/><path d="m6.34 6.34 2.83 2.83"/><path d="M2 12h4"/><path d="m6.34 17.66 2.83-2.83"/><path d="M12 18v4"/><path d="m17.66 17.66-2.83-2.83"/><path d="M18 12h4"/><path d="m17.66 6.34-2.83 2.83"/></svg>
                <span class="opt-card-title">Optimization Potential</span>
            </div>
            <div class="opt-summary">
                If you shifted your flexible load to the greenest hours, you could save
                <span class="opt-highlight">${opt.co2_saved_kg.toFixed(1)} kg CO2</span>
                over ${carbon.period_days} days
                (a <span class="opt-highlight">${opt.co2_saved_pct.toFixed(1)}%</span> reduction).
                Estimated cost impact: <span class="opt-highlight">$${opt.estimated_cost_saved.toFixed(2)}</span>.
            </div>
            <div style="margin-top: 0.75rem;">
                <span class="form-label">Greenest hours</span>
                <div class="opt-hours" style="margin-top: 0.25rem;">
                    ${opt.greenest_hours.map(h => `<span class="opt-hour-tag">${formatHourFull(h)}</span>`).join('')}
                </div>
            </div>
            <div style="margin-top: 0.5rem;">
                <span class="form-label">Dirtiest hours</span>
                <div class="opt-hours" style="margin-top: 0.25rem;">
                    ${opt.dirtiest_hours.map(h => `<span class="opt-hour-tag dirty">${formatHourFull(h)}</span>`).join('')}
                </div>
            </div>
        </div>
    `;

    renderGreenBrownChart(carbon.hourly_breakdown);
    renderCarbonCurveChart(carbon.hourly_breakdown, opt.optimized_hourly);
}

function carbonColor(value) {
    if (value < 200) return '#22c55e';
    if (value < 400) return '#f59e0b';
    return '#ef4444';
}

// ── D3: Green/Brown Stacked Bar Chart ──

function renderGreenBrownChart(hourlyBreakdown) {
    const container = document.getElementById('green-brown-chart');
    container.innerHTML = '';

    const margin = { top: 10, right: 10, bottom: 28, left: 40 };
    const width = container.clientWidth - margin.left - margin.right;
    const height = 220 - margin.top - margin.bottom;

    if (width <= 0) return;

    const svg = d3.select(container)
        .append('svg')
        .attr('width', width + margin.left + margin.right)
        .attr('height', height + margin.top + margin.bottom)
        .append('g')
        .attr('transform', `translate(${margin.left},${margin.top})`);

    const x = d3.scaleBand()
        .domain(hourlyBreakdown.map(d => d.hour))
        .range([0, width])
        .padding(0.15);

    const maxKwh = d3.max(hourlyBreakdown, d => d.kwh) || 1;
    const y = d3.scaleLinear()
        .domain([0, maxKwh])
        .nice()
        .range([height, 0]);

    // Brown bars (bottom portion)
    svg.selectAll('.bar-brown')
        .data(hourlyBreakdown)
        .join('rect')
        .attr('class', 'bar-brown')
        .attr('x', d => x(d.hour))
        .attr('y', d => y(d.kwh))
        .attr('width', x.bandwidth())
        .attr('height', d => height - y(d.brown_kwh))
        .attr('fill', '#78716c')
        .attr('rx', 1);

    // Green bars (stacked on top of brown)
    svg.selectAll('.bar-green')
        .data(hourlyBreakdown)
        .join('rect')
        .attr('class', 'bar-green')
        .attr('x', d => x(d.hour))
        .attr('y', d => y(d.kwh))
        .attr('width', x.bandwidth())
        .attr('height', d => height - y(d.green_kwh))
        .attr('fill', '#22c55e')
        .attr('rx', 1);

    // X axis
    svg.append('g')
        .attr('transform', `translate(0,${height})`)
        .call(d3.axisBottom(x).tickValues(hourlyBreakdown.filter(d => d.hour % 3 === 0).map(d => d.hour)).tickFormat(h => formatHour(h)))
        .selectAll('text')
        .style('fill', '#64748b')
        .style('font-size', '9px');

    svg.selectAll('.domain, .tick line').style('stroke', '#334155');

    // Y axis
    svg.append('g')
        .call(d3.axisLeft(y).ticks(4).tickFormat(d => `${d} kWh`))
        .selectAll('text')
        .style('fill', '#64748b')
        .style('font-size', '9px');

    // Legend
    const legend = svg.append('g')
        .attr('transform', `translate(${width - 110}, 0)`);

    legend.append('rect').attr('width', 10).attr('height', 10).attr('fill', '#22c55e').attr('rx', 2);
    legend.append('text').attr('x', 14).attr('y', 9).text('Green').style('fill', '#94a3b8').style('font-size', '10px');

    legend.append('rect').attr('y', 14).attr('width', 10).attr('height', 10).attr('fill', '#78716c').attr('rx', 2);
    legend.append('text').attr('x', 14).attr('y', 23).text('Fossil').style('fill', '#94a3b8').style('font-size', '10px');

    // Tooltip on hover
    const tooltip = d3.select(container)
        .append('div')
        .style('position', 'absolute')
        .style('pointer-events', 'none')
        .style('background', '#1e293b')
        .style('border', '1px solid #334155')
        .style('border-radius', '0.375rem')
        .style('padding', '0.375rem 0.625rem')
        .style('font-size', '0.6875rem')
        .style('color', '#f1f5f9')
        .style('opacity', 0)
        .style('z-index', 10);

    // Invisible hover rects
    svg.selectAll('.hover-rect')
        .data(hourlyBreakdown)
        .join('rect')
        .attr('x', d => x(d.hour))
        .attr('y', 0)
        .attr('width', x.bandwidth())
        .attr('height', height)
        .attr('fill', 'transparent')
        .on('mouseenter', (event, d) => {
            tooltip
                .html(`<strong>${formatHourFull(d.hour)}</strong><br>
                    ${d.kwh.toFixed(2)} kWh total<br>
                    <span style="color:#22c55e">${d.green_kwh.toFixed(2)} kWh green</span><br>
                    <span style="color:#78716c">${d.brown_kwh.toFixed(2)} kWh fossil</span><br>
                    ${d.carbon_intensity.toFixed(0)} gCO2/kWh`)
                .style('opacity', 1);
        })
        .on('mousemove', (event) => {
            const containerRect = container.getBoundingClientRect();
            tooltip
                .style('left', `${event.clientX - containerRect.left + 12}px`)
                .style('top', `${event.clientY - containerRect.top - 10}px`);
        })
        .on('mouseleave', () => {
            tooltip.style('opacity', 0);
        });
}

// ── D3: Carbon Curve (Actual vs Optimized) ──

function renderCarbonCurveChart(actualHourly, optimizedHourly) {
    const container = document.getElementById('carbon-curve-chart');
    container.innerHTML = '';

    const margin = { top: 10, right: 10, bottom: 28, left: 50 };
    const width = container.clientWidth - margin.left - margin.right;
    const height = 220 - margin.top - margin.bottom;

    if (width <= 0) return;

    const svg = d3.select(container)
        .append('svg')
        .attr('width', width + margin.left + margin.right)
        .attr('height', height + margin.top + margin.bottom)
        .append('g')
        .attr('transform', `translate(${margin.left},${margin.top})`);

    const x = d3.scaleLinear()
        .domain([0, 23])
        .range([0, width]);

    const maxCO2 = d3.max([
        ...actualHourly.map(d => d.co2_g),
        ...optimizedHourly.map(d => d.co2_g),
    ]) || 1;

    const y = d3.scaleLinear()
        .domain([0, maxCO2])
        .nice()
        .range([height, 0]);

    // Actual area (filled, reddish)
    const actualArea = d3.area()
        .x(d => x(d.hour))
        .y0(height)
        .y1(d => y(d.co2_g))
        .curve(d3.curveMonotoneX);

    svg.append('path')
        .datum(actualHourly)
        .attr('d', actualArea)
        .attr('fill', 'rgba(245, 158, 11, 0.2)')
        .attr('stroke', '#f59e0b')
        .attr('stroke-width', 2);

    // Optimized area (filled, greenish)
    const optimizedArea = d3.area()
        .x(d => x(d.hour))
        .y0(height)
        .y1(d => y(d.co2_g))
        .curve(d3.curveMonotoneX);

    svg.append('path')
        .datum(optimizedHourly)
        .attr('d', optimizedArea)
        .attr('fill', 'rgba(34, 197, 94, 0.15)')
        .attr('stroke', '#22c55e')
        .attr('stroke-width', 2)
        .attr('stroke-dasharray', '4,3');

    // X axis
    svg.append('g')
        .attr('transform', `translate(0,${height})`)
        .call(d3.axisBottom(x).ticks(8).tickFormat(h => formatHour(h)))
        .selectAll('text')
        .style('fill', '#64748b')
        .style('font-size', '9px');

    svg.selectAll('.domain, .tick line').style('stroke', '#334155');

    // Y axis
    svg.append('g')
        .call(d3.axisLeft(y).ticks(4).tickFormat(d => `${d.toFixed(0)}g`))
        .selectAll('text')
        .style('fill', '#64748b')
        .style('font-size', '9px');

    // Y label
    svg.append('text')
        .attr('transform', 'rotate(-90)')
        .attr('y', -40)
        .attr('x', -height / 2)
        .attr('text-anchor', 'middle')
        .style('fill', '#64748b')
        .style('font-size', '9px')
        .text('gCO2');

    // Legend
    const legend = svg.append('g')
        .attr('transform', `translate(${width - 120}, 0)`);

    legend.append('line').attr('x1', 0).attr('y1', 5).attr('x2', 16).attr('y2', 5)
        .attr('stroke', '#f59e0b').attr('stroke-width', 2);
    legend.append('text').attr('x', 20).attr('y', 9).text('Actual')
        .style('fill', '#94a3b8').style('font-size', '10px');

    legend.append('line').attr('x1', 0).attr('y1', 19).attr('x2', 16).attr('y2', 19)
        .attr('stroke', '#22c55e').attr('stroke-width', 2).attr('stroke-dasharray', '4,3');
    legend.append('text').attr('x', 20).attr('y', 23).text('Optimized')
        .style('fill', '#94a3b8').style('font-size', '10px');
}

// ── Event Listeners ──

document.getElementById('profile-preset').addEventListener('change', (e) => {
    applyPreset(e.target.value);
});

document.getElementById('analyze-btn').addEventListener('click', runAnalysis);

// Resize handler
let resizeTimer;
window.addEventListener('resize', () => {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(() => {
        if (analysisResult) renderResults(analysisResult);
    }, 250);
});

// Initial load
loadPresets();

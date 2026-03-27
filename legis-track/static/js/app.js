/**
 * Legis Track App
 * Member lookup, trades table, bills list, timeline, and suspicious trade flagging.
 */

let selectedMemberId = '';

// ── Helpers ──

function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

// ── Member List ──

async function loadMembers(query) {
    const url = query ? `/api/members?q=${encodeURIComponent(query)}` : '/api/members';
    try {
        const resp = await fetch(url);
        const data = await resp.json();
        renderMemberList(data.members);
    } catch (err) {
        console.error('Failed to load members:', err);
    }
}

function renderMemberList(members) {
    const el = document.getElementById('member-list');
    if (!members || members.length === 0) {
        el.innerHTML = '<span style="color:var(--text-muted);font-size:0.8125rem;padding:0.5rem;">No members found</span>';
        return;
    }

    el.innerHTML = members.map(m => `
        <div class="member-item${m.id === selectedMemberId ? ' active' : ''}"
             data-member-id="${escapeHtml(m.id)}">
            <span class="party-badge ${escapeHtml(m.party)}">${escapeHtml(m.party)}</span>
            <span class="member-name">${escapeHtml(m.name)}</span>
            <span class="member-state">${escapeHtml(m.state)}</span>
        </div>
    `).join('');
}

// ── Trades Table ──

async function loadTrades(memberId) {
    const url = memberId ? `/api/trades?member_id=${encodeURIComponent(memberId)}` : '/api/trades';
    try {
        const resp = await fetch(url);
        const data = await resp.json();
        renderTrades(data.trades);
    } catch (err) {
        console.error('Failed to load trades:', err);
    }
}

function renderTrades(trades) {
    const tbody = document.getElementById('trades-body');
    if (!trades || trades.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" style="color:var(--text-muted);text-align:center;padding:1rem;">No trades found</td></tr>';
        return;
    }

    tbody.innerHTML = trades.map(t => `
        <tr>
            <td style="font-family:var(--font-mono);font-size:0.75rem;">${escapeHtml(t.date)}</td>
            <td>${escapeHtml(t.member_name)}</td>
            <td><span class="trade-type ${escapeHtml(t.type)}">${escapeHtml(t.type)}</span></td>
            <td style="font-family:var(--font-mono);color:var(--accent);">${escapeHtml(t.ticker)}</td>
            <td>${escapeHtml(t.company)}</td>
            <td style="font-size:0.75rem;">${escapeHtml(t.amount_range)}</td>
            <td style="font-size:0.75rem;">${escapeHtml(t.sector)}</td>
        </tr>
    `).join('');
}

// ── Bills List ──

async function loadBills() {
    try {
        const resp = await fetch('/api/bills');
        const data = await resp.json();
        renderBills(data.bills);
    } catch (err) {
        console.error('Failed to load bills:', err);
    }
}

function renderBills(bills) {
    const el = document.getElementById('bills-list');
    if (!bills || bills.length === 0) {
        el.innerHTML = '<span style="color:var(--text-muted);">No bills found</span>';
        return;
    }

    el.innerHTML = bills.map(b => `
        <div class="bill-item">
            <span class="bill-id">${escapeHtml(b.id)}</span>
            <div class="bill-title">${escapeHtml(b.title)}</div>
            <div class="bill-meta">
                ${escapeHtml(b.introduced)} | ${escapeHtml(b.status)}
                ${b.sponsor_name ? ' | Sponsor: ' + escapeHtml(b.sponsor_name) : ''}
            </div>
            ${b.subjects && b.subjects.length > 0 ? `
                <div class="bill-subjects">
                    ${b.subjects.map(s => `<span class="subject-tag">${escapeHtml(s)}</span>`).join('')}
                </div>
            ` : ''}
        </div>
    `).join('');
}

// ── Flagged Trades ──

async function loadFlagged() {
    try {
        const resp = await fetch('/api/suspicious?window_days=14');
        const data = await resp.json();
        renderFlagged(data.flagged);
    } catch (err) {
        console.error('Failed to load flagged trades:', err);
    }
}

function renderFlagged(flagged) {
    const el = document.getElementById('flagged-list');
    if (!flagged || flagged.length === 0) {
        el.innerHTML = '<span style="color:var(--text-muted);font-size:0.8125rem;">No suspicious trades detected in the current window.</span>';
        return;
    }

    el.innerHTML = flagged.map(f => `
        <div class="bill-item" style="border-left:3px solid #f59e0b;">
            <div style="display:flex;align-items:center;gap:0.5rem;">
                <span class="flag-badge">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z"/><line x1="4" y1="22" x2="4" y2="15"/></svg>
                    FLAGGED
                </span>
                <span class="trade-type ${escapeHtml(f.type)}">${escapeHtml(f.type)}</span>
                <span style="font-family:var(--font-mono);color:var(--accent);">${escapeHtml(f.ticker)}</span>
                <span style="color:var(--text-muted);font-size:0.75rem;">${escapeHtml(f.amount_range)}</span>
            </div>
            <div class="bill-title" style="font-size:0.8125rem;margin-top:0.375rem;">${escapeHtml(f.member_name)}</div>
            <div class="bill-meta">${escapeHtml(f.flag_reason)}</div>
            <div class="bill-meta">${escapeHtml(f.days_from_vote)} days ${escapeHtml(f.trade_timing)} vote | Vote: ${escapeHtml(f.vote_direction)}</div>
        </div>
    `).join('');
}

// ── Timeline ──

async function loadTimeline(memberId) {
    const url = memberId ? `/api/timeline?member_id=${encodeURIComponent(memberId)}` : '/api/timeline';
    try {
        const resp = await fetch(url);
        const data = await resp.json();
        renderTimeline(data.events);
    } catch (err) {
        console.error('Failed to load timeline:', err);
    }
}

function renderTimeline(events) {
    const container = document.getElementById('timeline-chart');
    container.innerHTML = '';

    if (!events || events.length === 0) {
        container.innerHTML = '<div class="loading-state">No events to display</div>';
        return;
    }

    const margin = { top: 20, right: 30, bottom: 30, left: 80 };
    const rect = container.getBoundingClientRect();
    const width = rect.width - margin.left - margin.right;
    const height = Math.max(300, events.length * 28) - margin.top - margin.bottom;

    const svg = d3.select(container).append('svg')
        .attr('width', rect.width)
        .attr('height', height + margin.top + margin.bottom);

    const g = svg.append('g')
        .attr('transform', `translate(${margin.left},${margin.top})`);

    const parseDate = d3.timeParse('%Y-%m-%d');
    const data = events.map((e, i) => ({
        ...e,
        parsedDate: parseDate(e.date),
        index: i,
    })).filter(d => d.parsedDate);

    if (data.length === 0) {
        container.innerHTML = '<div class="loading-state">No valid dates in events</div>';
        return;
    }

    const typeColors = {
        trade: '#a78bfa',
        vote: '#38bdf8',
        bill: '#10b981',
    };

    const x = d3.scaleTime()
        .domain(d3.extent(data, d => d.parsedDate))
        .range([0, width]);

    const y = d3.scalePoint()
        .domain(data.map((_, i) => i))
        .range([0, height])
        .padding(0.5);

    // Gridlines
    g.append('g')
        .call(d3.axisBottom(x).ticks(6).tickSize(height).tickFormat(''))
        .selectAll('.tick line')
        .attr('stroke', 'var(--border)')
        .attr('opacity', 0.3);

    g.selectAll('.domain').remove();

    // Event dots
    g.selectAll('.event-dot')
        .data(data)
        .join('circle')
        .attr('cx', d => x(d.parsedDate))
        .attr('cy', (_, i) => y(i))
        .attr('r', 5)
        .attr('fill', d => typeColors[d.type] || '#64748b')
        .attr('opacity', 0.9);

    // Event labels
    g.selectAll('.event-label')
        .data(data)
        .join('text')
        .attr('x', d => x(d.parsedDate) + 10)
        .attr('y', (_, i) => y(i) + 4)
        .attr('fill', 'var(--text-secondary)')
        .attr('font-size', '0.6875rem')
        .text(d => d.label.length > 50 ? d.label.slice(0, 47) + '...' : d.label);

    // X axis
    g.append('g')
        .attr('transform', `translate(0,${height})`)
        .call(d3.axisBottom(x).ticks(6).tickFormat(d3.timeFormat('%b %d')).tickSize(0))
        .selectAll('text')
        .attr('fill', 'var(--text-muted)')
        .attr('font-size', '0.625rem');

    // Legend
    const legend = svg.append('g')
        .attr('transform', `translate(${margin.left}, 5)`);

    Object.entries(typeColors).forEach(([type, color], i) => {
        const lg = legend.append('g')
            .attr('transform', `translate(${i * 80}, 0)`);
        lg.append('circle').attr('r', 4).attr('fill', color).attr('cx', 4).attr('cy', 4);
        lg.append('text')
            .attr('x', 12)
            .attr('y', 8)
            .attr('fill', 'var(--text-muted)')
            .attr('font-size', '0.625rem')
            .text(type.charAt(0).toUpperCase() + type.slice(1));
    });
}

// ── Tab Switching ──

function switchTab(tabName) {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));

    document.querySelector(`.tab-btn[data-tab="${tabName}"]`).classList.add('active');
    document.getElementById(`tab-${tabName}`).classList.add('active');
}

// ── Init ──

document.addEventListener('DOMContentLoaded', () => {
    loadMembers();
    loadTrades();
    loadBills();
    loadFlagged();
    loadTimeline();

    // Member search
    let searchTimeout;
    document.getElementById('member-search').addEventListener('input', (e) => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => loadMembers(e.target.value), 300);
    });

    // Member selection
    document.getElementById('member-list').addEventListener('click', (e) => {
        const item = e.target.closest('.member-item');
        if (!item) return;

        selectedMemberId = item.dataset.memberId;
        document.querySelectorAll('.member-item').forEach(m => m.classList.remove('active'));
        item.classList.add('active');

        loadTrades(selectedMemberId);
        loadTimeline(selectedMemberId);
    });

    // Tab switching
    document.querySelector('.tab-bar').addEventListener('click', (e) => {
        const btn = e.target.closest('.tab-btn');
        if (!btn) return;
        switchTab(btn.dataset.tab);
    });
});

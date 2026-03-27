/**
 * Legis Track - Congress member lookup with bills and campaign finance
 */

let selectedMemberId = null;
let searchTimeout = null;

// ── Tab switching ──
document.querySelector('.tab-bar').addEventListener('click', (e) => {
    const btn = e.target.closest('.tab-btn');
    if (!btn) return;
    const tab = btn.dataset.tab;
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById(`tab-${tab}`).classList.add('active');
});

// ── Members ──
async function loadMembers(query = '') {
    const list = document.getElementById('member-list');
    try {
        const resp = await fetch(`/api/members?q=${encodeURIComponent(query)}`);
        const data = await resp.json();

        if (!data.members || data.members.length === 0) {
            list.innerHTML = '<div class="empty-state">No members found</div>';
            return;
        }

        list.innerHTML = data.members.map(m => `
            <div class="member-item${m.id === selectedMemberId ? ' active' : ''}"
                 data-id="${m.id}" data-name="${m.name}">
                <span class="party-badge ${m.party}">${m.party}</span>
                <span class="member-name">${m.name}</span>
                <span class="member-state">${m.state}</span>
            </div>
        `).join('');
    } catch (err) {
        list.innerHTML = `<div class="empty-state">Error: ${err.message}</div>`;
    }
}

document.getElementById('member-list').addEventListener('click', (e) => {
    const item = e.target.closest('.member-item');
    if (!item) return;
    selectedMemberId = item.dataset.id;
    const name = item.dataset.name;
    document.querySelectorAll('.member-item').forEach(i => i.classList.remove('active'));
    item.classList.add('active');
    loadMemberDetail(selectedMemberId, name);
});

document.getElementById('member-search').addEventListener('input', (e) => {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => loadMembers(e.target.value), 300);
});

// ── Member detail ──
async function loadMemberDetail(memberId, memberName) {
    const sponsoredEl = document.getElementById('sponsored-list');
    sponsoredEl.innerHTML = '<div class="loading-state" style="height:auto;padding:1rem;"><div class="feed-spinner" style="margin-right:0.5rem;"></div>Loading...</div>';

    try {
        const resp = await fetch(`/api/member/${memberId}`);
        const data = await resp.json();

        if (data.error) {
            sponsoredEl.innerHTML = `<div class="empty-state">${data.error}</div>`;
            return;
        }

        // Sponsored bills
        if (data.sponsored_bills && data.sponsored_bills.length > 0) {
            sponsoredEl.innerHTML = data.sponsored_bills.map(b => `
                <div class="bill-item">
                    <span class="bill-id">${b.id}</span>
                    <div class="bill-title">${b.title}</div>
                    <div class="bill-meta">${b.introduced || ''} ${b.status ? '/ ' + b.status : ''}</div>
                </div>
            `).join('');
        } else {
            sponsoredEl.innerHTML = '<div class="empty-state">No sponsored legislation found</div>';
        }

        // Campaign finance
        const financeEl = document.getElementById('finance-panel');
        if (data.campaign_finance && data.campaign_finance.length > 0) {
            const f = data.campaign_finance[0];
            financeEl.innerHTML = `
                <div class="finance-card">
                    <div style="font-weight:600; margin-bottom:0.25rem;">${f.candidate_name || memberName}</div>
                    <div style="font-size:0.75rem; color:var(--text-muted);">${f.office || ''} ${f.state || ''} / ${f.party || ''} / Cycle: ${f.election_year || 'N/A'}</div>
                    <div class="finance-grid">
                        <div class="finance-stat">
                            <div class="finance-value">${formatMoney(f.total_receipts)}</div>
                            <div class="finance-label">Total Receipts</div>
                        </div>
                        <div class="finance-stat">
                            <div class="finance-value">${formatMoney(f.total_disbursements)}</div>
                            <div class="finance-label">Disbursements</div>
                        </div>
                        <div class="finance-stat">
                            <div class="finance-value">${formatMoney(f.individual_contributions)}</div>
                            <div class="finance-label">Individual</div>
                        </div>
                        <div class="finance-stat">
                            <div class="finance-value">${formatMoney(f.pac_contributions)}</div>
                            <div class="finance-label">PAC</div>
                        </div>
                    </div>
                </div>
            `;
        } else {
            financeEl.innerHTML = '<div class="empty-state">No campaign finance data found</div>';
        }
    } catch (err) {
        sponsoredEl.innerHTML = `<div class="empty-state">Error: ${err.message}</div>`;
    }
}

// ── Bills ──
async function loadBills() {
    const el = document.getElementById('bills-list');
    try {
        const resp = await fetch('/api/bills?limit=30');
        const data = await resp.json();

        if (!data.bills || data.bills.length === 0) {
            el.innerHTML = '<div class="empty-state">No bills found. Set CONGRESS_API_KEY in .env.</div>';
            return;
        }

        el.innerHTML = data.bills.map(b => `
            <div class="bill-item">
                <span class="bill-id">${b.id}</span>
                <div class="bill-title">${b.title}</div>
                <div class="bill-meta">${b.introduced || ''} ${b.status ? '/ ' + b.status : ''}</div>
            </div>
        `).join('');
    } catch (err) {
        el.innerHTML = `<div class="empty-state">Error: ${err.message}</div>`;
    }
}

// ── Timeline ──
async function loadTimeline() {
    const el = document.getElementById('timeline-list');
    try {
        const resp = await fetch('/api/timeline');
        const data = await resp.json();

        if (!data.events || data.events.length === 0) {
            el.innerHTML = '<div class="empty-state">No timeline events</div>';
            return;
        }

        el.innerHTML = data.events.map(ev => `
            <div class="event-item">
                <span class="event-date">${ev.date || ''}</span>
                <span class="event-dot ${ev.type}"></span>
                <div class="event-text">
                    <div class="event-label">${ev.label}</div>
                    <div style="font-size:0.75rem; color:var(--text-muted); margin-top:0.125rem;">${ev.detail}</div>
                </div>
            </div>
        `).join('');
    } catch (err) {
        el.innerHTML = `<div class="empty-state">Error: ${err.message}</div>`;
    }
}

// ── Utilities ──
function formatMoney(amount) {
    if (!amount) return '$0';
    if (amount >= 1000000) return `$${(amount / 1000000).toFixed(1)}M`;
    if (amount >= 1000) return `$${(amount / 1000).toFixed(0)}K`;
    return `$${amount.toFixed(0)}`;
}

// ── Init ──
loadMembers();
loadBills();
loadTimeline();

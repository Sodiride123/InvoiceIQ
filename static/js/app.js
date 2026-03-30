/* ═══════════════════════════════════════════════════════════════
   InvoiceIQ — Main Application JavaScript
   ═══════════════════════════════════════════════════════════════ */

'use strict';

// ── State ──────────────────────────────────────────────────────
const State = {
  invoices: [],
  filteredInvoices: [],
  categories: [],
  dashboardData: null,
  currentPage: 'dashboard',
  sortCol: 'date',
  sortDir: 'desc',
  filters: { search: '', category: '', duplicate: '' },
  createdInvoice: null,
  createStep: 'describe',
};

// ── API ────────────────────────────────────────────────────────
const API = {
  base: '/api',
  async get(path) {
    const r = await fetch(this.base + path);
    return r.json();
  },
  async post(path, body) {
    const r = await fetch(this.base + path, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    return r.json();
  },
  async delete(path) {
    const r = await fetch(this.base + path, { method: 'DELETE' });
    return r.json();
  },
  async upload(files) {
    const fd = new FormData();
    for (const f of files) fd.append('files', f);
    const r = await fetch(this.base + '/upload', { method: 'POST', body: fd });
    return r.json();
  },
};

// ── Utility ────────────────────────────────────────────────────
const $ = (sel, ctx = document) => ctx.querySelector(sel);
const $$ = (sel, ctx = document) => [...ctx.querySelectorAll(sel)];
const fmt = n => new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(n || 0);
const fmtNum = n => new Intl.NumberFormat('en-US').format(n || 0);

function escHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&')
    .replace(/</g, '<')
    .replace(/>/g, '>')
    .replace(/"/g, '"');
}

function getCatClass(cat = '') {
  const map = {
    'Software & Subscriptions': 'cat-software',
    'Office Supplies':          'cat-office',
    'Travel & Transportation':  'cat-travel',
    'Food & Entertainment':     'cat-food',
    'Marketing & Advertising':  'cat-marketing',
    'Professional Services':    'cat-professional',
    'Utilities & Facilities':   'cat-utilities',
    'Healthcare & Insurance':   'cat-healthcare',
    'Shipping & Logistics':     'cat-shipping',
    'Hardware & Equipment':     'cat-hardware',
    'Miscellaneous':            'cat-misc',
  };
  return map[cat] || 'cat-misc';
}

const CHART_COLORS = [
  '#059669','#10b981','#34d399','#6ee7b7','#f59e0b',
  '#ef4444','#06b6d4','#f97316','#a3e635','#14b8a6',
  '#a855f7','#22c55e',
];

// ── Toast Notifications ────────────────────────────────────────
function toast(title, msg = '', type = 'info') {
  const iconSvg = {
    success: `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="color:var(--success)"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>`,
    error:   `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="color:var(--danger)"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>`,
    warning: `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="color:var(--warning)"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>`,
    info:    `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="color:var(--primary-light)"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>`,
  };
  const container = $('#toast-container');
  const el = document.createElement('div');
  el.className = `toast ${type}`;
  el.innerHTML = `
    <span class="toast-icon">${iconSvg[type] || iconSvg.info}</span>
    <div class="toast-content">
      <div class="toast-title">${escHtml(title)}</div>
      ${msg ? `<div class="toast-msg">${escHtml(msg)}</div>` : ''}
    </div>
    <button class="toast-close" onclick="this.closest('.toast').remove()">
      <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
    </button>
  `;
  container.appendChild(el);
  setTimeout(() => el.remove(), 4500);
}

// ── Navigation ─────────────────────────────────────────────────
function navigate(page) {
  State.currentPage = page;
  $$('.nav-item').forEach(el => el.classList.toggle('active', el.dataset.page === page));
  $$('.page').forEach(el => el.classList.toggle('active', el.id === `page-${page}`));

  const titles = {
    dashboard: ['Dashboard',        'Overview of your invoice data'],
    create:    ['Create Invoice',   'AI-powered invoice generation'],
    upload:    ['Upload Invoices',  'Process PDF & image invoices'],
    invoices:  ['All Invoices',     'Browse and manage extracted invoices'],
    summary:   ['Monthly Summary',  'Expense trends and breakdowns'],
    export:    ['Export & Reports', 'Download data and generate reports'],
  };
  const [title, sub] = titles[page] || ['InvoiceIQ', ''];
  $('#page-title').textContent = title;
  $('#page-subtitle').textContent = sub;

  if (page === 'dashboard') loadDashboard();
  if (page === 'invoices') {
    // Reset filters when navigating to All Invoices directly
    State.filters = { search: '', category: '', duplicate: '' };
    const searchEl = $('#search-invoices');
    const catEl = $('#filter-category');
    const dupEl = $('#filter-duplicate');
    if (searchEl) searchEl.value = '';
    if (catEl) catEl.value = '';
    if (dupEl) dupEl.value = '';
    renderInvoiceTable();
  }
  if (page === 'summary')   loadSummary();
}

// ── Data Loading ───────────────────────────────────────────────
async function loadAll() {
  try {
    const [invRes, catRes] = await Promise.all([
      API.get('/invoices'),
      API.get('/categories'),
    ]);
    if (invRes.success) {
      State.invoices = invRes.invoices;
      State.filteredInvoices = [...invRes.invoices];
    }
    if (catRes.success) State.categories = catRes.categories;
    updateNavBadges();
  } catch (e) {
    console.error('Load error:', e);
  }
}

async function loadDashboard() {
  try {
    const res = await API.get('/dashboard');
    if (res.success) {
      State.dashboardData = res;
      renderDashboard(res);
    }
  } catch (e) {
    console.error('Dashboard error:', e);
  }
}

async function loadSummary() {
  try {
    const res = await API.get('/dashboard');
    if (res.success) renderSummaryPage(res);
  } catch (e) {
    console.error('Summary error:', e);
  }
}

function updateNavBadges() {
  const total = State.invoices.length;
  const dups  = State.invoices.filter(i => i.is_duplicate).length;

  const badgeInv = $('#badge-invoices');
  badgeInv.textContent = total;
  badgeInv.style.display = total ? 'inline' : 'none';

  const badgeDup = $('#badge-duplicates');
  if (dups > 0) {
    badgeDup.textContent = dups;
    badgeDup.style.display = 'inline';
  } else {
    badgeDup.style.display = 'none';
  }
}

// ── Dashboard Rendering ────────────────────────────────────────
function renderDashboard(data) {
  const stats = data.summary?.stats || {};
  const cd    = data.chart_data    || {};

  $('#stat-total').textContent   = fmt(stats.grand_total);
  $('#stat-invoices').textContent = fmtNum(stats.total_invoices);
  $('#stat-avg').textContent     = fmt(stats.avg_invoice);
  $('#stat-tax').textContent     = fmt(stats.total_tax);
  $('#stat-dups').textContent    = stats.duplicate_count || 0;
  $('#stat-largest').textContent = fmt(stats.largest_invoice);

  renderMonthlyChart(cd);
  renderCategoryDonut(cd, data.summary?.categories);
  renderTopVendorsChart(cd);
  renderRecentInvoices(data.invoices || []);
}

// ── Charts ─────────────────────────────────────────────────────
let chartInstances = {};

function destroyChart(id) {
  if (chartInstances[id]) {
    chartInstances[id].destroy();
    delete chartInstances[id];
  }
}

function renderMonthlyChart(cd) {
  destroyChart('monthly');
  const ctx = $('#chart-monthly')?.getContext('2d');
  if (!ctx || !cd.monthly_labels?.length) return;

  chartInstances['monthly'] = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: cd.monthly_labels.map(l => {
        const [y, m] = l.split('-');
        return new Date(y, m - 1).toLocaleString('default', { month: 'short', year: '2-digit' });
      }),
      datasets: [
        {
          label: 'Total Spend',
          data: cd.monthly_totals,
          backgroundColor: 'rgba(5,150,105,0.75)',
          borderColor: '#059669',
          borderWidth: 1,
          borderRadius: 6,
          yAxisID: 'y',
        },
        {
          label: 'Invoice Count',
          data: cd.monthly_counts,
          type: 'line',
          borderColor: '#34d399',
          backgroundColor: 'rgba(52,211,153,0.08)',
          borderWidth: 2,
          pointBackgroundColor: '#34d399',
          pointRadius: 4,
          tension: 0.4,
          yAxisID: 'y1',
          fill: true,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: { labels: { color: '#94a3b8', font: { size: 12 }, boxWidth: 12 } },
        tooltip: {
          backgroundColor: '#1e293b',
          borderColor: '#334155',
          borderWidth: 1,
          titleColor: '#f1f5f9',
          bodyColor: '#94a3b8',
          callbacks: {
            label: ctx => ctx.dataset.yAxisID === 'y'
              ? ` ${fmt(ctx.raw)}`
              : ` ${ctx.raw} invoices`,
          },
        },
      },
      scales: {
        x: {
          grid: { color: 'rgba(51,65,85,0.5)' },
          ticks: { color: '#64748b', font: { size: 11 } },
        },
        y: {
          position: 'left',
          grid: { color: 'rgba(51,65,85,0.5)' },
          ticks: {
            color: '#64748b', font: { size: 11 },
            callback: v => '$' + (v >= 1000 ? (v / 1000).toFixed(0) + 'k' : v),
          },
        },
        y1: {
          position: 'right',
          grid: { drawOnChartArea: false },
          ticks: { color: '#34d399', font: { size: 11 } },
        },
      },
    },
  });
}

function renderCategoryDonut(cd, catMap) {
  destroyChart('category');
  const ctx = $('#chart-category')?.getContext('2d');
  if (!ctx || !cd.category_labels?.length) return;

  chartInstances['category'] = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: cd.category_labels,
      datasets: [{
        data: cd.category_totals,
        backgroundColor: CHART_COLORS,
        borderColor: '#1e293b',
        borderWidth: 2,
        hoverOffset: 8,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      cutout: '65%',
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: '#1e293b',
          borderColor: '#334155',
          borderWidth: 1,
          titleColor: '#f1f5f9',
          bodyColor: '#94a3b8',
          callbacks: {
            label: ctx => {
              const total = cd.category_totals.reduce((a, b) => a + b, 0);
              return ` ${fmt(ctx.raw)} (${((ctx.raw / total) * 100).toFixed(1)}%)`;
            },
          },
        },
      },
    },
  });

  // Legend
  const legend = $('#category-legend');
  if (legend && catMap) {
    const total  = Object.values(catMap).reduce((a, b) => a + b, 0);
    const sorted = Object.entries(catMap).sort((a, b) => b[1] - a[1]).slice(0, 8);
    legend.innerHTML = sorted.map(([cat, val], i) => `
      <div class="legend-item">
        <div style="display:flex;align-items:center;flex:1;gap:6px;min-width:0">
          <div class="legend-dot" style="background:${CHART_COLORS[i % CHART_COLORS.length]}"></div>
          <span class="legend-name" style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${escHtml(cat)}</span>
        </div>
        <span class="legend-val">${fmt(val)}</span>
      </div>
      <div class="legend-bar-wrap">
        <div class="legend-bar" style="width:${Math.round((val/total)*100)}%;background:${CHART_COLORS[i % CHART_COLORS.length]}"></div>
      </div>
    `).join('');
  }
}

function renderTopVendorsChart(cd) {
  destroyChart('vendors');
  const ctx = $('#chart-vendors')?.getContext('2d');
  if (!ctx || !cd.top_vendor_labels?.length) return;

  chartInstances['vendors'] = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: cd.top_vendor_labels.map(v => v.length > 18 ? v.slice(0, 16) + '…' : v),
      datasets: [{
        label: 'Total Spend',
        data: cd.top_vendor_totals,
        backgroundColor: CHART_COLORS.map(c => c + 'bb'),
        borderColor: CHART_COLORS,
        borderWidth: 1,
        borderRadius: 6,
      }],
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: true,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: '#1e293b',
          borderColor: '#334155',
          borderWidth: 1,
          titleColor: '#f1f5f9',
          bodyColor: '#94a3b8',
          callbacks: { label: ctx => ` ${fmt(ctx.raw)}` },
        },
      },
      scales: {
        x: {
          grid: { color: 'rgba(51,65,85,0.5)' },
          ticks: {
            color: '#64748b', font: { size: 11 },
            callback: v => '$' + (v >= 1000 ? (v / 1000).toFixed(0) + 'k' : v),
          },
        },
        y: {
          grid: { display: false },
          ticks: { color: '#94a3b8', font: { size: 11 } },
        },
      },
    },
  });
}

function renderRecentInvoices(invoices) {
  const container = $('#recent-invoices');
  if (!container) return;

  const recent = [...invoices]
    .sort((a, b) => new Date(b.processed_at || 0) - new Date(a.processed_at || 0))
    .slice(0, 5);

  if (!recent.length) {
    container.innerHTML = `
      <div class="empty-state" style="padding:40px">
        <div class="empty-state-icon">
          <svg xmlns="http://www.w3.org/2000/svg" width="52" height="52" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round" style="color:var(--dark-muted)"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
        </div>
        <h3>No invoices yet</h3>
        <p>Upload invoices or load sample data to get started.</p>
        <div style="display:flex;gap:10px;justify-content:center">
          <button class="btn btn-primary" onclick="navigate('upload')">Upload Invoice</button>
          <button class="btn btn-outline" onclick="loadSampleData()">Load Sample Data</button>
        </div>
      </div>`;
    return;
  }

  container.innerHTML = `
    <table>
      <thead>
        <tr>
          <th>Vendor</th>
          <th>Date</th>
          <th>Category</th>
          <th>Total</th>
          <th>Status</th>
        </tr>
      </thead>
      <tbody>
        ${recent.map(inv => `
          <tr class="${inv.is_duplicate ? 'dup-row' : ''}"
              onclick="showInvoiceDetail('${inv.id}')" style="cursor:pointer">
            <td class="primary-col">${escHtml(inv.vendor || 'Unknown')}</td>
            <td>${inv.date || '—'}</td>
            <td>
              <span class="badge ${getCatClass(inv.category)}" style="display:inline-flex;align-items:center;gap:5px">
                <span style="display:inline-flex;align-items:center">${categoryIcon(inv.category)}</span>
                ${escHtml(inv.category || 'Misc')}
              </span>
            </td>
            <td style="color:var(--success);font-weight:700">${fmt(inv.total)}</td>
            <td>
              ${inv.is_duplicate
                ? `<span class="badge badge-danger" style="display:inline-flex;align-items:center;gap:4px">
                     <svg xmlns="http://www.w3.org/2000/svg" width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
                     Duplicate
                   </span>`
                : `<span class="badge badge-success" style="display:inline-flex;align-items:center;gap:4px">
                     <svg xmlns="http://www.w3.org/2000/svg" width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
                     Valid
                   </span>`}
            </td>
          </tr>
        `).join('')}
      </tbody>
    </table>`;
}

// ── Category Icon (returns inline SVG string) ──────────────────
function categoryIcon(cat) {
  const icons = {
    'Software & Subscriptions': `<svg xmlns="http://www.w3.org/2000/svg" width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="4" width="16" height="16" rx="2"/><rect x="9" y="9" width="6" height="6"/><line x1="9" y1="1" x2="9" y2="4"/><line x1="15" y1="1" x2="15" y2="4"/><line x1="9" y1="20" x2="9" y2="23"/><line x1="15" y1="20" x2="15" y2="23"/><line x1="20" y1="9" x2="23" y2="9"/><line x1="20" y1="14" x2="23" y2="14"/><line x1="1" y1="9" x2="4" y2="9"/><line x1="1" y1="14" x2="4" y2="14"/></svg>`,
    'Office Supplies':           `<svg xmlns="http://www.w3.org/2000/svg" width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/></svg>`,
    'Travel & Transportation':   `<svg xmlns="http://www.w3.org/2000/svg" width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17.8 19.2L16 11l3.5-3.5C21 6 21 4 19 4s-2 1-3.5 2.5L9 8.2 2.8 6.4 2 7.2l4 4-2 2-4-1-.8.8L3 16l3.5 3.5L10 20l.8-.8-1-4 2-2 4 4z"/></svg>`,
    'Food & Entertainment':      `<svg xmlns="http://www.w3.org/2000/svg" width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 8h1a4 4 0 0 1 0 8h-1"/><path d="M2 8h16v9a4 4 0 0 1-4 4H6a4 4 0 0 1-4-4V8z"/><line x1="6" y1="1" x2="6" y2="4"/><line x1="10" y1="1" x2="10" y2="4"/><line x1="14" y1="1" x2="14" y2="4"/></svg>`,
    'Marketing & Advertising':   `<svg xmlns="http://www.w3.org/2000/svg" width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 11l19-9-9 19-2-8-8-2z"/></svg>`,
    'Professional Services':     `<svg xmlns="http://www.w3.org/2000/svg" width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>`,
    'Utilities & Facilities':    `<svg xmlns="http://www.w3.org/2000/svg" width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>`,
    'Healthcare & Insurance':    `<svg xmlns="http://www.w3.org/2000/svg" width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>`,
    'Shipping & Logistics':      `<svg xmlns="http://www.w3.org/2000/svg" width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="16.5" y1="9.4" x2="7.5" y2="4.21"/><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/><polyline points="3.27 6.96 12 12.01 20.73 6.96"/><line x1="12" y1="22.08" x2="12" y2="12"/></svg>`,
    'Hardware & Equipment':      `<svg xmlns="http://www.w3.org/2000/svg" width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg>`,
    'Miscellaneous':             `<svg xmlns="http://www.w3.org/2000/svg" width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg>`,
  };
  return icons[cat] || icons['Miscellaneous'];
}

// ── Invoice Table ──────────────────────────────────────────────
function applyFilters() {
  let list = [...State.invoices];
  const { search, category, duplicate } = State.filters;

  if (search) {
    const q = search.toLowerCase();
    list = list.filter(inv =>
      (inv.vendor || '').toLowerCase().includes(q) ||
      (inv.invoice_number || '').toLowerCase().includes(q) ||
      (inv.category || '').toLowerCase().includes(q) ||
      (inv.filename || '').toLowerCase().includes(q)
    );
  }
  if (category)          list = list.filter(inv => inv.category === category);
  if (duplicate === 'yes') list = list.filter(inv =>  inv.is_duplicate);
  if (duplicate === 'no')  list = list.filter(inv => !inv.is_duplicate);

  // Sort
  list.sort((a, b) => {
    let va = a[State.sortCol] || '';
    let vb = b[State.sortCol] || '';
    if (['total','tax','subtotal'].includes(State.sortCol)) {
      va = parseFloat(va) || 0;
      vb = parseFloat(vb) || 0;
    }
    if (va < vb) return State.sortDir === 'asc' ? -1 :  1;
    if (va > vb) return State.sortDir === 'asc' ?  1 : -1;
    return 0;
  });

  State.filteredInvoices = list;
}

function renderInvoiceTable() {
  applyFilters();
  const tbody = $('#invoice-tbody');
  if (!tbody) return;

  // Populate category filter dropdown
  const catFilter = $('#filter-category');
  if (catFilter && State.categories.length) {
    const current = catFilter.value;
    catFilter.innerHTML = '<option value="">All Categories</option>' +
      State.categories.map(c =>
        `<option value="${escHtml(c)}" ${c === current ? 'selected' : ''}>${escHtml(c)}</option>`
      ).join('');
  }

  if (!State.filteredInvoices.length) {
    tbody.innerHTML = `<tr><td colspan="10">
      <div class="empty-state">
        <div class="empty-state-icon">
          <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round" style="color:var(--dark-muted)"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
        </div>
        <h3>No invoices found</h3>
        <p>Try adjusting your filters or upload some invoices.</p>
        <button class="btn btn-primary" onclick="navigate('upload')">Upload Invoices</button>
      </div>
    </td></tr>`;
    $('#invoice-count').textContent = '0 invoices';
    return;
  }

  $('#invoice-count').textContent =
    `${State.filteredInvoices.length} invoice${State.filteredInvoices.length !== 1 ? 's' : ''}`;

  const dupBadge = `
    <span class="badge badge-danger" style="display:inline-flex;align-items:center;gap:4px">
      <svg xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
      Dup
    </span>`;
  const validBadge = `
    <span class="badge badge-success" style="display:inline-flex;align-items:center;gap:4px">
      <svg xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
      Valid
    </span>`;

  tbody.innerHTML = State.filteredInvoices.map(inv => `
    <tr class="${inv.is_duplicate ? 'dup-row' : ''}" data-id="${inv.id}">
      <td><input type="checkbox" class="row-check" data-id="${inv.id}" onclick="event.stopPropagation()" onchange="updateBulkBar()"></td>
      <td class="primary-col" style="cursor:pointer" onclick="showInvoiceDetail('${inv.id}')">
        <div>${escHtml(inv.vendor || 'Unknown')}</div>
        <div style="font-size:11px;color:var(--text-muted);font-weight:400">${escHtml(inv.invoice_number || '')}</div>
      </td>
      <td>${inv.date || '—'}</td>
      <td>
        <span class="badge ${getCatClass(inv.category)}" style="display:inline-flex;align-items:center;gap:5px">
          <span style="display:inline-flex;align-items:center">${categoryIcon(inv.category)}</span>
          ${escHtml(inv.category || 'Misc')}
        </span>
      </td>
      <td style="color:var(--text-secondary)">${fmt(inv.subtotal)}</td>
      <td style="color:var(--warning)">${fmt(inv.tax)}</td>
      <td style="color:var(--success);font-weight:700">${fmt(inv.total)}</td>
      <td><span style="font-size:11px;color:var(--text-muted)">${escHtml(inv.payment_terms || 'Net 30')}</span></td>
      <td>${inv.is_duplicate ? dupBadge : validBadge}</td>
      <td>
        <div style="display:flex;gap:6px">
          <button class="btn btn-outline btn-sm" onclick="showInvoiceDetail('${inv.id}')" title="View Details"
            style="padding:5px 8px">
            <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
          </button>
          <button class="btn btn-danger btn-sm" onclick="deleteInvoice('${inv.id}')" title="Delete"
            style="padding:5px 8px">
            <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"/></svg>
          </button>
        </div>
      </td>
    </tr>
  `).join('');
}

function setSort(col) {
  if (State.sortCol === col) {
    State.sortDir = State.sortDir === 'asc' ? 'desc' : 'asc';
  } else {
    State.sortCol = col;
    State.sortDir = 'desc';
  }
  renderInvoiceTable();
}

// ── Invoice Detail Modal ───────────────────────────────────────
async function showInvoiceDetail(id) {
  const inv = State.invoices.find(i => i.id === id);
  if (!inv) return;

  const modal = $('#modal-detail');
  const body  = $('#modal-detail-body');

  const lineItemsHtml = inv.line_items?.length
    ? `<ul class="line-items-list">
        ${inv.line_items.map(item => `
          <li class="line-item-row">
            <span class="line-item-desc">${escHtml(item.description || '')}</span>
            <span class="line-item-amount">${fmt(item.amount)}</span>
          </li>`).join('')}
      </ul>`
    : '<p style="color:var(--text-muted);font-size:13px">No line items extracted</p>';

  body.innerHTML = `
    <div style="display:flex;gap:12px;align-items:flex-start;margin-bottom:20px">
      <div style="flex:1">
        <h2 style="font-size:20px;font-weight:800;color:var(--text-primary);margin-bottom:8px">
          ${escHtml(inv.vendor || 'Unknown')}
        </h2>
        <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap">
          <span class="badge ${getCatClass(inv.category)}" style="display:inline-flex;align-items:center;gap:5px">
            <span style="display:inline-flex;align-items:center">${categoryIcon(inv.category)}</span>
            ${escHtml(inv.category || 'Misc')}
          </span>
          ${inv.is_duplicate ? `
            <span class="badge badge-danger" style="display:inline-flex;align-items:center;gap:4px">
              <svg xmlns="http://www.w3.org/2000/svg" width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
              Duplicate
            </span>` : ''}
        </div>
      </div>
      <div style="text-align:right;flex-shrink:0">
        <div style="font-size:28px;font-weight:800;color:var(--success)">${fmt(inv.total)}</div>
        <div style="font-size:12px;color:var(--text-muted)">Total Amount</div>
      </div>
    </div>

    <div class="detail-grid">
      <div class="detail-item">
        <div class="detail-label">Invoice Number</div>
        <div class="detail-value">${escHtml(inv.invoice_number || '—')}</div>
      </div>
      <div class="detail-item">
        <div class="detail-label">Invoice Date</div>
        <div class="detail-value">${inv.date || '—'}</div>
      </div>
      <div class="detail-item">
        <div class="detail-label">Subtotal</div>
        <div class="detail-value">${fmt(inv.subtotal)}</div>
      </div>
      <div class="detail-item">
        <div class="detail-label">Tax</div>
        <div class="detail-value">${fmt(inv.tax)}</div>
      </div>
      <div class="detail-item">
        <div class="detail-label">Payment Terms</div>
        <div class="detail-value">${escHtml(inv.payment_terms || '—')}</div>
      </div>
      <div class="detail-item">
        <div class="detail-label">File</div>
        <div class="detail-value" style="font-size:12px;color:var(--text-muted)">${escHtml(inv.filename || '—')}</div>
      </div>
    </div>

    <div style="margin-bottom:20px">
      <div class="detail-label" style="margin-bottom:8px">Re-categorize</div>
      <div style="display:flex;gap:8px">
        <select id="recategorize-select" class="filter-select" style="flex:1">
          ${State.categories.map(c =>
            `<option value="${escHtml(c)}" ${c === inv.category ? 'selected' : ''}>${escHtml(c)}</option>`
          ).join('')}
        </select>
        <button class="btn btn-primary btn-sm" onclick="recategorize('${inv.id}')">Update</button>
      </div>
    </div>

    <div>
      <div class="card-title" style="margin-bottom:10px;display:flex;align-items:center;gap:8px">
        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/></svg>
        Line Items
      </div>
      ${lineItemsHtml}

      <div style="margin-top:16px;padding-top:16px;border-top:1px solid var(--dark-border)">
        <div style="display:flex;justify-content:space-between;font-size:13px;color:var(--text-muted);margin-bottom:6px">
          <span>Subtotal</span><span>${fmt(inv.subtotal)}</span>
        </div>
        <div style="display:flex;justify-content:space-between;font-size:13px;color:var(--warning);margin-bottom:6px">
          <span>Tax</span><span>${fmt(inv.tax)}</span>
        </div>
        <div style="display:flex;justify-content:space-between;font-size:16px;font-weight:800;color:var(--success)">
          <span>Total</span><span>${fmt(inv.total)}</span>
        </div>
      </div>
    </div>

    ${inv.raw_text_preview ? `
      <details style="margin-top:16px">
        <summary style="cursor:pointer;font-size:12px;color:var(--text-muted);padding:8px 0;
          display:flex;align-items:center;gap:6px;list-style:none">
          <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
          Raw OCR Text Preview
        </summary>
        <pre style="font-size:11px;color:var(--text-muted);background:var(--dark);padding:12px;
          border-radius:8px;margin-top:8px;overflow-x:auto;white-space:pre-wrap;
          border:1px solid var(--dark-border)">${escHtml(inv.raw_text_preview)}</pre>
      </details>` : ''}
  `;

  modal.classList.add('open');
}

async function recategorize(id) {
  const sel = $('#recategorize-select');
  if (!sel) return;
  const cat = sel.value;
  const res = await API.post(`/invoices/${id}/recategorize`, { category: cat });
  if (res.success) {
    toast('Category Updated', `Recategorized to: ${cat}`, 'success');
    await loadAll();
    renderInvoiceTable();
    $('#modal-detail').classList.remove('open');
  } else {
    toast('Error', res.error, 'error');
  }
}

async function deleteInvoice(id) {
  if (!confirm('Delete this invoice? This cannot be undone.')) return;

  // Optimistic removal from state
  State.invoices = State.invoices.filter(inv => inv.id !== id);
  updateNavBadges();
  renderInvoiceTable();

  const res = await API.delete(`/invoices/${id}`);
  if (res.success) {
    toast('Deleted', 'Invoice removed', 'success');
  } else {
    // Revert on failure
    toast('Error', res.error, 'error');
    await loadAll();
    renderInvoiceTable();
  }
}

async function bulkDeleteInvoices() {
  const checked = $$('.row-check:checked');
  if (!checked.length) {
    toast('No Selection', 'Select invoices to delete first.', 'warning');
    return;
  }
  const ids = checked.map(cb => cb.dataset.id);
  if (!confirm(`Delete ${ids.length} invoice(s)? This cannot be undone.`)) return;

  // Optimistic removal
  const idSet = new Set(ids);
  State.invoices = State.invoices.filter(inv => !idSet.has(inv.id));
  updateNavBadges();
  renderInvoiceTable();
  updateBulkBar();

  try {
    const res = await API.post('/invoices/bulk-delete', { ids });
    if (res.success) {
      toast('Deleted', `${res.deleted} invoice(s) removed`, 'success');
    } else {
      toast('Error', res.error, 'error');
      await loadAll();
      renderInvoiceTable();
    }
  } catch (e) {
    toast('Error', e.message, 'error');
    await loadAll();
    renderInvoiceTable();
  }
}

function updateBulkBar() {
  const checked = $$('.row-check:checked');
  const bar = $('#bulk-action-bar');
  if (!bar) return;
  if (checked.length > 0) {
    bar.style.display = 'flex';
    const countEl = $('#bulk-count');
    if (countEl) countEl.textContent = `${checked.length} selected`;
  } else {
    bar.style.display = 'none';
  }
}

// ── Upload ─────────────────────────────────────────────────────
function initUploadZone() {
  const zone      = $('#upload-zone');
  const fileInput = $('#file-input');
  if (!zone || !fileInput) return;

  zone.addEventListener('click', () => fileInput.click());

  zone.addEventListener('dragover', e => {
    e.preventDefault();
    zone.classList.add('dragover');
  });
  zone.addEventListener('dragleave', () => zone.classList.remove('dragover'));
  zone.addEventListener('drop', e => {
    e.preventDefault();
    zone.classList.remove('dragover');
    processUpload(Array.from(e.dataTransfer.files));
  });

  fileInput.addEventListener('change', () => {
    if (fileInput.files.length) processUpload(Array.from(fileInput.files));
  });
}

async function processUpload(files) {
  if (!files.length) return;

  const zone         = $('#upload-zone');
  const progressWrap = $('#upload-progress');
  const progressBar  = $('#upload-progress-bar');
  const statusText   = $('#upload-status');
  const resultsEl    = $('#upload-results');

  zone.style.pointerEvents = 'none';
  progressWrap.style.display = 'block';
  resultsEl.innerHTML = '';
  statusText.textContent = `Processing ${files.length} file(s)…`;
  progressBar.style.width = '30%';

  try {
    progressBar.style.width = '65%';
    const res = await API.upload(files);
    progressBar.style.width = '100%';

    if (res.success) {
      statusText.textContent = `Done — ${res.successful}/${res.processed} succeeded`;

      res.results.forEach(r => {
        const cls    = r.success ? (r.is_duplicate ? 'warning' : 'success') : 'error';
        const iconSvg = r.success
          ? (r.is_duplicate
              ? `<svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="color:var(--warning)"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>`
              : `<svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="color:var(--success)"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>`)
          : `<svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="color:var(--danger)"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>`;

        const detail = r.success
          ? `${r.invoice?.vendor || 'Unknown'} — ${fmt(r.invoice?.total)} — ${r.invoice?.category || ''}`
          : (r.error || 'Processing failed');

        const dupNote = r.is_duplicate
          ? `<span class="badge badge-danger" style="margin-left:8px;font-size:10px">Duplicate</span>`
          : '';

        resultsEl.innerHTML += `
          <div class="process-result-item ${cls}">
            <span style="display:inline-flex;align-items:center;flex-shrink:0">${iconSvg}</span>
            <div style="flex:1;min-width:0">
              <div style="font-weight:600;color:var(--text-primary);display:flex;align-items:center;flex-wrap:wrap;gap:4px">
                ${escHtml(r.filename)}${dupNote}
              </div>
              <div style="font-size:12px;color:var(--text-muted);margin-top:2px">${escHtml(detail)}</div>
            </div>
          </div>`;
      });

      const dups = res.results.filter(r => r.is_duplicate).length;
      toast(
        `${res.successful} Invoice${res.successful !== 1 ? 's' : ''} Processed`,
        `${res.failed ? `${res.failed} failed. ` : ''}${dups ? `${dups} duplicate(s) detected.` : ''}`,
        res.successful ? 'success' : 'error'
      );
      await loadAll();
    } else {
      statusText.textContent = 'Upload failed';
      toast('Upload Failed', res.error, 'error');
    }
  } catch (e) {
    statusText.textContent = 'Network error';
    toast('Error', e.message, 'error');
  }

  setTimeout(() => {
    progressBar.style.width = '0%';
    progressWrap.style.display = 'none';
    zone.style.pointerEvents = '';
  }, 2500);
}

let _loadingSamples = false;
async function loadSampleData() {
  if (_loadingSamples) return;
  _loadingSamples = true;

  // Disable all buttons that trigger this
  const allBtns = $$('[onclick*="loadSampleData"]');
  const saved = allBtns.map(b => ({ el: b, html: b.innerHTML }));
  allBtns.forEach(b => {
    b.disabled = true;
    b.innerHTML = '<span class="spinner"></span> Loading\u2026';
  });

  try {
    const res  = await fetch('/api/load-samples', { method: 'POST' });
    const data = await res.json();

    if (data.success) {
      const ok = data.results?.filter(r => r.success).length || 0;
      toast('Sample Data Loaded', `${ok} invoices processed successfully`, 'success');
      await loadAll();
      navigate('dashboard');
    } else {
      toast('Error', data.error, 'error');
    }
  } catch (e) {
    toast('Error', e.message, 'error');
  } finally {
    _loadingSamples = false;
    saved.forEach(({ el, html }) => {
      el.disabled = false;
      el.innerHTML = html;
    });
  }
}

// ── Summary Page ───────────────────────────────────────────────
function renderSummaryPage(data) {
  const stats    = data.summary?.stats     || {};
  const monthly  = data.summary?.monthly   || {};
  const categories = data.summary?.categories || {};
  const cd       = data.chart_data         || {};

  $('#sum-total').textContent = fmt(stats.grand_total);
  $('#sum-count').textContent = fmtNum(stats.valid_invoices);
  $('#sum-tax').textContent   = fmt(stats.total_tax);
  $('#sum-avg').textContent   = fmt(stats.avg_invoice);

  // Monthly breakdown cards
  const monthGrid = $('#month-grid');
  if (monthGrid) {
    const sorted = Object.entries(monthly).sort((a, b) => a[0].localeCompare(b[0]));
    monthGrid.innerHTML = sorted.length
      ? sorted.map(([key, val]) => {
          const [y, m] = key.split('-');
          const label = new Date(y, m - 1).toLocaleString('default', { month: 'long', year: 'numeric' });
          return `
            <div class="month-card">
              <div class="month-name">${label}</div>
              <div class="month-total">${fmt(val.total)}</div>
              <div class="month-count">${val.count} invoice${val.count !== 1 ? 's' : ''}</div>
            </div>`;
        }).join('')
      : '<p style="color:var(--text-muted);font-size:13px">No data available</p>';
  }

  // Top vendors
  const vendorList = $('#vendor-list');
  if (vendorList && data.summary?.top_vendors?.length) {
    const max = data.summary.top_vendors[0]?.[1] || 1;
    vendorList.innerHTML = data.summary.top_vendors.map(([name, total], i) => `
      <li class="vendor-row">
        <div class="vendor-rank">${i + 1}</div>
        <div class="vendor-name">${escHtml(name)}</div>
        <div class="vendor-bar-wrap">
          <div class="vendor-bar" style="width:${Math.round((total/max)*100)}%"></div>
        </div>
        <div class="vendor-total">${fmt(total)}</div>
      </li>`).join('');
  }

  // Category spend
  const catContainer = $('#category-spend');
  if (catContainer) {
    const sorted = Object.entries(categories).sort((a, b) => b[1] - a[1]);
    const total  = sorted.reduce((s, [, v]) => s + v, 0);
    catContainer.innerHTML = sorted.map(([cat, val], i) => `
      <div class="legend-item" style="padding:9px 0;border-bottom:1px solid rgba(51,65,85,0.4)">
        <div style="display:flex;align-items:center;flex:1;gap:8px">
          <div class="legend-dot" style="background:${CHART_COLORS[i % CHART_COLORS.length]};width:10px;height:10px;border-radius:50%;flex-shrink:0"></div>
          <span class="badge ${getCatClass(cat)}" style="display:inline-flex;align-items:center;gap:5px">
            <span style="display:inline-flex;align-items:center">${categoryIcon(cat)}</span>
            ${escHtml(cat)}
          </span>
        </div>
        <div style="display:flex;gap:16px;align-items:center">
          <span style="font-size:12px;color:var(--text-muted)">${((val/total)*100).toFixed(1)}%</span>
          <span style="font-weight:700;color:var(--text-primary);min-width:90px;text-align:right">${fmt(val)}</span>
        </div>
      </div>`).join('');
  }

  // Trend chart
  destroyChart('sum-monthly');
  const smCtx = $('#chart-sum-monthly')?.getContext('2d');
  if (smCtx && cd.monthly_labels?.length) {
    chartInstances['sum-monthly'] = new Chart(smCtx, {
      type: 'line',
      data: {
        labels: cd.monthly_labels.map(l => {
          const [y, m] = l.split('-');
          return new Date(y, m - 1).toLocaleString('default', { month: 'short', year: '2-digit' });
        }),
        datasets: [{
          label: 'Monthly Spend',
          data: cd.monthly_totals,
          borderColor: '#059669',
          backgroundColor: 'rgba(5,150,105,0.08)',
          borderWidth: 3,
          pointBackgroundColor: '#059669',
          pointBorderColor: '#1e293b',
          pointBorderWidth: 2,
          pointRadius: 5,
          tension: 0.4,
          fill: true,
        }],
      },
      options: {
        responsive: true,
        plugins: {
          legend: { labels: { color: '#94a3b8', font: { size: 12 } } },
          tooltip: {
            backgroundColor: '#1e293b', borderColor: '#334155', borderWidth: 1,
            titleColor: '#f1f5f9', bodyColor: '#94a3b8',
            callbacks: { label: ctx => ` ${fmt(ctx.raw)}` },
          },
        },
        scales: {
          x: { grid: { color: 'rgba(51,65,85,0.5)' }, ticks: { color: '#64748b', font: { size: 11 } } },
          y: {
            grid: { color: 'rgba(51,65,85,0.5)' },
            ticks: { color: '#64748b', font: { size: 11 }, callback: v => '$' + (v >= 1000 ? (v/1000).toFixed(0)+'k' : v) },
          },
        },
      },
    });
  }
}

// ── Create Invoice (AI) ────────────────────────────────────

function setCreateStep(step) {
  State.createStep = step;
  const steps = ['describe', 'preview', 'download'];
  steps.forEach(s => {
    const el = $(`#create-step-${s}`);
    if (el) el.style.display = s === step ? '' : 'none';
  });
  // loading is separate
  const loadingEl = $('#create-step-loading');
  if (loadingEl) loadingEl.style.display = step === 'loading' ? '' : 'none';
  if (step === 'loading') {
    $('#create-step-describe').style.display = 'none';
  }

  // Update step indicators
  const stepOrder = ['describe', 'preview', 'download'];
  const activeIdx = step === 'loading' ? 0 : stepOrder.indexOf(step);
  ['step-describe', 'step-preview', 'step-download'].forEach((id, i) => {
    const el = $(`#${id}`);
    if (!el) return;
    el.classList.remove('active', 'done');
    if (i < activeIdx) el.classList.add('done');
    else if (i === activeIdx) el.classList.add('active');
  });
}

function fillExample(el) {
  const text = el.getAttribute('data-text');
  if (text) {
    const ta = $('#create-description');
    if (ta) ta.value = text;
  }
}

async function generateInvoice() {
  const desc = ($('#create-description')?.value || '').trim();
  if (!desc) {
    toast('Description Required', 'Please describe the services you want to invoice.', 'warning');
    return;
  }

  const fromName = $('#create-from-name')?.value || '';
  const fromAddress = $('#create-from-address')?.value || '';
  const taxRate = $('#create-tax-rate')?.value || '';
  const template = $('#create-template')?.value || 'professional';

  const btn = $('#btn-generate-invoice');
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Generating...';
  }

  setCreateStep('loading');

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 120000);

    const res = await fetch('/api/create-invoice', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        description: desc,
        from_name: fromName,
        from_address: fromAddress,
        tax_rate: taxRate,
        template: template,
      }),
      signal: controller.signal,
    });
    clearTimeout(timeoutId);

    const data = await res.json();

    if (data.success && data.invoice) {
      State.createdInvoice = data.invoice;
      renderInvoicePreview(data.invoice);
      setCreateStep('preview');
      toast('Invoice Generated', 'Review your invoice and make any edits.', 'success');
    } else {
      setCreateStep('describe');
      toast('Generation Failed', data.error || 'Could not generate invoice. Please try again.', 'error');
    }
  } catch (e) {
    setCreateStep('describe');
    if (e.name === 'AbortError') {
      toast('Timeout', 'The AI took too long to respond. Please try again.', 'error');
    } else {
      toast('Error', e.message || 'Network error', 'error');
    }
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = `
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
        Generate Invoice with AI`;
    }
  }
}

function renderInvoicePreview(inv) {
  const container = $('#invoice-preview-container');
  if (!container) return;

  const items = inv.items || [];
  const itemRows = items.map((item, i) => `
    <tr>
      <td><input class="inv-edit-input" value="${escHtml(item.description || '')}" onchange="updateLineItem(${i},'description',this.value)"></td>
      <td><input class="inv-edit-input num" type="number" value="${item.quantity}" min="0" step="1" onchange="updateLineItem(${i},'quantity',this.value)"></td>
      <td><input class="inv-edit-input num" type="number" value="${item.unit_price}" min="0" step="0.01" onchange="updateLineItem(${i},'unit_price',this.value)"></td>
      <td style="font-weight:700;color:#059669">${fmt(item.amount)}</td>
      <td class="line-item-actions">
        <button onclick="removeLineItem(${i})" title="Remove">
          <svg xmlns="http://www.w3.org/2000/svg" width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
        </button>
      </td>
    </tr>
  `).join('');

  container.innerHTML = `
    <div class="invoice-preview">
      <div class="inv-header">
        <div>
          <div class="inv-title">INVOICE</div>
          <div style="margin-top:4px">
            <input class="inv-edit-input" value="${escHtml(inv.invoice_number || '')}" onchange="updateInvField('invoice_number',this.value)" style="font-size:14px;font-weight:600;max-width:200px">
          </div>
        </div>
        <div style="text-align:right">
          <div style="font-size:32px;font-weight:900;color:#059669">${fmt(inv.total)}</div>
          <div style="font-size:12px;color:#64748b">Total Due</div>
        </div>
      </div>

      <div class="inv-from-to">
        <div>
          <div class="inv-section-label">From</div>
          <div class="inv-section-value">
            <input class="inv-edit-input" value="${escHtml(inv.from_name || '')}" onchange="updateInvField('from_name',this.value)" style="font-weight:600;margin-bottom:4px">
            <input class="inv-edit-input" value="${escHtml(inv.from_address || '')}" onchange="updateInvField('from_address',this.value)" placeholder="Address">
          </div>
        </div>
        <div>
          <div class="inv-section-label">Bill To</div>
          <div class="inv-section-value">
            <input class="inv-edit-input" value="${escHtml(inv.client_name || '')}" onchange="updateInvField('client_name',this.value)" style="font-weight:600;margin-bottom:4px">
            <input class="inv-edit-input" value="${escHtml(inv.client_address || '')}" onchange="updateInvField('client_address',this.value)" placeholder="Address">
          </div>
        </div>
      </div>

      <div class="inv-meta">
        <div class="inv-meta-item">
          <span class="inv-meta-label">Date</span>
          <input class="inv-edit-input" type="date" value="${inv.date || ''}" onchange="updateInvField('date',this.value)" style="width:140px">
        </div>
        <div class="inv-meta-item">
          <span class="inv-meta-label">Due Date</span>
          <input class="inv-edit-input" type="date" value="${inv.due_date || ''}" onchange="updateInvField('due_date',this.value)" style="width:140px">
        </div>
        <div class="inv-meta-item">
          <span class="inv-meta-label">Terms</span>
          <input class="inv-edit-input" value="${escHtml(inv.payment_terms || 'Net 30')}" onchange="updateInvField('payment_terms',this.value)" style="width:100px">
        </div>
        <div class="inv-meta-item">
          <span class="inv-meta-label">Tax Rate</span>
          <input class="inv-edit-input num" type="number" value="${((inv.tax_rate || 0) * 100).toFixed(1)}" min="0" max="100" step="0.5" onchange="updateTaxRate(this.value)" style="width:70px">%
        </div>
      </div>

      <table>
        <thead>
          <tr>
            <th style="width:50%">Description</th>
            <th style="width:10%;text-align:center">Qty</th>
            <th style="width:15%;text-align:right">Unit Price</th>
            <th style="width:15%;text-align:right">Amount</th>
            <th style="width:10%"></th>
          </tr>
        </thead>
        <tbody id="preview-line-items">
          ${itemRows}
        </tbody>
      </table>

      <div style="margin-bottom:16px">
        <button class="btn-add-item" onclick="addLineItem()">
          <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
          Add Line Item
        </button>
      </div>

      <div class="inv-totals">
        <div class="inv-totals-table">
          <div class="inv-totals-row">
            <span>Subtotal</span>
            <span id="preview-subtotal">${fmt(inv.subtotal)}</span>
          </div>
          <div class="inv-totals-row">
            <span>Tax (${((inv.tax_rate || 0) * 100).toFixed(1)}%)</span>
            <span id="preview-tax">${fmt(inv.tax_amount)}</span>
          </div>
          <div class="inv-totals-row grand">
            <span>Total Due</span>
            <span id="preview-total">${fmt(inv.total)}</span>
          </div>
        </div>
      </div>

      <div class="inv-notes">
        <input class="inv-edit-input" value="${escHtml(inv.notes || '')}" onchange="updateInvField('notes',this.value)" placeholder="Notes..." style="font-style:italic;color:#64748b;border:none;font-size:12px">
      </div>
    </div>
  `;
}

function updateInvField(field, value) {
  if (!State.createdInvoice) return;
  State.createdInvoice[field] = value;
}

function updateLineItem(index, field, value) {
  if (!State.createdInvoice?.items?.[index]) return;
  const item = State.createdInvoice.items[index];
  if (field === 'description') {
    item.description = value;
  } else {
    item[field] = parseFloat(value) || 0;
    item.amount = Math.round(item.quantity * item.unit_price * 100) / 100;
  }
  recalculateTotals();
  renderInvoicePreview(State.createdInvoice);
}

function updateTaxRate(value) {
  if (!State.createdInvoice) return;
  State.createdInvoice.tax_rate = (parseFloat(value) || 0) / 100;
  recalculateTotals();
  renderInvoicePreview(State.createdInvoice);
}

function addLineItem() {
  if (!State.createdInvoice) return;
  if (!State.createdInvoice.items) State.createdInvoice.items = [];
  State.createdInvoice.items.push({
    description: 'New item',
    quantity: 1,
    unit_price: 0,
    amount: 0,
  });
  recalculateTotals();
  renderInvoicePreview(State.createdInvoice);
}

function removeLineItem(index) {
  if (!State.createdInvoice?.items) return;
  State.createdInvoice.items.splice(index, 1);
  recalculateTotals();
  renderInvoicePreview(State.createdInvoice);
}

function recalculateTotals() {
  if (!State.createdInvoice) return;
  const inv = State.createdInvoice;
  let subtotal = 0;
  (inv.items || []).forEach(item => {
    item.amount = Math.round(item.quantity * item.unit_price * 100) / 100;
    subtotal += item.amount;
  });
  inv.subtotal = Math.round(subtotal * 100) / 100;
  inv.tax_amount = Math.round(subtotal * (inv.tax_rate || 0) * 100) / 100;
  inv.total = Math.round((inv.subtotal + inv.tax_amount) * 100) / 100;
}

function backToDescribe() {
  setCreateStep('describe');
}

function resetCreateInvoice() {
  State.createdInvoice = null;
  const desc = $('#create-description');
  if (desc) desc.value = '';
  setCreateStep('describe');
}

async function downloadInvoicePdf() {
  if (!State.createdInvoice) return;

  const template = $('#create-template')?.value || 'professional';

  try {
    toast('Generating PDF', 'Preparing your invoice for download...', 'info');
    const res = await fetch('/api/create-invoice/pdf', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ invoice: State.createdInvoice, template }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      toast('PDF Error', err.error || 'Could not generate PDF', 'error');
      return;
    }

    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `invoice_${State.createdInvoice.invoice_number || 'new'}.pdf`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    setCreateStep('download');
    toast('PDF Downloaded', 'Your invoice PDF has been saved.', 'success');
  } catch (e) {
    toast('Error', e.message || 'Download failed', 'error');
  }
}

async function saveCreatedInvoice() {
  if (!State.createdInvoice) return;

  try {
    const res = await API.post('/create-invoice/save', { invoice: State.createdInvoice });
    if (res.success) {
      toast('Saved to Library', 'Invoice added to your invoice library.', 'success');
      await loadAll();
    } else {
      toast('Error', res.error || 'Could not save invoice', 'error');
    }
  } catch (e) {
    toast('Error', e.message, 'error');
  }
}

// ── Clear All ──────────────────────────────────────────────────
async function clearAllData() {
  if (!confirm('Clear ALL invoice data? This cannot be undone.')) return;
  const res = await API.post('/clear', {});
  if (res.success) {
    toast('Cleared', 'All invoice data removed', 'success');
    await loadAll();
    renderInvoiceTable();
  }
}

// ── Init ───────────────────────────────────────────────────────
async function init() {
  $$('.nav-item[data-page]').forEach(el => {
    el.addEventListener('click', () => navigate(el.dataset.page));
  });

  const searchEl = $('#search-invoices');
  if (searchEl) searchEl.addEventListener('input', e => {
    State.filters.search = e.target.value;
    renderInvoiceTable();
  });

  const catFilterEl = $('#filter-category');
  if (catFilterEl) catFilterEl.addEventListener('change', e => {
    State.filters.category = e.target.value;
    renderInvoiceTable();
  });

  const dupFilterEl = $('#filter-duplicate');
  if (dupFilterEl) dupFilterEl.addEventListener('change', e => {
    State.filters.duplicate = e.target.value;
    renderInvoiceTable();
  });

  $$('th.sortable').forEach(th => {
    th.addEventListener('click', () => setSort(th.dataset.sort));
  });

  const modalOverlay = $('#modal-detail');
  if (modalOverlay) {
    modalOverlay.addEventListener('click', e => {
      if (e.target === modalOverlay) modalOverlay.classList.remove('open');
    });
  }
  $('#modal-close-btn')?.addEventListener('click', () => {
    $('#modal-detail')?.classList.remove('open');
  });

  initUploadZone();
  await loadAll();
  navigate('dashboard');
  loadDashboard();
}

document.addEventListener('DOMContentLoaded', init);
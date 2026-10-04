/**
 * Magnus Dynamic CMS - Activity Logs Controller
 */

let currentPage = 1;
const pageLimit = 15;

document.addEventListener("DOMContentLoaded", () => {
  if (!Auth.requireAdmin()) return;
  Auth.initSidebar();

  loadActivityLogs(1);
  setupEventListeners();
});

function setupEventListeners() {
  document.getElementById("btn-refresh-logs").addEventListener("click", () => loadActivityLogs(currentPage));

  const searchInput = document.getElementById("table-search");
  if (searchInput) {
    let debounceTimer;
    searchInput.addEventListener("input", () => {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => loadActivityLogs(1), 250);
    });
  }

  const moduleFilter = document.getElementById("module-filter");
  if (moduleFilter) {
    moduleFilter.addEventListener("change", () => loadActivityLogs(1));
  }

  const actionFilter = document.getElementById("action-filter");
  if (actionFilter) {
    actionFilter.addEventListener("change", () => loadActivityLogs(1));
  }
}

async function loadActivityLogs(page = 1) {
  currentPage = page;
  const tableBody = document.getElementById("table-body");
  tableBody.innerHTML = '<tr><td colspan="7" class="loading-container"><span class="spinner"></span><span>Retrieving activity records...</span></td></tr>';

  const search = (document.getElementById("table-search")?.value || "").trim();
  const moduleParam = document.getElementById("module-filter")?.value || "ALL";
  const actionParam = document.getElementById("action-filter")?.value || "ALL";

  const res = await apiClient.get("/api/activity-logs", {
    page: page,
    limit: pageLimit,
    search: search,
    module: moduleParam,
    action: actionParam
  });

  if (!res.success) {
    tableBody.innerHTML = `<tr><td colspan="7" class="empty-state"><p>${res.message || "Failed to load activity logs"}</p></td></tr>`;
    return;
  }

  const data = res.data || {};
  const items = data.items || [];
  const pagination = data.pagination || { total: 0, page: 1, total_pages: 1 };

  renderTable(items);
  renderPagination(pagination);
}

function getActionBadge(action) {
  const act = (action || "SYSTEM").toUpperCase();
  switch (act) {
    case 'CREATE':
    case 'SUBMIT':
      return `<span class="badge badge-active">${escapeHtml(act)}</span>`;
    case 'DELETE':
      return `<span class="badge badge-inactive">${escapeHtml(act)}</span>`;
    case 'UPDATE':
      return `<span class="badge" style="background:#fef3c7; color:#b45309;">${escapeHtml(act)}</span>`;
    default:
      return `<span class="badge" style="background:#e0f2fe; color:#0369a1;">${escapeHtml(act)}</span>`;
  }
}

function renderTable(items) {
  const tableBody = document.getElementById("table-body");

  if (items.length === 0) {
    tableBody.innerHTML = `
      <tr>
        <td colspan="7" class="empty-state">
          <div class="empty-state-icon">📋</div>
          <div class="empty-state-title">No Activity Logs Match Your Filter</div>
          <p>Activity records are generated automatically upon CREATE, UPDATE, DELETE, and SUBMIT actions.</p>
        </td>
      </tr>
    `;
    return;
  }

  tableBody.innerHTML = items.map(log => `
    <tr>
      <td><strong>#${log.id}</strong></td>
      <td>${getActionBadge(log.action)}</td>
      <td><span style="font-weight: 600; color: #475569;">[${escapeHtml(log.module)}]</span></td>
      <td><code>${log.record_id ? '#' + log.record_id : '—'}</code></td>
      <td><div style="font-size: 0.9rem; color: var(--text-main);">${escapeHtml(log.description || "System action")}</div></td>
      <td>
        <div style="font-weight: 600; font-size: 0.85rem;">${escapeHtml(log.user_name || "System")}</div>
        <small style="color: var(--text-muted);">${escapeHtml(log.user_email || "")}</small>
      </td>
      <td><small style="color: var(--text-light);">${log.created_at}</small></td>
    </tr>
  `).join("");
}

function renderPagination(p) {
  const countEl = document.getElementById("table-record-count");
  if (countEl) countEl.textContent = `Showing page ${p.page} of ${p.total_pages} (${p.total} total records)`;

  const container = document.getElementById("pagination-controls");
  if (!container) return;

  container.innerHTML = `
    <button class="btn btn-sm btn-outline" ${!p.has_prev ? 'disabled' : ''} onclick="loadActivityLogs(${p.page - 1})">◀ Prev</button>
    <span style="font-size: 0.85rem; font-weight: 600; padding: 0 6px;">Page ${p.page} / ${p.total_pages}</span>
    <button class="btn btn-sm btn-outline" ${!p.has_next ? 'disabled' : ''} onclick="loadActivityLogs(${p.page + 1})">Next ▶</button>
  `;
}

function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

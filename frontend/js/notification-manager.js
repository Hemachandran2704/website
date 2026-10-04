/**
 * Magnus Dynamic CMS - Notification Manager Controller
 */

let currentItems = [];
let editingItemId = null;

document.addEventListener("DOMContentLoaded", () => {
  if (!Auth.requireAdmin()) return;
  Auth.initSidebar();

  loadNotifications();
  setupEventListeners();
});

function setupEventListeners() {
  document.getElementById("btn-add-new").addEventListener("click", () => openModal());
  document.getElementById("modal-close-btn").addEventListener("click", () => closeModal());
  document.getElementById("modal-cancel-btn").addEventListener("click", () => closeModal());
  document.getElementById("view-modal-close-btn").addEventListener("click", () => closeViewModal());

  document.getElementById("item-form").addEventListener("submit", handleFormSubmit);

  const searchInput = document.getElementById("table-search");
  if (searchInput) {
    let debounceTimer;
    searchInput.addEventListener("input", () => {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => filterAndRender(), 200);
    });
  }

  const typeFilter = document.getElementById("type-filter");
  if (typeFilter) {
    typeFilter.addEventListener("change", () => filterAndRender());
  }

  const statusFilter = document.getElementById("status-filter");
  if (statusFilter) {
    statusFilter.addEventListener("change", () => loadNotifications());
  }
}

async function loadNotifications() {
  const tableBody = document.getElementById("table-body");
  tableBody.innerHTML = '<tr><td colspan="7" class="loading-container"><span class="spinner"></span><span>Loading notifications...</span></td></tr>';

  const status = document.getElementById("status-filter").value;
  const res = await apiClient.get("/api/notifications", { status });

  if (!res.success) {
    tableBody.innerHTML = `<tr><td colspan="7" class="empty-state"><p>${res.message || "Failed to load notifications"}</p></td></tr>`;
    return;
  }

  currentItems = res.data || [];
  filterAndRender();
}

function filterAndRender() {
  const searchTerm = (document.getElementById("table-search")?.value || "").toLowerCase().trim();
  const notifType = (document.getElementById("type-filter")?.value || "all").toLowerCase();

  const filtered = currentItems.filter(item => {
    const matchSearch = !searchTerm ||
      item.title.toLowerCase().includes(searchTerm) ||
      item.message.toLowerCase().includes(searchTerm);
    
    const matchType = notifType === "all" || item.type.toLowerCase() === notifType;
    return matchSearch && matchType;
  });

  renderTable(filtered);
}

function getBadgeForType(type) {
  switch (type.toLowerCase()) {
    case 'success':
      return '<span class="badge badge-active">✅ Success</span>';
    case 'warning':
      return '<span class="badge" style="background:#fef3c7; color:#b45309;">⚠️ Warning</span>';
    case 'alert':
      return '<span class="badge badge-inactive">🚨 Alert</span>';
    default:
      return '<span class="badge" style="background:#e0f2fe; color:#0369a1;">ℹ️ Info</span>';
  }
}

function renderTable(items) {
  const tableBody = document.getElementById("table-body");
  const countEl = document.getElementById("table-record-count");
  if (countEl) countEl.textContent = `Showing ${items.length} records`;

  if (items.length === 0) {
    tableBody.innerHTML = `
      <tr>
        <td colspan="7" class="empty-state">
          <div class="empty-state-icon">🔔</div>
          <div class="empty-state-title">No Notifications Found</div>
          <p>Click "+ Create Notification" above to send a new alert or message.</p>
        </td>
      </tr>
    `;
    return;
  }

  tableBody.innerHTML = items.map(item => `
    <tr>
      <td><strong>#${item.id}</strong></td>
      <td>
        <div style="font-weight: 600;">${escapeHtml(item.title)}</div>
        <small style="color: var(--text-muted);">${escapeHtml(item.message.substring(0, 55))}${item.message.length > 55 ? '...' : ''}</small>
      </td>
      <td>${getBadgeForType(item.type)}</td>
      <td><span class="badge badge-${item.status}">${item.status}</span></td>
      <td><small>${item.created_at}</small></td>
      <td><small>${item.updated_at || item.created_at}</small></td>
      <td>
        <div class="table-actions">
          <button class="btn btn-sm btn-action-view" onclick="viewNotification(${item.id})" title="View Details">👁️ View</button>
          <button class="btn btn-sm btn-action-edit" onclick="editNotification(${item.id})" title="Edit Notification">✏️ Edit</button>
          <button class="btn btn-sm btn-action-delete" onclick="deleteNotification(${item.id}, '${escapeHtml(item.title)}')" title="Delete">🗑️</button>
        </div>
      </td>
    </tr>
  `).join("");
}

function openModal(item = null) {
  editingItemId = item ? item.id : null;
  const modal = document.getElementById("crud-modal");
  const titleEl = document.getElementById("modal-title");
  const errorEl = document.getElementById("form-error");

  errorEl.style.display = "none";
  errorEl.textContent = "";

  if (item) {
    titleEl.textContent = `Edit Notification #${item.id}`;
    document.getElementById("notif-title").value = item.title;
    document.getElementById("notif-type").value = item.type;
    document.getElementById("notif-status").value = item.status;
    document.getElementById("notif-message").value = item.message;
  } else {
    titleEl.textContent = "Create Notification";
    document.getElementById("item-form").reset();
    document.getElementById("notif-type").value = "info";
    document.getElementById("notif-status").value = "active";
  }

  modal.classList.add("active");
}

function closeModal() {
  document.getElementById("crud-modal").classList.remove("active");
  editingItemId = null;
}

function closeViewModal() {
  document.getElementById("view-modal").classList.remove("active");
}

async function handleFormSubmit(e) {
  e.preventDefault();
  const errorEl = document.getElementById("form-error");
  const submitBtn = document.getElementById("modal-submit-btn");

  errorEl.style.display = "none";

  const payload = {
    title: document.getElementById("notif-title").value.trim(),
    type: document.getElementById("notif-type").value,
    status: document.getElementById("notif-status").value,
    message: document.getElementById("notif-message").value.trim()
  };

  submitBtn.disabled = true;
  submitBtn.textContent = "Saving...";

  let res;
  if (editingItemId) {
    res = await apiClient.put(`/api/notifications/${editingItemId}`, payload);
  } else {
    res = await apiClient.post("/api/notifications", payload);
  }

  submitBtn.disabled = false;
  submitBtn.textContent = "Save Notification";

  if (!res.success) {
    errorEl.textContent = res.message || "Operation failed.";
    if (res.errors) {
      errorEl.textContent += " " + Object.values(res.errors).join(" ");
    }
    errorEl.style.display = "block";
    return;
  }

  showToast(editingItemId ? "Notification updated successfully!" : "Notification broadcast created!", "success");
  closeModal();
  await loadNotifications();
}

function viewNotification(id) {
  const item = currentItems.find(i => i.id === id);
  if (!item) return;

  const modal = document.getElementById("view-modal");
  const body = document.getElementById("view-modal-body");
  document.getElementById("view-modal-title").textContent = `Notification #${item.id}: ${item.title}`;

  body.innerHTML = `
    <div class="view-detail-row">
      <span class="view-detail-label">Title</span>
      <span class="view-detail-value font-weight-bold">${escapeHtml(item.title)}</span>
    </div>
    <div class="view-detail-row">
      <span class="view-detail-label">Type & Status</span>
      <span class="view-detail-value">
        ${getBadgeForType(item.type)}
        <span class="badge badge-${item.status}" style="margin-left: 8px;">${item.status}</span>
      </span>
    </div>
    <div class="view-detail-row">
      <span class="view-detail-label">Message Content</span>
      <div style="background: #f8fafc; padding: 14px; border-radius: 6px; border: 1px solid var(--border-color); white-space: pre-wrap; font-size: 0.9rem; line-height: 1.6;">
        ${escapeHtml(item.message)}
      </div>
    </div>
    <div class="view-detail-row">
      <span class="view-detail-label">Created Date</span>
      <span class="view-detail-value">${item.created_at}</span>
    </div>
  `;

  modal.classList.add("active");
}

function editNotification(id) {
  const item = currentItems.find(i => i.id === id);
  if (item) openModal(item);
}

async function deleteNotification(id, title) {
  const confirmed = await confirmAction(
    `Are you sure you want to delete notification "${title}" (#${id})?`,
    "Delete Notification"
  );
  if (!confirmed) return;

  const res = await apiClient.delete(`/api/notifications/${id}`);
  if (res.success) {
    showToast("Notification deleted successfully.", "success");
    await loadNotifications();
  } else {
    showToast(res.message || "Failed to delete notification.", "error");
  }
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

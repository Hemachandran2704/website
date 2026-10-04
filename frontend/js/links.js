/**
 * Magnus Dynamic CMS - Links Admin Controller
 */

let currentItems = [];
let editingItemId = null;

document.addEventListener("DOMContentLoaded", () => {
  if (!Auth.checkAuth()) return;
  Auth.initSidebar();

  loadLinks();
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
    searchInput.addEventListener("input", (e) => {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => filterAndRender(), 200);
    });
  }

  const statusFilter = document.getElementById("status-filter");
  if (statusFilter) {
    statusFilter.addEventListener("change", () => loadLinks());
  }
}

async function loadLinks() {
  const tableBody = document.getElementById("table-body");
  tableBody.innerHTML = '<tr><td colspan="7" class="loading-container"><span class="spinner"></span><span>Loading links...</span></td></tr>';

  const status = document.getElementById("status-filter").value;
  const res = await apiClient.get("/api/links", { status });

  if (!res.success) {
    tableBody.innerHTML = `<tr><td colspan="7" class="empty-state"><p>${res.message || "Failed to load links"}</p></td></tr>`;
    return;
  }

  currentItems = res.data || [];
  filterAndRender();
  renderLiveLinksPreview();
}

function filterAndRender() {
  const searchTerm = (document.getElementById("table-search")?.value || "").toLowerCase().trim();
  const filtered = currentItems.filter(item => {
    return !searchTerm ||
      item.title.toLowerCase().includes(searchTerm) ||
      item.url.toLowerCase().includes(searchTerm) ||
      (item.description && item.description.toLowerCase().includes(searchTerm));
  });

  renderTable(filtered);
}

function renderTable(items) {
  const tableBody = document.getElementById("table-body");
  const countEl = document.getElementById("table-record-count");
  if (countEl) countEl.textContent = `Showing ${items.length} records`;

  if (items.length === 0) {
    tableBody.innerHTML = `
      <tr>
        <td colspan="7" class="empty-state">
          <div class="empty-state-icon">🔗</div>
          <div class="empty-state-title">No Links Found</div>
          <p>Click "+ Add Link" above to configure your verified web links.</p>
        </td>
      </tr>
    `;
    return;
  }

  tableBody.innerHTML = items.map(link => `
    <tr>
      <td><strong>#${link.id}</strong></td>
      <td>
        <div style="font-weight: 600;">${escapeHtml(link.title)}</div>
        <small style="color: var(--text-muted);">${escapeHtml(link.description || 'No description')}</small>
      </td>
      <td>
        <a href="${escapeHtml(link.url)}" target="${link.target}" rel="noopener noreferrer" style="display: inline-flex; align-items: center; gap: 4px;">
          <code>${escapeHtml(link.url.substring(0, 35))}${link.url.length > 35 ? '...' : ''}</code> ↗
        </a>
      </td>
      <td><code>${link.target}</code></td>
      <td>
        <span class="badge badge-${link.status}">${link.status}</span>
        <small style="color: var(--text-light); margin-left: 6px;">Order: ${link.display_order}</small>
      </td>
      <td><small>${link.created_at}</small></td>
      <td>
        <div class="table-actions">
          <button class="btn btn-sm btn-action-view" onclick="viewLink(${link.id})" title="View Details">👁️ View</button>
          <button class="btn btn-sm btn-action-edit" ${link.can_manage ? "" : "disabled"} onclick="editLink(${link.id})" title="Edit Link">✏️ Edit</button>
          <button class="btn btn-sm btn-action-delete" ${link.can_manage ? "" : "disabled"} onclick="deleteLink(${link.id})" title="Delete Link">🗑️ Delete</button>
        </div>
      </td>
    </tr>
  `).join("");
}

function renderLiveLinksPreview() {
  const container = document.getElementById("preview-links-container");
  if (!container) return;

  const activeLinks = currentItems.filter(l => l.status === "active");

  if (activeLinks.length === 0) {
    container.innerHTML = "<p style='color: var(--text-muted);'>No active links to preview.</p>";
    return;
  }

  container.innerHTML = activeLinks.map(l => `
    <div style="display: flex; align-items: center; justify-content: space-between; padding: 12px 16px; background: #fafbfc; border: 1px solid var(--border-color); border-radius: 6px; margin-bottom: 8px;">
      <div>
        <div style="font-weight: 600; font-size: 0.9rem;">${escapeHtml(l.title)}</div>
        <div style="font-size: 0.775rem; color: var(--text-muted);">${escapeHtml(l.description || l.url)}</div>
      </div>
      <a href="${escapeHtml(l.url)}" target="${l.target}" rel="noopener noreferrer" class="btn btn-sm btn-outline">
        Open ${l.target === '_blank' ? '↗' : '→'}
      </a>
    </div>
  `).join("");
}

function openModal(link = null) {
  editingItemId = link ? link.id : null;
  document.getElementById("modal-title").textContent = link ? "Edit Link" : "Create New Link";
  document.getElementById("link-title").value = link ? link.title : "";
  document.getElementById("link-url").value = link ? link.url : "";
  document.getElementById("link-target").value = link ? link.target : "_self";
  document.getElementById("link-description").value = link ? (link.description || "") : "";
  document.getElementById("link-order").value = link ? link.display_order : 0;
  document.getElementById("link-status").value = link ? link.status : "active";

  clearFormErrors();
  document.getElementById("crud-modal").classList.add("active");
}

function closeModal() {
  document.getElementById("crud-modal").classList.remove("active");
  editingItemId = null;
}

window.viewLink = function(id) {
  const link = currentItems.find(t => t.id === id);
  if (!link) return;

  document.getElementById("view-link-title").textContent = link.title;
  document.getElementById("view-link-id").textContent = `#${link.id}`;
  document.getElementById("view-link-url").textContent = link.url;
  document.getElementById("view-link-target").textContent = link.target;
  document.getElementById("view-link-status").innerHTML = `<span class="badge badge-${link.status}">${link.status}</span>`;
  document.getElementById("view-link-desc").textContent = link.description || "No description provided.";
  document.getElementById("view-link-order").textContent = link.display_order;
  document.getElementById("view-link-created").textContent = link.created_at;

  document.getElementById("view-modal").classList.add("active");
};

function closeViewModal() {
  document.getElementById("view-modal").classList.remove("active");
}

window.editLink = function(id) {
  const link = currentItems.find(t => t.id === id);
  if (link) openModal(link);
};

window.deleteLink = async function(id) {
  const link = currentItems.find(t => t.id === id);
  const title = link ? link.title : `Link #${id}`;

  const confirmed = await confirmAction(`Delete link "${title}"?`, "Delete Link");
  if (!confirmed) return;

  const res = await apiClient.delete(`/api/links/${id}`);
  if (!res.success) {
    showToast(res.message || "Failed to delete link", "error");
    return;
  }

  showToast("Link deleted successfully", "success");
  await loadLinks();
};

async function handleFormSubmit(e) {
  e.preventDefault();
  clearFormErrors();

  const title = document.getElementById("link-title").value.trim();
  const url = document.getElementById("link-url").value.trim();
  const target = document.getElementById("link-target").value;
  const description = document.getElementById("link-description").value.trim();
  const display_order = parseInt(document.getElementById("link-order").value || 0);
  const status = document.getElementById("link-status").value;

  let hasError = false;
  if (!title) {
    setFieldError("link-title", "Title is required.");
    hasError = true;
  }
  if (!url) {
    setFieldError("link-url", "URL is required.");
    hasError = true;
  } else if (url.startsWith("javascript:") || url.startsWith("data:")) {
    setFieldError("link-url", "Dangerous URL protocol detected.");
    hasError = true;
  }
  if (hasError) return;

  const payload = { title, url, target, description, display_order, status };
  const submitBtn = document.getElementById("modal-submit-btn");
  submitBtn.disabled = true;
  submitBtn.innerHTML = '<span class="spinner" style="width:14px;height:14px;border-width:2px;"></span> Saving...';

  let res;
  if (editingItemId) {
    res = await apiClient.put(`/api/links/${editingItemId}`, payload);
  } else {
    res = await apiClient.post("/api/links", payload);
  }

  submitBtn.disabled = false;
  submitBtn.textContent = "Save Link";

  if (!res.success) {
    if (res.errors) {
      Object.keys(res.errors).forEach(key => {
        setFieldError(`link-${key}`, res.errors[key]);
      });
    }
    showToast(res.message || "Failed to save link", "error");
    return;
  }

  showToast(editingItemId ? "Link updated successfully" : "Link created successfully", "success");
  closeModal();
  await loadLinks();
}

function setFieldError(fieldId, message) {
  const field = document.getElementById(fieldId);
  if (field) {
    field.classList.add("is-invalid");
    const errSpan = document.getElementById(`${fieldId}-error`);
    if (errSpan) errSpan.textContent = message;
  }
}

function clearFormErrors() {
  document.querySelectorAll(".form-control").forEach(el => el.classList.remove("is-invalid"));
  document.querySelectorAll(".form-error").forEach(el => el.textContent = "");
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

/**
 * Magnus Dynamic CMS - Content Manager Controller
 */

let currentItems = [];
let editingItemId = null;

document.addEventListener("DOMContentLoaded", () => {
  if (!Auth.requireAdmin()) return;
  Auth.initSidebar();

  loadContent();
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

  const categoryFilter = document.getElementById("category-filter");
  if (categoryFilter) {
    categoryFilter.addEventListener("change", () => filterAndRender());
  }

  const statusFilter = document.getElementById("status-filter");
  if (statusFilter) {
    statusFilter.addEventListener("change", () => loadContent());
  }
}

async function loadContent() {
  const tableBody = document.getElementById("table-body");
  tableBody.innerHTML = '<tr><td colspan="7" class="loading-container"><span class="spinner"></span><span>Loading content...</span></td></tr>';

  const status = document.getElementById("status-filter").value;
  const res = await apiClient.get("/api/content", { status });

  if (!res.success) {
    tableBody.innerHTML = `<tr><td colspan="7" class="empty-state"><p>${res.message || "Failed to load content"}</p></td></tr>`;
    return;
  }

  currentItems = res.data || [];
  filterAndRender();
}

function filterAndRender() {
  const searchTerm = (document.getElementById("table-search")?.value || "").toLowerCase().trim();
  const category = (document.getElementById("category-filter")?.value || "all").toLowerCase();

  const filtered = currentItems.filter(item => {
    const matchSearch = !searchTerm ||
      item.title.toLowerCase().includes(searchTerm) ||
      (item.description && item.description.toLowerCase().includes(searchTerm)) ||
      (item.content && item.content.toLowerCase().includes(searchTerm));
    
    const matchCategory = category === "all" || (item.category && item.category.toLowerCase() === category);
    return matchSearch && matchCategory;
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
          <div class="empty-state-icon">📝</div>
          <div class="empty-state-title">No Content Records Found</div>
          <p>Click "+ Add New Content" above to create your first content entry.</p>
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
        <small style="color: var(--text-muted);">${escapeHtml(item.description || item.content.substring(0, 50))}</small>
      </td>
      <td><span class="badge" style="background:#f1f5f9; color:#334155;">${escapeHtml(item.category || "General")}</span></td>
      <td>
        <span class="badge badge-${item.status}">${item.status}</span>
        <small style="color: var(--text-light); margin-left: 6px;">Order: ${item.display_order}</small>
      </td>
      <td><small>${item.created_at}</small></td>
      <td><small>${item.updated_at || item.created_at}</small></td>
      <td>
        <div class="table-actions">
          <button class="btn btn-sm btn-action-view" onclick="viewContent(${item.id})" title="View Details">👁️ View</button>
          <button class="btn btn-sm btn-action-edit" onclick="editContent(${item.id})" title="Edit Content">✏️ Edit</button>
          <button class="btn btn-sm btn-action-delete" onclick="deleteContent(${item.id}, '${escapeHtml(item.title)}')" title="Delete">🗑️</button>
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
    titleEl.textContent = `Edit Content #${item.id}`;
    document.getElementById("content-title").value = item.title;
    document.getElementById("content-category").value = item.category || "General";
    document.getElementById("content-desc").value = item.description || "";
    document.getElementById("content-body-text").value = item.content;
    document.getElementById("content-order").value = item.display_order || 0;
    document.getElementById("content-status").value = item.status;
  } else {
    titleEl.textContent = "Add Content Record";
    document.getElementById("item-form").reset();
    document.getElementById("content-category").value = "General";
    document.getElementById("content-order").value = (currentItems.length + 1) * 10;
    document.getElementById("content-status").value = "active";
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
    title: document.getElementById("content-title").value.trim(),
    category: document.getElementById("content-category").value.trim() || "General",
    description: document.getElementById("content-desc").value.trim(),
    content: document.getElementById("content-body-text").value.trim(),
    display_order: parseInt(document.getElementById("content-order").value, 10) || 0,
    status: document.getElementById("content-status").value
  };

  submitBtn.disabled = true;
  submitBtn.textContent = "Saving...";

  let res;
  if (editingItemId) {
    res = await apiClient.put(`/api/content/${editingItemId}`, payload);
  } else {
    res = await apiClient.post("/api/content", payload);
  }

  submitBtn.disabled = false;
  submitBtn.textContent = "Save Content";

  if (!res.success) {
    errorEl.textContent = res.message || "Operation failed.";
    if (res.errors) {
      errorEl.textContent += " " + Object.values(res.errors).join(" ");
    }
    errorEl.style.display = "block";
    return;
  }

  showToast(editingItemId ? "Content updated successfully!" : "Content created successfully!", "success");
  closeModal();
  await loadContent();
}

async function viewContent(id) {
  const item = currentItems.find(i => i.id === id);
  if (!item) return;

  const modal = document.getElementById("view-modal");
  const body = document.getElementById("view-modal-body");
  document.getElementById("view-modal-title").textContent = `Content #${item.id}: ${item.title}`;

  body.innerHTML = `
    <div class="view-detail-row">
      <span class="view-detail-label">Title</span>
      <span class="view-detail-value font-weight-bold">${escapeHtml(item.title)}</span>
    </div>
    <div class="view-detail-row">
      <span class="view-detail-label">Category</span>
      <span class="view-detail-value"><span class="badge" style="background:#f1f5f9; color:#334155;">${escapeHtml(item.category || "General")}</span></span>
    </div>
    <div class="view-detail-row">
      <span class="view-detail-label">Status / Order</span>
      <span class="view-detail-value">
        <span class="badge badge-${item.status}">${item.status}</span>
        <span style="margin-left: 10px; color: var(--text-muted);">Display Order: ${item.display_order}</span>
      </span>
    </div>
    <div class="view-detail-row">
      <span class="view-detail-label">Description</span>
      <span class="view-detail-value">${escapeHtml(item.description || "—")}</span>
    </div>
    <div class="view-detail-row">
      <span class="view-detail-label">Content Body</span>
      <div style="background: #f8fafc; padding: 14px; border-radius: 6px; border: 1px solid var(--border-color); white-space: pre-wrap; font-size: 0.9rem; line-height: 1.6;">
        ${escapeHtml(item.content)}
      </div>
    </div>
    <div class="view-detail-row">
      <span class="view-detail-label">Created At</span>
      <span class="view-detail-value">${item.created_at}</span>
    </div>
  `;

  modal.classList.add("active");
}

function editContent(id) {
  const item = currentItems.find(i => i.id === id);
  if (item) openModal(item);
}

async function deleteContent(id, title) {
  const confirmed = await confirmAction(
    `Are you sure you want to permanently delete content item "${title}" (#${id})?`,
    "Delete Content"
  );
  if (!confirmed) return;

  const res = await apiClient.delete(`/api/content/${id}`);
  if (res.success) {
    showToast("Content record deleted successfully.", "success");
    await loadContent();
  } else {
    showToast(res.message || "Failed to delete content record.", "error");
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

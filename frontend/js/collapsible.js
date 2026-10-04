/**
 * Magnus Dynamic CMS - Collapsible Content Admin Controller
 */

let currentItems = [];
let editingItemId = null;

document.addEventListener("DOMContentLoaded", () => {
  if (!Auth.checkAuth()) return;
  Auth.initSidebar();

  loadCollapsibleItems();
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
    statusFilter.addEventListener("change", () => loadCollapsibleItems());
  }
}

async function loadCollapsibleItems() {
  const tableBody = document.getElementById("table-body");
  tableBody.innerHTML = '<tr><td colspan="6" class="loading-container"><span class="spinner"></span><span>Loading collapsible items...</span></td></tr>';

  const status = document.getElementById("status-filter").value;
  const res = await apiClient.get("/api/collapsible", { status });

  if (!res.success) {
    tableBody.innerHTML = `<tr><td colspan="6" class="empty-state"><p>${res.message || "Failed to load records"}</p></td></tr>`;
    return;
  }

  currentItems = res.data || [];
  filterAndRender();
  renderLiveAccordionPreview();
}

function filterAndRender() {
  const searchTerm = (document.getElementById("table-search")?.value || "").toLowerCase().trim();
  const filtered = currentItems.filter(item => {
    return !searchTerm ||
      item.title.toLowerCase().includes(searchTerm) ||
      item.content.toLowerCase().includes(searchTerm);
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
        <td colspan="6" class="empty-state">
          <div class="empty-state-icon">📂</div>
          <div class="empty-state-title">No Collapsible Items Found</div>
          <p>Click "+ Add Collapsible Item" above to create an expandable section.</p>
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
        <small style="color: var(--text-muted);">${escapeHtml(item.content.substring(0, 50))}${item.content.length > 50 ? '...' : ''}</small>
      </td>
      <td>
        <span class="badge badge-${item.status}">${item.status}</span>
        <small style="color: var(--text-light); margin-left: 6px;">Order: ${item.display_order}</small>
      </td>
      <td><small>${item.created_at}</small></td>
      <td><small>${item.updated_at || item.created_at}</small></td>
      <td>
        <div class="table-actions">
          <button class="btn btn-sm btn-action-view" onclick="viewItem(${item.id})" title="View Details">👁️ View</button>
          <button class="btn btn-sm btn-action-edit" ${item.can_manage ? "" : "disabled"} onclick="editItem(${item.id})" title="Edit Item">✏️ Edit</button>
          <button class="btn btn-sm btn-action-delete" ${item.can_manage ? "" : "disabled"} onclick="deleteItem(${item.id})" title="Delete Item">🗑️ Delete</button>
        </div>
      </td>
    </tr>
  `).join("");
}

function renderLiveAccordionPreview() {
  const accordionContainer = document.getElementById("preview-accordion-container");
  if (!accordionContainer) return;

  const activeItems = currentItems.filter(i => i.status === "active");

  if (activeItems.length === 0) {
    accordionContainer.innerHTML = "<p style='color: var(--text-muted);'>No active collapsible items to preview.</p>";
    return;
  }

  accordionContainer.innerHTML = activeItems.map((item, idx) => `
    <div class="accordion-item" style="border: 1px solid var(--border-color); border-radius: 6px; margin-bottom: 8px; overflow: hidden;">
      <div class="accordion-header" 
           style="padding: 14px 18px; background: #f8fafc; cursor: pointer; display: flex; align-items: center; justify-content: space-between; user-select: none;"
           onclick="togglePreviewAccordion(this)">
        <span style="font-weight: 600; font-size: 0.95rem; color: var(--text-main);">${escapeHtml(item.title)}</span>
        <span class="accordion-icon" style="font-size: 0.85rem; color: var(--text-muted); transition: transform 0.2s;">➕</span>
      </div>
      <div class="accordion-body" style="display: none; padding: 16px 18px; background: #ffffff; border-top: 1px solid var(--border-color); font-size: 0.875rem; color: var(--text-muted); line-height: 1.6;">
        ${escapeHtml(item.content)}
      </div>
    </div>
  `).join("");
}

window.togglePreviewAccordion = function(headerEl) {
  const bodyEl = headerEl.nextElementSibling;
  const icon = headerEl.querySelector(".accordion-icon");
  if (bodyEl.style.display === "none" || !bodyEl.style.display) {
    bodyEl.style.display = "block";
    icon.textContent = "➖";
  } else {
    bodyEl.style.display = "none";
    icon.textContent = "➕";
  }
};

function openModal(item = null) {
  editingItemId = item ? item.id : null;
  document.getElementById("modal-title").textContent = item ? "Edit Collapsible Item" : "Create New Collapsible Item";
  document.getElementById("item-title").value = item ? item.title : "";
  document.getElementById("item-content").value = item ? item.content : "";
  document.getElementById("item-order").value = item ? item.display_order : 0;
  document.getElementById("item-status").value = item ? item.status : "active";

  clearFormErrors();
  document.getElementById("crud-modal").classList.add("active");
}

function closeModal() {
  document.getElementById("crud-modal").classList.remove("active");
  editingItemId = null;
}

window.viewItem = function(id) {
  const item = currentItems.find(t => t.id === id);
  if (!item) return;

  document.getElementById("view-item-title").textContent = item.title;
  document.getElementById("view-item-id").textContent = `#${item.id}`;
  document.getElementById("view-item-status").innerHTML = `<span class="badge badge-${item.status}">${item.status}</span>`;
  document.getElementById("view-item-order").textContent = item.display_order;
  document.getElementById("view-item-content").textContent = item.content;
  document.getElementById("view-item-created").textContent = item.created_at;
  document.getElementById("view-item-updated").textContent = item.updated_at || item.created_at;

  document.getElementById("view-modal").classList.add("active");
};

function closeViewModal() {
  document.getElementById("view-modal").classList.remove("active");
}

window.editItem = function(id) {
  const item = currentItems.find(t => t.id === id);
  if (item) openModal(item);
};

window.deleteItem = async function(id) {
  const item = currentItems.find(t => t.id === id);
  const title = item ? item.title : `Item #${id}`;

  const confirmed = await confirmAction(`Delete collapsible item "${title}"?`, "Delete Item");
  if (!confirmed) return;

  const res = await apiClient.delete(`/api/collapsible/${id}`);
  if (!res.success) {
    showToast(res.message || "Failed to delete item", "error");
    return;
  }

  showToast("Item deleted successfully", "success");
  await loadCollapsibleItems();
};

async function handleFormSubmit(e) {
  e.preventDefault();
  clearFormErrors();

  const title = document.getElementById("item-title").value.trim();
  const content = document.getElementById("item-content").value.trim();
  const display_order = parseInt(document.getElementById("item-order").value || 0);
  const status = document.getElementById("item-status").value;

  let hasError = false;
  if (!title) {
    setFieldError("item-title", "Title is required.");
    hasError = true;
  }
  if (!content) {
    setFieldError("item-content", "Content is required.");
    hasError = true;
  }
  if (hasError) return;

  const payload = { title, content, display_order, status };
  const submitBtn = document.getElementById("modal-submit-btn");
  submitBtn.disabled = true;
  submitBtn.innerHTML = '<span class="spinner" style="width:14px;height:14px;border-width:2px;"></span> Saving...';

  let res;
  if (editingItemId) {
    res = await apiClient.put(`/api/collapsible/${editingItemId}`, payload);
  } else {
    res = await apiClient.post("/api/collapsible", payload);
  }

  submitBtn.disabled = false;
  submitBtn.textContent = "Save Item";

  if (!res.success) {
    if (res.errors) {
      Object.keys(res.errors).forEach(key => {
        setFieldError(`item-${key}`, res.errors[key]);
      });
    }
    showToast(res.message || "Failed to save item", "error");
    return;
  }

  showToast(editingItemId ? "Item updated successfully" : "Item created successfully", "success");
  closeModal();
  await loadCollapsibleItems();
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

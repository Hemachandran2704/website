/**
 * Magnus Dynamic CMS - Multiple Tabs Admin Controller
 */

let currentItems = [];
let editingItemId = null;

document.addEventListener("DOMContentLoaded", () => {
  if (!Auth.checkAuth()) return;
  Auth.initSidebar();

  loadTabs();
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
    statusFilter.addEventListener("change", () => loadTabs());
  }
}

async function loadTabs() {
  const tableBody = document.getElementById("table-body");
  tableBody.innerHTML = '<tr><td colspan="6" class="loading-container"><span class="spinner"></span><span>Loading tabs...</span></td></tr>';

  const status = document.getElementById("status-filter").value;
  const res = await apiClient.get("/api/tabs", { status });

  if (!res.success) {
    tableBody.innerHTML = `<tr><td colspan="6" class="empty-state"><p>${res.message || "Failed to load tabs"}</p></td></tr>`;
    return;
  }

  currentItems = res.data || [];
  filterAndRender();
  renderLivePreview();
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
          <div class="empty-state-icon">📑</div>
          <div class="empty-state-title">No Tabs Found</div>
          <p>Click "+ Add New Tab" above to create your first dynamic tab entry.</p>
        </td>
      </tr>
    `;
    return;
  }

  tableBody.innerHTML = items.map(tab => `
    <tr>
      <td><strong>#${tab.id}</strong></td>
      <td>
        <div style="font-weight: 600;">${escapeHtml(tab.title)}</div>
        <small style="color: var(--text-muted);">${escapeHtml(tab.content.substring(0, 45))}${tab.content.length > 45 ? '...' : ''}</small>
      </td>
      <td>
        <span class="badge badge-${tab.status}">${tab.status}</span>
        <small style="color: var(--text-light); margin-left: 6px;">Order: ${tab.display_order}</small>
      </td>
      <td><small>${tab.created_at}</small></td>
      <td><small>${tab.updated_at || tab.created_at}</small></td>
      <td>
        <div class="table-actions">
          <button class="btn btn-sm btn-action-view" onclick="viewTab(${tab.id})" title="View Details">👁️ View</button>
          <button class="btn btn-sm btn-action-edit" ${tab.can_manage ? "" : "disabled"} onclick="editTab(${tab.id})" title="Edit Tab">✏️ Edit</button>
          <button class="btn btn-sm btn-action-delete" ${tab.can_manage ? "" : "disabled"} onclick="deleteTab(${tab.id})" title="Delete Tab">🗑️ Delete</button>
        </div>
      </td>
    </tr>
  `).join("");
}

function renderLivePreview() {
  const previewTabsNav = document.getElementById("preview-tabs-nav");
  const previewTabContent = document.getElementById("preview-tab-content");
  if (!previewTabsNav || !previewTabContent) return;

  const activeTabs = currentItems.filter(t => t.status === "active");

  if (activeTabs.length === 0) {
    previewTabsNav.innerHTML = "";
    previewTabContent.innerHTML = "<p style='color: var(--text-muted);'>No active tabs available to preview.</p>";
    return;
  }

  previewTabsNav.innerHTML = activeTabs.map((t, idx) => `
    <button class="btn btn-outline btn-sm preview-tab-btn ${idx === 0 ? 'btn-primary' : ''}" 
            data-tab-id="${t.id}" 
            onclick="switchPreviewTab(${t.id})">
      ${escapeHtml(t.title)}
    </button>
  `).join("");

  previewTabContent.innerHTML = `
    <div style="padding: 16px; background: #fafbfc; border-radius: 6px; border: 1px solid var(--border-color);">
      <h4 style="margin-bottom: 8px;">${escapeHtml(activeTabs[0].title)}</h4>
      <p style="white-space: pre-line;">${escapeHtml(activeTabs[0].content)}</p>
    </div>
  `;
}

window.switchPreviewTab = function(tabId) {
  const activeTabs = currentItems.filter(t => t.status === "active");
  const tab = activeTabs.find(t => t.id === tabId);
  if (!tab) return;

  document.querySelectorAll(".preview-tab-btn").forEach(btn => {
    if (parseInt(btn.getAttribute("data-tab-id")) === tabId) {
      btn.className = "btn btn-primary btn-sm preview-tab-btn";
    } else {
      btn.className = "btn btn-outline btn-sm preview-tab-btn";
    }
  });

  const previewTabContent = document.getElementById("preview-tab-content");
  previewTabContent.innerHTML = `
    <div style="padding: 16px; background: #fafbfc; border-radius: 6px; border: 1px solid var(--border-color);">
      <h4 style="margin-bottom: 8px;">${escapeHtml(tab.title)}</h4>
      <p style="white-space: pre-line;">${escapeHtml(tab.content)}</p>
    </div>
  `;
};

function openModal(tab = null) {
  editingItemId = tab ? tab.id : null;
  document.getElementById("modal-title").textContent = tab ? "Edit Tab" : "Create New Tab";
  document.getElementById("tab-title").value = tab ? tab.title : "";
  document.getElementById("tab-content").value = tab ? tab.content : "";
  document.getElementById("tab-order").value = tab ? tab.display_order : 0;
  document.getElementById("tab-status").value = tab ? tab.status : "active";

  clearFormErrors();
  document.getElementById("crud-modal").classList.add("active");
}

function closeModal() {
  document.getElementById("crud-modal").classList.remove("active");
  editingItemId = null;
}

window.viewTab = function(id) {
  const tab = currentItems.find(t => t.id === id);
  if (!tab) return;

  document.getElementById("view-tab-title").textContent = tab.title;
  document.getElementById("view-tab-id").textContent = `#${tab.id}`;
  document.getElementById("view-tab-status").innerHTML = `<span class="badge badge-${tab.status}">${tab.status}</span>`;
  document.getElementById("view-tab-order").textContent = tab.display_order;
  document.getElementById("view-tab-content").textContent = tab.content;
  document.getElementById("view-tab-created").textContent = tab.created_at;
  document.getElementById("view-tab-updated").textContent = tab.updated_at || tab.created_at;

  document.getElementById("view-modal").classList.add("active");
};

function closeViewModal() {
  document.getElementById("view-modal").classList.remove("active");
}

window.editTab = function(id) {
  const tab = currentItems.find(t => t.id === id);
  if (tab) openModal(tab);
};

window.deleteTab = async function(id) {
  const tab = currentItems.find(t => t.id === id);
  const title = tab ? tab.title : `Tab #${id}`;

  const confirmed = await confirmAction(`Are you sure you want to delete tab "${title}"? This action cannot be undone.`, "Delete Tab");
  if (!confirmed) return;

  const res = await apiClient.delete(`/api/tabs/${id}`);
  if (!res.success) {
    showToast(res.message || "Failed to delete tab", "error");
    return;
  }

  showToast("Tab deleted successfully", "success");
  await loadTabs();
};

async function handleFormSubmit(e) {
  e.preventDefault();
  clearFormErrors();

  const title = document.getElementById("tab-title").value.trim();
  const content = document.getElementById("tab-content").value.trim();
  const display_order = parseInt(document.getElementById("tab-order").value || 0);
  const status = document.getElementById("tab-status").value;

  let hasError = false;
  if (!title) {
    setFieldError("tab-title", "Title is required.");
    hasError = true;
  }
  if (!content) {
    setFieldError("tab-content", "Content is required.");
    hasError = true;
  }
  if (hasError) return;

  const payload = { title, content, display_order, status };
  const submitBtn = document.getElementById("modal-submit-btn");
  submitBtn.disabled = true;
  submitBtn.innerHTML = '<span class="spinner" style="width:14px;height:14px;border-width:2px;"></span> Saving...';

  let res;
  if (editingItemId) {
    res = await apiClient.put(`/api/tabs/${editingItemId}`, payload);
  } else {
    res = await apiClient.post("/api/tabs", payload);
  }

  submitBtn.disabled = false;
  submitBtn.textContent = "Save Tab";

  if (!res.success) {
    if (res.errors) {
      Object.keys(res.errors).forEach(key => {
        setFieldError(`tab-${key}`, res.errors[key]);
      });
    }
    showToast(res.message || "Failed to save tab", "error");
    return;
  }

  showToast(editingItemId ? "Tab updated successfully" : "Tab created successfully", "success");
  closeModal();
  await loadTabs();
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

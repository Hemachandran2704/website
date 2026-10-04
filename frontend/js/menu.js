/**
 * Magnus Dynamic CMS - Navigation Menu Admin Controller
 */

let currentItems = [];
let editingItemId = null;

document.addEventListener("DOMContentLoaded", () => {
  if (!Auth.checkAuth()) return;
  Auth.initSidebar();

  loadMenus();
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
    statusFilter.addEventListener("change", () => loadMenus());
  }
}

async function loadMenus() {
  const tableBody = document.getElementById("table-body");
  tableBody.innerHTML = '<tr><td colspan="7" class="loading-container"><span class="spinner"></span><span>Loading menus...</span></td></tr>';

  const status = document.getElementById("status-filter").value;
  const res = await apiClient.get("/api/menus", { status });

  if (!res.success) {
    tableBody.innerHTML = `<tr><td colspan="7" class="empty-state"><p>${res.message || "Failed to load menus"}</p></td></tr>`;
    return;
  }

  currentItems = res.data || [];
  filterAndRender();
  renderLiveTreePreview();
}

function filterAndRender() {
  const searchTerm = (document.getElementById("table-search")?.value || "").toLowerCase().trim();
  const filtered = currentItems.filter(item => {
    return !searchTerm ||
      item.name.toLowerCase().includes(searchTerm) ||
      item.url.toLowerCase().includes(searchTerm) ||
      (item.parent_name && item.parent_name.toLowerCase().includes(searchTerm));
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
          <div class="empty-state-icon">🗂️</div>
          <div class="empty-state-title">No Menu Items Found</div>
          <p>Click "+ Add Menu Item" above to configure your navigation tree.</p>
        </td>
      </tr>
    `;
    return;
  }

  tableBody.innerHTML = items.map(menu => `
    <tr>
      <td><strong>#${menu.id}</strong></td>
      <td>
        <div style="font-weight: 600;">
          ${menu.parent_id ? '<span style="color: var(--text-light); margin-right: 4px;">↳</span>' : ''}
          ${escapeHtml(menu.name)}
        </div>
      </td>
      <td><code>${escapeHtml(menu.url)}</code></td>
      <td>
        ${menu.parent_name ? `<span class="badge" style="background:#f1f5f9; color:#475569;">${escapeHtml(menu.parent_name)}</span>` : '<span style="color: var(--text-light); font-size: 0.75rem;">None (Root)</span>'}
      </td>
      <td>
        <span class="badge badge-${menu.status}">${menu.status}</span>
        <small style="color: var(--text-light); margin-left: 6px;">Order: ${menu.display_order}</small>
      </td>
      <td><small>${menu.created_at}</small></td>
      <td>
        <div class="table-actions">
          <button class="btn btn-sm btn-action-view" onclick="viewMenu(${menu.id})" title="View Details">👁️ View</button>
          <button class="btn btn-sm btn-action-edit" ${menu.can_manage ? "" : "disabled"} onclick="editMenu(${menu.id})" title="Edit Menu">✏️ Edit</button>
          <button class="btn btn-sm btn-action-delete" ${menu.can_manage ? "" : "disabled"} onclick="deleteMenu(${menu.id})" title="Delete Menu">🗑️ Delete</button>
        </div>
      </td>
    </tr>
  `).join("");
}

function renderLiveTreePreview() {
  const treeContainer = document.getElementById("preview-menu-tree");
  if (!treeContainer) return;

  // Build tree from active items
  const activeItems = currentItems.filter(m => m.status === "active");

  function buildSubtree(parentId) {
    const children = activeItems.filter(m => m.parent_id === parentId);
    if (children.length === 0) return "";
    return `
      <ul style="list-style: none; padding-left: 20px; border-left: 2px solid var(--border-color); margin-top: 6px;">
        ${children.map(child => `
          <li style="margin-bottom: 8px;">
            <div style="display: flex; align-items: center; gap: 8px;">
              <span style="font-weight: 500; font-size: 0.875rem;">${escapeHtml(child.name)}</span>
              <code style="font-size: 0.75rem; color: var(--text-muted); background: #f1f5f9; padding: 2px 6px; border-radius: 4px;">${escapeHtml(child.url)}</code>
            </div>
            ${buildSubtree(child.id)}
          </li>
        `).join("")}
      </ul>
    `;
  }

  const rootItems = activeItems.filter(m => !m.parent_id);

  if (rootItems.length === 0) {
    treeContainer.innerHTML = "<p style='color: var(--text-muted);'>No active menu items available to preview.</p>";
    return;
  }

  treeContainer.innerHTML = `
    <ul style="list-style: none; padding: 0;">
      ${rootItems.map(item => `
        <li style="margin-bottom: 12px;">
          <div style="display: flex; align-items: center; gap: 8px;">
            <span style="font-weight: 700; color: var(--primary); font-size: 0.95rem;">📁 ${escapeHtml(item.name)}</span>
            <code style="font-size: 0.75rem; color: var(--text-muted); background: #f1f5f9; padding: 2px 6px; border-radius: 4px;">${escapeHtml(item.url)}</code>
          </div>
          ${buildSubtree(item.id)}
        </li>
      `).join("")}
    </ul>
  `;
}

function populateParentDropdown(excludeId = null) {
  const select = document.getElementById("menu-parent");
  select.innerHTML = '<option value="">None (Top-level Menu)</option>';

  currentItems.forEach(item => {
    if (excludeId && item.id === excludeId) return; // Prevent self as parent
    const opt = document.createElement("option");
    opt.value = item.id;
    opt.textContent = `${item.parent_id ? '  ↳ ' : ''}${item.name} (#${item.id})`;
    select.appendChild(opt);
  });
}

function openModal(menu = null) {
  editingItemId = menu ? menu.id : null;
  populateParentDropdown(editingItemId);

  document.getElementById("modal-title").textContent = menu ? "Edit Menu Item" : "Create New Menu Item";
  document.getElementById("menu-name").value = menu ? menu.name : "";
  document.getElementById("menu-url").value = menu ? menu.url : "";
  document.getElementById("menu-parent").value = menu && menu.parent_id ? menu.parent_id : "";
  document.getElementById("menu-order").value = menu ? menu.display_order : 0;
  document.getElementById("menu-status").value = menu ? menu.status : "active";

  clearFormErrors();
  document.getElementById("crud-modal").classList.add("active");
}

function closeModal() {
  document.getElementById("crud-modal").classList.remove("active");
  editingItemId = null;
}

window.viewMenu = function(id) {
  const menu = currentItems.find(m => m.id === id);
  if (!menu) return;

  document.getElementById("view-menu-name").textContent = menu.name;
  document.getElementById("view-menu-id").textContent = `#${menu.id}`;
  document.getElementById("view-menu-url").textContent = menu.url;
  document.getElementById("view-menu-parent").textContent = menu.parent_name || "None (Top-Level)";
  document.getElementById("view-menu-status").innerHTML = `<span class="badge badge-${menu.status}">${menu.status}</span>`;
  document.getElementById("view-menu-order").textContent = menu.display_order;
  document.getElementById("view-menu-created").textContent = menu.created_at;
  document.getElementById("view-menu-updated").textContent = menu.updated_at || menu.created_at;

  document.getElementById("view-modal").classList.add("active");
};

function closeViewModal() {
  document.getElementById("view-modal").classList.remove("active");
}

window.editMenu = function(id) {
  const menu = currentItems.find(m => m.id === id);
  if (menu) openModal(menu);
};

window.deleteMenu = async function(id) {
  const menu = currentItems.find(m => m.id === id);
  const name = menu ? menu.name : `Menu #${id}`;

  const confirmed = await confirmAction(`Delete menu item "${name}"? Child items will automatically be promoted to top-level.`, "Delete Menu Item");
  if (!confirmed) return;

  const res = await apiClient.delete(`/api/menus/${id}`);
  if (!res.success) {
    showToast(res.message || "Failed to delete menu item", "error");
    return;
  }

  showToast("Menu item deleted successfully", "success");
  await loadMenus();
};

async function handleFormSubmit(e) {
  e.preventDefault();
  clearFormErrors();

  const name = document.getElementById("menu-name").value.trim();
  const url = document.getElementById("menu-url").value.trim();
  const parent_id = document.getElementById("menu-parent").value;
  const display_order = parseInt(document.getElementById("menu-order").value || 0);
  const status = document.getElementById("menu-status").value;

  let hasError = false;
  if (!name) {
    setFieldError("menu-name", "Menu name is required.");
    hasError = true;
  }
  if (!url) {
    setFieldError("menu-url", "URL is required.");
    hasError = true;
  }
  if (hasError) return;

  const payload = {
    name,
    url,
    parent_id: parent_id ? parseInt(parent_id) : null,
    display_order,
    status
  };

  const submitBtn = document.getElementById("modal-submit-btn");
  submitBtn.disabled = true;
  submitBtn.innerHTML = '<span class="spinner" style="width:14px;height:14px;border-width:2px;"></span> Saving...';

  let res;
  if (editingItemId) {
    res = await apiClient.put(`/api/menus/${editingItemId}`, payload);
  } else {
    res = await apiClient.post("/api/menus", payload);
  }

  submitBtn.disabled = false;
  submitBtn.textContent = "Save Menu Item";

  if (!res.success) {
    if (res.errors) {
      Object.keys(res.errors).forEach(key => {
        setFieldError(`menu-${key}`, res.errors[key]);
      });
    }
    showToast(res.message || "Failed to save menu item", "error");
    return;
  }

  showToast(editingItemId ? "Menu item updated successfully" : "Menu item created successfully", "success");
  closeModal();
  await loadMenus();
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

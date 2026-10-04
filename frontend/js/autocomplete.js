/**
 * Magnus Dynamic CMS - Autocomplete Admin Controller
 */

let currentItems = [];
let editingItemId = null;

document.addEventListener("DOMContentLoaded", () => {
  if (!Auth.checkAuth()) return;
  Auth.initSidebar();

  loadAutocompleteItems();
  setupEventListeners();
  setupLiveSearchTest();
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
    statusFilter.addEventListener("change", () => loadAutocompleteItems());
  }
}

async function loadAutocompleteItems() {
  const tableBody = document.getElementById("table-body");
  tableBody.innerHTML = '<tr><td colspan="6" class="loading-container"><span class="spinner"></span><span>Loading autocomplete records...</span></td></tr>';

  const status = document.getElementById("status-filter").value;
  const res = await apiClient.get("/api/autocomplete", { status });

  if (!res.success) {
    tableBody.innerHTML = `<tr><td colspan="6" class="empty-state"><p>${res.message || "Failed to load records"}</p></td></tr>`;
    return;
  }

  currentItems = res.data || [];
  filterAndRender();
}

function filterAndRender() {
  const searchTerm = (document.getElementById("table-search")?.value || "").toLowerCase().trim();
  const filtered = currentItems.filter(item => {
    return !searchTerm ||
      item.label.toLowerCase().includes(searchTerm) ||
      item.value.toLowerCase().includes(searchTerm) ||
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
        <td colspan="6" class="empty-state">
          <div class="empty-state-icon">🔍</div>
          <div class="empty-state-title">No Autocomplete Items Found</div>
          <p>Click "+ Add Autocomplete Item" above to add new search keywords.</p>
        </td>
      </tr>
    `;
    return;
  }

  tableBody.innerHTML = items.map(item => `
    <tr>
      <td><strong>#${item.id}</strong></td>
      <td>
        <div style="font-weight: 600;">${escapeHtml(item.label)}</div>
        <small style="color: var(--text-muted);">${escapeHtml(item.description || 'No description')}</small>
      </td>
      <td><code>${escapeHtml(item.value)}</code></td>
      <td>
        <span class="badge badge-${item.status}">${item.status}</span>
      </td>
      <td><small>${item.created_at}</small></td>
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

function setupLiveSearchTest() {
  const searchInput = document.getElementById("live-autocomplete-input");
  const suggestionsBox = document.getElementById("autocomplete-suggestions-box");
  const indicator = document.getElementById("search-loading-indicator");
  if (!searchInput || !suggestionsBox) return;

  let debounceTimer;

  searchInput.addEventListener("input", (e) => {
    clearTimeout(debounceTimer);
    const query = e.target.value.trim();

    if (query.length < 2) {
      suggestionsBox.innerHTML = "";
      suggestionsBox.style.display = "none";
      if (indicator) indicator.style.display = "none";
      return;
    }

    if (indicator) indicator.style.display = "inline-block";

    debounceTimer = setTimeout(async () => {
      const res = await apiClient.get("/api/autocomplete/search", { q: query });
      if (indicator) indicator.style.display = "none";

      if (!res.success || !res.data || res.data.length === 0) {
        suggestionsBox.innerHTML = '<div style="padding: 10px; font-size: 0.85rem; color: var(--text-muted);">No matching results in MySQL</div>';
        suggestionsBox.style.display = "block";
        return;
      }

      suggestionsBox.innerHTML = res.data.map(item => `
        <div class="autocomplete-suggestion-item" 
             style="padding: 10px 14px; cursor: pointer; border-bottom: 1px solid var(--border-color); font-size: 0.875rem;"
             data-val="${escapeHtml(item.value)}"
             data-lbl="${escapeHtml(item.label)}">
          <div style="font-weight: 600; color: var(--text-main);">${escapeHtml(item.label)}</div>
          <div style="font-size: 0.75rem; color: var(--text-muted);">${escapeHtml(item.description || item.value)}</div>
        </div>
      `).join("");

      suggestionsBox.querySelectorAll(".autocomplete-suggestion-item").forEach(itemEl => {
        itemEl.addEventListener("click", () => {
          searchInput.value = itemEl.getAttribute("data-lbl");
          suggestionsBox.innerHTML = "";
          suggestionsBox.style.display = "none";
          showToast(`Selected "${itemEl.getAttribute('data-lbl')}" (${itemEl.getAttribute('data-val')})`, "info");
        });
        itemEl.addEventListener("mouseenter", () => {
          itemEl.style.backgroundColor = "#f1f5f9";
        });
        itemEl.addEventListener("mouseleave", () => {
          itemEl.style.backgroundColor = "transparent";
        });
      });

      suggestionsBox.style.display = "block";
    }, 250);
  });

  // Close dropdown on click outside
  document.addEventListener("click", (e) => {
    if (!searchInput.contains(e.target) && !suggestionsBox.contains(e.target)) {
      suggestionsBox.style.display = "none";
    }
  });
}

function openModal(item = null) {
  editingItemId = item ? item.id : null;
  document.getElementById("modal-title").textContent = item ? "Edit Autocomplete Item" : "Create New Autocomplete Item";
  document.getElementById("item-label").value = item ? item.label : "";
  document.getElementById("item-value").value = item ? item.value : "";
  document.getElementById("item-description").value = item ? (item.description || "") : "";
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

  document.getElementById("view-item-label").textContent = item.label;
  document.getElementById("view-item-id").textContent = `#${item.id}`;
  document.getElementById("view-item-value").textContent = item.value;
  document.getElementById("view-item-status").innerHTML = `<span class="badge badge-${item.status}">${item.status}</span>`;
  document.getElementById("view-item-desc").textContent = item.description || "No description provided.";
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
  const label = item ? item.label : `Item #${id}`;

  const confirmed = await confirmAction(`Delete autocomplete item "${label}"?`, "Delete Item");
  if (!confirmed) return;

  const res = await apiClient.delete(`/api/autocomplete/${id}`);
  if (!res.success) {
    showToast(res.message || "Failed to delete item", "error");
    return;
  }

  showToast("Item deleted successfully", "success");
  await loadAutocompleteItems();
};

async function handleFormSubmit(e) {
  e.preventDefault();
  clearFormErrors();

  const label = document.getElementById("item-label").value.trim();
  const value = document.getElementById("item-value").value.trim();
  const description = document.getElementById("item-description").value.trim();
  const status = document.getElementById("item-status").value;

  let hasError = false;
  if (!label) {
    setFieldError("item-label", "Label is required.");
    hasError = true;
  }
  if (!value) {
    setFieldError("item-value", "Value is required.");
    hasError = true;
  }
  if (hasError) return;

  const payload = { label, value, description, status };
  const submitBtn = document.getElementById("modal-submit-btn");
  submitBtn.disabled = true;
  submitBtn.innerHTML = '<span class="spinner" style="width:14px;height:14px;border-width:2px;"></span> Saving...';

  let res;
  if (editingItemId) {
    res = await apiClient.put(`/api/autocomplete/${editingItemId}`, payload);
  } else {
    res = await apiClient.post("/api/autocomplete", payload);
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
  await loadAutocompleteItems();
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

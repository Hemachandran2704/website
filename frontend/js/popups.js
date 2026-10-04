/**
 * Magnus Dynamic CMS - Popups Admin Controller
 */

let currentItems = [];
let editingItemId = null;

document.addEventListener("DOMContentLoaded", () => {
  if (!Auth.checkAuth()) return;
  Auth.initSidebar();

  loadPopups();
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
    statusFilter.addEventListener("change", () => loadPopups());
  }

  // Live trigger popup close
  const livePopupClose = document.getElementById("live-popup-close-btn");
  if (livePopupClose) {
    livePopupClose.addEventListener("click", () => {
      document.getElementById("live-preview-popup-modal").classList.remove("active");
    });
  }
}

async function loadPopups() {
  const tableBody = document.getElementById("table-body");
  tableBody.innerHTML = '<tr><td colspan="6" class="loading-container"><span class="spinner"></span><span>Loading popups...</span></td></tr>';

  const status = document.getElementById("status-filter").value;
  const res = await apiClient.get("/api/popups", { status });

  if (!res.success) {
    tableBody.innerHTML = `<tr><td colspan="6" class="empty-state"><p>${res.message || "Failed to load popups"}</p></td></tr>`;
    return;
  }

  currentItems = res.data || [];
  filterAndRender();
  renderLivePopupsPreview();
}

function filterAndRender() {
  const searchTerm = (document.getElementById("table-search")?.value || "").toLowerCase().trim();
  const filtered = currentItems.filter(item => {
    return !searchTerm ||
      item.title.toLowerCase().includes(searchTerm) ||
      item.content.toLowerCase().includes(searchTerm) ||
      item.trigger_type.toLowerCase().includes(searchTerm);
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
          ${popup.can_manage ? `
          <div class="empty-state-icon">🪟</div>
          <div class="empty-state-title">No Popups Found</div>
          ` : ""}
          <p>Click "+ Add Popup" above to configure dynamic modal dialogs.</p>
        </td>
      </tr>
    `;
    return;
  }

  tableBody.innerHTML = items.map(popup => `
    <tr>
      <td><strong>#${popup.id}</strong></td>
      <td>
        <div style="font-weight: 600;">${escapeHtml(popup.title)}</div>
        <small style="color: var(--text-muted);">${escapeHtml(popup.content.substring(0, 45))}${popup.content.length > 45 ? '...' : ''}</small>
      </td>
      <td>
        <span class="badge" style="background: #e0e7ff; color: #3730a3; text-transform: uppercase;">${popup.trigger_type}</span>
      </td>
      <td>
        <span class="badge badge-${popup.status}">${popup.status}</span>
      </td>
      <td><small>${popup.created_at}</small></td>
      <td>
        <div class="table-actions">
          <button class="btn btn-sm btn-action-view" onclick="testTriggerPopup(${popup.id})" title="Test Trigger">🚀 Trigger</button>
          <button class="btn btn-sm btn-action-edit" ${popup.can_manage ? "" : "disabled"} onclick="editPopup(${popup.id})" title="Edit Popup">✏️ Edit</button>
          <button class="btn btn-sm btn-action-delete" ${popup.can_manage ? "" : "disabled"} onclick="deletePopup(${popup.id})" title="Delete Popup">🗑️ Delete</button>
        </div>
      </td>
    </tr>
  `).join("");
}

function renderLivePopupsPreview() {
  const container = document.getElementById("preview-popups-triggers");
  if (!container) return;

  const activePopups = currentItems.filter(p => p.status === "active");

  if (activePopups.length === 0) {
    container.innerHTML = "<p style='color: var(--text-muted);'>No active popups available.</p>";
    return;
  }

  container.innerHTML = `
    <div style="display: flex; flex-wrap: wrap; gap: 12px; align-items: center;">
      ${activePopups.map(p => `
        <button class="btn btn-primary btn-sm" onclick="testTriggerPopup(${p.id})">
          Trigger: ${escapeHtml(p.title)} (${p.trigger_type})
        </button>
      `).join("")}
    </div>
  `;
}

window.testTriggerPopup = function(id) {
  const popup = currentItems.find(p => p.id === id);
  if (!popup) return;

  const modal = document.getElementById("live-preview-popup-modal");
  document.getElementById("live-popup-title").textContent = popup.title;
  document.getElementById("live-popup-content").textContent = popup.content;
  document.getElementById("live-popup-trigger-badge").textContent = popup.trigger_type.toUpperCase();

  modal.classList.add("active");
};

function openModal(popup = null) {
  editingItemId = popup ? popup.id : null;
  document.getElementById("modal-title").textContent = popup ? "Edit Popup" : "Create New Popup";
  document.getElementById("popup-title").value = popup ? popup.title : "";
  document.getElementById("popup-content").value = popup ? popup.content : "";
  document.getElementById("popup-trigger").value = popup ? popup.trigger_type : "button_click";
  document.getElementById("popup-status").value = popup ? popup.status : "active";

  clearFormErrors();
  document.getElementById("crud-modal").classList.add("active");
}

function closeModal() {
  document.getElementById("crud-modal").classList.remove("active");
  editingItemId = null;
}

function closeViewModal() {
  document.getElementById("view-modal").classList.remove("active");
}

window.editPopup = function(id) {
  const popup = currentItems.find(t => t.id === id);
  if (popup) openModal(popup);
};

window.deletePopup = async function(id) {
  const popup = currentItems.find(t => t.id === id);
  const title = popup ? popup.title : `Popup #${id}`;

  const confirmed = await confirmAction(`Delete popup "${title}"?`, "Delete Popup");
  if (!confirmed) return;

  const res = await apiClient.delete(`/api/popups/${id}`);
  if (!res.success) {
    showToast(res.message || "Failed to delete popup", "error");
    return;
  }

  showToast("Popup deleted successfully", "success");
  await loadPopups();
};

async function handleFormSubmit(e) {
  e.preventDefault();
  clearFormErrors();

  const title = document.getElementById("popup-title").value.trim();
  const content = document.getElementById("popup-content").value.trim();
  const trigger_type = document.getElementById("popup-trigger").value;
  const status = document.getElementById("popup-status").value;

  let hasError = false;
  if (!title) {
    setFieldError("popup-title", "Title is required.");
    hasError = true;
  }
  if (!content) {
    setFieldError("popup-content", "Content is required.");
    hasError = true;
  }
  if (hasError) return;

  const payload = { title, content, trigger_type, status };
  const submitBtn = document.getElementById("modal-submit-btn");
  submitBtn.disabled = true;
  submitBtn.innerHTML = '<span class="spinner" style="width:14px;height:14px;border-width:2px;"></span> Saving...';

  let res;
  if (editingItemId) {
    res = await apiClient.put(`/api/popups/${editingItemId}`, payload);
  } else {
    res = await apiClient.post("/api/popups", payload);
  }

  submitBtn.disabled = false;
  submitBtn.textContent = "Save Popup";

  if (!res.success) {
    if (res.errors) {
      Object.keys(res.errors).forEach(key => {
        setFieldError(`popup-${key}`, res.errors[key]);
      });
    }
    showToast(res.message || "Failed to save popup", "error");
    return;
  }

  showToast(editingItemId ? "Popup updated successfully" : "Popup created successfully", "success");
  closeModal();
  await loadPopups();
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

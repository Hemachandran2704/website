/**
 * Magnus Dynamic CMS - Tooltips Admin Controller
 */

let currentItems = [];
let editingItemId = null;
let activeTooltipEl = null;

document.addEventListener("DOMContentLoaded", () => {
  if (!Auth.checkAuth()) return;
  Auth.initSidebar();

  loadTooltips();
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
    statusFilter.addEventListener("change", () => loadTooltips());
  }
}

async function loadTooltips() {
  const tableBody = document.getElementById("table-body");
  tableBody.innerHTML = '<tr><td colspan="6" class="loading-container"><span class="spinner"></span><span>Loading tooltips...</span></td></tr>';

  const status = document.getElementById("status-filter").value;
  const res = await apiClient.get("/api/tooltips", { status });

  if (!res.success) {
    tableBody.innerHTML = `<tr><td colspan="6" class="empty-state"><p>${res.message || "Failed to load tooltips"}</p></td></tr>`;
    return;
  }

  currentItems = res.data || [];
  filterAndRender();
  renderLiveTooltipsPreview();
}

function filterAndRender() {
  const searchTerm = (document.getElementById("table-search")?.value || "").toLowerCase().trim();
  const filtered = currentItems.filter(item => {
    return !searchTerm ||
      item.element_name.toLowerCase().includes(searchTerm) ||
      item.content.toLowerCase().includes(searchTerm) ||
      item.position.toLowerCase().includes(searchTerm);
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
          <div class="empty-state-icon">💬</div>
          <div class="empty-state-title">No Tooltips Found</div>
          <p>Click "+ Add Tooltip" above to bind interactive tooltips to UI elements.</p>
        </td>
      </tr>
    `;
    return;
  }

  tableBody.innerHTML = items.map(tip => `
    <tr>
      <td><strong>#${tip.id}</strong></td>
      <td>
        <code style="font-weight: 600; color: var(--primary);">${escapeHtml(tip.element_name)}</code>
      </td>
      <td>
        <div style="font-size: 0.85rem; max-width: 280px;">${escapeHtml(tip.content)}</div>
      </td>
      <td>
        <span class="badge" style="background: #f1f5f9; color: #334155; text-transform: uppercase;">${tip.position}</span>
      </td>
      <td>
        <span class="badge badge-${tip.status}">${tip.status}</span>
      </td>
      <td>
        <div class="table-actions">
          <button class="btn btn-sm btn-action-view" onclick="viewTooltip(${tip.id})" title="View Details">👁️ View</button>
          <button class="btn btn-sm btn-action-edit" ${tip.can_manage ? "" : "disabled"} onclick="editTooltip(${tip.id})" title="Edit Tooltip">✏️ Edit</button>
          <button class="btn btn-sm btn-action-delete" ${tip.can_manage ? "" : "disabled"} onclick="deleteTooltip(${tip.id})" title="Delete Tooltip">🗑️ Delete</button>
        </div>
      </td>
    </tr>
  `).join("");
}

function renderLiveTooltipsPreview() {
  const playground = document.getElementById("preview-tooltips-playground");
  if (!playground) return;

  const activeTips = currentItems.filter(t => t.status === "active");

  if (activeTips.length === 0) {
    playground.innerHTML = "<p style='color: var(--text-muted);'>No active tooltips to preview.</p>";
    return;
  }

  playground.innerHTML = `
    <div style="display: flex; flex-wrap: wrap; gap: 24px; padding: 20px; align-items: center; justify-content: center;">
      ${activeTips.map(tip => `
        <div style="position: relative; display: inline-flex; align-items: center; gap: 8px; padding: 10px 16px; background: #ffffff; border: 1px solid var(--border-color); border-radius: 8px; box-shadow: var(--shadow-sm);">
          <span style="font-size: 0.85rem; font-weight: 600;">${escapeHtml(tip.element_name)}</span>
          <button class="btn btn-primary btn-sm btn-icon interactive-tooltip-trigger" 
                  data-tip-content="${escapeHtml(tip.content)}"
                  data-tip-pos="${tip.position}"
                  style="width: 22px; height: 22px; border-radius: 50%; padding: 0; font-size: 0.75rem; font-weight: bold;">
            ?
          </button>
        </div>
      `).join("")}
    </div>
  `;

  // Attach hover listeners
  playground.querySelectorAll(".interactive-tooltip-trigger").forEach(btn => {
    btn.addEventListener("mouseenter", (e) => {
      showDynamicTooltip(btn, btn.getAttribute("data-tip-content"), btn.getAttribute("data-tip-pos"));
    });
    btn.addEventListener("mouseleave", () => {
      hideDynamicTooltip();
    });
  });
}

function showDynamicTooltip(targetEl, content, position = "top") {
  hideDynamicTooltip();

  const tipBox = document.createElement("div");
  tipBox.className = `custom-tooltip-box pos-${position}`;
  tipBox.textContent = content;
  document.body.appendChild(tipBox);
  activeTooltipEl = tipBox;

  const rect = targetEl.getBoundingClientRect();
  const tipRect = tipBox.getBoundingClientRect();
  const scrollY = window.scrollY || window.pageYOffset;
  const scrollX = window.scrollX || window.pageXOffset;

  let top, left;

  switch (position) {
    case "bottom":
      top = rect.bottom + scrollY + 8;
      left = rect.left + scrollX + (rect.width / 2) - (tipRect.width / 2);
      break;
    case "left":
      top = rect.top + scrollY + (rect.height / 2) - (tipRect.height / 2);
      left = rect.left + scrollX - tipRect.width - 8;
      break;
    case "right":
      top = rect.top + scrollY + (rect.height / 2) - (tipRect.height / 2);
      left = rect.right + scrollX + 8;
      break;
    case "top":
    default:
      top = rect.top + scrollY - tipRect.height - 8;
      left = rect.left + scrollX + (rect.width / 2) - (tipRect.width / 2);
      break;
  }

  tipBox.style.top = `${top}px`;
  tipBox.style.left = `${left}px`;
}

function hideDynamicTooltip() {
  if (activeTooltipEl) {
    activeTooltipEl.remove();
    activeTooltipEl = null;
  }
}

function openModal(tip = null) {
  editingItemId = tip ? tip.id : null;
  document.getElementById("modal-title").textContent = tip ? "Edit Tooltip" : "Create New Tooltip";
  document.getElementById("tooltip-element").value = tip ? tip.element_name : "";
  document.getElementById("tooltip-content").value = tip ? tip.content : "";
  document.getElementById("tooltip-position").value = tip ? tip.position : "top";
  document.getElementById("tooltip-status").value = tip ? tip.status : "active";

  clearFormErrors();
  document.getElementById("crud-modal").classList.add("active");
}

function closeModal() {
  document.getElementById("crud-modal").classList.remove("active");
  editingItemId = null;
}

window.viewTooltip = function(id) {
  const tip = currentItems.find(t => t.id === id);
  if (!tip) return;

  document.getElementById("view-tooltip-element").textContent = tip.element_name;
  document.getElementById("view-tooltip-id").textContent = `#${tip.id}`;
  document.getElementById("view-tooltip-position").textContent = tip.position.toUpperCase();
  document.getElementById("view-tooltip-status").innerHTML = `<span class="badge badge-${tip.status}">${tip.status}</span>`;
  document.getElementById("view-tooltip-content").textContent = tip.content;
  document.getElementById("view-tooltip-created").textContent = tip.created_at;

  document.getElementById("view-modal").classList.add("active");
};

function closeViewModal() {
  document.getElementById("view-modal").classList.remove("active");
}

window.editTooltip = function(id) {
  const tip = currentItems.find(t => t.id === id);
  if (tip) openModal(tip);
};

window.deleteTooltip = async function(id) {
  const tip = currentItems.find(t => t.id === id);
  const name = tip ? tip.element_name : `Tooltip #${id}`;

  const confirmed = await confirmAction(`Delete tooltip for "${name}"?`, "Delete Tooltip");
  if (!confirmed) return;

  const res = await apiClient.delete(`/api/tooltips/${id}`);
  if (!res.success) {
    showToast(res.message || "Failed to delete tooltip", "error");
    return;
  }

  showToast("Tooltip deleted successfully", "success");
  await loadTooltips();
};

async function handleFormSubmit(e) {
  e.preventDefault();
  clearFormErrors();

  const element_name = document.getElementById("tooltip-element").value.trim();
  const content = document.getElementById("tooltip-content").value.trim();
  const position = document.getElementById("tooltip-position").value;
  const status = document.getElementById("tooltip-status").value;

  let hasError = false;
  if (!element_name) {
    setFieldError("tooltip-element", "Element identifier is required.");
    hasError = true;
  }
  if (!content) {
    setFieldError("tooltip-content", "Tooltip content is required.");
    hasError = true;
  }
  if (hasError) return;

  const payload = { element_name, content, position, status };
  const submitBtn = document.getElementById("modal-submit-btn");
  submitBtn.disabled = true;
  submitBtn.innerHTML = '<span class="spinner" style="width:14px;height:14px;border-width:2px;"></span> Saving...';

  let res;
  if (editingItemId) {
    res = await apiClient.put(`/api/tooltips/${editingItemId}`, payload);
  } else {
    res = await apiClient.post("/api/tooltips", payload);
  }

  submitBtn.disabled = false;
  submitBtn.textContent = "Save Tooltip";

  if (!res.success) {
    if (res.errors) {
      Object.keys(res.errors).forEach(key => {
        setFieldError(`tooltip-${key}`, res.errors[key]);
      });
    }
    showToast(res.message || "Failed to save tooltip", "error");
    return;
  }

  showToast(editingItemId ? "Tooltip updated successfully" : "Tooltip created successfully", "success");
  closeModal();
  await loadTooltips();
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
